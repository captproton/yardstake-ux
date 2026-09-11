"""
verify_furniture.py — furniture is not measured, so it needs different gates.

Every other verify file asks "does the model match the sheet?". That question
is meaningless here: the plan set specifies no furniture at all, and
spec.fixtures.furniture says so at length. What CAN be checked is that the
furniture does not lie about itself and does not foul the things that ARE
measured.

THE GATE THAT MATTERS MOST IS `arrangements are separate meshes`. build_adu
merges by material across the whole building -- multibox("Appl_body", ...) is
one mesh holding the fridge, the range, the dishwasher and the bedroom-closet
washer/dryer. Furniture merged that way could never be switched, because you
cannot hide half a mesh, and the presence-swap work (#76) would have to rebuild
it. That property is invisible in a render and cheap to lose in a refactor.

    blender --background barn_cabin_524.blend --python verify_furniture.py
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec, ft  # noqa: E402
from verify_lib import inside_mesh, inside_mesh_cases  # noqa: E402

FAILED = []

# Things furniture must not be inside. Deliberately excludes Furn_ itself:
# two bedroom arrangements share the floor on purpose.
STRUCTURAL = ("Wall_", "Part_", "Cab_", "Appl_", "Fix_", "Ladder_", "Rail_",
              "Ledger_", "Porch_post", "Found_", "Trim_")


def gate(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:56s} {detail}")
    if not ok:
        FAILED.append(name)


def piece_box(pc):
    return (pc["x0"], pc["x1"], pc["y0"], pc["y1"], pc["z0"], pc["z1"])


def samples(box, inset=0.03):
    """Centre plus the eight corners, pulled just inside the surface."""
    x0, x1, y0, y1, z0, z1 = box
    xs = (x0 + inset, x1 - inset)
    ys = (y0 + inset, y1 - inset)
    zs = (z0 + inset, z1 - inset)
    pts = [Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))]
    pts += [Vector((x, y, z)) for x in xs for y in ys for z in zs]
    return pts


def plan_overlap(a, b, pad=0.0):
    return (a[0] < b[1] + pad and b[0] < a[1] + pad
            and a[2] < b[3] + pad and b[2] < a[3] + pad)


def main():
    spec = load_spec(HERE / "spec.yaml")
    fx = spec["fixtures"]["furniture"]
    arrs = fx["arrangements"]

    print("=" * 100)
    print("FURNITURE — not measured, so gated on self-consistency and clearance")
    print("=" * 100)

    furn = [o for o in bpy.data.objects
            if o.type == "MESH" and o.name.startswith("Furn_")]
    gate("furniture was built at all", bool(furn), f"{len(furn)} meshes")

    # ---- 1. one default per room -----------------------------------------
    rooms = {}
    for a in arrs:
        rooms.setdefault(a["room"], []).append(bool(a.get("default")))
    bad = {r: sum(d) for r, d in rooms.items() if sum(d) != 1}
    gate("exactly one default arrangement per room", not bad,
         ", ".join(f"{r}={sum(d)}" for r, d in sorted(rooms.items()))
         + (f" — WRONG {bad}" if bad else ""))

    # ---- 1a. the shared helper, against known answers --------------------
    # inside_mesh is now in verify_lib and used by two gate files. A shared
    # helper with one home needs a test with one home: these cases pin the
    # behaviour that a bounding box alone gets wrong (a point inside a merged
    # mesh's box but in open floor) and the behaviour that a nearest-surface
    # test alone gets wrong (a point far outside an open shell).
    cases = inside_mesh_cases()
    wrong = []
    for name, pt, expect, why in cases:
        ob = bpy.data.objects.get(name)
        if ob is None:
            wrong.append(f"{name} missing")
            continue
        if inside_mesh(ob, pt) != expect:
            wrong.append(f"{name} @ {tuple(round(v, 2) for v in pt)}: "
                         f"expected {expect} ({why})")
    gate("inside_mesh agrees with its known answers", not wrong,
         f"{len(cases)} cases"
         + (f" — WRONG {wrong}" if wrong else ""))

    # ---- 1b. the two declarations of "default" must agree ----------------
    # There are now two: fixtures.furniture.arrangements[].default decides what
    # the viewable .blend shows, and variants.presence options[].default is
    # what the RUNTIME reads on first load. Nothing stops them drifting, and a
    # drift would mean Blender and the browser disagree about the same model.
    pres = spec.get("variants", {}).get("presence")
    if pres:
        spec_default = {a["room"]: a["id"] for a in arrs if a.get("default")}
        run_default = {}
        for st in pres["sets"]:
            for o in st["options"]:
                if o.get("default"):
                    run_default[st["room"]] = o.get("arrangement")
        gate("the blend default and the runtime default agree",
             spec_default == run_default,
             f"{spec_default}"
             + ("" if spec_default == run_default else f" vs runtime {run_default}"))

        # TWO DISTINCT FAULTS, REPORTED SEPARATELY. A first version folded
        # them together and an unknown id read as "misplaced", because
        # by_id.get() returns None and None never equals a room — so a typo
        # was reported as a room mismatch and the real cause stayed hidden.
        by_id = {a["id"]: a["room"] for a in arrs}
        named = [(st, o) for st in pres["sets"] for o in st["options"]
                 if o.get("arrangement")]

        unknown = [f"{st['id']}.{o['id']}->{o['arrangement']}"
                   for st, o in named if o["arrangement"] not in by_id]
        gate("every presence option names an arrangement that exists",
             not unknown, f"{len(named)} options naming an arrangement"
             + (f" — UNKNOWN {unknown}" if unknown else ""))

        misplaced = [f"{st['id']}({st['room']}).{o['id']}->{o['arrangement']}"
                     f"[{by_id[o['arrangement']]}]"
                     for st, o in named
                     if o["arrangement"] in by_id
                     and by_id[o["arrangement"]] != st["room"]]
        gate("every presence option names an arrangement in its own room",
             not misplaced, f"{len(pres['sets'])} sets"
             + (f" — MISPLACED {misplaced}" if misplaced else ""))

    # ---- 2. arrangements are separate meshes ------------------------------
    # For each object, every polygon must fall inside one of ITS OWN
    # arrangement's declared pieces. A mesh that merged two arrangements would
    # have polygons outside its own boxes, and this is what protects #76.
    strays = []
    for a in arrs:
        boxes = [piece_box(pc) for pc in a["pieces"]]
        pref = f"Furn_{a['id']}_"
        for ob in (o for o in furn if o.name.startswith(pref)):
            for poly in ob.data.polygons:
                c = ob.matrix_world @ poly.center
                if not any(x0 - 0.01 <= c.x <= x1 + 0.01
                           and y0 - 0.01 <= c.y <= y1 + 0.01
                           and z0 - 0.01 <= c.z <= z1 + 0.01
                           for x0, x1, y0, y1, z0, z1 in boxes):
                    strays.append(f"{ob.name} @ {tuple(round(v, 2) for v in c)}")
                    break
    gate("arrangements are separate meshes, none merged across", not strays,
         f"{len(furn)} meshes, each inside its own arrangement"
         + (f" — STRAY {strays[:2]}" if strays else ""))

    # ---- 3. every arrangement exists as geometry, by position -------------
    missing = []
    for a in arrs:
        found = False
        for pc in a["pieces"]:
            c = Vector(((pc["x0"] + pc["x1"]) / 2, (pc["y0"] + pc["y1"]) / 2,
                        (pc["z0"] + pc["z1"]) / 2))
            for ob in furn:
                if any((ob.matrix_world @ p.center - c).length < 0.6
                       for p in ob.data.polygons):
                    found = True
                    break
            if found:
                break
        if not found:
            missing.append(a["id"])
    gate("every arrangement exists as geometry", not missing,
         f"{len(arrs)} arrangements"
         + (f" — MISSING {missing}" if missing else ""))

    # ---- 4. nothing is inside a fixture or a wall -------------------------
    solids = [o for o in bpy.data.objects
              if o.type == "MESH" and o.name.startswith(STRUCTURAL)]
    clashes = []
    for a in arrs:
        for pc in a["pieces"]:
            for p in samples(piece_box(pc)):
                for ob in solids:
                    if inside_mesh(ob, p):
                        clashes.append(f"{a['id']}.{pc['id']} in {ob.name}")
                        break
                else:
                    continue
                break
    gate("no furniture is inside a fixture, wall or partition", not clashes,
         f"{sum(len(a['pieces']) for a in arrs)} pieces checked"
         + (f" — {len(clashes)} CLASH: {clashes[:3]}" if clashes else ""))

    # ---- 5. no doorway is blocked -----------------------------------------
    # THE DOOR IS NOT THE DOORWAY, and this gate spent its life testing the
    # wrong one. It took each Door_ mesh's bounding box as the opening -- and
    # for the bedroom's 5'-0" DOUBLE POCKET door the leaves live inside the
    # wall, one on each side of the hole: x 10.76-13.26 and 18.26-20.76. The
    # opening is the 5 feet BETWEEN them, x 13.26-18.26, and no Door_ object
    # covers it. A sofa parked across three quarters of that doorway passed.
    #
    # So find the hole instead of the leaf: walk along each partition at door
    # height and ask the solid itself where it stops. A run of not-inside
    # wider than a person is a doorway. That is the wall answering, not the
    # spec's arithmetic being read back (rule 36).
    openings = []
    for w in bpy.data.objects:
        if w.type != "MESH" or not w.name.startswith(("Part_", "Wall_")):
            continue
        cs = [w.matrix_world @ v.co for v in w.data.vertices]
        x0, x1 = min(c.x for c in cs), max(c.x for c in cs)
        y0, y1 = min(c.y for c in cs), max(c.y for c in cs)
        if (x1 - x0) < (y1 - y0):        # only walls that run in X, for now
            continue
        # AT TWO HEIGHTS, BECAUSE A WINDOW IS ALSO A HOLE. Sampling at body
        # height alone called the bedroom's 5'-1" egress window a doorway and
        # failed the bed that is meant to sit under it. A doorway goes to the
        # floor; a window does not. Void at the ankle AND at the body is a
        # door, and nothing else in this building is.
        ym = (y0 + y1) / 2
        run, step = None, 0.05
        x = x0 + step
        while x < x1:
            solid = (inside_mesh(w, Vector((x, ym, 3.0)))
                     or inside_mesh(w, Vector((x, ym, 0.30))))
            if not solid and run is None:
                run = x
            elif solid and run is not None:
                if x - run > 1.5:        # wider than a person: a doorway
                    openings.append((w.name, run, x, y0, y1))
                run = None
            x += step
        if run is not None and x1 - run > 1.5:
            openings.append((w.name, run, x1, y0, y1))

    blocked = []
    reach = circ["min_walkway"]["ft"] if (circ := spec["fixtures"]["furniture"]
                                          .get("circulation")) else 2.5
    for wn, ox0, ox1, oy0, oy1 in openings:
        # the doorway plus the room you need to get through it, both sides
        db = (ox0, ox1, oy0 - reach, oy1 + reach, 0, 0)
        for a in arrs:
            for pc in a["pieces"]:
                if pc["z0"] > 3.0:        # above head height cannot block
                    continue
                if plan_overlap(piece_box(pc), db):
                    blocked.append(f"{a['id']}.{pc['id']} blocks the "
                                   f"{(ox1-ox0)*12:.0f}\" opening in {wn}")
    blocked = sorted(set(blocked))
    gate("no furniture stands in a doorway or its approach", not blocked,
         f"{len(openings)} openings found by walking the walls, each kept "
         f"clear by {ft(reach)}"
         + (f" — BLOCKED {blocked[:3]}" if blocked else ""))

    # ---- 5b. nothing is buried in the floor finish ------------------------
    # A piece thinner than the finish, starting at z=0, is INVISIBLE: the floor
    # closes over it. That is how the office rug shipped as nothing at all --
    # 1/2" thick, starting at 0, under a 3/4" finish. No other gate saw it,
    # because Floor_ is not structural for clearance purposes and the
    # floor-to-ceiling gate only asks whether z0 is above zero.
    # The predicate is "does not CLEAR the finish", which includes the
    # exactly-flush case -- a piece whose top sits precisely at the finish
    # surface is coplanar with it and z-fights rather than showing. The
    # message says "does not clear" for that reason: an earlier version read
    # "top 0.0625 < finish 0.0625", which is false on its face and would send
    # a reader looking for a rounding bug that is not there.
    ff = spec["construction"]["floor_finish_thickness"]["ft"]
    buried = [f"{a['id']}.{pc['id']} (top {pc['z1']:.4f} does not clear {ff:.4f})"
              for a in arrs for pc in a["pieces"] if pc["z1"] <= ff + 1e-6]
    gate("no piece is buried inside the floor finish", not buried,
         f"finish is {ff * 12:.2f}\" thick"
         + (f" — {len(buried)} BURIED: {buried[:3]}"
            f"{'…' if len(buried) > 3 else ''}" if buried else ""))

    # ---- 6. everything rests on the floor and clears the ceiling ----------
    off = [f"{a['id']}.{pc['id']}"
           for a in arrs for pc in a["pieces"]
           if pc["z0"] < -0.01 or pc["z1"] > 8.0]
    # ---- circulation: how wide are the gaps? -------------------------------
    # TWELVE GATES ABOVE THIS ONE AND NOT ONE OF THEM ASKED. They check that
    # furniture exists, that it is not inside a wall or a fixture or the
    # floor, that it is not standing in a doorway, that arrangements do not
    # merge. All twelve passed on a sofa with 20 1/2" between its arm and the
    # loft ladder, in a room whose other half was bare floor -- because "not
    # inside anything" and "reachable around" are different questions, and
    # only the first was being asked. verify_fixtures has had real clearance
    # gates since the bath; furniture never got them. #101.
    def bounds(name):
        o = bpy.data.objects[name]
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        return ([min(v[i] for v in vs) for i in range(3)],
                [max(v[i] for v in vs) for i in range(3)])

    circ = spec["fixtures"]["furniture"].get("circulation")
    if circ:
        min_w = circ["min_walkway"]["ft"]
        against = circ["against_it"]["ft"]
        furn_b = {o.name: bounds(o.name) for o in bpy.data.objects
                  if o.type == "MESH" and o.name.startswith("Furn_")}

        # 1. the named runs are the ways through the building. Nothing stands
        #    in them. This is the cheap half and it would NOT have caught the
        #    sofa: it sat beside the run, not in it.
        intruding = []
        for run in circ["runs"]:
            r = (run["x0"], run["x1"], run["y0"], run["y1"])
            for n, b in furn_b.items():
                if (b[0][0] < r[1] - 1e-6 and b[1][0] > r[0] + 1e-6
                        and b[0][1] < r[3] - 1e-6 and b[1][1] > r[2] + 1e-6):
                    intruding.append(f"{n} stands in {run['id']}")
        gate("every declared circulation run is clear of furniture",
             not intruding, "; ".join(intruding) or
             f"{len(circ['runs'])} runs, {len(furn_b)} furniture meshes, none in the way")

        # 2. AND THE THINGS YOU HAVE TO GET TO. This is the half that
        #    matters: the sofa sat BESIDE the run, not in it, so gate 1 would
        #    have passed it.
        #
        #    A gap is either something you walk through, or furniture pushed
        #    up against something. The band between -- too narrow to use, too
        #    wide to be deliberate -- is the defect, and 20 1/2" was squarely
        #    in it.
        #
        #    Measured only against solids the spec NAMES, and only where the
        #    two actually overlap in Z. The first draft asked the general
        #    question of every solid and fired on a bed's linen 2" from the
        #    window casing over it, and on loft trim ten feet above it — both
        #    fine, and a gate that cries about them gets switched off.
        pinch = []
        for tgt in circ.get("keep_clear", []):
            tb = [bounds(o.name) for o in bpy.data.objects
                  if o.type == "MESH" and o.name.startswith(tgt["prefix"])]
            if not tb:
                pinch.append(f"nothing named {tgt['prefix']} to keep clear of")
                continue
            lo = [min(b[0][i] for b in tb) for i in range(3)]
            hi = [max(b[1][i] for b in tb) for i in range(3)]
            for n, b in furn_b.items():
                if b[0][2] >= hi[2] or b[1][2] <= lo[2]:
                    continue                       # never at the same height
                for ax, other in ((0, 1), (1, 0)):
                    if not (b[0][other] < hi[other] - 1e-6
                            and b[1][other] > lo[other] + 1e-6):
                        continue                   # no slot on this axis
                    d = max(lo[ax] - b[1][ax], b[0][ax] - hi[ax])
                    if against < d < tgt["min"]:
                        pinch.append(
                            f"{n} leaves {ft(d)} to the {tgt['id']} — want "
                            f"{ft(tgt['min'])} clear, or hard against it")
        pinch = sorted(set(pinch))
        gate("furniture keeps its distance from what you have to reach",
             not pinch, "; ".join(pinch[:3]) or
             (f"{len(circ.get('keep_clear', []))} named, closest furniture is "
              f"clear" if circ.get("keep_clear") else "nothing declared"))


    gate("furniture sits between floor and ceiling", not off,
         "0 ft to 8 ft" + (f" — OUTSIDE {off[:3]}" if off else ""))

    print("=" * 100)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 100)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
