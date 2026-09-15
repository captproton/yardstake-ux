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
    load_spec, box, box_geom, prism_geom, weld, multibox,
    difference, collection, world_bbox, mark_reveals, ft,
)

FAILED = []

# BOOKKEEPING, NOT DIMENSIONS. Every one of these is about meshes, arithmetic
# or printing; none is a length off a sheet. They are named and gathered here
# so test_build_literals.py can hold the rest of the file to zero -- the
# done-when PLAN.md sets for #129 is "no dimension literal appears in
# build.py", and a gate is worth more than a promise.
VOL_TOL = 1e-4          # cu ft; a boolean that removes nothing is off by whole feet
LEN_TOL = 1e-6          # ft, for comparing two lengths the spec already agrees on
PLANE_TOL = 1e-9        # ft, for a plane through two points it is defined by
CUT_MARGIN = 1.0        # ft a cutter stands proud of the wall, so no face is coplanar
SASH_DEPTH = 6          # a sash is this fraction of the wall depth, centred
RULE = 76               # characters across, for the printed report


def gate(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


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
        far = near + it if row["studs_toward"].startswith("+") else near - it
        lo, hi = sorted((near, far))
        a, b = sorted((row["from_ft"], row["to_ft"]))
        if row["runs_along"] == "X":
            profile = [(a, 0.0), (b, 0.0), (b, shed.under(lo)), (a, shed.under(lo))]
            # a wall running along X sits at one Y, so its head is level
            walls[row["id"]] = box(row["id"], a, b, lo, hi, 0.0, shed.under(lo), partitions)
        else:
            # running along Y, the head rakes with the roof
            profile = [(a, 0.0), (b, 0.0), (b, shed.under(b)), (a, shed.under(a))]
            v, f = prism_geom(profile, lo, hi, plane="yz")
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
    want_gone = {}          # wall -> volume its openings must remove
    sashes = []

    def cutter(name, wall, a0, a1, z0, z1, along, depth=None):
        """A hole through `wall`, spanning a0..a1 along the wall and z0..z1 up.

        The cutter is padded through the wall's whole depth, plus a margin, so
        the boolean removes material rather than imprinting edges on a
        coplanar face -- the defect #129 inherits the memory of from the barn
        cabin's P2 (see verify_openings.py, VOLUME).
        """
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
        want_gone[wall] = want_gone.get(wall, 0.0) + (a1 - a0) * depth * (z1 - z0)
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
                              z0=z0, z1=z1, along=along, row=row))

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
    volumes = {}
    if cut_openings:
        for wall, cl in cut_by_wall.items():
            before = _volume(walls[wall])
            difference(walls[wall], cl)
            volumes[wall] = (before, _volume(walls[wall]), want_gone[wall])

    # ---- sashes and leaves ------------------------------------------------
    # Every opening gets what it is: a window gets a sash, a door gets a leaf.
    # An opening with nothing in it reads as a hole in a wall, and the gate
    # below counts them, so this is not optional.
    for o in built:
        lo, hi = _wall_band(walls, o["wall"], o["along"])
        if o["along"] == "x":
            specs = [(o["a0"], o["a1"], lo, hi, o["z0"], o["z1"])]
        else:
            specs = [(lo, hi, o["a0"], o["a1"], o["z0"], o["z1"])]
        kind = "Sash" if o["id"].startswith("W-") else "Leaf"
        ob = multibox(f"{kind}_{o['id']}", specs, openings)
        _thin(ob, o["along"], lo, hi)
        sashes.append(ob)

    geo = dict(W=W, D=D, t=t, it=it, shed=shed, walls=walls, roof=roof,
               built=built, sashes=sashes, volumes=volumes)
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


def _thin(ob, along, lo, hi):
    """Leave the pane/leaf as a thin plate centred in the wall's depth."""
    import bmesh
    mid = (lo + hi) / 2
    half = (hi - lo) / (SASH_DEPTH * 2)
    idx = 1 if along == "x" else 0
    for v in ob.data.vertices:
        co = list(v.co)
        co[idx] = mid - half if co[idx] < mid else mid + half
        v.co = co


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
    ov = rf["overhangs"]
    gate(abs((bb[1][0] - bb[0][0]) - (W + 2 * ov["ends"]["ft"])) < LEN_TOL,
         f'roof spans the width plus both end overhangs ({ft(W + 2 * ov["ends"]["ft"])})')
    gate(abs(shed.under(0.0) - lv["top_of_plate_rear"]["ft"]) < PLANE_TOL
         and abs(shed.under(D) - lv["top_of_plate_front"]["ft"]) < PLANE_TOL,
         f'the roof plane meets T.P. 1 ({ft(shed.under(0.0))}) and T.P. 2 ({ft(shed.under(D))})')
    gate(shed.under(D) > shed.under(0.0),
         "the roof rises toward the front (+Y), as the side elevations draw it")

    # the frame is not mirrored — checked on GEOMETRY, not on the spec
    ok, why = _frame_not_mirrored(spec, geo)
    gate(ok, "not mirrored: D and E open on the X 24 wall, the C windows on X 0", why)

    # every schedule row produced a cut opening with a sash
    ok, why = _every_row_built(spec, geo)
    gate(ok, "every schedule row produced a cut opening with a sash or a leaf", why)

    ok, why = _no_degenerate()
    gate(ok, "no NaN or degenerate geometry", why)

    print("=" * RULE)
    return not FAILED


def _frame_not_mirrored(spec, geo):
    """D and E are on the X 24 wall; the C windows on X 0. A-2.0's SIDE (LEFT)
    ELEVATION draws D and E, and the building's left side seen from the front
    is +X when the front faces +Y and Z is up. Checked on the built objects."""
    wrong = []
    for o in geo["built"]:
        ty = str(o["row"].get("type"))
        if ty in ("D", "E") and o["wall"] != "Wall_x24":
            wrong.append(f"{o['id']} ({ty}) is in {o['wall']}")
        if ty == "C" and o["wall"] not in ("Wall_x0", "Wall_rear"):
            wrong.append(f"{o['id']} (C) is in {o['wall']}")
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
    for wall, (before, after, want) in geo["volumes"].items():
        got = before - after
        if abs(got - want) > VOL_TOL:
            missing.append(f"{wall} lost {got:.4f} cu ft, its openings are {want:.4f}")
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
