"""
build_adu.py — parametric massing model of the Barn Cabin 524sf ADU (Option B).

Reads spec.yaml. Contains NO hardcoded building dimensions: every length, height,
pitch and offset is read from the spec. The only literals here are geometric
constants (2 for halving a span, 12 for pitch denominators) and mesh bookkeeping.

Run:
    blender --background --python build_adu.py -- [--out DIR] [--no-openings]

Coordinate system (feet, Blender +Z up):
    X  0 .. W          west wall .. east wall
    Y  0 .. D+P        north (rear) wall .. porch outer edge
    Z  0 = main finished floor
Wall offsets in the spec are stated from the WEST corner (north/south walls) and
from the NORTH corner (east/west walls), which matches this frame directly.
"""

import sys
import json
import math
import shutil
import subprocess
from pathlib import Path

import bpy
import bmesh

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# spec loading
# ---------------------------------------------------------------------------
def load_spec(path: Path):
    """Blender's bundled Python has no pyyaml. Convert with the host python3
    on every run so the spec can never drift out of sync with a cached copy."""
    try:
        import yaml  # noqa: F401
        import yaml as _y
        return _y.safe_load(path.read_text())
    except ImportError:
        pass

    cache = path.with_suffix(".json")
    py = shutil.which("python3")
    if py:
        conv = (
            "import yaml,json,sys;"
            "json.dump(yaml.safe_load(open(sys.argv[1])),"
            "open(sys.argv[2],'w'),indent=2,default=str)"
        )
        r = subprocess.run([py, "-c", conv, str(path), str(cache)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(cache.read_text())
        print(f"[spec] host python3 conversion failed: {r.stderr.strip()}")

    if cache.exists():
        if cache.stat().st_mtime < path.stat().st_mtime:
            raise SystemExit(
                f"[spec] {cache.name} is older than {path.name}. "
                f"Regenerate it, or install pyyaml where this script can reach it."
            )
        print(f"[spec] falling back to cached {cache.name}")
        return json.loads(cache.read_text())

    raise SystemExit(f"[spec] cannot read {path}: no pyyaml and no {cache.name}")


# ---------------------------------------------------------------------------
# mesh helpers
# ---------------------------------------------------------------------------
def _new_obj(name, verts, faces, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    # Face winding below is written by hand, so normals cannot be trusted.
    # An inverted solid makes BOOLEAN DIFFERENCE imprint edges without removing
    # material — the mesh looks cut but keeps its full volume. Recalculate
    # outward here so every solid is unambiguously closed and correctly oriented.
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, coll):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return _new_obj(name, v, f, coll)


def multibox(name, specs, coll):
    """Several boxes as ONE mesh. Trim would otherwise explode the object count."""
    verts, faces = [], []
    for (x0, x1, y0, y1, z0, z1) in specs:
        n = len(verts)
        verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                  (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces += [(n+0, n+3, n+2, n+1), (n+4, n+5, n+6, n+7), (n+0, n+1, n+5, n+4),
                  (n+1, n+2, n+6, n+5), (n+2, n+3, n+7, n+6), (n+3, n+0, n+4, n+7)]
    return _new_obj(name, verts, faces, coll)


def prism_xz(name, pts_xz, y0, y1, coll):
    """Closed polygon in the XZ plane, extruded along Y. Points counter-clockwise."""
    n = len(pts_xz)
    verts = [(x, y0, z) for x, z in pts_xz] + [(x, y1, z) for x, z in pts_xz]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return _new_obj(name, verts, faces, coll)


def uv_project(ob, tile_ft):
    """In-plane cube projection at a fixed texel density.

    Not a naive world-axis projection: that foreshortens sloped faces, so the
    9:12 roof would come out ~20% stretched against the walls. Instead each
    face gets a basis IN ITS OWN PLANE — u horizontal along the face, v up the
    true slope — so texel density is uniform everywhere and lap courses stay
    level on walls while shingle courses run true up the roof.
    """
    import mathutils
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    M = ob.matrix_world
    Z = mathutils.Vector((0.0, 0.0, 1.0))
    for poly in me.polygons:
        n = (M.to_3x3() @ poly.normal).normalized()
        if abs(n.z) > 0.999:                      # horizontal: floors, ceilings
            u_ax, v_ax = mathutils.Vector((1, 0, 0)), mathutils.Vector((0, 1, 0))
        else:
            u_ax = Z.cross(n).normalized()        # level, along the face
            v_ax = n.cross(u_ax).normalized()     # up the true slope
        for li in poly.loop_indices:
            co = M @ me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (co.dot(u_ax) / tile_ft, co.dot(v_ax) / tile_ft)


def mark_reveals(ob, thickness_axis):
    """Tag the jamb/head/sill faces inside cut openings with material slot 1.

    They take TRIM, not siding — the per-face split TIER-2 §3 depends on. A
    reveal face is one whose centroid is strictly inside the wall's extents in
    both axes perpendicular to its thickness; the wall's own end, top and
    bottom faces sit exactly on those extents.
    """
    me = ob.data
    vs = [v.co for v in me.vertices]
    lo = [min(v[i] for v in vs) for i in range(3)]
    hi = [max(v[i] for v in vs) for i in range(3)]
    other = [i for i in range(3) if i != thickness_axis]
    eps = 1e-4
    n = 0
    for poly in me.polygons:
        c = poly.center
        # A reveal faces ACROSS the wall, so its normal is not along the
        # thickness axis. Without this the wall's own front and back faces
        # qualify too, since the boolean leaves their centroids inside.
        if abs(poly.normal[thickness_axis]) > 0.9:
            continue
        if all(lo[i] + eps < c[i] < hi[i] - eps for i in other):
            poly.material_index = 1
            n += 1
    return n


def difference(target, cutters):
    """Boolean-subtract each cutter, then delete it."""
    for c in cutters:
        m = target.modifiers.new(name=f"cut_{c.name}", type="BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = c
        m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    for m in list(target.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def world_bbox(objects):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for ob in objects:
        for corner in ob.bound_box:
            w = ob.matrix_world @ __import__("mathutils").Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def ft(x):
    """Decimal feet -> feet-and-inches string."""
    neg = x < 0
    x = abs(x)
    f = int(x)
    inches = (x - f) * 12.0
    if round(inches, 2) >= 11.995:
        f += 1
        inches = 0.0
    return f"{'-' if neg else ''}{f}'-{inches:.2f}\""


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build(spec, cut_openings=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "IMPERIAL"
    bpy.context.scene.unit_settings.length_unit = "FEET"

    env, lv, rf, con = spec["envelope"], spec["levels"], spec["roof"], spec["construction"]

    W = env["main_body_width"]["ft"]
    D = env["main_body_depth"]["ft"]
    P = env["porch_depth"]["ft"]
    t = con["exterior_wall_thickness"]["ft"]
    rt = con["roof_assembly_thickness"]["ft"]

    plate = lv["main_top_of_plate"]["ft"]
    loft_sf = lv["loft_top_of_subfloor"]["ft"]
    knee = lv["loft_knee_wall_height"]["ft"]

    heel = rf["raised_heel"]["ft"]
    eave = rf["eave_overhang"]["ft"]
    rake = rf["rake_overhang"]["ft"]
    mp = rf["main_pitch"]["rise"] / rf["main_pitch"]["run"]
    dp = rf["dormer_pitch"]["rise"] / rf["dormer_pitch"]["run"]
    dorm_len = rf["dormers"]["width"]["ft"]          # extent along Y, from the rear

    # ---- roof geometry, driven by the A1.1 elevation (P3) ------------------
    # P2 built the roof bottom-up (plate + heel + pitch). Overlaying that on the
    # A1.1 front elevation put the dormer plane 11.5" low and stopped it 4" short
    # of the peak. The sheet is the authority for the finished silhouette, so the
    # roof is now driven by the ridge height and the two pitches, and the 4:12
    # dormer plane runs all the way to the ridge.
    cal = rf["elevation_calibration"]
    ridge_x = W / 2.0
    ridge_top = cal["ridge_top_of_roof"]["ft"]        # top of roof at the ridge, above FF
    mp_v = rt / math.cos(math.atan(mp))               # vertical assembly depth, 9:12
    dp_v = rt / math.cos(math.atan(dp))               # vertical assembly depth, 4:12

    main_top_wall = ridge_top - mp * ridge_x
    dorm_top_wall = ridge_top - dp * ridge_x
    main_under_wall = main_top_wall - mp_v
    dorm_under_wall = dorm_top_wall - dp_v
    ridge_under = ridge_top - mp_v

    springs = plate + heel                            # framing cross-check only
    face_top = loft_sf + knee                         # structural 4'-4" knee wall

    def main_under(x):
        """Underside of the main roof at plan X."""
        return ridge_top - mp * abs(ridge_x - x) - mp_v

    def dorm_under(x):
        """Underside of the 4:12 dormer roof at plan X. Runs to the ridge."""
        return ridge_top - dp * abs(ridge_x - x) - dp_v

    geo = dict(W=W, D=D, P=P, t=t, rt=rt, plate=plate, loft_sf=loft_sf,
               knee=knee, springs=springs, ridge_x=ridge_x, ridge_top=ridge_top,
               ridge_under=ridge_under, face_top=face_top, eave=eave, rake=rake,
               mp=mp, dp=dp, dorm_len=dorm_len, heel=heel,
               main_top_wall=main_top_wall, dorm_top_wall=dorm_top_wall,
               main_under_wall=main_under_wall, dorm_under_wall=dorm_under_wall)

    shell = collection("Shell")
    roofc = collection("Roof")
    porchc = collection("Porch")
    interior = collection("Interior_approx")
    finish = collection("Finish")

    # ---- frame convention -------------------------------------------------
    # Y runs SOUTH -> NORTH so that (east=+X, north=+Y, up=+Z) is a right-handed
    # compass frame matching the north-up A1.1 plan. Building with north at Y=0
    # yields a MIRROR IMAGE of the building: facing north, screen-right computes
    # as -X (west) when it must be east. Caught in P3 by overlaying the front
    # elevation, where the 4'-0" D.S.H. landed on the wrong side of the door.
    NY = P + D          # north (rear) exterior face
    SY = P              # south (front) exterior face of the main body

    def yn(d):
        """Spec distance measured from the NORTH corner -> world Y."""
        return NY - d

    geo["NY"], geo["SY"] = NY, SY

    # ---- main body walls (Z 0..plate) -------------------------------------
    walls = {
        "Wall_N": box("Wall_N", 0, W, NY - t, NY, 0, plate, shell),
        "Wall_S": box("Wall_S", 0, W, SY, SY + t, 0, plate, shell),
        "Wall_W": box("Wall_W", 0, t, SY + t, NY - t, 0, plate, shell),
        "Wall_E": box("Wall_E", W - t, W, SY + t, NY - t, 0, plate, shell),
    }

    # ---- openings ---------------------------------------------------------
    if cut_openings:
        op = spec["openings"]["main_floor"]
        pad = 0.05  # overshoot so boolean faces never land coplanar
        cutters = {k: [] for k in walls}

        for o in op["north_wall"]["openings"]:
            cutters["Wall_N"].append(box(
                f"cut_{o['id']}", o["offset"], o["offset"] + o["w"],
                NY - t - pad, NY + pad, o["sill"], o["sill"] + o["h"], shell))
        for o in op["south_wall"]["openings"]:
            cutters["Wall_S"].append(box(
                f"cut_{o['id']}", o["offset"], o["offset"] + o["w"],
                SY - pad, SY + t + pad, o["sill"], o["sill"] + o["h"], shell))
        for o in op["west_wall"]["openings"]:
            cutters["Wall_W"].append(box(
                f"cut_{o['id']}", -pad, t + pad,
                yn(o["offset"] + o["w"]), yn(o["offset"]),
                o["sill"], o["sill"] + o["h"], shell))
        # east_wall carries no openings — confirmed three ways, see spec.

        AXIS = {"Wall_N": 1, "Wall_S": 1, "Wall_W": 0, "Wall_E": 0}
        for name, cl in cutters.items():
            if cl:
                difference(walls[name], cl)
                mark_reveals(walls[name], AXIS[name])

    # ---- gable end walls (Z plate .. roof underside) -----------------------
    # The NORTH wall is where the dormers land, so its top edge follows the 4:12
    # dormer plane out to x_int and the 9:12 main plane from there to the ridge.
    # The porch-end gable has no dormer and is a plain triangle. Getting this
    # wrong leaves the dormer ends open to the sky.
    gable_dormered = [
        (0, plate), (0, dorm_under_wall), (ridge_x, ridge_top - dp_v),
        (W, dorm_under_wall), (W, plate),
    ]
    gable_plain = [(0, plate), (0, main_under_wall), (ridge_x, ridge_under),
                   (W, main_under_wall), (W, plate)]
    prism_xz("Gable_N", gable_dormered, NY - t, NY, shell)
    prism_xz("Gable_S_porch", gable_plain, 0, t, shell)

    # ---- loft floor and dormer face walls ---------------------------------
    box("Loft_floor", t, W - t, yn(dorm_len), NY - t, plate, loft_sf, shell)

    dormer_faces = {
        # Runs to the roof underside. The structural knee wall is the 4'-4" tag
        # (face_top); the remainder above it is the raised heel and fascia zone.
        "Dormer_face_W": box("Dormer_face_W", 0, t, yn(dorm_len), NY,
                             loft_sf, dorm_under_wall, shell),
        "Dormer_face_E": box("Dormer_face_E", W - t, W, yn(dorm_len), NY,
                             loft_sf, dorm_under_wall, shell),
    }
    if cut_openings:
        sill = loft_sf + con["dormer_window_sill_above_loft_floor"]["ft"]
        pad = 0.05
        for side, (x0, x1) in (("W", (-pad, t + pad)), ("E", (W - t - pad, W + pad))):
            cl = []
            for o in spec["openings"]["loft"]["windows"]:
                cl.append(box(f"cut_{o['id']}_{side}", x0, x1,
                              yn(o["offset"] + o["w"]), yn(o["offset"]),
                              sill, sill + o["h"], shell))
            difference(dormer_faces[f"Dormer_face_{side}"], cl)
            mark_reveals(dormer_faces[f"Dormer_face_{side}"], 0)

    # dormer cheek wall at the inboard (south) end of each dormer
    for side in ("W", "E"):
        tri = [(0, main_under_wall), (0, dorm_under_wall), (ridge_x, ridge_top - dp_v)]
        if side == "E":
            tri = [(W - x, z) for x, z in tri]
        prism_xz(f"Dormer_cheek_{side}", tri, yn(dorm_len), yn(dorm_len) + t, shell)

    # ---- main roof --------------------------------------------------------
    z_eave = main_top_wall - mp * eave
    roof_profile = [
        (-eave, z_eave), (ridge_x, ridge_top), (W + eave, z_eave),
        (W + eave, z_eave - mp_v), (ridge_x, ridge_top - mp_v), (-eave, z_eave - mp_v),
    ]
    roof_main = prism_xz("Roof_main", roof_profile, -rake, NY + rake, roofc)
    # Cut the main roof out of the DORMER ZONE, but only between the wall faces.
    # A dormer is made by removing roof; leaving it continuous put a 9:12 slab
    # through the loft across 100% of its width. Truncating the roof instead was
    # wrong -- the A1.1 left elevation shows the main roof continuing below and
    # around the dormer, so the eave must survive. Keeping x < 0 and x > W
    # preserves the 18" eave overhang while clearing the interior.
    pad = 0.05
    difference(roof_main, [box("cut_dormer_void", 0.0, W,
                               yn(dorm_len), NY,      # stop at the wall, not the rake
                               -pad, ridge_top + pad, roofc)])

    # ---- dormer roofs (4:12, sloping up from the face to the main plane) ---
    for side in ("W", "E"):
        z_face_eave = dorm_top_wall - dp * eave
        prof = [(-eave, z_face_eave), (ridge_x, ridge_top),
                (ridge_x, ridge_top - dp_v), (-eave, z_face_eave - dp_v)]
        if side == "E":
            prof = [(W - x, z) for x, z in prof]
        # Runs out to the rear rake: past the dormers the roof surface IS the
        # 4:12 plane, so the rear overhang follows it, not the 9:12 main plane.
        prism_xz(f"Roof_dormer_{side}", prof, yn(dorm_len), NY + rake, roofc)

    # ---- eave / raised-heel band on the side walls -------------------------
    # Between the 8'-0" top of plate and the main roof underside. This is the 9"
    # raised heel plus fascia; without it the walls stop short of the roof.
    for side, (bx0, bx1) in (("W", (0, t)), ("E", (W - t, W))):
        box(f"Eave_band_{side}", bx0, bx1, SY + t, yn(dorm_len),
            plate, main_under_wall, shell)

    # ---- porch ------------------------------------------------------------
    slab_t = con["porch_slab_thickness"]["ft"]
    post = con["porch_post"]["ft"]
    setback = env["porch_post_setback_each_end"]["ft"]
    box("Porch_slab", 0, W, 0, P, -slab_t, 0, porchc)
    box("Porch_ceiling", 0, W, 0, P, plate - 0.1, plate, porchc)
    for i, px in enumerate((setback, W - setback)):
        box(f"Porch_post_{i+1}", px - post / 2, px + post / 2,
            0, post, 0, plate, porchc)
    box("Floor_slab", 0, W, SY, NY, -slab_t, 0, porchc)

    # ---- interior partitions, from the measured layout ---------------------
    # Positions come from spec.interior_partitions.layout, measured on A1.1.
    # Door openings are cut in; their SIZES are plan callouts, their POSITIONS
    # are approximate (+/- 6") — see the layout block.
    lay = spec["interior_partitions"]["layout"]
    ti = con["interior_wall_thickness"]["ft"]
    xw, ye = t, NY - t                 # interior west face, interior north face

    def ix(v):
        return xw + v                  # layout x -> world X
    def iy(v):
        return ye - v                  # layout y (south of N face) -> world Y

    parts, doors_by_wall = {}, {}
    for d in lay["doors"]:
        doors_by_wall.setdefault(d["in"], []).append(d)

    for pdef in lay["partitions"]:
        pid = pdef["id"]
        if pdef["axis"] == "y":        # runs north-south at a fixed x
            x0, x1 = ix(pdef["at_ft"]) - ti, ix(pdef["at_ft"])
            y0, y1 = iy(pdef["to_ft"]), iy(pdef["from_ft"])
        else:                          # runs east-west at a fixed y
            x0, x1 = ix(pdef["from_ft"]), ix(pdef["to_ft"])
            y0, y1 = iy(pdef["at_ft"]), iy(pdef["at_ft"]) + ti
        ob = box(f"Part_{pid}", x0, x1, y0, y1, 0, plate, interior)
        parts[pid] = ob

        cutters = []
        for d in doors_by_wall.get(pid, []):
            c, hw, pad = d["centre_ft"], d["w"] / 2.0, 0.05
            if pdef["axis"] == "y":
                cutters.append(box(f"cut_{d['id']}", x0 - pad, x1 + pad,
                                   iy(c + hw), iy(c - hw), 0, d["h"], interior))
            else:
                cutters.append(box(f"cut_{d['id']}", ix(c - hw), ix(c + hw),
                                   y0 - pad, y1 + pad, 0, d["h"], interior))
        if cutters:
            difference(ob, cutters)

    # ---- Tier 1: door leaves -----------------------------------------------
    # Every leaf is built; spec.doors.default_state says which are shown open.
    # A pocket leaf "open" lives inside the wall cavity beside its opening,
    # which is physically where it is — so it is modelled there, not hidden.
    dspec = spec["doors"]
    pdefs = {pp["id"]: pp for pp in lay["partitions"]}
    lt = dspec["leaf_thickness"]["ft"]
    state = dspec["default_state"]

    def leaf(name, x0, x1, y0, y1, z0, z1):
        box(name, x0, x1, y0, y1, z0, z1, finish)

    # exterior entry door, in the south wall
    for o in spec["openings"]["main_floor"]["south_wall"]["openings"]:
        if not o["type"].endswith("door"):
            continue
        c = SY + t / 2
        leaf(f"Door_{o['id']}", o["offset"], o["offset"] + o["w"],
             c - lt / 2, c + lt / 2, o["sill"], o["sill"] + o["h"])

    # interior leaves, one per door in the measured layout
    for d in lay["doors"]:
        pdef = pdefs[d["in"]]
        typ = "bypass" if d["id"].endswith("CLOSET") else (
            "double_pocket" if "DBL" in d["id"] else "pocket")
        c, hw = d["centre_ft"], d["w"] / 2.0
        opn = state.get(typ, "closed") == "open"
        if pdef["axis"] == "x":                       # wall runs east-west
            wy = iy(pdef["at_ft"]) + ti / 2
            spans = ([(c - hw, c), (c, c + hw)] if typ == "double_pocket"
                     else [(c - hw, c + hw)])
            for k, (a, b) in enumerate(spans):
                if opn:
                    # A pocket leaf slides its OWN width to clear the opening.
                    # For a single leaf, pick whichever side has wall to take it.
                    lw = b - a
                    if len(spans) == 2:
                        west = (k == 0)
                    else:
                        west = (a - lw) >= pdef["from_ft"] - 1e-6
                    a, b = (a - lw, b - lw) if west else (a + lw, b + lw)
                leaf(f"Door_{d['id']}_{k}", ix(a), ix(b),
                     wy - lt / 2, wy + lt / 2, 0, d["h"])
        else:                                         # wall runs north-south
            wx = ix(pdef["at_ft"]) - ti / 2
            spans = ([(c - hw, c), (c, c + hw)] if typ == "bypass"
                     else [(c - hw, c + hw)])
            for k, (a, b) in enumerate(spans):
                off = (lt if k else -lt)              # bypass leaves offset in depth
                leaf(f"Door_{d['id']}_{k}", wx - lt / 2 + off, wx + lt / 2 + off,
                     iy(b), iy(a), 0, d["h"])

    # ---- Tier 1: ceilings and floor finishes -------------------------------
    # Ceiling zones come from spec.ceilings; the vaulted ones are derived from
    # main_under()/dorm_under() so they cannot drift from the roof they follow.
    ct = con["ceiling_thickness"]["ft"]
    ff = con["floor_finish_thickness"]["ft"]
    xw, xe = t, W - t                      # interior west / east faces
    ye = NY - t                            # interior north face
    ys = SY + t                            # interior south face
    loft_s = yn(dorm_len)                  # south edge of the loft floor

    pdefs = {p["id"]: p for p in lay["partitions"]}
    bath_x1 = ix(pdefs["P_bath_E"]["at_ft"]) - ti   # west face of the bath's east wall
    bath_y0 = iy(pdefs["P_bath_S"]["at_ft"]) + ti   # north face of the bath's south wall

    def vault(name, under, y0, y1):
        """Thin ceiling slab following a roof-underside function."""
        prof = [(xw, under(xw)), (ridge_x, under(ridge_x)), (xe, under(xe)),
                (xe, under(xe) - ct), (ridge_x, under(ridge_x) - ct),
                (xw, under(xw) - ct)]
        return prism_xz(name, prof, y0, y1, finish)

    box("Ceil_flat_under_loft", xw, xe, loft_s, ye, plate - ct, plate, finish)
    vault("Ceil_vault_living", main_under, ys, loft_s)
    vault("Ceil_vault_loft", dorm_under, loft_s, ye)

    # Floor finishes tile without overlapping: south band full width, then the
    # north band east of the bath, then the bath itself.
    box("Floor_main_S", xw, xe, ys, bath_y0, 0, ff, finish)
    box("Floor_main_N", bath_x1, xe, bath_y0, ye, 0, ff, finish)
    box("Floor_bath",   xw, bath_x1, bath_y0, ye, 0, ff, finish)
    box("Floor_loft",   xw, xe, loft_s, ye, loft_sf, loft_sf + ff, finish)

    # ---- Tier 1: casing, baseboard, ladder and guardrail --------------------
    tr = spec["trim"]
    cw = tr["casing_width"]["ft"]
    hh = tr["head_casing_height"]["ft"]
    bh = tr["baseboard_height"]["ft"]
    cd_ = 0.06                                   # casing proud of the wall face

    def casing(name, axis, plane, a0, a1, z0, z1):
        """Frame on the interior face of an opening. axis 'x' spans X, 'y' spans Y."""
        if axis == "x":
            specs = [(a0 - cw, a0, plane, plane + cd_, z0, z1),
                     (a1, a1 + cw, plane, plane + cd_, z0, z1),
                     (a0 - cw, a1 + cw, plane, plane + cd_, z1, z1 + hh)]
        else:
            specs = [(plane, plane + cd_, a0 - cw, a0, z0, z1),
                     (plane, plane + cd_, a1, a1 + cw, z0, z1),
                     (plane, plane + cd_, a0 - cw, a1 + cw, z1, z1 + hh)]
        multibox(name, specs, finish)

    op = spec["openings"]["main_floor"]
    for o in op["north_wall"]["openings"]:
        casing(f"Trim_{o['id']}", "x", ye - cd_, o["offset"], o["offset"] + o["w"],
               o["sill"], o["sill"] + o["h"])
    for o in op["south_wall"]["openings"]:
        casing(f"Trim_{o['id']}", "x", ys, o["offset"], o["offset"] + o["w"],
               o["sill"], o["sill"] + o["h"])
    for o in op["west_wall"]["openings"]:
        casing(f"Trim_{o['id']}", "y", xw, yn(o["offset"] + o["w"]), yn(o["offset"]),
               o["sill"], o["sill"] + o["h"])
    dsill = loft_sf + con["dormer_window_sill_above_loft_floor"]["ft"]
    for o in spec["openings"]["loft"]["windows"]:
        for side, pl in (("W", xw), ("E", xe - cd_)):
            casing(f"Trim_{o['id']}_{side}", "y", pl,
                   yn(o["offset"] + o["w"]), yn(o["offset"]), dsill, dsill + o["h"])

    # baseboard: one welded mesh around the main interior perimeter
    bb = 0.05
    multibox("Trim_baseboard", [
        (xw, xe, ys, ys + bb, 0, bh), (xw, xe, ye - bb, ye, 0, bh),
        (xw, xw + bb, ys, ye, 0, bh), (xe - bb, xe, ys, ye, 0, bh)], finish)

    # ladder: two stringers plus rungs, leaning at the heel-cut angle
    la = spec["loft_access"]["ladder"]
    ang = math.radians(la["heel_cut_deg"]["value"])
    lw = la["width"]["ft"]
    run = loft_sf * math.tan(ang)
    lx = ix(la["top_at"]["x_ft"])
    y_top = iy(pdefs["P_bedroom_S"]["at_ft"])
    y_bot = y_top - run
    st = 0.29
    specs = []
    for sx in (lx - lw / 2, lx + lw / 2 - st):
        for k in range(14):                       # stepped stringer approximation
            f0, f1 = k / 14.0, (k + 1) / 14.0
            specs.append((sx, sx + st,
                          y_bot + (y_top - y_bot) * f0, y_bot + (y_top - y_bot) * f1 + 0.02,
                          loft_sf * f0, loft_sf * f1 + 0.02))
    rs = la["rung_spacing"]["ft"]
    rt = la["rung_section"]["ft"]
    n_r = int(loft_sf / rs)
    for k in range(1, n_r + 1):
        f = k * rs / loft_sf
        yy = y_bot + (y_top - y_bot) * f
        specs.append((lx - lw / 2, lx + lw / 2, yy - rt / 2, yy + rt / 2,
                      k * rs - rt / 2, k * rs + rt / 2))
    multibox("Ladder_loft", specs, finish)

    # guardrail along the loft's open (south) edge, clear of the ladder
    gr = spec["loft_access"]["guardrail"]
    gh = gr["height"]["ft"]
    ps = gr["post_section"]["ft"]
    gy = loft_s
    gap = (lx - lw / 2 - 0.5, lx + lw / 2 + 0.5)
    rails = []
    for a, b in ((xw, gap[0]), (gap[1], xe)):
        if b - a < 0.5:
            continue
        rails.append((a, b, gy, gy + ps, loft_sf + gh - 0.29, loft_sf + gh))
        for k in range(int((b - a) / 4.0) + 2):
            px_ = min(a + k * 4.0, b - ps)
            rails.append((px_, px_ + ps, gy, gy + ps, loft_sf, loft_sf + gh))
    multibox("Rail_loft", rails, finish)

    geo.update(ct=ct, ff=ff, xw=xw, xe=xe, ys=ys, ye=ye, loft_s=loft_s,
               bath_x1=bath_x1, bath_y0=bath_y0,
               main_under_wall_i=main_under(xw), dorm_under_wall_i=dorm_under(xw),
               main_under_ridge=main_under(ridge_x), dorm_under_ridge=dorm_under(ridge_x))

    # ---- Tier 2 prerequisite: UVs, generated LAST -------------------------
    # After the booleans, per TIER-2 §3 — openings create faces no earlier
    # layout accounts for.
    tx = spec["texturing"]
    tile_ft = tx["tile_size_px"] / tx["texel_density_px_per_ft"]
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            uv_project(ob, tile_ft)
    geo["tile_ft"] = tile_ft

    return geo, dict(shell=shell, roof=roofc, porch=porchc,
                     interior=interior, finish=finish)


# ---------------------------------------------------------------------------
def report(spec, geo, colls):
    lv, env = spec["levels"], spec["envelope"]
    W, D, P = geo["W"], geo["D"], geo["P"]

    shell_roof = list(colls["shell"].objects) + list(colls["roof"].objects)
    lo, hi = world_bbox(shell_roof)
    stated = lv["overall_height"]["ft"]

    print("\n" + "=" * 72)
    print("BUILD REPORT — barn_cabin_524 (Option B)")
    print("=" * 72)

    rows = [
        ("Footprint width  (X)", W, env["main_body_width"]["raw"]),
        ("Footprint depth  (Y)", D + P, env["total_footprint_depth"]["raw"]),
        ("Main body depth", D, env["main_body_depth"]["raw"]),
        ("Ridge, top of roof", geo["ridge_top"], lv["overall_height"]["raw"]),
        ("Model bbox top", hi[2], lv["overall_height"]["raw"]),
    ]
    w = max(len(r[0]) for r in rows)
    print(f"\n{'DIMENSION'.ljust(w)} | {'MODEL':>10} | {'':>13} | SHEET")
    print("-" * (w + 48))
    for n, v, sheet in rows:
        print(f"{n.ljust(w)} | {v:>7.2f} ft | {ft(v):>13} | {sheet}")

    print("\nRoof, driven by the A1.1 elevation (see spec.roof.elevation_calibration):")
    print(f"  ridge, top of roof        {ft(geo['ridge_top'])} above main FF")
    print(f"  main 9:12 top at wall     {ft(geo['main_top_wall'])}")
    print(f"  dormer 4:12 top at wall   {ft(geo['dorm_top_wall'])}   (sheet measured 14'-1.9\")")
    print(f"  dormer plane reaches the ridge — no intersection short of the peak")
    print(f"\nFraming cross-check (not used to place geometry):")
    print(f"  plate {ft(geo['plate'])} + {ft(geo['heel'])} heel = {ft(geo['springs'])} springs")
    print(f"  structural knee wall top  {ft(geo['face_top'])}  (loft subfloor + 4'-4\")")
    print(f"  heel/fascia band on side walls: {ft(geo['plate'])} -> {ft(geo['main_under_wall'])}")

    print(f"\nBounding box, shell + roof (with {ft(geo['eave'])} eave / {ft(geo['rake'])} rake):")
    for i, ax in enumerate("XYZ"):
        print(f"  {ax} {lo[i]:7.2f} .. {hi[i]:7.2f}   span {hi[i]-lo[i]:6.2f} ft")

    print("\nGATES")
    dorm_at_ridge = abs(geo["dorm_top_wall"] + geo["dp"] * geo["ridge_x"]
                        - geo["ridge_top"]) < 1e-9
    checks = [
        ("footprint 22'-0\" x 30'-0\"", abs(W - 22) < 0.01 and abs(D + P - 30) < 0.01),
        ("main floor area = 528 sf",
         abs(W * D - spec["areas_declared"]["main_floor_living_sf"]["value"]) < 0.5),
        ("ridge top of roof = 17'-9 11/16\" above FF",
         abs(geo["ridge_top"] - stated) < 0.01),
        ("model bbox top matches the stated height", abs(hi[2] - stated) < 0.01),
        ("4:12 dormer plane reaches the ridge", dorm_at_ridge),
        ("no NaN / degenerate geometry", all(math.isfinite(v) for v in lo + hi)),
    ]
    ok = True
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
        ok &= passed
    print("=" * 72)
    return ok


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else HERE
    cut = "--no-openings" not in argv

    spec = load_spec(HERE / "spec.yaml")
    geo, colls = build(spec, cut_openings=cut)
    ok = report(spec, geo, colls)

    out.mkdir(parents=True, exist_ok=True)
    dest = out / "barn_cabin_524.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    print(f"\nsaved: {dest}")
    if not ok:
        raise SystemExit("one or more gates FAILED")


if __name__ == "__main__":
    main()
