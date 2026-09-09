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
from build_adu import load_spec  # noqa: E402
from verify_lib import inside_mesh, inside_mesh_cases  # noqa: E402

FAILED = []

# Things furniture must not be inside. Deliberately excludes Furn_ itself:
# two bedroom arrangements share the floor on purpose.
STRUCTURAL = ("Wall_", "Part_", "Cab_", "Appl_", "Fix_", "Ladder_", "Rail_",
              "Porch_post", "Found_", "Trim_")


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
    doors = [o for o in bpy.data.objects
             if o.type == "MESH" and o.name.startswith("Door_")]
    blocked = []
    for d in doors:
        cs = [d.matrix_world @ v.co for v in d.data.vertices]
        db = (min(c.x for c in cs), max(c.x for c in cs),
              min(c.y for c in cs), max(c.y for c in cs), 0, 0)
        for a in arrs:
            for pc in a["pieces"]:
                if pc["z0"] > 3.0:        # above head height cannot block
                    continue
                if plan_overlap(piece_box(pc), db):
                    blocked.append(f"{a['id']}.{pc['id']} across {d.name}")
    gate("no furniture stands in a doorway", not blocked,
         f"{len(doors)} doors"
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
    gate("furniture sits between floor and ceiling", not off,
         "0 ft to 8 ft" + (f" — OUTSIDE {off[:3]}" if off else ""))

    print("=" * 100)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 100)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
