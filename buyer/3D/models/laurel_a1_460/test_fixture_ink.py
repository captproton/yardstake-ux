"""
test_fixture_ink.py — spec.fixtures.drawn is what A-1.0 draws (#134).

    python3 -m unittest discover -s models/laurel_a1_460 -p "test_*.py"

The fixtures' positions were measured once off A-1.0's vectors by
fixture_ink.py. This measures them again, on every run, so a hand-edited
number -- or a reader that changed -- fails here instead of quietly moving a
fixture. Needs pdftocairo and pdftotext (poppler), which CI installs.
"""
import shutil
import unittest
from pathlib import Path

import yaml

import fixture_ink
import plan_ink

HERE = Path(__file__).resolve().parent
FIT_FT = 0.001                 # the recorded values are rounded to 4 places


@unittest.skipUnless(shutil.which("pdftocairo") and shutil.which("pdftotext"),
                     "needs pdftocairo and pdftotext (poppler)")
class FixtureInk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spec = yaml.safe_load((HERE / "spec.yaml").read_text())
        cls.plan = fixture_ink.Plan(plan_ink.svg(), plan_ink.labels())
        cls.measured = fixture_ink.measure(cls.plan)
        cls.drawn = {k: v for k, v in cls.spec["fixtures"]["drawn"].items() if isinstance(v, dict)}

    def test_every_fixture_is_found_and_recorded(self):
        self.assertEqual(set(self.measured), set(self.drawn))
        for name, bb in self.measured.items():
            with self.subTest(fixture=name):
                self.assertIsNotNone(bb, f"{name}: nothing found in its window")

    def test_every_fixture_is_where_the_spec_records_it(self):
        for name, bb in self.measured.items():
            with self.subTest(fixture=name):
                for axis in ("x", "y"):
                    for got, want in zip(bb[axis], self.drawn[name][axis]):
                        self.assertAlmostEqual(got, want, delta=FIT_FT)

    def test_the_vanity_is_its_label(self):
        """A-1.0 labels it 36" VANITY; the ink is an independent reading of it."""
        x0, x1 = self.measured["vanity"]["x"]
        self.assertAlmostEqual((x1 - x0) * 12, 36.0, delta=0.25)

    def test_a_window_with_nothing_in_it_finds_nothing(self):
        """A fixture that is not there is None, never a guess: the middle of
        the living room holds no fixture."""
        for method in ("rect", "sides", "ink", "circle"):
            with self.subTest(method=method):
                opts = {"min_len": 2.0} if method == "sides" else {}
                self.assertIsNone(fixture_ink.METHODS[method](self.plan, 3.0, 4.0, 3.0, 4.0, **opts))

    def test_a_dashed_outline_closes_only_with_its_gap(self):
        """The dishwasher is drawn dashed. Without the gap allowance there is
        no rectangle there at all, which is why the dishwasher has one."""
        _, x0, x1, y0, y1, _ = fixture_ink.FIXTURES["dishwasher"]
        self.assertIsNone(fixture_ink.rect(self.plan, x0, x1, y0, y1))


if __name__ == "__main__":
    unittest.main()
