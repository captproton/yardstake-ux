"""
Pixel <-> model-feet mapping for the A1.1 FRONT ELEVATION - OPTION B.

THIS SHEET HAS ALREADY DEFEATED TWO CALIBRATION ATTEMPTS. They returned 59.3
and then 44.3 px/ft where 1/4"=1'-0" at 200 dpi must give exactly 50.0; the
second had grabbed the door casing instead of the leaf. The elevation is a
harder target than the plan because the shingle field puts a candidate edge
every course, and because each opening is drawn as FOUR nested rectangles —
casing, unit, and two frame lines — of which only one is the size callout.

WHICH RECTANGLE IS THE CALLOUT, settled by known answers rather than by eye.
`W-LIVING-S1` and `W-LIVING-S2` are already in the spec at 4'-0" x 3'-0" and
3'-0" x 5'-0", measured off the PLAN in P1. Read here, their outermost pair of
strong verticals spans 201 px and 150 px — their callout widths to within a
pixel — and the nested pairs inside sit at the same 6 px and 5 px insets on
both windows. So the OUTERMOST pair is the unit, and the casing sits 15 px
(3-1/2", the spec's casing width) outside it. Every opening below is read on
that rule.

CALIBRATION. Anchored on the sheet's own vertical dimension string, FF to
TOP OF PLATE, which is called out as 8'-0" and drawn between two dash-dot
level leaders 400.0 px apart -> 50.000 px/ft.

Cross-checks that did NOT feed the calibration:
  * exterior wall face to exterior wall face  1100 px = 22.000 ft (stated 22'-0")
  * loft knee wall, TOP OF PLATE to FF         217 px =  4.340 ft (stated 4'-4")
  * W-LIVING-S2 head lands at z 7.000 and its sill at z 2.000, reproducing two
    numbers the spec measured off a different sheet
  * the drawn roof apex lands at z 17.91, against the 17.90 that P3 recorded
    from its own independent trace of this elevation

Model frame (build_adu.py): east=+X, north=+Y, up=+Z. X=0 at the WEST exterior
wall face, Z=0 at main finished floor. On this elevation west is left and up is
up, so column increases with X and row DECREASES with Z.
"""
import subprocess
from pathlib import Path

import numpy as np

MODEL = Path(__file__).resolve().parents[2]
PDF = MODEL.parents[1] / "example plans/thataduguy/Barn-Cabin-524sf-ADU-1.0-.pdf"
CACHE = Path(__file__).resolve().parent / "_cache"

DPI = 200
PX_PER_FT = 50.0
PAGE = 3                        # A1.1, per spec.sheet_index

# Crop of the sheet holding the FRONT ELEVATION - OPTION B, in full-sheet pixels.
CROP = (3300, 80, 5200, 1320)

# Pixel anchors, in CROP coordinates. These are measurements of THIS raster at
# THIS crop, not building dimensions, so they stay literal here -- the same
# split frame.py makes. Everything derived from them belongs in spec.yaml.
ROW_MAIN_FF = 1007.5            # dash-dot "FF" leader, lower
ROW_TOP_PLATE = 607.5           # dash-dot "TOP OF PLATE" leader, lower
COL_WEST_FACE = 146.0           # west exterior wall face
COL_EAST_FACE = 1246.0          # east exterior wall face

# Dark threshold. The sheet is a vector render, so ink is near-black and the
# shingle course lines are near-black too; there is no grey to separate them by
# and the separation is done geometrically instead, by run length.
INK = 100


def elevation_raster():
    """Rasterise A1.1 and return the cropped front-elevation image.

    Cached under a key carrying PAGE, DPI and CROP, so a change to any of them
    cannot silently hand back the previous render. Every number in this module
    is taken off this image; one stale raster would corrupt all of them.
    """
    from PIL import Image

    CACHE.mkdir(exist_ok=True)
    key = "p{}_d{}_c{}".format(PAGE, DPI, "-".join(str(v) for v in CROP))
    crop_png = CACHE / ("frontelev_%s.png" % key)
    if crop_png.exists():
        return Image.open(crop_png)

    if not PDF.exists():
        raise SystemExit(f"plan set not found: {PDF}")
    stem = CACHE / ("sheet_p%d_d%d" % (PAGE, DPI))
    renders = sorted(CACHE.glob("sheet_p%d_d%d-*.png" % (PAGE, DPI)))
    if not renders:
        subprocess.run(
            ["pdftoppm", "-f", str(PAGE), "-l", str(PAGE), "-r", str(DPI),
             "-png", str(PDF), str(stem)],
            check=True,
        )
        renders = sorted(CACHE.glob("sheet_p%d_d%d-*.png" % (PAGE, DPI)))
    if not renders:
        raise SystemExit(f"pdftoppm produced no output for page {PAGE}")
    im = Image.open(renders[0]).convert("L").crop(CROP)
    im.save(crop_png)
    return im


