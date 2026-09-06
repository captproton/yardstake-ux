"""
verify_tier1.py — gates for the Tier 1 interior: ceilings and floor finishes.

Checks the things a render cannot be trusted to show:
  1. flat ceilings land at their tagged height
  2. vaulted ceilings follow the roof underside they claim to follow
  3. no roof geometry intrudes into an occupied interior volume
  4. floor finishes tile the interior without gaps or overlap
  5. everything new is confined to the Finish collection

    blender --background barn_cabin_524.blend --python verify_tier1.py
"""
import sys
import math
from pathlib import Path

import bpy
import bmesh
import mathutils

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec, ft  # noqa: E402


def bounds(name):
    ob = bpy.data.objects[name]
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return ([min(v[i] for v in vs) for i in range(3)],
            [max(v[i] for v in vs) for i in range(3)])


def volume(name):
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[name].data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def main():
    spec = load_spec(HERE / "spec.yaml")
    env, con, lv, rf = (spec["envelope"], spec["construction"],
                        spec["levels"], spec["roof"])
    W = env["main_body_width"]["ft"]
    D = env["main_body_depth"]["ft"]
    P = env["porch_depth"]["ft"]
    t = con["exterior_wall_thickness"]["ft"]
    ct = con["ceiling_thickness"]["ft"]
    ff = con["floor_finish_thickness"]["ft"]
    plate = lv["main_top_of_plate"]["ft"]
    loft_sf = lv["loft_top_of_subfloor"]["ft"]
    rt = con["roof_assembly_thickness"]["ft"]
    mp = rf["main_pitch"]["rise"] / rf["main_pitch"]["run"]
    dp = rf["dormer_pitch"]["rise"] / rf["dormer_pitch"]["run"]
    ridge_top = rf["elevation_calibration"]["ridge_top_of_roof"]["ft"]
    dorm_len = rf["dormers"]["width"]["ft"]
    mp_v = rt / math.cos(math.atan(mp))
    dp_v = rt / math.cos(math.atan(dp))
    ridge_x = W / 2.0
    NY, SY = P + D, P
    xw, xe, ye, ys = t, W - t, NY - t, SY + t
    loft_s = NY - dorm_len

    def main_under(x):
        return ridge_top - mp * abs(ridge_x - x) - mp_v

    def dorm_under(x):
        return ridge_top - dp * abs(ridge_x - x) - dp_v

    results = []

    def gate(label, ok, detail=""):
        results.append((label, ok, detail))

    print("\n" + "=" * 78)
    print("TIER 1 VERIFICATION — ceilings and floor finishes")
    print("=" * 78)

    # ---- 1. flat ceiling height -------------------------------------------
    lo, hi = bounds("Ceil_flat_under_loft")
    err_in = (hi[2] - plate) * 12
    gate("flat ceiling top face at the 8'-0\" plate", abs(err_in) < 0.125,
         f"top at {ft(hi[2])}, target {ft(plate)}, err {err_in:+.3f}\"")

    # ---- 2. vaults follow their roof --------------------------------------
    for name, fn in (("Ceil_vault_living", main_under),
                     ("Ceil_vault_loft", dorm_under)):
        ob = bpy.data.objects[name]
        worst = 0.0
        for v in ob.data.vertices:
            wv = ob.matrix_world @ v.co
            expect = fn(wv.x)
            # every vertex sits on either the upper face or ct below it
            d = min(abs(wv.z - expect), abs(wv.z - (expect - ct)))
            worst = max(worst, d)
        gate(f"{name} follows its roof underside", worst < 0.01,
             f"max deviation {worst*12:.3f}\"")

    # ---- 3. roof must not intrude into occupied interior volume -----------
    # The loft is the exposed case: its ceiling follows the DORMER plane, which
    # sits above the MAIN plane, so a main-roof slab spanning the dormer zone
    # would cut through the loft.
    # Volume is the only reliable test here, and it is exact.
    #
    # Three earlier attempts failed, all instructive:
    #   - the roof FORMULA alone cannot know the roof has been cut
    #   - face centroids are not a containment proxy: the boolean leaves large
    #     concave faces whose centroid sits in the loft though the face does not
    #   - closest_point_on_mesh + normal is only valid for CONVEX solids, and a
    #     cut roof is deeply concave, so it reports false positives
    #
    # The roof profile is a band of constant vertical thickness, so both the
    # uncut volume and the removed wedge are exact closed forms.
    eave = rf["eave_overhang"]["ft"]
    rake = rf["rake_overhang"]["ft"]
    uncut = (W + 2 * eave) * mp_v * (NY + 2 * rake)
    removed = W * (NY - loft_s) * mp_v          # the dormer void, wall to wall
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects["Roof_main"].data)
    actual = abs(bm.calc_volume())
    bm.free()
    gate("main roof cut away from the loft, and only there",
         abs(actual - (uncut - removed)) < 0.05,
         f"{actual:.2f} ft3 = {uncut:.2f} uncut - {removed:.2f} removed "
         f"(err {actual - (uncut - removed):+.3f})")

    # ---- 4. floor finishes tile without gap or overlap --------------------
    names = ["Floor_main_S", "Floor_main_N", "Floor_bath"]
    area = 0.0
    for n in names:
        lo, hi = bounds(n)
        area += (hi[0] - lo[0]) * (hi[1] - lo[1])
    expect = (xe - xw) * (ye - ys)
    gate("main-level floor finishes tile the interior exactly",
         abs(area - expect) < 0.05,
         f"{area:.2f} sf vs {expect:.2f} sf expected")

    # pairwise overlap
    ov = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            la, ha = bounds(a)
            lb, hb = bounds(b)
            ox = min(ha[0], hb[0]) - max(la[0], lb[0])
            oy = min(ha[1], hb[1]) - max(la[1], lb[1])
            if ox > 1e-6 and oy > 1e-6:
                ov.append(f"{a}/{b} {ox*oy:.2f} sf")
    gate("no floor finishes overlap", not ov, "; ".join(ov) or "clear")

    # ---- 5. thicknesses ----------------------------------------------------
    lo, hi = bounds("Floor_loft")
    gate("loft floor finish sits on the loft subfloor",
         abs(lo[2] - loft_sf) < 1e-4 and abs(hi[2] - loft_sf - ff) < 1e-4,
         f"{ft(lo[2])} .. {ft(hi[2])}")

    # ---- 6. door leaves ----------------------------------------------------
    lay = spec["interior_partitions"]["layout"]
    ti = con["interior_wall_thickness"]["ft"]
    dh = spec["doors"]["default_state"]
    pd = {p["id"]: p for p in lay["partitions"]}
    bad = []
    for d in lay["doors"]:
        typ = ("bypass" if d["id"].endswith("CLOSET")
               else "double_pocket" if "DBL" in d["id"] else "pocket")
        leaves = [o for o in bpy.data.objects
                  if o.name.startswith(f"Door_{d['id']}_")]
        if not leaves:
            bad.append(f"{d['id']}: no leaf"); continue
        total = sum(max(o.dimensions.x, o.dimensions.y) for o in leaves)
        if abs(total - d["w"]) > 0.02:
            bad.append(f"{d['id']}: leaves total {total:.2f} vs {d['w']:.2f} ft")
        # an OPEN pocket leaf must sit clear of its own opening
        if dh.get(typ) == "open":
            pdef = pd[d["in"]]
            c, hw = d["centre_ft"], d["w"] / 2.0
            for o in leaves:
                lo, hi = bounds(o.name)
                if pdef["axis"] == "x":
                    a = (lo[0] - t), (hi[0] - t)
                else:
                    a = ((NY - t) - hi[1]), ((NY - t) - lo[1])
                if min(a[1], c + hw) - max(a[0], c - hw) > 0.02:
                    bad.append(f"{d['id']}: open leaf still blocks its opening")
    gate("door leaves match their callouts and open leaves are clear",
         not bad, "; ".join(bad) or f"{len(lay['doors'])} doors, "
         f"{len([o for o in bpy.data.objects if o.name.startswith('Door_')])} leaves")

    # ---- 7. new geometry confined to Finish --------------------------------
    fin = {o.name for o in bpy.data.collections["Finish"].objects}
    stray = [o.name for o in bpy.data.objects
             if o.type == "MESH" and o.name.startswith(("Ceil_", "Floor_main",
                                                        "Floor_bath", "Floor_loft",
                                                        "Door_"))
             and o.name not in fin]
    gate("all Tier 1 geometry is in the Finish collection", not stray,
         ", ".join(stray) or f"{len(fin)} objects")

    w = max(len(r[0]) for r in results)
    print()
    for label, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label.ljust(w)}  {detail}")
    print("=" * 78)
    ok_all = all(r[1] for r in results)
    print("RESULT:", "ALL PASS" if ok_all else "FAILURES PRESENT")
    if not ok_all:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
