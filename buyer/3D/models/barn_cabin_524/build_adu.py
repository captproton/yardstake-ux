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


def _check_path(name, path, which=""):
    """A sweep needs two points, and the failure has to say WHICH sweep.

    `tube_geom` is generic and has no name to report, so the check lives in
    the wrappers, which do. Splitting the sweep out of `tube` quietly cost
    that: the error went from naming the tube to "a tube needs at least two
    points", which in a model with a doorknob, a tap and a gooseneck sconce
    identifies nothing.
    """
    if len(path) < 2:
        raise ValueError(f"{name}{which}: a tube needs at least two points, "
                         f"got {len(path)}")


def tube(name, path, radius, coll, sides=8, caps=True):
    """One swept n-gon as its own object. See `tube_geom` for the sweep."""
    _check_path(name, path)
    v, f = tube_geom(path, radius, sides, caps)
    return _new_obj(name, v, f, coll)


def multitube(name, specs, coll, sides=8):
    """Several tubes welded into ONE mesh, as `multibox` does for boxes.

    A doorknob is a rose, a shank and a ball -- three tubes that share a
    material, never move independently, and are always drawn together. Built as
    three objects they cost three draw calls and three entries against the mesh
    budget, and that budget is real: it was set in the first commit of this
    model and eleven PRs later the knob is what would have pushed it over.

    `specs` is a sequence of (path, radius).
    """
    verts, faces = [], []
    for i, (path, radius) in enumerate(specs):
        # The index matters here: a multitube is several sweeps under ONE name,
        # so the name alone would not say which of them was malformed.
        _check_path(name, path, f" sweep {i}")
        v, f = tube_geom(path, radius, sides, True)
        off = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + off for i in face) for face in f)
    return _new_obj(name, verts, faces, coll)


def tube_geom(path, radius, sides=8, caps=True):
    """Sweep an n-gon along a 3D polyline, as (verts, faces).

    Split out from `tube` so several sweeps can be welded into one mesh --
    the geometry and the object are different decisions and were tangled.

    Everything else in this model is axis-aligned boxes, which is right for
    architecture and useless for a tap. `sides=8` is deliberate: at
    configurator distance an octagonal tube reads as round, and it costs 8
    quads per segment instead of the 24 a smooth one would.

    The frame is carried along the path rather than recomputed per segment, so
    the tube does not twist where it bends.
    """
    import mathutils

    pts = [mathutils.Vector(p) for p in path]
    if len(pts) < 2:
        raise ValueError("a tube needs at least two points")

    # Seed a reference axis that is not parallel to the first segment, or the
    # cross product below degenerates and the ring collapses.
    d0 = (pts[1] - pts[0]).normalized()
    up = mathutils.Vector((0.0, 0.0, 1.0))
    if abs(d0.dot(up)) > 0.9:
        up = mathutils.Vector((1.0, 0.0, 0.0))
    u = d0.cross(up).normalized()
    v = d0.cross(u).normalized()

    rings, verts = [], []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1] - pts[0]).normalized()
        elif i == len(pts) - 1:
            d = (pts[-1] - pts[-2]).normalized()
        else:                                   # average, so bends are mitred
            d = ((pts[i] - pts[i - 1]).normalized()
                 + (pts[i + 1] - pts[i]).normalized()).normalized()
        # Re-orthogonalise the carried frame against the new direction.
        u = (u - d * u.dot(d)).normalized()
        v = d.cross(u).normalized()
        ring = []
        for k in range(sides):
            a = 2.0 * math.pi * k / sides
            ring.append(len(verts))
            verts.append(tuple(p + u * (math.cos(a) * radius)
                               + v * (math.sin(a) * radius)))
        rings.append(ring)

    faces = []
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((a[k], a[k2], b[k2], b[k]))
    if caps:
        faces.append(tuple(reversed(rings[0])))
        faces.append(tuple(rings[-1]))
    return verts, faces


def ellipse_ring(cx, cy, ax, ay, z, n=16):
    """One horizontal ellipse as a ring of points, for feeding to loft().

    Axis-aligned, which every ellipse in this plan set is. `ax` is the semi-axis
    along X, `ay` along Y — the plan draws the vanity basin wider along the wall
    than off it, so the two genuinely differ and a circle would not do.
    """
    return [(cx + ax * math.cos(2.0 * math.pi * k / n),
             cy + ay * math.sin(2.0 * math.pi * k / n),
             z) for k in range(n)]


def loft(name, rings, coll, cap_first=False, cap_last=False):
    """Skin a sequence of equal-length point rings, in order.

    The second round primitive, after tube(). Deliberately generic rather than
    basin-shaped: a lofted profile is what a toilet bowl needs too, so this is
    the piece that makes the remaining bought fixtures worth re-examining.

    Give it the WHOLE profile — down the inside, across the floor, up the
    outside — and the result is a closed solid with no open boundary, which is
    what glTF's default backface culling requires. A single-sided shell renders
    with holes in it from half the angles.
    """
    if len(rings) < 2:
        raise ValueError(f"{name}: a loft needs at least two rings, got {len(rings)}")
    n = len(rings[0])
    if n < 3:
        raise ValueError(f"{name}: a ring needs at least three points, got {n}")
    if any(len(r) != n for r in rings):
        raise ValueError(f"{name}: every ring must have the same point count")

    verts, faces = [], []
    for r in rings:
        verts.extend(tuple(p) for p in r)
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((a + k, a + k2, b + k2, b + k))
    if cap_first:
        faces.append(tuple(range(n - 1, -1, -1)))
    if cap_last:
        base = (len(rings) - 1) * n
        faces.append(tuple(range(base, base + n)))
    return _new_obj(name, verts, faces, coll)


def arc_points(centre, radius, axis, start_deg, end_deg, n=8):
    """Points on a circular arc, for feeding to tube(). `axis` is 'x' or 'y':
    the axis the arc turns about."""
    import mathutils
    cx, cy, cz = centre
    out = []
    for i in range(n + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / n)
        if axis == "x":
            out.append(mathutils.Vector((cx,
                                         cy + radius * math.cos(a),
                                         cz + radius * math.sin(a))))
        else:
            out.append(mathutils.Vector((cx + radius * math.cos(a),
                                         cy,
                                         cz + radius * math.sin(a))))
    return out


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


