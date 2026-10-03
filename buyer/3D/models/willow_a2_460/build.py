"""
build.py -- parametric model of the Sacramento A2 "Willow" 460sf ADU (#172).

Reads spec.yaml. CONTAINS NO BUILDING DIMENSION. Every length, height and offset is read from
the spec; the only literals are geometric constants (2 for halving) and mesh bookkeeping, and
test_build_literals.py holds the file to that.

Run:
    blender --background --python-exit-code 1 --python models/willow_a2_460/build.py -- [--out DIR]
                                                                  [--no-openings]

Coordinate system (feet, Blender +Z up) -- spec.frame, and verify_spec.py enforces it. It is
Laurel's: Willow's A-1.0 is laid out the same way.

    X  0 .. 24      X 0 is the LIVING end (grid B, SIDE (RIGHT) ELEVATION); X 24 is the
                    KITCHEN and BATH end (grid A, SIDE (LEFT) ELEVATION).
    Y  0 .. 19'-2"  rear wall .. front (entry, porch) wall. The front faces +Y.
    Z  0            finished floor; grade is below it.

Both are FACES OF STUD, which is what A-1.0 dimensions to. The cladding is modelled at zero
thickness on purpose (spec.construction.exterior_wall.cladding_modelled).

THIS SLICE BUILDS: the slab, the four exterior walls to the plate, the sheathing skin on each,
the seven interior partitions to the (flat) ceiling, and every opening in the two schedules cut
with a sash or a leaf. NOT YET: the two roofs and the gable ends above the plate, and the porch's
posts and beam (the next slices of #172); and Tier B (trim, finishes, fixtures, furniture).

WILLOW'S CEILING IS FLAT AT THE PLATE, AN ASSUMPTION the spec says so about (roof.ceiling.settled
is false): the walls and partitions ask the CEILING for their head, as Laurel's ask it, and the
ceiling is `Flat` where Laurel's follows the roof (adu_kit/roof.py, #167 and #172).
"""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parents[1]))          # buyer/3D, where adu_kit lives
from adu_kit.kernel import (  # noqa: E402
    load_spec, box, box_geom, weld, multibox, sash_geom, difference, collection, world_bbox, ft,
)
from adu_kit.roof import ceiling_from_spec  # noqa: E402
from adu_kit.rectangle import partition_band  # noqa: E402
from adu_kit.gatelog import GateLog  # noqa: E402
from adu_kit.specread import axis as _axis  # noqa: E402
from adu_kit.gates import (  # noqa: E402
    MESH_TOL, every_partition_built, every_row_built, footprint, no_degenerate,
    openings_on_the_wall_their_block_names, sash_members)

LOG = GateLog()
FAILED, SKIPPED = LOG.failed, LOG.skipped
gate, skip = LOG.gate, LOG.skip

# BOOKKEEPING, NOT DIMENSIONS. Each of these is about meshes, arithmetic or printing; none is a
# length off a sheet. They are gathered here so test_build_literals.py can hold the rest of the
# file to zero.
CUT_MARGIN = 1.0        # ft a cutter stands proud of the wall, so no face is coplanar
RULE = 76               # characters across, for the printed report
AXIS_X = 0              # index of X in a vertex or a bounding-box corner
AXIS_Y = 1              # index of Y in a vertex or a bounding-box corner

# the exterior wall each opening block belongs to, and the object that is its wall
EXTERIOR = [("front_wall", "Wall_front", "x0", "x1", "x"),
            ("rear_wall", "Wall_rear", "x0", "x1", "x"),
            ("end_wall_x0", "Wall_x0", "y0", "y1", "y"),
            ("end_wall_x24", "Wall_x24", "y0", "y1", "y")]


def _wall_band(walls, wall, along):
    """The depth band a wall occupies, so a sash can sit inside its opening."""
    bb = world_bbox([walls[wall]])
    return (bb[0][1], bb[1][1]) if along == "x" else (bb[0][0], bb[1][0])