def ink():
    """The raster as a boolean ink mask."""
    from PIL import Image  # noqa: F401  (kept for the import-time dependency)
    return np.asarray(elevation_raster()) < INK


def z_ft(row):
    return (ROW_MAIN_FF - row) / PX_PER_FT


def x_ft(col):
    return (col - COL_WEST_FACE) / PX_PER_FT


def row_px(z):
    return ROW_MAIN_FF - z * PX_PER_FT


def col_px(x):
    return COL_WEST_FACE + x * PX_PER_FT


def inches(px):
    return px / PX_PER_FT * 12.0


def _edges(vals, tol=2):
    """Collapse runs of adjacent inked columns/rows into one edge each, at the
    run's centre. A drawn line is 2-3 px wide at this resolution, so without
    this every line counts two or three times and every inset is wrong."""
    out, run = [], [vals[0]]
    for v in vals[1:]:
        if v - run[-1] <= tol:
            run.append(v)
        else:
            out.append(sum(run) / len(run))
            run = [v]
    out.append(sum(run) / len(run))
    return out


def strong_cols(mask, r0, r1, c0, c1, frac=0.4):
    """Columns inked over at least `frac` of the row band.

    A window's frame lines run the full height of the band and the shingle
    courses do not, so RUN LENGTH is what separates them. There is no
    brightness difference to use: this is a vector render and the shingle
    coursing is the same near-black as the frames.
    """
    prof = mask[r0:r1, c0:c1].sum(axis=0)
    hits = [c0 + i for i, n in enumerate(prof) if n >= (r1 - r0) * frac]
    return _edges(hits) if hits else []


def strong_rows(mask, r0, r1, c0, c1, frac=0.4):
    prof = mask[r0:r1, c0:c1].sum(axis=1)
    hits = [r0 + i for i, n in enumerate(prof) if n >= (c1 - c0) * frac]
    return _edges(hits) if hits else []


def unit_cols(mask, r0, r1, c0, c1, casing_px, frac=0.4):
    """The pair of columns that is the window UNIT, not its casing.

    An opening on this sheet is drawn as a nest of symmetric rectangles and
    only one of them is the size callout. Two rules, both checked against
    known answers before use:

      * a level counts only if BOTH sides of it are inked, so a casing line
        that survived on one jamb and not the other cannot set the width;
      * if the outermost surviving level sits a CASING WIDTH outside the next
        one, it is the casing and is dropped.

    The casing width comes from the spec (`trim.casing_width`), so this rule
    is not a magic number tuned until the answer looked right -- which is
    exactly how an earlier attempt on this sheet reached 44.3 px/ft by
    measuring the front door's casing and calling it the leaf.
    """
    edges = strong_cols(mask, r0, r1, c0, c1, frac)
    if len(edges) < 2:
        return None
    # The centre is found by SYMMETRY, not by taking the midpoint of the
    # outermost lines. On W-LIVING-S1 the casing survived the run-length test
    # on the west jamb and not the east, so a midpoint centre landed 7 px off
    # and every half-width after it was wrong.
    centre = max(
        (c / 2 for c in range(2 * c0, 2 * c1)),
        key=lambda cand: (sum(any(abs(o - (2 * cand - e)) < 2 for o in edges)
                              for e in edges),
                          -abs(cand - (c0 + c1) / 2)),
    )
    half = sorted({round(abs(e - centre), 1) for e in edges}, reverse=True)
    paired = [h for h in half
              if any(abs(e - (centre - h)) < 2 for e in edges)
              and any(abs(e - (centre + h)) < 2 for e in edges)]
    if not paired:
        return None
    if len(paired) > 1 and abs((paired[0] - paired[1]) - casing_px) < 3:
        paired = paired[1:]
    return centre - paired[0], centre + paired[0]


