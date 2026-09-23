"""
render_elevations.py — orthographic elevations at true 1/4" = 1'-0" (#130).

Rendered at 100 px/ft, which is what the sheet's own 1/4" = 1'-0" comes to
when A-2.0 is rasterised at 400 dpi. That makes the output directly
overlayable on the plan elevations with no resampling, and resampling is
exactly what would let a disagreement hide. The barn cabin used 50 px/ft for
the same reason against a sheet it had rasterised at 200 dpi; Laurel's
measurements were all taken at 400, so it stays there.

    blender --background models/laurel_a1_460/laurel_a1_460.blend \\
        --python models/laurel_a1_460/render_elevations.py -- OUTDIR

Writes four PNGs and a `manifest.json` carrying the pixel-to-world mapping for
each, so the comparison step reads the mapping rather than re-deriving it. Two
files that each work out the scale for themselves are two chances to get it
wrong, and no way to notice.

THE FOUR VIEWS ARE A-2.0's FOUR, under A-2.0's names. The frame is
spec.frame: front faces +Y, X 0 is the living-room end, X 24 the kitchen and
bath end.

    FRONT        looks -Y from in front.  X increases to the viewer's LEFT,
                 which is the fact the first draft of this spec had backwards.
    REAR         looks +Y from behind.    X increases to the viewer's RIGHT.
    SIDE (RIGHT) looks +X from X below 0. The X 0 end: the two C windows,
                 with the front on the viewer's LEFT.
    SIDE (LEFT)  looks -X from beyond X 24. The kitchen and bath end: windows
                 D and E, with the front on the viewer's RIGHT.

Those handednesses are not decoration. They are what `frame.evidence` cites
from the sheets, and getting one backwards would make a mirrored model look
like a matching one.

WHAT IT RENDERS, AND WHAT IT LEAVES OUT. Shell, roof and openings: what an
elevation draws. The slab and the partitions are hidden -- the slab is a band
below F.F. that A-2.0 does not draw as solid, and the partitions are interior
and can only add noise to a silhouette they cannot legitimately change.
"""
import json
import sys
from pathlib import Path

import bpy
import mathutils
import numpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build import load_spec  # noqa: E402

# Framing bookkeeping, not building dimensions.
PX_PER_FT = 100.0
MARGIN_FT = 2.0          # air around the model, so nothing touches an edge
FAR_FT = 200.0           # how far back the ortho camera stands; ortho makes it arbitrary
Z_LO, Z_HI = -1.0, 12.0  # below grade to above the roof
HIDE = ("Partitions", "Site")


def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sh = sc.display.shading
    sh.light = "FLAT"
    sh.color_type = "SINGLE"
    sh.single_color = (0.1, 0.1, 0.1)
    sh.show_object_outline = False
    for name in HIDE:
        coll = bpy.data.collections.get(name)
        if coll:
            for ob in coll.objects:
                ob.hide_render = True
    return sc


