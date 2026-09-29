"""
condenser_ink.py — where the plans DRAW the mini-split condenser (#134, PR C).

    python3 models/laurel_a1_460/condenser_ink.py      (from buyer/3D; needs pdftocairo)

The first piece of equipment outside the building, and three sheets draw it:

  A-1.1  the power plan, as an "A/C" square outside the X 24 wall, with its
         disconnect beside it. A-1.1's plan IS A-1.0's, placed at another
         spot on the page, so it is registered on A-1.0 by the drawing both
         share -- the vanity basin's circle -- and the offset is proved on
         every long line A-1.0's plan draws before anything is read through it.
  A-2.0  the SIDE (LEFT) ELEVATION, as a dashed square standing on the F.F.
         line, 6" above the grade line: the pad. Its scale and the cladding's
         drawn thickness are solved from two elevations' wall outlines, whose
         stud dimensions A-1.0 gives (24'-0" and 19'-2").
  A-2.0  the REAR ELEVATION, as the same square against the REAR wall.

THE REAR ELEVATION DISAGREES WITH THE OTHER TWO. An elevation draws what lies
between the viewer and the wall: a condenser outside the X 24 wall would show
in the rear elevation beyond that wall's edge, and one against the rear wall
would show in the side elevation beyond the rear wall's edge. Neither does.
A-1.1 and the side elevation put it outside the X 24 wall; the rear
elevation stands alone. spec.discrepancies records it; the plan governs where
the unit is, the side elevation how tall and on what.

It prints what it measures and writes nothing; spec.fixtures.condenser
records the numbers and test_condenser_ink.py measures them again.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plan_ink  # noqa: E402

PLAN_PAGE, POWER_PAGE, ELEV_PAGE = 4, 5, 6    # A-1.0, A-1.1, A-2.0
PLACES = 4

# WHERE TO LOOK, in each page's points (y down). Searches, not answers.
BASIN_A10 = (525, 565, 1172, 1212)            # the vanity basin's circle on A-1.0
BASIN_A11 = (557, 597, 1186, 1226)            # ... and on A-1.1
AC_A11 = (520, 580, 1030, 1080)               # the A/C square on A-1.1
REAR_ELEV = (150, 720, 540, 800)              # A-2.0 drawing 2, the rear elevation
SIDE_ELEV = (150, 720, 1380, 1620)            # A-2.0 drawing 4, the side (left) elevation
PLAN_BOX = (280, 660, 1040, 1500)             # A-1.0's plan, for proving the offset

CIRCLE_MIN_PTS = 20                           # a Bezier circle is 20-odd points; a line is 2
CIRCLE_PT = (25.0, 45.0)                      # the basin is 28.4 pt across
OFFSET_MIN_MATCH = 60                         # of A-1.0's long plan lines found on A-1.1
LONG_LINE_PT = 20.0
MATCH_PT = 0.1
SQUARE_MIN_PT = 20.0                          # the A/C square is 30 pt; its label's box is 16 x 11
SYMBOL_CORNER_PT = 6.0                        # the dashed square's corner ticks
SYMBOL_TOL_PT = 0.2
OUTLINE_MIN_PT = 60.0                         # a wall outline's side is 60 pt or more
DATUM_MIN_PT = 150.0                          # F.F. and grade run the elevation's length
AXIS_TOL_PT = 0.05
STUD_WIDTH_FT, STUD_DEPTH_FT = 24.0, 19.1667  # A-1.0's 24'-0" and 19'-2", face of stud


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def _within(box, bb):
    return box[0] <= bb[0] and bb[1] <= box[1] and box[2] <= bb[2] and bb[3] <= box[3]


def circle_centre(paths, box):
    """The centre of the one circle -- a many-pointed square-boxed path -- in `box`."""
    found = []
    for _, pts in paths:
        if len(pts) < CIRCLE_MIN_PTS:
            continue
        bb = _bbox(pts)
        w, h = bb[1] - bb[0], bb[3] - bb[2]
        if _within(box, bb) and abs(w - h) < 1.0 and CIRCLE_PT[0] < w < CIRCLE_PT[1]:
            found.append(((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2))
    if len(found) != 1:
        raise ValueError(f"expected one circle in {box}, found {len(found)}")
    return found[0]


def a11_offset(segs10, segs11, paths10, paths11):
    """(dx, dy) that carries A-1.0's plan onto A-1.1's, PROVED: at least
    OFFSET_MIN_MATCH of A-1.0's long plan lines must lie on A-1.1 there."""
    c10, c11 = circle_centre(paths10, BASIN_A10), circle_centre(paths11, BASIN_A11)
    dx, dy = c11[0] - c10[0], c11[1] - c10[1]
    have = [(p, q) for p, q, _ in segs11]
    hits = 0
    for p, q, _ in segs10:
        if not (PLAN_BOX[0] <= p[0] <= PLAN_BOX[1] and PLAN_BOX[2] <= p[1] <= PLAN_BOX[3]):
            continue
        if ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 < LONG_LINE_PT:
            continue
        P, Q = (p[0] + dx, p[1] + dy), (q[0] + dx, q[1] + dy)
        if any(max(abs(a[0] - P[0]), abs(a[1] - P[1]), abs(b[0] - Q[0]), abs(b[1] - Q[1])) < MATCH_PT
               or max(abs(b[0] - P[0]), abs(b[1] - P[1]), abs(a[0] - Q[0]), abs(a[1] - Q[1])) < MATCH_PT
               for a, b in have):
            hits += 1
    if hits < OFFSET_MIN_MATCH:
        raise ValueError(f"A-1.1 shifted by ({dx:.2f}, {dy:.2f}) matches only {hits} of A-1.0's "
                         f"long plan lines: it is not A-1.0's plan, and cannot be read through it")
    return dx, dy, hits


