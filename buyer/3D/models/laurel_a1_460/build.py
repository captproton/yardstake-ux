"""
build.py — parametric massing model of the Sacramento A1 "Laurel" 460sf ADU (#129).

Reads spec.yaml. CONTAINS NO BUILDING DIMENSION. Every length, height, slope
and offset is read from the spec; the only literals are geometric constants
(2 for halving, 12 for a pitch denominator) and mesh bookkeeping.

Run:
    blender --background --python-exit-code 1 --python models/laurel_a1_460/build.py -- [--out DIR]
                                                                  [--no-openings]

Coordinate system (feet, Blender +Z up) — spec.frame, and verify_spec.py
enforces it:

    X  0 .. 24      X 0 is the LIVING ROOM end (grid B, SIDE (RIGHT)
                    ELEVATION); X 24 is the KITCHEN and BATH end (grid A,
                    SIDE (LEFT) ELEVATION). Facing the front from outside,
                    X increases to the viewer's LEFT.
    Y  0 .. 19'-2"  rear wall .. front (entry) wall. The front faces +Y.
    Z  0            finished floor; grade is below it.

Both are FACES OF STUD, which is what A-1.0 dimensions to. The cladding is
modelled at zero thickness on purpose — see
spec.construction.exterior_wall.cladding_modelled.

WHAT THIS BUILDS: slab, exterior walls, the seven interior partitions, the
single shed roof with its overhangs, vaulted ceilings that follow the roof,
every opening in the two schedules cut with a sash or a leaf, Tier 1 trim
(#132): casing, stools and baseboard inside, and Tier 2's two exterior
finishes (#133): a stucco skin and a lap-siding skin over the same
sheathing face, the siding with its exterior trim, both UV-mapped for their
textures. The page shows one finish at a time (spec.variants.presence).
And the interior fixtures (#134): the kitchen, bath and laundry, and the
water heater at its maker's published size, where A-1.0 draws them.

And the first equipment outside it (#134, PR C): the mini-split condenser
on its pad, placed under spec.fixtures.condenser.placement_rule.

And the furniture (#135): the barn cabin's arrangements, reused, turned and
placed in the studio as a sleeping area and a sitting area.

And the optional entry canopy (#144): A-3.4's cedar frame, slats and braces,
hung where A-2.0 draws it, as a collection of its own a buyer can switch.

WHAT IT DOES NOT: the mini-split's indoor unit, which no sheet draws, and
the 1-bedroom option (a configurator variant, spec.variants).
"""

import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parents[1]))          # buyer/3D, where adu_kit lives
from adu_kit.kernel import (  # noqa: E402,F401
    load_spec, box, box_geom, prism_geom, weld, multibox, sash_geom,
    difference, collection, world_bbox, mark_reveals, ft, uv_project, tube,
)
from adu_kit.verify_lib import inside_mesh  # noqa: E402
from adu_kit.manifest import face_slots  # noqa: E402
from adu_kit.roof import Plane, Roof, ceiling_for  # noqa: E402

FAILED = []
SKIPPED = []

# BOOKKEEPING, NOT DIMENSIONS. Every one of these is about meshes, arithmetic
# or printing; none is a length off a sheet. They are named and gathered here
# so test_build_literals.py can hold the rest of the file to zero -- the
# done-when PLAN.md sets for #129 is "no dimension literal appears in
# build.py", and a gate is worth more than a promise.
VOL_TOL = 1e-4          # cu ft; a boolean that removes nothing is off by whole feet
LEN_TOL = 1e-6          # ft, for comparing two lengths the spec already agrees on
MESH_TOL = 1e-5         # ft, reading a length back off a mesh: Blender stores vertices as float32, so a value laid down as 8.0 comes back as 7.9999998
CUT_MARGIN = 1.0        # ft a cutter stands proud of the wall, so no face is coplanar
RULE = 76               # characters across, for the printed report
SASH_FRAME_MEMBERS = 4  # jambs, sill and head: the four every frame has, whatever its type
VERTS_PER_BOX = 8       # how a welded member count is read back off a mesh
CORNER_TOL = 1e-4       # ft, matching a boolean's output vertex to the cut it came from
INCHES_PER_FOOT = 12    # unit arithmetic, for a spec tolerance given in inches and a report that prints them
UP = 0.9                # a face whose normal's Z exceeds this faces up: the slab's top
SPAN_PLACES = 4         # decimal places openings are compared to when grouping a window with its transom; the spec writes feet to 4
WH_SIDES = 24           # the water heater's cylinder: faces round it, so its flats sit within 1% of the published diameter
FACE_TOL = 0.01         # ft; a fixture side drawn this close past a finished face is still "drawn to the finished face"
MIN_RUN = 1e-3          # ft; a baseboard run shorter than this is a sliver where a casing meets a corner, not a run


