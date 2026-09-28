"""
make_textures.py — Laurel's two exterior textures (#133).

    python3 models/laurel_a1_460/make_textures.py            write textures/
    python3 models/laurel_a1_460/make_textures.py --check    compare, write nothing

Run with the host Python (numpy, PIL, PyYAML), not Blender's.

The two exterior finishes A-2.0 offers, and nothing else: every other
material in the library is flat colour. Both maps are NEUTRAL, carrying light
and shade only; the colour rides on the glTF baseColorFactor, so the page's
Exterior colour set recolours a textured wall (spec.texturing).

  stucco   a sand-float plaster: layered smooth noise, no pattern, at half
           the tile's pixels. A-3.0 names 3 COAT CEMENT PLASTER and no finish
           texture, so the grain is declared, not read.
  siding   fibre-cement lap siding at spec.texturing.siding_exposure, from
           adu_kit.textures.lap_siding, the generator the barn cabin's siding
           uses.

The tile is spec.texturing.tile_size_px square and a whole number of
courses, so the siding repeats on a course line. `--check` regenerates in
memory and compares the PIXELS with what is committed, to within one level,
as make_fixtures.py compares its files, so a spec change that moves the
texture cannot ship with the old one. CI runs it.
"""
import io
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"
sys.path.insert(0, str(HERE.parents[1]))  # buyer/3D, for adu_kit
from adu_kit.textures import lap_siding, lowfreq, normal_from_height, tint  # noqa: E402


def stucco(px):
    """Sand-float plaster: two octaves of smooth, wrapping noise. A third,
    finer one was four pixels across at this size and made the normal map
    145 KB for grain nothing on the page resolves."""
    rng = np.random.default_rng(133)
    n = sum(lowfreq(px, cells, rng, amp, smooth=True)
            for cells, amp in ((12, 1.0), (42, 0.55)))
    n = (n - n.min()) / (np.ptp(n) + 1e-9)
    shade = 0.92 + 0.12 * n
    return tint(None, shade, neutral=True), normal_from_height(n, 1.4)


def render(spec):
    """{file name: PNG bytes}, built in memory."""
    tx = spec["texturing"]
    px = tx["tile_size_px"]["value"]
    dens = tx["texel_density_px_per_ft"]["value"]
    exposure = tx["siding_exposure"]["ft"]
    course = exposure * dens
    if abs(course - round(course)) > 0.01 or px % round(course):   # feet are written to 4 places
        raise SystemExit(f"a {exposure} ft course is {course:.3f} px at {dens} px/ft, and the "
                         f"{px} px tile must be a whole number of whole-pixel courses")
    lib = spec["materials"]["library"]
    made = {}
    # STUCCO AT HALF RESOLUTION, over the same tile. It has no course line to
    # keep crisp, and noise is what PNG compresses worst: at full size its two
    # maps were 277 KB, over half of lod1's budget, for grain nobody can see.
    for name, (albedo, normal) in (("stucco", stucco(px // 2)),
                                   ("siding", lap_siding(px, dens, exposure,
                                                         lib["siding"]["base_color_linear"]))):
        maps = lib[name]["maps"]
        for key, arr in (("base_color", albedo), ("normal", normal)):
            buf = io.BytesIO()
            Image.fromarray(arr).save(buf, format="PNG")
            made[maps[key]] = buf.getvalue()
    return made


# PIXELS, NOT BYTES. A PNG's bytes depend on the zlib that compressed it, and
# CI's Linux and a Mac need not agree; and linear_to_srgb's pow() comes from
# each platform's maths library, which can round one level differently. A
# texture that is actually stale -- a changed exposure, a new tile -- differs
# by far more than one level in far more than a few pixels.
PIXEL_TOL = 1


def _same_pixels(path, png):
    if not path.is_file():
        return False
    have = np.asarray(Image.open(path)).astype(np.int16)
    want = np.asarray(Image.open(io.BytesIO(png))).astype(np.int16)
    return have.shape == want.shape and int(np.abs(have - want).max()) <= PIXEL_TOL


def main(argv):
    spec = yaml.safe_load((HERE / "spec.yaml").read_text())
    made = render(spec)
    if "--check" in argv:
        stale = [n for n, b in made.items() if not _same_pixels(OUT / n, b)]
        if stale:
            print(f"FAIL  textures differ from what make_textures.py generates: {stale}")
            return 1
        print(f"PASS  {len(made)} texture(s) match make_textures.py")
        return 0
    OUT.mkdir(exist_ok=True)
    for name, b in made.items():
        (OUT / name).write_bytes(b)
        print(f"  {name:22} {len(b) / 1024:7.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
