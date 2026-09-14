"""
models/laurel_a1_460/verify_spec.py — Laurel's spec against itself, and against
the drawings' orientation (#128).

    python3 models/laurel_a1_460/verify_spec.py [SPEC]      (from buyer/3D)

Plain Python; needs PyYAML. SPEC defaults to this model's spec.yaml.

WHAT THE SPEC LINT CANNOT SEE. adu_kit/spec_lint.py checks that every number
is cited and every drawn length is on its sheet. The first draft of this spec
had every front- and rear-wall position MIRRORED, and it passed the lint:
each number was cited and on its sheet. The error was in the frame. So these
gates check what numbers mean together:

- the positions of the openings follow from the dimension strings they cite
- no two openings overlap, and every one sits inside its wall
- the drawn window counts match the openings
- THE FRAME IS NOT MIRRORED. That is a fact about the drawings, so it is
  written here rather than read from the spec: A-2.0's SIDE (LEFT) ELEVATION
  draws windows D and E, and the building's left side, seen from the front, is
  +X when the front faces +Y and Z is up. So D and E must be on the X 24 wall,
  the two C windows on the X 0 wall, the front and rear strings must run from
  grid A at X 24, and door 1's sidelite (drawn on grid A's side) must be on the
  X 24 side of the door.
"""
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # buyer/3D, for adu_kit
from adu_kit import spec_lint  # noqa: E402
from adu_kit.sheets import parse_length  # noqa: E402

TOL = 0.0005
FAILED = []


