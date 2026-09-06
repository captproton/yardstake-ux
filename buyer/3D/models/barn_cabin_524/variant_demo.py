"""
variant_demo.py — prove export/variants.json actually drives the model.

The configurator manifest is only useful if applying it changes what a viewer
renders. `finish_adu.py` gates that the manifest's targets *name real
materials*; this proves the swap *does something*, by re-importing the exported
`.glb` and applying three themes exactly as the Three.js runtime will —
baseColorFactor by material name, nothing else touched.

That distinction earned itself. The first run of this script produced three
byte-different but visually identical images, because the swap was looking for
the wrong node type and silently failing. A gate on names alone would have
passed.

    blender --background --python variant_demo.py -- MODEL.glb VARIANTS.json OUTDIR

Writes one PNG per theme plus a side-by-side `variants.png`, and prints the
mean wall colour of each so the difference is a number, not an impression.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import mathutils

FT = 0.3048

# Which themes to render. Ids only — every value comes from the manifest, so
# this cannot drift from the spec. A typo fails loudly in `apply()`.
DEMOS = [
    ("variant_sandstone", {"color_theme": "sandstone", "roof_colour": "weathered",
                           "trim_colour": "white"}),
    ("variant_sage",      {"color_theme": "sage",      "roof_colour": "charcoal",
                           "trim_colour": "white"}),
    ("variant_charcoal",  {"color_theme": "charcoal",  "roof_colour": "driftwood",
                           "trim_colour": "almond"}),
]

# A patch of the south wall, well clear of windows, trim and the porch shadow.
WALL_PATCH = (slice(380, 470), slice(120, 420))


def set_base_color(mat, rgba):
    """Set a material's baseColorFactor, whichever way the importer expressed it.

    Blender's glTF importer has two representations. With a texture it inserts
    a MULTIPLY node between the image and Base Color and puts the factor in
    that node's B socket; without one, the factor is Base Color's own default.
    So assigning Base Color unconditionally is a silent no-op in the textured
    case, because the socket is already linked — which is precisely what made
    three colour themes render identically the first time round.

    Two further traps: the node is type 'MIX' in Blender 4.x, not the 'MIX_RGB'
    that older code looks for; and 'A'/'B' each appear on it once per data
    type, so the RGBA pair has to be picked out by socket type rather than by
    name alone.
    """
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        return False
    sock = bsdf.inputs["Base Color"]
    if not sock.is_linked:
        sock.default_value = rgba
        return True
    src = sock.links[0].from_node
    if src.type in ("MIX", "MIX_RGB"):
        for i in src.inputs:
            if i.name in ("B", "Color2") and i.type == "RGBA" and not i.is_linked:
                i.default_value = rgba
                return True
    return False


def apply(manifest, choice):
    """Exactly what the Three.js runtime does: baseColorFactor, by material name."""
    for st in manifest["sets"]:
        pick = choice.get(st["id"])
        if pick is None:
            continue
        opt = next((o for o in st["options"] if o["id"] == pick), None)
        if opt is None:
            raise SystemExit(f"no option {pick!r} in set {st['id']!r}")
        for tname in st["targets"]:
            mat = bpy.data.materials.get(tname)
            if mat is None:
                raise SystemExit(f"manifest target {tname!r} is not in the glb")
            if not set_base_color(mat, opt["value"]):
                raise SystemExit(f"could not set base colour on {tname!r}")
            print(f"   {st['id']}={pick} -> {tname}")


def build_scene():
    """Overcast-ish daylight. Deliberately not blown out: the first pass was lit
    hard enough that a 0.15 charcoal read as mid grey, which flatters the swap
    by hiding how dark the dark options really are."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1000, 700

    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.60, 0.68, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sc.world = w

    sd = bpy.data.lights.new("S", "SUN")
    sd.energy = 2.2
    sd.color = (1.0, 0.96, 0.90)
    so = bpy.data.objects.new("S", sd)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(215))

    cd = bpy.data.cameras.new("C")
    cd.lens = 42
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (-12 * FT, -14 * FT, 6.5 * FT)
    tgt = mathutils.Vector((11 * FT, 15 * FT, 4.5 * FT))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    return sc


def montage(out, names):
    """Side-by-side, plus the measured wall colour of each. numpy ships with
    Blender; PIL does not, so the PNGs are read back through Blender's own
    image loader."""
    import numpy as np

    strips, report = [], []
    for name in names:
        img = bpy.data.images.load(str(out / f"{name}.png"))
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        px = px[::-1]                      # Blender images are bottom-up
        rgb = np.clip(px[:, :, :3], 0, 1)
        strips.append(rgb)
        m = rgb[WALL_PATCH] .mean(axis=(0, 1)) * 255.0
        report.append((name, m))
        bpy.data.images.remove(img)

    for name, m in report:
        print(f"[wall] {name:20s} mean RGB {m[0]:6.1f} {m[1]:6.1f} {m[2]:6.1f}")
    spread = max(abs(a[1][0] - b[1][0]) for a in report for b in report)
    print(f"[wall] widest separation between themes: {spread:.1f} / 255")
    if spread < 20.0:
        raise SystemExit("themes are not visibly distinct — the swap did nothing")

    joined = np.concatenate(strips, axis=1)
    h, w, _ = joined.shape
    outimg = bpy.data.images.new("variants", width=w, height=h, alpha=True)
    rgba = np.concatenate([joined, np.ones((h, w, 1), np.float32)], axis=2)
    outimg.pixels = rgba[::-1].ravel()
    outimg.filepath_raw = str(out / "variants.png")
    outimg.file_format = "PNG"
    outimg.save()
    print(f"[montage] {out / 'variants.png'}  {w}x{h}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    glb, man, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(man.read_text())

    for name, choice in DEMOS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        apply(manifest, choice)
        sc = build_scene()
        sc.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", name)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    montage(out, [n for n, _ in DEMOS])


if __name__ == "__main__":
    main()
