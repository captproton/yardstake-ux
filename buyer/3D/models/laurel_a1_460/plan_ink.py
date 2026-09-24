"""
plan_ink.py — where A-1.0 DRAWS Laurel's partitions and interior doors (#132).

    python3 models/laurel_a1_460/plan_ink.py      (from buyer/3D; needs pdftocairo)

P3b. No elevation shows the interior, so #130's overlay could not reach it.
This reads the floor plan instead, and reads it as VECTORS, not pixels: A-1.0
is a CAD plot, and pdftocairo writes its lines out as SVG with their exact
coordinates. A 400 dpi raster, which #129 used, resolves about an inch. The
vectors resolve a few hundredths.

WHAT IS READ, AND HOW IT IS REGISTERED.
  * The frame comes from the sheet's own dimension ticks. The 19'-2" and
    24'-0" strings' end ticks sit on the outside faces of stud (A-1.0: "ALL
    DIMENSIONS TO FACE OF STUD U.N.O."), which fixes X 0, Y 0 and the scale.
    The plot is 17.9875 pt/ft, 0.07% under a true 1/4" = 1'-0".
  * A face is a 0.48 pt stroke: the sheet draws each stud face as a thin line
    and each gyp board face as a thick one.
  * A partition is the PAIR of those lines its thickness apart.
  * A door is the gap in its partition's stud-face line, read as a centre.

It prints what it measures and writes nothing. The numbers it prints are the
ones spec.plan_overlay records, and test_plan_ink.py re-measures them on
every CI run, so the spec cannot drift from the drawing.

WHAT IT CANNOT READ: height. A plan has none, and no section in A-3.0 to
A-3.5 cuts a partition.
"""
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF = HERE.parents[1] / "example plans" / "sacramento_adus" / "adu-plan-full-set-a1-laurel.pdf"
PAGE = 4                                      # A-1.0
NS = "{http://www.w3.org/2000/svg}"
NUM = r"-?\d+(?:\.\d+)?(?:e-?\d+)?"

# The frame's registration: page points of the ticks on the 19'-2" string
# (Y 19'-2" .. Y 0) and the 24'-0" string (X 24 .. X 0). Plot bookkeeping,
# not building dimensions: the ticks are read, and the feet come from the
# strings they carry.
TICK_Y_FRONT_PT, TICK_Y_REAR_PT, DEPTH_FT = 291.27, 636.03, 19.1667
TICK_X_TOP_PT, TICK_X_BOTTOM_PT, WIDTH_FT = 1057.35, 1489.05, 24.0
STUD_LINE_PT = 0.48                           # the stroke A-1.0 draws a stud face with
STROKE_TOL_PT = 0.05


def svg(page=PAGE, pdf=PDF):
    """A-1.0 as SVG text, via pdftocairo."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "page.svg"
        subprocess.run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page),
                        str(pdf), str(out)], check=True, capture_output=True)
        return out.read_text()


def segments(svg_text):
    """Every stroked straight segment: ((x0, y0), (x1, y1), stroke width), in
    page points with y down. Curves contribute their end points only."""
    out = []
    for el in ET.fromstring(svg_text).iter(NS + "path"):
        if el.get("stroke") in (None, "none"):
            continue
        m = re.fullmatch(r"matrix\((.*)\)", el.get("transform", "matrix(1,0,0,1,0,0)"))
        a, b, c, d, e, f = (float(v) for v in m.group(1).split(","))
        toks = re.findall(r"[MLCZ]|" + NUM, el.get("d", ""))
        cur = start = None
        i = 0
        while i < len(toks):
            t = toks[i]
            if t in "ML":
                x, y = float(toks[i + 1]), float(toks[i + 2])
                p = (a * x + c * y + e, b * x + d * y + f)
                if t == "L" and cur is not None:
                    out.append((cur, p, float(el.get("stroke-width", "1")) * abs(a)))
                if t == "M":
                    start = p
                cur, i = p, i + 3
            elif t == "C":
                x, y = float(toks[i + 5]), float(toks[i + 6])
                cur, i = (a * x + c * y + e, b * x + d * y + f), i + 7
            elif t == "Z":
                if cur is not None and start is not None and cur != start:
                    out.append((cur, start, float(el.get("stroke-width", "1")) * abs(a)))
                cur, i = start, i + 1
            else:
                i += 1
    return out


def frame():
    """(pt per ft, page x of Y 0, page y of X 0), from the two strings' ticks."""
    sy = (TICK_Y_REAR_PT - TICK_Y_FRONT_PT) / DEPTH_FT
    sx = (TICK_X_BOTTOM_PT - TICK_X_TOP_PT) / WIDTH_FT
    return (sx + sy) / 2, TICK_Y_REAR_PT, TICK_X_BOTTOM_PT


