"""
render_elevations.py — orthographic elevations at true 1/4" = 1'-0".

Rendered at 200 dpi, where 1/4"=1'-0" is exactly 50.0 px/ft — the same scale the
A1.1 sheet was rasterised at in P1. That makes the output directly overlayable on
the plan elevations with no resampling.

Frame convention (see build_adu.py): east=+X, north=+Y, up=+Z.
  FRONT elevation  looks north (+Y): screen-right = +X = east, west on the left.
  REAR  elevation  looks south (-Y): screen-right = -X = west, east on the left.
Both match standard architectural convention and the A1.1 sheet.

    blender --background barn_cabin_524.blend --python render_elevations.py -- OUTDIR
"""
import sys
from pathlib import Path

import bpy
import mathutils

PX_PER_FT = 50.0
MARGIN_X = 2.0      # ft of air either side
Z_LO, Z_HI = -2.0, 19.0

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec  # noqa: E402


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
    # interior partitions are approximate and would clutter an overlay
    for c in bpy.data.collections:
        if c.name == "Interior_approx":
            for o in c.objects:
                o.hide_render = True
    return sc


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out = Path(argv[0]) if argv else HERE / "renders"
    out.mkdir(parents=True, exist_ok=True)

    spec = load_spec(HERE / "spec.yaml")
    W = spec["envelope"]["main_body_width"]["ft"]
    D = spec["envelope"]["main_body_depth"]["ft"]
    P = spec["envelope"]["porch_depth"]["ft"]
    NY, SY = P + D, P

    sc = setup_scene()
    cd = bpy.data.cameras.new("elev")
    cam = bpy.data.objects.new("elev", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.type = "ORTHO"

    # (name, camera pos, look dir, horizontal span in ft, centre of that span)
    span_x = W + 2 * MARGIN_X
    span_y = (NY) + 2 * MARGIN_X
    views = {
        "ortho_front_S": ((W / 2, -200.0, 0), (0, 1, 0), span_x, W / 2),
        "ortho_rear_N":  ((W / 2, 200.0, 0), (0, -1, 0), span_x, W / 2),
        "ortho_west_W":  ((-200.0, NY / 2, 0), (1, 0, 0), span_y, NY / 2),
        "ortho_east_E":  ((200.0, NY / 2, 0), (-1, 0, 0), span_y, NY / 2),
    }

    z_mid = (Z_LO + Z_HI) / 2.0
    res_y = int(round((Z_HI - Z_LO) * PX_PER_FT))

    manifest = []
    for name, (loc, look, span, ctr) in views.items():
        res_x = int(round(span * PX_PER_FT))
        sc.render.resolution_x, sc.render.resolution_y = res_x, res_y
        cd.ortho_scale = span if res_x >= res_y else span * res_x / res_y
        cam.location = (loc[0], loc[1], z_mid)
        cam.rotation_euler = mathutils.Vector(look).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        manifest.append((name, res_x, res_y, span, ctr))
        print(f"[render] {name}  {res_x}x{res_y}px  {span:.0f}ft wide  "
              f"{PX_PER_FT:.1f}px/ft")

    print("\nPixel mapping (top-left origin, y down):")
    print(f"  world Z = {Z_HI} - py/{PX_PER_FT}")
    print(f"  FRONT/REAR: horizontal covers {-MARGIN_X} .. {W + MARGIN_X} ft")
    print(f"  WEST/EAST : horizontal covers {-MARGIN_X} .. {NY + MARGIN_X} ft")


if __name__ == "__main__":
    main()
