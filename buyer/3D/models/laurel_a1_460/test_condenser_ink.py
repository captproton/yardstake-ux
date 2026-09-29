"""
test_condenser_ink.py — spec.fixtures.condenser is what the sheets draw (#134, PR C).

    python3 -m unittest discover -s models/laurel_a1_460 -p "test_*.py"

The condenser was read once off A-1.1 and A-2.0 by condenser_ink.py. This
reads it again, on every run, so the spec cannot drift from the drawings --
and holds the discrepancy the spec records to be still true, so it is
retired the day a revised sheet fixes it rather than believed forever.
Needs pdftocairo and pdftotext (poppler).
"""
import shutil
import unittest
from pathlib import Path

import yaml

import condenser_ink

HERE = Path(__file__).resolve().parent
FIT_FT = 0.001                 # the recorded values are rounded to 4 places


@unittest.skipUnless(shutil.which("pdftocairo") and shutil.which("pdftotext"),
                     "needs pdftocairo and pdftotext (poppler)")
class CondenserInk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spec = yaml.safe_load((HERE / "spec.yaml").read_text())
        cls.c = cls.spec["fixtures"]["condenser"]
        cls.m = condenser_ink.measure()

    def close(self, got, want):
        for g, w in zip(got if isinstance(got, list) else [got], want if isinstance(want, list) else [want]):
            self.assertAlmostEqual(g, w, delta=FIT_FT)

    def test_the_plan_reading_is_the_recorded_one(self):
        for axis in ("x", "y"):
            with self.subTest(axis=axis):
                self.close(self.m["plan"][axis], self.c["plan"][axis])

    def test_the_side_elevation_reading_is_the_recorded_one(self):
        for key in ("y", "base", "top", "grade"):
            with self.subTest(key=key):
                self.close(self.m["side"][key], self.c["side_elevation"][key])

    def test_the_rear_elevation_reading_is_the_recorded_one(self):
        self.close(self.m["rear"]["x"], self.c["rear_elevation"]["x"])

    def test_a_11_is_a_10s_plan_shifted(self):
        """The offset is proved on many lines, not assumed from one circle."""
        self.assertGreaterEqual(self.m["a11"]["lines_matched"], condenser_ink.OFFSET_MIN_MATCH)

    def test_a_20s_scale_agrees_with_a_10s(self):
        """Solved independently from two elevations' outlines; A-1.0's plot
        scale is 17.9875 pt/ft (spec.plan_overlay)."""
        a10 = self.spec["plan_overlay"]["scale"]["pt_per_ft"]
        self.assertAlmostEqual(self.m["a20"]["pt_per_ft"] / a10, 1.0, delta=0.002)

    def test_the_discrepancy_is_still_true(self):
        """The spec says the rear elevation puts it on the wrong wall: A-1.1
        draws it outside the X 24 wall, the rear elevation within the rear
        wall's span. If a revised sheet agrees, this fails and the
        discrepancy is retired."""
        W = self.spec["envelope"]["width"]["ft"]
        self.assertGreaterEqual(self.m["plan"]["x"][0], W)
        self.assertLess(self.m["rear"]["x"][1], W)

    def test_the_plan_and_the_side_elevation_draw_one_size(self):
        """Both 20 inches: the plan across, the elevation along and up."""
        px, py = self.m["plan"]["x"], self.m["plan"]["y"]
        sy = self.m["side"]["y"]
        for span in (px[1] - px[0], py[1] - py[0], sy[1] - sy[0],
                     self.m["side"]["top"] - self.m["side"]["base"]):
            self.assertAlmostEqual(span * 12, 20.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
