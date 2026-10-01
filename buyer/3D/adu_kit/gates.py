"""
adu_kit/gates.py -- build gates that read a model's built scene and its spec (#169).

Runs in Blender (it reads meshes); the plumbing it reports through is
adu_kit/gatelog.py, which does not.

MOVED UNCHANGED FROM LAUREL'S build.py, batch 1 of two. These are the gates that
need no builder helper and no Laurel-only content: they depend on `(spec, geo)`, a few
tolerances, `world_bbox`, AND the Blender scene and its object names (the section
"BEYOND geo" below, which an earlier draft of this docstring left out). Each returns
`(ok, why)`, and the model's own report() decides the order and the label, as it did.

THE `geo` CONTRACT. This module is where a model's build and the shared gates meet,
so what the gates read from `geo` is written down here, measured from the code
with an AST walk (not guessed):

  W, D, t        floats, in feet: the building's width, depth and wall thickness.

  walls          dict {name: Blender mesh object}. It holds EVERY solid the opening
                 builder cuts, not only the shell: the four shell walls under the
                 exact names "Wall_rear", "Wall_front", "Wall_x0" and "Wall_x24"
                 (footprint() looks for these four by name), each interior partition
                 under its spec id, and each wall's skins ("Sheathing_*", "Siding_*").

  built          a FLAT LIST of opening records, one dict per opening, with the keys
                 the gates read:
                   id        the opening's id, e.g. "W-A1" or "D-1"
                   wall      the key in `walls` it is cut from
                   a0, a1    its span along that wall, in feet
                   z0, z1    its height range, in feet
                   along     "x" or "y", the axis the span runs along
                   row       the spec row it was built from (it carries "type")
                   block     the spec block an EXTERIOR opening came from, e.g.
                             "front_wall". Optional: a door cut in a partition has
                             none, and the gate that reads it skips those.

  depths         dict {wall or skin name: thickness}: how deep that solid's cutters
                 pass through it.
  volumes        dict {wall name: (volume_before_cutting, volume_after_cutting)}, one
                 pair per WALL (not per opening), recorded around the boolean.
  skin_of        dict {wall name: its sheathing skin's name in `walls`}.
  siding_of      dict {wall name: its siding skin's name in `walls`}.
  trim           a LIST of Blender objects: the interior trim, one per host wall,
                 named "Trim_<host>".
  siding         a LIST of Blender objects: the exterior siding trim, named
                 "Trim_ext_siding_<wall>". (Not the siding skins, which are in `walls`.)
  ceiling        an adu_kit.roof ceiling object (the walls' head), NOT the roof.
  furniture      (read by a gate that moves in the second batch)

The gates of THIS batch read exactly: W, D, t, walls, built, depths, volumes,
skin_of, siding_of, siding, trim, ceiling. Their spec reads are `interior_partitions`
(partitions), `openings` and `windows` (openings, sashes). A model that builds a
`geo` with those keys, holding what they say, gets the gates.
Names such as "Wall_front" and the opening blocks "front_wall", "end_wall_x0" are
the one-storey-rectangle class's; a different class would name its own.

BEYOND `geo`: THE BLENDER SCENE AND ITS NAMES. Five of the eight gates also read the
global scene (`bpy.data.objects`), so a model can match the `geo` shapes above and
still be incompatible. What they need, read off the code:

  every_partition_built   an object in the scene named by each partition's spec id
                          (`bpy.data.objects.get(row["id"])`), not looked up in `geo`.
  every_row_built         for each opening in `built`: an object named "Sash_<id>" if
                          the id starts with "W-" (a window), else "Leaf_<id>" (a door);
                          and the wall object, found by name in the scene, to read the
                          opening's four corners from its vertices.
  sash_members            for each "W-" opening, an object named "Sash_<id>".
  trim_inside_its_walls   tells interior from exterior trim by the NAME prefix
                          "Trim_ext_siding_".
  no_degenerate           scans EVERY mesh in the scene for NaN or infinite vertices;
                          it takes no arguments and reads no `geo` at all.

So the contract also includes: opening ids start "W-" for windows; every opening has a
"Sash_"/"Leaf_" object; partitions are scene objects named by their spec ids; and the
scene holds only this model (no_degenerate sees all of it). These are the one-storey
class's conventions, as with the wall names above, and they are NOT routed through
`geo`. Routing them through `geo` would change the gates, so this move documents them
instead; Willow's build either follows the names or that is the moment to route them.

THESE SHAPES WERE READ OFF LAUREL'S BUILD (build.py's `built.append(...)`,
`volumes[wall] = ...`, `walls[name] = ...`), because the first draft of this block
described `built` and `volumes` wrongly and a reviewer caught it. They are one model's
shapes. Willow is the second, and its build is the test of whether they generalize.

The second batch (trim, fixtures, furniture, canopy, condenser) needs builder
helpers (`room_faces`, `_pt`, `_stacks`...) that move with it, so it is not here.
"""
import math

