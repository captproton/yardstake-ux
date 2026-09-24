"""
test_plan_ink.py — spec.plan_overlay is what A-1.0 draws (#132).

    python3 -m unittest discover -s models/laurel_a1_460 -p "test_*.py"

The overlay's numbers were measured once off A-1.0's vectors by plan_ink.py.
This measures them again, on every run, so a hand-edited number -- or a
reader that changed -- fails here instead of quietly moving a wall. Needs
pdftocairo (poppler), which CI installs for the harvester.
"""
import shutil
import unittest
from pathlib import Path

import yaml

import plan_ink

HERE = Path(__file__).resolve().parent
FIT_FT = 0.001                 # the recorded values are rounded to 4 places


@unittest.skipUnless(shutil.which("pdftocairo"), "needs pdftocairo (poppler)")
class PlanInk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spec = yaml.safe_load((HERE / "spec.yaml").read_text())
        cls.parts, cls.doors = plan_ink.measure(
            cls.spec, plan_ink.stud_lines(plan_ink.segments(plan_ink.svg())))
        cls.po = cls.spec["plan_overlay"]

    def test_the_scale_is_the_recorded_one(self):
        self.assertAlmostEqual(plan_ink.frame()[0], self.po["scale"]["pt_per_ft"], places=4)

    def test_every_face_is_the_recorded_one(self):
        faces = {k: v for k, v in self.po["faces"].items() if k != "source"}
        self.assertEqual(set(faces), set(self.parts))
        for pid, (near, far) in self.parts.items():
            with self.subTest(partition=pid):
                self.assertIsNotNone(near, f"{pid}: no pair of stud faces found")
                self.assertAlmostEqual(near, faces[pid][0], delta=FIT_FT)
                self.assertAlmostEqual(far, faces[pid][1], delta=FIT_FT)

    def test_every_door_centre_is_the_recorded_one(self):
        centres = {k: v for k, v in self.po["door_centres"].items() if k != "source"}
        self.assertEqual(set(centres), set(self.doors))
        for did, centre in self.doors.items():
            with self.subTest(door=did):
                self.assertIsNotNone(centre, f"{did}: no gap found")
                self.assertAlmostEqual(centre, centres[did], delta=FIT_FT)

    def test_a_partition_three_inches_off_is_not_found(self):
        """The reader looks within 3" of the layout, so a layout that has
        drifted further finds no wall -- a failure, never a match."""
        lines = plan_ink.stud_lines(plan_ink.segments(plan_ink.svg()))
        near, far = plan_ink.partition(lines, "X", 11.4583 + 0.5, 11.1667 + 0.5, 11.2917, 17.4583)
        self.assertIsNone(near)


if __name__ == "__main__":
    unittest.main()
