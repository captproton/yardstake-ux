"""
verify_geometry.py — every MEASURED fixture must actually exist as geometry.

The tub/shower was measured in Tier 3a, reproduced its callout better than
almost anything in the spec, had its own PASSING clearance gate, and was never
built. Spec gates cannot catch that: verify_fixtures checks numbers, and the
numbers were right. Only a check that opens the model and looks can.

WHY THIS TESTS LOCATION AND NOT NAMES. The first version mapped each fixture to
an object-name prefix. build_adu deliberately groups appliances into shared
meshes — Appl_body, Appl_front, Appl_dark — so "does anything start with Appl_"
returned True for the refrigerator, the range, the dishwasher and the stacked
W/D alike. Six of its ten checks would have passed with only one appliance
built. That is the same defect the gate exists to catch, reproduced inside the
gate: a check that passes without verifying the thing it names.

So it now asks the question that actually matters, and the one that found the
missing tub by hand in the first place: IS THERE ANY NON-STRUCTURAL GEOMETRY
INSIDE THIS FIXTURE'S MEASURED FOOTPRINT, AND WITHIN ITS OWN HEIGHT? Shared
meshes are irrelevant to that, because faces have positions.

    blender --background barn_cabin_524.blend --python verify_geometry.py
"""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec  # noqa: E402

# Structure is not a fixture. Without this, a wall or floor passing through a
# fixture's footprint would satisfy the check on its own.
STRUCTURAL = ("Wall_", "Floor_main", "Floor_bath", "Floor_loft", "Floor_slab",
              "Ceil_", "Roof_", "Trim_", "Part_", "Glazing_", "Door_", "Gable_",
              "Dormer_", "Eave_", "Porch_", "Loft_floor", "Rail_", "Ladder_")

FAILED = []


def gate(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:54s} {detail}")
    if not ok:
        FAILED.append(name)


def vents_built(spec):
    """Every vent A2.0 draws must exist as geometry where A2.0 draws it.

    Tested by POSITION, like everything else here: is there a mesh face inside
    the measured opening, at the vent's own height band? Naming Found_vent
    would prove nothing -- the whole point of this file is that one shared mesh
    can satisfy a check for eight things that are not all there.
    """
    fd = spec["foundation"]
    fb = fd["floor_buildup"]
    vt = fd["venting"]
    z_found = -(fb["subfloor"]["ft"] + fb["joist"]["ft"] + fb["mud_sill"]["ft"])
    z1 = z_found - vt["below_foundation"]["ft"]
    z0 = z1 - vt["height"]["ft"]
    vw = vt["width"]["ft"]

    env, con = spec["envelope"], spec["construction"]
    W = env["main_body_width"]["ft"]
    P = env["porch_depth"]["ft"]
    SY, NY = P, P + env["main_body_depth"]["ft"]
    st = fd["stemwall"]["thickness"]["ft"]

    missing = []
    for o in vt["openings"]:
        wall, c = o["wall"], o["at"]["ft"]
        if wall in ("north", "south"):
            bx = (c - vw / 2, c + vw / 2)
            by = (NY - st, NY) if wall == "north" else (SY, SY + st)
        else:
            by = (NY - c - vw / 2, NY - c + vw / 2)
            bx = (0.0, st) if wall == "west" else (W - st, W)

        hit = False
        for ob in bpy.data.objects:
            if ob.type != "MESH":
                continue
            for poly in ob.data.polygons:
                q = ob.matrix_world @ poly.center
                if (bx[0] <= q.x <= bx[1] and by[0] <= q.y <= by[1]
                        and z0 - 0.01 <= q.z <= z1 + 0.01):
                    hit = True
                    break
            if hit:
                break
        if not hit:
            missing.append(f"{wall}@{c:.2f}")
    return missing