def unit_rows(mask, r0, r1, c0, c1, frac=0.4):
    """The head and sill of the window UNIT, by the nesting signature.

    Vertically the nest is NOT symmetric -- a head casing sits above and an
    apron below -- so the outermost pair is the wrong answer here even though
    it is the right one horizontally. What is stable is the inward nesting:
    on both `W-LIVING-S1` and `W-LIVING-S2` the unit edge is followed by two
    more lines at +6 and +11 px, on both the head and the sill.
    """
    edges = strong_rows(mask, r0, r1, c0, c1, frac)

    def nested(e, direction):
        return (any(abs(x - (e + 6 * direction)) < 2 for x in edges)
                and any(abs(x - (e + 11 * direction)) < 2.5 for x in edges))

    heads = [e for e in edges if nested(e, +1)]
    sills = [e for e in edges if nested(e, -1)]
    if not heads or not sills:
        return None
    return min(heads), max(sills)


def door_leaf(mask, r0, r1, c0, c1, frac=0.85):
    """The front door's LEAF -- and it is not found the way a window is.

    A WINDOW's callout is its unit, the second level in from the casing. A
    DOOR's callout is its leaf, which is a level further in still: 3'-0" of
    leaf inside a 3'-3" frame inside the casing. Running `unit_cols` on this
    door returns 39", the frame, and relaxing it one more level returns 46",
    the casing -- which is 44.3 px/ft, the exact number an earlier attempt on
    this sheet published.

    So the door gets its own rule, and the rule is INNERMOST rather than
    outermost: inside the leaf nothing else runs the door's full height. The
    lite grid stops at the lock rail and the recessed panel stops above the
    bottom rail, so the innermost full-height pair can only be the leaf.

    That rule cannot be shared with the windows: their innermost full-height
    pair is the sash. Two openings that look alike are being measured by
    opposite rules on purpose, and pretending otherwise is what broke this
    twice.
    """
    edges = strong_cols(mask, r0, r1, c0, c1, frac)
    if len(edges) < 2:
        return None
    centre = (min(edges) + max(edges)) / 2
    inner = [e for e in edges if abs(e - centre) > 2]     # skip a centre stile
    left = max(e for e in inner if e < centre)
    right = min(e for e in inner if e > centre)
    return left, right


def _fmt(v):
    """Feet as a plan-style string, to the nearest 1/16 inch."""
    neg, v = v < 0, abs(v)
    ft = int(v)
    e = round((v - ft) * 192)
    if e == 192:
        ft, e = ft + 1, 0
    i, r = divmod(e, 16)
    return f"{'-' if neg else ''}{ft}'-{i}" + (f' {r}/16"' if r else '"')


def _spec():
    import yaml
    return yaml.safe_load((MODEL / "spec.yaml").read_text())


# Search bands, in CROP pixels. Each is a generous box around one opening --
# generous on purpose, because a band tightened until the answer came out right
# would be the fitting this sheet has already punished twice. The readers above
# do the discriminating; the band only says which opening.
BANDS = {
    "W-LIVING-S1": dict(cols=(680, 790, 270, 530), rows=(640, 830, 330, 470)),
    "W-LIVING-S2": dict(cols=(690, 880, 920, 1075), rows=(640, 930, 950, 1050)),
    "W-GABLE-S":   dict(cols=(340, 450, 600, 800), rows=(290, 500, 660, 735)),
}

# The two openings the spec measured off a DIFFERENT sheet in P1. They are the
# known answers this module is checked against before any of its own numbers
# are believed. If either stops reproducing, every reading here is suspect.
KNOWN = {"W-LIVING-S1": (4.0, 3.0), "W-LIVING-S2": (3.0, 5.0)}


def read_opening(mask, name, casing_px):
    b = BANDS[name]
    cols = unit_cols(mask, *b["cols"], casing_px)
    rows = unit_rows(mask, *b["rows"])
    if cols is None or rows is None:
        raise SystemExit(f"{name}: could not isolate the unit")
    cl, cr = cols
    rt, rb = rows
    return dict(w=(cr - cl) / PX_PER_FT, h=(rb - rt) / PX_PER_FT,
                centre=x_ft((cl + cr) / 2), sill=z_ft(rb), head=z_ft(rt),
                px=dict(left=cl, right=cr, top=rt, bottom=rb))


