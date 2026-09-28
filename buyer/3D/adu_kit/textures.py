"""
adu_kit/textures.py — tileable procedural textures that know no building.

MOVED, NOT CHANGED (#133), from models/barn_cabin_524/make_textures.py, when
Laurel became the second model to need a lap-siding texture. The barn
cabin's generated PNGs are byte-identical before and after. What stays in
each model's make_textures.py is what reads that building: which materials
get which pattern, at which exposure, and where the files go.

Procedural rather than photographic (TIER-2 §4): regular patterns, perfect
tiling, no licensing risk, and a scale set exactly from the spec.

Plain Python with numpy and PIL, run with the host Python, not Blender's.
"""
import numpy as np


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


def lowfreq(px, cells, rng, sigma, smooth=False):
    """Tileable low-frequency noise: generated small, then upsampled.

    Per-pixel noise is invisible at these contrasts and destroys PNG
    compression — it cost ~2.4 MB across three maps for nothing you can see.

    `smooth` picks bilinear over nearest-neighbour upsampling. Nearest leaves
    hard-edged cells — at 24 cells on a 1024 tile that is a 42 px block — which
    the siding, shingle, oak and slate generators get away with because a lap
    line or a plank seam sits on top and dominates. A generator whose ONLY
    content is this noise does not get away with it: the first cabinet-wood
    texture read as brickwork. Both paths wrap, so the tile still tiles.

    The older generators deliberately keep nearest. Switching them would churn
    every shipped texture and every exported byte for a difference nothing in
    those maps would show.
    """
    small = rng.normal(0, sigma, (cells, cells))
    if not smooth:
        idx = (np.arange(px) * cells // px)
        return small[np.ix_(idx, idx)]
    t = np.arange(px) * cells / px
    i0 = np.floor(t).astype(int) % cells
    i1 = (i0 + 1) % cells
    f = (t - np.floor(t))
    rows = small[i0] * (1 - f)[:, None] + small[i1] * f[:, None]
    return rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :]


def tint(base_linear, shade, neutral=False):
    """shade multiplies the linear base colour, then encodes to sRGB bytes.

    With neutral=True the base colour is left OUT and the map carries only the
    luminance pattern. The colour then rides on the glTF baseColorFactor, so a
    colour variant is a three-float change rather than a whole new texture —
    which is what makes the configurator's colour options free.
    """
    base = np.ones(3) if neutral else np.asarray(base_linear)
    c = base[None, None, :] * shade[..., None]
    return (linear_to_srgb(c) * 255).astype(np.uint8)


def lap_siding(px, density, exposure_ft, base):
    """Lap siding: each course laps the one below, so the bottom edge casts a
    line. The tile repeats cleanly only if `px` is a whole number of courses,
    which is the caller's to choose."""
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
    return tint(base, np.clip(shade, 0, 1.3), neutral=True), normal_from_height(h, 3.0)
