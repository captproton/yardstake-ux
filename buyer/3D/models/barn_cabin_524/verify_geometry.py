"""verify_geometry.py — every MEASURED fixture must actually exist as geometry.

The tub/shower was measured in Tier 3a, reproduced its callout better than
almost anything in the spec, had its own passing clearance gate, and was never
built. It slipped because it moved from the BUY list to the BUILD list and
nothing tracked that moving it left it undone.

Spec gates cannot catch that: verify_fixtures checks numbers, and the numbers
were right. Only a check that opens the model and looks for the object can.
"""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_adu import load_spec, ft  # noqa: E402

# fixture id -> the object-name prefix its geometry must appear under
EXPECTED = {
    "tub_shower":   "Fix_tub",
    "toilet":       "Fix_toilet",
    "vanity":       "Cab_",
    "refrigerator": "Appl_",
    "range":        "Appl_",
    "dishwasher":   "Appl_",
    "sink_cabinet": "Cab_",
    "crawl_hole":   "Floor_crawl_hatch",
    "stacked_wd":   "Appl_",
}

FAILED = []


def gate(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")
    if not ok:
        FAILED.append(name)


def main():
    spec = load_spec(HERE / "spec.yaml")
    fx = spec["fixtures"]
    names = [o.name for o in bpy.data.objects if o.type == "MESH"]

    print("=" * 92)
    print("GEOMETRY VERIFICATION — every measured fixture is actually modelled")
    print("=" * 92)

    seen = set()
    for group in ("kitchen", "bath", "laundry", "access"):
        for it in fx[group].get("items", []):
            fid = it.get("id")
            if not fid or "x" not in it:
                continue
            seen.add(fid)
            want = EXPECTED.get(fid)
            if want is None:
                gate(f"{fid} is declared as unmodelled",
                     it.get("not_modelled", False) or it.get("floor_opening", False),
                     "no expected prefix and not flagged unmodelled"
                     if not it.get("floor_opening") else "floor opening")
                continue
            hits = [n for n in names if n.startswith(want)]
            gate(f"{fid} has geometry under {want}*", bool(hits),
                 f"{len(hits)} object(s)" if hits
                 else "MEASURED BUT NEVER BUILT")

    missing = set(EXPECTED) - seen
    gate("every expected id exists in the spec", not missing,
         ", ".join(sorted(missing)) if missing else "all present")

    print("=" * 92)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 92)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
