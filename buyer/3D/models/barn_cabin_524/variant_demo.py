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

# Two scenes, because the manifest now drives finishes in two places. Ids only
# — every VALUE comes from the manifest, so this cannot drift from the spec, and
# a typo fails loudly in `apply()`.
#
# `patches` are image regions to measure, keyed by what they should show. Each
# scene asserts two things: that its own set moves (separation), and that a set
# does NOT move anything it does not target (isolation). The isolation half
# matters — it is what proves a swap is addressing the material it claims to.
SCENES = {
    "exterior": {
        "out": "variants.png",
        "cam": ((-12 * FT, -14 * FT, 6.5 * FT), (11 * FT, 15 * FT, 4.5 * FT), 42),
        "hide": (),
        "res": (1000, 700),
        "demos": [
            ("variant_sandstone", {"color_theme": "sandstone", "roof_colour": "weathered",
                                   "trim_colour": "white"}),
            ("variant_sage",      {"color_theme": "sage",      "roof_colour": "charcoal",
                                   "trim_colour": "white"}),
            ("variant_charcoal",  {"color_theme": "charcoal",  "roof_colour": "driftwood",
                                   "trim_colour": "almond"}),
        ],
        # A patch of the south wall, clear of windows, trim and the porch shadow.
        "patches": {"wall": (slice(380, 470), slice(120, 420))},
        "expect": [("wall", "variant_sandstone", "variant_charcoal", 20.0, "move")],
    },
    "interior": {
        "out": "variants_casework.png",
        # Roof and ceilings off so daylight reaches the room, as dollhouse does.
        "hide": ("Roof_", "Ceil_"),
        "cam": ((11.0 * FT, 10.5 * FT, 5.2 * FT), (0.5 * FT, 16.5 * FT, 4.0 * FT), 21),
        "res": (900, 560),
        "demos": [
            ("casework_default",  {"cabinet_finish": "natural",  "countertop": "white_granite"}),
            ("casework_tan",      {"cabinet_finish": "natural",  "countertop": "tan_granite"}),
            ("casework_espresso", {"cabinet_finish": "espresso", "countertop": "charcoal"}),
        ],
        "patches": {
            "countertop": (slice(322, 344), slice(100, 320)),
            "cabinet":    (slice(430, 520), slice(150, 380)),
        },
        "expect": [
            # countertop-only change: the counter moves, the cabinets must not.
            ("countertop", "casework_default", "casework_tan", 8.0, "move"),
            ("cabinet",    "casework_default", "casework_tan", 1.0, "hold"),
            ("cabinet",    "casework_default", "casework_espresso", 20.0, "move"),
        ],
    },
}


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


def build_scene(cfg):
    """Overcast-ish daylight. Deliberately not blown out: the first pass was lit
    hard enough that a 0.15 charcoal read as mid grey, which flatters the swap
    by hiding how dark the dark options really are."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = cfg["res"]

    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith(tuple(cfg["hide"]) or ("\0",)):
            ob.hide_render = True

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

    eye, tgt, lens = cfg["cam"]
    cd = bpy.data.cameras.new("C")
    cd.lens = lens
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = eye
    cam.rotation_euler = (mathutils.Vector(tgt)
                          - mathutils.Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    return sc


def montage(out, cfg):
    """Side-by-side, plus the measured patch colours. numpy ships with Blender;
    PIL does not, so the PNGs are read back through Blender's own image loader."""
    import numpy as np

    names = [n for n, _ in cfg["demos"]]
    strips, vals = [], {}
    for name in names:
        img = bpy.data.images.load(str(out / f"{name}.png"))
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
        rgb = np.clip(px[:, :, :3], 0, 1)
        strips.append(rgb)
        for pname, sl in cfg["patches"].items():
            vals[(pname, name)] = rgb[sl].mean(axis=(0, 1)) * 255.0
        bpy.data.images.remove(img)

    for pname in cfg["patches"]:
        for name in names:
            m = vals[(pname, name)]
            print(f"  [{pname:10s}] {name:20s} {m[0]:6.1f} {m[1]:6.1f} {m[2]:6.1f}")

    bad = []
    for pname, a, b, thresh, kind in cfg["expect"]:
        sep = float(max(abs(vals[(pname, a)] - vals[(pname, b)])))
        ok = sep >= thresh if kind == "move" else sep <= thresh
        verb = "moves" if kind == "move" else "holds"
        print(f"  [{'PASS' if ok else 'FAIL'}] {pname} {verb} between {a} and "
              f"{b}: {sep:.1f} (limit {thresh})")
        if not ok:
            bad.append(f"{pname} {a}->{b} {sep:.1f}")
    if bad:
        raise SystemExit("variant assertions failed: " + "; ".join(bad))

    joined = np.concatenate(strips, axis=1)
    h, w, _ = joined.shape
    outimg = bpy.data.images.new("v", width=w, height=h, alpha=True)
    rgba = np.concatenate([joined, np.ones((h, w, 1), np.float32)], axis=2)
    outimg.pixels = rgba[::-1].ravel()
    outimg.filepath_raw = str(out / cfg["out"])
    outimg.file_format = "PNG"
    outimg.save()
    bpy.data.images.remove(outimg)
    print(f"  [montage] {cfg['out']}  {w}x{h}")


USAGE = ("blender --background --python variant_demo.py"
         " -- MODEL.glb VARIANTS.json OUTDIR")


def main():
    # Blender swallows everything before "--", so a script run without it sees
    # the wrong argv entirely. Unchecked, that surfaced as a ValueError or an
    # IndexError from deep inside the parse — a stack trace that says nothing
    # about the actual mistake, which is simply calling it wrongly.
    if "--" not in sys.argv:
        raise SystemExit(f"missing '--' before the arguments.\nusage: {USAGE}")
    argv = sys.argv[sys.argv.index("--") + 1:]
    if len(argv) != 3:
        raise SystemExit(f"expected 3 arguments, got {len(argv)}: {argv}\n"
                         f"usage: {USAGE}")

    glb, man, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    for path, what in ((glb, "model"), (man, "manifest")):
        if not path.exists():
            raise SystemExit(f"{what} not found: {path}")
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(man.read_text())

    for scene, cfg in SCENES.items():
        print(f"\n=== {scene}")
        for name, choice in cfg["demos"]:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(glb))
            apply(manifest, choice)
            sc = build_scene(cfg)
            sc.render.filepath = str(out / f"{name}.png")
            bpy.ops.render.render(write_still=True)
            print("  rendered", name)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        montage(out, cfg)


if __name__ == "__main__":
    main()
