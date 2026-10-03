"""
test_rectangle.py -- adu_kit/rectangle.py, with no Blender (#172).

    python3 -m unittest adu_kit.test_rectangle -v          (from buyer/3D)
"""
import unittest

from adu_kit.rectangle import partition_band

IT = 0.2917      # a 2x4 interior wall's 3 1/2", as both Laurel's and Willow's specs carry it


class PartitionBand(unittest.TestCase):
    def test_studs_toward_the_plus_side_run_up_from_the_cited_face(self):
        lo, hi = partition_band({"id": "P_bath_W", "at_ft": 6.0, "studs_toward": "+Y"}, IT)
        self.assertEqual((lo, hi), (6.0, 6.0 + IT))

    def test_studs_toward_the_minus_side_run_down_from_it(self):
        lo, hi = partition_band({"id": "P_bath_S", "at_ft": 14.9583, "studs_toward": "-X"}, IT)
        self.assertEqual((lo, hi), (14.9583 - IT, 14.9583))

    def test_the_band_is_always_low_then_high(self):
        for toward in ("+X", "-X", "+Y", "-Y"):
            lo, hi = partition_band({"id": "P", "at_ft": 5.0, "studs_toward": toward}, IT)
            self.assertLess(lo, hi)

    def test_laurels_numbers(self):
        """Known answers from Laurel's layout (its spec, 2026-09), which its own build computes
        the same way: the bath wall's far face and the pantry wall's far face."""
        for got, want in ((partition_band({"id": "P_bath_S", "at_ft": 14.9583, "studs_toward": "-X"}, 0.2917), (14.6666, 14.9583)),
                          (partition_band({"id": "P_pantry_N", "at_ft": 17.1667, "studs_toward": "+X"}, 0.2917), (17.1667, 17.4584))):
            self.assertAlmostEqual(got[0], want[0], places=9)
            self.assertAlmostEqual(got[1], want[1], places=9)

    def test_a_direction_the_spec_cannot_mean_is_a_readable_failure(self):
        for bad in ("north", "X", "+Z", "", None, ["+X"], {"+X": 1}, 1):
            with self.subTest(bad=bad), self.assertRaises(SystemExit) as cm:
                partition_band({"id": "P_x", "at_ft": 1.0, "studs_toward": bad}, IT)
            self.assertIn("studs_toward", str(cm.exception))
            self.assertIn("P_x", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
