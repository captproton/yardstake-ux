"""
fixture_ink.py — where A-1.0 DRAWS Laurel's fixtures (#134, PR A).

    python3 models/laurel_a1_460/fixture_ink.py      (from buyer/3D; needs pdftocairo)

The fixtures' positions and sizes in plan, read off A-1.0's VECTORS the way
plan_ink.py reads the walls: the same SVG, the same frame registered on the
19'-2" and 24'-0" strings, so a fixture is placed in the frame every wall is
in. It prints what it measures and writes nothing; spec.fixtures.drawn
records the numbers, and test_fixture_ink.py measures them again on every CI
run, so the spec cannot drift from the drawing.

HOW EACH IS READ. A fixture is drawn in thin line (0.24 pt), and each has a
WINDOW below: the part of the plan to look in, in plan feet. The window only
says where to look; the numbers are the ink's.

  rect     the largest closed rectangle of thin lines in the window: range,
           sink, refrigerator, vanity, washer/dryer. `gap` lets a DASHED
           outline close -- the dishwasher, drawn dashed under the counter.
  sides    the bounding box of the thin STRAIGHT lines at least `min_len`
           long: the tub, whose three drawn sides meet the wall's line for
           its fourth, with the basin's shorter lines inside.
  ink      the bounding box of every thin path in the window: the toilet,
           a tank and a bowl drawn as a polyline.
  circle   the one path with the most points in the window: the water
           heater, a circle drawn as Bezier curves, whose control points lie
           on its bounding box.

The COUNTER is not drawn as a box. Its front is the long line at X 21.5, and
its ends are the refrigerator's side and the range's, so it is derived from
three measurements, not read as one.

WHAT IT CANNOT READ: height, which no plan carries, and the mini-split's
indoor unit, which no sheet draws. The condenser is on A-2.0 (#134, PR C).

FIXTURES ARE DRAWN TO THE FINISHED FACE. The vanity's back is at Y 5.959,
half an inch in from P_bath_W's stud face at 6.0: the 1/2" gyp board the
wall legend calls for. This model carries that board as a material, not a
thickness, so the build (PR B) takes a fixture's wall side to the stud face.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plan_ink  # noqa: E402

THIN_PT = 0.3                      # a fixture's lines are 0.24 pt; walls are 0.48 and heavier
AXIS_TOL_FT = 1e-3                 # a line is axis-aligned if its ends differ by less than this
CLOSE_FT = 0.01                    # rectangle sides meet to within this
DASH_GAP_FT = 0.3                  # the dishwasher's dashes leave gaps of about 0.25 ft
MIN_SIDE_FT = 0.4                  # a rectangle smaller than this is a symbol's detail, not a fixture
PLACES = 4

# WHERE TO LOOK, in plan feet: (method, X from, X to, Y from, Y to, options).
FIXTURES = {
    "range":        ("rect",   21.0,  23.6,  16.0,  18.75, {}),
    "sink":         ("rect",   21.55, 23.6,  11.0,  14.0,  {}),
    "refrigerator": ("rect",   21.3,  23.6,  6.3,   8.85,  {}),
    "dishwasher":   ("rect",   21.4,  23.6,  8.84,  10.9,  {"gap": DASH_GAP_FT}),
    "vanity":       ("rect",   14.95, 18.05, 4.0,   5.99,  {}),
    "washer_dryer": ("rect",   11.7,  14.5,  4.55,  7.3,   {}),
    "tub":          ("sides",  20.9,  23.55, 0.5,   6.0,   {"min_len": 2.0}),
    "toilet":       ("ink",    18.0,  20.95, 3.2,   5.96,  {}),
    "toilet_tank":  ("ink",    18.6,  20.4,  4.95,  5.99,  {}),   # the tank alone: PR B builds it taller than the bowl
    "water_heater": ("circle", 15.0,  17.15, 6.3,   11.15, {}),
}
COUNTER_FRONT = (21.3, 21.6, 8.8, 16.2)   # where to look for the counter's front line


class Plan:
    """A-1.0's thin ink in plan feet: straight lines and whole paths."""

    def __init__(self, svg_text, marks):
        segs = plan_ink.segments(svg_text)
        s, y0_px, x0_py = plan_ink.frame(segs, marks)
        to_x = lambda py: (x0_py - py) / s     # noqa: E731
        to_y = lambda px: (y0_px - px) / s     # noqa: E731
        self.along_y, self.along_x = [], []    # (at, lo, hi)
        for p, q, w in segs:
            if w >= THIN_PT:
                continue
            x1, y1, x2, y2 = to_x(p[1]), to_y(p[0]), to_x(q[1]), to_y(q[0])
            if abs(x1 - x2) < AXIS_TOL_FT:
                self.along_y.append((x1, min(y1, y2), max(y1, y2)))
            elif abs(y1 - y2) < AXIS_TOL_FT:
                self.along_x.append((y1, min(x1, x2), max(x1, x2)))
        self.paths = [[(to_x(py), to_y(px)) for px, py in pts]
                      for w, pts in plan_ink.paths(svg_text) if w < THIN_PT and pts]


