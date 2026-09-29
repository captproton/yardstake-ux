"""
canopy_ink.py — where and how the plans DRAW the optional entry canopy (#144).

    python3 models/laurel_a1_460/canopy_ink.py      (from buyer/3D; needs pdftocairo)

Two sheets draw it, four times:

  A-3.4  AWNING PLAN VIEW (1" = 1'-0"): the 6'-6" by 2'-6" frame, its members,
         the joist that splits it into two bays, and the slats in each bay.
  A-3.4  AWNING SECTION (3" = 1'-0"): the 2x6 frame's depth, and the 2'-6"
         again.
  A-2.0  FRONT ELEVATION: where along the front wall it hangs, how high, and
         the two braces rising to their wall connections.
  A-2.0  SIDE (LEFT) ELEVATION: the projection and the heights again, and
         where each brace lands on the frame.

Each drawing's scale comes from itself: A-3.4's from its own dimension
strings (the 6'-6" and the 2'-6" are the frame's outer faces), A-2.0's from
the two wall outlines condenser_ink solves it from.

THEY DISAGREE ON THE DEPTH. Both elevations draw the frame 8" deep; the
section details a 2x6, 5 1/2". The detail governs the member and the
elevations the height of its underside (decided 2026-09-29); spec.discrepancies
records it, and test_canopy_ink.py holds it still true.

It prints what it measures and writes nothing; spec.variants.canopy records
the numbers and test_canopy_ink.py measures them again.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import condenser_ink  # noqa: E402
import plan_ink  # noqa: E402

AWNING_PAGE, ELEV_PAGE = 11, 6                # A-3.4, A-2.0
PLACES = 4

# WHERE TO LOOK, in each page's points (y down). Searches, not answers.
A34_PLAN = (100, 460, 120, 700)               # A-3.4 drawing 1, the awning plan view
A34_SECTION = (100, 700, 1300, 1500)          # A-3.4 drawing 2, the awning section
FRONT_ELEV = (150, 720, 100, 420)             # A-2.0 drawing 1, the front elevation
BRACE_ZONE = (360, 540, 190, 235)             # above the front door, where the braces rise

AXIS_TOL_PT = 0.05
RUN_GAP_PT = 5.0                              # a line broken by a callout's stem is one line
PLAN_PT_PER_FT = 72.0                         # A-3.4 plan, 1" = 1'-0"
SECTION_PT_PER_FT = 216.0                     # A-3.4 section, 3" = 1'-0"
FACE_RUN_PT = (100.0, 140.0)                  # the canopy's face in the front elevation, 6'-6" at 18 pt/ft
PROJ_RUN_PT = (30.0, 60.0)                    # its side in the side elevation, 2'-6" at 18 pt/ft
PLATE_PT = (2.0, 4.0)                         # a brace plate's face is 3 pt across
EDGE_PT = (1.0, 2.0)                          # ... and its edge, 1.4 to 1.6 pt
WALL_END_PT = 0.1


def _runs(segs, box, horizontal=True):
    """{line position: [(a0, a1), ...]}: the axis-aligned segments in `box`,
    joined where a gap of RUN_GAP_PT or less breaks them -- and each as
    drawn too, since a frame's inner line can lie within its outer one's
    span on the same row, and joining would swallow it."""
    lines = {}
    for p, q, w in segs:
        if not all(box[0] <= v[0] <= box[1] and box[2] <= v[1] <= box[3] for v in (p, q)):
            continue
        i, j = (1, 0) if horizontal else (0, 1)
        if abs(p[i] - q[i]) > AXIS_TOL_PT or abs(p[j] - q[j]) < AXIS_TOL_PT:
            continue
        lines.setdefault(round(p[i], 2), []).append(tuple(sorted((p[j], q[j]))))
    out = {}
    for at, spans in lines.items():
        merged = []
        for a0, a1 in sorted(spans):
            if merged and a0 <= merged[-1][1] + RUN_GAP_PT:
                merged[-1] = (merged[-1][0], max(merged[-1][1], a1))
            else:
                merged.append((a0, a1))
        out[at] = sorted(set(merged) | set(spans))
    return out


def _two_lines(runs, length, where, start=None):
    """The two positions at which one run of about `length` pt lies, and it;
    with `start`, only runs that begin there (the wall a canopy hangs from)."""
    best = {}                                  # the longest qualifying run on each row
    for at, spans in runs.items():
        for a0, a1 in spans:
            if length[0] <= a1 - a0 <= length[1] and (start is None or abs(a0 - start) <= WALL_END_PT):
                if at not in best or a1 - a0 > best[at][1] - best[at][0]:
                    best[at] = (a0, a1)
    hits = sorted((at, a0, a1) for at, (a0, a1) in best.items())
    if len(hits) != 2:
        raise ValueError(f"expected the canopy's two lines in {where}, found {len(hits)}: {hits}")
    return hits


def _plates(segs, box, wide=PLATE_PT, tall=PLATE_PT):
    """The brace plates in `box`: small closed rectangles `wide` by `tall`
    pt, as (x0, x1, y0, y1). The front elevation sees a wall plate's face;
    the side elevation sees it edge on, and the plate on the frame flat."""
    h = _runs(segs, box, horizontal=True)
    found = []
    for y0 in sorted(h):
        for a0, a1 in h[y0]:
            if not wide[0] <= a1 - a0 <= wide[1]:
                continue
            for y1 in sorted(h):
                if tall[0] <= y1 - y0 <= tall[1] and any(
                        abs(b0 - a0) < AXIS_TOL_PT and abs(b1 - a1) < AXIS_TOL_PT for b0, b1 in h[y1]):
                    found.append((round(a0, 2), round(a1, 2), y0, y1))
    return sorted(set(found))                  # a line drawn twice is one plate


def _covers(spans, lo, hi):
    """Whether one of `spans` runs the whole of lo..hi. A frame's side can run
    on past its corner as a dimension's extension line, so it covers the
    frame's height rather than matching it."""
    return any(a0 <= lo + AXIS_TOL_PT and a1 >= hi - AXIS_TOL_PT for a0, a1 in spans)