def ink_width_ft(path):
    """How far across the image the opaque pixels reach, in feet."""
    img = bpy.data.images.load(str(path), check_existing=False)
    try:
        w, h = img.size
        px = numpy.empty(w * h * 4, dtype=numpy.float32)
        img.pixels.foreach_get(px)
    finally:
        bpy.data.images.remove(img)
    cols = numpy.flatnonzero((px[3::4].reshape(h, w) > 0.5).any(axis=0))
    return 0.0 if cols.size == 0 else (cols[-1] - cols[0] + 1) / PX_PER_FT


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[0]) if argv else HERE / "renders"
    out.mkdir(parents=True, exist_ok=True)

    spec = load_spec(HERE / "spec.yaml")
    W = spec["envelope"]["width"]["ft"]
    D = spec["envelope"]["depth"]["ft"]
    ov = spec["roof"]["overhangs"]

    # The horizontal span each view must cover: the building plus whatever the
    # roof reaches past it on that axis, plus air.
    x_lo, x_hi = -ov["ends"]["ft"] - MARGIN_FT, W + ov["ends"]["ft"] + MARGIN_FT
    y_lo, y_hi = -ov["rear"]["ft"] - MARGIN_FT, D + ov["front"]["ft"] + MARGIN_FT

    sc = setup_scene()
    cd = bpy.data.cameras.new("elev")
    cam = bpy.data.objects.new("elev", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.type = "ORTHO"

    # name -> (look direction, the world axis running across the image,
    #          whether that axis increases to the RIGHT in the image,
    #          the span it covers)
    views = {
        "front":      ((0, -1, 0), "x", False, (x_lo, x_hi)),
        "rear":       ((0, 1, 0), "x", True, (x_lo, x_hi)),
        "side_right": ((1, 0, 0), "y", False, (y_lo, y_hi)),
        "side_left":  ((-1, 0, 0), "y", True, (y_lo, y_hi)),
    }

    z_mid = (Z_LO + Z_HI) / 2.0
    model_centre = ((x_lo + x_hi) / 2.0, (y_lo + y_hi) / 2.0, z_mid)
    res_y = int(round((Z_HI - Z_LO) * PX_PER_FT))
    manifest = {"px_per_ft": PX_PER_FT, "z_hi": Z_HI, "z_lo": Z_LO, "views": {}}
    short = []

    for name, (look, axis, rightwards, (lo, hi)) in views.items():
        span = hi - lo
        res_x = int(round(span * PX_PER_FT))
        sc.render.resolution_x, sc.render.resolution_y = res_x, res_y
        # ortho_scale sets the LONGER edge, so it only equals the horizontal
        # span while the image is at least as wide as it is tall.
        cd.ortho_scale = span if res_x >= res_y else span * res_x / res_y
        ctr = (lo + hi) / 2.0
        # STAND BEHIND THE MODEL AND LOOK THROUGH IT. Deriving the position
        # from the look direction is the whole trick: the first version chose
        # it with a chain of conditionals and got the two Y views backwards,
        # putting the camera in FRONT of the building while pointing it away.
        # Those renders came out empty and the script printed four cheerful
        # lines anyway. ink_width_ft() below is what now notices.
        eye = mathutils.Vector(model_centre) - mathutils.Vector(look) * FAR_FT
        cam.location = (eye.x, eye.y, z_mid)
        if axis == "x":
            cam.location = (ctr, eye.y, z_mid)
        else:
            cam.location = (eye.x, ctr, z_mid)
        cam.rotation_euler = mathutils.Vector(look).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(out / f"ortho_{name}.png")
        bpy.ops.render.render(write_still=True)
        manifest["views"][name] = {
            "file": f"ortho_{name}.png", "axis": axis,
            "axis_increases_right": rightwards,
            "axis_lo": lo, "axis_hi": hi,
            "res_x": res_x, "res_y": res_y,
        }
        # The EXTENT, not "any ink": a view that caught a sliver of the building
        # would pass a non-empty check. The ink must span at least the wall it
        # faces, face of stud to face of stud; overhangs only add to that.
        ink = ink_width_ft(out / f"ortho_{name}.png")
        wall = W if axis == "x" else D
        ok = ink >= wall
        print(f"[render] {name:11s} {res_x}x{res_y}px  {axis} {lo:.2f}..{hi:.2f} ft  "
              f"{'->' if rightwards else '<-'} across the image  "
              f"ink {ink:.2f} ft vs wall {wall:.2f} ft  {'ok' if ok else 'FAIL'}")
        if not ok:
            short.append(f"{name}: ink spans {ink:.2f} ft, the wall it faces is {wall:.2f} ft")

    if short:
        print("\nRENDER FAILED -- no manifest written:\n  " + "\n  ".join(short))
        sys.exit(1)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nwrote {out / 'manifest.json'}")
    print("pixel mapping, top-left origin, y down:")
    print(f"  world Z    = {Z_HI} - py / {PX_PER_FT}")
    print(f"  world axis = lo + px / {PX_PER_FT}   (or hi - px/... where it runs leftwards)")


if __name__ == "__main__":
    main()
