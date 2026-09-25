"""
test_plan_ink.py — spec.plan_overlay is what A-1.0 draws (#132).

    python3 -m unittest discover -s models/laurel_a1_460 -p "test_*.py"

The overlay's numbers were measured once off A-1.0's vectors by plan_ink.py.
This measures them again, on every run, so a hand-edited number -- or a
reader that changed -- fails here instead of quietly moving a wall. Needs
pdftocairo and pdftotext (poppler), which CI installs for the harvester.
"""
import shutil
import unittest
from pathlib import Path

import yaml

import plan_ink

HERE = Path(__file__).resolve().parent
FIT_FT = 0.001                 # the recorded values are rounded to 4 places


@unittest.skipUnless(shutil.which("pdftocairo") and shutil.which("pdftotext"),
                     "needs pdftocairo and pdftotext (poppler)")
class PlanInk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spec = yaml.safe_load((HERE / "spec.yaml").read_text())
        cls.segs, cls.marks = plan_ink.segments(plan_ink.svg()), plan_ink.labels()
        cls.parts, cls.doors = plan_ink.measure(cls.spec, plan_ink.stud_lines(cls.segs, cls.marks))
        cls.po = cls.spec["plan_overlay"]

    def test_the_scale_is_the_recorded_one(self):
        """Measured from the ticks the drawing carries, not from constants."""
        self.assertAlmostEqual(plan_ink.frame(self.segs, self.marks)[0], self.po["scale"]["pt_per_ft"], places=3)

    def test_a_page_that_moved_is_refused_not_misread(self):
        """Found by review: the frame was four hard-coded page points, so a
        page shifted by its producer would have been read with a
        consistently wrong origin. Shifted 10 pt, no tick is where the frame
        looks, and it refuses."""
        moved = [((p[0] + 10, p[1]), (q[0] + 10, q[1]), w) for p, q, w in self.segs]
        with self.assertRaises(ValueError):
            plan_ink.frame(moved, self.marks)

    def test_ticks_without_their_label_are_refused(self):
        """Found by review: nothing showed the four ticks were the 19'-2" and
        24'-0" strings' own. Each pair must now have its label centred
        between them. Move the 19'-2" label 20 pt along its string, as if
        the ticks were a neighbour's, and the frame refuses."""
        import dataclasses
        moved = [dataclasses.replace(c, box=(c.box[0] + 20, c.box[1], c.box[2] + 20, c.box[3]))
                 if c.raw.replace(" ", "") == plan_ink.DEPTH_TEXT else c for c in self.marks]
        self.assertNotEqual(moved, self.marks)
        with self.assertRaisesRegex(ValueError, "19'-2"):
            plan_ink.frame(self.segs, moved)

    def test_a_label_of_another_value_does_not_confirm(self):
        """The label must say the string's value: the 24'-0" label's box
        with 23'-0" written in it confirms nothing."""
        import dataclasses
        from fractions import Fraction
        other = [dataclasses.replace(c, feet=Fraction(23)) if c.feet == 24 else c
                 for c in self.marks]
        with self.assertRaisesRegex(ValueError, "24'-0"):
            plan_ink.frame(self.segs, other)

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

    def test_a_space_separated_transform_parses(self):
        """Found by review: SVG allows whitespace between a matrix's numbers,
        and the parser split on commas only."""
        svg = ('<svg xmlns="http://www.w3.org/2000/svg"><path stroke="black" '
               'stroke-width="1" d="M 0 0 L 10 0" transform="matrix(2 0 0 -2 5 7)"/></svg>')
        self.assertEqual(plan_ink.segments(svg), [((5.0, 7.0), (25.0, 7.0), 2.0)])

    def test_a_partition_three_inches_off_is_not_found(self):
        """The reader looks within 3" of the layout, so a layout that has
        drifted further finds no wall -- a failure, never a match."""
        lines = plan_ink.stud_lines(self.segs, self.marks)
        near, far = plan_ink.partition(lines, "X", 11.4583 + 0.5, 11.1667 + 0.5, 11.2917, 17.4583)
        self.assertIsNone(near)


if __name__ == "__main__":
    unittest.main()