def _rectangles(h, v):
    """Every closed rectangle two equal horizontal runs and two covering
    verticals make, as (x0, x1, y0, y1), largest first."""
    rows = [(y, a0, a1) for y, spans in h.items() for a0, a1 in spans]
    found = set()
    for y0, a0, a1 in rows:
        for y1, b0, b1 in rows:
            if y1 > y0 and abs(a0 - b0) < AXIS_TOL_PT and abs(a1 - b1) < AXIS_TOL_PT \
                    and all(_covers(v.get(round(x, 2), ()), y0, y1) for x in (a0, a1)):
                found.add((round(a0, 2), round(a1, 2), y0, y1))
    return sorted(found, key=lambda r: -(r[1] - r[0]) * (r[3] - r[2]))


def plan_view(segs):
    """A-3.4's plan, in feet, the wall on the page's right: the frame's outer
    faces (the 6'-6" and 2'-6" strings dimension them, which proves the
    scale), its member, the bay joist, and one bay's slats, each slat's two
    faces measured from the frame's outer face."""
    h = _runs(segs, A34_PLAN, horizontal=True)
    v = _runs(segs, A34_PLAN, horizontal=False)
    rects = _rectangles(h, v)
    if not rects:
        raise ValueError("no frame in A-3.4's plan")
    ox0, ox1, oy0, oy1 = rects[0]
    # the frame's inner faces: the largest rectangle wholly inside its outer
    inside = [r for r in rects if r[0] > ox0 and r[1] < ox1 and r[2] > oy0 and r[3] < oy1]
    if not inside:
        raise ValueError(f"no inner faces to A-3.4's frame {rects[0]}")
    ix0, ix1, iy0, iy1 = inside[0]
    # the bay joist: the two rows between the inner faces that run the
    # inner width, nearest the middle
    mid = (iy0 + iy1) / 2
    joist = sorted((y for y, spans in h.items() if iy0 < y < iy1
                    and any(abs(a0 - ix0) < AXIS_TOL_PT and abs(a1 - ix1) < AXIS_TOL_PT for a0, a1 in spans)),
                   key=lambda y: abs(y - mid))[:2]
    if len(joist) != 2:
        raise ValueError(f"no bay joist in A-3.4's plan between {iy0} and {iy1}")
    bay = (iy0, min(joist))
    # the slats: the verticals that run the bay, in pairs, from the outer member in
    edges = sorted(x for x, spans in v.items() if ix0 - AXIS_TOL_PT <= x <= ix1 + AXIS_TOL_PT
                   and _covers(spans, *bay))
    if len(edges) % 2:
        raise ValueError(f"the slats' edges in A-3.4's plan do not pair: {edges}")
    slats = [[(edges[i] - ox0) / PLAN_PT_PER_FT, (edges[i + 1] - ox0) / PLAN_PT_PER_FT]
             for i in range(0, len(edges), 2)]
    return {"width": (oy1 - oy0) / PLAN_PT_PER_FT, "projection": (ox1 - ox0) / PLAN_PT_PER_FT,
            "member": (ix0 - ox0) / PLAN_PT_PER_FT, "bay_joist": abs(joist[1] - joist[0]) / PLAN_PT_PER_FT,
            "slats": slats}