def filled_square(svg_text, box):
    """The bounding box of the one FILLED closed path in `box`: A-1.1's A/C."""
    found = []
    for el in ET.fromstring(svg_text).iter(plan_ink.NS + "path"):
        if el.get("fill") in (None, "none") or el.get("stroke") not in (None, "none"):
            continue
        a, b, c, d, e, f = plan_ink.matrix(el)
        nums = [float(n) for n in re.findall(plan_ink.NUM, el.get("d", ""))]
        pts = [(a * x + c * y + e, b * x + d * y + f) for x, y in zip(nums[::2], nums[1::2])]
        if pts and _within(box, _bbox(pts)):
            bb = _bbox(pts)
            # A SQUARE, and a large one: the "A/C" label sits on a white
            # 16 x 11 pt box of its own inside the symbol.
            if abs((bb[1] - bb[0]) - (bb[3] - bb[2])) < 1.0 and bb[1] - bb[0] > SQUARE_MIN_PT:
                found.append(bb)
    if len(found) != 1:
        raise ValueError(f"expected one filled square in {box}, found {len(found)}")
    return found[0]


def symbol_square(paths, box):
    """The dashed square drawn by its corner ticks (6 pt L's) inside `box`."""
    ticks = []
    for _, pts in paths:
        if len(pts) == 3:
            bb = _bbox(pts)
            if (_within(box, bb) and abs(bb[1] - bb[0] - SYMBOL_CORNER_PT) < SYMBOL_TOL_PT
                    and abs(bb[3] - bb[2] - SYMBOL_CORNER_PT) < SYMBOL_TOL_PT):
                ticks.append(bb)
    if len(ticks) < 3:
        raise ValueError(f"no condenser symbol in {box}: {len(ticks)} corner ticks")
    return (min(t[0] for t in ticks), max(t[1] for t in ticks),
            min(t[2] for t in ticks), max(t[3] for t in ticks))


