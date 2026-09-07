"""
overlay.py — draw spec.fixtures back onto the A1.1 sheet they were measured from.

    python3 tools/tier3/overlay.py

`verify_fixtures.py` checks the recorded numbers against each other and against
code minimums. That cannot catch a systematic error: a wrong datum or a wrong
scale would satisfy every one of those gates, because they are all relative.
This puts the rectangles back on the drawing, where a bad anchor is obvious at
a glance.

Writes renders/tier3_fixture_overlay.png.
"""
import sys
from pathlib import Path

import yaml
from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from frame import MODEL, TOTAL_DEPTH, WALL, col_px, plan_raster, row_px  # noqa: E402

OUT = MODEL / "renders" / "tier3_fixture_overlay.png"
COLOUR = {"kitchen": (200, 30, 30), "bath": (20, 90, 200),
          "laundry": (0, 140, 60), "access": (170, 100, 0)}


def to_px(x_int, y_int):
    """spec.fixtures datum (x from interior west, y south from interior north)
    -> model feet -> sheet pixels.

    TOTAL_DEPTH comes from frame.py, which reads it from the spec. It was a
    literal 30.0 here, duplicating a dimension the spec already owns.
    """
    return col_px(WALL + x_int), row_px(TOTAL_DEPTH - WALL - y_int)


def main():
    spec = yaml.safe_load((MODEL / "spec.yaml").read_text())
    fx = spec["fixtures"]

    im = plan_raster().convert("RGB")
    d = ImageDraw.Draw(im)

    n = 0
    for group, colour in COLOUR.items():
        for it in fx[group].get("items", []):
            if "x" not in it:
                continue
            c0, r0 = to_px(it["x"], it["y"])
            c1, r1 = to_px(it["x"] + it["w"], it["y"] + it["d"])
            d.rectangle([c0, r0, c1, r1], outline=colour, width=4)
            d.text((c0 + 8, r0 + 6), it["id"], fill=colour)
            n += 1

    im.crop((400, 500, 1000, 1750)).save(OUT)
    print(f"drew {n} fixtures -> {OUT.relative_to(MODEL)}")


if __name__ == "__main__":
    main()