def report():
    m = ink()
    s = _spec()
    casing_px = s["trim"]["casing_width"]["ft"] * PX_PER_FT
    s_door = next(o for o in s["openings"]["main_floor"]["south_wall"]["openings"]
                  if o["id"] == "D-FRONT")
    px_per_ft = (ROW_MAIN_FF - ROW_TOP_PLATE) / 8.0

    print("CALIBRATION")
    print(f"  FF row {ROW_MAIN_FF} -> TOP OF PLATE row {ROW_TOP_PLATE}, "
          f"called out 8'-0\"  =  {px_per_ft:.3f} px/ft")
    span = COL_EAST_FACE - COL_WEST_FACE
    print(f"  cross-check (did not feed): wall face to wall face {span:.0f} px "
          f"= {span / PX_PER_FT:.3f} ft, stated 22'-0\"")
    print(f"  cross-check (did not feed): loft knee wall 217 px "
          f"= {217 / PX_PER_FT:.3f} ft, stated 4'-4\"")

    print("\nKNOWN ANSWERS — read by the same code path as everything below")
    bad = []
    for name, (want_w, want_h) in KNOWN.items():
        r = read_opening(m, name, casing_px)
        ok_w, ok_h = abs(r["w"] - want_w) < 0.05, abs(r["h"] - want_h) < 0.05
        print(f"  {name:12s} {r['w']:.3f} x {r['h']:.3f} ft  "
              f"(spec {want_w:.1f} x {want_h:.1f})  "
              f"head z {r['head']:.3f}  sill z {r['sill']:.3f}  "
              f"{'OK' if ok_w and ok_h else 'MISMATCH'}")
        if not (ok_w and ok_h):
            bad.append(name)
    if bad:
        raise SystemExit(f"\nREFUSING TO REPORT: {bad} no longer reproduce. "
                         "The reader is wrong, so nothing it says can be used.")

    print("\nGABLE WINDOW — the measurement this module exists for")
    g = read_opening(m, "W-GABLE-S", casing_px)
    print(f"  {g['w']:.3f} x {g['h']:.3f} ft  = {_fmt(g['w'])} x {_fmt(g['h'])}")
    print(f"  centre x {g['centre']:.3f} ft   sill z {g['sill']:.3f}   "
          f"head z {g['head']:.3f}")
    print(f"  pixels {g['px']}")

    print("\nFRONT DOOR D-FRONT")
    want = s_door["w"]
    leaf = door_leaf(m, 700, 1000, 590, 800)
    got = (leaf[1] - leaf[0]) / PX_PER_FT
    if abs(got - want) > 0.05:
        raise SystemExit(f"door leaf read {got:.3f} ft against a {want:.3f} ft "
                         "callout — the reader has found the frame or the "
                         "casing again, and nothing below can be used")
    print(f"  leaf {inches(leaf[1] - leaf[0]):.2f} in wide "
          f"(callout {_fmt(want)}), centre x {x_ft(sum(leaf) / 2):.3f} ft, "
          f"top z {z_ft(673.5):.3f}")
    grid_c = strong_cols(m, 695, 838, 620, 775, frac=0.7)
    grid_r = strong_rows(m, 690, 850, 650, 745, frac=0.7)
    print(f"  lite-grid verticals   {[round(v, 1) for v in grid_c]}")
    print(f"  lite-grid horizontals {[round(v, 1) for v in grid_r]}")

    print("\nRIDGE BEAM")
    rc = strong_cols(m, 190, 250, 660, 730, frac=0.9)
    print(f"  shaft edges {[round(v, 1) for v in rc]} -> "
          f"{inches(max(rc) - min(rc)):.2f} in between them")
    print(f"  drawn top z {z_ft(182):.3f}   bottom z {z_ft(268):.3f}")

    print("\nANOMALY, checked and NOT acted on")
    print(f"  the dash-dot TOP OF ROOF leader is at row 141.5 -> z {z_ft(141.5):.3f},")
    print(f"  but the drawn roof apex is at row 112 -> z {z_ft(112):.3f}. P3 chose")
    print("  the apex on an independent check (the 4:12 dormer plane where it")
    print("  meets the wall line) and the model is built to it. The leader is 7\"")
    print("  low. Recorded so the next reader does not re-derive it as a defect.")


if __name__ == "__main__":
    report()