def section_view(segs):
    """A-3.4's section, in feet, the wall on the page's right: the frame's
    depth, its projection to the wall's face, and the outer member."""
    h = _runs(segs, A34_SECTION, horizontal=True)
    v = _runs(segs, A34_SECTION, horizontal=False)
    rects = _rectangles(h, v)
    if not rects:
        raise ValueError("no frame in A-3.4's section")
    x0, x1, y0, y1 = rects[0]
    inner = sorted(x for x, spans in v.items() if x0 + AXIS_TOL_PT < x < x1 and _covers(spans, y0, y1))
    return {"depth": (y1 - y0) / SECTION_PT_PER_FT, "projection": (x1 - x0) / SECTION_PT_PER_FT,
            "member": (inner[0] - x0) / SECTION_PT_PER_FT}


def measure():
    """Every reading, in plan feet: {"plan", "section", "front", "side"}."""
    svg34, svg20 = (plan_ink.svg(page=p) for p in (AWNING_PAGE, ELEV_PAGE))
    segs34, segs20 = plan_ink.segments(svg34), plan_ink.segments(svg20)
    plan, section = plan_view(segs34), section_view(segs34)

    # A-2.0's scale and drawn cladding, as condenser_ink solves them
    rl, rr, _, _ = condenser_ink.elevation_frame(segs20, condenser_ink.REAR_ELEV)
    sl, sr, sff, _ = condenser_ink.elevation_frame(segs20, condenser_ink.SIDE_ELEV)
    s20 = ((rr - rl) - (sr - sl)) / (condenser_ink.STUD_WIDTH_FT - condenser_ink.STUD_DEPTH_FT)
    clad = ((rr - rl) / s20 - condenser_ink.STUD_WIDTH_FT) / 2
    W = condenser_ink.STUD_WIDTH_FT

    # FRONT: the front wall seen from +Y, so X 24 is on the viewer's LEFT
    fl, fr, fff, _ = condenser_ink.elevation_frame(segs20, FRONT_ELEV)
    to_X = lambda px: W - ((px - fl) / s20 - clad)     # noqa: E731
    to_Z = lambda py, ff: (ff - py) / s20               # noqa: E731
    (ft_y, fa0, fa1), (fb_y, _, _) = _two_lines(_runs(segs20, FRONT_ELEV), FACE_RUN_PT, "the front elevation")
    plates = _plates(segs20, BRACE_ZONE)
    if len(plates) != 2:
        raise ValueError(f"expected two brace wall plates over the door, found {plates}")
    front = {"x": sorted([to_X(fa0), to_X(fa1)]),
             "underside": to_Z(fb_y, fff), "top": to_Z(ft_y, fff),
             "brace_x": sorted(to_X((p[0] + p[1]) / 2) for p in plates),
             "wall_connection": [to_Z(plates[0][3], fff), to_Z(plates[0][2], fff)]}

    # SIDE (LEFT): the X 24 end seen from +X, the front on the viewer's RIGHT,
    # so the canopy runs right from the wall's drawn outer face
    side_box = (sr - WALL_END_PT, sr + PROJ_RUN_PT[1] + 5, condenser_ink.SIDE_ELEV[2], sff)
    (st_y, sa0, sa1), (sb_y, _, _) = _two_lines(_runs(segs20, side_box), PROJ_RUN_PT,
                                                "the side elevation", start=sr)
    above = (sr - WALL_END_PT, sa1 + PLATE_PT[1], condenser_ink.SIDE_ELEV[2], st_y + AXIS_TOL_PT)
    walls = [p for p in _plates(segs20, above, wide=EDGE_PT) if abs(p[0] - sr) <= WALL_END_PT]
    # the plate on the frame sits ON its top line, so its bottom edge is that
    # line: it is found by its top edge, one plate's edge above the frame.
    lands = [(a0, a1, y, st_y) for y, spans in _runs(segs20, above).items()
             if EDGE_PT[0] <= st_y - y <= EDGE_PT[1]
             for a0, a1 in spans if PLATE_PT[0] <= a1 - a0 <= PLATE_PT[1]]
    if len(walls) != 1 or len(lands) != 1:
        raise ValueError(f"expected one wall plate and one plate on the frame in the side "
                         f"elevation, found {walls} and {lands}")
    wall_plate, land = walls[0], lands[0]
    side = {"projection": (sa1 - sa0) / s20,
            "underside": to_Z(sb_y, sff), "top": to_Z(st_y, sff),
            "wall_connection": [to_Z(wall_plate[3], sff), to_Z(wall_plate[2], sff)],
            "brace_lands_from_wall": ((land[0] + land[1]) / 2 - sr) / s20}

    def rnd(v):
        if isinstance(v, dict):
            return {k: rnd(a) for k, a in v.items()}
        return [rnd(a) for a in v] if isinstance(v, list) else round(v, PLACES)
    return {"plan": rnd(plan), "section": rnd(section), "front": rnd(front), "side": rnd(side),
            "a20": {"pt_per_ft": round(s20, PLACES), "cladding_ft": round(clad, PLACES)}}


def main():
    for k, v in measure().items():
        print(f"  {k:8s} {v}")


if __name__ == "__main__":
    sys.exit(main())