import bpy

from adu_kit.kernel import world_bbox
from adu_kit.specread import axis as _axis, sign as _sign

# BOOKKEEPING, NOT DIMENSIONS: tolerances and counts about meshes and arithmetic,
# moved here from build.py with their comments. build.py imports them from here, so
# the number lives once.

VOL_TOL = 1e-4          # cu ft; a boolean that removes nothing is off by whole feet
MESH_TOL = 1e-5         # ft, reading a length back off a mesh: Blender stores vertices as float32, so a value laid down as 8.0 comes back as 7.9999998
SASH_FRAME_MEMBERS = 4  # jambs, sill and head: the four every frame has, whatever its type
VERTS_PER_BOX = 8       # how a welded member count is read back off a mesh
CORNER_TOL = 1e-4       # ft, matching a boolean's output vertex to the cut it came from


def frame_not_mirrored(spec, geo):
    """D and E sit at the X 24 end; the C windows at X 0.

    A-2.0's SIDE (LEFT) ELEVATION draws D and E, and the building's left side
    seen from the front is +X when the front faces +Y and Z is up. That is the
    fact the first draft of this spec had backwards, so it is written here
    rather than read from the spec.

    IT MEASURES THE WALL, NOT ITS NAME. The first version compared
    `o["wall"]` against the string "Wall_x24" -- which is a label this same
    file assigned a few hundred lines earlier, so the gate could only ever
    agree with itself. Review asked what would happen if the two end walls
    were built in each other's places: the answer, reproduced before this was
    changed, is that the model came out mirrored and the anti-mirroring gate
    reported PASS. A gate derived from the build's own expression cannot
    disagree with the build (rule 29), so this one asks the geometry where
    the wall actually is.
    """
    W = geo["W"]
    wrong = []
    for o in geo["built"]:
        ty = str(o["row"].get("type"))
        if ty not in ("C", "D", "E"):
            continue
        lo, hi = world_bbox([geo["walls"][o["wall"]]])
        end_wall = (hi[0] - lo[0]) < W / 2          # thin in X: an end wall
        at_x_max = (lo[0] + hi[0]) / 2 > W / 2
        where = f"x {lo[0]:.3f}..{hi[0]:.3f}"
        if ty in ("D", "E") and not (end_wall and at_x_max):
            wrong.append(f"{o['id']} ({ty}) is on a wall at {where}, not the X {W:g} end")
        if ty == "C" and end_wall and at_x_max:
            wrong.append(f"{o['id']} (C) is on the end wall at {where}, the X {W:g} end")
    return not wrong, "; ".join(wrong)


def footprint(spec, geo):
    """The shell measures what the envelope says, to face of stud.

    THERE WAS NO SUCH GATE. The barn cabin's first one is its footprint, and
    Laurel had nothing equivalent: building the rear wall a foot short left
    the building the wrong size with all nine gates green, because the only
    span being checked was the ROOF's -- and the roof is laid out from W
    directly, so it does not move when the shell does. Found reviewing my own
    work after the third Copilot pass.

    EACH WALL IS MEASURED, NOT THE UNION. The first version took one bounding
    box over all four and compared its span, which is blind to exactly the
    defect it was written for: a rear wall built a foot short still leaves the
    other three reaching X 0 and X 24, so the union never moves. Caught by the
    perturbation that was meant to prove the gate -- the gate failed to fail.
    """
    W, D = geo["W"], geo["D"]
    t = geo["t"]
    want = {"Wall_rear":  ((0.0, W), (0.0, t)),
            "Wall_front": ((0.0, W), (D - t, D)),
            "Wall_x0":    ((0.0, t), (0.0, D)),
            "Wall_x24":   ((W - t, W), (0.0, D))}
    wrong = []
    for name, (xs, ys) in want.items():
        ob = geo["walls"].get(name)
        if ob is None:
            wrong.append(f"{name} was never built")
            continue
        lo, hi = world_bbox([ob])
        for axis, (want_lo, want_hi) in ((0, xs), (1, ys)):
            if abs(lo[axis] - want_lo) > MESH_TOL or abs(hi[axis] - want_hi) > MESH_TOL:
                wrong.append(f'{name} {"XY"[axis]} measures {lo[axis]:.4f}..{hi[axis]:.4f}, '
                             f'the envelope puts it at {want_lo:.4f}..{want_hi:.4f}')
    return not wrong, "; ".join(wrong)