def envelope_gap(spec, probes=24):
    """The tallest vertical gap in the perimeter, from footing to finished floor.

    Replacing Floor_slab with a real foundation left the whole floor build-up
    -- subfloor, joists and mud sill -- as EMPTY AIR: walls started at Z=0, the
    stemwall stopped at the top of foundation, and the building floated over
    its own footing. Every gate passed. Spec gates could not see it, because
    every number was right, and the fixture gate could not see it, because
    nothing was missing from a fixture footprint.

    So walk the perimeter, and at each probe collect the Z spans of every
    structural box that covers that point. Merge them. Any gap between the top
    of the footing and the finished floor is a hole in the building.
    """
    fd = spec["foundation"]
    fb = fd["floor_buildup"]
    z_found = -(fb["subfloor"]["ft"] + fb["joist"]["ft"] + fb["mud_sill"]["ft"])
    z_foot = z_found - fd["stemwall"]["height"]["ft"]

    env, con = spec["envelope"], spec["construction"]
    W = env["main_body_width"]["ft"]
    P = env["porch_depth"]["ft"]
    SY, NY = P, P + env["main_body_depth"]["ft"]
    t = con["exterior_wall_thickness"]["ft"]
    inset = t / 2.0                       # mid-thickness, inside every face

    pts = []
    for i in range(probes):
        f = (i + 0.5) / probes
        pts.append((W * f, SY + inset))   # south wall line
        pts.append((W * f, NY - inset))   # north wall line
        pts.append((inset, SY + (NY - SY) * f))
        pts.append((W - inset, SY + (NY - SY) * f))

    boxes = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith(("Fix_", "Cab_", "Appl_")):
            continue
        cs = [ob.matrix_world @ v.co for v in ob.data.vertices]
        if not cs:
            continue
        boxes.append((min(c.x for c in cs), max(c.x for c in cs),
                      min(c.y for c in cs), max(c.y for c in cs),
                      min(c.z for c in cs), max(c.z for c in cs)))

    worst, where = 0.0, None
    for px, py in pts:
        spans = sorted((z0, z1) for x0, x1, y0, y1, z0, z1 in boxes
                       if x0 <= px <= x1 and y0 <= py <= y1
                       and z1 > z_foot and z0 < 0.0)
        cursor, gap = z_foot, 0.0
        for z0, z1 in spans:
            if z0 - cursor > gap:
                gap, hole = z0 - cursor, (cursor, z0)
            cursor = max(cursor, z1)
        if 0.0 - cursor > gap:
            gap, hole = 0.0 - cursor, (cursor, 0.0)
        if gap > worst:
            worst, where = gap, (px, py, hole)
    return worst, where


