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

    gate("every measured fixture was checked", checked > 0, f"{checked} fixtures")

    print("=" * 96)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 96)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
