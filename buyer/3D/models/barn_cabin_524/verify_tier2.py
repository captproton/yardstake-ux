"""
verify_tier2.py — gates for Tier 2: UVs, texel density and texture budget.

The texel density gate is the one that matters. Without it, hand-authored or
drifting UVs make the siding scale jump visibly between walls, and nobody
notices until the textures are on.

    blender --background barn_cabin_524.blend --python verify_tier2.py
"""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec  # noqa: E402


def main():
    spec = load_spec(HERE / "spec.yaml")
    tx = spec["texturing"]
    tile_px = tx["tile_size_px"]
    target = tx["texel_density_px_per_ft"]
    tol = tx["tolerance_pct"] / 100.0

    results = []

    def gate(label, ok, detail=""):
        results.append((label, ok, detail))

    print("\n" + "=" * 80)
    print("TIER 2 VERIFICATION — UVs and texel density")
    print("=" * 80)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    no_uv = [o.name for o in meshes if not o.data.uv_layers]
    gate("every mesh carries a UV layer", not no_uv,
         ", ".join(no_uv) or f"{len(meshes)} meshes")

    # per-edge texel density
    n = ok = 0
    worst = ("", 0.0, 0.0)
    per_obj = {}
    for o in meshes:
        if not o.data.uv_layers:
            continue
        me = o.data
        uv = me.uv_layers.active.data
        M = o.matrix_world
        o_worst = 0.0
        for p in me.polygons:
            li = list(p.loop_indices)
            for a, b in zip(li, li[1:] + li[:1]):
                wa = M @ me.vertices[me.loops[a].vertex_index].co
                wb = M @ me.vertices[me.loops[b].vertex_index].co
                wl = (wb - wa).length
                if wl < 1e-4:
                    continue
                dens = (uv[b].uv - uv[a].uv).length * tile_px / wl
                err = abs(dens - target) / target
                n += 1
                if err <= tol:
                    ok += 1
                if err > worst[1]:
                    worst = (o.name, err, dens)
                o_worst = max(o_worst, err)
        per_obj[o.name] = o_worst

    gate(f"texel density within +/-{tx['tolerance_pct']}% of {target} px/ft",
         ok == n,
         f"{ok}/{n} edges; worst {worst[0]} at {worst[2]:.1f} px/ft "
         f"({worst[1]*100:.1f}% off)")

    offenders = sorted(((v, k) for k, v in per_obj.items() if v > tol),
                       reverse=True)[:6]
    if offenders:
        print("\n  objects outside tolerance:")
        for v, k in offenders:
            print(f"    {k:24} {v*100:6.1f}% off")

    # reveals must reach slot 1 — materials.clear() once wiped this silently
    want = {}
    op = spec["openings"]["main_floor"]
    for wall, key in (("Wall_N", "north_wall"), ("Wall_S", "south_wall"),
                      ("Wall_W", "west_wall"), ("Wall_E", "east_wall")):
        want[wall] = len(op[key]["openings"])
    want["Dormer_face_W"] = want["Dormer_face_E"] = len(
        spec["openings"]["loft"]["windows"])
    bad = []
    for n, k in want.items():
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        tagged = sum(1 for p in ob.data.polygons if p.material_index == 1)
        if (k > 0) != (tagged > 0):
            bad.append(f"{n}: {tagged} tagged faces for {k} openings")
    gate("reveal faces still carry material slot 1", not bad,
         "; ".join(bad) or "reveals tagged on every wall that has openings")

    # tile coverage: a tile spans tile_px / density feet
    tile_ft = tile_px / target
    gate("tile size is sane for the longest wall", tile_ft >= 4.0,
         f"one {tile_px}px tile covers {tile_ft:.1f} ft")

    w = max(len(r[0]) for r in results)
    print()
    for label, good, detail in results:
        print(f"  [{'PASS' if good else 'FAIL'}] {label.ljust(w)}  {detail}")
    print("=" * 80)
    all_ok = all(r[1] for r in results)
    print("RESULT:", "ALL PASS" if all_ok else "FAILURES PRESENT")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
