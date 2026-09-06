"""
finish_adu.py — P4. Materials, glazing, LODs, Draco-compressed glTF.

Builds the model from spec.yaml via build_adu.build(), applies the material
library and assignment map from spec.yaml (no colours hardcoded here), fills the
openings with glazing and door panels, then exports three LOD levels as .glb
with Draco mesh compression for the Three.js track.

    blender --background --python finish_adu.py -- [--out DIR]

Scene is authored at 1 Blender unit = 1 foot. scale_length is set to 0.3048 so
the glTF exporter writes metres, per glTF convention.
"""
import sys
import json
import struct
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec, build, box, collection, ft  # noqa: E402

FOOT_M = 0.3048


# ---------------------------------------------------------------------------
def make_materials(spec, textured=True):
    lib = spec["materials"]["library"]
    tdir = HERE / spec.get("textures", {}).get("dir", "textures/")
    out = {}
    for name, m in lib.items():
        mat = bpy.data.materials.new(f"adu_{name}")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        r, g, b = m["base_color_linear"]
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)

        # Textures, where the spec declares them. A base-colour map carries the
        # colour itself, so the factor is left white and not double-tinted.
        maps = (m.get("maps") or {}) if textured else {}
        for slot, fname in maps.items():
            path = tdir / fname
            if not path.exists():
                raise SystemExit(f"[tex] missing {path}")
            img = bpy.data.images.load(str(path), check_existing=True)
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            tex.location = (-600, {"base_color": 300, "normal": -300,
                                   "roughness": 0}.get(slot, 0))
            if slot == "base_color":
                img.colorspace_settings.name = "sRGB"
                nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
                bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
            elif slot == "normal":
                img.colorspace_settings.name = "Non-Color"
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.location = (-300, -300)
                nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
            elif slot == "roughness":
                img.colorspace_settings.name = "Non-Color"
                nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])
        bsdf.inputs["Roughness"].default_value = m.get("roughness", 0.8)
        bsdf.inputs["Metallic"].default_value = m.get("metallic", 0.0)
        if m.get("transmission"):
            for key in ("Transmission Weight", "Transmission"):
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = m["transmission"]
                    break
            mat.blend_method = "BLEND"
        out[name] = mat
    return out


def assign(spec, mats):
    """Apply spec.materials.assignment by object-name prefix. First match wins."""
    rules = list(spec["materials"]["assignment"].items())
    unmatched = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for prefix, mname in rules:
            if ob.name.startswith(prefix):
                # materials.clear() RESETS every polygon's material_index to 0,
                # which silently discarded the reveal tagging from
                # build_adu.mark_reveals(). Capture the indices first and put
                # them back once both slots exist.
                tagged = [i for i, poly in enumerate(ob.data.polygons)
                          if poly.material_index == 1]
                ob.data.materials.clear()
                ob.data.materials.append(mats[mname])
                if tagged:
                    ob.data.materials.append(mats["trim"])
                    for i in tagged:
                        ob.data.polygons[i].material_index = 1
                break
        else:
            unmatched.append(ob.name)
    return unmatched


# ---------------------------------------------------------------------------
def add_glazing(spec, geo, coll):
    """A thin slab in each opening: glass for windows, a trim panel for doors."""
    t, W = geo["t"], geo["W"]
    NY, SY = geo["NY"], geo["SY"]
    loft_sf = spec["levels"]["loft_top_of_subfloor"]["ft"]
    dsill = loft_sf + spec["construction"]["dormer_window_sill_above_loft_floor"]["ft"]
    op = spec["openings"]["main_floor"]
    d = 0.04                      # pane thickness, ft
    made = []

    def pane(name, x0, x1, y0, y1, z0, z1):
        made.append(box(name, x0, x1, y0, y1, z0, z1, coll))

    def yn(v):
        return NY - v

    for o in op["north_wall"]["openings"]:
        c = NY - t / 2
        pane(f"Glazing_{o['id']}", o["offset"], o["offset"] + o["w"],
             c - d / 2, c + d / 2, o["sill"], o["sill"] + o["h"])
    for o in op["south_wall"]["openings"]:
        c = SY + t / 2
        nm = ("Door_" if o["type"].endswith("door") else "Glazing_") + o["id"]
        pane(nm, o["offset"], o["offset"] + o["w"],
             c - d / 2, c + d / 2, o["sill"], o["sill"] + o["h"])
    for o in op["west_wall"]["openings"]:
        c = t / 2
        pane(f"Glazing_{o['id']}", c - d / 2, c + d / 2,
             yn(o["offset"] + o["w"]), yn(o["offset"]),
             o["sill"], o["sill"] + o["h"])
    for o in spec["openings"]["loft"]["windows"]:
        for side, c in (("W", t / 2), ("E", W - t / 2)):
            pane(f"Glazing_{o['id']}_{side}", c - d / 2, c + d / 2,
                 yn(o["offset"] + o["w"]), yn(o["offset"]),
                 dsill, dsill + o["h"])
    return made


# ---------------------------------------------------------------------------
def to_metres(objects):
    """The glTF exporter writes raw Blender units as metres and ignores
    scene.unit_settings.scale_length, so convert the mesh data explicitly.
    The scene is authored at 1 unit = 1 foot."""
    done = set()
    for ob in objects:
        if ob.data.name in done:
            continue
        done.add(ob.data.name)
        for v in ob.data.vertices:
            v.co *= FOOT_M


