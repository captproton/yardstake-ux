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
    # Measure the REAL top surface, not the bounding box. A bbox cannot see a
    # hole: cutting the 24"x24" crawl opening out of Floor_main_N leaves the
    # bbox identical, so the old form of this gate would have kept reporting a
    # perfect tiling over a floor with a square missing. Rule 12 -- a gate that
    # names a container must test the extent.
    names = ["Floor_main_S", "Floor_main_N", "Floor_bath"]
    area = 0.0
    for n in names:
        ob = bpy.data.objects[n]
        for poly in ob.data.polygons:
            if poly.normal.z > 0.9 and abs((ob.matrix_world @ poly.center).z - ff) < 1e-4:
                area += poly.area
    hole = next((i for i in spec["fixtures"]["access"]["items"]
                 if i["id"] == "crawl_hole" and i.get("floor_opening")), None)
    cut = (hole["w"] * hole["d"]) if hole else 0.0
    expect = (xe - xw) * (ye - ys) - cut
    gate("main-level floor finishes tile the interior, less the crawl opening",
         abs(area - expect) < 0.05,
         f"{area:.2f} sf vs {expect:.2f} sf expected "
         f"({(xe - xw) * (ye - ys):.2f} less {cut:.2f} crawl hole)")

    # And the hatch must fill that opening exactly, or the floor has a gap.
    if hole:
        hlo, hhi = bounds("Floor_crawl_hatch")
        gate("crawl hatch fills its opening",
             abs((hhi[0] - hlo[0]) - hole["w"]) < 0.01
             and abs((hhi[1] - hlo[1]) - hole["d"]) < 0.01,
             f"{hhi[0] - hlo[0]:.3f} x {hhi[1] - hlo[1]:.3f} ft "
             f"vs {hole['w']:.3f} x {hole['d']:.3f}")

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

    # ---- 7. reveals tagged for the trim material ---------------------------
    # A door with sill 0 has no sill reveal, so it contributes 3 faces, not 4.
    op = spec["openings"]["main_floor"]
    want = {}
    for wall, key in (("Wall_N", "north_wall"), ("Wall_S", "south_wall"),
                      ("Wall_W", "west_wall"), ("Wall_E", "east_wall")):
        want[wall] = sum(3 if o["sill"] <= 1e-6 else 4
                         for o in op[key]["openings"])
    nloft = len(spec["openings"]["loft"]["windows"]) * 4
    want["Dormer_face_W"] = want["Dormer_face_E"] = nloft
    wrong = []
    for n, k in want.items():
        got = sum(1 for p in bpy.data.objects[n].data.polygons
                  if p.material_index == 1)
        if got != k:
            wrong.append(f"{n} {got} vs {k}")
    gate("window/door reveals tagged for trim, not siding", not wrong,
         "; ".join(wrong) or f"{sum(want.values())} reveal faces across 6 walls")

    # ---- 8. ladder and guardrail -------------------------------------------
    la = spec["loft_access"]["ladder"]
    lo, hi = bounds("Ladder_loft")
    rise = hi[2] - lo[2]
    run = hi[1] - lo[1]
    ang = math.degrees(math.atan(run / rise)) if rise else 0.0
    want_ang = la["heel_cut_deg"]["value"]
    gate("ladder stands at the 20 degree heel cut", abs(ang - want_ang) < 0.6,
         f"{ang:.2f} deg vs {want_ang} deg")
    gate("ladder reaches the loft subfloor", abs(hi[2] - loft_sf) < 0.05,
         f"top at {ft(hi[2])}, loft subfloor {ft(loft_sf)}")
    gh = spec["loft_access"]["guardrail"]["height"]["ft"]
    lo, hi = bounds("Rail_loft")
    gate("guardrail reaches its stated height", abs((hi[2] - loft_sf) - gh) < 0.02,
         f"{ft(hi[2] - loft_sf)} above the loft floor (stated {ft(gh)}, ASSUMED)")

    # ---- 9. mesh budget ----------------------------------------------------
    nm = len([o for o in bpy.data.objects if o.type == "MESH"])
    gate("lod0 mesh count within budget", nm <= 120, f"{nm} meshes, cap 120")

    # ---- 10. new geometry confined to Finish -------------------------------
    fin = {o.name for o in bpy.data.collections["Finish"].objects}
    stray = [o.name for o in bpy.data.objects
             if o.type == "MESH" and o.name.startswith(("Ceil_", "Floor_main",
                                                        "Floor_bath", "Floor_loft",
                                                        "Door_", "Trim_", "Ladder_",
                                                        "Rail_", "Hdw_"))
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