def gate(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def close(a, b):
    return abs(float(a) - float(b)) <= TOL


def span(opening, lo, hi):
    return opening[lo], opening[hi]


def check(spec):
    o = spec["openings"]
    width = parse_length(spec["envelope"]["width"]["raw"])
    depth = parse_length(spec["envelope"]["depth"]["raw"])
    by_id = {}
    for wall in ("front_wall", "rear_wall", "end_wall_x0", "end_wall_x24"):
        for row in o[wall]["openings"]:
            by_id[row["id"]] = row
    doors = {str(d["mark"]): d for d in o["door_types"]["types"]}

    # ── the front wall: its string, read from grid A at X 24 ──────────────
    front = [parse_length(s) for s in o["front_wall"]["string"]]
    gate(sum(front) == width, "the front wall's string sums to the width", f"{sum(front)} vs {width}")
    edges = [width]
    for seg in front:
        edges.append(edges[-1] - seg)
    expected = {"W-A1": (edges[2], edges[1]), "D-1": (edges[4], edges[3]), "W-A2": (edges[6], edges[5])}
    wrong = [f"{i}: {span(by_id[i], 'x0', 'x1')} vs {tuple(round(float(v), 4) for v in xy)}"
             for i, xy in expected.items()
             if not (close(by_id[i]["x0"], xy[0]) and close(by_id[i]["x1"], xy[1]))]
    gate(not wrong, "front openings follow from the string, starting at grid A = X 24", "; ".join(wrong))
    transoms = [b for b, a in (("W-B1", "W-A1"), ("W-B2", "W-A2"))
                if not (close(by_id[b]["x0"], by_id[a]["x0"]) and close(by_id[b]["x1"], by_id[a]["x1"]))]
    gate(not transoms, "each B transom sits over its A window", ", ".join(transoms))

    d1 = by_id["D-1"]
    leaf, side = d1["leaf_x"], d1["sidelite_x"]
    inside = d1["x0"] - TOL <= min(leaf[0], side[0]) and max(leaf[1], side[1]) <= d1["x1"] + TOL
    gate(inside and close(leaf[1] - leaf[0], doors["1"]["width"]["ft"]) and close(side[1] - side[0], 1),
         "door 1 is its 3'-0\" leaf and 12\" sidelite, inside the opening", f"leaf {leaf}, sidelite {side}")
    gate(side[0] >= leaf[1] - TOL, "door 1's sidelite is on the X 24 side, where the plan draws it (grid A's side)",
         f"sidelite {side}, leaf {leaf}")

    # ── the rear wall: its string ends at grid B, X 0 ─────────────────────
    rear = [parse_length(s) for s in o["rear_wall"]["string"]]
    start = sum(rear)
    gate(close(o["rear_wall"]["string_start"]["ft"], start), "the rear string starts where its total puts it",
         f"{o['rear_wall']['string_start']['ft']} vs {float(start):.4f}")
    edges = [start]
    for seg in rear:
        edges.append(edges[-1] - seg)
    expected = {"D-6": (edges[2], edges[1]), "W-C3": (edges[4], edges[3])}
    wrong = [f"{i}: {span(by_id[i], 'x0', 'x1')} vs {tuple(round(float(v), 4) for v in xy)}"
             for i, xy in expected.items()
             if not (close(by_id[i]["x0"], xy[0]) and close(by_id[i]["x1"], xy[1]))]
    gate(not wrong and close(edges[-1], 0), "rear openings follow from the string, ending at grid B = X 0", "; ".join(wrong))

    # ── the end walls: which windows, and where along Y ───────────────────
    x24 = {row["type"] for row in o["end_wall_x24"]["openings"]}
    x0 = {row["type"] for row in o["end_wall_x0"]["openings"]}
    gate(x24 == {"D", "E"} and x0 == {"C"},
         "not mirrored: D and E on the X 24 wall, the C windows on X 0 (A-2.0 SIDE (LEFT) ELEVATION draws D and E)",
         f"X 24 holds {sorted(x24)}, X 0 holds {sorted(x0)}")
    from_front = [parse_length(s) for s in o["end_wall_x24"]["string_from_front"]]
    to_rear = [parse_length(s) for s in o["end_wall_x24"]["string_to_rear"]]
    d_y1 = depth - from_front[0]
    e_y0 = to_rear[-1]
    wrong = []
    if not (close(by_id["W-D1"]["y1"], d_y1) and close(by_id["W-D1"]["y0"], d_y1 - from_front[1])):
        wrong.append(f"W-D1 {span(by_id['W-D1'], 'y0', 'y1')}")
    if not (close(by_id["W-E1"]["y0"], e_y0) and close(by_id["W-E1"]["y1"], e_y0 + to_rear[0])):
        wrong.append(f"W-E1 {span(by_id['W-E1'], 'y0', 'y1')}")
    bottom = [parse_length(s) for s in o["end_wall_x0"]["string"]]
    gate(sum(bottom) == depth, "the X 0 wall's string sums to the depth", f"{sum(bottom)} vs {depth}")
    if not (close(by_id["W-C1"]["y1"], depth - bottom[0]) and close(by_id["W-C1"]["y0"], depth - bottom[0] - bottom[1])):
        wrong.append(f"W-C1 {span(by_id['W-C1'], 'y0', 'y1')}")
    if not (close(by_id["W-C2"]["y0"], bottom[-1]) and close(by_id["W-C2"]["y1"], bottom[-1] + bottom[-2])):
        wrong.append(f"W-C2 {span(by_id['W-C2'], 'y0', 'y1')}")
    gate(not wrong, "end-wall openings follow from their strings", "; ".join(wrong))

    # ── inside their walls, no overlaps, counts ───────────────────────────
    outside, overlaps = [], []
    for wall, lo, hi, length in (("front_wall", "x0", "x1", width), ("rear_wall", "x0", "x1", width),
                                 ("end_wall_x0", "y0", "y1", depth), ("end_wall_x24", "y0", "y1", depth)):
        rows = o[wall]["openings"]
        outside += [r["id"] for r in rows if not (-TOL <= r[lo] < r[hi] <= float(length) + TOL)]
        spans = sorted((r[lo], r[hi], r["id"]) for r in rows if r["type"] != "B")
        overlaps += [f"{a[2]} and {b[2]}" for a, b in zip(spans, spans[1:]) if b[0] < a[1] - TOL]
    gate(not outside, "every opening sits inside its wall", ", ".join(outside))
    gate(not overlaps, "no two openings on a wall overlap", ", ".join(overlaps))
    drawn = {}
    for row in by_id.values():
        if row["type"] in "ABCDE":
            drawn[row["type"]] = drawn.get(row["type"], 0) + 1
    stated = {k: v for k, v in o["count_check"]["windows_drawn"].items() if k in "ABCDE"}
    gate(drawn == stated, "the drawn window counts match the openings", f"openings {drawn}, count_check {stated}")


def main(argv):
    import yaml
    path = Path(argv[1]) if len(argv) > 1 else HERE / "spec.yaml"
    print("=" * 76)
    print(f"{path.name} -- Laurel's spec against itself and the drawings' orientation")
    print("=" * 76)
    try:
        text = path.read_text()
    except (OSError, UnicodeError) as e:
        print(f"verify_spec.py: cannot read {path}: {e}")
        return 1
    dups = spec_lint.duplicate_keys(text)
    gate(not dups, "no duplicate keys", "; ".join(f"line {ln}: {k!r}" for ln, k in dups))
    try:
        check(yaml.safe_load(text))
    except (KeyError, TypeError, ValueError, IndexError) as e:
        gate(False, "the spec has the blocks these gates read", f"{type(e).__name__}: {e}")
    print("-" * 76)
    if FAILED:
        print(f"{len(FAILED)} GATE(S) FAILED")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