def _volume(ob):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = bm.calc_volume(signed=False)
    bm.free()
    return v


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build(spec, cut_openings=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "IMPERIAL"
    bpy.context.scene.unit_settings.length_unit = "FEET"

    env, rf, con = spec["envelope"], spec["roof"], spec["construction"]
    W = env["width"]["ft"]                       # X 0 .. W
    D = env["depth"]["ft"]                       # Y 0 .. D
    t = con["exterior_wall"]["stud_depth"]["ft"]
    it = spec["interior_partitions"]["layout"]["thickness"]["ft"]
    sheath = con["exterior_wall"]["sheathing"]["ft"]
    slab_t = con["foundation"]["slab"]["thickness"]["ft"]
    # THE ROOF AND THE CEILING ARE TWO THINGS (#167). Walls and partitions run to the CEILING.
    # Willow's is flat at the plate (spec.roof.ceiling), so every wall asks one number.
    ceiling = ceiling_from_spec(rf["ceiling"])

    shell = collection("Shell")
    partitions = collection("Partitions")
    roof_coll = collection("Roof")
    openings = collection("Openings")
    site = collection("Site")

    # ---- slab ------------------------------------------------------------
    # Slab on grade: its top IS the finished floor, so it sits below Z 0.
    box("Slab", 0.0, W, 0.0, D, -slab_t, 0.0, site)

    # ---- exterior walls ---------------------------------------------------
    # Each wall runs from the slab to the ceiling. The gable ends will rise above the plate to
    # the roof's underside when the roof is built; until then every wall is a box.
    head = ceiling.under_y(0.0)
    walls = {}
    walls["Wall_rear"] = box("Wall_rear", 0.0, W, 0.0, t, 0.0, head, shell)
    walls["Wall_front"] = box("Wall_front", 0.0, W, D - t, D, 0.0, head, shell)
    walls["Wall_x0"] = box("Wall_x0", 0.0, t, 0.0, D, 0.0, head, shell)
    walls["Wall_x24"] = box("Wall_x24", W - t, W, 0.0, D, 0.0, head, shell)

    # The modelled exterior surface: face of stud plus sheathing, the cladding carried as a
    # material (cladding_modelled is zero, and says why). ONE OBJECT PER WALL, not one skin: an
    # opening's cutter spans its wall's whole depth, so a single wrapped skin would be punched
    # through on the far side as well.
    skin_of = {}
    if sheath:
        faces = {
            "Wall_rear":  box_geom(-sheath, W + sheath, -sheath, 0.0, 0.0, head),
            "Wall_front": box_geom(-sheath, W + sheath, D, D + sheath, 0.0, head),
            "Wall_x0":    box_geom(-sheath, 0.0, 0.0, D, 0.0, head),
            "Wall_x24":   box_geom(W, W + sheath, 0.0, D, 0.0, head),
        }
        for wall, geom in faces.items():
            name = wall.replace("Wall_", "Sheathing_")
            walls[name] = weld(name, [geom], shell)
            skin_of[wall] = name

    # ---- interior partitions ---------------------------------------------
    layout = spec["interior_partitions"]["layout"]
    for row in layout["partitions"]:
        lo, hi = partition_band(row, it)
        a, b = sorted((row["from_ft"], row["to_ft"]))
        top = ceiling.under_y(lo)
        if _axis(row["id"], row["runs_along"]) == "X":
            walls[row["id"]] = box(row["id"], a, b, lo, hi, 0.0, top, partitions)
        else:
            walls[row["id"]] = box(row["id"], lo, hi, a, b, 0.0, top, partitions)

    # ---- openings ---------------------------------------------------------
    cut_by_wall = {}
    depths = {}             # wall -> the thickness a cut passes through
    sashes = []

    def cutter(name, wall, a0, a1, z0, z1, along, depth=None):
        """A hole through `wall`, spanning a0..a1 along the wall and z0..z1 up. The cutter is
        padded through the wall's whole depth, plus a margin, so the boolean removes material
        rather than imprinting edges on a coplanar face. WITH --no-openings IT BUILDS NOTHING:
        `difference()` is what deletes a cutter, so cutters left standing would plug the holes."""
        if not cut_openings:
            return None
        ob = walls[wall]
        bb = world_bbox([ob])
        pad = (bb[1][1] - bb[0][1]) if along == "x" else (bb[1][0] - bb[0][0])
        pad = max(pad, CUT_MARGIN)
        if along == "x":
            depth = (bb[1][1] - bb[0][1]) if depth is None else depth
            c = box(name, a0, a1, bb[0][1] - pad, bb[1][1] + pad, z0, z1, openings)
        else:
            depth = (bb[1][0] - bb[0][0]) if depth is None else depth
            c = box(name, bb[0][0] - pad, bb[1][0] + pad, a0, a1, z0, z1, openings)
        cut_by_wall.setdefault(wall, []).append(c)
        depths[wall] = depth
        return c

    wt = {w["mark"]: w for w in spec["openings"]["window_types"]["types"]}
    dt = {str(d["mark"]): d for d in spec["openings"]["door_types"]["types"]}

    built = []
    for block, wall, lo, hi, along in EXTERIOR:
        for row in spec["openings"][block]["openings"]:
            a0, a1 = row[lo], row[hi]
            if row["id"].startswith("W-"):
                ty = wt[row["type"]]
                z0 = ty["sill"]["ft"]
                z1 = z0 + ty["height"]["ft"]
            else:
                ty = dt[str(row["type"])]
                z0 = 0.0
                z1 = ty["height"]["ft"]
            cutter(f"cut_{row['id']}", wall, a0, a1, z0, z1, along)
            built.append(dict(id=row["id"], wall=wall, a0=a0, a1=a1,
                              z0=z0, z1=z1, along=along, row=row, block=block))

    for d in layout["door_openings"]:
        ty = dt[str(d["type"])]
        along = "x" if d["along"] == "X" else "y"
        cutter(f"cut_{d['id']}", d["in"], d["a_ft"], d["b_ft"], 0.0, ty["height"]["ft"], along)
        built.append(dict(id=d["id"], wall=d["in"], a0=d["a_ft"], a1=d["b_ft"],
                          z0=0.0, z1=ty["height"]["ft"], along=along, row=d))

    # the skin gets every exterior hole too, or the windows are blind from outside
    for o in list(built):
        if o["wall"] in skin_of:
            cutter(f"cut_skin_{o['id']}", skin_of[o["wall"]], o["a0"], o["a1"],
                   o["z0"], o["z1"], o["along"], depth=sheath)

    # THE OPENING GATE IS A VOLUME GATE: a boolean that imprints edges without removing material
    # leaves corners and a face count that look right, and only the volume shows it. Only the
    # MEASUREMENTS are recorded here; what they should be is derived in the gate, from the
    # opening rows, never from the build's own expression.
    volumes = {}
    if cut_openings:
        for wall, cl in cut_by_wall.items():
            before = _volume(walls[wall])
            difference(walls[wall], cl)
            volumes[wall] = (before, _volume(walls[wall]))

    # ---- sashes and leaves ------------------------------------------------
    # Every opening gets what it is: a window gets a sash, a door gets a leaf. An opening with
    # nothing in it reads as a hole in a wall, and the gate counts them.
    win = spec["windows"]
    f2g = win["frame_to_glass"]["ft"]
    proud = win["proud_of_glass"]["ft"]
    mull = win["mullion"]["ft"]
    ops = win["operations"]
    leaf_t = spec["openings"]["door_types"]["leaf_thickness"]["ft"]

    def _glazed(name, along, plane, a0, a1, z0, z1, operation):
        """A sash, from the OPERATION the schedule declares. An operation the spec does not
        define is a readable failure, not a guess."""
        op = ops.get(operation)
        if op is None:
            raise SystemExit(
                f"{name} is operated {operation!r}, which spec.windows.operations does not "
                f"define (have {sorted(ops)}). A window cannot be built from an operation alone.")
        if op["meeting_rail"]:
            rail = win.get("meeting_rail")
            if rail is None:
                raise SystemExit(f"operation {operation!r} declares a meeting rail and "
                                 "spec.windows.meeting_rail does not say where it sits.")
            at, thick = rail["ratio"], rail["thickness"]["ft"]
        else:
            at, thick = None, 0.0
        parts = sash_geom(along, plane, a0, a1, z0, z1, f2g, proud,
                          units=op["units"], meeting_rail_at=at,
                          meeting_rail_thickness=thick, mullion=mull)
        return multibox(name, parts, openings)

    for o in built:
        lo, hi = _wall_band(walls, o["wall"], o["along"])
        plane = (lo + hi) / 2                 # spec.windows.glazing_plane: the wall's centre
        row, along = o["row"], o["along"]
        if o["id"].startswith("W-"):
            # The cut is the ROUGH OPENING (x0/x1); the sash is the window UNIT. They are the
            # same for every window but B, whose spec carries both spans (unit_x0/unit_x1).
            u0, u1 = row.get("unit_x0", o["a0"]), row.get("unit_x1", o["a1"])
            sashes.append(_glazed(f"Sash_{o['id']}", along, plane, u0, u1, o["z0"], o["z1"],
                                  wt[row["type"]]["operation"]))
            continue
        d0, d1 = plane - leaf_t / 2, plane + leaf_t / 2
        spec_box = ((o["a0"], o["a1"], d0, d1, o["z0"], o["z1"]) if along == "x"
                    else (d0, d1, o["a0"], o["a1"], o["z0"], o["z1"]))
        sashes.append(multibox(f"Leaf_{o['id']}", [spec_box], openings))

    geo = dict(W=W, D=D, t=t, it=it, ceiling=ceiling, walls=walls,
               built=built, sashes=sashes, volumes=volumes, cut=cut_openings,
               depths=depths, skin_of=skin_of, siding_of={}, trim=[], siding=[])
    return geo, dict(Shell=shell, Partitions=partitions, Roof=roof_coll,
                     Openings=openings, Site=site)


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------
def report(spec, geo, colls):
    env, lv = spec["envelope"], spec["levels"]
    # THE GATES' ENVELOPE IS READ FROM THE SPEC HERE, NOT FROM THE BUILD'S OWN RECORD. build() puts the W, D, t
    # and it it BUILT WITH into geo, and the gates (the kit's footprint among them) used to read them back, so a
    # wrong key in build() (D read from the width, say) moved the gates' expectation with the geometry and every
    # gate agreed with the mistake (review of #182). These lookups are written separately, so a slip in one
    # place shows against the other. `geo` is rebound for everything below.
    geo = dict(geo, W=env["width"]["ft"], D=env["depth"]["ft"],
               t=spec["construction"]["exterior_wall"]["stud_depth"]["ft"],
               it=spec["interior_partitions"]["layout"]["thickness"]["ft"])
    W, D = geo["W"], geo["D"]
    print("=" * RULE)
    print('Willow A2 460sf -- slab, walls, partitions and openings (#172)')
    print("=" * RULE)

    shell = [o for o in bpy.data.objects if o.name.startswith(("Wall_", "Sheathing"))]
    bb = world_bbox(shell)
    print("\nBounding box, walls:")
    for i, ax in enumerate("XYZ"):
        print(f"  {ax} {bb[0][i]:8.3f} .. {bb[1][i]:8.3f}   span {bb[1][i] - bb[0][i]:7.3f} ft")

    print("\nGATES")

    ok, why = footprint(spec, geo)
    gate(ok, f'the shell is {ft(W)} x {ft(D)} to face of stud', why)

    ok, why = _walls_to_the_plate(spec, geo)
    gate(ok, f'the walls and partitions run from the slab to the plate, T.P. {ft(lv["top_of_plate"]["ft"])}', why)

    ok, why = _slab_is_the_footprint(spec, geo)
    gate(ok, "the slab is the building's footprint, X 0..W and Y 0..D", why)

    ok, why = _sheathing_on_every_wall(spec, geo)
    gate(ok, "every exterior wall carries its sheathing skin, outside its face of stud", why)

    ok, why = every_partition_built(spec, geo)
    gate(ok, "every partition in the spec was built, where the spec puts it", why)

    ok, why = _frame_not_mirrored(spec, geo)
    gate(ok, "not mirrored: every opening is on the wall A-2.0's elevations draw its mark on", why)

    label = "every schedule row produced a cut opening with a sash or a leaf"
    if geo["cut"]:
        ok, why = every_row_built(spec, geo)
        gate(ok, label, why)
    else:
        skip(label, "--no-openings: nothing was cut, so there is no volume to measure")

    ok, why = openings_on_the_wall_their_block_names(geo)
    gate(ok, "every exterior opening is on the wall its spec block names", why)

    ok, why = sash_members(spec, geo)
    gate(ok, "every sash carries the members its declared operation implies", why)

    ok, why = _built_openings_are_the_spec_rows(spec, geo)
    gate(ok, "every opening was built to the spec's own row: the same ids, walls, spans and heights", why)

    ok, why = _sashes_and_leaves_in_their_openings(spec, geo)
    gate(ok, "every sash and leaf sits in its opening: its span along the wall, its height and its wall plane", why)

    ok, why = _window_b_unit_in_its_rough_opening(spec, geo)
    gate(ok, "window B's sash is its 1'-6\" unit, centred in the 1'-7\" rough opening the wall is cut to", why)

    ok, why = no_degenerate()
    gate(ok, "no NaN or degenerate geometry", why)

    print("=" * RULE)
    if SKIPPED:
        # A SKIPPED GATE IS NOT A PASSING BUILD; --no-openings is a diagnostic and has not
        # earned a success.
        print(f"{len(SKIPPED)} gate(s) SKIPPED, not passed: " + "; ".join(SKIPPED))
        print("This model is not complete. Re-run without --no-openings to judge them.")
    return not FAILED and not SKIPPED


def _walls_to_the_plate(spec, geo):
    """The walls and partitions are as tall as the plate, and the slab's top is the floor.

    Willow's ceiling is flat at the plate (spec.roof.ceiling, an assumption), so every shell wall,
    its skin and every partition tops out at T.P. The slab sits below the finished floor.
    """
    plate = spec["levels"]["top_of_plate"]["ft"]
    slab_t = spec["construction"]["foundation"]["slab"]["thickness"]["ft"]
    wrong = []
    for name, ob in geo["walls"].items():
        lo, hi = world_bbox([ob])
        if abs(lo[2]) > MESH_TOL or abs(hi[2] - plate) > MESH_TOL:
            wrong.append(f"{name} runs {lo[2]:.4f}..{hi[2]:.4f}, the slab to the plate is 0..{plate}")
    slab = bpy.data.objects.get("Slab")
    if slab is None:
        wrong.append("the slab was never built")
    else:
        lo, hi = world_bbox([slab])
        if abs(hi[2]) > MESH_TOL or abs(lo[2] + slab_t) > MESH_TOL:
            wrong.append(f"the slab runs {lo[2]:.4f}..{hi[2]:.4f}, its top is the floor, {slab_t} thick")
    return not wrong, "; ".join(wrong)


def _slab_is_the_footprint(spec, geo):
    """The slab covers the envelope, to face of stud: X 0..W and Y 0..D.

    `footprint()` measures the four wall objects, and `_walls_to_the_plate` measures the slab only
    in Z, so a slab built a foot short on one side passed every gate (review of #182). The slab is
    the floor the partitions stand on and the model's footprint on the ground.
    """
    slab = bpy.data.objects.get("Slab")
    if slab is None:
        return False, "the slab was never built"
    lo, hi = world_bbox([slab])
    wrong = []
    for axis, span in ((AXIS_X, geo["W"]), (AXIS_Y, geo["D"])):
        if abs(lo[axis]) > MESH_TOL or abs(hi[axis] - span) > MESH_TOL:
            wrong.append(f"the slab measures {'XY'[axis]} {lo[axis]:.4f}..{hi[axis]:.4f}, "
                         f"the envelope is 0..{span:.4f}")
    return not wrong, "; ".join(wrong)


def _sheathing_on_every_wall(spec, geo):
    """Each of the four walls has its sheathing skin, the spec's thickness thick, just outside it.

    The skins are the modelled exterior surface. `every_row_built` expects skin cuts only for the skins
    `skin_of` lists, so a build that never made them listed none, expected none, and passed every gate
    (review of #182). Read from the SCENE by name, never from `geo`, and held to the spec: a skin must
    exist for each wall, and stand sheath thick beyond the wall's own outer face.
    """
    sheath = spec["construction"]["exterior_wall"]["sheathing"]["ft"]
    if not sheath:
        return True, ""
    W, D = geo["W"], geo["D"]
    # each skin's whole plan extent, X then Y, derived from the envelope here: the front and rear skins
    # run the full width PLUS a sheathing at each end (they wrap the end walls' corners), the end skins
    # the full depth. Thickness alone was not enough (review of #182: a rear skin cut to W left its last
    # 3/8 inch bare while every gate passed), so BOTH axes are held for every skin.
    want = {"Sheathing_rear": ((-sheath, W + sheath), (-sheath, 0.0)),
            "Sheathing_front": ((-sheath, W + sheath), (D, D + sheath)),
            "Sheathing_x0": ((-sheath, 0.0), (0.0, D)),
            "Sheathing_x24": ((W, W + sheath), (0.0, D))}
    wrong = []
    for name, spans in want.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            wrong.append(f"{name} was never built")
            continue
        lo, hi = world_bbox([ob])
        for axis, (lo_want, hi_want) in ((AXIS_X, spans[0]), (AXIS_Y, spans[1])):
            if abs(lo[axis] - lo_want) > MESH_TOL or abs(hi[axis] - hi_want) > MESH_TOL:
                wrong.append(f"{name} measures {'XY'[axis]} {lo[axis]:.4f}..{hi[axis]:.4f}, "
                             f"its wall's skin is {lo_want:.4f}..{hi_want:.4f}")
    return not wrong, "; ".join(wrong)


def _frame_not_mirrored(spec, geo):
    """Every exterior opening is cut into the wall the ELEVATIONS draw its mark on.

    Laurel's version of this gate hardcodes its window marks and moved back out of the kit for it
    (#177). This one reads the expectation from the spec (spec.frame.drawn_on, a fact A-2.0's
    elevations state, held to the plan's strings by verify_spec.py) and measures the BUILT wall
    each opening was cut into, so a build that routes a block to the wrong wall, or a spec that
    puts a window on the wrong block, fails here. It FAILS when it has nothing to check.
    """
    drawn = spec["frame"]["drawn_on"]["walls"]
    # THE GATE'S OWN TABLE, not EXTERIOR's: the build routes each block through EXTERIOR, so an
    # expectation read from it moves with a misrouted block and the gate passes the very mistake it
    # exists to catch (a probe routed the X 0 block at the X 24 wall and this gate said PASS).
    block_of = {"front_wall": "Wall_front", "rear_wall": "Wall_rear",
                "end_wall_x0": "Wall_x0", "end_wall_x24": "Wall_x24"}
    W, D, t = geo["W"], geo["D"], geo["t"]
    # the exterior band each wall occupies, as (axis, lo, hi)
    band = {"Wall_front": (AXIS_Y, D - t, D), "Wall_rear": (AXIS_Y, 0.0, t),
            "Wall_x0": (AXIS_X, 0.0, t), "Wall_x24": (AXIS_X, W - t, W)}
    checked, wrong = [], []
    for o in geo["built"]:
        if o.get("block") is None:
            continue
        mark = o["row"]["type"] if o["id"].startswith("W-") else f"door_{o['row']['type']}"
        want_block = drawn.get(mark)
        if want_block is None:
            wrong.append(f"{o['id']}: the elevations draw no wall for {mark!r} (frame.drawn_on)")
            continue
        axis, want_lo, want_hi = band[block_of[want_block]]
        lo, hi = world_bbox([geo["walls"][o["wall"]]])
        checked.append(o["id"])
        if abs(lo[axis] - want_lo) > MESH_TOL or abs(hi[axis] - want_hi) > MESH_TOL:
            wrong.append(f"{o['id']} ({mark}) is cut into {o['wall']}, {'XY'[axis]} "
                         f"{lo[axis]:.3f}..{hi[axis]:.3f}; the elevations draw it on "
                         f"{want_block} ({want_lo:.3f}..{want_hi:.3f})")
    if not checked:
        wrong.append("no exterior opening was available to check, so nothing was held to the elevations")
    return not wrong, "; ".join(wrong)


def _built_openings_are_the_spec_rows(spec, geo):
    """The records the build keeps of its openings ARE the spec's rows.

    `every_row_built` derives each wall's expected volume loss and corners from `geo["built"]`, and the
    sash and leaf gate compares each mesh with the same record, so a build that halved every interior door
    (or shifted every window) in BOTH its cutters and its records passed all of them (review of #182). This
    gate reads the spans from the spec's rows itself: exterior rows by their block, interior doors by
    `a_ft`/`b_ft`, heights from the schedules; the walls from its own table. It also requires the same SET
    of ids, so an opening that was never recorded cannot hide.
    """
    wt = {w["mark"]: w for w in spec["openings"]["window_types"]["types"]}
    dt = {str(d["mark"]): d for d in spec["openings"]["door_types"]["types"]}
    blocks = (("front_wall", "Wall_front", "x0", "x1"), ("rear_wall", "Wall_rear", "x0", "x1"),
              ("end_wall_x0", "Wall_x0", "y0", "y1"), ("end_wall_x24", "Wall_x24", "y0", "y1"))
    want = {}
    for block, wall, lo_key, hi_key in blocks:
        for row in spec["openings"][block]["openings"]:
            if row["id"].startswith("W-"):
                ty = wt[row["type"]]
                z0 = ty["sill"]["ft"]
                z1 = z0 + ty["height"]["ft"]
            else:
                z0, z1 = 0.0, dt[str(row["type"])]["height"]["ft"]
            want[row["id"]] = (wall, row[lo_key], row[hi_key], z0, z1)
    for d in spec["interior_partitions"]["layout"]["door_openings"]:
        want[d["id"]] = (d["in"], d["a_ft"], d["b_ft"], 0.0, dt[str(d["type"])]["height"]["ft"])
    got = {o["id"]: o for o in geo["built"]}
    wrong = []
    for oid in sorted(set(want) - set(got)):
        wrong.append(f"{oid} is in the spec and was never recorded as built")
    for oid in sorted(set(got) - set(want)):
        wrong.append(f"{oid} was built but is not a row of the spec")
    for oid in sorted(set(want) & set(got)):
        wall, a0, a1, z0, z1 = want[oid]
        o = got[oid]
        if o["wall"] != wall:
            wrong.append(f"{oid} was cut into {o['wall']}, the spec puts it in {wall}")
        for what, have, need in (("starts", o["a0"], a0), ("ends", o["a1"], a1),
                                 ("rises from", o["z0"], z0), ("rises to", o["z1"], z1)):
            if abs(have - need) > MESH_TOL:
                wrong.append(f"{oid} {what} {have:.4f}, the spec's row says {need:.4f}")
    return not wrong, "; ".join(wrong)


def _sashes_and_leaves_in_their_openings(spec, geo):
    """Every sash and every leaf is MEASURED in its opening, off its mesh.

    `every_row_built` checks the wall's cut and that a `Sash_`/`Leaf_` object EXISTS, and `sash_members`
    counts boxes, so a sash shifted along its wall, built the wrong height, or set off the wall's centre
    plane, and a leaf of the wrong width, height, thickness or position, all passed (review of #182).
    Each member is held to: its span along the wall (the opening, or window B's unit), its height
    (the schedule's sill to head for a window, the floor to the leaf's height for a door), and its
    thickness band, centred on the wall's centre plane (a sash straddles it by `proud_of_glass` each
    way, a leaf by half its thickness). The expectations are derived HERE from the spec and the
    envelope, not read from the build's own variables.
    """
    W, D, t, it = geo["W"], geo["D"], geo["t"], geo["it"]
    proud = spec["windows"]["proud_of_glass"]["ft"]
    leaf_t = spec["openings"]["door_types"]["leaf_thickness"]["ft"]
    wt = {w["mark"]: w for w in spec["openings"]["window_types"]["types"]}
    dt = {str(d["mark"]): d for d in spec["openings"]["door_types"]["types"]}
    plane_of = {"Wall_front": D - t / 2, "Wall_rear": t / 2, "Wall_x0": t / 2, "Wall_x24": W - t / 2}
    partitions = {r["id"]: r for r in spec["interior_partitions"]["layout"]["partitions"]}
    wrong = []
    for o in geo["built"]:
        window = o["id"].startswith("W-")
        ob = bpy.data.objects.get(("Sash_" if window else "Leaf_") + o["id"])
        if ob is None:
            wrong.append(f"{o['id']} has no {'sash' if window else 'leaf'}")
            continue
        if o["wall"] in plane_of:
            plane = plane_of[o["wall"]]
        elif o["wall"] in partitions:
            lo_p, hi_p = partition_band(partitions[o["wall"]], it)
            plane = (lo_p + hi_p) / 2
        else:
            wrong.append(f"{o['id']} is cut into {o['wall']}, which is neither an exterior wall nor a partition")
            continue
        if window:
            ty = wt[o["row"]["type"]]
            a0, a1 = o["row"].get("unit_x0", o["a0"]), o["row"].get("unit_x1", o["a1"])
            z0 = ty["sill"]["ft"]
            z1 = z0 + ty["height"]["ft"]
            half = proud
        else:
            a0, a1 = o["a0"], o["a1"]
            z0, z1 = 0.0, dt[str(o["row"]["type"])]["height"]["ft"]
            half = leaf_t / 2
        along = AXIS_X if o["along"] == "x" else AXIS_Y
        thin = AXIS_Y if along == AXIS_X else AXIS_X
        lo, hi = world_bbox([ob])
        for what, got_lo, got_hi, want_lo, want_hi in (
                ("along the wall", lo[along], hi[along], a0, a1),
                ("in height", lo[2], hi[2], z0, z1),
                ("across the wall", lo[thin], hi[thin], plane - half, plane + half)):
            if abs(got_lo - want_lo) > MESH_TOL or abs(got_hi - want_hi) > MESH_TOL:
                wrong.append(f"{ob.name} measures {got_lo:.4f}..{got_hi:.4f} {what}, "
                             f"its opening wants {want_lo:.4f}..{want_hi:.4f}")
    return not wrong, "; ".join(wrong)


def _window_b_unit_in_its_rough_opening(spec, geo):
    """Window B is built to its unit span, not to the rough opening the wall is cut to.

    The cut is x0/x1 (1'-7"); the sash is unit_x0/unit_x1 (the schedule's 1'-6", centred). Read
    the sash back off the mesh: it must span exactly the unit, and sit inside the cut.
    """
    row = next((o for o in geo["built"] if o["id"] == "W-B1"), None)
    if row is None:
        return False, "W-B1 was never built"
    r = row["row"]
    sash = bpy.data.objects.get("Sash_W-B1")
    if sash is None:
        return False, "W-B1 has no sash"
    lo, hi = world_bbox([sash])
    wrong = []
    if abs(lo[0] - r["unit_x0"]) > MESH_TOL or abs(hi[0] - r["unit_x1"]) > MESH_TOL:
        wrong.append(f"the sash spans X {lo[0]:.4f}..{hi[0]:.4f}, the unit is {r['unit_x0']:.4f}..{r['unit_x1']:.4f}")
    if lo[0] < row["a0"] - MESH_TOL or hi[0] > row["a1"] + MESH_TOL:
        wrong.append(f"the sash spills outside the rough opening {row['a0']:.4f}..{row['a1']:.4f}")
    return not wrong, "; ".join(wrong)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else HERE
    cut = "--no-openings" not in argv

    spec = load_spec(HERE / "spec.yaml")
    geo, colls = build(spec, cut_openings=cut)
    ok = report(spec, geo, colls)

    out.mkdir(parents=True, exist_ok=True)
    dest = out / "willow_a2_460.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    print(f"\nsaved: {dest}")
    if not ok:
        raise SystemExit("one or more gates FAILED")


if __name__ == "__main__":
    main()