def stud_lines(segs):
    """Stud-face lines in Laurel's frame: {"along_X": [(Y, X0, X1)], "along_Y": [(X, Y0, Y1)]}.
    A line running along X is page-vertical, because A-1.0 draws X up the page."""
    s, y0_px, x0_py = frame()
    to_Y = lambda px: (y0_px - px) / s          # noqa: E731
    to_X = lambda py: (x0_py - py) / s          # noqa: E731
    along_X, along_Y = [], []
    for p, q, w in segs:
        if abs(w - STUD_LINE_PT) > STROKE_TOL_PT:
            continue
        if abs(p[0] - q[0]) < 0.05:
            a, b = sorted((to_X(p[1]), to_X(q[1])))
            along_X.append((to_Y(p[0]), a, b))
        elif abs(p[1] - q[1]) < 0.05:
            a, b = sorted((to_Y(p[0]), to_Y(q[0])))
            along_Y.append((to_X(p[1]), a, b))
    return {"along_X": along_X, "along_Y": along_Y}


def _runs(lines, runs_along, near, lo, hi, reach):
    """{position: total drawn length} of stud-face lines within `reach`."""
    runs = {}
    for pos, a, b in lines["along_" + runs_along]:
        if abs(pos - near) < reach and b > lo - 0.1 and a < hi + 0.1:
            key = round(pos, 4)
            runs[key] = runs.get(key, 0.0) + (b - a)
    return runs


def partition(lines, runs_along, near, far, lo, hi, reach=0.25, fit=0.02):
    """The drawn stud faces of a partition: the PAIR of stud-face lines whose
    spacing is the wall's thickness, `far - near`, to within `fit` ft, with
    the longest drawn runs. Returns (near, far) or (None, None).

    A PAIR, NOT THE NEAREST LINE. A door's jamb returns are short strokes of
    the same weight, and at P_laundry_E they sit half an inch outside both of
    the wall's faces -- nearer the old reading of it than the wall itself.
    A line on its own cannot tell a jamb from a face; two lines 3 1/2" apart
    running the wall's length can."""
    t = far - near
    a_runs = _runs(lines, runs_along, near, lo, hi, reach)
    b_runs = _runs(lines, runs_along, far, lo, hi, reach)
    pairs = [(ra + rb, a, b) for a, ra in a_runs.items() for b, rb in b_runs.items()
             if abs((b - a) - t) < fit]
    if not pairs:
        return None, None
    _, a, b = max(pairs)
    return a, b


def gap_centre(lines, runs_along, at, lo, hi):
    """The centre of the widest gap in a partition's stud-face line between
    lo and hi: its door. A CENTRE, because the schedule fixes the width, and
    where a wall is drawn as jamb returns the gap in the stud line is the
    rough opening while the jambs mark the leaf; both share a centre."""
    spans = sorted((a, b) for pos, a, b in lines["along_" + runs_along]
                   if abs(pos - at) < 0.005 and b > lo and a < hi)
    best, reach = None, lo
    for a, b in spans:
        if a > reach and (best is None or a - reach > best[1] - best[0]):
            best = (reach, a)
        reach = max(reach, b)
    return None if best is None else (best[0] + best[1]) / 2


def measure(spec, lines):
    """{partition id: (drawn near face, drawn far face)}, {door id: drawn centre}."""
    lay = spec["interior_partitions"]["layout"]
    t = lay["thickness"]["ft"]
    parts, doors = {}, {}
    for p in lay["partitions"]:
        sign = 1 if p["studs_toward"].startswith("+") else -1
        parts[p["id"]] = partition(lines, p["runs_along"], p["at_ft"],
                                   p["at_ft"] + sign * t, p["from_ft"], p["to_ft"])
    by_id = {p["id"]: p for p in lay["partitions"]}
    for d in lay["door_openings"]:
        host = by_id[d["in"]]
        at = parts[host["id"]][0]
        if at is not None:
            doors[d["id"]] = gap_centre(lines, host["runs_along"], at,
                                        host["from_ft"], host["to_ft"])
    return parts, doors


def main():
    import yaml
    spec = yaml.safe_load((HERE / "spec.yaml").read_text())
    s, _, _ = frame()
    lines = stud_lines(segments(svg()))
    parts, doors = measure(spec, lines)
    print(f"A-1.0 at {s:.4f} pt/ft")
    for pid, (near, far) in parts.items():
        print(f"  {pid:12s} face {near:.4f}  far face {far:.4f}")
    for did, centre in doors.items():
        print(f"  {did:12s} centre {centre:.4f}")


if __name__ == "__main__":
    sys.exit(main())