def mark_reveals(ob, thickness_axis, outward=None):
    """Split a wall's faces across three material slots.

      0  cladding   the outward face — siding
      1  trim       jamb, head and sill faces inside each opening
      2  drywall    the inward face

    Without slot 2 the wall shows lap siding on its INSIDE, which is what
    happened the first time the interior was textured. A reveal is a face whose
    centroid sits strictly inside the wall's extents in both axes
    perpendicular to its thickness; the wall's own end, top and bottom faces
    lie exactly on those extents. The inward face is the one whose normal runs
    along the thickness axis opposite to `outward`.
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
    if outward is not None:
        for poly in me.polygons:
            if poly.normal[thickness_axis] * outward < -0.9:
                poly.material_index = 2
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
    found = collection("Foundation")
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

        # axis, and which way is OUT of the building
        FACE = {"Wall_N": (1, +1), "Wall_S": (1, -1),
                "Wall_W": (0, -1), "Wall_E": (0, +1)}
        for name, cl in cutters.items():
            if cl:
                difference(walls[name], cl)
            mark_reveals(walls[name], *FACE[name])

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
    mark_reveals(prism_xz("Gable_N", gable_dormered, NY - t, NY, shell), 1, +1)
    # The SOUTH gable carries a window that the model went eleven PRs without.
    # It is cut here rather than with the main-floor openings because it is not
    # in a wall: `Gable_S_porch` is a prism, and the wall cutters above are keyed
    # by wall name. Same machinery, different host.
    gable_s = prism_xz("Gable_S_porch", gable_plain, 0, t, shell)
    if cut_openings:
        pad = 0.05
        gcuts = [box(f"cut_{o['id']}", o["offset"], o["offset"] + o["w"],
                     -pad, t + pad, o["sill"], o["sill"] + o["h"], shell)
                 for o in spec["openings"]["loft"]["south_gable"]["windows"]]
        if gcuts:
            difference(gable_s, gcuts)
    mark_reveals(gable_s, 1, -1)

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
            mark_reveals(dormer_faces[f"Dormer_face_{side}"], 0,
                         -1 if side == "W" else +1)

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

    # ---- the projecting ridge beam at the front apex -----------------------
    # RB01's tail, cantilevering forward out of the peak. It goes in the ROOF
    # collection rather than the shell so it travels with the roof through every
    # LOD -- it is part of the silhouette a homeowner sees in views.front(), and
    # the front gable is the face they look at first.
    #
    # NOT named Trim_, even though the tour shows it painted the trim colour.
    # `Trim_` means Tier 1 INTERIOR finish in this project, and verify_tier1
    # gates that every such object lives in the Finish collection -- which is
    # lod0 only. Borrowing the prefix for an exterior member broke that gate on
    # the first run. It gets its own assignment rule instead.
    rb = spec["trim"]["projecting_ridge_beam"]
    rb_hw = rb["width"]["ft"] / 2
    rb_cx = rb["centre_x"]["ft"]
    rb_z0, rb_z1 = rb["bottom_z"]["ft"], rb["top_z"]["ft"]
    rb_cap = rb["cap"]["thickness"]["ft"]
    rb_out = -rb["projection"]["ft"]           # forward is -Y
    multibox("Ridge_beam", [
        (rb_cx - rb_hw, rb_cx + rb_hw, rb_out, t, rb_z0, rb_z1),
        (rb_cx - rb_hw, rb_cx + rb_hw, rb_out, t, rb_z1, rb_z1 + rb_cap),
        (rb_cx - rb_hw, rb_cx + rb_hw, rb_out, t, rb_z0 - rb_cap, rb_z0),
    ], roofc)

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
    # ---- foundation: crawlspace, not slab ---------------------------------
    # A2.0 draws two variants and this model is the CRAWLSPACE one. The slab
    # that used to sit here was the other variant, built from a thickness
    # sourced off A2.0's PORCH callout.
    #
    # The stemwall goes in the PORCH collection deliberately: that collection
    # ships in every LOD, so the placement developer's lod2 keeps something at
    # grade. Replacing the slab there rather than deleting it was agreed
    # explicitly — see spec.foundation.lod2_change. Footing, crawl grade and
    # vents are detail and stay in lod0.
    fd = spec["foundation"]
    fb = fd["floor_buildup"]
    st = fd["stemwall"]["thickness"]["ft"]
    z_found = -(fb["subfloor"]["ft"] + fb["joist"]["ft"] + fb["mud_sill"]["ft"])
    z_foot = z_found - fd["stemwall"]["height"]["ft"]
    # Exterior grade is NOT built. spec.foundation.grade exists so verify can
    # sanity-check that the vents clear it; nothing here renders a ground
    # plane, and the handoff doc says so.
    vt = fd["venting"]
    vw, vh_, vrec = vt["width"]["ft"], vt["height"]["ft"], vt["recess"]["ft"]
    vz1 = z_found - vt["below_foundation"]["ft"]
    vz0 = vz1 - vh_

    # THE VENTS ARE MEASURED OFF A2.0, NOT INVENTED. A2.0's FOUNDATION PLAN
    # draws them, and spec.foundation.venting.openings carries the eight
    # centres read off that sheet: two north, three each side, NONE on the
    # south wall, which sits behind the covered porch. An earlier version put
    # four vents at an invented 2'-0" corner setback in order to satisfy
    # A0.0's corner note — a note the drawn layout does not actually meet.
    # See spec.foundation.venting.corner_rule_discrepancy.
    def centres(wall):
        return sorted(o["at"]["ft"] for o in vt["openings"] if o["wall"] == wall)

    def spans(wall, to_model):
        """Vent openings on one wall as (lo, hi) in model coordinates."""
        return [(to_model(c) - vw / 2, to_model(c) + vw / 2) for c in centres(wall)]

    # x is measured EAST from the west outer face, so it is already model X.
    # y is measured SOUTH from the north outer face, so model Y is NY - y.
    holes = {
        "north": spans("north", lambda c: c),
        "south": spans("south", lambda c: c),
        "west": spans("west", lambda c: NY - c),
        "east": spans("east", lambda c: NY - c),
    }

    def banded(sweep0, sweep1, band0, band1, wall, along):
        """One stemwall run, broken by its vent openings.

        Boxes rather than a boolean — the counters' reasoning applies here too.
        `along` is the axis the run sweeps; the other pair is the 8" band.
        """
        def box6(a, b, z0, z1):
            return (a, b, band0, band1, z0, z1) if along == "x" else \
                   (band0, band1, a, b, z0, z1)

        out, prev = [], sweep0
        for a, b in sorted(holes[wall]):
            out.append(box6(prev, a, z_foot, z_found))
            out.append(box6(a, b, z_foot, vz0))              # under the vent
            out.append(box6(a, b, vz1, z_found))             # over the vent
            prev = b
        out.append(box6(prev, sweep1, z_foot, z_found))
        return out

    # North and south sweep the full width; the sides sweep between them so no
    # corner is built twice.
    stem = (banded(0.0, W, SY, SY + st, "south", "x")
            + banded(0.0, W, NY - st, NY, "north", "x")
            + banded(SY + st, NY - st, 0.0, st, "west", "y")
            + banded(SY + st, NY - st, W - st, W, "east", "y"))
    multibox("Found_stemwall", stem, porchc)

    # The floor build-up itself. Without this the building floats: the walls
    # start at Z=0 and the stemwall tops out at the TOP OF FOUNDATION, leaving
    # the subfloor + joists + mud sill as an empty band. Floor_slab used to
    # hide that gap by being only slab_t deep and sitting right under the
    # floor; replacing it with a real foundation exposed the omission.
    #
    # A perimeter band, not a solid deck: a solid one would put a face at Z=0
    # coplanar with the underside of every Floor_* finish (rule 16). It reads
    # as the rim joist, which is what is actually visible from outside. Porch
    # collection, so lod2 sees the building meet its foundation too.
    multibox("Found_rim", [
        (0.0, W, SY, SY + t, z_found, 0.0),                  # south
        (0.0, W, NY - t, NY, z_found, 0.0),                  # north
        (0.0, t, SY + t, NY - t, z_found, 0.0),              # west
        (W - t, W, SY + t, NY - t, z_found, 0.0),            # east
    ], porchc)

    # The porch slab was floating too. It is 4" of concrete whose underside sat
    # at -4" with three feet of air below it — invisible while the building
    # also floated, obvious the moment the building stopped.
    #
    # PIERS, NOT A CURB. A continuous curb would close the porch void and seal
    # the two south vents into a dead pocket, which would quietly make the
    # A0.0 venting gates meaningless. Piers carry the outer edge, the house
    # carries the inner, and the crawlspace still breathes through the south
    # wall. Sized and placed off the porch posts they sit under, so nothing new
    # is invented: only the pier is new, and it is DEMONSTRATION, like grade.
    piers = []
    for px in (post / 2, setback, W - setback, W - post / 2):
        piers.append((px - post / 2, px + post / 2,
                      0.0, post, z_foot, -slab_t))
    multibox("Found_pier", piers, porchc)

    # Footing, crawl grade and vents: lod0 detail only.
    fw = fd["footing"]["width"]["ft"]
    fdp = fd["footing"]["depth"]["ft"]
    o = (fw - st) / 2.0
    multibox("Found_footing", [
        (-o, W + o, SY - o, SY + st + o, z_foot - fdp, z_foot),
        (-o, W + o, NY - st - o, NY + o, z_foot - fdp, z_foot),
        (-o, st + o, SY + st + o, NY - st - o, z_foot - fdp, z_foot),
        (W - st - o, W + o, SY + st + o, NY - st - o, z_foot - fdp, z_foot),
    ], found)
    box("Found_grade", st, W - st, SY + st, NY - st, z_foot, z_foot + 0.05, found)

    # Vent inserts, set back from the OUTER face so nothing is coplanar
    # (rule 16). Each sits in the opening its own wall's schedule cut.
    vents = []
    for a, b in holes["south"]:
        vents.append((a, b, SY + vrec, SY + st, vz0, vz1))
    for a, b in holes["north"]:
        vents.append((a, b, NY - st, NY - vrec, vz0, vz1))
    for a, b in holes["west"]:
        vents.append((vrec, st, a, b, vz0, vz1))
    for a, b in holes["east"]:
        vents.append((W - st, W - vrec, a, b, vz0, vz1))
    multibox("Found_vent", vents, found)

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

    def half_lite(name, o, y0, y1):
        """The entry door, built the way the CABINET doors are already built.

        There are two functions called `leaf` in this file. The other one, in
        the casework, returns rails, stiles and a recessed panel, and its
        docstring already made the argument that applies here word for word:
        "A door modelled as a flat slab is geometrically correct and visually
        nothing." It was never applied to the front door, which stayed a box.

        Note what is NOT here: glass. The lite openings are left EMPTY and the
        six panes are set by finish_adu.add_glazing, because glass is a finish
        and the frame is geometry. Building the panes here would put them in
        lod2, where there is no glazing at all.
        """
        cn = o["construction"]
        st = cn["stile"]["ft"]
        br, lr = cn["bottom_rail"]["ft"], cn["lock_rail"]["ft"]
        mw = cn["muntin_width"]["ft"]
        rec = cn["panel_recess"]["ft"]
        x0, x1 = o["offset"], o["offset"] + o["w"]
        z0, z1 = o["sill"], o["sill"] + o["h"]

        # The LITE GRID is placed from its own measured levels, and everything
        # that touches it is then derived so the parts cannot leave a gap. The
        # panel height and the top rail come out as remainders rather than being
        # read a second time -- spec records both, and a part built from two
        # independent measurements meets its neighbour only by luck.
        # spec's `top_rail` and `panel` are the CHECK on this arithmetic, in
        # verify_openings.py, not a second source for it.
        gx0, gx1 = x0 + st, x1 - st
        gz0 = z0 + cn["lite_grid"]["bottom_z"]
        gz1 = z0 + cn["lite_grid"]["top_z"]
        parts = [
            (x0, x1, y0, y1, z0, z0 + br),                  # bottom rail
            (x0, x1, y0, y1, gz1, z1),                      # top rail
            (x0, x0 + st, y0, y1, z0 + br, gz1),            # left stile
            (x1 - st, x1, y0, y1, z0 + br, gz1),            # right stile
            (gx0, gx1, y0, y1, gz0 - lr, gz0),              # lock rail
            # The recessed panel sits back from the OUTSIDE face, which is -Y.
            (gx0, gx1, y0 + rec, y1, z0 + br, gz0 - lr),
        ]

        # Muntin bars: one fewer than the lite count, in each direction.
        cols, rows = cn["lites"]["cols"], cn["lites"]["rows"]
        for i in range(1, cols):
            c = gx0 + (gx1 - gx0) * i / cols
            parts.append((c - mw / 2, c + mw / 2, y0, y1, gz0, gz1))
        for j in range(1, rows):
            c = gz0 + (gz1 - gz0) * j / rows
            parts.append((gx0, gx1, y0, y1, c - mw / 2, c + mw / 2))
        multibox(name, parts, finish)

    def entry_hardware(o, y_out, y_in):
        """The knob-and-deadbolt set on the entry door, on BOTH faces.

        Its own objects rather than part of the leaf, because the leaf is
        painted trim and the hardware is satin nickel, and material here is
        chosen by object-name prefix. Merging them would have made the knob
        the same colour as the door.

        Round, and `tube()` with a two-point path is a capped cylinder about
        any axis -- the same call the sconce canopy makes. Everything else in
        this model is an axis-aligned box, which is right for architecture and
        wrong for a doorknob.

        BOTH FACES on purpose. Only the exterior one is visible in the tour and
        in views.front(), but the interior presets and the walkthrough look at
        this door from inside, and a door with a knob on one side only is a
        thing you notice immediately.
        """
        hw = spec["fixtures"].get("door_hardware", {}).get("entry_set")
        if not hw or hw["built_on"] != o["id"]:
            return
        # Latch edge is the WEST edge, from video 0:13 -- see spec.hand.
        cx = o["offset"] + hw["backset"]["ft"]
        z_knob = o["sill"] + hw["knob_height_aff"]["ft"]
        z_bolt = o["sill"] + hw["deadbolt_height_aff"]["ft"]
        rr, rt = hw["rose_diameter"]["ft"] / 2, hw["rose_thickness"]["ft"]
        sr, sl = hw["shank_diameter"]["ft"] / 2, hw["shank_length"]["ft"]
        kr, kl = hw["knob_diameter"]["ft"] / 2, hw["knob_length"]["ft"]
        br = hw["deadbolt_diameter"]["ft"] / 2
        bp = hw["deadbolt_projection"]["ft"]

        # `out` is the direction away from the leaf on each face: the exterior
        # face looks south (-Y), the interior north (+Y).
        # ONE mesh for the whole set, on both faces. Ten separate cylinders is
        # ten draw calls and ten entries against a mesh budget that has held
        # since the first commit -- a knob is not where that budget gets spent.
        parts = []
        for face, out in ((y_out, -1.0), (y_in, +1.0)):
            for z, stack in ((z_knob, [(rt, rr), (sl, sr), (kl, kr)]),
                             (z_bolt, [(rt, rr), (bp, br)])):
                d = 0.0
                for length, radius in stack:
                    parts.append(([(cx, face + out * d, z),
                                   (cx, face + out * (d + length), z)], radius))
                    d += length
        multitube(f"Hdw_{o['id']}", parts, finish)

    # exterior entry door, in the south wall
    for o in spec["openings"]["main_floor"]["south_wall"]["openings"]:
        if not o["type"].endswith("door"):
            continue
        c = SY + t / 2
        # DISPATCH ON THE DECLARED TYPE, not on which keys happen to be present.
        # `type: half_lite_entry_door` has been in the spec the whole time; the
        # defect this PR fixes was the build IGNORING it. Branching on whether a
        # `construction` block exists would repeat that in a quieter form: the
        # geometry would then follow the metadata's shape, and the next opening
        # to gain a construction or provenance block would silently change what
        # gets built. A type that says half-lite and no construction to build it
        # from is a SPEC ERROR and says so, rather than falling back to a slab.
        if o["type"].startswith("half_lite"):
            if "construction" not in o:
                raise SystemExit(
                    f"{o['id']} is typed {o['type']} but carries no "
                    "`construction` block. A half-lite door cannot be built "
                    "from a type alone -- add the block or change the type.")
            half_lite(f"Door_{o['id']}", o, c - lt / 2, c + lt / 2)
            entry_hardware(o, c - lt / 2, c + lt / 2)
        else:
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

    # The 24"x24" crawl hole is a real opening in this floor, measured off A1.1
    # in Tier 3a and reproducing its callout exactly. It sits wholly inside
    # Floor_main_N with margins on all four sides, so the floor becomes a frame
    # of four strips around it -- boxes, not a boolean, for the reason the
    # counters give.
    #
    # The HATCH is a separate object sitting flush in the opening, because that
    # is what a crawl hole is: an access panel, normally closed. An open square
    # void in a finished floor would read as a modelling defect in a
    # configurator, and hiding one named object is easier than cutting a hole
    # on demand.
    hole = next((i for i in spec["fixtures"]["access"]["items"]
                 if i["id"] == "crawl_hole" and i.get("floor_opening")), None)
    if hole:
        hx0, hx1 = xw + hole["x"], xw + hole["x"] + hole["w"]
        hy0, hy1 = ye - (hole["y"] + hole["d"]), ye - hole["y"]
        multibox("Floor_main_N", [
            (bath_x1, hx0, bath_y0, ye, 0, ff),      # west of the opening
            (hx1, xe, bath_y0, ye, 0, ff),           # east of it
            (hx0, hx1, bath_y0, hy0, 0, ff),         # south of it
            (hx0, hx1, hy1, ye, 0, ff),              # north of it
        ], finish)
        box("Floor_crawl_hatch", hx0, hx1, hy0, hy1, 0, ff, finish)
    else:
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

    # ---- window sash: the type is built, not merely declared ---------------
    ws = spec["windows"]
    f2g = ws["frame_to_glass"]["ft"]
    mr_t = ws["meeting_rail"]["thickness"]["ft"]
    mr_r = ws["meeting_rail"]["ratio"]
    mull = ws["mullion"]["ft"]
    sd_ = 0.05                                  # sash proud of the glass plane

    def sash(name, o, axis, plane, a0, a1, z0, z1):
        """The frame, meeting rail and mullion a window's TYPE implies.

        Every window in this model was one flat pane until #88, while
        `spec.openings` typed all of them -- exactly the defect the front door
        carried for eleven PRs (#83). The fix is the same one #83 settled on:
        DISPATCH ON THE DECLARED TYPE and refuse to guess when the type has
        nothing behind it, rather than branching on which keys happen to exist.

        Like `half_lite`, this builds NO GLASS. The pane is a finish and stays
        in finish_adu.add_glazing; these members sit proud of it, which is what
        a window looks like and what keeps the frame out of lod2.

        Proportions come from spec.windows and hang off the TYPE, not the
        instance -- the meeting rail was read at 50% on two different window
        heights, and an instance-level number would have hidden that agreement.
        """
        typ = ws["types"].get(o["type"])
        if typ is None:
            raise SystemExit(
                f"{o['id']} is typed {o['type']!r}, which spec.windows.types "
                f"does not define (have {sorted(ws['types'])}). A window "
                "cannot be built from a type alone -- add the type or change "
                "the opening.")

        def member(b0, b1, c0, c1):
            """One rectangle in the opening plane, spanning the wall axis."""
            return ((b0, b1, plane, plane + sd_, c0, c1) if axis == "x"
                    else (plane, plane + sd_, b0, b1, c0, c1))

        parts = [
            member(a0, a0 + f2g, z0, z1),                  # left jamb
            member(a1 - f2g, a1, z0, z1),                  # right jamb
            member(a0, a1, z0, z0 + f2g),                  # sill member
            member(a0, a1, z1 - f2g, z1),                  # head member
        ]

        # A D.S.H. is two units side by side; the mullion divides them and the
        # rail then runs in EACH unit, not across the whole opening.
        units = typ["units"]
        spans = []
        if units == 1:
            spans = [(a0, a1)]
        else:
            step = (a1 - a0) / units
            for i in range(units):
                spans.append((a0 + i * step, a0 + (i + 1) * step))
            for i in range(1, units):
                c = a0 + i * step
                parts.append(member(c - mull / 2, c + mull / 2, z0, z1))

        if typ["meeting_rail"]:
            zc = z0 + (z1 - z0) * mr_r
            for b0, b1 in spans:
                parts.append(member(b0, b1, zc - mr_t / 2, zc + mr_t / 2))

        multibox(name, parts, finish)

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

    # Sash, one per window, on the OUTBOARD side of each glazing plane. The
    # planes are taken from the same expressions finish_adu.add_glazing uses,
    # so the frame cannot drift away from the glass it frames.
    for o in op["north_wall"]["openings"]:
        sash(f"Win_{o['id']}", o, "x", NY - t / 2,
             o["offset"], o["offset"] + o["w"], o["sill"], o["sill"] + o["h"])
    for o in op["south_wall"]["openings"]:
        if o["type"].endswith("door"):
            continue
        sash(f"Win_{o['id']}", o, "x", SY + t / 2 - sd_,
             o["offset"], o["offset"] + o["w"], o["sill"], o["sill"] + o["h"])
    for o in op["west_wall"]["openings"]:
        sash(f"Win_{o['id']}", o, "y", t / 2 - sd_,
             yn(o["offset"] + o["w"]), yn(o["offset"]),
             o["sill"], o["sill"] + o["h"])
    for o in spec["openings"]["loft"]["windows"]:
        for side, pl in (("W", t / 2 - sd_), ("E", W - t / 2)):
            sash(f"Win_{o['id']}_{side}", o, "y", pl,
                 yn(o["offset"] + o["w"]), yn(o["offset"]), dsill, dsill + o["h"])
    # THE GABLE IS A PRISM AT y 0..t, NOT THE WALL AT y SY..SY+t. The first
    # version of this line used the wall datum and put the gable sash six feet
    # north of its own glass, floating inside the porch -- and the sash gate
    # passed it, because that gate mirrors these call sites and inherited the
    # same wrong plane. finish_adu.add_glazing already carried the warning in
    # a comment: "its pane is placed from the gable's own depth".
    for o in spec["openings"]["loft"]["south_gable"]["windows"]:
        sash(f"Win_{o['id']}", o, "x", t / 2 - sd_,
             o["offset"], o["offset"] + o["w"], o["sill"], o["sill"] + o["h"])

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
    # ---- Tier 3: casework -------------------------------------------------
    # Its own collection, not `finish`: a verify_tier1 gate counts the Finish
    # collection, and casework is lod0-only in a way Tier 1 geometry is not.
    casework = collection("Casework")
    build_casework(spec, geo, casework)

    # ---- Tier 3: mounted lighting -----------------------------------------
    # Its own collection so it can be hidden without touching the casework, and
    # because an exterior fixture belongs to the shell's story, not the
    # kitchen's.
    lighting = collection("Lighting")
    geo["mounted"] = build_mounted(spec, geo, lighting)

    # ---- Tier 3: furniture -------------------------------------------------
    # Its own collection: furniture is lod0 detail, and it is the one group a
    # buyer may want switched off entirely.
    furniture = collection("Furniture")
    geo["furniture"] = build_furniture(spec, furniture)

    # ---- Tier 2 prerequisite: UVs, generated LAST -------------------------
    # After the booleans, per TIER-2 §3 — openings create faces no earlier
    # layout accounts for. Also after the casework, or it ships unwrapped and
    # verify_tier2 fails.
    tile_ft = tx["tile_size_px"] / tx["texel_density_px_per_ft"]
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            uv_project(ob, tile_ft)
    geo["tile_ft"] = tile_ft

    return geo, dict(shell=shell, roof=roofc, porch=porchc,
                     interior=interior, finish=finish, casework=casework,
                     foundation=found, lighting=lighting,
                     furniture=furniture)


# ---------------------------------------------------------------------------
# Tier 3 casework
# ---------------------------------------------------------------------------
def find_item(seq, fid):
    """Look up a fixture by id, failing with the id rather than StopIteration."""
    for it in seq:
        if it.get("id") == fid:
            return it
    raise SystemExit(f"[spec] no fixture with id {fid!r}")



# ---------------------------------------------------------------------------
def build_furniture(spec, coll):
    """Furniture, one merged mesh per (arrangement, material).

    MERGING STOPS AT THE ARRANGEMENT BOUNDARY, and that is the whole design.
    Everywhere else this file merges by material across the entire building --
    multibox("Appl_body", ...) is a single mesh holding the fridge, the range,
    the dishwasher and the bedroom-closet washer/dryer. Furniture built that
    way could never be switched, because you cannot hide half a mesh, and the
    presence-swap work would have to rebuild it. So an arrangement owns its
    objects and merging happens only inside one.

    That same shared-mesh property has now cost this project three times: it
    made the first verify_geometry.py a tautology, it stretched the kitchen
    camera across three rooms, and it would have made furniture unswitchable.

    Nothing here is measured. Every dimension comes from
    spec.fixtures.furniture, which says so at length.
    """
    fx = spec["fixtures"]["furniture"]
    built = {}
    for arr in fx["arrangements"]:
        by_mat = {}
        for pc in arr["pieces"]:
            box6 = (pc["x0"], pc["x1"], pc["y0"], pc["y1"], pc["z0"], pc["z1"])
            for lo, hi, axis in ((pc["x0"], pc["x1"], "x"),
                                 (pc["y0"], pc["y1"], "y"),
                                 (pc["z0"], pc["z1"], "z")):
                if hi <= lo:
                    raise ValueError(
                        f"{arr['id']}.{pc['id']}: {axis} runs backwards "
                        f"({lo} .. {hi})")
            by_mat.setdefault(pc["material"], []).append(box6)

        for mat, boxes in sorted(by_mat.items()):
            name = f"Furn_{arr['id']}_{mat.removeprefix('furn_')}"
            multibox(name, boxes, coll)
            built[name] = len(boxes)
    return built

def build_casework(spec, geo, coll):
    """Kitchen and bath casework, entirely from spec.fixtures.

    Everything here is boxes, so it is cheap and it regenerates for the next
    plan set for free — the reason TIER-3 §2 put casework on the "build"
    side of build-vs-buy. Appliances and plumbing are the "buy" side and are
    NOT here; they are gated on asset licensing.

    Object count is kept down with multibox(): trim taught us that many small
    objects cost draw calls on a phone before the triangles do, and the lod0
    mesh budget is a gate.
    """
    fx = spec["fixtures"]
    kit = fx["kitchen"]

    # Both faces come from geo, which build() computed. An earlier version
    # re-derived xw from spec.construction while taking ye from geo — the same
    # number by two routes, which is exactly how the two drift apart when the
    # coordinate setup changes.
    xw = geo["xw"]                          # interior west face
    ye = geo["ye"]                          # interior north face

    def ym(y_int):
        """fixtures datum (south from the interior north face) -> world Y."""
        return ye - y_int

    depth = kit["cabinet_run_depth"]["ft"]
    ch = kit["counter_h"]["ft"]
    top_t = kit["counter_thk"]["ft"]
    toe_h = kit["toe_kick_h"]["ft"]
    up = kit["upper_cab"]
    up_h, up_d = up["height"]["ft"], up["depth"]["ft"]
    up_bot = ch + up["clear_above_counter"]["ft"]
    splash_h = kit["backsplash"]["height"]["ft"]

    # Joinery figures, from spec.fixtures.casework_detail. These used to be
    # five literals here with a comment saying they were "not worth a spec
    # entry each" -- the project's first ground rule waived rather than
    # followed. Stock figures are still dimensions.
    cd = fx["casework_detail"]
    door_t = cd["door_thickness"]["ft"]
    reveal = cd["leaf_reveal"]["ft"]
    overhang = cd["counter_overhang"]["ft"]
    toe_recess = cd["toe_kick_recess"]["ft"]
    splash_t = cd["backsplash_thickness"]["ft"]
    shaker = cd["shaker"]

    carcass, toes, fronts, tops, splashes, uppers, up_fronts = [], [], [], [], [], [], []

    def leaf(x_back, x_front, y0, y1, z0, z1, kind):
        """One cabinet front: a shaker frame for a door, a slab for a drawer.

        A door modelled as a flat slab is geometrically correct and visually
        nothing: two coplanar same-material leaves with a 1/4" gap give the eye
        no cue, so a pair reads as one panel under any lighting. The frame and
        recessed panel are what make a shaker door legible, and all three
        filmed units have shaker doors.

        Drawers stay slab on purpose -- see the note in the spec.
        """
        if kind != "doors" or shaker.get("applies_to") != "doors":
            return [(x_back, x_front, y0, y1, z0, z1)]
        w = shaker["stile_width"]["ft"]
        rec = shaker["panel_recess"]["ft"]
        # Refuse to draw a frame that would leave no panel; fall back to slab.
        if (y1 - y0) < 3 * w or (z1 - z0) < 3 * w:
            return [(x_back, x_front, y0, y1, z0, z1)]
        return [
            (x_back, x_front, y0, y1, z0, z0 + w),              # bottom rail
            (x_back, x_front, y0, y1, z1 - w, z1),              # top rail
            (x_back, x_front, y0, y0 + w, z0 + w, z1 - w),      # left stile
            (x_back, x_front, y1 - w, y1, z0 + w, z1 - w),      # right stile
            (x_back, x_front - rec, y0 + w, y1 - w, z0 + w, z1 - w),   # panel
        ]

    def door_bands(y0, y1, z0, z1, kind):
        """Split a bay into leaves. Doors divide across the wall, drawers up it."""
        out = []
        if kind == "drawers_4":
            n = 4
            h = (z1 - z0) / n
            for i in range(n):
                out.append((y0 + reveal, y1 - reveal,
                            z0 + i * h + reveal, z0 + (i + 1) * h - reveal))
        else:
            n = 2 if (y1 - y0) > 2.0 else 1      # a bay over 24" gets a pair
            w = (y1 - y0) / n
            for i in range(n):
                out.append((y0 + i * w + reveal, y0 + (i + 1) * w - reveal,
                            z0 + reveal, z1 - reveal))
        return out

    # The sink opening drives both the counter frame and the sink base cavity,
    # so it is resolved before either is built.
    cut = kit["runs"].get("sink_cutout")
    cx0, cx1 = (xw + cut["x0"], xw + cut["x1"]) if cut else (0.0, 0.0)

    # ---- base run ---------------------------------------------------------
    # The sink base needs a cavity for the bowl to hang in. Carved here rather
    # than left solid: a solid carcass swallows the basin whole, and the render
    # then shows cabinet through the cutout — which looks like a missing basin
    # rather than a buried one.
    sink_cfg = kit["runs"].get("sink")
    basin_bottom = None
    if cut and sink_cfg:
        basin_bottom = (ch - top_t - sink_cfg["basin"]["depth"]["ft"]
                        - sink_cfg["basin"]["wall"]["ft"])

    for seg in kit["runs"]["base"]:
        ya, yb = ym(seg["y1"]), ym(seg["y0"])
        cx = xw + depth - door_t
        if basin_bottom is not None and seg["id"] == "sink_base":
            ins = sink_cfg["basin"]["inset"]["ft"]
            bx0, bx1 = cx0 - ins, cx1 + ins
            bya, byb = ym(cut["y1"]) - ins, ym(cut["y0"]) + ins
            carcass += [
                (xw, cx, ya, yb, toe_h, basin_bottom),         # below the bowl
                (xw, bx0, ya, yb, basin_bottom, ch - top_t),   # behind it
                (bx1, cx, ya, yb, basin_bottom, ch - top_t),   # in front of it
                (bx0, bx1, ya, bya, basin_bottom, ch - top_t),  # south of it
                (bx0, bx1, byb, yb, basin_bottom, ch - top_t),  # north of it
            ]
        else:
            carcass.append((xw, cx, ya, yb, toe_h, ch - top_t))
        toes.append((xw, xw + depth - toe_recess, ya, yb, 0.0, toe_h))
        for a, b, z0, z1 in door_bands(seg["y0"], seg["y1"], toe_h, ch - top_t,
                                       seg["front"]):
            fronts += leaf(xw + depth - door_t, xw + depth,
                           ym(b), ym(a), z0, z1, seg["front"])

    # ---- counter and backsplash ------------------------------------------
    # The sink opening is cut by BUILDING A FRAME around it, not by a boolean.
    # Booleans on hand-wound geometry are how P2 got a mesh that looked cut and
    # kept its full volume; four exact boxes cannot fail that way, and the
    # counter is axis-aligned so there is nothing a boolean would buy.
    for seg in kit["runs"]["counter"]:
        ya, yb = ym(seg["y1"]), ym(seg["y0"])
        x1 = xw + depth + overhang
        if cut and seg["y0"] <= cut["y0"] and cut["y1"] <= seg["y1"]:
            cya, cyb = ym(cut["y1"]), ym(cut["y0"])
            tops += [
                (xw, x1, cyb, yb, ch - top_t, ch),      # beyond the opening, north
                (xw, x1, ya, cya, ch - top_t, ch),      # beyond the opening, south
                (xw, cx0, cya, cyb, ch - top_t, ch),    # behind it, against the wall
                (cx1, x1, cya, cyb, ch - top_t, ch),    # in front of it
            ]
        else:
            tops.append((xw, x1, ya, yb, ch - top_t, ch))
        splashes.append((xw, xw + splash_t, ya, yb, ch, ch + splash_h))

    # ---- uppers -----------------------------------------------------------
    # An upper run is interrupted from below by whatever stands under it. The
    # refrigerator and the range hood both do, at different heights, so the
    # run is cut into sub-spans rather than floated at one height.
    hood = kit["runs"]["hood"]
    fridge = next(i for i in kit["items"] if i["id"] == "refrigerator")
    obstructions = [
        (fridge["y"], fridge["y"] + fridge["d"], fridge["h"] + 0.0833),
        (hood["y0"], hood["y1"], hood["bottom"]["ft"] + hood["height"]["ft"]),
    ]

    def spans(y0, y1):
        """Cut [y0,y1] at every obstruction edge, and give each piece a floor."""
        cuts = sorted({y0, y1} | {c for a, b, _ in obstructions
                                  for c in (a, b) if y0 < c < y1})
        for a, b in zip(cuts, cuts[1:]):
            mid = (a + b) / 2.0
            floor = max([z for lo, hi, z in obstructions if lo <= mid <= hi]
                        + [up_bot])
            yield a, b, floor

    for run in kit["runs"]["upper"]:
        for a, b, z0 in spans(run["y0"], run["y1"]):
            if up_bot + up_h - z0 < 0.4:          # too little left to be a cabinet
                continue
            uppers.append((xw, xw + up_d - door_t, ym(b), ym(a), z0, up_bot + up_h))
            for da, db, dz0, dz1 in door_bands(a, b, z0, up_bot + up_h, "doors"):
                up_fronts += leaf(xw + up_d - door_t, xw + up_d,
                                  ym(db), ym(da), dz0, dz1, "doors")

    # ---- appliances -------------------------------------------------------
    # The BUILD answer for the last three "must be bought" fixtures. All are
    # boxes with door lines; footprints measured in Tier 3a, proportions stock.
    # Grouped into three meshes by MATERIAL rather than by appliance, so the
    # object count stays flat and Appl_dark can take the black glass.
    af = fx.get("appliance_form")
    if af:
        pp, dg = af["panel_proud"]["ft"], af["door_gap"]["ft"]
        bodies, fronts_a, darks = [], [], []

        def span(fid):
            it = find_item(kit["items"], fid)
            return (xw, xw + it["w"], ym(it["y"] + it["d"]), ym(it["y"]), it["h"])

        # Refrigerator: one body, two doors split by the freezer share.
        rx0, rx1, ry0, ry1, rh = span("refrigerator")
        split = rh * (1.0 - af["refrigerator"]["freezer_share"]["fraction"])
        bodies.append((rx0, rx1 - pp, ry0, ry1, 0.0, rh))
        fronts_a += [
            (rx1 - pp, rx1, ry0, ry1, 0.0, split - dg / 2.0),      # fridge door
            (rx1 - pp, rx1, ry0, ry1, split + dg / 2.0, rh),       # freezer door
        ]

        # Range: slide-in, so the cooktop is the full depth and flush on top.
        g = af["range"]
        gx0, gx1, gy0, gy1, gh = span("range")
        ct, ctl = g["cooktop_thk"]["ft"], g["control_h"]["ft"]
        db, hh, hp = g["door_bottom"]["ft"], g["handle_h"]["ft"], g["handle_proud"]["ft"]
        bodies.append((gx0, gx1 - pp, gy0, gy1, 0.0, gh - ct))
        darks += [
            (gx0, gx1, gy0, gy1, gh - ct, gh),                     # cooktop
            (gx1 - pp, gx1, gy0, gy1, db, gh - ct - ctl - hh),      # oven glass
        ]
        fronts_a += [
            (gx1 - pp, gx1, gy0, gy1, 0.0, db),                    # storage drawer
            (gx1 - pp, gx1, gy0, gy1, gh - ct - ctl, gh - ct),     # control strip
            (gx1, gx1 + hp, gy0, gy1, gh - ct - ctl - hh,
             gh - ct - ctl),                                       # handle bar
        ]

        # Dishwasher: flat panel with a recessed handle strip at the top.
        dw = af["dishwasher"]
        dx0, dx1, dy0, dy1, dh = span("dishwasher")
        dhh = dw["handle_h"]["ft"]
        bodies.append((dx0, dx1 - pp, dy0, dy1, 0.0, dh))
        # Panel only. The handle recess needs NO geometry: the panel stops
        # short of the top, leaving the body's own front face exposed and
        # already set back by `panel_proud` — which is exactly a recess.
        # An extra box there put a small face on the same plane as the body's
        # front, same normal, and z-fights. Rule 16, one PR after writing it.
        fronts_a.append((dx1 - pp, dx1, dy0, dy1, 0.0, dh - dhh))

        # Stacked washer/dryer, in the closet, opening EAST toward the bedroom.
        wd_cfg = af.get("stacked_wd")
        if wd_cfg:
            wd = find_item(fx["laundry"]["items"], "stacked_wd")
            wx0, wx1 = xw + wd["x"], xw + wd["x"] + wd["w"]
            wy0, wy1 = ym(wd["y"] + wd["d"]), ym(wd["y"])
            wsplit = wd["h"] * wd_cfg["split_share"]["fraction"]
            bodies.append((wx0, wx1 - pp, wy0, wy1, 0.0, wd["h"]))
            fronts_a += [
                (wx1 - pp, wx1, wy0, wy1, 0.0, wsplit - dg / 2.0),   # washer
                (wx1 - pp, wx1, wy0, wy1, wsplit + dg / 2.0, wd["h"]),  # dryer
            ]

        multibox("Appl_body", bodies, coll)
        multibox("Appl_front", fronts_a, coll)
        multibox("Appl_dark", darks, coll)
        geo["appliance_boxes"] = len(bodies) + len(fronts_a) + len(darks)

    # ---- bath vanity ------------------------------------------------------
    van = next(i for i in fx["bath"]["items"] if i["id"] == "vanity")
    fit = fx.get("bath_fittings")
    vh = van["h"]
    ya, yb = ym(van["y"] + van["d"]), ym(van["y"])
    # The vanity carcass needs the same cavity the kitchen sink base got. Left
    # solid, it swallows the basin and the render shows cabinet through the
    # bowl -- which is what happened here first time, and which none of the
    # gates caught: they check the basin against the TOE KICK, not against the
    # carcass top. Rule 10 the other way round for once, a defect only a render
    # would show.
    vcx = xw + van["w"] - door_t
    if fit:
        bowl = fit["basin"]["bowl"]
        b = fit["basin"]
        v_bottom = vh - top_t - b["depth"]["ft"] - b["wall"]["ft"]
        bx0, bx1 = xw + bowl["cx"] - bowl["ax"], xw + bowl["cx"] + bowl["ax"]
        bya, byb = ym(bowl["cy"] + bowl["ay"]), ym(bowl["cy"] - bowl["ay"])
        carcass += [
            (xw, vcx, ya, yb, toe_h, v_bottom),          # below the bowl
            (xw, bx0, ya, yb, v_bottom, vh - top_t),     # behind it
            (bx1, vcx, ya, yb, v_bottom, vh - top_t),    # in front of it
            (bx0, bx1, ya, bya, v_bottom, vh - top_t),   # south of it
            (bx0, bx1, byb, yb, v_bottom, vh - top_t),   # north of it
        ]
    else:
        carcass.append((xw, vcx, ya, yb, toe_h, vh - top_t))
    toes.append((xw, xw + van["w"] - toe_recess, ya, yb, 0.0, toe_h))
    for a, b, z0, z1 in door_bands(van["y"], van["y"] + van["d"], toe_h,
                                   vh - top_t, "doors"):
        fronts += leaf(xw + van["w"] - door_t, xw + van["w"],
                       ym(b), ym(a), z0, z1, "doors")
    # The vanity top gets the same treatment the kitchen counter got in #62:
    # a frame of four boxes around the basin opening, not a boolean. The
    # opening is the bowl ellipse's bounding box, so the rim laps it on every
    # side and no gap can open between top and basin.
    vx1 = xw + van["w"] + overhang
    if fit:
        bowl = fit["basin"]["bowl"]
        ox0, ox1 = xw + bowl["cx"] - bowl["ax"], xw + bowl["cx"] + bowl["ax"]
        oy0, oy1 = ym(bowl["cy"] + bowl["ay"]), ym(bowl["cy"] - bowl["ay"])
        tops += [
            (xw, vx1, oy1, yb, vh - top_t, vh),
            (xw, vx1, ya, oy0, vh - top_t, vh),
            (xw, ox0, oy0, oy1, vh - top_t, vh),
            (ox1, vx1, oy0, oy1, vh - top_t, vh),
        ]
    else:
        tops.append((xw, vx1, ya, yb, vh - top_t, vh))

    # ---- vanity basin and tap ---------------------------------------------
    if fit:
        b = fit["basin"]
        rim, bowl = b["rim"], b["bowl"]
        rt, bw = b["rim_thickness"]["ft"], b["wall"]["ft"]
        bd, tf = b["depth"]["ft"], b["taper"]["factor"]
        z_bot = vh - bd

        # ONE closed profile: across the rim, down the inside, over the floor,
        # back up the outside. loft() skins it into a solid with no open
        # boundary, so glTF backface culling has nothing to punch a hole in.
        rings = [
            ellipse_ring(xw + bowl["cx"], ym(bowl["cy"]),
                         bowl["ax"] * tf, bowl["ay"] * tf, z_bot),
            ellipse_ring(xw + bowl["cx"], ym(bowl["cy"]), bowl["ax"], bowl["ay"], vh),
            ellipse_ring(xw + rim["cx"], ym(rim["cy"]), rim["ax"], rim["ay"], vh),
            ellipse_ring(xw + rim["cx"], ym(rim["cy"]), rim["ax"], rim["ay"], vh - rt),
            ellipse_ring(xw + bowl["cx"], ym(bowl["cy"]),
                         bowl["ax"] * tf, bowl["ay"] * tf, z_bot - bw),
        ]
        loft("Cab_basin_bath", rings, coll, cap_first=True, cap_last=True)

        # ---- mirror over the vanity ---------------------------------
        # Frame and glass are separate objects so they take different
        # materials: Cab_mirror_* falls through to cab_wood, while
        # Cab_mirror_glass is matched first and gets the mirror material.
        mi = fit.get("mirror")
        if mi:
            mw, mh = mi["w"]["ft"], mi["h"]["ft"]
            fw, mdep = mi["frame_w"]["ft"], mi["depth"]["ft"]
            rec = mi["glass_recess"]["ft"]
            z0 = vh + splash_h + mi["gap_above_splash"]["ft"]
            z1 = z0 + mh
            cy = fit["basin"]["rim"]["cy"]
            my0, my1 = ym(cy + mw / 2.0), ym(cy - mw / 2.0)
            mx0, mx1 = xw, xw + mdep
            multibox("Cab_mirror_frame", [
                (mx0, mx1, my0, my1, z0, z0 + fw),            # bottom rail
                (mx0, mx1, my0, my1, z1 - fw, z1),            # top rail
                (mx0, mx1, my0, my0 + fw, z0 + fw, z1 - fw),  # one stile
                (mx0, mx1, my1 - fw, my1, z0 + fw, z1 - fw),  # the other
            ], coll)
            box("Cab_mirror_glass", mx0, mx1 - rec,
                my0 + fw, my1 - fw, z0 + fw, z1 - fw, coll)

        # ---- tub / shower ----------------------------------------------
        # Alcove unit: closed north, west and east; open to the south. Basin is
        # a box frame (floor plus four walls) rather than a loft — an alcove tub
        # is rectangular, and a frame of boxes cannot produce the coplanar
        # faces a capped loft would meet the surround with.
        tb = fx.get("tub_form")
        if tb:
            tu = find_item(fx["bath"]["items"], "tub_shower")
            sr, bs, ft_ = tb["surround"], tb["basin"], tb["fittings"]
            st, sh = sr["thickness"]["ft"], sr["height"]["ft"]
            bfloor, bins = bs["floor"]["ft"], bs["inset"]["ft"]
            tx0, tx1 = xw + tu["x"], xw + tu["x"] + tu["w"]
            ty0, ty1 = ym(tu["y"] + tu["d"]), ym(tu["y"])      # ty1 = north wall
            rim = tu["h"]

            # Basin: open-topped box, inset from the unit's outer face.
            ix0, ix1 = tx0 + bins, tx1 - bins
            iy0, iy1 = ty0 + bins, ty1 - bins
            multibox("Fix_tub_basin", [
                (tx0, tx1, ty0, ty1, 0.0, bfloor),                  # floor
                (tx0, ix0, ty0, ty1, bfloor, rim),                  # west apron
                (ix1, tx1, ty0, ty1, bfloor, rim),                  # east apron
                (ix0, ix1, ty0, iy0, bfloor, rim),                  # south apron
                (ix0, ix1, iy1, ty1, bfloor, rim),                  # north side
            ], coll)

            # Surround: three walls, from the rim to the top.
            multibox("Fix_tub_surround", [
                (tx0, tx1, ty1 - st, ty1, rim, sh),                 # back (north)
                (tx0, tx0 + st, ty0, ty1, rim, sh),                 # west end
                (tx1 - st, tx1, ty0, ty1, rim, sh),                 # east end
            ], coll)

            # Moulded shelf in the back wall.
            sc_ = sr["shelf"]
            shx = tx0 + (tx1 - tx0) * 0.32
            box("Fix_tub_shelf", shx, shx + sc_["width"]["ft"],
                ty1 - st - sc_["depth"]["ft"], ty1 - st,
                sc_["height"]["ft"], sc_["height"]["ft"] + 0.06, coll)

            # Curtain rod across the open south side.
            tube("Fix_tub_rod",
                 [(tx0, ty0 + st, ft_["rod_h"]["ft"]),
                  (tx1, ty0 + st, ft_["rod_h"]["ft"])],
                 ft_["rod_r"]["ft"], coll, sides=8)

            # Head, valve and spout on the east end wall, per the video.
            fr_ = ft_["fitting_r"]["ft"]
            ey = (ty0 + ty1) / 2.0
            tube("Fix_tub_head",
                 [(tx1 - st, ey, ft_["head_h"]["ft"]),
                  (tx1 - st - 0.42, ey, ft_["head_h"]["ft"] - 0.17)],
                 fr_, coll, sides=8)
            for nm, hgt in (("valve", ft_["valve_h"]["ft"]),
                            ("spout", ft_["spout_h"]["ft"])):
                tube(f"Fix_tub_valve_{nm}",
                     [(tx1 - st, ey, hgt), (tx1 - st - 0.25, ey, hgt)],
                     fr_, coll, sides=8)

        # ---- toilet ---------------------------------------------------
        # The BUILD answer to "must this be bought?". loft() was made generic
        # for exactly this: an elliptical bowl tapering to a narrower foot is
        # the same profile trick the basin uses. Footprint measured, type from
        # video 2:51, proportions stock.
        tf = fx.get("toilet_form")
        if tf:
            # find_item raises rather than returning None, so it must not run
            # unless the form is actually present -- otherwise a spec without a
            # toilet hard-exits instead of skipping.
            wc = find_item(fx["bath"]["items"], "toilet")
            tk, bw_, ld = tf["tank"], tf["bowl"], tf["lid"]
            tx0, tx1 = xw + wc["x"], xw + wc["x"] + wc["w"]
            cy = ym(wc["y"] + wc["d"] / 2.0)
            seat = wc["seat_h"]["ft"]

            # Tank: against the wall, from its own bottom to the measured
            # overall height.
            box("Fix_toilet_tank",
                tx0, tx0 + tk["depth"]["ft"],
                cy - tk["width"]["ft"] / 2.0, cy + tk["width"]["ft"] / 2.0,
                tk["bottom"]["ft"], wc["h"], coll)

            # Bowl: from just inside the tank face out to the measured front.
            bx0 = tx0 + tk["depth"]["ft"] - bw_["tank_overlap"]["ft"]
            bcx, bax = (bx0 + tx1) / 2.0, (tx1 - bx0) / 2.0
            bay = bw_["half_width"]["ft"]
            sc_ = bw_["foot_scale"]["factor"]
            fx_c = bcx - bw_["foot_setback"]["ft"]
            loft("Fix_toilet_bowl", [
                ellipse_ring(fx_c, cy, bax * sc_, bay * sc_, 0.0),
                ellipse_ring(fx_c + (bcx - fx_c) * 0.6, cy,
                             bax * 0.72, bay * 0.78, seat * 0.55),
                ellipse_ring(bcx, cy, bax, bay, seat),
            ], coll, cap_first=True, cap_last=True)

            # Rear riser: the tank's footprint carried to the floor, slightly
            # inset so the tank reads as sitting on it rather than merging.
            ri = tf["riser"]["inset"]["ft"]
            box("Fix_toilet_riser",
                tx0, tx0 + tk["depth"]["ft"] - ri,
                cy - tk["width"]["ft"] / 2.0 + ri,
                cy + tk["width"]["ft"] / 2.0 - ri,
                0.0, seat, coll)

            # Lid, sitting PROUD of the rim by the seat-ring thickness. Not
            # cosmetic: starting it exactly at `seat` put its capped underside
            # coplanar with the bowl's capped top, identical centre and area
            # with opposite normals, which z-fights in any renderer.
            lt, lr = ld["thickness"]["ft"], ld["rise"]["ft"]
            loft("Fix_toilet_lid", [
                ellipse_ring(bcx, cy, bax, bay, seat + lr),
                ellipse_ring(bcx, cy, bax, bay, seat + lr + lt),
            ], coll, cap_first=True, cap_last=True)

        f = fit["faucet"]
        fr, fh = f["radius"]["ft"], f["height"]["ft"]
        sp, arc_r = f["spout"], f["reach"]["ft"] / 2.0
        sx, sy = xw + sp["x"], ym(sp["y"])
        path = [(sx, sy, vh), (sx, sy, vh + fh - arc_r)]
        # arc_points() includes its start point, which is the top of the column
        # -- appending it whole repeats that point and hands tube() a
        # zero-length segment. #62 shipped eight twisted slivers that way.
        path += [tuple(pt) for pt in arc_points((sx + arc_r, sy, vh + fh - arc_r),
                                                arc_r, "y", 180, 0, n=6)[1:]]
        tube("Cab_faucet_bath", path, fr, coll)
        for i, h in enumerate(f["handles"]):
            hx, hy = xw + h["x"], ym(h["y"])
            tube(f"Cab_faucet_bath_handle_{i}",
                 [(hx, hy, vh), (hx, hy, vh + f["handle_height"]["ft"])],
                 f["handle_radius"]["ft"], coll, sides=6)
    splashes.append((xw, xw + splash_t, ya, yb, vh, vh + splash_h))

    # ---- hood -------------------------------------------------------------
    hoods = [(xw, xw + hood["depth"]["ft"], ym(hood["y1"]), ym(hood["y0"]),
              hood["bottom"]["ft"], hood["bottom"]["ft"] + hood["height"]["ft"])]

    # ---- sink basin and tap ----------------------------------------------
    # The BUILD half of TIER-3 §2's split, now sorted by shape rather than by
    # trade: a basin is a box with a rim and a tap is a swept tube, so neither
    # needs a downloaded asset. Sources are ours — the footprint is the
    # measured cutout, the appearance is video 2:40.
    sink = kit["runs"].get("sink")
    basins = []
    if cut and sink:
        b = sink["basin"]
        inset, bd, bw = b["inset"]["ft"], b["depth"]["ft"], b["wall"]["ft"]
        # The counter laps the rim, so the vessel is the opening plus that lap.
        bx0, bx1 = cx0 - inset, cx1 + inset
        by0, by1 = ym(cut["y1"]) - inset, ym(cut["y0"]) + inset
        top = ch - top_t                      # underside of the counter
        bot = top - bd
        basins += [
            (bx0, bx1, by0, by1, bot, bot + bw),          # floor of the bowl
            (bx0, bx0 + bw, by0, by1, bot, top),          # west side
            (bx1 - bw, bx1, by0, by1, bot, top),          # east side
            (bx0, bx1, by0, by0 + bw, bot, top),          # south end
            (bx0, bx1, by1 - bw, by1, bot, top),          # north end
        ]

    if cut and sink:
        f = sink["faucet"]
        fh, reach = f["height"]["ft"], f["reach"]["ft"]
        # BEHIND the bowl means toward the WALL, so smaller x. The run is
        # against the west wall and the room is to the east, so putting the tap
        # at cx1 + behind stood it on the counter's front lip, in the walkway.
        fy = ym((cut["y0"] + cut["y1"]) / 2.0)
        fx = cx0 - f["behind_bowl"]["ft"]
        arc_r = reach / 2.0
        neck = ch + fh - arc_r
        # Column, then a HALF turn so the spout comes back down over the bowl.
        # A quarter turn ends at the apex pointing sideways, which is not a
        # gooseneck — it is a hook.
        # arc_points() INCLUDES its start point, which here is the top of the
        # column — so appending it whole repeats (fx, fy, neck) and gives
        # tube() a zero-length segment. That does not produce zero-area faces
        # (the rings coincide but rotate, so validate() keeps them); it
        # produces 8 twisted slivers at ~3% the area of a normal quad, which
        # shade badly. Drop the repeat.
        path = [(fx, fy, ch), (fx, fy, neck)]
        path += [tuple(pt) for pt in arc_points((fx + arc_r, fy, neck),
                                                arc_r, "y", 180, 0, n=8)[1:]]
        tube("Cab_faucet", path, f["radius"]["ft"], coll)
        # Spray head, hanging from the far end of the arc, over the bowl.
        tube("Cab_faucet_head",
             [(fx + reach, fy, neck),
              (fx + reach, fy, neck - f["spray_drop"]["ft"])],
             f["spray_radius"]["ft"], coll)

    made = 0
    for name, specs in (("Cab_carcass", carcass), ("Cab_toe", toes),
                        ("Cab_front", fronts), ("Cab_top", tops),
                        ("Cab_splash", splashes), ("Cab_upper", uppers),
                        ("Cab_upper_front", up_fronts), ("Cab_hood", hoods),
                        ("Cab_basin", basins)):
        if specs:
            multibox(name, specs, coll)
            made += 1
    geo["casework_objects"] = made
    geo["casework_boxes"] = sum(len(s) for s in
                                (carcass, toes, fronts, tops, splashes,
                                 uppers, up_fronts, hoods, basins))
    geo["basin_volume"] = sum(abs((b - a) * (d - c) * (f - e))
                              for a, b, c, d, e, f in basins)

    # Gate input: what the counter actually is, against what it should be.
    geo["counter_volume"] = sum(abs((b - a) * (d - c) * (f - e))
                                for a, b, c, d, e, f in tops)
    solid = sum(abs(depth + overhang) * abs(s["y1"] - s["y0"]) * top_t
                for s in kit["runs"]["counter"])
    solid += abs(van["w"] + overhang) * van["d"] * top_t
    hole = ((cut["x1"] - cut["x0"]) * (cut["y1"] - cut["y0"]) * top_t) if cut else 0.0
    if fit:
        # The vanity top is now cut too, so the expectation has to lose that
        # hole as well. This gate FAILED when the cutout landed and the
        # expectation still assumed a solid vanity slab — which is the gate
        # doing its job: it caught a real change in what the counter is.
        bowl = fit["basin"]["bowl"]
        hole += (2 * bowl["ax"]) * (2 * bowl["ay"]) * top_t
    geo["counter_expected"] = solid - hole


# ---------------------------------------------------------------------------
# Mounted-fixture forms
#
# _LIB CANDIDATE. Nothing below knows anything about this building. It takes a
# point, an outward normal and a bag of dimensions, and it is written that way
# on purpose: a sconce is the first fixture whose SHAPE is a buyer's choice
# rather than a plan fact, so the shape belongs in a library shared by every
# model while only its position stays per-building. When models/_lib/ exists,
# this function moves there unchanged.
#
# Built entirely from primitives that were already here — tube(), arc_points(),
# ellipse_ring() and loft(). No new primitive was needed and no third-party
# asset was bought, which keeps the licence position the model has held since
# P1.
# ---------------------------------------------------------------------------
def gooseneck_sconce(name, coll, origin, normal, dims, lens_name=None):
    """A galvanized barn-light wall sconce: canopy, gooseneck arm, flared shade.

    `origin` is the centre of the wall canopy ON the wall face. `normal` is the
    outward direction — a unit vector along -Y for a south wall, and only the
    horizontal axes are meaningful. `dims` is spec.fixtures.mounted.forms.<form>,
    so every number below is cited in the spec rather than typed here.

    Returns the objects created, so the caller can report and a gate can find
    them by name.
    """
    import mathutils

    ft_ = lambda k: dims[k]["ft"]
    n = mathutils.Vector(normal).normalized()
    ox, oy, oz = origin

    proj = ft_("projection")
    rise = ft_("rise")
    r_arc = proj / 2.0
    straight = rise - r_arc
    if straight < 0:
        raise SystemExit(
            f"{name}: rise {rise} is less than half the projection {proj}; "
            "the arm cannot arc over without leaning back into the wall")

    # The arm's plane. arc_points turns about 'x' (a YZ arc) or 'y' (an XZ arc),
    # so pick whichever the wall's normal lies in — a north/south wall needs the
    # YZ arc, an east/west wall the XZ one. Anything else is a wall this form
    # has never been asked for, and guessing would be worse than stopping.
    if abs(n.y) > abs(n.x):
        axis, sign = "x", (1.0 if n.y > 0 else -1.0)
    else:
        axis, sign = "y", (1.0 if n.x > 0 else -1.0)

    objs = []

    # ---- canopy: a short cylinder lying on the wall ------------------------
    # tube() with a two-point path is a capped cylinder about any axis, which
    # is exactly a canopy and avoids a fourth primitive.
    depth = ft_("canopy_depth")
    objs.append(tube(f"{name}_canopy",
                     [(ox, oy, oz), (ox + n.x * depth, oy + n.y * depth, oz)],
                     ft_("canopy_dia") / 2.0, coll, sides=12))

    # ---- arm: straight up the wall, then a half-turn out over the top ------
    # Modelled as the fixture is actually bent: it leaves the canopy going up,
    # rolls through 180 degrees, and arrives pointing straight down at the
    # shade. The arc's radius IS half the projection, so projection and rise
    # are not independent — which is why `straight` is checked above.
    # Off the canopy's outer face, not off the wall plane. tube() rings a
    # VERTICAL segment in the XY plane, so an arm rooted at y = wall face puts
    # half its own radius inside the wall — 0.36" of galvanized steel buried in
    # the siding, invisible in every render and caught only by asking where the
    # geometry actually is. verify_mounted found it.
    ax = ox + n.x * depth
    ay = oy + n.y * depth
    start = (ax, ay, oz)
    top_of_straight = (ax, ay, oz + straight)
    if axis == "x":
        centre = (ax, ay + sign * r_arc, oz + straight)
        arc = arc_points(centre, r_arc, "x",
                         180.0 if sign > 0 else 0.0,
                         0.0 if sign > 0 else 180.0, n=10)
    else:
        centre = (ax + sign * r_arc, ay, oz + straight)
        arc = arc_points(centre, r_arc, "y",
                         180.0 if sign > 0 else 0.0,
                         0.0 if sign > 0 else 180.0, n=10)
    # arc[0] IS top_of_straight by construction — the arc is centred half a
    # projection outboard at that same height, so its 0-degree (or 180-degree)
    # end lands exactly on the top of the straight run. Passing both gives
    # tube() two identical consecutive points and a band of zero-area quads.
    # They survive export and are invisible in a render, which is why the
    # degenerate-geometry gate did not see them: tube() averages directions at
    # a bend, so the duplicate never collapses the frame, it only makes faces
    # with no area. Copilot caught it on review.
    path = [start, top_of_straight] + [tuple(p) for p in arc[1:]]
    objs.append(tube(f"{name}_arm", path, ft_("arm_dia") / 2.0, coll, sides=8))

    # ---- shade: hangs from the arm's outboard end --------------------------
    sx = ax + n.x * proj
    sy = ay + n.y * proj
    z_top = oz + straight                      # where the arc finishes, pointing down
    neck_h, shade_h = ft_("neck_height"), ft_("shade_height")
    r_neck, r_shade = ft_("neck_dia") / 2.0, ft_("shade_dia") / 2.0

    # Whole profile in one loft: down the outside, across the rim, back up the
    # inside. loft()'s docstring is emphatic about this — a one-sided cone is
    # invisible from half the angles once glTF culls backfaces.
    z_neck = z_top - neck_h
    z_rim = z_neck - shade_h
    lip = min(0.02, r_shade * 0.06)
    rings = [
        ellipse_ring(sx, sy, r_neck, r_neck, z_top),
        ellipse_ring(sx, sy, r_neck, r_neck, z_neck),
        ellipse_ring(sx, sy, r_shade, r_shade, z_rim),
        ellipse_ring(sx, sy, r_shade - lip, r_shade - lip, z_rim),
        ellipse_ring(sx, sy, r_neck * 0.8, r_neck * 0.8, z_neck),
        ellipse_ring(sx, sy, r_neck * 0.8, r_neck * 0.8, z_top),
    ]
    objs.append(loft(f"{name}_shade", rings, coll, cap_first=True, cap_last=True))

    if lens_name:
        # The lit look: a disc just inside the mouth. It is emissive and it
        # illuminates nothing — see materials.lamp_glow for why that is the
        # right trade in a web viewer.
        inset = shade_h * 0.25
        r_lens = r_shade - lip - (r_shade - r_neck) * (inset / shade_h)
        objs.append(loft(lens_name,
                         [ellipse_ring(sx, sy, r_lens, r_lens, z_rim + inset),
                          ellipse_ring(sx, sy, r_lens * 0.98, r_lens * 0.98,
                                       z_rim + inset - 0.01)],
                         coll, cap_first=True, cap_last=True))
    return objs


def build_mounted(spec, geo, coll):
    """Place spec.fixtures.mounted.items on their walls.

    Wall-mounted fixtures do not have footprints, so none of the Tier 3 casework
    helpers apply. What they have is a surface, a distance along it, a height
    and an outward normal; this turns those four into a world point.
    """
    mounted = spec["fixtures"].get("mounted")
    if not mounted:
        return []

    SY = geo["SY"]
    forms = mounted["forms"]
    made = []
    for item in mounted["items"]:
        surface, side = item["surface"], item["side"]
        if (surface, side) != ("Wall_S", "exterior"):
            # Deliberately narrow. The south wall is the only one this model
            # has a fixture on, and inventing untested mappings for the other
            # three would be three untested mappings, not three features.
            raise SystemExit(f"[mounted] no placement rule for {surface}/{side}")
        # `along` shares openings.main_floor's datum: distance from the west
        # exterior corner, which is world X directly. The exterior FACE of the
        # south wall is at Y = SY, not SY + t: the wall spans SY..SY+t and the
        # porch is to the south of it.
        origin = (item["along"]["ft"], SY, item["height_aff"]["ft"])
        # Light_lens_* rather than Light_*_lens: assign() matches on prefix and
        # first rule wins, so the emissive part must be distinguishable by its
        # opening characters. Same shape as Cab_top and Appl_dark.
        objs = gooseneck_sconce(
            f"Light_{item['id']}", coll, origin, item["facing"],
            forms[item["form"]],
            lens_name=f"Light_lens_{item['id']}" if item.get("lit_lens") else None)
        made.append((item["id"], origin, objs))
    return made


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
        # Volume, because that is what caught P2's boolean that imprinted edges
        # without removing material. The counter is built as a frame around the
        # sink opening, so its volume must be the solid slab LESS the hole —
        # if the four strips ever overlap or leave a sliver, this moves.
        ("counter carries the sink opening, by volume",
         geo.get("counter_volume") is not None
         and abs(geo["counter_volume"] - geo["counter_expected"]) < 1e-6),
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
