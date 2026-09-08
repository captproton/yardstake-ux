"""
verify_fixtures.py — gates on the Tier 3 fixture footprints, from spec alone.

No geometry exists yet: this pass measured fixtures off A1.1 and wrote them to
`spec.fixtures`. These gates check the NUMBERS, which is the cheapest moment to
catch a bad measurement — before anything is modelled on top of it.

Run it with plain Python; Blender is not needed.

    python3 verify_fixtures.py

The clearance checks are the ones that matter for credibility. The bath is
5'-1" x 8'-0" with a 5'-0" tub, so the clearances there are genuinely tight and
worth asserting rather than assuming. A failing clearance is a finding about
the PLAN, to be recorded in spec.discrepancies — not a licence to nudge
geometry until it fits.
"""
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent

# Datum: x from the interior WEST face, y measured SOUTH from the interior
# NORTH face. Same as interior_partitions.layout and spec.fixtures.datum.
FAILED = []
PASSED = []
MISSING = []


def gate(ok, name, detail=""):
    (PASSED if ok else FAILED).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")


def ftin(v):
    neg, v = v < 0, abs(v)
    ft = int(v)
    e = round((v - ft) * 96)
    if e == 96:
        ft, e = ft + 1, 0
    i, r = divmod(e, 8)
    return f"{'-' if neg else ''}{ft}'-{i}" + (f" {r}/8\"" if r else '"')


def find(seq, fid, what):
    """Look up one entry by id, WITHOUT raising.

    `next(gen)` raises StopIteration and kills the whole script with a bare
    traceback if the id is ever renamed. In verification code that is the wrong
    failure: a gate should report FAIL and let the remaining gates run, so one
    rename does not hide every other result. Callers gate on None.
    """
    for it in seq:
        if it.get("id") == fid:
            return it
    MISSING.append(f"{what} ({fid})")
    return None


def duplicate_keys(text):
    """Mapping keys that appear twice in the spec.

    PyYAML keeps the LAST of a duplicated key and says nothing, so a duplicate
    is a value that is visibly in the file and is not the value the build uses.
    This gate exists because exactly that happened: a second `note:` was added
    under `foundation.grade` and silently shadowed the first.
    """
    class Loader(yaml.SafeLoader):
        pass

    found = []

    def mapping(loader, node, deep=False):
        seen = set()
        for k, _ in node.value:
            key = loader.construct_object(k, deep=deep)
            if key in seen:
                found.append((k.start_mark.line + 1, key))
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    Loader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    yaml.load(text, Loader=Loader)
    return found


def all_items(fx):
    for group in ("kitchen", "bath", "laundry", "access"):
        for it in fx[group].get("items", []):
            if "x" in it:
                yield group, it