def export_glb(path, objects, draco=True):
    to_metres(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    kw = dict(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_materials="EXPORT",
    )
    if draco:
        kw.update(
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=6,
            export_draco_position_quantization=14,
            export_draco_normal_quantization=10,
        )
    bpy.ops.export_scene.gltf(**kw)


def glb_info(path):
    """Read a GLB's JSON chunk: extension use, mesh/accessor counts, bbox."""
    raw = path.read_bytes()
    assert raw[:4] == b"glTF", "not a GLB"
    off, n = 12, len(raw)
    js = None
    while off < n:
        clen, ctype = struct.unpack_from("<II", raw, off)
        if ctype == 0x4E4F534A:
            js = json.loads(raw[off + 8: off + 8 + clen].decode("utf-8"))
            break
        off += 8 + clen
    # POSITION accessors only — NORMAL is also VEC3 and would inflate the bbox
    pos_idx = {prim["attributes"]["POSITION"]
               for m in js.get("meshes", []) for prim in m["primitives"]
               if "POSITION" in prim.get("attributes", {})}
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for i_a, a in enumerate(js.get("accessors", [])):
        if i_a in pos_idx and "min" in a and len(a["min"]) == 3:
            for i in range(3):
                lo[i] = min(lo[i], a["min"][i])
                hi[i] = max(hi[i], a["max"][i])
    return dict(
        size_kb=len(raw) / 1024.0,
        meshes=len(js.get("meshes", [])),
        materials=len(js.get("materials", [])),
        extensions=js.get("extensionsUsed", []),
        bbox=[round(hi[i] - lo[i], 3) for i in range(3)],
    )


# ---------------------------------------------------------------------------
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else HERE / "export"
    out.mkdir(parents=True, exist_ok=True)

    spec = load_spec(HERE / "spec.yaml")
    results = {}

    for lod in ("lod0", "lod1", "lod2"):
        geo, colls = build(spec, cut_openings=(lod != "lod2"))
        bpy.context.scene.unit_settings.scale_length = FOOT_M

        tex_cfg = spec.get("textures", {})
        textured = lod not in tex_cfg.get("untextured_levels", [])
        mats = make_materials(spec, textured=textured)
        glaz = colls["shell"] if lod == "lod2" else collection("Glazing")
        if lod != "lod2":
            add_glazing(spec, geo, glaz)
        unmatched = assign(spec, mats)

        keep = list(colls["shell"].objects) + list(colls["roof"].objects) \
            + list(colls["porch"].objects)
        if lod == "lod0":
            keep += list(colls["interior"].objects)
            keep += list(colls["finish"].objects)   # Tier 1: ceilings, floors, doors
        if lod != "lod2":
            keep += [o for o in glaz.objects]

        p = out / f"barn_cabin_524_{lod}.glb"
        export_glb(p, keep)
        info = glb_info(p)
        info["objects"] = len(keep)
        info["unmatched_materials"] = unmatched
        info["textured"] = textured
        results[lod] = info

    # primary deliverable is a copy of lod0
    (out / "barn_cabin_524.glb").write_bytes((out / "barn_cabin_524_lod0.glb").read_bytes())

    print("\n" + "=" * 76)
    print("P4 EXPORT REPORT")
    print("=" * 76)
    print(f"{'level':7} {'objects':>8} {'meshes':>7} {'mats':>5} {'size KB':>9}  "
          f"{'bbox (m)':>22}  draco")
    print("-" * 76)
    ok = True
    for lod, i in results.items():
        draco = "KHR_draco_mesh_compression" in i["extensions"]
        ok &= draco
        bb = "x".join(f"{v:.2f}" for v in i["bbox"])
        print(f"{lod:7} {i['objects']:>8} {i['meshes']:>7} {i['materials']:>5} "
              f"{i['size_kb']:>9.1f}  {bb:>22}  {'yes' if draco else 'NO'}"
              f"  {'tex' if i['textured'] else 'flat'}")
        if i["unmatched_materials"]:
            print(f"        unmatched: {i['unmatched_materials']}")
            ok = False

    budget = spec.get("textures", {}).get("budget_kb", {})
    over = [f"{k} {results[k]['size_kb']:.0f} KB > {v} KB"
            for k, v in budget.items() if results[k]["size_kb"] > v]
    print("-" * 76)
    for k, v in budget.items():
        print(f"  budget {k}: {results[k]['size_kb']:8.1f} KB / {v:5d} KB ceiling"
              f"   {'OK' if results[k]['size_kb'] <= v else 'OVER'}")
    ok &= not over

    W = spec["envelope"]["main_body_width"]["ft"]
    exp_x = (W + 2 * spec["roof"]["eave_overhang"]["ft"]) * FOOT_M
    got_x = results["lod0"]["bbox"][0]
    print("-" * 76)
    print(f"expected X span (22'-0\" + 2 x 18\" eave) = {exp_x:.3f} m   got {got_x:.3f} m")
    scale_ok = abs(got_x - exp_x) < 0.01
    print(f"\n  [{'PASS' if not over else 'FAIL'}] every level within its size budget")
    print(f"  [{'PASS' if scale_ok else 'FAIL'}] glTF exported in metres at the right scale")
    print(f"  [{'PASS' if ok else 'FAIL'}] Draco applied and every object matched a material")
    print("=" * 76)
    if not (ok and scale_ok):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