def _index(lines):
    """{position rounded to PLACES: [(lo, hi)]}, so a side is looked up, not
    searched for. Scanning every line for every candidate side made the
    rectangle search take minutes."""
    out = {}
    for c, a, b in lines:
        out.setdefault(round(c, PLACES), []).append((a, b))
    return out


def _covered(index, at, lo, hi, gap):
    """Do the collinear lines at `at` run from lo to hi, allowing `gap`?"""
    spans = sorted((a, b) for a, b in index.get(at, ())
                   if b > lo - CLOSE_FT and a < hi + CLOSE_FT)
    reach = lo
    for a, b in spans:
        if a > reach + max(gap, CLOSE_FT):
            return False
        reach = max(reach, b)
    return reach >= hi - max(gap, CLOSE_FT)


def _inside(lines, lo, hi, a_lo, a_hi):
    return [ln for ln in lines if lo <= ln[0] <= hi and ln[1] >= a_lo - CLOSE_FT and ln[2] <= a_hi + CLOSE_FT]


def rect(plan, x0, x1, y0, y1, gap=0.0):
    """The largest closed rectangle of thin lines within the window."""
    vy = _inside(plan.along_y, x0, x1, y0, y1)     # constant X
    vx = _inside(plan.along_x, y0, y1, x0, x1)     # constant Y
    vy, vx = _index(vy), _index(vx)
    xs, ys = sorted(vy), sorted(vx)
    best = None
    for i, a in enumerate(xs):
        for b in xs[i + 1:]:
            if b - a < MIN_SIDE_FT:
                continue
            for j, c in enumerate(ys):
                for d in ys[j + 1:]:
                    if d - c < MIN_SIDE_FT:
                        continue
                    area = (b - a) * (d - c)
                    if best and area <= best[0]:
                        continue
                    if (_covered(vx, c, a, b, gap) and _covered(vx, d, a, b, gap)
                            and _covered(vy, a, c, d, gap) and _covered(vy, b, c, d, gap)):
                        best = (area, a, b, c, d)
    return None if best is None else best[1:]


def sides(plan, x0, x1, y0, y1, min_len):
    """The bounding box of the straight thin lines at least `min_len` long."""
    lines = ([(c, c, a, b) for c, a, b in _inside(plan.along_y, x0, x1, y0, y1) if b - a >= min_len]
             + [(a, b, c, c) for c, a, b in _inside(plan.along_x, y0, y1, x0, x1) if b - a >= min_len])
    if not lines:
        return None
    return (min(ln[0] for ln in lines), max(ln[1] for ln in lines),
            min(ln[2] for ln in lines), max(ln[3] for ln in lines))


def _within(plan, x0, x1, y0, y1):
    return [pts for pts in plan.paths
            if all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)]


def ink(plan, x0, x1, y0, y1):
    """The bounding box of every thin path lying wholly in the window."""
    pts = [p for path in _within(plan, x0, x1, y0, y1) for p in path]
    if not pts:
        return None
    return (min(x for x, _ in pts), max(x for x, _ in pts),
            min(y for _, y in pts), max(y for _, y in pts))


def circle(plan, x0, x1, y0, y1):
    """The bounding box of the path with the most points in the window."""
    found = _within(plan, x0, x1, y0, y1)
    if not found:
        return None
    pts = max(found, key=len)
    return (min(x for x, _ in pts), max(x for x, _ in pts),
            min(y for _, y in pts), max(y for _, y in pts))


METHODS = {"rect": rect, "sides": sides, "ink": ink, "circle": circle}


def measure(plan):
    """{fixture: {"x": [lo, hi], "y": [lo, hi]}}, rounded to PLACES; a fixture
    the window finds nothing in is None, never a guess."""
    out = {}
    for name, (method, x0, x1, y0, y1, opts) in FIXTURES.items():
        bb = METHODS[method](plan, x0, x1, y0, y1, **opts)
        out[name] = None if bb is None else {
            "x": [round(bb[0], PLACES), round(bb[1], PLACES)],
            "y": [round(bb[2], PLACES), round(bb[3], PLACES)]}
    fx0, fx1, fy0, fy1 = COUNTER_FRONT
    # The front is the LONGEST constant-X line crossing the window: it runs
    # from the refrigerator past the sink and the dishwasher, where every
    # other line there is a fixture's own short side.
    fronts = [(b - a, c) for c, a, b in plan.along_y
              if fx0 <= c <= fx1 and a < fy1 and b > fy0]
    ref, rng = out.get("refrigerator"), out.get("range")
    out["counter"] = None if not (fronts and ref and rng) else {
        "x": [round(max(fronts)[1], PLACES), ref["x"][1]],
        "y": [ref["y"][1], rng["y"][0]]}
    return out


def main():
    plan = Plan(plan_ink.svg(), plan_ink.labels())
    for name, bb in measure(plan).items():
        if bb is None:
            print(f"  {name:13s} NOT FOUND")
            continue
        (a, b), (c, d) = bb["x"], bb["y"]
        print(f"  {name:13s} X {a:8.4f} .. {b:8.4f} ({(b - a) * 12:5.1f}\")   "
              f"Y {c:8.4f} .. {d:8.4f} ({(d - c) * 12:5.1f}\")")


if __name__ == "__main__":
    sys.exit(main())
