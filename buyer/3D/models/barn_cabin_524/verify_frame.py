"""
verify_frame.py — the built barn cabin is not a mirror image of A1.1 (#145).

Laurel's first spec draft was mirrored (#128): it read a plan whose front is
the plan's left edge as though plan-up were plan-right. This model's P2 build
was mirrored too, the other way (spec `mirrored-model`). Neither was caught by
a gate; both were caught by looking.

WHY THE OTHER GATES CANNOT SEE IT. verify_openings.py places every opening
with the same compass convention build_adu.py uses -- west at X 0, south at
low Y. If "west" had been read off the plan backwards, the build and that gate
would agree with each other and both would be wrong (rule 29). So this file
never reads the spec's compass labels. It reads the MESH, and holds it to what
A1.1 draws, in terms that need no compass at all: the viewer's left and right.

THE WITNESS IS THE SHEET (rule 40). A1.1, OPTION B (PDF page 3), where every
fact below reads plainly at 40 dpi:

  * MAIN FLOOR PLAN: the covered porch is at the bottom of the plan, the bath
    and kitchen windows on the plan's LEFT wall, the meter on its RIGHT wall.
    Standing outside the front, plan-left is the viewer's left.
  * FRONT ELEVATION: the wide 4'-0" x 3'-0" D.S.H. is LEFT of the door, the
    tall 3'-0" x 5'-0" S.H. to its RIGHT.
  * LEFT ELEVATION: two windows, with the porch at the viewer's RIGHT.
  * RIGHT ELEVATION: no windows at the main floor, the porch at the viewer's
    LEFT.
  * REAR ELEVATION: the egress window sits LEFT of centre.

"Front" is where the porch is, taken from the mesh. Everything else follows
from that and from +Z being up.

    blender --background --python verify_frame.py

It opens barn_cabin_524.blend beside it rather than trusting whatever scene it
was handed (rule 28). Exit 1 on a failed gate.
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "barn_cabin_524.blend"
UP = Vector((0.0, 0.0, 1.0))
FAILED = []


def gate(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def box(name):
    o = bpy.data.objects.get(name)
    if o is None:
        raise KeyError(f"{name} is not in {BLEND.name}")
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def centre(name):
    lo, hi = box(name)
    return (lo + hi) / 2.0


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    print("=" * 76)
    print(f"{BLEND.name} -- the built frame against A1.1's plan and elevations")
    print("=" * 76)

    walls = [box(n) for n in ("Wall_N", "Wall_S", "Wall_E", "Wall_W")]
    lo = Vector([min(b[0][i] for b in walls) for i in range(3)])
    hi = Vector([max(b[1][i] for b in walls) for i in range(3)])
    mid = (lo + hi) / 2.0
    mid.z = 0.0

    # FRONT: from the body's centre toward the porch, flattened to the ground.
    front = centre("Porch_slab") - mid
    front.z = 0.0
    front.normalize()
    # Standing outside, looking back at the front wall: look = -front.
    right = (-front).cross(UP)
    left = -right
    half_width = abs((hi - lo).dot(right)) / 2.0

    def side(name):
        """Signed distance toward the viewer's LEFT, facing the front from outside."""
        c = centre(name)
        c.z = 0.0
        return (c - mid).dot(left)

    door = side("Door_D-FRONT")
    gate("the front door is on the porch side of the building",
         (centre("Door_D-FRONT") - mid).dot(front) > 0,
         "FRONT ELEVATION draws the door under the porch roof")

    # The plan's left wall: the bath and kitchen windows, at the far left.
    for w in ("Win_W-BATH", "Win_W-KITCHEN"):
        s = side(w)
        gate(f"facing the front, {w[4:]} is on the viewer's LEFT wall",
             s > 0.9 * half_width,
             f"{s:+.2f} ft toward the left, the wall is at {half_width:+.2f}; "
             "A1.1 draws it on the plan's left wall and on the LEFT ELEVATION")

    # The right elevation: nothing at the main floor on the far right wall.
    plate = min(b[1].z for b in walls)
    stray = [o.name for o in bpy.data.objects
             if o.type == "MESH" and o.name.startswith("Win_")
             and centre(o.name).z < plate
             and side(o.name) < -0.9 * half_width]
    gate("the RIGHT ELEVATION's wall has no main-floor window", not stray,
         f"found {', '.join(sorted(stray))}")

    # The front elevation: the D.S.H. left of the door, the S.H. right of it.
    s1, s2 = side("Win_W-LIVING-S1"), side("Win_W-LIVING-S2")
    gate("the FRONT ELEVATION's D.S.H. is left of the door, its S.H. right",
         s1 > door > s2,
         f"D.S.H. {s1:+.2f}, door {door:+.2f}, S.H. {s2:+.2f} ft toward the left")

    # The rear elevation, seen from behind: the viewer's left is the front
    # viewer's right.
    egress = -side("Win_W-BED-EGRESS")
    gate("the REAR ELEVATION's egress window is left of centre", egress > 0,
         f"{egress:+.2f} ft toward the rear viewer's left")

    axis = max(("+X", Vector((1, 0, 0))), ("-X", Vector((-1, 0, 0))),
               ("+Y", Vector((0, 1, 0))), ("-Y", Vector((0, -1, 0))),
               key=lambda a: a[1].dot(front))[0]
    print("-" * 76)
    print(f"front faces {axis} in Blender; facing it from outside, "
          f"X increases to the viewer's {'right' if right.x > 0 else 'left'}")
    if FAILED:
        print(f"{len(FAILED)} GATE(S) FAILED")
        sys.exit(1)
    print("all frame gates pass")


if __name__ == "__main__":
    main()