def gate(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def skip(label, why):
    """A gate that CANNOT be judged on this run, said out loud.

    `--no-openings` builds an uncut model on purpose, and the opening gate
    read its evidence from the volumes recorded while cutting. With no cuts
    that mapping is empty, every loop over it runs zero times, and the gate
    printed PASS on a model with no openings in it at all. A gate with
    nothing to look at has not passed; it has not run.
    """
    print(f"  [SKIP] {label} -- {why}")
    SKIPPED.append(label)


# ---------------------------------------------------------------------------
# reading the spec, which is untrusted input like any other file (rule 25)
# ---------------------------------------------------------------------------
# A SPEC IS READ, NOT OBEYED. Both of these used to be `startswith("+")` and
# `== "X"` with an else, so `studs_toward: north` built the wall on the
# negative side and `runs_along: Z` rotated it, both in silence and both
# producing a model that the envelope and door gates would go on to bless.
# Review asked what a malformed value does; the answer was "something", and
# the answer has to be "a readable failure".
AXES = ("X", "Y")
DIRECTIONS = {"+X": +1, "-X": -1, "+Y": +1, "-Y": -1}


def _axis(who, value):
    if value not in AXES:
        raise SystemExit(f"{who}: runs_along is {value!r}, which is not one of "
                         f"{list(AXES)}. A partition runs along an axis of the frame.")
    return value


def _sign(who, value):
    if value not in DIRECTIONS:
        raise SystemExit(f"{who}: studs_toward is {value!r}, which is not one of "
                         f"{sorted(DIRECTIONS)}. It says which way the studs run "
                         "from the cited face.")
    return DIRECTIONS[value]


# ---------------------------------------------------------------------------
# the roof plane
# ---------------------------------------------------------------------------
def shed_roof(spec):
    """Laurel's roof: a list of ONE plane (adu_kit.roof, #167).

    A-2.0 marks the slope 1" / 1'-0", and it also dimensions T.P. 1 and T.P. 2.
    Those disagree: 19 1/2" over 19'-2" is 1.017" per foot. The PLATE HEIGHTS
    WIN, because they are what the elevations dimension and what #130 gates,
    and because a slope read off a marked ratio would put the front plate
    3/8" below the height four elevations draw.

    The plane runs out over all four overhangs, so asking it for a point on the
    roof's own edge is allowed and asking it for one past the edge is an error.
    This was the `Shed` class, a function of Y alone; the expression is the
    same, so every height is the same float.
    """
    lv, env, ov = spec["levels"], spec["envelope"], spec["roof"]["overhangs"]
    rear = lv["top_of_plate_rear"]["ft"]
    front = lv["top_of_plate_front"]["ft"]
    depth, width = env["depth"]["ft"], env["width"]["ft"]
    slope = (front - rear) / depth
    return Roof([Plane(z0=rear, dz_dx=0.0, dz_dy=slope,
                       x=(-ov["ends"]["ft"], width + ov["ends"]["ft"]),
                       y=(-ov["rear"]["ft"], depth + ov["front"]["ft"]))])


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build(spec, cut_openings=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "IMPERIAL"
    bpy.context.scene.unit_settings.length_unit = "FEET"

    env, lv, rf, con = spec["envelope"], spec["levels"], spec["roof"], spec["construction"]
    W = env["width"]["ft"]                       # X 0 .. W
    D = env["depth"]["ft"]                       # Y 0 .. D
    t = con["exterior_wall"]["stud_depth"]["ft"]
    it = spec["interior_partitions"]["layout"]["thickness"]["ft"]
    sheath = con["exterior_wall"]["sheathing"]["ft"]
    grade = lv["grade"]["ft"]
    slab_t = con["foundation"]["slab"]["ft"]
    # THE ROOF AND THE CEILING ARE TWO THINGS (#167). Walls and partitions run to
    # the CEILING; the roof solid and the roof gates ask the ROOF. Here the ceiling
    # follows the roof (spec.roof.ceiling, A-1.0), so both give the same height,
    # and a model whose ceiling is separate changes this line, not every wall.
    roof_planes = shed_roof(spec)
    ceiling = ceiling_for(rf["ceiling"]["follows"], roof_planes)

    shell = collection("Shell")
    partitions = collection("Partitions")
    roof_coll = collection("Roof")
    openings = collection("Openings")
    site = collection("Site")
    trim_coll = collection("Trim")
    siding_coll = collection("Siding")        # the siding finish: its skins and its trim

    # ---- slab ------------------------------------------------------------
    # Slab on grade: its top IS the finished floor, so it sits below Z 0.
    # The floor finish is a material on that top face (spec.finishes.floor),
    # not a layer, so the face is tagged for materials.face_slots and every
    # height the elevations dimension stays where it is.
    slab = box("Slab", 0.0, W, 0.0, D, -slab_t, 0.0, site)
    floor_slot = _floor_slot(spec)
    for poly in slab.data.polygons:
        if poly.normal.z > UP:
            poly.material_index = floor_slot

    # ---- exterior walls ---------------------------------------------------
    # Each wall runs from the slab to the underside of the roof, so the
    # ceilings follow the roof line (A-1.0, "CEILINGS FOLLOW ROOF LINE") with
    # no separate ceiling plane to keep in step. The end walls rake, so they
    # are prisms in YZ; the front and rear walls are level, so they are boxes.
    walls = {}
    walls["Wall_rear"] = box("Wall_rear", 0.0, W, 0.0, t, 0.0, ceiling.under_y(0.0), shell)
    walls["Wall_front"] = box("Wall_front", 0.0, W, D - t, D, 0.0, ceiling.under_y(D), shell)
    for name, x0, x1 in (("Wall_x0", 0.0, t), ("Wall_x24", W - t, W)):
        profile = [(0.0, 0.0), (D, 0.0), (D, ceiling.under_y(D)), (0.0, ceiling.under_y(0.0))]
        v, f = prism_geom(profile, x0, x1, plane="yz")
        walls[name] = weld(name, [(v, f)], shell)

    # The modelled exterior surface: face of stud plus sheathing, with the
    # cladding carried as a material (cladding_modelled is zero, and says why).
    # ONE OBJECT PER WALL, not one skin. A single welded skin wraps all four
    # sides, and an opening's cutter spans its wall's whole depth -- so a hole
    # in the front would have been punched straight through the rear skin as
    # well. Per-wall objects keep each cut inside the face it belongs to.
    # TWO SKINS PER WALL, ONE PER FINISH (#133). The siding skin is the same
    # solid as the stucco one, in the Siding collection: the page shows one or
    # the other (spec.variants.presence), so they are never drawn together,
    # and lod2's contract keeps the stucco skin alone.
    skin_of, siding_of = {}, {}
    if sheath:
        faces = {
            "Wall_rear":  box_geom(-sheath, W + sheath, -sheath, 0.0, 0.0, ceiling.under_y(0.0)),
            "Wall_front": box_geom(-sheath, W + sheath, D, D + sheath, 0.0, ceiling.under_y(D)),
        }
        rake = [(0.0, 0.0), (D, 0.0), (D, ceiling.under_y(D)), (0.0, ceiling.under_y(0.0))]
        faces["Wall_x0"] = prism_geom(rake, -sheath, 0.0, plane="yz")
        faces["Wall_x24"] = prism_geom(rake, W, W + sheath, plane="yz")
        for wall, geom in faces.items():
            name = wall.replace("Wall_", "Sheathing_")
            walls[name] = weld(name, [geom], shell)
            skin_of[wall] = name
            name = wall.replace("Wall_", "Siding_")
            walls[name] = weld(name, [geom], siding_coll)
            siding_of[wall] = name

    # ---- interior partitions ---------------------------------------------
    layout = spec["interior_partitions"]["layout"]
    for row in layout["partitions"]:
        lo, hi = _partition_band(row, it)
        a, b = sorted((row["from_ft"], row["to_ft"]))
        # EVERY PARTITION IS A YZ PRISM, both orientations, because the roof
        # rises with Y and so does the head of any wall with any extent in Y
        # -- INCLUDING its own thickness. A wall running along X was built as
        # a box capped at ceiling.under_y(lo), which left a triangular gap to the
        # roof on its +Y face: small (0.30" here) but a real hole, and a
        # contradiction of layout.height's "to: roof_underside". Found by
        # review; measured on the built model before it was fixed.
        if _axis(row["id"], row["runs_along"]) == "X":
            profile = [(lo, 0.0), (hi, 0.0), (hi, ceiling.under_y(hi)), (lo, ceiling.under_y(lo))]
            extrude = (a, b)                       # along X
        else:
            profile = [(a, 0.0), (b, 0.0), (b, ceiling.under_y(b)), (a, ceiling.under_y(a))]
            extrude = (lo, hi)                     # across X, at one Y band
        v, f = prism_geom(profile, extrude[0], extrude[1], plane="yz")
        walls[row["id"]] = weld(row["id"], [(v, f)], partitions)

    # ---- the shed roof ----------------------------------------------------
    # One plane, T.P. 1 at the rear to T.P. 2 at the front, carried out over
    # the overhangs. Drawn as a YZ prism so the slope is the geometry rather
    # than a stack of steps, and extruded past both ends by the end overhang.
    asm = rf["assembly"]["modelled_thickness"]["ft"]
    (profile, x0, x1), = roof_planes.yz_solids(asm)   # one plane, so one prism
    v, f = prism_geom(profile, x0, x1, plane="yz")
    roof = weld("Roof_shed", [(v, f)], roof_coll)

    # ---- openings ---------------------------------------------------------
    cut_by_wall = {}
    depths = {}             # wall -> the thickness a cut passes through
    sashes = []

    def cutter(name, wall, a0, a1, z0, z1, along, depth=None):
        """A hole through `wall`, spanning a0..a1 along the wall and z0..z1 up.

        The cutter is padded through the wall's whole depth, plus a margin, so
        the boolean removes material rather than imprinting edges on a
        coplanar face -- the defect #129 inherits the memory of from the barn
        cabin's P2 (see verify_openings.py, VOLUME).

        WITH --no-openings IT BUILDS NOTHING. `difference()` is what deletes a
        cutter, so skipping the boolean and keeping the cutters left 26 solid
        boxes sitting in the saved file, plugging every opening they were cut
        to make -- an uncut model that looked worse than an uncut model.
        Counted in the blend before this returned early. The caller still gets
        its `built` entry, because the sashes and the report are built from
        that and not from the cutters.
        """
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

    exterior = [("front_wall", "Wall_front", "x0", "x1", "x"),
                ("rear_wall", "Wall_rear", "x0", "x1", "x"),
                ("end_wall_x0", "Wall_x0", "y0", "y1", "y"),
                ("end_wall_x24", "Wall_x24", "y0", "y1", "y")]

    built = []
    for block, wall, lo, hi, along in exterior:
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

    # the skin gets every exterior hole too, or the windows are blind from
    # outside. Each cut goes in the skin of its own wall.
    for o in list(built):
        if o["wall"] in skin_of:
            cutter(f"cut_skin_{o['id']}", skin_of[o["wall"]], o["a0"], o["a1"],
                   o["z0"], o["z1"], o["along"], depth=sheath)
            cutter(f"cut_siding_{o['id']}", siding_of[o["wall"]], o["a0"], o["a1"],
                   o["z0"], o["z1"], o["along"], depth=sheath)

    # THE OPENING GATE IS A VOLUME GATE. A boolean that imprints edges on a
    # coplanar face without removing material leaves corners and a face count
    # that look right, and only the volume shows it -- the defect the barn
    # cabin shipped in its P2 (models/barn_cabin_524/verify_openings.py).
    # Counting cutter objects would prove nothing either: difference() deletes
    # them. So the volume is measured before and after.
    #
    # WHAT IT MEASURES AND WHAT IT MUST NOT. The expected loss used to be
    # accumulated by cutter() itself, in the same call that built the cutter.
    # That is rule 29 -- a gate derived from the build's own expression cannot
    # disagree with the build -- and it cost exactly what rule 29 says it
    # costs: deleting one cutter call removed the hole AND the expectation
    # together, so a wall with a missing window passed every gate, including
    # the one written to catch a missing window. Reproduced on W-C1 before
    # this changed. Only the MEASUREMENTS are recorded here now; what they
    # should be is derived in the gate, from the opening rows.
    volumes = {}
    if cut_openings:
        for wall, cl in cut_by_wall.items():
            before = _volume(walls[wall])
            difference(walls[wall], cl)
            volumes[wall] = (before, _volume(walls[wall]))

    # ---- the siding's reveals, and the textured skins' UVs (#133) ---------
    # A SIDING OPENING'S REVEAL IS TRIM (spec.trim.reveal_material), as the
    # barn cabin's is: the skin's faces inside each cut take the trim slot of
    # materials.face_slots. Found by position, not by shape: a face is a
    # reveal if it faces across the wall and its centre lies within an
    # opening's rectangle, so a raked top edge, whose normal also leans off
    # the wall's axis, is never mistaken for one.
    trim_slot = _face_slot(spec, spec["trim"]["reveal_material"]["value"])
    for wall, skin in siding_of.items():
        ob = walls[skin]
        across = 1 if wall in ("Wall_front", "Wall_rear") else 0     # the wall's depth axis
        along = 1 - across
        rects = [(o["a0"], o["a1"], o["z0"], o["z1"]) for o in built if o["wall"] == wall]
        for poly in ob.data.polygons:
            if abs(poly.normal[across]) > UP:
                continue                                    # the skin's own faces
            c = poly.center
            if any(a0 - MESH_TOL <= c[along] <= a1 + MESH_TOL and z0 - MESH_TOL <= c.z <= z1 + MESH_TOL
                   for a0, a1, z0, z1 in rects):
                poly.material_index = trim_slot
    tx = spec["texturing"]
    for name, ob in walls.items():
        if name.startswith(tuple(tx["textured"])):
            uv_project(ob, tx["tile_ft"]["value"])

    # ---- sashes and leaves ------------------------------------------------
    # Every opening gets what it is: a window gets a sash, a door gets a leaf.
    # An opening with nothing in it reads as a hole in a wall, and the gate
    # below counts them, so this is not optional.
    win = spec["windows"]
    f2g = win["frame_to_glass"]["ft"]
    proud = win["proud_of_glass"]["ft"]
    mull = win["mullion"]["ft"]
    ops = win["operations"]
    leaf_t = spec["openings"]["door_types"]["leaf_thickness"]["ft"]

    def _glazed(name, along, plane, a0, a1, z0, z1, operation):
        """A sash, from the OPERATION the schedule declares.

        Dispatching on the declared operation, and refusing to guess when it
        has nothing behind it, is the rule the barn cabin arrived at after
        shipping flat panes through eleven PRs while its spec typed every one
        of them. Laurel's schedule declares an operation for all five marks.
        """
        op = ops.get(operation)
        if op is None:
            raise SystemExit(
                f"{name} is operated {operation!r}, which spec.windows."
                f"operations does not define (have {sorted(ops)}). A window "
                "cannot be built from an operation alone -- add it or change "
                "the schedule.")
        if op["meeting_rail"]:
            rail = win.get("meeting_rail")
            if rail is None:
                raise SystemExit(
                    f"operation {operation!r} declares a meeting rail and "
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
        plane = (lo + hi) / 2                 # spec.windows.glazing_plane
        row, along = o["row"], o["along"]
        if o["id"].startswith("W-"):
            sashes.append(_glazed(f"Sash_{o['id']}", along, plane,
                                  o["a0"], o["a1"], o["z0"], o["z1"],
                                  wt[row["type"]]["operation"]))
            continue

        # A DOOR IS A LEAF, and door 1 is a leaf AND a sidelite. The schedule
        # calls it an "ENTRY DOOR W/ 12\" SIDELITE" and glazes it tempered, so
        # the sidelite is a glazed panel, not more door. The spec already says
        # which band is which, and verify_spec gates that the sidelite is on
        # the X 24 side, where A-1.0 draws it.
        if "leaf_x" in row and "sidelite_x" in row:
            bands = [("leaf", row["leaf_x"]), ("sidelite", row["sidelite_x"])]
        else:
            bands = [("leaf", (o["a0"], o["a1"]))]
        for what, (b0, b1) in bands:
            name = f"Leaf_{o['id']}" if what == "leaf" else f"Sash_{o['id']}_sidelite"
            if what == "sidelite":
                sashes.append(_glazed(name, along, plane, b0, b1, o["z0"], o["z1"],
                                      win["sidelite_operation"]))
            else:
                d0, d1 = plane - leaf_t / 2, plane + leaf_t / 2
                spec_box = ((b0, b1, d0, d1, o["z0"], o["z1"]) if along == "x"
                            else (d0, d1, b0, b1, o["z0"], o["z1"]))
                sashes.append(multibox(name, [spec_box], openings))

    # ---- Tier 1 trim (#132) ------------------------------------------------
    # spec.trim says what each value is and where it came from; every one is
    # the barn cabin's, declared `assumed`.
    tr = spec["trim"]
    cw = tr["casing_width"]["ft"]
    hh = tr["head_casing_height"]["ft"]
    bh = tr["baseboard_height"]["ft"]
    stock = tr["interior_stool_thickness"]["ft"]   # the 1x every member is cut from
    stool_p = tr["interior_stool_projection"]["ft"]
    apron = tr["interior_apron_height"]["ft"]
    sill_t = tr["exterior_sill_thickness"]["ft"]
    sill_p = tr["exterior_sill_projection"]["ft"]
    ext_apron = tr["exterior_apron_height"]["ft"]
    horn = cw / 2                  # stool horns and the siding head cap: a proportion

    def members(along, face, out, a0, a1, lo_z, hi_z, window, sill_depth, sill_thick, apron_h,
                cap=0.0):
        """The boxes that case one opening on one face.

        `face` is the wall face the trim is fixed to and `out` the way it
        stands off it (+1 or -1 along the wall's depth axis). Jambs and a
        head band for every opening; under a window, a sill -- a stool
        inside, a sill board outside -- and an apron below it. A door has a
        threshold, not a sill, as the barn cabin found after burying one in
        its porch slab.

        `cap` is how far the head runs past the jambs each side: nothing
        inside, and the siding head's cap outside (spec.trim).
        """
        def bx(b0, b1, d0, d1, z0, z1):
            d0, d1 = sorted((d0, d1))
            return (b0, b1, d0, d1, z0, z1) if along == "x" else (d0, d1, b0, b1, z0, z1)
        skin = face + out * stock
        parts = [bx(a0 - cw, a0, face, skin, lo_z, hi_z),
                 bx(a1, a1 + cw, face, skin, lo_z, hi_z),
                 bx(a0 - cw - cap, a1 + cw + cap, face, skin, hi_z, hi_z + hh)]
        if window:
            under = lo_z - sill_thick
            parts += [bx(a0 - cw - horn, a1 + cw + horn, face, face + out * sill_depth, under, lo_z),
                      bx(a0 - cw, a1 + cw, face, skin, under - apron_h, under)]
        return parts

    # A STACK IS CASED AS ONE OPENING. W-A1 and its transom W-B1 share a
    # width and a wall with 8" of wall between them, and two casings would
    # cross there: A's head band runs up to 7.39 ft and B's stool and apron
    # down to 7.31. So each (wall, span) is one cased opening, from the
    # lowest sill to the highest head; the lowest unit decides the sill.
    stacks = {}
    for o in built:
        stacks.setdefault((o["wall"], round(o["a0"], SPAN_PLACES), round(o["a1"], SPAN_PLACES)), []).append(o)

    def stack_span(group):
        low = min(group, key=lambda o: o["z0"])
        return low["z0"], max(o["z1"] for o in group), low["id"].startswith("W-")

    trim_parts = {host: [] for host in walls if host.startswith(("Wall_", "P_"))}
    siding_parts = {}
    faces = room_faces(spec)
    for (host, a0, a1), group in stacks.items():
        lo_z, hi_z, window = stack_span(group)
        for face in faces[host]:
            trim_parts[host] += members(face["along"], face["at"], face["into"], a0, a1,
                                        lo_z, hi_z, window, stool_p, stock, apron)
        if host in skin_of:
            outer, out = outer_face(spec, host)
            siding_parts.setdefault(host, []).extend(
                members(group[0]["along"], outer, out, a0, a1, lo_z, hi_z,
                        window, sill_p, sill_t, ext_apron, cap=horn))

    # BASEBOARD along every room face, broken where a doorway's casing comes
    # down to the floor. Runs pass through the ends of partitions that abut
    # them and hide there, which is what keeps a corner closed without a
    # mitre table.
    for host, fl in faces.items():
        doors = sorted((a0 - cw, a1 + cw) for (h, a0, a1), g in stacks.items()
                       if h == host and not stack_span(g)[2])
        for face in fl:
            start = face["from"]
            for d0, d1 in doors + [(face["to"], face["to"])]:
                if d0 - start > MIN_RUN:
                    trim_parts[host] += members_run(face, start, d0, bh, stock)
                start = max(start, d1)

    trim = [multibox(f"Trim_{host}", parts, trim_coll)
            for host, parts in trim_parts.items() if parts]

    fixture_coll = collection("Fixtures")
    fixtures = _build_fixtures(spec, fixture_coll)
    equipment_coll = collection("Equipment")      # outside the building: lod0 and lod1
    equipment = _build_condenser(spec, equipment_coll)
    furniture_coll = collection("Furniture")      # inside, switchable: lod0
    furniture = _build_furniture(spec, furniture_coll)
    canopy_coll = collection("Canopy")            # outside, switchable: lod0 and lod1
    canopy = _build_canopy(spec, canopy_coll)
    # ONE NODE PER WALL, like the interior trim, so the cutaway can hide the
    # front wall's siding trim with the front wall.
    siding = [multibox(host.replace("Wall_", "Trim_ext_siding_"), parts, siding_coll)
              for host, parts in siding_parts.items()]

    geo = dict(W=W, D=D, t=t, it=it, roof_planes=roof_planes, ceiling=ceiling,
               walls=walls, roof=roof,
               built=built, sashes=sashes, volumes=volumes, cut=cut_openings,
               depths=depths, skin_of=skin_of, siding_of=siding_of, trim=trim, siding=siding,
               fixtures=fixtures, equipment=equipment, furniture=furniture, canopy=canopy)
    return geo, dict(Shell=shell, Partitions=partitions, Roof=roof_coll,
                     Openings=openings, Site=site, Trim=trim_coll, Siding=siding_coll,
                     Fixtures=fixture_coll, Equipment=equipment_coll, Furniture=furniture_coll,
                     Canopy=canopy_coll)


def _face_slot(spec, material):
    """The polygon material index spec.materials.face_slots gives `material`,
    as a whole number whichever loader read the spec (adu_kit.manifest
    .face_slots)."""
    slots, bad = face_slots(spec["materials"])
    if bad or material not in slots.values():
        raise SystemExit("spec.materials.face_slots: "
                         + ("; ".join(bad) or f"no slot is {material!r}"))
    return {v: k for k, v in slots.items()}[material]


def _floor_slot(spec):
    return _face_slot(spec, "floor")


def to_stud_faces(spec, bb):
    """A drawn fixture's plan box with each side that stands at a FINISHED
    face moved to that wall's STUD face (spec.fixtures).

    A-1.0 draws fixtures against the gyp board, half an inch in from a stud
    face; this model carries the board as a material, so a fixture built as
    drawn stands half an inch off a bare stud face with a gap behind it. A
    side is moved only if it lies within the wall's finish thickness (plus
    FACE_TOL) on the room side of a face, and the fixture overlaps that face
    along its run."""
    con = spec["construction"]
    ext = con["exterior_wall"]["interior_finish"]["ft"]
    part = con["interior_wall"]["interior_finish"]["ft"]
    (x0, x1), (y0, y1) = bb["x"], bb["y"]
    box_ = {"x": [x0, x1], "y": [y0, y1]}
    for host, faces in room_faces(spec).items():
        finish = ext if host.startswith("Wall_") else part
        for f in faces:
            across = "y" if f["along"] == "x" else "x"
            lo, hi = box_[f["along"]]
            if hi <= f["from"] or lo >= f["to"]:
                continue                        # not alongside this face
            side = 0 if f["into"] > 0 else 1    # the side that faces the wall
            gap = (box_[across][side] - f["at"]) * f["into"]
            if 0 < gap <= finish + FACE_TOL:
                box_[across][side] = f["at"]
    return box_


def _build_fixtures(spec, coll):
    """The interior fixtures (#134): plan from spec.fixtures.drawn taken to
    the stud faces, heights from spec.fixtures.heights, the water heater at
    its published size."""
    fx = spec["fixtures"]
    h = {k: v["ft"] for k, v in fx["heights"].items()}
    at = {k: to_stud_faces(spec, v) for k, v in fx["drawn"].items() if isinstance(v, dict)}

    def slab(bb, z0, z1):
        return (bb["x"][0], bb["x"][1], bb["y"][0], bb["y"][1], z0, z1)

    base = h["counter_top"] - h["countertop"]
    made = []
    # The counter: base cabinets either side of the dishwasher, which stands
    # under the top in its own drawn place; one top over the whole run.
    cnt, dw = at["counter"], at["dishwasher"]
    runs = [(cnt["y"][0], dw["y"][0]), (dw["y"][1], cnt["y"][1])]
    made.append(multibox("Fix_counter", [
        (cnt["x"][0], cnt["x"][1], a, b, 0.0, base) for a, b in runs if b - a > MIN_RUN], coll))
    made.append(box("Fix_countertop", *slab(cnt, base, h["counter_top"]), coll))
    made.append(box("Fix_dishwasher", *slab(dw, 0.0, base), coll))
    sk = at["sink"]
    made.append(box("Fix_sink", *slab(sk, h["counter_top"] - h["sink_basin"],
                                      h["counter_top"] + h["sink_rim"]), coll))
    made.append(box("Fix_range", *slab(at["range"], 0.0, h["range"]), coll))
    made.append(box("Fix_refrigerator", *slab(at["refrigerator"], 0.0, h["refrigerator"]), coll))
    made.append(box("Fix_vanity", *slab(at["vanity"], 0.0, h["vanity"]), coll))
    made.append(box("Fix_tub", *slab(at["tub"], 0.0, h["tub"]), coll))
    made.append(box("Fix_washer_dryer", *slab(at["washer_dryer"], 0.0, h["washer_dryer"]), coll))
    # The toilet: its bowl to the rim over the whole drawn outline short of
    # the tank, and the tank to its top, both one object.
    tl, tk = at["toilet"], at["toilet_tank"]
    bowl = dict(tl, y=[tl["y"][0], tk["y"][0]])
    made.append(multibox("Fix_toilet", [slab(bowl, 0.0, h["toilet_bowl"]),
                                        slab(tk, 0.0, h["toilet_tank"])], coll))
    # The water heater: the drawn circle's centre, the maker's size.
    wh, whs = at["water_heater"], fx["water_heater"]
    cx, cy = sum(wh["x"]) / 2, sum(wh["y"]) / 2
    made.append(tube("Fix_water_heater", [(cx, cy, 0.0), (cx, cy, whs["height"]["ft"])],
                     whs["diameter"]["ft"] / 2, coll, sides=WH_SIDES))
    return made


def condenser_box(spec):
    """(x0, x1, y0, y1, z0, z1) the condenser stands in: A-1.1's plan, its
    wall side taken from the drawn FINISHED face to the model's outer face
    (the cladding is a material here, as the gyp board is inside), at the
    height the side elevation draws, on its pad."""
    c = spec["fixtures"]["condenser"]
    W = spec["envelope"]["width"]["ft"]
    outer = W + spec["construction"]["exterior_wall"]["sheathing"]["ft"]
    (x0, x1), (y0, y1) = c["plan"]["x"], c["plan"]["y"]
    se = c["side_elevation"]
    return outer, outer + (x1 - x0), y0, y1, c["pad"]["top"]["ft"], c["pad"]["top"]["ft"] + se["top"] - se["base"]


def _build_condenser(spec, coll):
    """The condenser and its pad (spec.fixtures.condenser)."""
    c = spec["fixtures"]["condenser"]
    x0, x1, y0, y1, z0, z1 = condenser_box(spec)
    m, pad = c["pad"]["margin"]["ft"], c["pad"]
    return [box("Equip_condenser", x0, x1, y0, y1, z0, z1, coll),
            # the pad's wall side stops at the wall; it is wider on the other three
            box("Equip_pad", x0, x1 + m, y0 - m, y1 + m, pad["bottom"]["ft"], pad["top"]["ft"], coll)]


def _build_canopy(spec, coll):
    """The optional entry canopy (spec.variants.canopy), as its `placement`
    says: the frame, the slats and the two braces, each its own node so the
    page can show or hide the canopy whole."""
    c = spec["variants"]["canopy"]
    fe, se, pl = c["front_elevation"], c["side_elevation"], c["a34_plan"]
    face, _ = outer_face(spec, "Wall_front")
    w, proj, depth = c["width"]["ft"], c["projection"]["ft"], c["depth"]["ft"]
    m, j = pl["member"], pl["bay_joist"]
    cx = sum(fe["x"]) / 2
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, face, face + proj
    z0 = fe["underside"]
    z1 = z0 + depth
    frame = [(x0, x1, y0, y0 + m, z0, z1),                      # the ledger, at the wall
             (x0, x1, y1 - m, y1, z0, z1),                      # the header, at the outer edge
             (x0, x0 + m, y0 + m, y1 - m, z0, z1),              # the end joists
             (x1 - m, x1, y0 + m, y1 - m, z0, z1),
             (cx - j / 2, cx + j / 2, y0 + m, y1 - m, z0, z1)]  # the bay joist
    st = c["slat_thickness"]["ft"]
    bays = ((x0 + m, cx - j / 2), (cx + j / 2, x1 - m))
    # a slat's faces are measured from the frame's OUTER face, toward the wall
    slats = [(b0, b1, y1 - s1, y1 - s0, z1 - st, z1) for b0, b1 in bays for s0, s1 in pl["slats"]]
    r = c["brace_rod"]["ft"] / 2
    zw = sum(fe["wall_connection"]) / 2
    land = proj - (se["projection"] - se["brace_lands_from_wall"])
    # THE ROD'S END RINGS TOUCH THE PLATE'S MIDDLE AND THE LANDING POINT. A
    # tilted rod's ring reaches r * |dz| past its centre in Y and r * dy in
    # Z, along (0, -dz, dy) -- the direction tube_geom's ring puts a vertex
    # on -- so both ends shift by that same vector and the direction does
    # not change. Found by review: shifting by the full radius on each axis
    # left the rod 0.10" off the wall and 0.05" above the frame.
    run, fall = land, z1 - zw
    length = math.hypot(run, fall)
    oy, oz = -r * fall / length, r * run / length
    braces = [tube(f"Canopy_brace_{i}", [(bx, face + oy, zw + oz), (bx, face + land + oy, z1 + oz)], r, coll)
              for i, bx in enumerate(fe["brace_x"], start=1)]
    return [multibox("Canopy_frame", frame, coll), multibox("Canopy_slats", slats, coll)] + braces


ROTATIONS = {0: (1, 0, 0, 1), 90: (0, -1, 1, 0), 180: (-1, 0, 0, -1), 270: (0, 1, -1, 0)}


def place_box(pc, place):
    """A barn-cabin piece's box, turned about `place.from` by `place.rotate`
    degrees (counter-clockwise in plan) and moved to `place.to`: (x0, x1, y0,
    y1, z0, z1) in Laurel's frame. Heights are the piece's own."""
    a, b, c, d = ROTATIONS[place["rotate"]]
    (fx, fy), (tx, ty) = place["from"], place["to"]
    xs, ys = [], []
    for x in (pc["x0"], pc["x1"]):
        for y in (pc["y0"], pc["y1"]):
            dx, dy = x - fx, y - fy
            xs.append(tx + a * dx + b * dy)
            ys.append(ty + c * dx + d * dy)
    return min(xs), max(xs), min(ys), max(ys), pc["z0"], pc["z1"]


def _barn_arrangements():
    """The barn cabin's furniture arrangements, by id: the pieces Laurel reuses."""
    barn = load_spec(HERE.parent / "barn_cabin_524" / "spec.yaml")
    return {a["id"]: a for a in barn["fixtures"]["furniture"]["arrangements"]}


def arrangement_ids(spec):
    """The furniture arrangements spec.fixtures.furniture declares, by id."""
    furniture = (spec.get("fixtures") or {}).get("furniture") or {}
    return {a["id"] for a in furniture.get("arrangements") or ()}


def option_nodes(option, names, arrangements):
    """The nodes a presence option shows, out of `names`: its `show` list, or,
    for a furniture option, its arrangement's Furn_<arrangement>_<material>
    nodes -- the build names them, so the spec never lists them and cannot
    drift from them. Only null shows nothing (the room unfurnished).
    finish.py and views.py both read an option through this, so the export
    and the viewer agree.

    AN ARRANGEMENT MUST BE ONE `arrangements` DECLARES, and a node must be
    its prefix and ONE material word, never a prefix alone. Found by review:
    `arrangement: sleep` matched the bed's nodes and the office's, and
    published both; `living` published the sofa; "" passed as null. An
    undeclared id resolves to nothing, which finish.py names."""
    if "arrangement" not in option:
        return list(option.get("show") or [])
    arr = option["arrangement"]
    if arr is None or arr not in arrangements:
        return []
    prefix = f"Furn_{arr}_"
    return sorted(n for n in names if n.startswith(prefix) and "_" not in n[len(prefix):])


def _build_furniture(spec, coll):
    """Every arrangement in spec.fixtures.furniture, as the barn cabin builds
    its own: one mesh per (arrangement, material), named
    Furn_<arrangement>_<material>, so an arrangement can be shown or hidden
    whole and never half of one."""
    fx = spec["fixtures"]["furniture"]
    barn = _barn_arrangements()
    made = []
    for arr in fx["arrangements"]:
        src = barn.get(arr["reuse"])
        if src is None:
            raise SystemExit(f"{arr['id']} reuses {arr['reuse']!r}, which the barn cabin's "
                             f"spec does not define (has {sorted(barn)})")
        if arr["place"]["rotate"] not in ROTATIONS:
            raise SystemExit(f"{arr['id']}: rotate {arr['place']['rotate']!r} is not one of "
                             f"{sorted(ROTATIONS)}")
        by_mat = {}
        for pc in src["pieces"]:
            by_mat.setdefault(pc["material"], []).append(place_box(pc, arr["place"]))
        for mat, boxes in sorted(by_mat.items()):
            made.append(multibox(f"Furn_{arr['id']}_{mat.removeprefix('furn_')}", boxes, coll))
    return made


def _partition_band(row, it):
    """(lo, hi): where a partition sits across its run -- its cited face and
    the face its studs run toward. ONE DEFINITION for the wall and the trim
    on it, so a partition that moves takes its casing and baseboard along."""
    near = row["at_ft"]
    far = near + it if _sign(row["id"], row["studs_toward"]) > 0 else near - it
    return tuple(sorted((near, far)))


def members_run(face, a0, a1, height, stock):
    """One baseboard run on a room face, as a box spec."""
    d0, d1 = sorted((face["at"], face["at"] + face["into"] * stock))
    return ([(a0, a1, d0, d1, 0.0, height)] if face["along"] == "x"
            else [(d0, d1, a0, a1, 0.0, height)])


def room_faces(spec):
    """{host: [face]} -- every wall face a room sees, from the spec.

    A face is {along, at, into, from, to}: the axis it runs along ("x" or
    "y"), its position across that axis, the way the room lies from it (+1
    or -1), and its extent. An exterior wall has one, its inside face of
    stud; a partition has two. The exterior walls' faces run between the
    other two walls' inside faces, and a partition's between its own ends.
    """
    env, con = spec["envelope"], spec["construction"]
    W, D = env["width"]["ft"], env["depth"]["ft"]
    t = con["exterior_wall"]["stud_depth"]["ft"]
    layout = spec["interior_partitions"]["layout"]
    it = layout["thickness"]["ft"]
    faces = {
        "Wall_rear":  [{"along": "x", "at": t, "into": DIRECTIONS["+Y"], "from": t, "to": W - t}],
        "Wall_front": [{"along": "x", "at": D - t, "into": DIRECTIONS["-Y"], "from": t, "to": W - t}],
        "Wall_x0":    [{"along": "y", "at": t, "into": DIRECTIONS["+X"], "from": t, "to": D - t}],
        "Wall_x24":   [{"along": "y", "at": W - t, "into": DIRECTIONS["-X"], "from": t, "to": D - t}],
    }
    for row in layout["partitions"]:
        lo, hi = _partition_band(row, it)
        a, b = sorted((row["from_ft"], row["to_ft"]))
        along = "x" if _axis(row["id"], row["runs_along"]) == "X" else "y"
        across = "Y" if along == "x" else "X"      # a face's room lies across its run
        faces[row["id"]] = [
            {"along": along, "at": lo, "into": DIRECTIONS["-" + across], "from": a, "to": b},
            {"along": along, "at": hi, "into": DIRECTIONS["+" + across], "from": a, "to": b}]
    return faces


def outer_face(spec, wall):
    """(position, outward sign) of an exterior wall's modelled outer face:
    face of stud plus sheathing, where the siding trim is fixed."""
    env, con = spec["envelope"], spec["construction"]
    W, D = env["width"]["ft"], env["depth"]["ft"]
    s = con["exterior_wall"]["sheathing"]["ft"]
    return {"Wall_rear": (-s, DIRECTIONS["-Y"]), "Wall_front": (D + s, DIRECTIONS["+Y"]),
            "Wall_x0": (-s, DIRECTIONS["-X"]), "Wall_x24": (W + s, DIRECTIONS["+X"])}[wall]


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
# gates
# ---------------------------------------------------------------------------
def report(spec, geo, colls):
    env, lv, rf = spec["envelope"], spec["levels"], spec["roof"]
    W, D, roof_planes = geo["W"], geo["D"], geo["roof_planes"]
    print("=" * RULE)
    print('Laurel A1 460sf — massing and openings (#129)')
    print("=" * RULE)

    shell = [o for o in bpy.data.objects if o.name.startswith(("Wall_", "Sheathing"))]
    bb = world_bbox(shell + [geo["roof"]])
    print(f"\nBounding box, walls + roof:")
    for i, ax in enumerate("XYZ"):
        print(f"  {ax} {bb[0][i]:8.3f} .. {bb[1][i]:8.3f}   span {bb[1][i] - bb[0][i]:7.3f} ft")

    print("\nGATES")

    ok, why = _footprint(spec, geo)
    gate(ok, f'the shell is {ft(W)} x {ft(D)} to face of stud', why)

    ok, why = _roof_covers_its_overhangs(spec, geo)
    gate(ok, "the roof carries all four overhangs, measured on the mesh", why)

    ok, why = _roof_meets_the_plates(spec, geo)
    gate(ok, f'the built roof underside meets T.P. 1 ({ft(lv["top_of_plate_rear"]["ft"])}) '
             f'and T.P. 2 ({ft(lv["top_of_plate_front"]["ft"])})', why)

    gate(roof_planes.under_y(D) > roof_planes.under_y(0.0),
         "the roof rises toward the front (+Y), as the side elevations draw it")

    ok, why = _roof_top_at_the_front_edge(spec, geo)
    gate(ok, f'the roof top at the front edge is A-2.0\'s '
             f'{ft(lv["roof_top_at_front_edge"]["ft"])}', why)

    ok, why = _every_partition_built(spec, geo)
    gate(ok, "every partition in the spec was built, where the spec puts it", why)

    ok, why = _where_a10_draws_them(spec)
    gate(ok, "the built partitions and interior doors sit where A-1.0 draws them", why)

    # the frame is not mirrored — checked on GEOMETRY, not on the spec
    ok, why = _frame_not_mirrored(spec, geo)
    gate(ok, "not mirrored: D and E open on the X 24 wall, the C windows on X 0", why)

    # every schedule row produced a cut opening with a sash
    label = "every schedule row produced a cut opening with a sash or a leaf"
    if geo["cut"]:
        ok, why = _every_row_built(spec, geo)
        gate(ok, label, why)
    else:
        skip(label, "--no-openings: nothing was cut, so there is no volume to measure")

    ok, why = _openings_on_the_wall_their_block_names(geo)
    gate(ok, "every exterior opening is on the wall its spec block names", why)

    ok, why = _sash_members(spec, geo)
    gate(ok, "every sash carries the members its declared operation implies", why)

    ok, why = _door_one_has_its_sidelite(spec, geo)
    gate(ok, "door 1 is a leaf AND a glazed sidelite, as the schedule describes", why)

    ok, why = _every_opening_cased(spec, geo)
    gate(ok, "every opening is cased on each room side, and every window has its stool and apron", why)

    ok, why = _baseboard_runs(spec, geo)
    gate(ok, "every room face carries baseboard, and no doorway is blocked by it", why)

    ok, why = _siding_trim(spec, geo)
    gate(ok, "the siding exterior trim cases every exterior opening, one node per wall", why)

    ok, why = _siding_skins(spec, geo)
    gate(ok, "each wall's siding skin is its stucco skin's solid, with trim reveals and UVs", why)

    ok, why = _trim_inside_its_walls(spec, geo)
    gate(ok, "no trim runs outside the rooms or above the roof underside", why)

    ok, why = _floor_on_the_slab(spec)
    gate(ok, "the floor finish is the slab's top face, at the finished floor", why)

    ok, why = _fixtures_where_drawn(spec, geo)
    gate(ok, "every fixture is built where A-1.0 draws it, to the stud face, at its declared height", why)

    ok, why = _fixture_parts(spec)
    gate(ok, "the counter has its dishwasher opening, and the toilet a bowl lower than its tank", why)

    ok, why = _water_heater_as_published(spec)
    gate(ok, "the water heater stands on the drawn circle's centre, at the size Rheem publishes", why)

    ok, why = _furniture_placed(spec, geo)
    gate(ok, "the furniture stands in the room: clear of walls, partitions, fixtures, "
             "walkways and door swings, one group clear of the other", why)

    ok, why = _canopy_hung(spec, geo, colls)
    gate(ok, "the entry canopy hangs where A-2.0 draws it at A-3.4's size, in its own collection: "
             "outside the front wall, below the roof, clear of every opening and the siding trim", why)

    ok, why = _ground_mounted(spec, geo)
    gate(ok, "the condenser keeps the ground-mounted placement rule: on its pad on grade, outside, "
             "where A-1.1 draws it, below the roof, blocking no opening", why)

    ok, why = _no_degenerate()
    gate(ok, "no NaN or degenerate geometry", why)

    print("=" * RULE)
    if SKIPPED:
        # A SKIPPED GATE IS NOT A PASSING BUILD. Reporting the skip and then
        # exiting 0 let automation read an uncut model as a good one, which is
        # the whole failure the [SKIP] state was added to prevent, moved one
        # level up. --no-openings is a diagnostic, and a diagnostic run has
        # not earned a success.
        print(f"{len(SKIPPED)} gate(s) SKIPPED, not passed: " + "; ".join(SKIPPED))
        print("This model is not complete. Re-run without --no-openings to judge them.")
    return not FAILED and not SKIPPED


def _frame_not_mirrored(spec, geo):
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


def _footprint(spec, geo):
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


def _roof_covers_its_overhangs(spec, geo):
    """All four overhangs, measured on the roof mesh.

    Only `W + 2 x ends` was checked, so the 5'-0" front overhang -- the most
    prominent thing about this building -- could be halved with every gate
    still green. The rear and the front were never compared to anything.
    """
    ov = spec["roof"]["overhangs"]
    W, D = geo["W"], geo["D"]
    lo, hi = world_bbox([geo["roof"]])
    want = {"the X 0 end": (lo[0], -ov["ends"]["ft"]),
            "the X max end": (hi[0], W + ov["ends"]["ft"]),
            "the rear": (lo[1], -ov["rear"]["ft"]),
            "the front": (hi[1], D + ov["front"]["ft"])}
    wrong = [f"{where} edge is at {got:.4f}, the overhang puts it at {expect:.4f}"
             for where, (got, expect) in want.items() if abs(got - expect) > MESH_TOL]
    return not wrong, "; ".join(wrong)


def _roof_meets_the_plates(spec, geo):
    """The BUILT roof's underside passes through T.P. 1 and T.P. 2.

    The gate this replaces asked the Shed helper, which is the same expression
    the roof was laid out from -- rule 29 -- and `roof_planes.under_y(0)` is literally
    `top_of_plate_rear` read back, so half of it compared a spec value to
    itself. It caught a wrong slope and nothing else: lifting the built roof a
    foot off the walls, a gap visible right round the building, left all nine
    gates green. Reproduced before this was written. PLAN.md makes this #130's
    exit gate, so it had to measure the mesh.

    The underside is the prism's lower edge: two (y, z) points, one at each end
    of the run. The plane through them is then evaluated at the two walls.
    """
    lv = spec["levels"]
    D = geo["D"]
    pts = [(v.co[1], v.co[2]) for v in geo["roof"].data.vertices]
    if not pts:
        return False, "the roof has no vertices"
    y_lo, y_hi = min(p[0] for p in pts), max(p[0] for p in pts)
    if abs(y_hi - y_lo) < MESH_TOL:
        return False, "the roof has no extent in Y"
    under_lo = min(z for y, z in pts if abs(y - y_lo) <= MESH_TOL)
    under_hi = min(z for y, z in pts if abs(y - y_hi) <= MESH_TOL)
    slope = (under_hi - under_lo) / (y_hi - y_lo)

    def at(y):
        return under_lo + slope * (y - y_lo)

    wrong = []
    for label, y, want in (("T.P. 1", 0.0, lv["top_of_plate_rear"]["ft"]),
                           ("T.P. 2", D, lv["top_of_plate_front"]["ft"])):
        got = at(y)
        if abs(got - want) > MESH_TOL:
            wrong.append(f"at {label} the roof underside is {got:.4f}, not {want:.4f}")
    return not wrong, "; ".join(wrong)


def _roof_top_at_the_front_edge(spec, geo):
    """The one roof dimension A-2.0 gives that is not a plate height.

    F.F. to the top of the roof at the FRONT EDGE OF THE OVERHANG, 10'-9 1/2".
    #128 recorded it as unreconciled and left it to #130; it is the dimension
    that caught the roof being built 2.47" too thick, because it is the only
    one that sees the roof's THICKNESS. The plate gates see the underside, and
    the underside was right all along.

    It is measured on the mesh, at the vertices furthest forward in Y, so a
    wrong assembly depth or a wrong overhang both move it.
    """
    lv = spec["levels"]
    want = lv["roof_top_at_front_edge"]["ft"]
    tol = lv["roof_top_at_front_edge"]["tolerance_in"]["value"] / INCHES_PER_FOOT
    pts = [(v.co[1], v.co[2]) for v in geo["roof"].data.vertices]
    if not pts:
        return False, "the roof has no vertices"
    y_front = max(y for y, _ in pts)
    got = max(z for y, z in pts if abs(y - y_front) <= MESH_TOL)
    if abs(got - want) > tol:
        return False, (f"the built roof tops out at {got:.4f} ft at Y {y_front:.4f}, "
                       f"{(got - want) * INCHES_PER_FOOT:+.2f} in from the sheet's {want:.4f}")
    return True, ""


def _every_partition_built(spec, geo):
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


def _openings_on_the_wall_their_block_names(geo):
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


def _every_row_built(spec, geo):
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


def _sash_members(spec, geo):
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


def _door_one_has_its_sidelite(spec, geo):
    """A-1.0's Door Schedule calls door 1 an ENTRY DOOR W/ 12" SIDELITE and
    glazes it tempered, so it is two things: a leaf and a glazed panel. The
    spec says which band is which and verify_spec gates that the sidelite is
    on the X 24 side; this gates that both were actually built."""
    rows = {o["id"]: o["row"] for o in geo["built"]}
    bad = []
    for oid, row in rows.items():
        if "sidelite_x" not in row:
            continue
        for name in (f"Leaf_{oid}", f"Sash_{oid}_sidelite"):
            if name not in bpy.data.objects:
                bad.append(f"{oid}: {name} was not built")
    return not bad, "; ".join(bad)


def _where_a10_draws_them(spec):
    """P3b (#132): the BUILT walls and leaves, held to A-1.0's INK.

    _every_partition_built compares the mesh with the spec, so a spec that is
    wrong and a build that follows it pass together -- which is how #129's
    half-inch misreading of three walls and its door 2 stood for two steps.
    This compares the mesh with spec.plan_overlay: where A-1.0 draws each
    stud face and each door, measured off the PDF's vectors by plan_ink.py
    and re-measured by test_plan_ink.py. Two readings of one drawing, as
    #130's elevation overlay is for the outside.

    A partition is its mesh's extent across its run; a door is its leaf's
    centre along its wall, since the schedule, not the ink, gives the width.
    """
    po = spec["plan_overlay"]
    tol = po["tolerance_in"]["value"] / INCHES_PER_FOOT
    drawn = {k: v for k, v in po["faces"].items() if k != "source"}
    centres = {k: v for k, v in po["door_centres"].items() if k != "source"}
    layout = spec["interior_partitions"]["layout"]
    by_id = {r["id"]: r for r in layout["partitions"]}
    wrong = []
    for row in layout["partitions"]:
        ob = bpy.data.objects.get(row["id"])
        if ob is None or row["id"] not in drawn:
            wrong.append(f"{row['id']}: {'not built' if ob is None else 'not in plan_overlay'}")
            continue
        lo, hi = world_bbox([ob])
        ci = 1 if _axis(row["id"], row["runs_along"]) == "X" else 0   # across the run
        want = sorted(drawn[row["id"]])
        if abs(lo[ci] - want[0]) > tol or abs(hi[ci] - want[1]) > tol:
            wrong.append(f"{row['id']} is built {lo[ci]:.4f}..{hi[ci]:.4f}, A-1.0 draws "
                         f"{want[0]:.4f}..{want[1]:.4f}")
    for d in layout["door_openings"]:
        leaf = bpy.data.objects.get(f"Leaf_{d['id']}")
        if leaf is None or d["id"] not in centres:
            wrong.append(f"{d['id']}: {'no leaf built' if leaf is None else 'not in plan_overlay'}")
            continue
        lo, hi = world_bbox([leaf])
        ai = 0 if _axis(d["in"], by_id[d["in"]]["runs_along"]) == "X" else 1  # along the wall
        got, want = (lo[ai] + hi[ai]) / 2, float(centres[d["id"]])
        if abs(got - want) > tol:
            wrong.append(f"{d['id']}'s leaf centres on {got:.4f}, A-1.0 draws {want:.4f} "
                         f"({(got - want) * INCHES_PER_FOOT:+.2f} in)")
    return not wrong, "; ".join(wrong)


# ---------------------------------------------------------------------------
# Tier 1 trim (#132). Each gate asks the MESH whether a point is inside it,
# at a place worked out here from spec.trim and the openings -- never from
# the boxes build() made, so deleting a member cannot delete its check
# (rule 29). The points sit in the middle of a member, clear of the corners
# where members overlap, because inside_mesh reads the nearest face.
# ---------------------------------------------------------------------------
def _pt(along, a, depth, z):
    from mathutils import Vector
    return Vector((a, depth, z)) if along == "x" else Vector((depth, a, z))


def _stacks(geo):
    """{(host, a0, a1): (lowest sill, highest head, is a window)} -- a window
    and the transom over it are one cased opening (spec.trim)."""
    out = {}
    for o in geo["built"]:
        key = (o["wall"], round(o["a0"], SPAN_PLACES), round(o["a1"], SPAN_PLACES))
        out.setdefault(key, []).append(o)
    return {k: (min(o["z0"] for o in g), max(o["z1"] for o in g),
                min(g, key=lambda o: o["z0"])["id"].startswith("W-"))
            for k, g in out.items()}


def _cased(ob, along, face, out, a0, a1, lo_z, hi_z, window, tr, sill_depth, sill_thick, apron_h,
           cap=False):
    """The members missing from one opening's casing on one face, by name."""
    cw = tr["casing_width"]["ft"]
    stock = tr["interior_stool_thickness"]["ft"]
    hh = tr["head_casing_height"]["ft"]
    mid_d = face + out * stock / 2
    probes = {"left jamb": _pt(along, a0 - cw / 2, mid_d, (lo_z + hi_z) / 2),
              "right jamb": _pt(along, a1 + cw / 2, mid_d, (lo_z + hi_z) / 2),
              "head": _pt(along, (a0 + a1) / 2, mid_d, hi_z + hh / 2)}
    if cap:
        # past the jamb, where only the siding head's cap reaches
        probes["head cap"] = _pt(along, a0 - cw - (cw / 2) / 2, mid_d, hi_z + hh / 2)
    if window:
        # IN THE HORN, where the sill is the only member. Under the opening the
        # apron's top face lies half a sill's thickness away, as near as the
        # sill's own faces, and inside_mesh reads the nearest face: a probe
        # there found no sill on every window while every sill was built.
        probes["sill"] = _pt(along, a0 - cw - (cw / 2) / 2, face + out * sill_depth / 2,
                             lo_z - sill_thick / 2)
        probes["apron"] = _pt(along, (a0 + a1) / 2, mid_d, lo_z - sill_thick - apron_h / 2)
    return [name for name, p in probes.items() if ob is None or not inside_mesh(ob, p)]


def _every_opening_cased(spec, geo):
    """Interior casing on every room face an opening has: one for an exterior
    wall, two for a partition. A window also has its stool and apron."""
    tr = spec["trim"]
    faces = room_faces(spec)
    wrong = []
    for (host, a0, a1), (lo_z, hi_z, window) in sorted(_stacks(geo).items()):
        ob = bpy.data.objects.get(f"Trim_{host}")
        for f in faces[host]:
            missing = _cased(ob, f["along"], f["at"], f["into"], a0, a1, lo_z, hi_z, window,
                             tr, tr["interior_stool_projection"]["ft"],
                             tr["interior_stool_thickness"]["ft"],
                             tr["interior_apron_height"]["ft"])
            if missing:
                wrong.append(f"{host} {a0:.4f}..{a1:.4f} on its face at {f['at']:.4f}: "
                             f"no {', '.join(missing)}")
    return not wrong, "; ".join(wrong)


def _baseboard_runs(spec, geo):
    """Baseboard on every stretch of every room face that is not a doorway,
    and none across a doorway."""
    tr = spec["trim"]
    cw, bh = tr["casing_width"]["ft"], tr["baseboard_height"]["ft"]
    stock = tr["interior_stool_thickness"]["ft"]
    stacks = _stacks(geo)
    wrong = []
    for host, fl in room_faces(spec).items():
        ob = bpy.data.objects.get(f"Trim_{host}")
        doors = sorted((a0, a1) for (h, a0, a1), (_, _, win) in stacks.items()
                       if h == host and not win)
        for f in fl:
            d = f["at"] + f["into"] * stock / 2
            start = f["from"]
            for a0, a1 in doors + [(f["to"] + cw, f["to"] + cw)]:
                if a0 - cw - start > cw:           # a stretch worth a probe
                    p = _pt(f["along"], (start + a0 - cw) / 2, d, bh / 2)
                    if ob is None or not inside_mesh(ob, p):
                        wrong.append(f"{host}'s face at {f['at']:.4f} has no baseboard "
                                     f"between {start:.4f} and {a0 - cw:.4f}")
                if a1 > a0:
                    p = _pt(f["along"], (a0 + a1) / 2, d, bh / 2)
                    if ob is not None and inside_mesh(ob, p):
                        wrong.append(f"baseboard runs across the doorway in {host} "
                                     f"at {a0:.4f}..{a1:.4f}")
                start = max(start, a1 + cw)
    return not wrong, "; ".join(wrong)


def _siding_trim(spec, geo):
    """Each wall's Trim_ext_siding_<wall> cases every opening in it on the
    outer face, head cap and all, with a sill and apron under each window --
    and sits in the Siding collection alone. lod1 exports that collection and
    not Trim, so siding trim anywhere else would vanish from the street view
    while lod0 still carried it. Found by review."""
    tr = spec["trim"]
    wrong = [f"{ob.name} is in {[c.name for c in ob.users_collection]}, not the "
             f"Siding collection alone" for ob in geo["siding"]
             if [c.name for c in ob.users_collection] != ["Siding"]]
    for (host, a0, a1), (lo_z, hi_z, window) in sorted(_stacks(geo).items()):
        if host not in geo["skin_of"]:
            continue
        name = host.replace("Wall_", "Trim_ext_siding_")
        ob = bpy.data.objects.get(name)
        along = next(f["along"] for f in room_faces(spec)[host])
        outer, out = outer_face(spec, host)
        missing = _cased(ob, along, outer, out, a0, a1, lo_z, hi_z, window, tr,
                         tr["exterior_sill_projection"]["ft"],
                         tr["exterior_sill_thickness"]["ft"],
                         tr["exterior_apron_height"]["ft"], cap=True)
        if missing:
            wrong.append(f"{name} at {a0:.4f}..{a1:.4f}: no {', '.join(missing)}")
    return not wrong, "; ".join(wrong)


def _siding_skins(spec, geo):
    """The siding finish (#133): every wall's Siding_ skin is the SAME solid as
    its stucco skin, so choosing a finish changes the surface and never the
    building; it sits in the Siding collection, which lod2 never exports; its
    cut faces carry the trim slot (trim.reveal_material); and both skins
    carry UVs for their textures."""
    trim_slot = _face_slot(spec, spec["trim"]["reveal_material"]["value"])
    wrong = []
    for wall, stucco_name in geo["skin_of"].items():
        siding = bpy.data.objects.get(geo["siding_of"].get(wall, ""))
        stucco = bpy.data.objects.get(stucco_name)
        if siding is None or stucco is None:
            wrong.append(f"{wall} lacks a skin: {stucco_name} or its siding")
            continue
        (sl, sh), (tl, th) = world_bbox([siding]), world_bbox([stucco])
        if any(abs(a - b) > MESH_TOL for a, b in zip(list(sl) + list(sh), list(tl) + list(th))):
            wrong.append(f"{siding.name} is not the same extent as {stucco.name}")
        if abs(_volume(siding) - _volume(stucco)) > VOL_TOL:
            wrong.append(f"{siding.name} holds {_volume(siding):.4f} cu ft, {stucco.name} "
                         f"{_volume(stucco):.4f}: one was cut differently")
        if [c.name for c in siding.users_collection] != ["Siding"]:
            wrong.append(f"{siding.name} is not in the Siding collection alone")
        # EVERY OPENING'S REVEAL, not the skin's: one tagged face anywhere
        # passed a skin whose other openings were left siding-coloured. Found
        # by review. Each opening needs a trim-slot face on each of its four
        # sides -- two jambs, the head and the sill, where the stack has one.
        if geo["cut"]:
            across = 1 if wall in ("Wall_front", "Wall_rear") else 0
            along = 1 - across
            tagged = [siding.matrix_world @ p.center for p in siding.data.polygons
                      if p.material_index == trim_slot]
            for o in (o for o in geo["built"] if o["wall"] == wall):
                a0, a1, z0, z1 = o["a0"], o["a1"], o["z0"], o["z1"]
                sides = {"jamb at " + f"{a0:.4f}": lambda c, a=a0: abs(c[along] - a) < MESH_TOL and z0 < c.z < z1,
                         "jamb at " + f"{a1:.4f}": lambda c, a=a1: abs(c[along] - a) < MESH_TOL and z0 < c.z < z1,
                         "head": lambda c: abs(c.z - z1) < MESH_TOL and a0 < c[along] < a1}
                if z0 > MESH_TOL:                        # a door has no sill in the skin
                    sides["sill"] = lambda c: abs(c.z - z0) < MESH_TOL and a0 < c[along] < a1
                missing = [s for s, hit in sides.items() if not any(hit(c) for c in tagged)]
                if missing:
                    wrong.append(f"{siding.name}: {o['id']} has no trim reveal at its "
                                 f"{', '.join(missing)}")
        for ob in (siding, stucco):
            if not ob.data.uv_layers:
                wrong.append(f"{ob.name} carries no UVs for its texture")
    return not wrong, "; ".join(wrong)


def _trim_inside_its_walls(spec, geo):
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


def _floor_on_the_slab(spec):
    """The floor finish is a material on ONE face: the slab's top, facing
    up at Z 0 (spec.finishes.floor). Not the underside, not an edge, and not
    missing -- a slab left untagged exports as concrete wall to wall and
    passes everything else. Found by review: nothing checked it."""
    slab = bpy.data.objects.get("Slab")
    if slab is None:
        return False, "no Slab"
    slot = _floor_slot(spec)
    tagged = [p for p in slab.data.polygons if p.material_index == slot]
    if len(tagged) != 1:
        return False, f"{len(tagged)} slab faces carry the floor slot {slot}, not 1"
    p = tagged[0]
    z = (slab.matrix_world @ p.center).z
    if p.normal.z <= UP or abs(z) > MESH_TOL:
        return False, f"the floor slot is on a face at z {z:.4f} facing {tuple(round(c, 2) for c in p.normal)}"
    return True, ""


# ---------------------------------------------------------------------------
# fixtures (#134). What each built object must be, worked out here from
# spec.fixtures -- drawn plan, declared heights -- and compared with the
# MESH, never with the boxes _build_fixtures made (rule 29).
# ---------------------------------------------------------------------------
def _fixture_targets(spec):
    """{object: (drawn key, bottom, top)} for every box-built fixture."""
    h = {k: v["ft"] for k, v in spec["fixtures"]["heights"].items()}
    base = h["counter_top"] - h["countertop"]
    return {
        "Fix_counter": ("counter", 0.0, base),
        "Fix_countertop": ("counter", base, h["counter_top"]),
        "Fix_dishwasher": ("dishwasher", 0.0, base),
        "Fix_sink": ("sink", h["counter_top"] - h["sink_basin"], h["counter_top"] + h["sink_rim"]),
        "Fix_range": ("range", 0.0, h["range"]),
        "Fix_refrigerator": ("refrigerator", 0.0, h["refrigerator"]),
        "Fix_vanity": ("vanity", 0.0, h["vanity"]),
        "Fix_tub": ("tub", 0.0, h["tub"]),
        "Fix_washer_dryer": ("washer_dryer", 0.0, h["washer_dryer"]),
        "Fix_toilet": ("toilet", 0.0, h["toilet_tank"]),
    }


def _fixtures_where_drawn(spec, geo):
    """Each fixture's mesh against A-1.0 and the declared heights.

    PLAN: every side is where A-1.0 draws it, or on a wall's stud face no
    further from the drawn side than that wall's finish -- the one move the
    build is allowed (spec.fixtures). A side moved further, or moved to
    anything but a stud face, fails.
    NO GAP: no side stands off a stud face by a finish's thickness or less,
    which is the gap a fixture built exactly as drawn would leave.
    HEIGHT: bottom and top as spec.fixtures.heights declares."""
    con = spec["construction"]
    finish = max(con["exterior_wall"]["interior_finish"]["ft"],
                 con["interior_wall"]["interior_finish"]["ft"])
    faces = [f for fl in room_faces(spec).values() for f in fl]
    drawn = spec["fixtures"]["drawn"]
    wrong = []
    for name, (key, z0, z1) in _fixture_targets(spec).items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            wrong.append(f"{name} was not built")
            continue
        lo, hi = world_bbox([ob])
        for axis, i in (("x", 0), ("y", 1)):
            for side, got in ((0, lo[i]), (1, hi[i])):
                want = drawn[key][axis][side]
                if abs(got - want) <= MESH_TOL:
                    continue
                on_a_face = any(abs(got - f["at"]) <= MESH_TOL
                                and (f["along"] == ("y" if axis == "x" else "x")) for f in faces)
                if abs(got - want) > finish + FACE_TOL or not on_a_face:
                    wrong.append(f"{name}'s {axis} {'lo' if side == 0 else 'hi'} is {got:.4f}, "
                                 f"A-1.0 draws {want:.4f}")
        for f in faces:
            across = 0 if f["along"] == "y" else 1
            along = 1 - across
            if hi[along] <= f["from"] or lo[along] >= f["to"]:
                continue
            side = lo[across] if f["into"] > 0 else hi[across]
            gap = (side - f["at"]) * f["into"]
            if MESH_TOL < gap <= finish + FACE_TOL:
                wrong.append(f"{name} stands {gap * INCHES_PER_FOOT:.2f} in off a stud face at "
                             f"{f['at']:.4f}: the gap the gyp board's thickness leaves")
        if abs(lo[2] - z0) > MESH_TOL or abs(hi[2] - z1) > MESH_TOL:
            wrong.append(f"{name} stands {lo[2]:.4f}..{hi[2]:.4f}, declared {z0:.4f}..{z1:.4f}")
    return not wrong, "; ".join(wrong)


def _fixture_parts(spec):
    """What an outer box cannot see in the two COMPOUND fixtures. Found by
    review: a solid counter across the dishwasher's opening, or a toilet
    built as one block at the tank's height, has the same outer box as the
    right one and passed _fixtures_where_drawn.

    So the MESH is asked about points worked out from spec.fixtures:
    - the counter's base cabinets are there either side of the dishwasher,
      and NOT in the dishwasher's opening;
    - the toilet's tank is there at the tank's height, and its bowl is NOT
      there above the bowl's rim."""
    from mathutils import Vector
    fx = spec["fixtures"]
    h = {k: v["ft"] for k, v in fx["heights"].items()}
    drawn = fx["drawn"]
    base = h["counter_top"] - h["countertop"]
    wrong = []
    counter = bpy.data.objects.get("Fix_counter")
    toilet = bpy.data.objects.get("Fix_toilet")
    if counter is None or toilet is None:
        return False, "Fix_counter or Fix_toilet was not built"
    cnt, dw = drawn["counter"], drawn["dishwasher"]
    mid_x = sum(cnt["x"]) / 2
    for label, y in (("the cabinets before the dishwasher", (cnt["y"][0] + dw["y"][0]) / 2),
                     ("the cabinets after the dishwasher", (dw["y"][1] + cnt["y"][1]) / 2)):
        if not inside_mesh(counter, Vector((mid_x, y, base / 2))):
            wrong.append(f"Fix_counter has no base cabinet in {label}")
    if inside_mesh(counter, Vector((mid_x, sum(dw["y"]) / 2, base / 2))):
        wrong.append("Fix_counter fills the dishwasher's opening")
    tl, tk = drawn["toilet"], drawn["toilet_tank"]
    tx = sum(tl["x"]) / 2
    between = (h["toilet_bowl"] + h["toilet_tank"]) / 2      # above the rim, below the tank's top
    if not inside_mesh(toilet, Vector((tx, sum(tk["y"]) / 2, between))):
        wrong.append("Fix_toilet has no tank standing above the bowl's rim")
    if inside_mesh(toilet, Vector((tx, (tl["y"][0] + tk["y"][0]) / 2, between))):
        wrong.append("Fix_toilet's bowl stands above its rim height")
    return not wrong, "; ".join(wrong)


def _water_heater_as_published(spec):
    """The named equipment (#134): Rheem's published height and diameter,
    centred where A-1.0 draws its circle. A cylinder of WH_SIDES faces is at
    least cos(pi / WH_SIDES) of its diameter across its flats."""
    import math
    ob = bpy.data.objects.get("Fix_water_heater")
    if ob is None:
        return False, "Fix_water_heater was not built"
    wh, circle = spec["fixtures"]["water_heater"], spec["fixtures"]["drawn"]["water_heater"]
    d, height = wh["diameter"]["ft"], wh["height"]["ft"]
    lo, hi = world_bbox([ob])
    wrong = []
    for i, axis in ((0, "x"), (1, "y")):
        centre = sum(circle[axis]) / 2
        if abs((lo[i] + hi[i]) / 2 - centre) > FACE_TOL:
            wrong.append(f"its {axis} centre is {(lo[i] + hi[i]) / 2:.4f}, the drawn circle's {centre:.4f}")
        across = hi[i] - lo[i]
        if not (d * math.cos(math.pi / WH_SIDES) - MESH_TOL <= across <= d + MESH_TOL):
            wrong.append(f"it is {across * INCHES_PER_FOOT:.2f} in across {axis}; Rheem publishes "
                         f"{d * INCHES_PER_FOOT:.2f} in")
    if abs(lo[2]) > MESH_TOL or abs(hi[2] - height) > MESH_TOL:
        wrong.append(f"it stands {lo[2]:.4f}..{hi[2]:.4f}; Rheem publishes {height:.4f} ft")
    return not wrong, "; ".join(wrong)


def _mesh_boxes(ob):
    """The boxes a multibox mesh was built from, read back off its vertices,
    VERTS_PER_BOX at a time, in world space."""
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    out = []
    for i in range(0, len(vs), VERTS_PER_BOX):
        chunk = vs[i:i + VERTS_PER_BOX]
        out.append((min(v.x for v in chunk), max(v.x for v in chunk),
                    min(v.y for v in chunk), max(v.y for v in chunk),
                    min(v.z for v in chunk), max(v.z for v in chunk)))
    return out


def _overlap(a, b, tol=MESH_TOL):
    """Do two plan boxes (x0, x1, y0, y1) overlap by more than `tol`?"""
    ax0, ax1, ay0, ay1 = a
    bx0, bx1, by0, by1 = b
    return ax0 < bx1 - tol and bx0 < ax1 - tol and ay0 < by1 - tol and by0 < ay1 - tol


def _furniture_placed(spec, geo):
    """Every furniture box, read off the MESH, against what the plan and the
    spec say it must leave alone. Worked out here from the spec -- walls,
    partitions, the fixtures' drawn plan, the declared walkways -- never from
    place_box's arithmetic (rule 29).

    Arrangements of ONE group are alternatives for one floor and may overlap
    each other, as the barn cabin's bed and office do; two groups may not,
    because a buyer can show both at once."""
    fx = spec["fixtures"]["furniture"]
    W, D, t = geo["W"], geo["D"], geo["t"]
    layout = spec["interior_partitions"]["layout"]
    it = layout["thickness"]["ft"]
    underfoot = fx["underfoot"]["ft"]
    solids = []                                        # (label, plan box) furniture must not enter
    for row in layout["partitions"]:
        lo, hi = _partition_band(row, it)
        a, b = sorted((row["from_ft"], row["to_ft"]))
        solids.append((row["id"], (a, b, lo, hi) if row["runs_along"] == "X" else (lo, hi, a, b)))
    for name, f in spec["fixtures"]["drawn"].items():
        if isinstance(f, dict):
            solids.append((f"the {name}", (f["x"][0], f["x"][1], f["y"][0], f["y"][1])))
    runs = [(r["id"], (r["x0"], r["x1"], r["y0"], r["y1"])) for r in fx["keep_clear"]["runs"]]
    groups = {}
    for g in (spec.get("variants") or {}).get("presence") or []:
        for prefix in g.get("controls") or ():
            if prefix.startswith("Furn_"):
                groups[prefix] = g["id"]
    wrong, by_group = [], {}
    arrangements = {a["id"] for a in fx["arrangements"]}
    built = {ob.name for ob in geo["furniture"]}
    for arr in sorted(arrangements):
        if not any(n.startswith(f"Furn_{arr}_") for n in built):
            wrong.append(f"{arr} was not built")
    for ob in geo["furniture"]:
        group = next((g for pfx, g in groups.items() if ob.name.startswith(pfx)), None)
        if group is None:
            wrong.append(f"{ob.name} is controlled by no presence group")
            # NOT GROUPED: a None among the group ids made sorted() raise
            # instead of this gate naming the object. Found by review.
        for x0, x1, y0, y1, _, z1 in _mesh_boxes(ob):
            plan = (x0, x1, y0, y1)
            if x0 < t - MESH_TOL or x1 > W - t + MESH_TOL or y0 < t - MESH_TOL or y1 > D - t + MESH_TOL:
                wrong.append(f"{ob.name} runs into an exterior wall at X {x0:.3f}..{x1:.3f}, Y {y0:.3f}..{y1:.3f}")
            for label, s in solids:
                if _overlap(plan, s):
                    wrong.append(f"{ob.name} runs into {label}")
            if z1 > underfoot + MESH_TOL:
                for label, r in runs:
                    if _overlap(plan, r):
                        wrong.append(f"{ob.name} stands in {label}")
            if group is not None:
                by_group.setdefault(group, []).append((ob.name, plan))
    names = sorted(by_group)
    for i, g in enumerate(names):
        for h in names[i + 1:]:
            for n1, b1 in by_group[g]:
                for n2, b2 in by_group[h]:
                    if _overlap(b1, b2):
                        wrong.append(f"{n1} ({g}) and {n2} ({h}) overlap, and both can be shown at once")
    for arr in sorted(arrangements):
        obs = [ob for ob in geo["furniture"] if ob.name.startswith(f"Furn_{arr}_")]
        if obs and abs(min(world_bbox([ob])[0][2] for ob in obs)) > MESH_TOL:
            wrong.append(f"{arr} does not stand on the floor")
    return not wrong, "; ".join(sorted(set(wrong)))


def _canopy_hung(spec, geo, colls):
    """spec.variants.canopy's `placement`, on the MESH: each expectation is
    worked out here from the spec's readings and A-3.4's strings, never
    read back from _build_canopy's arithmetic (rule 29)."""
    c = spec["variants"]["canopy"]
    fe, se, pl = c["front_elevation"], c["side_elevation"], c["a34_plan"]
    tol = c["tolerance_in"]["value"] / INCHES_PER_FOOT
    face, _ = outer_face(spec, "Wall_front")
    wrong = []
    # ITS OWN COLLECTION, AND NOTHING ELSE IN IT: hiding the collection hides
    # the canopy whole and touches nothing of the building.
    coll = colls["Canopy"]
    named = {o.name for o in bpy.data.objects if o.name.startswith("Canopy_")}
    held = {o.name for o in coll.objects}
    wrong += [f"{n} is not in the Canopy collection" for n in sorted(named - held)]
    wrong += [f"{n} is in the Canopy collection and is not the canopy" for n in sorted(held - named)]
    frame, slats = bpy.data.objects.get("Canopy_frame"), bpy.data.objects.get("Canopy_slats")
    braces = sorted((o for o in coll.objects if o.name.startswith("Canopy_brace_")), key=lambda o: o.name)
    if frame is None or slats is None or len(braces) != len(fe["brace_x"]):
        return False, "; ".join(wrong + ["the frame, the slats or a brace was not built"])
    (fx0, fy0, fz0), (fx1, fy1, fz1) = world_bbox([frame])
    # WHERE A-2.0 DRAWS IT: centred on the front elevation's reading
    if abs((fx0 + fx1) / 2 - sum(fe["x"]) / 2) > tol:
        wrong.append(f"it is centred at X {(fx0 + fx1) / 2:.4f}, the front elevation draws {sum(fe['x']) / 2:.4f}")
    if abs(fz0 - fe["underside"]) > MESH_TOL:
        wrong.append(f"its underside is at {fz0:.4f}, the elevations draw {fe['underside']}")
    # AT A-3.4'S SIZE, from the wall's modelled outer face
    for label, got, want in (("width", fx1 - fx0, c["width"]["ft"]),
                             ("projection", fy1 - face, c["projection"]["ft"]),
                             ("depth", fz1 - fz0, c["depth"]["ft"])):
        if abs(got - want) > MESH_TOL:
            wrong.append(f"its {label} is {got:.4f}, A-3.4 gives {want}")
    if abs(fy0 - face) > MESH_TOL:
        wrong.append(f"its wall side is at Y {fy0:.4f}, not the front wall's outer face {face:.4f}")
    boxes = _mesh_boxes(slats)
    if len(boxes) != 2 * len(pl["slats"]):
        wrong.append(f"{len(boxes)} slats, where A-3.4 draws {len(pl['slats'])} in each of two bays")
    for sx0, sx1, sy0, sy1, _, sz1 in boxes:
        if abs(sz1 - fz1) > MESH_TOL or sx0 < fx0 - MESH_TOL or sx1 > fx1 + MESH_TOL \
                or sy0 < fy0 - MESH_TOL or sy1 > fy1 + MESH_TOL:
            wrong.append(f"a slat at X {sx0:.3f}..{sx1:.3f} is not flush in the frame's top")
            break
    # EACH BRACE from its wall plate, where the front elevation draws it, to
    # the frame's top, where the side elevation lands it
    land = c["projection"]["ft"] - (se["projection"] - se["brace_lands_from_wall"])
    for ob, bx in zip(braces, sorted(fe["brace_x"])):
        vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
        # TOUCHING, not near: the rod's nearest point to the wall is ON the
        # wall's face, within the plate; its lowest point is ON the frame's
        # top, where the side elevation lands it. Found by review: a
        # half-inch tolerance here passed a rod floating off both.
        wall_pt, low = min(vs, key=lambda v: v.y), min(vs, key=lambda v: v.z)
        if abs(sum(v.x for v in vs) / len(vs) - bx) > tol:
            wrong.append(f"{ob.name} is not at the front elevation's X {bx}")
        if abs(wall_pt.y - face) > MESH_TOL:
            wrong.append(f"{ob.name} stops at Y {wall_pt.y:.4f}, off the wall's face {face:.4f}")
        if not fe["wall_connection"][0] - MESH_TOL <= wall_pt.z <= fe["wall_connection"][1] + MESH_TOL:
            wrong.append(f"{ob.name} meets the wall at {wall_pt.z:.4f}, not its plate at "
                         f"{fe['wall_connection'][0]}..{fe['wall_connection'][1]}")
        if abs(low.z - fz1) > MESH_TOL or abs(low.y - (face + land)) > tol:
            wrong.append(f"{ob.name} lands at Y {low.y:.4f} Z {low.z:.4f}, not on the frame at "
                         f"Y {face + land:.4f} Z {fz1:.4f}")
    # OUTSIDE, BELOW THE ROOF, CLEAR OF THE OPENINGS AND THE SIDING TRIM
    parts = [(frame.name, b) for b in _mesh_boxes(frame)] + [(slats.name, b) for b in boxes] + \
            [(o.name, tuple(v for pair in zip(*world_bbox([o])) for v in pair)) for o in braces]
    # no roof at this Y means no limit above the canopy, not an extrapolated one
    under = (geo["roof_planes"].under_y(face) if geo["roof_planes"].covers_y(face)
             else float("inf"))
    wt = {w["mark"]: w for w in spec["openings"]["window_types"]["types"]}
    dt = {d["mark"]: d for d in spec["openings"]["door_types"]["types"]}
    holes = []
    for row in spec["openings"]["front_wall"]["openings"]:
        if row["id"].startswith("W-"):
            typ = wt[row["type"]]
            holes.append((row["id"], row["x0"], row["x1"], typ["sill"]["ft"], typ["sill"]["ft"] + typ["height"]["ft"]))
        else:
            holes.append((row["id"], row["x0"], row["x1"], 0.0, dt[row["type"]]["height"]["ft"]))
    trim = bpy.data.objects.get("Trim_ext_siding_front")
    trim_boxes = _mesh_boxes(trim) if trim is not None else []
    # THE LEDGER BEARS ON DOOR 1'S HEAD TRIM, and nothing else touches trim
    # (decided 2026-09-29). Under siding, the head band over door 1 -- its
    # 6'-8" head plus the borrowed trim.head_casing_height -- rises past the
    # canopy's drawn 7'-0" underside; A-3.4 fixes the canopy through a trim
    # board, and drawn beats assumed, so the ledger may sit over that band's
    # top -- its underside never below the drawn 7'-0", and the band never
    # higher than door 1's head plus its borrowed height.
    d1 = next(r for r in spec["openings"]["front_wall"]["openings"] if r["id"] == "D-1")
    band_top = dt[d1["type"]]["height"]["ft"] + spec["trim"]["head_casing_height"]["ft"]
    m = pl["member"]
    for name, (x0, x1, y0, y1, z0, z1) in parts:
        if y0 < face - MESH_TOL:
            wrong.append(f"{name} reaches Y {y0:.4f}, inside the front wall's outer face {face:.4f}")
        if z1 > under + MESH_TOL:
            wrong.append(f"{name} rises to {z1:.4f}, above the roof's underside {under:.4f}")
        for hid, h0, h1, hz0, hz1 in holes:
            if _overlap((x0, x1, z0, z1), (h0, h1, hz0, hz1)):
                wrong.append(f"{name} is in front of {hid}")
        ledger = name == frame.name and abs(y0 - face) < MESH_TOL and abs(y1 - y0 - m) < MESH_TOL
        for tx0, tx1, ty0, ty1, tz0, tz1 in trim_boxes:
            if _overlap((x0, x1, y0, y1), (tx0, tx1, ty0, ty1)) and z0 < tz1 - MESH_TOL and tz0 < z1 - MESH_TOL:
                if ledger and abs(tz1 - band_top) < MESH_TOL and z0 >= fe["underside"] - MESH_TOL:
                    continue
                wrong.append(f"{name} runs into the front wall's siding trim at Z {tz0:.4f}..{tz1:.4f}")
                break
    return not wrong, "; ".join(sorted(set(wrong)))


def _ground_mounted(spec, geo):
    """spec.fixtures.condenser.placement_rule, clause by clause, on the MESH.
    Each expectation is worked out here from the spec -- A-1.1's plan, the
    side elevation, the pad, grade, the openings -- never read back from
    what _build_condenser made."""
    c = spec["fixtures"]["condenser"]
    tol = c["tolerance_in"]["value"] / INCHES_PER_FOOT
    W = spec["envelope"]["width"]["ft"]
    outer = W + spec["construction"]["exterior_wall"]["sheathing"]["ft"]
    grade = spec["levels"]["grade"]["ft"]
    se, plan = c["side_elevation"], c["plan"]
    unit, pad = bpy.data.objects.get("Equip_condenser"), bpy.data.objects.get("Equip_pad")
    if unit is None or pad is None:
        return False, "the condenser or its pad was not built"
    (ux0, uy0, uz0), (ux1, uy1, uz1) = world_bbox([unit])
    (px0, py0, pz0), (px1, py1, pz1) = world_bbox([pad])
    wrong = []
    # 1. on its own pad, and the pad on grade
    if abs(pz0 - grade) > MESH_TOL:
        wrong.append(f"the pad's bottom is at {pz0:.4f}, grade is {grade}")
    if abs(uz0 - pz1) > MESH_TOL:
        wrong.append(f"the unit stands at {uz0:.4f}, its pad's top is {pz1:.4f}")
    if ux0 < px0 - MESH_TOL or ux1 > px1 + MESH_TOL or uy0 < py0 - MESH_TOL or uy1 > py1 + MESH_TOL:
        wrong.append("the unit overhangs its pad")
    # EVERY FACE OF THE PAD, from the spec: its top where the side elevation
    # stands the unit, its wall side at the outer face, and the declared
    # margin on its three open sides. Found by review: checking only that
    # the unit sat somewhere on the pad let a thick pad lift the unit, or a
    # pad without its margins, pass.
    m = c["pad"]["margin"]["ft"]
    for label, got, want in (("top", pz1, c["pad"]["top"]["ft"]),
                             ("wall side", px0, outer),
                             ("outer side", px1, outer + (plan["x"][1] - plan["x"][0]) + m),
                             ("rear side", py0, plan["y"][0] - m),
                             ("front side", py1, plan["y"][1] + m)):
        if abs(got - want) > MESH_TOL:
            wrong.append(f"the pad's {label} is at {got:.4f}, the spec puts it at {want:.4f}")
    # 2. outside the building
    if min(ux0, px0) < outer - MESH_TOL:
        wrong.append(f"it reaches X {min(ux0, px0):.4f}, inside the X 24 wall's outer face at {outer:.4f}")
    # 3. where A-1.1 draws it, its wall side at the outer face
    if abs(ux0 - outer) > MESH_TOL:
        wrong.append(f"its wall side is at X {ux0:.4f}, not the outer face {outer:.4f}")
    if abs((ux1 - ux0) - (plan["x"][1] - plan["x"][0])) > tol:
        wrong.append(f"it is {ux1 - ux0:.4f} deep, A-1.1 draws {plan['x'][1] - plan['x'][0]:.4f}")
    if abs(uy0 - plan["y"][0]) > tol or abs(uy1 - plan["y"][1]) > tol:
        wrong.append(f"it stands at Y {uy0:.4f}..{uy1:.4f}, A-1.1 draws {plan['y'][0]}..{plan['y'][1]}")
    # 4. as tall as drawn, below the roof
    if abs((uz1 - uz0) - (se["top"] - se["base"])) > tol:
        wrong.append(f"it is {uz1 - uz0:.4f} tall, the side elevation draws {se['top'] - se['base']:.4f}")
    # No roof overhead (a unit placed beyond the rear overhang) means nothing to be
    # above; the position checks above report that mistake. The old Shed extrapolated
    # a surface there, and #167's plane refuses to, so the question is asked only
    # where there is a roof.
    roof_planes = geo["roof_planes"]
    if roof_planes.covers_y(uy0) and uz1 > roof_planes.under_y(uy0) + MESH_TOL:
        wrong.append(f"its top {uz1:.4f} is above the roof's underside {roof_planes.under_y(uy0):.4f}")
    # 5. blocking no opening in the wall behind it
    wt = {w["mark"]: w for w in spec["openings"]["window_types"]["types"]}
    for row in spec["openings"]["end_wall_x24"]["openings"]:
        if row["y1"] <= uy0 or row["y0"] >= uy1:
            continue
        if not row["id"].startswith("W-"):
            wrong.append(f"it stands in front of door {row['id']}")
        elif uz1 > wt[row["type"]]["sill"]["ft"] + MESH_TOL:
            wrong.append(f"it rises above {row['id']}'s sill in front of it")
    return not wrong, "; ".join(wrong)


def _no_degenerate():
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


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else HERE
    cut = "--no-openings" not in argv

    spec = load_spec(HERE / "spec.yaml")
    geo, colls = build(spec, cut_openings=cut)
    ok = report(spec, geo, colls)

    out.mkdir(parents=True, exist_ok=True)
    dest = out / "laurel_a1_460.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    print(f"\nsaved: {dest}")
    if not ok:
        raise SystemExit("one or more gates FAILED")


if __name__ == "__main__":
    main()
