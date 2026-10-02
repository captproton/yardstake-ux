"""
models/willow_a2_460/verify_spec.py -- Willow's spec against itself, and against
the drawings' orientation (#171).

    python3 models/willow_a2_460/verify_spec.py [SPEC]      (from buyer/3D)

Plain Python; needs PyYAML. SPEC defaults to this model's spec.yaml.

WHAT THE SPEC LINT CANNOT SEE. adu_kit/spec_lint.py checks that every number is
cited and every drawn length is on its sheet. It does not check what the numbers
mean together: Laurel's first draft had every front- and rear-wall position
MIRRORED and passed the lint. So these gates check:

- every opening's position follows from the dimension string it cites
- the frame is not mirrored (written here, from what the elevations draw)
- no opening overlaps another or leaves its wall; the drawn window counts match
- the partition faces follow from the interior strings (carried from Laurel's
  layout, which Willow's A-1.0 draws with the same strings)
- every interior door is its schedule width, inside the wall it names, and every
  schedule row is built or recorded as the option
- THE ROOF ARITHMETIC CLOSES: top of roof less the plate, the main slope's rise,
  and what is left over for the heel; the porch ridge and where it meets the main
  roof's front slope

Adapted from Laurel's verify_spec.py, with what Willow does not have removed
(a sidelite on door 1, a transom row, two plate heights, Tier B blocks) and what it
does have added (the six D windows, window B, the two-roof arithmetic). Laurel's
file is the better-tested one; the kit move for it is a later step.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # buyer/3D, for adu_kit
from adu_kit import spec_lint  # noqa: E402
from adu_kit.sheets import parse_length  # noqa: E402
from adu_kit.specread import axis as _axis, sign as _sign  # noqa: E402

TOL = 0.0005
FAILED = []


def gate(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def close(a, b, tol=TOL):
    return abs(float(a) - float(b)) <= tol


def span(opening, lo, hi):
    return opening[lo], opening[hi]


def edges_from(start, string):
    """The running edge positions of a dimension string that begins at `start`
    and runs toward 0."""
    out = [start]
    for seg in string:
        out.append(out[-1] - seg)
    return out


def check(spec):
    o = spec["openings"]
    width = parse_length(spec["envelope"]["width"]["raw"])
    depth = parse_length(spec["envelope"]["depth"]["raw"])
    by_id = {}
    for wall in ("front_wall", "rear_wall", "end_wall_x0", "end_wall_x24"):
        for row in o[wall]["openings"]:
            by_id[row["id"]] = row
    doors = {str(d["mark"]): d for d in o["door_types"]["types"]}
    wins = {w["mark"]: w for w in o["window_types"]["types"]}

    # ── the front wall: its string, read from grid A at X 24 ──────────────
    front = [parse_length(s) for s in o["front_wall"]["string"]]
    gate(sum(front) == width, "the front wall's string sums to the width", f"{sum(front)} vs {width}")
    e = edges_from(width, front)
    # string order: wall, A, pier, B, door 1, wall, A, wall
    expected = {"W-A1": (e[2], e[1]), "W-B1": (e[4], e[3]), "D-1": (e[5], e[4]), "W-A2": (e[7], e[6])}
    wrong = [f"{i}: {span(by_id[i], 'x0', 'x1')} vs {tuple(round(float(v), 4) for v in xy)}"
             for i, xy in expected.items()
             if not (close(by_id[i]["x0"], xy[0]) and close(by_id[i]["x1"], xy[1]))]
    gate(not wrong, "front openings follow from the string, starting at grid A = X 24", "; ".join(wrong))

    d1 = by_id["D-1"]
    gate(close(d1["x1"] - d1["x0"], doors["1"]["width"]["ft"]), "door 1 is its schedule width",
         f"{d1['x1'] - d1['x0']:.4f} vs {doors['1']['width']['ft']}")
    b1 = by_id["W-B1"]
    rough = b1["x1"] - b1["x0"]
    sched = float(wins["B"]["width"]["ft"])
    gate(sched - TOL <= rough <= sched + 1 / 12 + TOL,
         "window B's rough opening is its schedule width plus at most an inch",
         f"opening {rough:.4f}, schedule {sched:.4f}")
    gate(b1["x0"] >= d1["x1"] - TOL,
         "window B is on the X 24 side of door 1, where the plan draws it (grid A's side)",
         f"B {b1['x0']}..{b1['x1']}, door {d1['x0']}..{d1['x1']}")

    # every exterior opening is its schedule width: a width typed twice (in a string and in the
    # schedule) cannot drift apart unseen. Window B is the one exception, by design: its span is
    # the rough opening, and its unit span (the window the sash is built to) is checked instead.
    off = []
    for wall, lo, hi in (("front_wall", "x0", "x1"), ("rear_wall", "x0", "x1"),
                         ("end_wall_x0", "y0", "y1"), ("end_wall_x24", "y0", "y1")):
        for row in o[wall]["openings"]:
            kind = str(row["type"])
            if kind in doors:
                want = float(doors[kind]["width"]["ft"])
            else:
                want = float(wins[kind]["width"]["ft"])
            got = row[hi] - row[lo]
            if kind == "B":
                if not (want - TOL <= got <= want + 1 / 12 + TOL):
                    off.append(f"{row['id']} rough opening {got:.4f} is not the schedule's {want:.4f} plus at most an inch")
                u0, u1 = row.get("unit_x0"), row.get("unit_x1")
                if u0 is None or u1 is None:
                    off.append(f"{row['id']} has no unit span (unit_x0/unit_x1)")
                else:
                    if not close(u1 - u0, want):
                        off.append(f"{row['id']} unit is {u1 - u0:.4f} wide, schedule says {want:.4f}")
                    if not (row[lo] - TOL <= u0 and u1 <= row[hi] + TOL):
                        off.append(f"{row['id']} unit {u0}..{u1} is outside its rough opening {row[lo]}..{row[hi]}")
                    if not close(u0 - row[lo], row[hi] - u1):
                        off.append(f"{row['id']} unit is not centred in its rough opening")
            elif not close(got, want):
                off.append(f"{row['id']} is {got:.4f} wide, schedule says {want:.4f}")
    gate(not off, "every exterior opening is its schedule width (window B's rough opening and its centred unit span, checked separately)",
         "; ".join(off))

    # a window type's operation has the units its schedule text says: "(DOUBLE)" is two units side
    # by side, so a plain SINGLE HUNG window must not get two (units counts sashes side by side)
    ops = spec["windows"]["operations"]
    bad_ops = []
    for w in o["window_types"]["types"]:
        op = ops.get(w["operation"])
        if op is None:
            bad_ops.append(f"window {w['mark']}: operation {w['operation']!r} is not in windows.operations")
            continue
        raw = w["operation_raw"].upper()
        want_units = 2 if "DOUBLE" in raw or raw == "SLIDER" else 1
        if op["units"] != want_units:
            bad_ops.append(f"window {w['mark']} ({w['operation_raw']}): operation {w['operation']} has units {op['units']}, expected {want_units}")
    gate(not bad_ops, "every window's operation has the number of side-by-side units its schedule text says",
         "; ".join(bad_ops))

    # ── the rear wall: its string runs from grid A to grid B ──────────────
    rear = [parse_length(s) for s in o["rear_wall"]["string"]]
    gate(sum(rear) == width, "the rear wall's string sums to the width", f"{sum(rear)} vs {width}")
    e = edges_from(width, rear)
    # string order: 9'-4" to the bath, wall to door, door 6, wall, E, wall
    expected = {"D-6": (e[3], e[2]), "W-E1": (e[5], e[4])}
    wrong = [f"{i}: {span(by_id[i], 'x0', 'x1')} vs {tuple(round(float(v), 4) for v in xy)}"
             for i, xy in expected.items()
             if not (close(by_id[i]["x0"], xy[0]) and close(by_id[i]["x1"], xy[1]))]
    gate(not wrong and close(e[-1], 0), "rear openings follow from the string, ending at grid B = X 0", "; ".join(wrong))

    # ── the end walls ─────────────────────────────────────────────────────
    x24 = {row["type"] for row in o["end_wall_x24"]["openings"]}
    x0 = {row["type"] for row in o["end_wall_x0"]["openings"]}
    gate(x24 == {"C", "F"} and x0 == {"D"},
         "not mirrored: C and F on the X 24 wall, the six D windows on X 0 (A-2.0 SIDE (LEFT) draws C and F)",
         f"X 24 holds {sorted(x24)}, X 0 holds {sorted(x0)}")
    gate(all(r["x1"] <= 11.1667 + TOL and r["x0"] >= -TOL for r in o["rear_wall"]["openings"]),
         "not mirrored: the rear wall's door 6 and window E are on the X 0 side (A-2.0 REAR ELEVATION draws them on the viewer's left)",
         str([span(r, "x0", "x1") for r in o["rear_wall"]["openings"]]))

    from_front = [parse_length(s) for s in o["end_wall_x24"]["string_from_front"]]
    to_rear = [parse_length(s) for s in o["end_wall_x24"]["string_to_rear"]]
    c_y1 = depth - from_front[0]
    f_y0 = to_rear[-1]
    wrong = []
    if not (close(by_id["W-C1"]["y1"], c_y1) and close(by_id["W-C1"]["y0"], c_y1 - from_front[1])):
        wrong.append(f"W-C1 {span(by_id['W-C1'], 'y0', 'y1')}")
    if not (close(by_id["W-F1"]["y0"], f_y0) and close(by_id["W-F1"]["y1"], f_y0 + to_rear[0])):
        wrong.append(f"W-F1 {span(by_id['W-F1'], 'y0', 'y1')}")
    for wid, mark in (("W-C1", "C"), ("W-F1", "F")):
        if not close(by_id[wid]["y1"] - by_id[wid]["y0"], wins[mark]["width"]["ft"]):
            wrong.append(f"{wid} is not its schedule width")

    bottom = [parse_length(s) for s in o["end_wall_x0"]["string"]]
    gate(sum(bottom) == depth, "the X 0 wall's string sums to the depth", f"{sum(bottom)} vs {depth}")
    halves = [parse_length(o["end_wall_x0"]["halves"][k]) for k in ("first", "second")]
    gate(sum(halves) == depth, "the X 0 wall's two halves sum to the depth", f"{sum(halves)} vs {depth}")
    # walk the string from the front: a 1'-6" segment is a window, the rest is wall
    d_rows = sorted((r for r in o["end_wall_x0"]["openings"]), key=lambda r: -r["y1"])
    windows = []
    at = float(depth)
    for seg in bottom:
        if seg == parse_length("1'-6\""):
            windows.append((round(float(at), 4), round(float(at - seg), 4)))
        at -= seg
    got = [(round(r["y1"], 4), round(r["y0"], 4)) for r in d_rows]
    if len(windows) != len(got) or any(not (close(a[0], b[0]) and close(a[1], b[1])) for a, b in zip(windows, got)):
        wrong.append(f"the D windows {got} vs the string's {windows}")
    gate(not wrong, "end-wall openings follow from their strings", "; ".join(wrong))

    # ── inside their walls, no overlaps, counts ───────────────────────────
    outside, overlaps = [], []
    for wall, lo, hi, length in (("front_wall", "x0", "x1", width), ("rear_wall", "x0", "x1", width),
                                 ("end_wall_x0", "y0", "y1", depth), ("end_wall_x24", "y0", "y1", depth)):
        rows = o[wall]["openings"]
        outside += [r["id"] for r in rows if not (-TOL <= r[lo] < r[hi] <= float(length) + TOL)]
        spans = sorted((r[lo], r[hi], r["id"]) for r in rows)
        overlaps += [f"{a[2]} and {b[2]}" for a, b in zip(spans, spans[1:]) if b[0] < a[1] - TOL]
    gate(not outside, "every opening sits inside its wall", ", ".join(outside))
    gate(not overlaps, "no two openings on a wall overlap", ", ".join(overlaps))
    drawn = {}
    for row in by_id.values():
        if row["type"] in "ABCDEF":
            drawn[row["type"]] = drawn.get(row["type"], 0) + 1
    stated = dict(o["count_check"]["windows_drawn"])
    scheduled = {w["mark"]: w["count_scheduled"] for w in o["window_types"]["types"]}
    gate(drawn == stated == scheduled, "the drawn window counts match the openings and the schedule",
         f"openings {drawn}, count_check {stated}, schedule {scheduled}")

    # ── the partitions ────────────────────────────────────────────────────
    layout = spec["interior_partitions"]["layout"]
    thick = float(layout["thickness"]["ft"])
    part = {}
    for row in layout["partitions"]:
        near = float(row["at_ft"])
        far = near + thick if _sign(row["id"], row["studs_toward"]) > 0 else near - thick
        _axis(row["id"], row["runs_along"])
        part[row["id"]] = dict(row, near=near, far=far, lo=min(near, far), hi=max(near, far),
                               a=float(row["from_ft"]), b=float(row["to_ft"]))

    # a wall's studs run ACROSS it: an X-running wall takes +Y or -Y, a Y-running wall +X or -X.
    # _sign reduces the direction to a sign, so without this `runs_along: X` with
    # `studs_toward: +X` passed every gate below while describing no wall.
    parallel = [pid for pid, r in part.items() if r["studs_toward"][1] == r["runs_along"]]
    gate(not parallel, "every partition's studs run across it (an X-running wall takes +Y or -Y, a Y-running wall +X or -X)",
         ", ".join(f"{pid} runs along {part[pid]['runs_along']} with studs_toward {part[pid]['studs_toward']}" for pid in parallel))
    # the one partition position Willow's own rear-wall string fixes: the bath wall's far face is where the
    # string's first segment ends (24'-0" less 9'-4")
    rear_first = float(parse_length(o["rear_wall"]["string"][0]))
    gate(close(part["P_bath_S"]["far"], float(width) - rear_first),
         "the bath wall's far face is the rear string's first segment from grid A (Willow's own 9'-4\")",
         f"far face {part['P_bath_S']['far']:.4f} vs {float(width) - rear_first:.4f}")

    strings = {r["raw"]: r["runs_along"] for r in spec["interior_partitions"]["dimension_strings"]["strings"]}
    stud = float(spec["construction"]["exterior_wall"]["stud_depth"]["ft"])
    reads = [
        ("6'-6 1/2\"", "X", float(width) - part["P_pantry_N"]["far"], "the X 24 face of stud to the pantry's far wall"),
        ("2'-6\"", "X", part["P_pantry_N"]["far"] - part["P_bath_S"]["near"], "the pantry block, outside to outside"),
        ("6'-2\"", "X", part["P_pantry_N"]["far"] - part["P_block_S"]["far"], "pantry and closet together"),
        ("7'-3\"", "Y", part["P_block_W"]["near"] - part["P_laundry_E"]["near"], "the closet and laundry block"),
        ("3'-2\"", "Y", part["P_laundry_W"]["far"] - part["P_laundry_E"]["near"], "the laundry"),
        ("5'-2\"", "Y", part["P_block_W"]["near"] - part["P_bath_W"]["far"], "P_bath_W's kitchen face to P_block_W's living face"),
        ("3'-9\"", "Y", part["P_laundry_E"]["near"] - stud, "the rear wall's inside face to P_laundry_E"),
    ]
    wrong = []
    for raw, axis, got, what in reads:
        want = float(parse_length(raw))
        if raw not in strings:
            wrong.append(f"{raw} is not one of the recorded strings")
            continue
        if strings[raw] != axis:
            wrong.append(f"{raw} ({what}) is read along {axis}, but the string records runs_along: {strings[raw]}")
        if not close(got, want):
            wrong.append(f"{raw} ({what}) computes to {got:.4f}, not {want:.4f}")
    gate(not wrong, "the partition faces follow from the interior strings", "; ".join(wrong))

    rooms = spec["interior_partitions"]["rooms"]
    gate(all(isinstance(r, str) and r.count("(") == r.count(")") and r.strip() for r in rooms),
         "every room name is one whole tag (a list split at its commas leaves an unbalanced parenthesis)",
         "; ".join(map(repr, rooms)))

    x_in = (stud, float(width) - stud)
    y_in = (stud, float(depth) - stud)
    outside = []
    for pid, r in part.items():
        across, along = (y_in, x_in) if r["runs_along"] == "X" else (x_in, y_in)
        if not (across[0] - TOL <= r["lo"] and r["hi"] <= across[1] + TOL):
            outside.append(f"{pid} across {r['lo']:.4f}..{r['hi']:.4f}")
        if not (along[0] - TOL <= min(r["a"], r["b"]) and max(r["a"], r["b"]) <= along[1] + TOL):
            outside.append(f"{pid} along {r['a']:.4f}..{r['b']:.4f}")
    gate(not outside, "every partition lies inside the envelope", ", ".join(outside))

    def rect(r):
        a, b = min(r["a"], r["b"]), max(r["a"], r["b"])
        return (a, b, r["lo"], r["hi"]) if r["runs_along"] == "X" else (r["lo"], r["hi"], a, b)

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
    gate(not over, "no partition runs through another (a junction is at most one thickness)", ", ".join(over))

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

    placed = {str(r["type"]) for r in by_id.values() if str(r["type"]) in doors}
    placed |= {str(d["type"]) for d in layout["door_openings"]}
    optional = {m for m, d in doors.items() if d.get("option")}
    missing = sorted(set(doors) - placed - optional)
    gate(not missing, "every row of the door schedule is built or recorded as an option",
         "not placed: " + ", ".join(missing))

    # ── the roof's arithmetic ─────────────────────────────────────────────
    roof, lv = spec["roof"], spec["levels"]
    plate = float(lv["top_of_plate"]["ft"])
    top = float(lv["top_of_roof"]["ft"])
    half = float(depth) / 2
    main = roof["main"]
    slope = main["slope"]["rise_in"] / main["slope"]["run_in"]
    rise = half * slope
    left = top - plate - rise
    gate(close(main["ridge_at_y"]["ft"], half, 0.0001),
         "the main ridge is at mid-depth", f"{main['ridge_at_y']['ft']} vs {half:.4f}")
    gate(close(roof["heel"]["unexplained_in"], left * 12, 0.05),
         "the heel's unexplained height is top of roof less the plate less the main slope's rise",
         f"spec says {roof['heel']['unexplained_in']} in, arithmetic gives {left * 12:.2f} in")
    gate(0 <= left <= 1.5,
         "the unexplained heel is a plausible truss heel plus roofing (0 to 18 inches), not a wrong slope",
         f"{left * 12:.2f} in")
    porch = roof["porch"]
    pslope = porch["slope"]["rise_in"] / porch["slope"]["run_in"]
    span_ft = float(width) + 2 * float(main["overhangs"]["rakes"]["ft"])
    gate(close(porch["side_eaves"]["ft"], main["overhangs"]["rakes"]["ft"]),
         "the porch roof's side eaves are the main roof's rakes (the front elevation draws them as one width)")
    porch_rise = span_ft / 2 * pslope
    junction = half - (top - plate - porch_rise) / slope
    gate(close(porch["junction_depth"]["ft"], junction, 0.01),
         "the porch roof meets the main roof where the two slopes are level, as derived",
         f"spec {porch['junction_depth']['ft']} vs arithmetic {junction:.4f}")
    gate(0 < junction < half,
         "the porch ridge meets the main roof's front slope (not above its ridge, not in front of the wall)",
         f"{junction:.4f} ft")
    # the porch's structure (#172 builds the posts and beam from these, with no literals)
    posts = porch["posts"]
    strings = [float(parse_length(x)) for x in posts["spacing"]["strings"]]
    gate(close(sum(strings), width),
         "the porch posts' spacing strings sum to the front wall's width", f"{sum(strings):.4f} vs {float(width)}")
    px = [float(v) for v in posts["x"]["ft"]]
    want = [float(width)]
    for seg in strings:
        want.append(want[-1] - seg)
    gate(posts["count"] == len(px) == len(strings) + 1 and all(close(a, b, 0.0001) for a, b in zip(px, want)),
         "the porch posts' positions follow from their spacing, from grid A, and their count matches",
         f"count {posts['count']}, positions {px}, from the strings {[round(w, 4) for w in want]}")
    setback = float(posts["setback_from_front_wall"]["ft"])
    gate(0 < setback < float(porch["projects"]["ft"]),
         "the porch posts stand inside the porch roof's edge (setback is less than the 5'-0\" the roof projects)",
         f"setback {setback:.4f}, roof projects {float(porch['projects']['ft'])}")
    gate(close(posts["king_post"]["at_x"]["ft"], float(width) / 2),
         "the king post is at the middle of the front wall (the porch ridge)",
         f"{posts['king_post']['at_x']['ft']} vs {float(width) / 2}")
    gate(close(posts["beam"]["top"]["ft"], plate),
         "the porch beam's top is at the plate line, T.P.", f"{posts['beam']['top']['ft']} vs {plate}")
    gate(close(spec["areas_declared"]["studio_sf"]["value"], float(width) * float(depth), 0.01),
         "the envelope's area is the declared 460 sf",
         f"{float(width) * float(depth):.4f} vs {spec['areas_declared']['studio_sf']['value']}")
    c = spec["roof"]["ceiling"]
    gate(c.get("settled") is False and isinstance(c.get("assumed"), str) and c["assumed"].strip()
         and close(c["at"]["ft"], plate),
         "the ceiling is declared an assumption, not a fact, and sits at the plate",
         "settled must be false, `assumed` must say why, `at` must equal T.P.")


def main(argv):
    import yaml
    path = Path(argv[1]) if len(argv) > 1 else HERE / "spec.yaml"
    print("=" * 76)
    print(f"{path.name} -- Willow's spec against itself and the drawings' orientation")
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
        except (KeyError, TypeError, ValueError, IndexError, AttributeError, ArithmeticError, SystemExit) as e:
            gate(False, "the spec has the blocks these gates read", f"{type(e).__name__}: {e}")
    print("-" * 76)
    if FAILED:
        print(f"{len(FAILED)} GATE(S) FAILED")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