def main():
    raw = (HERE / "spec.yaml").read_text()
    dups = duplicate_keys(raw)
    gate(not dups, "no duplicate keys in spec.yaml",
         "; ".join(f"line {ln}: {k!r}" for ln, k in dups) or
         "PyYAML would silently keep the last of any pair")
    spec = yaml.safe_load(raw)
    fx = spec["fixtures"]
    lay = spec["interior_partitions"]["layout"]
    part = {p["id"]: p for p in lay["partitions"]}

    W = spec["envelope"]["main_body_width"]["ft"]
    D = spec["envelope"]["main_body_depth"]["ft"]
    t = spec["construction"]["exterior_wall_thickness"]["ft"]
    int_w, int_d = W - 2 * t, D - 2 * t

    items = list(all_items(fx))
    print("=" * 96)
    print(f"TIER 3 FIXTURE GATES — {len(items)} measured footprints")
    print("=" * 96)

    # 1. Everything is inside the building.
    out = [i["id"] for _, i in items
           if i["x"] < -0.01 or i["y"] < -0.01
           or i["x"] + i["w"] > int_w + 0.01
           or i["y"] + i["d"] > int_d + 0.01]
    gate(not out, "every fixture sits inside the interior envelope",
         f"interior {ftin(int_w)} x {ftin(int_d)}" if not out else f"outside: {out}")

    # 2. No two fixtures overlap. Cheap, and it catches a mis-keyed offset.
    clashes = []
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            p, q = items[a][1], items[b][1]
            ox = min(p["x"] + p["w"], q["x"] + q["w"]) - max(p["x"], q["x"])
            oy = min(p["y"] + p["d"], q["y"] + q["d"]) - max(p["y"], q["y"])
            if ox > 0.02 and oy > 0.02:
                clashes.append(f"{p['id']}/{q['id']} by {ox*12:.1f}x{oy*12:.1f}in")
    gate(not clashes, "no two fixtures overlap",
         "clear" if not clashes else "; ".join(clashes))

    # 3. The tub is an alcove unit: it must fit its alcove, and only just.
    bath_e = part["P_bath_E"]["at_ft"]
    tub = find([i for _, i in items], "tub_shower", "bath fixture")
    slack = bath_e - (tub["x"] + tub["w"]) if tub else None
    gate(tub is not None and -0.02 <= slack <= 0.25, "tub fits the bath alcove",
         f"{ftin(slack)} spare against the bath east wall at {ftin(bath_e)}"
         if tub else "tub_shower not found in spec.fixtures")

    # 4. Kitchen aisle. Measured from the cabinet FRONT, which is exact (a
    #    single drawn line at x = 2.00), not from the appliances that project.
    front = fx["kitchen"]["cabinet_run_depth"]["ft"]
    bed_w = part["P_bedroom_W"]["at_ft"]
    bed_w_to = part["P_bedroom_W"]["to_ft"]
    worst = None
    for _, it in items:
        if it["id"] not in ("refrigerator", "range", "sink_cabinet", "dishwasher"):
            continue
        # the bedroom partition only obstructs north of its own south end
        limit = bed_w if it["y"] < bed_w_to else int_w
        aisle = limit - max(front, it["x"] + it["w"])
        if worst is None or aisle < worst[1]:
            worst = (it["id"], aisle)
    gate(worst is not None and worst[1] >= 3.0, "kitchen aisle >= 36in (NKBA)",
         f"tightest {ftin(worst[1])} at the {worst[0]}" if worst
         else "no kitchen appliances found in spec.fixtures")

    # 5. Clear floor in front of the toilet and the vanity. IRC 307.1 wants 21"
    #    clear in front; NKBA prefers 30".
    for fid, need in (("toilet", 1.75), ("vanity", 1.75)):
        it = find([i for _, i in items], fid, "bath fixture")
        clear = bath_e - (it["x"] + it["w"]) if it else None
        gate(it is not None and clear >= need,
             f"clear floor in front of the {fid} >= 21in",
             ftin(clear) if it else f"{fid} not found in spec.fixtures")

    # 6. Toilet centreline to the nearest obstruction each side: IRC wants 15".
    toilet = find([i for _, i in items], "toilet", "bath fixture")
    ctr = (toilet["y"] + toilet["d"] / 2.0) if toilet else 0.0
    near = []
    for _, it in items:
        if toilet is None or it["id"] == "toilet":
            continue
        if it["x"] > toilet["x"] + toilet["w"]:
            continue
        if it["y"] + it["d"] <= toilet["y"] + 0.01:
            near.append((it["id"], ctr - (it["y"] + it["d"])))
        elif it["y"] >= toilet["y"] + toilet["d"] - 0.01:
            near.append((it["id"], it["y"] - ctr))
    tight = min(near, key=lambda kv: kv[1]) if near else ("none", 99)
    gate(toilet is not None and tight[1] >= 1.25,
         "toilet centreline >= 15in to each side (IRC 307.1)",
         f"tightest {ftin(tight[1])} to the {tight[0]}"
         if toilet else "toilet not found in spec.fixtures")

    # 7. Fixtures land in the room they are filed under.
    wrong = []
    for group, it in items:
        in_bath = (it["x"] < bath_e and it["y"] < part["P_bath_S"]["at_ft"])
        if group == "bath" and not in_bath:
            wrong.append(it["id"])
        if group == "kitchen" and in_bath:
            wrong.append(it["id"])
    gate(not wrong, "each fixture is in the room it is filed under",
         "clear" if not wrong else str(wrong))

    # 8. Heights are declared assumed, without exception. The plan set has no
    #    interior elevations, so a height presented as measured would be false.
    bad = [i["id"] for _, i in items
           if ("h" in i or "z" in i) and i.get("height_confidence") != "assumed"]
    gate(not bad, "every height is labelled assumed, not measured",
         "no interior elevations exist in the set" if not bad else str(bad))

    # 9. Anything checked against a plan callout must actually reproduce it.
    callouts = {"tub_shower": (5.0, 2.667), "crawl_hole": (2.0, 2.0)}
    off = []
    for _, it in items:
        if it["id"] in callouts:
            cw, cd = callouts[it["id"]]
            if abs(it["w"] - cw) > 1 / 12.0 or abs(it["d"] - cd) > 1 / 12.0:
                off.append(f"{it['id']} {ftin(it['w'])}x{ftin(it['d'])} vs callout")
    gate(not off, "callout fixtures reproduce their callout within 1in",
         "tub and crawl hole both" if not off else "; ".join(off))

    # 10. The sink opening must sit inside the cabinet that carries it, and
    #     leave a rim of counter all the way round. A cutout that reaches the
    #     cabinet edge is a counter in two pieces, not a counter with a hole.
    cut = fx["kitchen"]["runs"].get("sink_cutout")
    if cut:
        base = find(fx["kitchen"]["runs"]["base"], "sink_base", "base cabinet run")
        depth = fx["kitchen"]["cabinet_run_depth"]["ft"]
        rim = min(cut["y0"] - base["y0"], base["y1"] - cut["y1"],
                  cut["x0"], depth - cut["x1"]) if base else None
        gate(base is not None and rim >= 1.5 / 12.0,
             "sink cutout leaves a counter rim all round",
             f"tightest {ftin(rim)}" if base
             else "sink_base not found in spec.fixtures.kitchen.runs.base")

        seg = [s for s in fx["kitchen"]["runs"]["counter"]
               if s["y0"] <= cut["y0"] and cut["y1"] <= s["y1"]]
        gate(len(seg) == 1, "sink cutout falls inside exactly one counter run",
             f"{len(seg)} matching run(s)")

        sink = fx["kitchen"]["runs"].get("sink")
        if sink:
            # The tap must stand BEHIND the bowl — between it and the wall —
            # not on the counter's front lip. An earlier version put it in the
            # walkway, which looked merely odd in a render and would have been
            # missed. x is measured from the interior west face, so "behind"
            # means a SMALLER x than the bowl's near edge.
            fa = sink["faucet"]
            fxpos = cut["x0"] - fa["behind_bowl"]["ft"]
            gate(0.0 < fxpos < cut["x0"],
                 "tap stands between the bowl and the wall",
                 f"tap at {ftin(fxpos)}, bowl starts {ftin(cut['x0'])}")

            # And its spout must actually reach over the bowl, or it pours onto
            # the counter.
            spout = fxpos + fa["reach"]["ft"]
            gate(cut["x0"] < spout < cut["x1"],
                 "tap spout lands over the bowl",
                 f"spout at {ftin(spout)}, bowl {ftin(cut['x0'])}..{ftin(cut['x1'])}")

            # The basin hangs below the counter and must clear the cabinet floor.
            depth = sink["basin"]["depth"]["ft"]
            counter_h = fx["kitchen"]["counter_h"]["ft"]
            toe = fx["kitchen"]["toe_kick_h"]["ft"]
            bottom = counter_h - fx["kitchen"]["counter_thk"]["ft"] - depth
            # Report the THRESHOLD, not just the inputs. Saying "carcass starts
            # at 3-1/2" hid the 3" margin actually being enforced, so a failure
            # would have looked like a contradiction rather than a near miss.
            clear = 0.25
            floor_limit = toe + clear
            gate(bottom > floor_limit,
                 "basin bottom clears the cabinet interior",
                 f"basin floor at {ftin(bottom)}, must clear {ftin(floor_limit)} "
                 f"(toe kick {ftin(toe)} + {ftin(clear)})")

        bowl_w, bowl_d = cut["y1"] - cut["y0"], cut["x1"] - cut["x0"]
        gate(1.5 <= bowl_w <= 3.0 and 1.0 <= bowl_d <= 2.0,
             "sink opening is a plausible bowl size",
             f"{ftin(bowl_w)} along the wall x {ftin(bowl_d)} off it")

    # 11. The bath vanity basin and its tap set. Same shape of check as the
    #     kitchen sink, on the fixture that is now the model's only ellipse.
    fit = fx.get("bath_fittings")
    van = find([i for _, i in items], "vanity", "bath fixture")
    if fit and van:
        rim, bowl = fit["basin"]["rim"], fit["basin"]["bowl"]

        # The rim must land inside the vanity top it sits in, on all four sides.
        margins = (
            (rim["cx"] - rim["ax"]) - van["x"],
            (van["x"] + van["w"]) - (rim["cx"] + rim["ax"]),
            (rim["cy"] - rim["ay"]) - van["y"],
            (van["y"] + van["d"]) - (rim["cy"] + rim["ay"]),
        )
        gate(min(margins) > 0.08,
             "basin rim sits inside the vanity top",
             f"tightest margin {ftin(min(margins))}, needs > {ftin(0.08)}")

        # The bowl opening must sit inside the rim, or the top has nothing to
        # lap and a gap opens between counter and basin.
        gate(bowl["ax"] < rim["ax"] and bowl["ay"] < rim["ay"],
             "bowl opening is inside the rim",
             f"bowl {ftin(bowl['ax'] * 2)}x{ftin(bowl['ay'] * 2)}, "
             f"rim {ftin(rim['ax'] * 2)}x{ftin(rim['ay'] * 2)}")

        # Basin depth against the vanity carcass, threshold reported (rule 9).
        vh = van["h"]
        bd = fit["basin"]["depth"]["ft"]
        bw = fit["basin"]["wall"]["ft"]
        toe = fx["kitchen"]["toe_kick_h"]["ft"]
        # Mirror build_adu exactly: the loft's lowest ring is at
        # (vh - depth) - wall. The old formula used vh - counter_thk - depth,
        # which is neither the inner floor nor the outer, and happened to sit
        # BELOW the real mesh -- conservative, so it could not pass wrongly,
        # but it was not measuring the thing it named.
        bottom = vh - bd - bw
        limit = toe + 0.25
        gate(bottom > limit,
             "bath basin bottom clears the vanity interior",
             f"basin floor at {ftin(bottom)}, must clear {ftin(limit)} "
             f"(toe kick {ftin(toe)} + {ftin(0.25)})")

        # The clearance gate above is correct but slack: a 32" vanity only trips
        # it past ~23" of bowl depth, which nothing real approaches. Proving
        # that took perturbing the value until it went red. So assert the
        # plausible range too, which is the check that would actually catch a
        # bad number -- same reasoning as the kitchen's bowl-size gate.
        gate(0.33 <= bd <= 0.83,
             "bath basin depth is a plausible bowl depth",
             f"{ftin(bd)}, expected {ftin(0.33)}..{ftin(0.83)}")

        # Tap set: handles and spout must all land on the rim, behind the bowl.
        f = fit["faucet"]
        pts = [(f["spout"]["x"], f["spout"]["y"], "spout")]
        pts += [(h["x"], h["y"], f"handle {i}") for i, h in enumerate(f["handles"])]
        # "Inside the rim" is not enough: the bowl opening is inside the rim
        # too, so that test passes for a tap mounted over the hole. Every hole
        # must be on the DECK -- inside the rim ellipse AND outside the bowl
        # ellipse. This is what caught the spout mounting at x 0.920, inside a
        # bowl opening spanning 0.720..1.600, rising out of the basin.
        for x, y, label in pts:
            in_rim = (((x - rim["cx"]) / rim["ax"]) ** 2
                      + ((y - rim["cy"]) / rim["ay"]) ** 2) < 1.0
            in_bowl = (((x - bowl["cx"]) / bowl["ax"]) ** 2
                       + ((y - bowl["cy"]) / bowl["ay"]) ** 2) < 1.0
            gate(in_rim and not in_bowl,
                 f"tap {label} mounts on the rim deck",
                 f"at x {ftin(x)} y {ftin(y)}"
                 + ("" if in_rim else " — outside the rim")
                 + (" — OVER THE BOWL OPENING" if in_bowl else ""))

        # Behind the bowl's wall-side EDGE, not merely its centre: half the
        # bowl is on the wall side of the centre.
        edge = bowl["cx"] - bowl["ax"]
        worst = max(x for x, _, _ in pts)
        gate(worst <= edge + 0.01,
             "tap set is behind the bowl's wall-side edge",
             f"furthest tap hole at {ftin(worst)}, bowl edge {ftin(edge)}")

        # And the spout must still REACH over the bowl, or it pours on the deck.
        tip = f["spout"]["x"] + f["reach"]["ft"]
        gate(bowl["cx"] - bowl["ax"] < tip < bowl["cx"] + bowl["ax"],
             "spout tip reaches over the bowl",
             f"tip at {ftin(tip)}, bowl {ftin(bowl['cx']-bowl['ax'])}"
             f"..{ftin(bowl['cx']+bowl['ax'])}")

    # 12. NO FIXTURE MAY BLOCK A DOOR OPENING.
    #     This gate is here because its absence shipped a defect: the bath
    #     vanity sat 7" across the bath doorway and every existing check
    #     passed. The room-assignment gate compares a fixture's ORIGIN corner
    #     against the partition, so anything whose far edge crosses a wall or a
    #     doorway is invisible to it. Extents, not corners.
    parts_by_id = {p["id"]: p for p in lay["partitions"]}
    for door in lay["doors"]:
        wall = parts_by_id.get(door["in"])
        if wall is None:
            MISSING.append(f"partition for door {door['id']} ({door['in']})")
            continue
        lo = door["centre_ft"] - door["w"] / 2.0
        hi = door["centre_ft"] + door["w"] / 2.0
        for group, it in items:
            # A FLOOR OPENING cannot block a door: a door leaf passes over a
            # hatch. The first version of this gate failed the 24"x24" crawl
            # hole against the closet bypass doors, which sit directly above
            # it. That is the plan's own arrangement, both positions are
            # measured, and it is awkward rather than wrong -- recorded in
            # discrepancies as `crawl-hole-under-closet-doors`, not gated here.
            if it.get("floor_opening"):
                continue
            # Only fixtures standing ON this wall can block it.
            along0, along1 = ((it["x"], it["x"] + it["w"]) if wall["axis"] == "x"
                              else (it["y"], it["y"] + it["d"]))
            # Check BOTH edges against the wall, not just the far one. A
            # fixture NORTH of an x-axis wall meets it with its south edge; one
            # SOUTH of the wall meets it with its north edge. Testing only the
            # far edge silently skipped every kitchen fixture against the bath
            # wall -- which is exactly the run that shares it.
            near, far = ((it["y"], it["y"] + it["d"]) if wall["axis"] == "x"
                         else (it["x"], it["x"] + it["w"]))
            if min(abs(near - wall["at_ft"]), abs(far - wall["at_ft"])) > 1.0:
                continue
            overlap = min(along1, hi) - max(along0, lo)
            gate(overlap <= 0.01,
                 f"{it['id']} does not block {door['id']}",
                 f"fixture {ftin(along0)}..{ftin(along1)} vs opening "
                 f"{ftin(lo)}..{ftin(hi)}"
                 + (f" — OVERLAP {ftin(overlap)}" if overlap > 0.01
                    else f", clear by {ftin(-overlap)}"))

    # 13. The toilet's ASSUMED proportions against its MEASURED footprint.
    #     This script reads spec numbers and never opens Blender, so nothing
    #     here inspects built geometry -- the earlier wording said "built form"
    #     and would have misled anyone looking for a mesh check.
    #     The footprint is the only measured thing about this fixture; every
    #     proportion below it is a stock assumption, so the assumptions are
    #     what get checked against the measurement rather than the reverse.
    tf = fx.get("toilet_form")
    wc = find([i for _, i in items], "toilet", "bath fixture")
    if tf and wc:
        tank, bowl = tf["tank"], tf["bowl"]
        gate(tank["width"]["ft"] <= wc["d"] + 0.01,
             "toilet tank fits the measured width",
             f"tank {ftin(tank['width']['ft'])} in {ftin(wc['d'])}")
        gate(2 * bowl["half_width"]["ft"] < tank["width"]["ft"],
             "toilet bowl is narrower than its tank",
             f"bowl {ftin(2 * bowl['half_width']['ft'])}, "
             f"tank {ftin(tank['width']['ft'])}")
        gate(tank["depth"]["ft"] < wc["w"] * 0.5,
             "toilet tank is a minority of the projection",
             f"tank {ftin(tank['depth']['ft'])} of {ftin(wc['w'])}")
        gate(tank["bottom"]["ft"] < wc["seat_h"]["ft"] < wc["h"],
             "toilet tank spans the seat height",
             f"tank {ftin(tank['bottom']['ft'])}..{ftin(wc['h'])}, "
             f"seat {ftin(wc['seat_h']['ft'])}")
        gate(0.0 < bowl["foot_scale"]["factor"] < 1.0,
             "toilet foot is narrower than its bowl",
             f"scale {bowl['foot_scale']['factor']}")

    # 14. Appliance forms against their MEASURED footprints. Same shape of
    #     check as the toilet: the footprint is the measured thing, every
    #     proportion is a stock assumption, so the assumptions are what get
    #     tested against the measurement.
    af = fx.get("appliance_form")
    if af:
        fr = find([i for _, i in items], "refrigerator", "kitchen fixture")
        rg = find([i for _, i in items], "range", "kitchen fixture")
        dw = find([i for _, i in items], "dishwasher", "kitchen fixture")
        pp = af["panel_proud"]["ft"]

        if fr:
            share = af["refrigerator"]["freezer_share"]["fraction"]
            gate(0.2 < share < 0.5, "refrigerator freezer share is plausible",
                 f"{share:.0%} of {ftin(fr['h'])} = {ftin(fr['h'] * share)} freezer")
        if rg:
            g = af["range"]
            stack = (g["door_bottom"]["ft"] + g["handle_h"]["ft"]
                     + g["control_h"]["ft"] + g["cooktop_thk"]["ft"])
            gate(stack < rg["h"], "range front elements fit its height",
                 f"drawer+handle+controls+cooktop {ftin(stack)} in {ftin(rg['h'])}")
            counter_h = fx["kitchen"]["counter_h"]["ft"]
            gate(abs(rg["h"] - counter_h) < 0.05,
                 "range is flush with the counter (slide-in)",
                 f"range {ftin(rg['h'])}, counter {ftin(counter_h)}")
        if dw:
            counter_h = fx["kitchen"]["counter_h"]["ft"]
            top_t = fx["kitchen"]["counter_thk"]["ft"]
            gate(dw["h"] <= counter_h - top_t + 0.01,
                 "dishwasher fits under the counter",
                 f"{ftin(dw['h'])} under {ftin(counter_h - top_t)}")
            gate(af["dishwasher"]["handle_h"]["ft"] < dw["h"] * 0.2,
                 "dishwasher handle strip is a minority of its face",
                 f"{ftin(af['dishwasher']['handle_h']['ft'])} of {ftin(dw['h'])}")
        gate(0.0 < pp < 0.15, "appliance doors stand proud by a plausible amount",
             f"{ftin(pp)}")

    # 15. Foundation venting against A0.0's own note, and the stemwall stack.
    fd = spec.get("foundation")
    if fd:
        env, con = spec["envelope"], spec["construction"]
        t = con["exterior_wall_thickness"]["ft"]
        area = ((env["main_body_width"]["ft"] - 2 * t)
                * (env["main_body_depth"]["ft"] - 2 * t))
        v = fd["venting"]
        # GROSS, not net free area: these are modelled openings with no screen
        # or louver, and a real vent's mesh cuts the free area roughly in half.
        # A0.0 asks for NET free area, so this gate is the weaker test. It
        # still passes by an order of magnitude, which is why it holds.
        gross = v["count"] * v["width"]["ft"] * v["height"]["ft"]
        need = area / 1500.0
        gate(gross >= need,
             "foundation vent GROSS area clears A0.0's net-free requirement",
             f"{gross:.2f} sf gross across {v['count']} vents vs {need:.2f} sf "
             f"net free required — {gross / need:.0f}x, so screen loss is moot")
        gate(v["count"] >= 4, "one vent per corner, per A0.0",
             f"{v['count']} vents; A0.0 wants one within 3 ft of each corner")
        # A0.0: "one such ventilating opening shall be WITHIN 3 FEET of each
        # corner". That locates the opening, not its far edge — a 1'-4" vent
        # starting 2'-0" out is within 3 ft even though it ends at 3'-4". The
        # first version of this gate tested setback + width and failed
        # correct geometry.
        gate(v["corner_setback"]["ft"] <= 3.0 + 0.01,
             "each vent is within 3 ft of its corner",
             f"near edge at {ftin(v['corner_setback']['ft'])}, limit 3'-0\"")

        fb = fd["floor_buildup"]
        z_found = -(fb["subfloor"]["ft"] + fb["joist"]["ft"] + fb["mud_sill"]["ft"])
        z_foot = z_found - fd["stemwall"]["height"]["ft"]
        z_grade = z_found - fd["grade"]["exposed_stemwall"]["ft"]
        gate(z_foot < z_grade < z_found,
             "grade sits between footing and top of foundation",
             f"footing {ftin(z_foot)}, grade {ftin(z_grade)}, "
             f"top of foundation {ftin(z_found)}")
        vz1 = z_found - v["below_foundation"]["ft"]
        # Real clearance, not "at or above": the first version of this gate
        # allowed equality and passed on geometry whose vent bottom sat
        # EXACTLY on grade, which would take water. 4" is a modelling sanity
        # margin, not a code figure -- grade itself is assumed.
        clear = (vz1 - v["height"]["ft"]) - z_grade
        gate(clear >= 4.0 / 12.0,
             "vents clear grade by a real margin",
             f"vent bottom {ftin(vz1 - v['height']['ft'])}, grade "
             f"{ftin(z_grade)}, clearance {ftin(clear)} (want 4\" min)")
        gate(fd["footing"]["width"]["ft"] > fd["stemwall"]["thickness"]["ft"],
             "footing is wider than the stemwall it carries",
             f"{ftin(fd['footing']['width']['ft'])} under "
             f"{ftin(fd['stemwall']['thickness']['ft'])}")

    print("=" * 96)
    if MISSING:
        print("spec entries the gates expected but could not find:")
        for m in MISSING:
            print(f"  - {m}")
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}"
          f"   ({len(PASSED)}/{len(PASSED) + len(FAILED)})")
    print("=" * 96)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
