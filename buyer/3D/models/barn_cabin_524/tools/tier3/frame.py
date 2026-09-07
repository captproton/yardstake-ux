"""
Pixel <-> model-feet mapping for the A1.1 main floor plan.

A1.1 is pdf page 3, rasterised at 200 dpi, where the sheet's 1/4" = 1'-0" is
exactly 50.0 px/ft — the same scale the exterior openings were measured at in
P1, so nothing here needs resampling.

ANCHORED ON THE INTERIOR WALL FACES, not the drawn wall band. The band measures
29 px (~7") where the wall is 5-1/2": the same line-weight inflation that made
the exterior wall read 6-1/2" until P4 corrected it. Interior faces are also
what fixtures physically sit against, so they are the right datum twice over.

Calibration, checked both ways:
  interior north face (row 559) -> interior south face (row 1713.5)
      = 1154.5 px for an interior depth of 23'-1"  ->  50.01 px/ft
  interior east face then lands within 0.006 ft of its expected 21'-6-1/2".
Both interior dimensions reproduce to 1/8".

Model frame (build_adu.py): east=+X, north=+Y, up=+Z, X=0 at the west exterior
wall face, Y=0 at the porch outer (south) edge. On the sheet north is up and
west is left, so row increases as Y decreases.
"""
import subprocess
from pathlib import Path

MODEL = Path(__file__).resolve().parents[2]
PDF = MODEL.parents[1] / "example plans/thataduguy/Barn-Cabin-524sf-ADU-1.0-.pdf"
CACHE = Path(__file__).resolve().parent / "_cache"

DPI = 200
PX_PER_FT = 50.0
PAGE = 3                      # A1.1, per spec.sheet_index

# Crop of the sheet holding the main floor plan, in full-sheet pixels.
CROP = (280, 180, 2100, 2750)

COL_W_INNER = 434.0           # interior face of the west wall, in CROP pixels
ROW_N_INNER = 559.0           # interior face of the north wall


def _spec():
    import yaml
    return yaml.safe_load((MODEL / "spec.yaml").read_text())


# Dimensions come FROM THE SPEC, not from literals here. An earlier version
# hardcoded the 5-1/2" wall and the 30'-0" overall depth, duplicating numbers
# the spec already owns. Those would drift silently the next time one was
# corrected -- which is exactly what happened to the wall thickness between P2
# and P4. The pixel anchors above stay literal: they are measurements of THIS
# raster, not building dimensions.
_S = _spec()
WALL = _S["construction"]["exterior_wall_thickness"]["ft"]
TOTAL_DEPTH = _S["envelope"]["total_footprint_depth"]["ft"]

X0 = WALL                     # model X at COL_W_INNER
Y0 = TOTAL_DEPTH - WALL       # model Y at ROW_N_INNER  (29.5417)


def plan_raster():
    """Rasterise A1.1 and return the cropped main-floor-plan image.

    Cached: the rasterise is slow and perfectly deterministic.
    """
    from PIL import Image

    CACHE.mkdir(exist_ok=True)
    # The cache filename carries the settings that produced it. Keyed only by a
    # fixed name, a change to PAGE, DPI or CROP would silently return the OLD
    # raster -- and every Tier 3 measurement is taken off this image, so one
    # stale render would corrupt all of them without a word.
    key = "p{}_d{}_c{}".format(PAGE, DPI, "-".join(str(v) for v in CROP))
    crop_png = CACHE / ("mainplan_%s.png" % key)
    if crop_png.exists():
        return Image.open(crop_png)

    if not PDF.exists():
        raise SystemExit(f"plan set not found: {PDF}")
    stem = CACHE / ("sheet_%s" % key)
    subprocess.run(
        ["pdftoppm", "-f", str(PAGE), "-l", str(PAGE), "-r", str(DPI), "-png",
         str(PDF), str(stem)],
        check=True,
    )
    # pdftoppm appends its own page suffix, so glob for the render THIS call
    # made rather than whatever sheet-*.png happens to be lying around.
    renders = sorted(CACHE.glob("sheet_%s-*.png" % key))
    if not renders:
        raise SystemExit(f"pdftoppm produced no output for page {PAGE}")
    im = Image.open(renders[0]).convert("L").crop(CROP)
    im.save(crop_png)
    return im


def x_ft(col):
    return X0 + (col - COL_W_INNER) / PX_PER_FT


def y_ft(row):
    return Y0 - (row - ROW_N_INNER) / PX_PER_FT


def col_px(x):
    return COL_W_INNER + (x - X0) * PX_PER_FT


def row_px(y):
    return ROW_N_INNER + (Y0 - y) * PX_PER_FT


def ftin(v):
    """Feet as a plan-style string, to the nearest 1/8 inch."""
    neg, v = v < 0, abs(v)
    ft = int(v)
    e = round((v - ft) * 96)
    if e == 96:
        ft, e = ft + 1, 0
    i, r = divmod(e, 8)
    return f"{'-' if neg else ''}{ft}'-{i}" + (f' {r}/8"' if r else '"')


if __name__ == "__main__":
    im = plan_raster()
    print(f"main floor plan raster {im.size} at {PX_PER_FT} px/ft")
    print(f"interior width  {ftin(x_ft(1488.5) - x_ft(434)):>10s}   expected 21'-1\"")
    print(f"interior depth  {ftin(y_ft(559) - y_ft(1713.5)):>10s}   expected 23'-1\"")
