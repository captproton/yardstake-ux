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
- THE PARTITION FACES FOLLOW FROM THE INTERIOR STRINGS (#129). Each of the
  five strings the layout claims to read is recomputed from the faces it is
  said to run between. A face moved by a typo stops agreeing with its string.
- every partition lies inside the envelope, and no two overlap in plan
- every interior door is its schedule width, and sits inside the wall it names
- EVERY ROW OF THE DOOR SCHEDULE IS ACCOUNTED FOR: built as an exterior
  opening, built as an interior one, or recorded as the 1-bedroom option
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

# A SPEC IS READ, NOT OBEYED (rule 25). These two used to be `startswith("+")`
# and `== "X"` with an else, in the verifier as well as in the build: so
# `studs_toward: north` silently meant the negative side, and `runs_along: Z`
# silently meant Y. A partition and its door could both carry the same wrong
# value, agree with each other, and pass every gate that follows while the
# geometry was rotated. Reproduced both ways before this was added.
AXES = ("X", "Y")
DIRECTIONS = {"+X", "-X", "+Y", "-Y"}


def _axis(who, value):
    if value not in AXES:
        raise ValueError(f"{who}: runs_along is {value!r}, not one of {list(AXES)}")
    return value


def _sign(who, value):
    if value not in DIRECTIONS:
        raise ValueError(f"{who}: studs_toward is {value!r}, not one of {sorted(DIRECTIONS)}")
    return +1 if value.startswith("+") else -1


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

    # ── the partitions (#129) ─────────────────────────────────────────────
    layout = spec["interior_partitions"]["layout"]
    thick = float(layout["thickness"]["ft"])
    part = {}
    for row in layout["partitions"]:
        near = float(row["at_ft"])
        far = near + thick if _sign(row["id"], row["studs_toward"]) > 0 else near - thick
        _axis(row["id"], row["runs_along"])
        part[row["id"]] = dict(row, near=near, far=far,
                               lo=min(near, far), hi=max(near, far),
                               a=float(row["from_ft"]), b=float(row["to_ft"]))

    # the interior strings, recomputed from the faces the layout reads them onto
    strings = {r["raw"]: r["runs_along"]
               for r in spec["interior_partitions"]["dimension_strings"]["strings"]}
    # Each row is (raw, EXPECTED AXIS, computed length, what it spans). The
    # axis is checked as well as the length, because a string that changed
    # axis would otherwise still pass: the faces it is read between are
    # measured along one axis, and `runs_along` claims another, and nothing
    # compared the two. Found by review.
    reads = [
        ("6'-6 1/2\"", "X", float(width) - part["P_pantry_N"]["far"],
         "the X 24 face of stud to the pantry's far wall"),
        ("2'-6\"", "X", part["P_pantry_N"]["far"] - part["P_bath_S"]["near"],
         "the pantry block, outside to outside"),
        ("6'-2\"", "X", part["P_pantry_N"]["far"] - part["P_block_S"]["far"],
         "pantry and closet together"),
        ("7'-3\"", "Y", part["P_block_W"]["near"] - part["P_laundry_E"]["near"],
         "the closet and laundry block"),
        ("3'-2\"", "Y", part["P_laundry_W"]["far"] - part["P_laundry_E"]["near"],
         "the laundry"),
        # Two more, resolved by #132 reading the strings' own ticks: until then
        # neither landed on a pair of faces #129's reading used.
        ("5'-2\"", "Y", part["P_block_W"]["near"] - part["P_bath_W"]["far"],
         "P_bath_W's kitchen face to P_block_W's living face"),
        ("3'-9\"", "Y", part["P_laundry_E"]["near"]
         - float(spec["construction"]["exterior_wall"]["stud_depth"]["ft"]),
         "the rear wall's inside face to P_laundry_E"),
    ]
    wrong = []
    for raw, axis, got, what in reads:
        want = float(parse_length(raw))
        if raw not in strings:
            wrong.append(f"{raw} is not one of the recorded strings")
            continue
        if strings[raw] != axis:
            wrong.append(f"{raw} ({what}) is read along {axis}, but the "
                         f"string records runs_along: {strings[raw]}")
        if not close(got, want):
            wrong.append(f"{raw} ({what}) computes to {got:.4f}, not {want:.4f}")
    gate(not wrong, "the partition faces follow from the interior strings", "; ".join(wrong))

    # inside the envelope, and no two overlapping in plan
    x_in = (float(spec["construction"]["exterior_wall"]["stud_depth"]["ft"]), float(width) - float(spec["construction"]["exterior_wall"]["stud_depth"]["ft"]))
    y_in = (x_in[0], float(depth) - x_in[0])
    outside = []
    for pid, r in part.items():
        across, along = (y_in, x_in) if r["runs_along"] == "X" else (x_in, y_in)
        if not (across[0] - TOL <= r["lo"] and r["hi"] <= across[1] + TOL):
            outside.append(f"{pid} across {r['lo']:.4f}..{r['hi']:.4f}")
        if not (along[0] - TOL <= min(r["a"], r["b"]) and max(r["a"], r["b"]) <= along[1] + TOL):
            outside.append(f"{pid} along {r['a']:.4f}..{r['b']:.4f}")
    gate(not outside, "every partition lies inside the envelope", ", ".join(outside))

    def rect(r):
        """(x_lo, x_hi, y_lo, y_hi) in plan."""
        a, b = min(r["a"], r["b"]), max(r["a"], r["b"])
        return (a, b, r["lo"], r["hi"]) if r["runs_along"] == "X" else (r["lo"], r["hi"], a, b)

    # Partitions run wall to wall, so two that meet share their junction: an
    # overlap no larger than one thickness each way is a butt or a tee. An
    # overlap longer than that is one wall running THROUGH another.
    over = []
    ids = sorted(part)
    for i, one in enumerate(ids):
        for other in ids[i + 1:]:
            ax0, ax1, ay0, ay1 = rect(part[one])
            bx0, bx1, by0, by1 = rect(part[other])
            ox = min(ax1, bx1) - max(ax0, bx0)
            oy = min(ay1, by1) - max(ay0, by0)
            if ox > TOL and oy > TOL and (ox > thick + TOL or oy > thick + TOL):
                over.append(f"{one} and {other} share {ox:.4f} by {oy:.4f}")
    gate(not over, "no partition runs through another (a junction is at most one thickness)",
         ", ".join(over))

    # interior doors: schedule width, and inside the wall they name
    doors = {str(d["mark"]): d for d in spec["openings"]["door_types"]["types"]}
    bad = []
    for d in layout["door_openings"]:
        host = part.get(d["in"])
        if host is None:
            bad.append(f"{d['id']} names {d['in']}, which is not a partition")
            continue
        a, b = float(d["a_ft"]), float(d["b_ft"])
        typed = doors.get(str(d["type"]))
        if typed is None:
            bad.append(f"{d['id']} is typed {d['type']!r}, which the Door Schedule does not list")
        elif not close(b - a, float(typed["width"]["ft"])):
            bad.append(f"{d['id']} is {b - a:.4f} wide, schedule says {float(typed['width']['ft']):.4f}")
        _axis(d["id"], d["along"])
        if d["along"] != host["runs_along"]:
            bad.append(f"{d['id']} runs along {d['along']}, {d['in']} runs along {host['runs_along']}")
        elif not (min(host["a"], host["b"]) - TOL <= a < b <= max(host["a"], host["b"]) + TOL):
            bad.append(f"{d['id']} at {a:.4f}..{b:.4f} is outside {d['in']}")
    gate(not bad, "every interior door is its schedule width, inside the wall it names", "; ".join(bad))

    # every schedule row is accounted for
    placed = {str(r["type"]) for r in by_id.values() if str(r["type"]) in doors}
    placed |= {str(d["type"]) for d in layout["door_openings"]}
    optional = {m for m, d in doors.items() if d.get("option")}
    missing = sorted(set(doors) - placed - optional)
    # ── A-2.0's ink against A-1.0's strings (#130) ────────────────────────
    # TWO SHEETS, TWO DERIVATIONS, COMPARED. Everything above checks this
    # spec against itself. These compare what #130 MEASURED off A-2.0's
    # elevation against what A-1.0's dimension strings put in the same place.
    # A window that agrees on both sheets is a window two independent readings
    # found in the same spot; one that does not is a question for a human.
    # It needs no Blender, so CI runs it.
    # INDEXED, NOT .get(). A gate reached through .get() disappears when its
    # block does: deleting elevation_overlay removed the whole cross-sheet
    # check and verify_spec still exited 0, reporting nineteen green gates and
    # never mentioning the twentieth. Reproduced before this changed. Indexing
    # makes the absence raise, which main() turns into a failed gate naming
    # the block -- the same way every other missing block here is handled.
    # And NO `if ov:` guard: an empty or null block skipped the gate the same
    # way. Unguarded, {} raises KeyError and null raises TypeError.
    ov = spec["elevation_overlay"]
    tol = ov["tolerance_in"]["value"] / 12.0
    sre = ov["side_right_elevation"]
    wt = {w["mark"]: w for w in o["window_types"]["types"]}
    lv = spec["levels"]
    off = []

    def near(what, drawn, strung):
        if abs(drawn - strung) > tol:
            off.append(f"{what}: A-2.0 draws {drawn:.4f}, A-1.0's strings give "
                       f"{strung:.4f} ({(drawn - strung) * 12:+.2f} in)")

    c = wt["C"]
    near("the C windows' sill", sre["window_c_sill"]["ft"], float(c["sill"]["ft"]))
    near("the C windows' head", sre["window_c_head"]["ft"],
         float(c["sill"]["ft"]) + float(c["height"]["ft"]))
    for drawn_key, oid in (("window_c1_drawn", "W-C1"), ("window_c2_drawn", "W-C2")):
        row = by_id[oid]
        near(f"{oid} near edge", sre[drawn_key]["y0"], row["y0"])
        near(f"{oid} far edge", sre[drawn_key]["y1"], row["y1"])
    # the plates are LABELLED on the sheet and DRAWN a fraction below;
    # this checks the ink against the label it sits under
    near("the roof underside at the front wall",
         sre["roof_underside_at_front_wall"]["ft"], float(lv["top_of_plate_front"]["ft"]))
    near("the roof underside at the rear wall",
         sre["roof_underside_at_rear_wall"]["ft"], float(lv["top_of_plate_rear"]["ft"]))
    near("the front overhang", sre["front_overhang"]["ft"],
         float(spec["roof"]["overhangs"]["front"]["ft"]))
    gate(not off, "A-2.0's drawn geometry agrees with A-1.0's dimension strings",
         "; ".join(off))

    # ── A-1.0's ink against the layout (#132, P3b) ────────────────────────
    # The interior's counterpart of the elevation overlay above: where A-1.0
    # DRAWS each partition's stud faces and each door, read off the PDF's
    # vectors by plan_ink.py, against where the layout's strings put them.
    # Indexed, like the elevation block, so a missing or empty block fails.
    po = spec["plan_overlay"]
    ptol = po["tolerance_in"]["value"] / 12.0
    # the measurements, not the citation that sits beside them
    drawn = {k: v for k, v in po["faces"].items() if k != "source"}
    centres = {k: v for k, v in po["door_centres"].items() if k != "source"}
    poff = []
    if set(drawn) != set(part):
        poff.append(f"plan_overlay.faces names {sorted(set(drawn) ^ set(part))} "
                    f"that the layout does not, or the other way round")
    for pid, r in part.items():
        if pid not in drawn:
            continue
        for what, want, got in (("face", r["near"], drawn[pid][0]),
                                ("far face", r["far"], drawn[pid][1])):
            if abs(got - want) > ptol:
                poff.append(f"{pid} {what}: A-1.0 draws {got:.4f}, the layout "
                            f"gives {want:.4f} ({(got - want) * 12:+.2f} in)")
    for d in layout["door_openings"]:
        if d["id"] not in centres:
            poff.append(f"{d['id']} has no drawn centre in plan_overlay")
            continue
        want = (float(d["a_ft"]) + float(d["b_ft"])) / 2
        got = float(centres[d["id"]])
        if abs(got - want) > ptol:
            poff.append(f"{d['id']} centre: A-1.0 draws {got:.4f}, the layout "
                        f"gives {want:.4f} ({(got - want) * 12:+.2f} in)")
    gate(not poff, "A-1.0's drawn partitions and interior doors agree with the layout",
         "; ".join(poff))

    gate(not missing, "every row of the door schedule is built or recorded as an option",
         "not placed: " + ", ".join(missing))


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
    try:
        dups = spec_lint.duplicate_keys(text)
        spec = yaml.safe_load(text)
    except yaml.YAMLError as e:
        gate(False, "the spec is valid YAML", " ".join(str(e).split()))
    else:
        gate(not dups, "no duplicate keys", "; ".join(f"line {ln}: {k!r}" for ln, k in dups))
        try:
            check(spec)
        except (KeyError, TypeError, ValueError, IndexError, AttributeError) as e:
            gate(False, "the spec has the blocks these gates read", f"{type(e).__name__}: {e}")
    print("-" * 76)
    if FAILED:
        print(f"{len(FAILED)} GATE(S) FAILED")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
