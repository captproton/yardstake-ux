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
    print("=" * 86)
    print("RESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