def every_partition_built(spec, geo):
    """Each partition the spec declares exists, and sits where it says.

    Dropping P_bath_W -- the wall between the bath and the kitchen -- left all
    nine gates green, because the volume and corner checks only reach walls
    that carry an opening and that one carries none. Reproduced. So the
    partitions are counted, and each one's measured extents are compared with
    the faces the spec gives it, which also catches one built in the wrong
    place rather than merely missing.
    """
    layout = spec["interior_partitions"]["layout"]
    thick = layout["thickness"]["ft"]
    wrong = []
    for row in layout["partitions"]:
        ob = bpy.data.objects.get(row["id"])
        if ob is None:
            wrong.append(f"{row['id']} was never built")
            continue
        near = row["at_ft"]
        far = near + thick if _sign(row["id"], row["studs_toward"]) > 0 else near - thick
        across = sorted((near, far))
        along = sorted((row["from_ft"], row["to_ft"]))
        lo, hi = world_bbox([ob])
        # a wall running along X is thin in Y, and the other way round
        ai, ci = (0, 1) if _axis(row["id"], row["runs_along"]) == "X" else (1, 0)
        for axis, (want_lo, want_hi), what in ((ci, across, "thickness"),
                                               (ai, along, "run")):
            if abs(lo[axis] - want_lo) > MESH_TOL or abs(hi[axis] - want_hi) > MESH_TOL:
                wrong.append(f"{row['id']} {what} measures {lo[axis]:.4f}..{hi[axis]:.4f}, "
                             f"the spec puts it at {want_lo:.4f}..{want_hi:.4f}")
    return not wrong, "; ".join(wrong)


def openings_on_the_wall_their_block_names(geo):
    """Each exterior opening sits on the wall its spec block is named for.

    Review asked what happens if a build routes the C windows to a front or
    rear wall: `_frame_not_mirrored` only rejects C at the +X end, so an
    end-wall window moved to the rear passed. Reproduced by routing
    `end_wall_x0` at `Wall_rear` -- the gate said PASS.

    The literal fix suggested, requiring every C to be on the X 0 end wall,
    WOULD FAIL THIS BUILDING: W-C3 is a C window and A-1.0 draws it on the
    rear wall, in the `rear_wall` block. C is a size and an operation, not a
    location. So the rule is per opening rather than per type -- each one has
    to be on a wall whose geometry matches the block that lists it, which
    catches the reported case and every other misrouting with it.
    """
    W, D = geo["W"], geo["D"]
    # block -> (axis the wall is thin on, which end of that axis, its length)
    sides = {"front_wall": (1, "max", D), "rear_wall": (1, "min", D),
             "end_wall_x0": (0, "min", W), "end_wall_x24": (0, "max", W)}
    wrong = []
    for o in geo["built"]:
        side = sides.get(o.get("block"))
        if side is None:
            continue                       # an interior door names a partition
        axis, end, span = side
        lo, hi = world_bbox([geo["walls"][o["wall"]]])
        thin = (hi[axis] - lo[axis]) < span / 2
        at_max = (lo[axis] + hi[axis]) / 2 > span / 2
        if not thin or at_max != (end == "max"):
            name = "XY"[axis]
            wrong.append(f"{o['id']} is listed under {o['block']} but sits on "
                         f"{o['wall']}, {name} {lo[axis]:.3f}..{hi[axis]:.3f}")
    return not wrong, "; ".join(wrong)


