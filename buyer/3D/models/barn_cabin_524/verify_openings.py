"""
verify_openings.py — geometric check that every opening in spec.yaml actually
exists in the built mesh, at the right place and the right size.

This does not trust a render. For each opening it asserts two things:

  VOLUME   the wall solid lost exactly the opening's volume. This is the strong
           test and the one that earns its keep: P2 shipped booleans that
           imprinted edges without removing material, so face counts rose and
           corners existed while the mesh kept its full volume. Only volume
           caught it.
  CORNERS  the wall mesh carries vertices at the corners of the hole.

It does NOT sample points for inside/outside containment. An earlier version of
this docstring said it did, which was never true — and a docstring describing a
check that does not exist is worse than no docstring, because it invites the
reader to trust a guarantee nobody is making.

Run after build_adu.py:

    blender --background barn_cabin_524.blend --python verify_openings.py
"""
import sys
from pathlib import Path

import math

import bpy
import bmesh
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec, ft  # noqa: E402
from verify_lib import inside_mesh  # noqa: E402

TOL = 0.02


def wall_verts(name):
    ob = bpy.data.objects[name]
    return [ob.matrix_world @ v.co for v in ob.data.vertices]


def has_vert(verts, target, tol=TOL):
    t = Vector(target)
    return any((v - t).length <= tol for v in verts)


