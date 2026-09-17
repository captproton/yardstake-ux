"""
build.py — parametric massing model of the Sacramento A1 "Laurel" 460sf ADU (#129).

Reads spec.yaml. CONTAINS NO BUILDING DIMENSION. Every length, height, slope
and offset is read from the spec; the only literals are geometric constants
(2 for halving, 12 for a pitch denominator) and mesh bookkeeping.

Run:
    blender --background --python models/laurel_a1_460/build.py -- [--out DIR]
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
and every opening in the two schedules cut with a sash or a leaf.

WHAT IT DOES NOT: fixtures (#134), finishes and trim (#132, #133), the
1-bedroom option (a configurator variant, spec.variants), and the optional
entry canopy (#144, whose dimensions are not on a harvested sheet).
"""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parents[1]))          # buyer/3D, where adu_kit lives
from adu_kit.kernel import (  # noqa: E402,F401
    load_spec, box, box_geom, prism_geom, weld, multibox, sash_geom,
    difference, collection, world_bbox, mark_reveals, ft,
)

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
class Shed:
    """The one roof plane, as a function of Y.

    A-2.0 marks the slope 1" / 1'-0", and it also dimensions T.P. 1 and T.P. 2.
    Those disagree: 19 1/2" over 19'-2" is 1.017" per foot. The PLATE HEIGHTS
    WIN, because they are what the elevations dimension and what #130 gates,
    and because a slope read off a marked ratio would put the front plate
    3/8" below the height four elevations draw.
    """

    def __init__(self, spec):
        lv, env = spec["levels"], spec["envelope"]
        self.rear = lv["top_of_plate_rear"]["ft"]
        self.front = lv["top_of_plate_front"]["ft"]
        self.depth = env["depth"]["ft"]
        self.slope = (self.front - self.rear) / self.depth

    def under(self, y):
        """Underside of the roof at this Y — the plane through both plates."""
        return self.rear + self.slope * y


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
    shed = Shed(spec)

    shell = collection("Shell")
    partitions = collection("Partitions")
    roof_coll = collection("Roof")
    openings = collection("Openings")
    site = collection("Site")

    # ---- slab ------------------------------------------------------------
    # Slab on grade: its top IS the finished floor, so it sits below Z 0.
    box("Slab", 0.0, W, 0.0, D, -slab_t, 0.0, site)

    # ---- exterior walls ---------------------------------------------------
    # Each wall runs from the slab to the underside of the roof, so the
    # ceilings follow the roof line (A-1.0, "CEILINGS FOLLOW ROOF LINE") with
    # no separate ceiling plane to keep in step. The end walls rake, so they
    # are prisms in YZ; the front and rear walls are level, so they are boxes.
    walls = {}
    walls["Wall_rear"] = box("Wall_rear", 0.0, W, 0.0, t, 0.0, shed.under(0.0), shell)
    walls["Wall_front"] = box("Wall_front", 0.0, W, D - t, D, 0.0, shed.under(D), shell)
    for name, x0, x1 in (("Wall_x0", 0.0, t), ("Wall_x24", W - t, W)):
        profile = [(0.0, 0.0), (D, 0.0), (D, shed.under(D)), (0.0, shed.under(0.0))]
        v, f = prism_geom(profile, x0, x1, plane="yz")
        walls[name] = weld(name, [(v, f)], shell)

    # The modelled exterior surface: face of stud plus sheathing, with the
    # cladding carried as a material (cladding_modelled is zero, and says why).
    # ONE OBJECT PER WALL, not one skin. A single welded skin wraps all four
    # sides, and an opening's cutter spans its wall's whole depth -- so a hole
    # in the front would have been punched straight through the rear skin as
    # well. Per-wall objects keep each cut inside the face it belongs to.
    skin_of = {}
    if sheath:
        faces = {
            "Wall_rear":  box_geom(-sheath, W + sheath, -sheath, 0.0, 0.0, shed.under(0.0)),
            "Wall_front": box_geom(-sheath, W + sheath, D, D + sheath, 0.0, shed.under(D)),
        }
        rake = [(0.0, 0.0), (D, 0.0), (D, shed.under(D)), (0.0, shed.under(0.0))]
        faces["Wall_x0"] = prism_geom(rake, -sheath, 0.0, plane="yz")
        faces["Wall_x24"] = prism_geom(rake, W, W + sheath, plane="yz")
        for wall, geom in faces.items():
            name = wall.replace("Wall_", "Sheathing_")
            walls[name] = weld(name, [geom], shell)
            skin_of[wall] = name

    # ---- interior partitions ---------------------------------------------
    layout = spec["interior_partitions"]["layout"]
    for row in layout["partitions"]:
        near = row["at_ft"]
        far = near + it if _sign(row["id"], row["studs_toward"]) > 0 else near - it
        lo, hi = sorted((near, far))
        a, b = sorted((row["from_ft"], row["to_ft"]))
        # EVERY PARTITION IS A YZ PRISM, both orientations, because the roof
        # rises with Y and so does the head of any wall with any extent in Y
        # -- INCLUDING its own thickness. A wall running along X was built as
        # a box capped at shed.under(lo), which left a triangular gap to the
        # roof on its +Y face: small (0.30" here) but a real hole, and a
        # contradiction of layout.height's "to: roof_underside". Found by
        # review; measured on the built model before it was fixed.
        if _axis(row["id"], row["runs_along"]) == "X":
            profile = [(lo, 0.0), (hi, 0.0), (hi, shed.under(hi)), (lo, shed.under(lo))]
            extrude = (a, b)                       # along X
        else:
            profile = [(a, 0.0), (b, 0.0), (b, shed.under(b)), (a, shed.under(a))]
            extrude = (lo, hi)                     # across X, at one Y band
        v, f = prism_geom(profile, extrude[0], extrude[1], plane="yz")
        walls[row["id"]] = weld(row["id"], [(v, f)], partitions)

    # ---- the shed roof ----------------------------------------------------
    # One plane, T.P. 1 at the rear to T.P. 2 at the front, carried out over
    # the overhangs. Drawn as a YZ prism so the slope is the geometry rather
    # than a stack of steps, and extruded past both ends by the end overhang.
    asm = rf["assembly"]["modelled_thickness"]["ft"]
    ov = rf["overhangs"]
    y0, y1 = -ov["rear"]["ft"], D + ov["front"]["ft"]
    x0, x1 = -ov["ends"]["ft"], W + ov["ends"]["ft"]
    profile = [(y0, shed.under(y0)), (y1, shed.under(y1)),
               (y1, shed.under(y1) + asm), (y0, shed.under(y0) + asm)]
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

    geo = dict(W=W, D=D, t=t, it=it, shed=shed, walls=walls, roof=roof,
               built=built, sashes=sashes, volumes=volumes, cut=cut_openings,
               depths=depths, skin_of=skin_of)
    return geo, dict(Shell=shell, Partitions=partitions, Roof=roof_coll,
                     Openings=openings, Site=site)


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
    W, D, shed = geo["W"], geo["D"], geo["shed"]
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

    gate(shed.under(D) > shed.under(0.0),
         "the roof rises toward the front (+Y), as the side elevations draw it")

    ok, why = _roof_top_at_the_front_edge(spec, geo)
    gate(ok, f'the roof top at the front edge is A-2.0\'s '
             f'{ft(lv["roof_top_at_front_edge"]["ft"])}', why)

    ok, why = _every_partition_built(spec, geo)
    gate(ok, "every partition in the spec was built, where the spec puts it", why)

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
    the roof was laid out from -- rule 29 -- and `shed.under(0)` is literally
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
        skin = geo["skin_of"].get(o["wall"])
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