def elevation_frame(segs, box):
    """(left face x, right face x, F.F. y, grade y) of one elevation: its wall
    outline's outer sides and its two longest datum lines, in page points."""
    vert = [(p[0], abs(p[1] - q[1])) for p, q, w in segs
            if w > 0.4 and abs(p[0] - q[0]) < AXIS_TOL_PT and abs(p[1] - q[1]) > OUTLINE_MIN_PT
            and box[0] <= p[0] <= box[1] and box[2] <= min(p[1], q[1]) and max(p[1], q[1]) <= box[3]]
    hor = sorted({round(p[1], 2) for p, q, w in segs
                  if w > 0.4 and abs(p[1] - q[1]) < AXIS_TOL_PT and abs(p[0] - q[0]) > DATUM_MIN_PT
                  and box[2] <= p[1] <= box[3] and box[0] <= min(p[0], q[0])})
    if len(vert) < 2 or len(hor) < 2:
        raise ValueError(f"no wall outline or datums in the elevation at {box}")
    left, right = min(v[0] for v in vert), max(v[0] for v in vert)
    return left, right, hor[-2], hor[-1]      # F.F., then grade below it


def measure():
    """Every reading, in plan feet: {"plan": ..., "side": ..., "rear": ..., "a20": ...}."""
    svg10, svg11, svg20 = (plan_ink.svg(page=p) for p in (PLAN_PAGE, POWER_PAGE, ELEV_PAGE))
    segs10, segs11, segs20 = (plan_ink.segments(t) for t in (svg10, svg11, svg20))
    paths10, paths11, paths20 = (plan_ink.paths(t) for t in (svg10, svg11, svg20))

    # A-1.1, through A-1.0's frame
    s10, y0_px, x0_py = plan_ink.frame(segs10, plan_ink.labels())
    dx, dy, hits = a11_offset(segs10, segs11, paths10, paths11)
    ax0, ax1, ay0, ay1 = filled_square(svg11, AC_A11)
    to_X = lambda py: (x0_py - (py - dy)) / s10     # noqa: E731  (A-1.1 page y -> plan X)
    to_Y = lambda px: (y0_px - (px - dx)) / s10     # noqa: E731  (A-1.1 page x -> plan Y)
    plan = {"x": sorted([to_X(ay0), to_X(ay1)]), "y": sorted([to_Y(ax0), to_Y(ax1)])}

    # A-2.0: scale and drawn cladding from the two elevations' outlines
    rl, rr, rff, rgr = elevation_frame(segs20, REAR_ELEV)
    sl, sr, sff, sgr = elevation_frame(segs20, SIDE_ELEV)
    s20 = ((rr - rl) - (sr - sl)) / (STUD_WIDTH_FT - STUD_DEPTH_FT)
    clad = ((rr - rl) / s20 - STUD_WIDTH_FT) / 2
    # side (left): the X 24 end seen from +X, the rear on the left, so page x -> Y
    bx0, bx1, by0, by1 = symbol_square(paths20, SIDE_ELEV)
    side = {"y": [(bx0 - sl) / s20 - clad, (bx1 - sl) / s20 - clad],
            "base": (sff - by1) / s20, "top": (sff - by0) / s20, "grade": (sff - sgr) / s20}
    # rear: the rear wall seen from -Y, X 0 on the left, so page x -> X
    rx0, rx1, ry0, ry1 = symbol_square(paths20, REAR_ELEV)
    rear = {"x": [(rx0 - rl) / s20 - clad, (rx1 - rl) / s20 - clad],
            "base": (rff - ry1) / s20, "top": (rff - ry0) / s20}

    def rnd(v):
        return [round(a, PLACES) for a in v] if isinstance(v, list) else round(v, PLACES)
    return {"plan": {k: rnd(v) for k, v in plan.items()},
            "side": {k: rnd(v) for k, v in side.items()},
            "rear": {k: rnd(v) for k, v in rear.items()},
            "a20": {"pt_per_ft": rnd(s20), "cladding_ft": rnd(clad)},
            "a11": {"offset_pt": [rnd(dx), rnd(dy)], "lines_matched": hits}}


def main():
    m = measure()
    for k, v in m.items():
        print(f"  {k:5s} {v}")


if __name__ == "__main__":
    sys.exit(main())