def volume(name):
    """Signed volume of a closed mesh, in cubic feet."""
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[name].data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def main():
    spec = load_spec(HERE / "spec.yaml")
    env, con, lv = spec["envelope"], spec["construction"], spec["levels"]
    W = env["main_body_width"]["ft"]
    D = env["main_body_depth"]["ft"]
    t = con["exterior_wall_thickness"]["ft"]
    plate = lv["main_top_of_plate"]["ft"]
    knee = lv["loft_knee_wall_height"]["ft"]
    dorm_len = spec["roof"]["dormers"]["width"]["ft"]
    P = env["porch_depth"]["ft"]
    NY = P + D          # north (rear) face — see build_adu frame convention
    SY = P              # south (front) face
    yn = lambda d: NY - d
    # Dormer face height must be derived exactly as build_adu.py derives it:
    # the wall runs from the loft subfloor up to the dormer roof underside.
    rt = con["roof_assembly_thickness"]["ft"]
    rf = spec["roof"]
    mp = rf["main_pitch"]["rise"] / rf["main_pitch"]["run"]
    dp = rf["dormer_pitch"]["rise"] / rf["dormer_pitch"]["run"]
    ridge_top = rf["elevation_calibration"]["ridge_top_of_roof"]["ft"]
    dp_v = rt / math.cos(math.atan(dp))
    dorm_under_wall = (ridge_top - dp * (W / 2.0)) - dp_v
    dorm_h = dorm_under_wall - lv["loft_top_of_subfloor"]["ft"]
    loft_sf = lv["loft_top_of_subfloor"]["ft"]
    dsill = loft_sf + con["dormer_window_sill_above_loft_floor"]["ft"]
    mp_v = rt / math.cos(math.atan(mp))
    main_under_wall = (ridge_top - mp * (W / 2.0)) - mp_v
    ridge_under = ridge_top - mp_v
    op = spec["openings"]["main_floor"]

    # wall -> (gross volume, [openings], corner builder)
    walls = {
        "Wall_N": (W * t * plate, op["north_wall"]["openings"],
                   lambda o: [(o["offset"] + dx * o["w"], NY, o["sill"] + dz * o["h"])
                              for dx in (0, 1) for dz in (0, 1)], t),
        "Wall_S": (W * t * plate, op["south_wall"]["openings"],
                   lambda o: [(o["offset"] + dx * o["w"], SY, o["sill"] + dz * o["h"])
                              for dx in (0, 1) for dz in (0, 1)], t),
        "Wall_W": (t * (D - 2 * t) * plate, op["west_wall"]["openings"],
                   lambda o: [(0.0, yn(o["offset"] + dy * o["w"]), o["sill"] + dz * o["h"])
                              for dy in (0, 1) for dz in (0, 1)], t),
        "Wall_E": (t * (D - 2 * t) * plate, op["east_wall"]["openings"], lambda o: [], t),
        "Dormer_face_W": (t * dorm_len * dorm_h, spec["openings"]["loft"]["windows"],
                          lambda o: [(0.0, yn(o["offset"] + dy * o["w"]), dsill + dz * o["h"])
                                     for dy in (0, 1) for dz in (0, 1)], t),
        "Dormer_face_E": (t * dorm_len * dorm_h, spec["openings"]["loft"]["windows"],
                          lambda o: [(W, yn(o["offset"] + dy * o["w"]), dsill + dz * o["h"])
                                     for dy in (0, 1) for dz in (0, 1)], t),
        # The south gable, which is a PRISM and not a wall -- so its gross
        # volume is the profile area times the thickness, not W x t x plate.
        # These three levels are re-derived here rather than imported for the
        # same reason `dorm_under_wall` above is: a gate that reads the number
        # the build used cannot catch the build using the wrong number.
        "Gable_S_porch": (
            (W * (main_under_wall - plate)
             + W * (ridge_under - main_under_wall) / 2.0) * t,
            spec["openings"]["loft"]["south_gable"]["windows"],
            lambda o: [(o["offset"] + dx * o["w"], 0.0, o["sill"] + dz * o["h"])
                       for dx in (0, 1) for dz in (0, 1)], t),
    }

    # interior partitions: same volume test, driven by the measured layout
    lay = spec["interior_partitions"]["layout"]
    ti = con["interior_wall_thickness"]["ft"]
    dby = {}
    for dr in lay["doors"]:
        dby.setdefault(dr["in"], []).append(dr)
    for pdef in lay["partitions"]:
        run = abs(pdef["to_ft"] - pdef["from_ft"])
        gross = run * ti * plate
        walls[f"Part_{pdef['id']}"] = (gross, dby.get(pdef["id"], []), lambda o: [], ti)

    print("\n" + "=" * 86)
    print("OPENING VERIFICATION — built mesh vs spec.yaml")
    print("=" * 86)
    print(f"{'wall':16} {'openings':>8} {'corners':>9} {'gross ft3':>10} "
          f"{'expected':>10} {'actual':>10} {'err':>7}  {'result':>7}")
    print("-" * 86)

    ok = True
    for name, (gross, ops, corner_fn, wt) in walls.items():
        cut = sum(o["w"] * o["h"] * wt for o in ops)
        expected = gross - cut
        actual = volume(name)
        err = actual - expected
        vol_ok = abs(err) < 0.05

        vs = wall_verts(name)
        c_ok = all(has_vert(vs, c) for o in ops for c in corner_fn(o))

        good = vol_ok and c_ok
        ok &= good
        print(f"{name:16} {len(ops):>8} {'PASS' if c_ok else 'FAIL':>9} "
              f"{gross:10.2f} {expected:10.2f} {actual:10.2f} {err:7.3f}  "
              f"{'PASS' if good else 'FAIL':>7}")

    print("-" * 86)
    print("Volume is the strong test: it confirms the holes exist AND are the")
    print("right size. Corner test confirms they are in the right place.")

    ok &= sash_gates(spec)

    print("=" * 86)
    print("RESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
    if not ok:
        raise SystemExit(1)


def sash_gates(spec):
    """Every window carries the divisions its declared TYPE implies.

    WRITTEN AGAINST THE FAILURE MODE (ground rule 24). The failure is a window
    that went back to being one flat pane, or one built as the wrong type --
    and the obvious gate, counting vertices, CANNOT SEE IT. A single_hung is
    four frame members plus a rail; a slider_XO is four plus a mullion. Both
    are five boxes and forty vertices. Counting passes on a slider built as a
    single-hung and on a single-hung built as a slider.

    So it samples POSITION. At the centre of every member the type implies the
    point must be inside sash solid, and at the centre of every light it must
    NOT be -- the second half being what fails when a window quietly becomes
    the wrong type, since a missing rail leaves the light where the rail was.
    """
    ws = spec["windows"]
    mr_r = ws["meeting_rail"]["ratio"]
    print()
    ok = True
    rows = []
    for name, o, axis, a0, a1, z0, z1, host_name in sash_targets(spec):
        obj = bpy.data.objects.get(name)
        if obj is None:
            rows.append((name, o["type"], "MISSING", ""))
            ok = False
            continue
        # A TYPE THE SPEC DOES NOT DEFINE IS A FINDING, NOT A CRASH. Indexing
        # straight into types[] would raise a KeyError out of the whole run,
        # so the suite would abort without naming the window that caused it --
        # a traceback where a readable gate failure belongs. build_adu already
        # refuses this case with a clear message; the gate should report it.
        typ = ws["types"].get(o["type"])
        if typ is None:
            rows.append((name, o["type"], "FAIL",
                         f"no such type in spec.windows.types "
                         f"(have {sorted(ws['types'])})"))
            ok = False
            continue
        units, rail = typ["units"], typ["meeting_rail"]
        zc = z0 + (z1 - z0) * mr_r
        step = (a1 - a0) / units

        want_solid, want_air = [], []
        for i in range(1, units):
            # SAMPLE THE MULLION CLEAR OF THE RAIL, at quarter and
            # three-quarter height. Mid-height is where a meeting rail crosses
            # it, so a sample there is inside three boxes at once -- a
            # degenerate point for a surface test, and worse, a point a rail
            # alone could satisfy. Two samples in different sashes can only be
            # explained by a full-height member.
            for f in (0.25, 0.75):
                want_solid.append((a0 + i * step, z0 + (z1 - z0) * f))
        for i in range(units):                           # per-unit light centres
            b = a0 + (i + 0.5) * step
            if rail:
                want_solid.append((b, zc))
                want_air += [(b, (z0 + zc) / 2), (b, (zc + z1) / 2)]
            else:
                want_air.append((b, (z0 + z1) / 2))

        bad = []
        for b, z in want_solid:
            if not solid_at(obj, axis, b, z):
                bad.append(f"no solid at ({b:.2f},{z:.2f})")
        for b, z in want_air:
            if solid_at(obj, axis, b, z):
                bad.append(f"solid where a light belongs ({b:.2f},{z:.2f})")
        # IS THE SASH EVEN IN ITS OWN WALL? The composition checks above are
        # blind to this: they sample at the object's OWN mid-depth, so a sash
        # built on the wrong datum is internally perfect and six feet from its
        # glass. That shipped -- the gable sash was placed on the wall plane
        # when its gable is a prism at y 0..t -- and every member gate passed.
        # A gate that only asks "is this well-formed" cannot ask "is this in
        # the right place", so the depth is checked against the host solid.
        host = bpy.data.objects.get(host_name)
        if host is None:
            bad.append(f"host {host_name} missing")
        else:
            i = 1 if axis == "x" else 0        # the depth axis of this wall
            sv = [obj.matrix_world @ v.co for v in obj.data.vertices]
            hv = [host.matrix_world @ v.co for v in host.data.vertices]
            s0, s1 = min(v[i] for v in sv), max(v[i] for v in sv)
            h0, h1 = min(v[i] for v in hv), max(v[i] for v in hv)
            if s1 < h0 - 0.1 or s0 > h1 + 0.1:
                bad.append(f"sits at {s0:.2f}..{s1:.2f} but {host_name} "
                           f"spans {h0:.2f}..{h1:.2f}")

        rows.append((name, o["type"],
                     "PASS" if not bad else "FAIL",
                     f"{len(want_solid)} members, {len(want_air)} lights, "
                     f"in {host_name}"
                     if not bad else "; ".join(bad[:2])))
        ok &= not bad

    w = max(len(r[0]) for r in rows)
    for name, typ, verdict, detail in rows:
        print(f"  [{verdict:4}] {name.ljust(w)}  {typ:20s} {detail}")
    print("A slider and a single-hung are both five boxes: this samples the")
    print("members' POSITIONS, because counting cannot tell them apart.")
    return ok and casing_gates(spec)


def casing_gates(spec):
    """Exterior casing exists, and is on the side of the wall you can see.

    THE FAILURE MODE IS BEING ON THE WRONG FACE, not being absent. Every
    `Trim_` in this model was interior casing for the whole ladder --
    Trim_D-FRONT at y 6.458..6.518 on a wall whose exterior face is 6.000 --
    and #80's own table ticked exterior casing as done, pointing at exactly
    that object. Nothing caught it because nothing asked which side.

    So the gate is a signed comparison against the exterior face, and it would
    have failed on day one. Presence is checked too, but presence is the weak
    half: a casing on the wrong face is present.
    """
    print()
    obj = bpy.data.objects.get("Trim_ext")
    if obj is None:
        print("  [FAIL] Trim_ext missing — no exterior casing at all")
        return False

    cw = spec["trim"]["casing_width"]["ft"]
    rows, ok = [], True
    for oid, host, face, out, sill, a0, a1, z0, z1 in casing_targets(spec):
        # SAMPLED PER OPENING, not read off a bounding box. The casing is one
        # welded mesh now, so a bbox says only where the whole run is -- it
        # cannot tell that ONE window lost its casing, nor that one is on the
        # wrong face. Two samples per jamb do both: outboard must be solid,
        # and the mirror point inboard of the wall must be air.
        i = 0 if out[0] else 1
        sgn = out[i]
        depth = 0.03
        bad = []
        for a in (a0 - cw / 2, a1 + cw / 2):          # both jambs
            zc = (z0 + z1) / 2
            p_out = [0.0, 0.0, zc]
            p_in = [0.0, 0.0, zc]
            j = 1 - i
            p_out[j] = p_in[j] = a
            p_out[i] = face + sgn * depth
            p_in[i] = face - sgn * depth
            if not inside_mesh(obj, Vector(p_out)):
                bad.append(f"no casing outboard at {a:.2f}")
            elif inside_mesh(obj, Vector(p_in)):
                bad.append(f"casing INBOARD of the face at {a:.2f}")
        rows.append((f"Trim_ext/{oid}", "PASS" if not bad else "FAIL",
                     "; ".join(bad) or
                     f"both jambs outboard of {face:.2f} on {host}"
                     f"{'' if sill else ' (no sill: a door)'}"))
        ok &= not bad

    w = max(len(r[0]) for r in rows)
    for name, verdict, detail in rows:
        print(f"  [{verdict:4}] {name.ljust(w)}  {detail}")
    print("Presence is the weak half: casing on the WRONG FACE is present.")
    return ok


def casing_targets(spec):
    """(id, host, exterior face, outward vector, has a sill, a0, a1, z0, z1)."""
    env = spec["envelope"]
    NY = env["porch_depth"]["ft"] + env["main_body_depth"]["ft"]
    SY = env["porch_depth"]["ft"]
    W = env["main_body_width"]["ft"]
    op = spec["openings"]["main_floor"]
    con = spec["construction"]
    loft_sf = spec["levels"]["loft_top_of_subfloor"]["ft"]
    dsill = loft_sf + con["dormer_window_sill_above_loft_floor"]["ft"]

    def yn(v):
        return NY - v

    out = []
    for o in op["north_wall"]["openings"]:
        out.append((o["id"], "Wall_N", NY, (0, +1), True,
                    o["offset"], o["offset"] + o["w"], o["sill"], o["sill"] + o["h"]))
    for o in op["south_wall"]["openings"]:
        out.append((o["id"], "Wall_S", SY, (0, -1),
                    not o["type"].endswith("door"),
                    o["offset"], o["offset"] + o["w"], o["sill"], o["sill"] + o["h"]))
    for o in op["west_wall"]["openings"]:
        out.append((o["id"], "Wall_W", 0.0, (-1, 0), True,
                    yn(o["offset"] + o["w"]), yn(o["offset"]),
                    o["sill"], o["sill"] + o["h"]))
    for o in spec["openings"]["loft"]["windows"]:
        for side, face, vec, host in (("W", 0.0, (-1, 0), "Dormer_face_W"),
                                      ("E", W, (+1, 0), "Dormer_face_E")):
            out.append((f"{o['id']}_{side}", host, face, vec, True,
                        yn(o["offset"] + o["w"]), yn(o["offset"]),
                        dsill, dsill + o["h"]))
    for o in spec["openings"]["loft"]["south_gable"]["windows"]:
        out.append((o["id"], "Gable_S_porch", 0.0, (0, -1), True,
                    o["offset"], o["offset"] + o["w"], o["sill"], o["sill"] + o["h"]))
    return out


def sash_targets(spec):
    """(object, opening, axis, a0, a1, z0, z1, host) for every window, as built.

    Mirrors build_adu's own call sites rather than re-deriving them, so a
    window that moves cannot leave the gate testing empty air.
    """
    env, con = spec["envelope"], spec["construction"]
    NY = env["porch_depth"]["ft"] + env["main_body_depth"]["ft"]
    op = spec["openings"]["main_floor"]
    loft_sf = spec["levels"]["loft_top_of_subfloor"]["ft"]
    dsill = loft_sf + con["dormer_window_sill_above_loft_floor"]["ft"]

    def yn(v):
        return NY - v

    out = []
    for o in op["north_wall"]["openings"] + op["south_wall"]["openings"]:
        if o["type"].endswith("door"):
            continue
        out.append((f"Win_{o['id']}", o, "x", o["offset"], o["offset"] + o["w"],
                    o["sill"], o["sill"] + o["h"],
                    "Wall_N" if o in op["north_wall"]["openings"] else "Wall_S"))
    for o in spec["openings"]["loft"]["south_gable"]["windows"]:
        out.append((f"Win_{o['id']}", o, "x", o["offset"], o["offset"] + o["w"],
                    o["sill"], o["sill"] + o["h"], "Gable_S_porch"))
    for o in op["west_wall"]["openings"]:
        out.append((f"Win_{o['id']}", o, "y", yn(o["offset"] + o["w"]),
                    yn(o["offset"]), o["sill"], o["sill"] + o["h"], "Wall_W"))
    for o in spec["openings"]["loft"]["windows"]:
        for side in ("W", "E"):
            out.append((f"Win_{o['id']}_{side}", o, "y",
                        yn(o["offset"] + o["w"]), yn(o["offset"]),
                        dsill, dsill + o["h"], f"Dormer_face_{side}"))
    return out


def solid_at(obj, axis, b, z):
    """Is (b, z) in the opening plane inside this sash object?

    The sash is a thin plate, so the sample is taken at its own mid-depth
    rather than at a wall plane -- a point on the face is neither in nor out.
    """
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if axis == "x":
        mid = (min(v.y for v in vs) + max(v.y for v in vs)) / 2
        p = Vector((b, mid, z))
    else:
        mid = (min(v.x for v in vs) + max(v.x for v in vs)) / 2
        p = Vector((mid, b, z))
    return inside_mesh(obj, p)


if __name__ == "__main__":
    main()
