"""
adu_kit/export.py — glTF export: feet to metres, the Draco-compressed .glb
writer, and a reader for a .glb's JSON chunk. Blender only.

MOVED, NOT CHANGED (#126), from models/barn_cabin_524/finish_adu.py. A scene
is authored at 1 Blender unit = 1 foot; the export is in metres, as glTF
requires. What a model exports, and the gates on it, stay with the model.
"""
import json
import struct

import bpy

FOOT_M = 0.3048


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
    sided = [(m.get("name", f"<{i}>"), bool(m.get("doubleSided")))
             for i, m in enumerate(js.get("materials", []))]
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
        sided=sided,
        size_kb=len(raw) / 1024.0,
        meshes=len(js.get("meshes", [])),
        materials=len(js.get("materials", [])),
        extensions=js.get("extensionsUsed", []),
        bbox=[round(hi[i] - lo[i], 3) for i in range(3)],
    )


# ---------------------------------------------------------------------------
