"""
test_canopy_ink.py — spec.variants.canopy is what the sheets draw (#144).

    python3 -m unittest discover -s models/laurel_a1_460 -p "test_*.py"

The canopy was read once off A-3.4 and A-2.0 by canopy_ink.py. This reads it
again, on every run, so the spec cannot drift from the drawings; holds the
four drawings to one another where they overlap; and holds the discrepancy
the spec records to be still true, so it is retired the day a revised sheet
fixes it rather than believed forever. Needs pdftocairo and pdftotext.
"""
import shutil
import unittest
from pathlib import Path

import yaml

import canopy_ink

HERE = Path(__file__).resolve().parent
FIT_FT = 0.001                 # the recorded values are rounded to 4 places
INCH = 1 / 12


@unittest.skipUnless(shutil.which("pdftocairo") and shutil.which("pdftotext"),
                     "needs pdftocairo and pdftotext (poppler)")
class CanopyInk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spec = yaml.safe_load((HERE / "spec.yaml").read_text())
        cls.c = cls.spec["variants"]["canopy"]
        cls.m = canopy_ink.measure()
        cls.tol = cls.c["tolerance_in"]["value"] * INCH

    def close(self, got, want):
        # equal lengths first: zip would stop at the shorter and pass
        got = got if isinstance(got, list) else [got]
        want = want if isinstance(want, list) else [want]
        self.assertEqual(len(got), len(want), f"measured {got}, recorded {want}")
        for g, w in zip(got, want):
            if isinstance(g, list):
                self.close(g, w)
            else:
                self.assertAlmostEqual(g, w, delta=FIT_FT)

    def test_each_reading_is_the_recorded_one(self):
        for key, block in (("plan", "a34_plan"), ("section", "a34_section"),
                           ("front", "front_elevation"), ("side", "side_elevation")):
            for field, got in self.m[key].items():
                with self.subTest(drawing=block, field=field):
                    self.close(got, self.c[block][field])

    def test_a_34s_strings_dimension_what_its_drawings_draw(self):
        """The 6'-6" and 2'-6" are the frame's outer faces, which proves each
        drawing's scale; the section draws the 2x6 the spec builds."""
        self.assertAlmostEqual(self.m["plan"]["width"], self.c["width"]["ft"], delta=self.tol)
        for view in ("plan", "section"):
            with self.subTest(view=view):
                self.assertAlmostEqual(self.m[view]["projection"], self.c["projection"]["ft"], delta=self.tol)
        self.assertAlmostEqual(self.m["section"]["depth"], self.c["depth"]["ft"], delta=FIT_FT)

    def test_the_elevations_agree_with_a_34_and_each_other(self):
        """Four drawings, one canopy: A-2.0's front width and side projection
        are A-3.4's, and its two elevations put it at one height."""
        fx = self.m["front"]["x"]
        self.assertAlmostEqual(fx[1] - fx[0], self.c["width"]["ft"], delta=self.tol)
        self.assertAlmostEqual(self.m["side"]["projection"], self.c["projection"]["ft"], delta=self.tol)
        for key in ("underside", "top", "wall_connection"):
            with self.subTest(key=key):
                self.close(self.m["side"][key], self.m["front"][key])

    def test_the_braces_stand_on_the_end_joists(self):
        """Each brace rises from over an end joist: in from the canopy's ends
        by no more than a member, as the side elevation lands it in from the
        outer edge."""
        fx, bx = self.m["front"]["x"], self.m["front"]["brace_x"]
        m = self.m["plan"]["member"]
        for inset in (bx[0] - fx[0], fx[1] - bx[1],
                      self.m["side"]["projection"] - self.m["side"]["brace_lands_from_wall"]):
            with self.subTest(inset=inset):
                self.assertGreater(inset, 0)
                self.assertLessEqual(inset, m + self.tol)

    def test_the_slats_fill_a_bay(self):
        """Seven slats between the header's and the ledger's inner faces."""
        slats, m, proj = self.m["plan"]["slats"], self.m["plan"]["member"], self.m["plan"]["projection"]
        self.assertAlmostEqual(slats[0][0], m, delta=FIT_FT)
        self.assertAlmostEqual(slats[-1][1], proj - m, delta=FIT_FT)
        for (_, a1), (b0, _) in zip(slats, slats[1:]):
            self.assertGreater(b0, a1)

    def test_the_discrepancy_is_still_true(self):
        """The spec says the elevations draw the frame deeper than A-3.4's
        2x6. If a revised sheet agrees with itself, this fails and the
        discrepancy is retired."""
        drawn = self.m["front"]["top"] - self.m["front"]["underside"]
        self.assertGreater(drawn - self.m["section"]["depth"], 2 * INCH)


if __name__ == "__main__":
    unittest.main()
