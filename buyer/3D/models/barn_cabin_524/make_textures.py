"""
make_textures.py — generate the tileable exterior textures.

Procedural rather than photographic, for the reasons in TIER-2 §4: these are
regular patterns, they tile perfectly, they carry no licensing risk, and the
scale can be dialled to match spec.texturing exactly.

Base colours come from spec.materials.library, so the hue sampled from the
video in P4 carries through rather than being re-invented here.

    python3 make_textures.py            # writes textures/*.png

Run with the host Python (needs numpy, PIL, pyyaml), not Blender's.
"""
import numpy as np
import yaml
from PIL import Image
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def normal_from_height(h, strength=2.0):
    """Tileable normal map from a height field, via wrapped gradients."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    n = np.dstack([-dx, -dy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def lowfreq(px, cells, rng, sigma):
    """Tileable low-frequency noise: generated small, then upsampled.

    Per-pixel noise is invisible at these contrasts and destroys PNG
    compression — it cost ~2.4 MB across three maps for nothing you can see.
    """
    small = rng.normal(0, sigma, (cells, cells))
    idx = (np.arange(px) * cells // px)
    return small[np.ix_(idx, idx)]


def save(name, arr):
    OUT.mkdir(exist_ok=True)
    Image.fromarray(arr).save(OUT / name)
    return (OUT / name).stat().st_size


def tint(base_linear, shade):
    """shade in [0,1] multiplies the linear base colour, then to sRGB bytes."""
    c = np.asarray(base_linear)[None, None, :] * shade[..., None]
    return (linear_to_srgb(c) * 255).astype(np.uint8)


def lap_siding(px, density, exposure_ft, base):
    """6" lap: each course laps the one below, so the bottom edge casts a line."""
    n = int(round(exposure_ft * density))
    y = np.arange(px)[:, None].repeat(px, 1)
    f = (y % n) / n                            # 0 at the top of a course
    shade = 0.94 + 0.10 * f                    # slightly darker under each lap
    shade[(y % n) < 2] = 0.62                  # the lap shadow line
    rng = np.random.default_rng(11)
    shade += lowfreq(px, 64, rng, 0.008)
    course = (y // n)
    shade += (rng.random(course.max() + 2)[course] - 0.5) * 0.020   # board-to-board
    h = np.clip(f, 0, 1) * 0.5
    h[(y % n) < 2] = 0.0
    return tint(base, np.clip(shade, 0, 1.3)), normal_from_height(h, 3.0)


def shingles(px, density, exposure_ft, base, min_w, max_w, seed, jitter):
    """Staggered coursed shingles — cedar on the gable, composition on the roof."""
    n = int(round(exposure_ft * density))
    rng = np.random.default_rng(seed)
    shade = np.ones((px, px)) * 0.97
    h = np.zeros((px, px))
    for row, y0 in enumerate(range(0, px, n)):
        x = -int(rng.integers(0, max_w * density))
        while x < px:
            w = int(rng.integers(min_w * density, max_w * density))
            a, b = x, min(x + w, px)
            sl = slice(max(a, 0), b)
            tone = 1.0 + rng.normal(0, jitter)
            shade[y0:y0 + n, sl] *= tone
            h[y0:y0 + n, sl] = 0.55 + rng.normal(0, 0.05)
            if a >= 0:                                   # keyway between shingles
                shade[y0:y0 + n, a:a + 2] *= 0.55
                h[y0:y0 + n, a:a + 2] = 0.0
            x += w
        shade[y0:y0 + 2, :] *= 0.60                      # course shadow
        h[y0:y0 + 2, :] = 0.0
    return tint(base, np.clip(shade, 0, 1.4)), normal_from_height(h, 2.2)


def concrete(px, base):
    rng = np.random.default_rng(5)
    n = np.zeros((px, px))
    for cells, amp in ((16, 1.0), (48, 0.5), (128, 0.25)):
        n += lowfreq(px, cells, rng, amp)
    n = (n - n.min()) / (np.ptp(n) + 1e-9)
    shade = 0.90 + 0.18 * n
    rough = (200 + 40 * n).astype(np.uint8)
    return tint(base, shade), np.dstack([rough] * 3)


def oak_floor(px, density, base, plank_in=5.0, seed=21):
    """Strip flooring: planks of one width, random lengths, longitudinal grain."""
    w = int(round(plank_in / 12 * density))
    rng = np.random.default_rng(seed)
    shade = np.ones((px, px))
    h = np.zeros((px, px))
    for col, x0 in enumerate(range(0, px, w)):
        y = -int(rng.integers(0, 4 * density))
        board_tone = 1.0 + rng.normal(0, 0.045)
        while y < px:
            ln = int(rng.integers(2 * density, 6 * density))
            a, b = max(y, 0), min(y + ln, px)
            if b > a:
                shade[a:b, x0:x0 + w] = board_tone * (1.0 + rng.normal(0, 0.025))
                h[a:b, x0:x0 + w] = 0.5
                if y >= 0:                                  # butt joint
                    shade[a:a + 2, x0:x0 + w] *= 0.45
                    h[a:a + 2, x0:x0 + w] = 0.0
            y += ln
        shade[:, x0:x0 + 2] *= 0.45                         # plank seam
        h[:, x0:x0 + 2] = 0.0
    grain = lowfreq(px, 96, rng, 0.030) + lowfreq(px, 192, rng, 0.018)
    shade += grain
    return tint(base, np.clip(shade, 0, 1.4)), normal_from_height(h, 1.6)


def slate(px, density, base, tile_in=12.0, seed=31):
    """Cleft slate: square tiles, strong tile-to-tile tone, narrow joints."""
    n = int(round(tile_in / 12 * density))
    rng = np.random.default_rng(seed)
    shade = np.ones((px, px))
    h = np.zeros((px, px))
    for y0 in range(0, px, n):
        for x0 in range(0, px, n):
            shade[y0:y0 + n, x0:x0 + n] = 1.0 + rng.normal(0, 0.16)
            h[y0:y0 + n, x0:x0 + n] = 0.5
        shade[y0:y0 + 2, :] *= 0.5
        h[y0:y0 + 2, :] = 0.0
    for x0 in range(0, px, n):
        shade[:, x0:x0 + 2] *= 0.5
        h[:, x0:x0 + 2] = 0.0
    shade += lowfreq(px, 128, rng, 0.05)                    # cleft mottling
    return tint(base, np.clip(shade, 0, 1.6)), normal_from_height(h, 1.4)


# Painted gypsum gets NO maps. A normal map for orange-peel cost 1.36 MB and
# is invisible at any distance this model is viewed from; flat colour is
# genuinely correct here, as TIER-2 §4 already said for trim.


def carpet(px, base, seed=51):
    """Cut pile: tonal grain over slow variation. Albedo only — pile relief is
    not readable at the distance a loft carpet is ever seen from."""
    rng = np.random.default_rng(seed)
    fine = lowfreq(px, 160, rng, 0.055)
    slow = lowfreq(px, 24, rng, 0.030)
    return tint(base, np.clip(1.0 + fine + slow, 0, 1.4))


def main():
    spec = yaml.safe_load((HERE / "spec.yaml").read_text())
    tx = spec["texturing"]
    px = tx["tile_size_px"]
    dens = tx["texel_density_px_per_ft"]
    lib = spec["materials"]["library"]

    made = []
    a, nrm = lap_siding(px, dens, 0.5, lib["siding"]["base_color_linear"])
    made += [("siding_albedo.png", a), ("siding_normal.png", nrm)]

    a, nrm = shingles(px, dens, 5.0 / 12, lib["shingle_gable"]["base_color_linear"],
                      0.35, 0.85, 3, 0.045)
    made += [("shingle_albedo.png", a), ("shingle_normal.png", nrm)]

    a, nrm = shingles(px, dens, 5.0 / 12, lib["roof"]["base_color_linear"],
                      0.85, 1.15, 7, 0.075)
    made += [("roof_albedo.png", a), ("roof_normal.png", nrm)]

    a, r = concrete(px, lib["concrete"]["base_color_linear"])
    made += [("concrete_albedo.png", a), ("concrete_roughness.png", r)]

    # --- interior ---------------------------------------------------------
    a, nrm = oak_floor(px, dens, lib["floor_oak"]["base_color_linear"])
    made += [("oak_albedo.png", a), ("oak_normal.png", nrm)]

    a, nrm = slate(px, dens, lib["slate_bath"]["base_color_linear"])
    made += [("slate_albedo.png", a), ("slate_normal.png", nrm)]

    made += [("carpet_albedo.png", carpet(px, lib["carpet_loft"]["base_color_linear"]))]

    print(f"{'file':28} {'KB':>8}   {px}px tile = {px/dens:.0f} ft at {dens} px/ft")
    print("-" * 62)
    total = 0
    for name, arr in made:
        n = save(name, arr)
        total += n
        print(f"  {name:26} {n/1024:8.1f}")
    print("-" * 62)
    print(f"  {'total':26} {total/1024:8.1f} KB uncompressed PNG")
    print(f"\n  lap exposure  {0.5*dens:.0f} px  (6\")")
    print(f"  shingle course {5/12*dens:.0f} px  (5\")")


if __name__ == "__main__":
    main()
