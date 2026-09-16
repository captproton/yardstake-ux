"""
adu_kit/kernel.py — the geometry kernel: boxes, prisms, welds, sweeps, lofts,
booleans, reveals, in-plane UVs, and reading a spec. Blender only.

MOVED, NOT CHANGED (#126), from models/barn_cabin_524/build_adu.py. Nothing
here knows a building: no dimension, no object name, no material. The barn
cabin's export is byte-identical before and after the move, which is the
test that it stayed a move. Its comments still cite the barn cabin where
that is where a rule was learned.
"""
import json
import math
import shutil
import subprocess
from pathlib import Path

import bpy
import bmesh


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


def box_geom(x0, x1, y0, y1, z0, z1):
    """One box as (verts, faces). Split out for the same reason `tube_geom` was:
    the geometry and the object are different decisions."""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def prism_geom(pts, lo, hi, plane="xz"):
    """Closed polygon extruded along the third axis, as (verts, faces).

    `plane` says which two axes the polygon lives in, so a raked member can be
    drawn in the plane it actually rakes in. The loft ladder leans along Y and
    climbs in Z, so its rails are a "yz" prism extruded across X -- drawn as
    XZ they would have to be faked with a staircase of boxes, which is exactly
    what they were until #95.
    """
    n = len(pts)
    if plane == "xz":
        ring = lambda c: [(a, c, b) for a, b in pts]
    elif plane == "yz":
        ring = lambda c: [(c, a, b) for a, b in pts]
    else:
        raise ValueError(f"prism_geom: plane must be 'xz' or 'yz', got {plane!r}")
    verts = ring(lo) + ring(hi)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return verts, faces


def clip_band(pts, lo, hi, idx=1):
    """Clip a closed polygon to a band on one axis. Sutherland-Hodgman.

    The ladder's dados need this: a dado is the rail's inner lamination
    ABSENT over the rung's thickness, so each length of that lamination is the
    rail profile clipped between two rungs. Clipping the real profile rather
    than approximating it with a rectangle keeps the flat foot and the
    radiused top intact at the two ends of the run, where the profile is not a
    rectangle at all.

    `idx` picks the axis within each 2-tuple: for a "yz" prism the points are
    (y, z) and the dado runs across z, which is 1.
    """
    def half(poly, val, keep_above):
        out = []
        for i, c in enumerate(poly):
            nx = poly[(i + 1) % len(poly)]
            cin = c[idx] >= val if keep_above else c[idx] <= val
            nin = nx[idx] >= val if keep_above else nx[idx] <= val
            if cin:
                out.append(c)
            if cin != nin:
                t = (val - c[idx]) / (nx[idx] - c[idx])
                out.append(tuple(c[j] + t * (nx[j] - c[j]) for j in range(2)))
        return out
    band = half(pts, lo, True)
    return half(band, hi, False) if len(band) >= 3 else []


def weld(name, parts, coll):
    """Several (verts, faces) pieces as ONE mesh, whatever produced them.

    `multibox` and `multitube` each weld one KIND of primitive. A ladder is
    two raked prisms and nine boxes that share a material and never move
    apart, so neither of those fits and three objects would be the wrong
    answer against a cap of 120.
    """
    verts, faces = [], []
    for v, f in parts:
        off = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + off for i in face) for face in f)
    return _new_obj(name, verts, faces, coll)


def multibox(name, specs, coll):
    """Several boxes as ONE mesh. Trim would otherwise explode the object count."""
    return weld(name, [box_geom(*s) for s in specs], coll)


def sash_geom(axis, plane, a0, a1, z0, z1, frame, proud,
              units=1, meeting_rail_at=None, meeting_rail_thickness=0.0,
              mullion=0.0):
    """The members a window's TYPE implies, as a list of box specs (#129).

    Promoted out of the barn cabin, which held the only part that knew a
    building: it read `spec.windows` and its own type table directly. Laurel
    needs the same members from a different table, so what is left here knows
    no building -- an opening, a frame width, and how many units the type says
    it has. The caller looks the type up and passes what it found.

    `axis` is the wall axis the opening spans, "x" or "y". `a0`..`a1` run
    along it and `z0`..`z1` up. `plane` is the GLAZING PLANE, and every member
    straddles it by `proud` on each side.

    A SASH IS SEEN FROM BOTH SIDES, which is why `proud` reaches both ways.
    The barn cabin's first version put a plate outboard of the glass, so the
    divisions read from the garden while the same window was one flat pane
    from the sofa: glass is drawn before the thing behind it, so the members
    were hidden by the pane they divide. A real sash holds the glass rather
    than sitting in front of it.

    `units` is how many sashes sit side by side, divided by a mullion. A
    meeting rail then runs in EACH unit rather than across the whole opening,
    which is what a pair of units looks like and what one span would get
    wrong. `meeting_rail_at` is the fraction of the opening's height it sits
    at, or None for a type that has none.

    It builds NO GLASS. The pane is a finish; these members sit proud of it.
    """
    def member(b0, b1, c0, c1):
        d0, d1 = plane - proud, plane + proud
        return ((b0, b1, d0, d1, c0, c1) if axis == "x"
                else (d0, d1, b0, b1, c0, c1))

    parts = [
        member(a0, a0 + frame, z0, z1),                # left jamb
        member(a1 - frame, a1, z0, z1),                # right jamb
        member(a0, a1, z0, z0 + frame),                # sill member
        member(a0, a1, z1 - frame, z1),                # head member
    ]

    spans = []
    if units == 1:
        spans = [(a0, a1)]
    else:
        step = (a1 - a0) / units
        for i in range(units):
            spans.append((a0 + i * step, a0 + (i + 1) * step))
        for i in range(1, units):
            c = a0 + i * step
            parts.append(member(c - mullion / 2, c + mullion / 2, z0, z1))

    if meeting_rail_at is not None:
        zc = z0 + (z1 - z0) * meeting_rail_at
        for b0, b1 in spans:
            parts.append(member(b0, b1, zc - meeting_rail_thickness / 2,
                                zc + meeting_rail_thickness / 2))
    return parts


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
    v, f = prism_geom(pts_xz, y0, y1, "xz")
    return _new_obj(name, v, f, coll)


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