def every_row_built(spec, geo):
    """The exit gate PLAN.md sets for #129.

    Every row of both schedules is either built with a sash or a leaf, or is
    the 1-bedroom option this model does not build. A window TYPE counts by
    its drawn instances, not by the schedule's count column: the schedule
    counts one B and the plan draws two (spec.discrepancies)."""
    names = {o.name for o in bpy.data.objects}
    missing = []
    for o in geo["built"]:
        kind = "Sash" if o["id"].startswith("W-") else "Leaf"
        if f"{kind}_{o['id']}" not in names:
            missing.append(f"{o['id']} has no {kind.lower()}")
    # WHAT EACH WALL SHOULD HAVE LOST, DERIVED HERE FROM THE OPENING ROWS.
    # Never from the cutter calls: see the note beside `volumes` in build().
    want = {}
    for o in geo["built"]:
        area = (o["a1"] - o["a0"]) * (o["z1"] - o["z0"])
        hosts = [(o["wall"], geo["depths"].get(o["wall"]))]
        for skin in (geo["skin_of"].get(o["wall"]), geo["siding_of"].get(o["wall"])):
            if skin:
                hosts.append((skin, geo["depths"].get(skin)))
        for wall, depth in hosts:
            if depth is None:
                missing.append(f"{o['id']} was never cut into {wall}")
                continue
            want[wall] = want.get(wall, 0.0) + area * depth
    for wall, (before, after) in geo["volumes"].items():
        got = before - after
        expected = want.get(wall, 0.0)
        if abs(got - expected) > VOL_TOL:
            missing.append(f"{wall} lost {got:.4f} cu ft, its openings are {expected:.4f}")

    # AND EACH HOLE IS WHERE ITS ROW SAYS. Volume alone is a total: a cutter
    # shifted along a wall removes the same amount from the same wall and the
    # sum never moves. So every opening's four corners must exist as vertices
    # in the wall that carries it, which is the barn cabin's CORNERS test.
    for o in geo["built"]:
        ob = bpy.data.objects.get(o["wall"])
        if ob is None:
            continue
        axis = 0 if o["along"] == "x" else 1
        seen = [(v.co[axis], v.co[2]) for v in ob.data.vertices]
        for a in (o["a0"], o["a1"]):
            for z in (o["z0"], o["z1"]):
                if not any(abs(sa - a) <= CORNER_TOL and abs(sz - z) <= CORNER_TOL
                           for sa, sz in seen):
                    missing.append(f"{o['id']}: {o['wall']} has no corner at "
                                   f"({a:.4f}, {z:.4f})")
    marks_built = {str(o["row"].get("type")) for o in geo["built"]}
    for d in spec["openings"]["door_types"]["types"]:
        if d.get("option"):
            continue
        if str(d["mark"]) not in marks_built:
            missing.append(f"door schedule row {d['mark']} was never built")
    for w in spec["openings"]["window_types"]["types"]:
        if w["mark"] not in marks_built:
            missing.append(f"window schedule row {w['mark']} was never built")
    return not missing, "; ".join(missing)


def sash_members(spec, geo):
    """A SASH IS NOT A PLATE, and this is what tells them apart.

    The first version of this build filled every opening with one rectangle
    centred in the wall. It satisfied "every schedule row produced a cut
    opening with a sash" perfectly, because the gate only asked whether an
    object existed -- which is the same defect the barn cabin carried for
    eleven PRs while its spec typed every window.

    So count the members, and count the ones the OPERATION implies: four for
    the frame, one mullion between each pair of units, and a meeting rail in
    each unit for a type that has one. Window E is the only slider, so it is
    the only one that should carry five.
    """
    wt = {w["mark"]: w for w in spec["openings"]["window_types"]["types"]}
    ops = spec["windows"]["operations"]
    bad = []
    for o in geo["built"]:
        if not o["id"].startswith("W-"):
            continue
        op = ops[wt[o["row"]["type"]]["operation"]]
        want = (SASH_FRAME_MEMBERS + (op["units"] - 1)
                + (op["units"] if op["meeting_rail"] else 0))
        ob = bpy.data.objects.get(f"Sash_{o['id']}")
        if ob is None:
            bad.append(f"{o['id']} has no sash at all")
            continue
        got = len(ob.data.vertices) // VERTS_PER_BOX
        if got != want:
            bad.append(f"{o['id']} ({wt[o['row']['type']]['operation']}) has "
                       f"{got} member(s), its operation implies {want}")
    return not bad, "; ".join(bad)


def trim_inside_its_walls(spec, geo):
    """Interior trim stays between the exterior walls' inside faces, and no
    trim, inside or out, rises above the walls' head where it stands. The head is
    the CEILING's (#167): here the ceiling follows the roof, so it is the roof
    underside, and a model with a flat ceiling gets that ceiling's height."""
    W, D, t, ceiling = geo["W"], geo["D"], geo["t"], geo["ceiling"]
    wrong = []
    for ob in geo["trim"] + geo["siding"]:
        inside = not ob.name.startswith("Trim_ext_siding_")
        for v in ob.data.vertices:
            x, y, z = ob.matrix_world @ v.co
            if inside and not (t - MESH_TOL <= x <= W - t + MESH_TOL
                               and t - MESH_TOL <= y <= D - t + MESH_TOL and z >= -MESH_TOL):
                wrong.append(f"{ob.name} reaches ({x:.3f}, {y:.3f}, {z:.3f}), outside the rooms")
                break
            if ceiling.covers_y(y) and z > ceiling.under_y(y) + MESH_TOL:
                wrong.append(f"{ob.name} reaches z {z:.3f} at y {y:.3f}, above the ceiling "
                             f"at {ceiling.under_y(y):.3f}")
                break
    return not wrong, "; ".join(wrong)


def no_degenerate():
    import math
    bad = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for v in ob.data.vertices:
            if any(math.isnan(c) or math.isinf(c) for c in v.co):
                bad.append(ob.name)
                break
        if not ob.data.polygons:
            bad.append(f"{ob.name} (no faces)")
    return not bad, ", ".join(sorted(set(bad)))