def main():
    spec = load_spec(HERE / "spec.yaml")
    fx = spec["fixtures"]
    env, con = spec["envelope"], spec["construction"]
    t = con["exterior_wall_thickness"]["ft"]
    ye = env["main_body_depth"]["ft"] + env["porch_depth"]["ft"] - t   # interior north
    xw = t                                                            # interior west

    meshes = [o for o in bpy.data.objects
              if o.type == "MESH" and not o.name.startswith(STRUCTURAL)]

    print("=" * 96)
    print("GEOMETRY VERIFICATION — every measured fixture is actually modelled")
    print("=" * 96)
    print(f"  checking {len(meshes)} non-structural meshes by POSITION, not by name\n")

    checked = 0
    for group in ("kitchen", "bath", "laundry", "access"):
        for it in fx[group].get("items", []):
            if "x" not in it:
                continue
            fid = it["id"]
            checked += 1

            # A floor opening is a hole, not an object standing in a footprint.
            # It is verified by its hatch instead.
            if it.get("floor_opening"):
                hatch = [o for o in bpy.data.objects
                         if o.name.startswith("Floor_crawl_hatch")]
                gate(f"{fid} (floor opening) has its hatch", bool(hatch),
                     f"{len(hatch)} object(s)" if hatch else "NO HATCH")
                continue

            x0, x1 = xw + it["x"], xw + it["x"] + it["w"]
            y0, y1 = ye - (it["y"] + it["d"]), ye - it["y"]

            # FACE CENTRES, not vertices. A box's vertices all lie ON its
            # boundary, so any inward margin excludes every one of them — the
            # first version of this shrank by 1" and failed the stacked W/D,
            # which was built correctly. A box's top and bottom face centres
            # are strictly inside its own footprint, and an abutting
            # neighbour's centres fall in ITS footprint, not this one.
            #
            # Height matters too: the wall cabinets sit directly above the
            # refrigerator, range and dishwasher, so an unbounded check passed
            # all three on Cab_upper_front. Bound it by the fixture's own
            # height.
            top = it.get("h", 3.0) + 0.10
            found, n = [], 0
            for ob in meshes:
                hits = 0
                for poly in ob.data.polygons:
                    c = ob.matrix_world @ poly.center
                    if x0 <= c.x <= x1 and y0 <= c.y <= y1 and 0.02 < c.z < top:
                        hits += 1
                if hits:
                    found.append(ob.name)
                    n += hits
            gate(f"{fid} has geometry in its measured footprint", bool(found),
                 f"{n} faces across {', '.join(sorted(found)[:3])}"
                 + ("…" if len(found) > 3 else "")
                 if found else "MEASURED BUT NEVER BUILT")

    # EVERY ITEM ACCOUNTED FOR, not "at least one was". The name said EVERY
    # while `checked > 0` said AT LEAST ONE -- so a whole group vanishing from
    # the spec would drop the count from 10 to 9 and still pass, under a name
    # claiming completeness. Found by auditing every gate in this repo for
    # exactly that mismatch after #93's review found four of them.
    #
    # The loop skips items with no `x`, which is legitimate -- an exhaust fan
    # has no footprint -- so the check is that skipping is DELIBERATE: each
    # item is either checked or named here as having no position.
    # AND "EXCUSED" MUST MEAN DECLARED, NOT MERELY ABSENT. The first version of
    # this repair counted every item lacking `x` as legitimately positionless,
    # which is the SAME condition the loop skips on -- so checked + excused
    # equalled declared by construction and the predicate could never fail. A
    # gate that over-claimed, replaced by a gate that cannot fail, is a worse
    # trade: rule 24, in the repair for rule 29. RED-tested by stripping an `x`
    # from the refrigerator, which the tautology version passed.
    #
    # The exemption is now `no_footprint: true` in the spec, so losing an `x`
    # by accident looks different from meaning it.
    excused, skipped = [], []
    for g in ("kitchen", "bath", "laundry", "access"):
        for it in fx[g].get("items", []):
            if "x" in it:
                continue
            (excused if it.get("no_footprint") else skipped).append(f"{g}.{it['id']}")
    declared = [(g, it["id"]) for g in ("kitchen", "bath", "laundry", "access")
                for it in fx[g].get("items", [])]
    positionless = excused
    unaccounted = len(skipped)
    #
    # AND THE NAME STILL HAS TO SAY *DECLARED*. The first attempt at this fix
    # was called "every measured fixture was checked" and it does not verify
    # that: emptying a whole group from the spec drops `declared` and `checked`
    # together, the accounting balances, and it passes. RED-tested exactly so.
    # A gate reading ONE source cannot notice that source shrinking -- rule 29,
    # met inside the repair for it. What it CAN verify is that nothing the spec
    # declares was silently skipped by the loop, so that is what it is called.
    # Catching a spec that lost an entry needs a second source: the built model
    # itself, via the inverse question -- non-structural geometry no fixture
    # claims. That is a real gate and it is not this one.
    gate("every fixture the spec DECLARES was checked or excused",
         unaccounted == 0,
         f"{checked} checked + {len(positionless)} declared no_footprint "
         f"({', '.join(positionless) or 'none'}) = {len(declared)} declared"
         + (f" — SKIPPED WITHOUT SAYING SO: {', '.join(skipped)}"
            if skipped else ""))

    missing = vents_built(spec)
    n = len(spec["foundation"]["venting"]["openings"])
    gate("every vent A2.0 draws exists as geometry", not missing,
         f"{n - len(missing)}/{n} found by position"
         + (f" — MISSING {', '.join(missing)}" if missing else ""))

    gap, where = envelope_gap(spec)
    if where:
        px, py, (h0, h1) = where
        detail = (f"worst {gap * 12:.2f}\" at x={px:.2f} y={py:.2f}, "
                  f"z {h0:.3f}..{h1:.3f}")
    else:
        detail = "no probe found a gap"
    gate("no vertical gap from footing to finished floor", gap < 0.01, detail)

    # ---- the stacked pair must read as a washer and dryer ------------------
    # THE FAILURE MODE IS A CUPBOARD. Before #91 the pair was a body and two
    # blank front panels, geometrically correct and visually nothing -- the
    # same defect the entry door carried for eleven PRs. Two features make a
    # front-load stack legible, so the gate demands exactly those two, ONE PER
    # UNIT, and by position rather than by count: two drums stacked in the
    # wrong half would satisfy any tally.
    fx = spec["fixtures"]
    wd = next(i for i in fx["laundry"]["items"] if i["id"] == "stacked_wd")
    drum = bpy.data.objects.get("Appl_drum")
    dark = bpy.data.objects.get("Appl_dark")
    split = wd["h"] * fx["appliance_form"]["stacked_wd"]["split_share"]["fraction"]
    bad = []
    if drum is None:
        bad.append("Appl_drum missing — the pair has no doors")
    else:
        zs = [(drum.matrix_world @ v.co).z for v in drum.data.vertices]
        lower = [z for z in zs if z < split]
        upper = [z for z in zs if z >= split]
        if not lower:
            bad.append("no drum on the washer")
        if not upper:
            bad.append("no drum on the dryer")
        # A drum is round: its vertical extent must match its width, or a flat
        # panel would pass a test that only asked "is something there".
        for label, s in (("washer", lower), ("dryer", upper)):
            if s:
                want = wd["w"] * fx["appliance_form"]["stacked_wd"]["drum"][
                    "diameter_share"]["fraction"]
                if abs((max(s) - min(s)) - want) > 0.02:
                    bad.append(f"{label} drum is {max(s) - min(s):.3f} ft tall, "
                               f"want {want:.3f}")
    if dark is None:
        # NOT A SILENT SKIP. `if dark is not None` let the whole control-panel
        # half of this gate vanish the moment the object did -- and the object
        # vanishing is precisely the regression worth catching.
        bad.append("Appl_dark missing — the pair has no control panels")
    else:
        # FILTER BY THE SPEC'S OWN FOOTPRINT, using the same datum mapping the
        # loop above uses: `xw + it["x"]`, `ye - it["y"]`. The first version
        # tested x > 8.0, a number true of this layout and of nothing else --
        # move the closet and the gate quietly starts reading the kitchen's
        # dark panels instead, and still passes.
        fx0, fx1 = xw + wd["x"], xw + wd["x"] + wd["w"]
        fy0, fy1 = ye - (wd["y"] + wd["d"]), ye - wd["y"]
        pad = 0.05
        tops = [p.z for p in (dark.matrix_world @ v.co
                              for v in dark.data.vertices)
                if fx0 - pad <= p.x <= fx1 + pad
                and fy0 - pad <= p.y <= fy1 + pad]
        if not tops:
            bad.append("no dark geometry in the stack's footprint at all")
        else:
            # One strip at the top of the washer, one at the top of the stack.
            if not any(abs(z - split) < 0.5 for z in tops):
                bad.append("no control panel on the washer")
            if not any(abs(z - wd["h"]) < 0.05 for z in tops):
                bad.append("no control panel on the dryer")
    gate("the stacked pair reads as a washer and dryer", not bad,
         "a drum and a control panel on each unit" if not bad
         else "; ".join(bad))

    # ---- the closet ships open, on the half the laundry is behind ---------
    # THE FAILURE MODE IS A DOOR IN FRONT OF THE APPLIANCES. `default_state`
    # declares this and build_adu ignored it for eight tiers -- the flag was
    # only honoured on walls running east-west, and the closet wall runs
    # north-south, so the one door the setting exists for never moved.
    # Gated in BOTH directions: a leaf covering the laundry is the state this
    # replaced, and both leaves on one half is what "open" has to mean.
    lay = spec["interior_partitions"]["layout"]
    # No default here either -- the builder now REQUIRES the key, so a gate
    # supplying one would be the same disagreement in the other direction.
    dstate = spec["doors"]["default_state"].get("bypass")
    leaves = [o for o in bpy.data.objects
              if o.name.startswith("Door_D-CLOSET")]
    wy0, wy1 = ye - (wd["y"] + wd["d"]), ye - wd["y"]
    trouble = []
    # A VALUE THIS GATE DOES NOT UNDERSTAND IS A FINDING, NOT A DEFAULT. The
    # first version tested `== "open"` and let everything else fall into the
    # closed branch, so `bypass: opne` would have been checked as though it
    # said closed -- and passed. The gate would then be certifying a state
    # nobody asked for, which is worse than not gating it at all.
    if dstate not in ("open", "closed"):
        trouble.append(f"default_state.bypass is {dstate!r}, not 'open' or "
                       f"'closed' — nothing can verify a state it cannot read")
    elif len(leaves) != 2:
        trouble.append(f"{len(leaves)} closet leaves, expected 2")
    else:
        # AGAINST THE DECLARED HALF, not against "somewhere plausible". The
        # first version compared the two leaves' lower bounds to each other and
        # checked nothing covered the laundry. Both are necessary and neither
        # is sufficient: a stack shifted into an INTERIOR three-foot interval
        # has equal starts, misses the laundry, and covers half the opening --
        # so it passed here AND passed verify_tier1's union, while sitting in
        # neither half of the door. The expected half is now derived from
        # `bypass_reveals` and the D-CLOSET callout, which is a fact the build
        # does not hand this gate.
        dcl = next(d for d in lay["doors"] if d["id"] == "D-CLOSET")
        c, hw = dcl["centre_ft"], dcl["w"] / 2.0
        south = (ye - (c + hw), ye - c)          # lower y
        north = (ye - c, ye - (c - hw))          # upper y
        reveals = spec["doors"].get("bypass_reveals")
        # Revealing the north half means the leaves stack on the south one.
        want = south if reveals == "north" else north
        want_name = "south" if reveals == "north" else "north"

        spans = []
        for o in leaves:
            vs = [o.matrix_world @ v.co for v in o.data.vertices]
            spans.append((min(v.y for v in vs), max(v.y for v in vs)))
        # OVERLAP IN Y IS NOT "BEHIND THE DOOR". The leaves and the laundry
        # were compared on the Y axis alone, and the door is in a NORTH-SOUTH
        # partition -- so the check never asked which SIDE of that partition
        # the appliance stands on. Move `stacked_wd.x` into the bedroom and
        # leave y alone: the overlap still holds and the gate still reports
        # "the laundry is behind one of them". Proved by lesion before fixing.
        #
        # The closet is the space between two partition MESHES, read from the
        # model rather than recomputed from the layout the build used -- the
        # closet's own west wall and the wall the door sits in.
        bath_e = bpy.data.objects.get("Part_P_bath_E")
        bed_w = bpy.data.objects.get("Part_P_bedroom_W")
        if bath_e is None or bed_w is None:
            trouble.append("cannot locate the closet's partitions")
            inside_closet = False
        else:
            west = max((bath_e.matrix_world @ v.co).x
                       for v in bath_e.data.vertices)
            east = min((bed_w.matrix_world @ v.co).x
                       for v in bed_w.data.vertices)
            wx0, wx1 = xw + wd["x"], xw + wd["x"] + wd["w"]
            inside_closet = wx0 >= west - 0.01 and wx1 <= east + 0.01
            if not inside_closet:
                trouble.append(
                    f"the laundry spans x {wx0:.2f}..{wx1:.2f}, outside the "
                    f"closet {west:.2f}..{east:.2f} — a door cannot conceal a "
                    "fixture that is not in the room behind it")
        blocking = [o.name for o, (a, b) in zip(leaves, spans)
                    if inside_closet and a < wy1 - 0.01 and b > wy0 + 0.01]

        if dstate == "open":
            if reveals not in ("north", "south"):
                trouble.append(f"bypass_reveals is {reveals!r}; cannot say "
                               "which half should be covered")
            else:
                for o, s in zip(leaves, spans):
                    if abs(s[0] - want[0]) > 0.02 or abs(s[1] - want[1]) > 0.02:
                        trouble.append(
                            f"{o.name} spans {s[0]:.2f}..{s[1]:.2f}, not the "
                            f"{want_name} half {want[0]:.2f}..{want[1]:.2f}")
                if blocking:
                    trouble.append(f"{', '.join(blocking)} covers the laundry")
        elif dstate == "closed":
            # CLOSED IS BOTH HALVES, not "something is in front of the
            # laundry". A pair stacked ON the laundry half satisfied that and
            # was reported as closed AND as side by side, which is two wrong
            # answers from one weak test.
            # EACH LEAF AGAINST ITS OWN HALF. Testing the combined hull plus
            # "the spans touch" let UNEQUAL leaves pass -- a 4.5 ft leaf beside
            # a 1.5 ft one spans the whole 6 ft opening and touches in the
            # middle, while the builder makes two half-width leaves. The hull
            # is a property of the pair; the invariant is a property of each.
            got = sorted(spans)
            for want_half, name, s in ((south, "south", got[0]),
                                       (north, "north", got[1])):
                if abs(s[0] - want_half[0]) > 0.02 or abs(s[1] - want_half[1]) > 0.02:
                    trouble.append(
                        f"closed leaf spans {s[0]:.2f}..{s[1]:.2f}, not the "
                        f"{name} half {want_half[0]:.2f}..{want_half[1]:.2f}")
            # AND THE CLAIM ABOUT THE LAUNDRY MUST BE CHECKED, NOT ASSERTED.
            # `blocking` was computed here and never read, while the success
            # line said "the laundry is behind one of them". If the fixture
            # ever moves outside the opening the two-half check still passes
            # and this gate goes on making that claim -- a message asserting a
            # relationship nothing verified, which is the class this PR has
            # been chasing for four review passes.
            if not blocking:
                trouble.append("closed leaves cover both halves but NOTHING "
                               "covers the laundry — the fixture is not behind "
                               "this door at all")
    # THE MESSAGE MUST DESCRIBE WHAT WAS VERIFIED. A fixed string read "the
    # washer/dryer is exposed" while the gate correctly verified the CLOSED
    # case; the replacement then hard-coded "stacked south", which is wrong
    # whenever `bypass_reveals` is south. Both are #79's message-vs-predicate
    # drift, and the second one was introduced while fixing the first.
    if trouble:
        detail = "; ".join(trouble)
    elif dstate == "open":
        detail = (f"both leaves on the {want_name} half; the "
                  f"{reveals} half is clear and the washer/dryer is exposed")
    else:
        detail = "leaves cover both halves; the laundry is behind one of them"
    gate(f"the closet bypass honours default_state ({dstate})", not trouble,
         detail)

    print("=" * 96)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 96)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
