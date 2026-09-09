"""
verify_front_elevation.py — the three things #80 added to the face a homeowner
looks at first, tested by POSITION.

EVERY GATE HERE IS WRITTEN AGAINST THE FAILURE MODE, NOT THE HEALTHY STATE.
That distinction is ground rule 24 and it was earned three times over: "has
glazing" passes on a single pane where six lites are drawn, "is a subset of
what is visible" passes on the empty set, "sits above z=0" passes on a rug
buried in the floor. Each of those described *a* correct state instead of *the*
thing that could go wrong.

So the gates below are phrased as the specific wrong outcomes this work could
have produced, and each is proved able to fail by breaking the exact line that
makes it true:

  * the door is a flat slab again           -> a lite centre is SOLID
  * the door got one sheet of glass         -> the lite COUNT is not 6
  * the glass runs the full leaf height     -> a lite centre sits below mid-leaf
  * the panel is flush, not recessed        -> the recess band is SOLID
  * the beam is buried in the gable         -> nothing forward of the gable face
  * the beam floats above the roof          -> its top is above the ridge
  * the gable window is a decal, not a hole -> its centre is SOLID

It also closes the loop on the measurement. `spec.trim.projecting_ridge_beam`
and `D-FRONT.construction` record figures the BUILD DOES NOT USE -- the top
rail and the panel come out of the build as remainders, so that the parts meet.
Those recorded measurements are checked here against what was actually built.
A measurement kept in the spec and never compared to anything is decoration.

    blender --background barn_cabin_524.blend --python verify_front_elevation.py
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec  # noqa: E402
from verify_lib import inside_mesh  # noqa: E402

FAILED = []


def gate(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:<58} {detail}")
    if not ok:
        FAILED.append(label)


def ob(name):
    return bpy.data.objects.get(name)


def bbox(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), max(c.x for c in cs),
            min(c.y for c in cs), max(c.y for c in cs),
            min(c.z for c in cs), max(c.z for c in cs))


def main():
    spec = load_spec(HERE / "spec.yaml")
    env, con = spec["envelope"], spec["construction"]
    t = con["exterior_wall_thickness"]["ft"]
    SY = env["porch_depth"]["ft"]

    door = next(o for o in spec["openings"]["main_floor"]["south_wall"]["openings"]
                if o["id"] == "D-FRONT")
    cn = door["construction"]
    st = cn["stile"]["ft"]
    gx0, gx1 = door["offset"] + st, door["offset"] + door["w"] - st
    gz0 = door["sill"] + cn["lite_grid"]["bottom_z"]
    gz1 = door["sill"] + cn["lite_grid"]["top_z"]
    cols, rows = cn["lites"]["cols"], cn["lites"]["rows"]

    leaf = ob("Door_D-FRONT")
    print("\n" + "=" * 96)
    print("FRONT ELEVATION — gable window, half-lite entry door, projecting ridge beam")
    print("=" * 96)

    # ---- 1. the door is not a slab ---------------------------------------
    # The failure this rejects: `Door_D-FRONT` goes back to being one box, and
    # every one of these points lands inside solid door.
    gate("the entry door was built at all", leaf is not None,
         "" if leaf else "Door_D-FRONT missing")
    if leaf is None:
        raise SystemExit(1)

    centres = []
    for i in range(cols):
        for j in range(rows):
            centres.append(Vector((
                gx0 + (gx1 - gx0) * (i + 0.5) / cols,
                (SY + t / 2),
                gz0 + (gz1 - gz0) * (j + 0.5) / rows)))
    solid = [p for p in centres if inside_mesh(leaf, p)]
    gate("you can see through every lite, not just some of them",
         not solid, f"{len(centres)} lite centres, {len(solid)} blocked by door solid")

    # ---- 2. SIX lites, counted -------------------------------------------
    # The failure this rejects: one sheet of glass across the upper half. That
    # passes any gate phrased as "the door has glazing", which is precisely why
    # this one counts instead of asking.
    lites = [o for o in bpy.data.objects
             if o.name.startswith("Glazing_D-FRONT_lite_")]
    want = cols * rows
    gate("the door carries exactly the lite count its TYPE claims",
         len(lites) == want,
         f"{len(lites)} panes against {cols}x{rows} = {want} "
         f"for a {door['type']}")

    # ---- 3. half-lite means the UPPER half -------------------------------
    # The failure this rejects: the glass runs the full 6'-8" of the leaf, which
    # is what the old code built. Every lite must sit above mid-leaf.
    #
    # The threshold carries the measurement tolerance, and NOT because that is
    # what made it pass. A1.1 puts the grid bottom at 3.322 where exact mid-leaf
    # is 3.333 — an eighth of an inch, which is this sheet's line weight and
    # already the declared tolerance for every other opening. Written to the
    # exact midpoint the gate would fail on a CORRECTLY built door, which is a
    # gate that has to be turned off, and a gate that has to be turned off gets
    # turned off. What it still rejects is the thing it is for: the old
    # full-height pane started at z=0, twenty times the tolerance away.
    tol = spec["openings"]["measurement"]["tolerance_ft"]
    mid = door["sill"] + door["h"] / 2
    lowest = min((bbox(o)[4] for o in lites), default=0.0)
    gate("no lite drops into the lower half — it is a HALF lite",
         lowest >= mid - tol,
         f"lowest lite bottom {lowest:.3f} against mid-leaf {mid:.3f} "
         f"±{tol:.2f}; a full-height pane would read 0.000")

    # ---- 4. the panel is recessed, not flush -----------------------------
    # The failure this rejects: the panel built flush with the stiles, which
    # looks like a slab and is what "geometrically correct and visually
    # nothing" means. Sampled INSIDE the recess band: air over the panel,
    # solid over the stile beside it, at the same depth.
    rec = cn["panel_recess"]["ft"]
    y_out = bbox(leaf)[2]                     # outside face of the leaf, -Y
    y_band = y_out + rec / 2                  # inside the recess, if there is one
    z_panel = (door["sill"] + cn["bottom_rail"]["ft"] + gz0 - cn["lock_rail"]["ft"]) / 2
    over_panel = Vector(((gx0 + gx1) / 2, y_band, z_panel))
    over_stile = Vector((door["offset"] + st / 2, y_band, z_panel))
    gate("the panel is set back from the face of the stiles",
         not inside_mesh(leaf, over_panel) and inside_mesh(leaf, over_stile),
         f"at y {y_band:.4f}: panel air={not inside_mesh(leaf, over_panel)}, "
         f"stile solid={inside_mesh(leaf, over_stile)}")

    # ---- 5. the build reproduces the measurements it did NOT use ---------
    # The top rail and the panel are REMAINDERS in build_adu, derived so the
    # parts meet. spec recorded both as measurements. If the two disagree, one
    # of them is wrong and the spec would otherwise never say so.
    built_top_rail = (door["sill"] + door["h"]) - gz1
    gate("the built top rail matches the one measured off A1.1",
         abs(built_top_rail - cn["top_rail"]["ft"]) <= tol,
         f"built {built_top_rail:.3f} vs measured {cn['top_rail']['ft']:.3f} ft")
    built_grid_w = gx1 - gx0
    gate("the built lite grid matches the one measured off A1.1",
         abs(built_grid_w - cn["lite_grid"]["w"]) <= tol,
         f"built {built_grid_w:.3f} vs measured {cn['lite_grid']['w']:.3f} ft")

    # ---- 6. the ridge beam PROJECTS ---------------------------------------
    # The failure this rejects: the beam built flush with the gable, or buried
    # in it, which is a beam nobody can see and the whole point of the item is
    # that it stands proud.
    rb = spec["trim"]["projecting_ridge_beam"]
    beam = ob("Ridge_beam")
    gate("the ridge beam was built at all", beam is not None,
         "" if beam else "Ridge_beam missing")
    if beam is None:
        raise SystemExit(1)
    bx0, bx1, by0, by1, bz0, bz1 = bbox(beam)
    gable_face = 0.0                          # the gable prism's outer face
    gate("the ridge beam stands proud of the gable, not flush with it",
         by0 < gable_face - 1e-6,
         f"beam reaches y {by0:.3f}, gable face at {gable_face:.3f} "
         f"— {(gable_face - by0) * 12:.1f}\" of tail")
    tip = Vector(((bx0 + bx1) / 2, by0 + abs(by0) / 2, (bz0 + bz1) / 2))
    gate("the projecting tail is solid, not an empty bounding box",
         inside_mesh(beam, tip), f"sampled at y {tip.y:.3f}")

    # ---- 7. the beam is at the apex, and BELOW the roof -------------------
    # The failure this rejects: a beam floating above the ridge, or off-centre.
    # It hangs under the gable peak; a top above the ridge means it is through
    # the roof.
    ridge = spec["roof"]["elevation_calibration"]["ridge_top_of_roof"]["ft"]
    gate("the ridge beam does not poke through the roof",
         bz1 < ridge, f"beam top {bz1:.3f} under ridge {ridge:.3f}")
    cx = (bx0 + bx1) / 2
    gate("the ridge beam sits on the building centreline",
         abs(cx - env["main_body_width"]["ft"] / 2) <= tol,
         f"centre x {cx:.3f} against {env['main_body_width']['ft'] / 2:.3f}")

    # ---- 8. the gable window is a HOLE, not a decal -----------------------
    # The failure this rejects: glazing placed over an uncut gable. The volume
    # gate in verify_openings.py already covers the cut; this covers the pane
    # sitting in it, and the shingle field still being solid around it.
    gw = spec["openings"]["loft"]["south_gable"]["windows"][0]
    gable = ob("Gable_S_porch")
    mid_x = gw["centre"]
    mid_z = gw["sill"] + gw["h"] / 2
    through = Vector((mid_x, t / 2, mid_z))
    beside = Vector((mid_x + gw["w"], t / 2, mid_z))
    # The detail REPORTS what it found rather than restating the pass case. An
    # earlier version read "centre air, shingle solid" unconditionally, so when
    # the RED test uncut the gable the failing line still said the opening was
    # air — a message that argues against its own verdict.
    hole = not inside_mesh(gable, through)
    wall = inside_mesh(gable, beside)
    gate("the gable window is cut through the shingle field", hole and wall,
         f"opening centre air={hole}, shingle at x {beside.x:.2f} solid={wall}")
    pane = ob(f"Glazing_{gw['id']}")
    gate("the gable window has glass in it",
         pane is not None and inside_mesh(pane, through),
         f"Glazing_{gw['id']}" + ("" if pane else " MISSING"))

    print("=" * 96)
    print("RESULT:", "ALL PASS" if not FAILED else f"FAILURES {FAILED}")
    print("=" * 96)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
