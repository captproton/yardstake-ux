"""
test_roof.py -- adu_kit/roof.py, with no Blender (#167).

    python3 -m unittest adu_kit.test_roof -v          (from buyer/3D)
"""
import unittest

from adu_kit.roof import (Flat, FollowsRoof, Plane, Roof, RoofError, ceiling_for)

# Laurel's numbers (A-2.0): T.P. 1 at the rear, T.P. 2 at the front, a 19'-2" depth,
# 1'-6" rear and end overhangs, a 5'-0" front overhang, a 24'-0" width.
REAR, FRONT, DEPTH, WIDTH = 8.0, 9.625, 19.1667, 24.0
OV_REAR, OV_FRONT, OV_ENDS = 1.5, 5.0, 1.5


def laurel():
    slope = (FRONT - REAR) / DEPTH
    return Roof([Plane(z0=REAR, dz_dx=0.0, dz_dy=slope,
                       x=(-OV_ENDS, WIDTH + OV_ENDS), y=(-OV_REAR, DEPTH + OV_FRONT))])


class SinglePlane(unittest.TestCase):
    def test_it_reproduces_the_old_shed_arithmetic_bit_for_bit(self):
        """`Shed.under(y)` was `rear + slope * y`. The move to a list of planes is
        only safe if every value is the SAME float, not an approximation."""
        slope = (FRONT - REAR) / DEPTH
        roof = laurel()
        for i in range(-15, 250):
            y = i / 10.0
            if -OV_REAR <= y <= DEPTH + OV_FRONT:
                self.assertEqual(roof.under_y(y), REAR + slope * y, f"y={y}")

    def test_at_the_plates(self):
        roof = laurel()
        self.assertEqual(roof.under_y(0.0), REAR)
        self.assertAlmostEqual(roof.under_y(DEPTH), FRONT, places=12)

    def test_under_xy_agrees_with_under_y_for_an_x_independent_plane(self):
        roof = laurel()
        for x in (-1.0, 0.0, 12.0, 24.0):
            for y in (0.0, 5.0, DEPTH):
                self.assertEqual(roof.under(x, y), roof.under_y(y))

    def test_the_solid_profile_is_the_one_laurel_was_built_with(self):
        asm = 0.1
        (profile, x0, x1), = laurel().yz_solids(asm)
        y0, y1 = -OV_REAR, DEPTH + OV_FRONT
        slope = (FRONT - REAR) / DEPTH
        u = lambda y: REAR + slope * y
        self.assertEqual(profile, [(y0, u(y0)), (y1, u(y1)), (y1, u(y1) + asm), (y0, u(y0) + asm)])
        self.assertEqual((x0, x1), (-OV_ENDS, WIDTH + OV_ENDS))

    def test_extent(self):
        self.assertEqual(laurel().extent(),
                         ((-OV_ENDS, WIDTH + OV_ENDS), (-OV_REAR, DEPTH + OV_FRONT)))

    def test_covers_y_says_whether_there_is_any_roof_there(self):
        """A gate asking "is this below the roof?" must be able to ask whether there IS
        a roof first. Found by the probe suite: a condenser placed 2.7 ft behind the
        rear wall is past the 1.5 ft overhang, and the old unbounded Shed extrapolated
        a roof height there; the plane refuses, and the gate must not crash."""
        roof = laurel()
        self.assertTrue(roof.covers_y(0.0))
        self.assertTrue(roof.covers_y(-OV_REAR))
        self.assertTrue(roof.covers_y(DEPTH + OV_FRONT))
        self.assertFalse(roof.covers_y(-2.667799949645996))
        self.assertFalse(roof.covers_y(DEPTH + OV_FRONT + 0.001))
        for c in (FollowsRoof(roof),):
            self.assertEqual(c.covers_y(-2.667799949645996), False)
            self.assertEqual(c.covers_y(5.0), True)
        self.assertTrue(Flat(8.0).covers_y(-99.0))

    def test_a_point_outside_the_plane_is_an_error_not_a_guess(self):
        roof = laurel()
        for y in (-OV_REAR - 0.01, DEPTH + OV_FRONT + 0.01):
            with self.assertRaises(RoofError):
                roof.under_y(y)
        with self.assertRaises(RoofError):
            roof.under(WIDTH + OV_ENDS + 1, 5.0)


class TwoPlanes(unittest.TestCase):
    """Synthetic, and shaped like Willow's preflight (a main gable and a porch gable).
    Only the interface is exercised; the real geometry is the Willow build's (#172)."""

    def gable(self):
        # a main gable whose ridge runs along X: two planes that fall away in Y
        rise = 5 / 12.0
        mid = 9.5
        return Roof([
            Plane(z0=8.0, dz_dx=0.0, dz_dy=rise, x=(0.0, 24.0), y=(0.0, mid)),
            Plane(z0=8.0 + rise * mid * 2, dz_dx=0.0, dz_dy=-rise, x=(0.0, 24.0), y=(mid, 19.0)),
        ])

    def test_each_plane_answers_inside_its_own_extent(self):
        g = self.gable()
        self.assertAlmostEqual(g.under_y(0.0), 8.0)
        self.assertAlmostEqual(g.under_y(19.0), 8.0, places=9)
        self.assertGreater(g.under_y(9.0), 8.0)

    def test_where_planes_overlap_the_lower_underside_wins(self):
        low = Plane(z0=8.0, dz_dx=0.0, dz_dy=0.0, x=(0.0, 10.0), y=(0.0, 10.0))
        high = Plane(z0=10.0, dz_dx=0.0, dz_dy=0.0, x=(0.0, 10.0), y=(0.0, 10.0))
        self.assertEqual(Roof([high, low]).under(5.0, 5.0), 8.0)
        self.assertEqual(Roof([low, high]).under_y(5.0), 8.0)

    def test_a_roof_with_a_plane_that_slopes_in_x_refuses_under_y(self):
        """The guard: a builder that draws every wall as a YZ profile cannot silently
        accept a porch gable that falls away in X."""
        porch = Plane(z0=8.0, dz_dx=0.25, dz_dy=0.0, x=(0.0, 10.0), y=(19.0, 24.0))
        roof = Roof([self.gable().planes[0], porch])
        with self.assertRaises(RoofError):
            roof.under_y(5.0)
        with self.assertRaises(RoofError):
            roof.yz_solids(0.1)
        self.assertEqual(roof.under(5.0, 5.0), self.gable().planes[0].under(5.0, 5.0))

    def test_flat_planes_at_different_heights_side_by_side_in_x_refuse_under_y(self):
        """Review of #176: both planes are X-flat, so "does not slope in X" passes, yet
        one height is wrong for half the span. under() knows the truth; under_y()
        must refuse rather than return the lower one."""
        left = Plane(z0=8.0, dz_dx=0.0, dz_dy=0.0, x=(0.0, 10.0), y=(0.0, 10.0))
        right = Plane(z0=10.0, dz_dx=0.0, dz_dy=0.0, x=(10.0, 20.0), y=(0.0, 10.0))
        roof = Roof([left, right])
        self.assertTrue(roof.x_independent)
        self.assertEqual(roof.under(5.0, 5.0), 8.0)
        self.assertEqual(roof.under(15.0, 5.0), 10.0)
        with self.assertRaises(RoofError) as cm:
            roof.under_y(5.0)
        self.assertIn("not one height across X", str(cm.exception))

    def test_a_gap_in_x_refuses_under_y(self):
        a = Plane(z0=8.0, dz_dx=0.0, dz_dy=0.0, x=(0.0, 10.0), y=(0.0, 10.0))
        b = Plane(z0=8.0, dz_dx=0.0, dz_dy=0.0, x=(12.0, 20.0), y=(0.0, 10.0))
        with self.assertRaises(RoofError) as cm:
            Roof([a, b]).under_y(5.0)
        self.assertIn("gap in X", str(cm.exception))

    def test_side_by_side_planes_at_one_height_are_a_valid_profile(self):
        """Not over-refused: pieces of X at the SAME height are one YZ profile."""
        a = Plane(z0=8.0, dz_dx=0.0, dz_dy=0.0, x=(0.0, 10.0), y=(0.0, 10.0))
        b = Plane(z0=8.0, dz_dx=0.0, dz_dy=0.0, x=(10.0, 20.0), y=(0.0, 10.0))
        self.assertEqual(Roof([a, b]).under_y(5.0), 8.0)

    def test_the_planes_of_a_roof_may_differ_across_y(self):
        """A gable's two planes are different heights at different Y, which is fine:
        the guard is about X, not Y."""
        g = self.gable()
        self.assertGreater(g.under_y(9.0), g.under_y(1.0))

    def test_a_point_no_plane_covers_is_an_error(self):
        with self.assertRaises(RoofError):
            self.gable().under(30.0, 5.0)


class Validation(unittest.TestCase):
    def test_a_roof_needs_planes(self):
        with self.assertRaises(RoofError):
            Roof([])
        with self.assertRaises(RoofError):
            Roof(["not a plane"])

    def test_an_extent_must_run_low_to_high(self):
        for bad in (dict(x=(5.0, 5.0), y=(0.0, 1.0)), dict(x=(0.0, 1.0), y=(2.0, 1.0)),
                    dict(x=(0.0,), y=(0.0, 1.0))):
            with self.subTest(bad=bad):
                with self.assertRaises(RoofError):
                    Plane(z0=1.0, dz_dx=0.0, dz_dy=0.0, **bad)


class Ceilings(unittest.TestCase):
    def test_follows_roof_gives_the_roofs_numbers(self):
        roof = laurel()
        ceiling = FollowsRoof(roof)
        for y in (0.0, 7.5, DEPTH):
            self.assertEqual(ceiling.under_y(y), roof.under_y(y))
            self.assertEqual(ceiling.under(3.0, y), roof.under(3.0, y))

    def test_flat_is_one_height_everywhere(self):
        flat = Flat(8.0)
        self.assertEqual(flat.under_y(0.0), 8.0)
        self.assertEqual(flat.under(1.0, 99.0), 8.0)

    def test_the_two_differ_where_a_roof_rises(self):
        """The point of the split: a flat ceiling is not the roof."""
        roof = laurel()
        self.assertNotEqual(Flat(REAR).under_y(DEPTH), FollowsRoof(roof).under_y(DEPTH))

    def test_ceiling_for_reads_the_spec_and_refuses_what_it_does_not_know(self):
        roof = laurel()
        self.assertIsInstance(ceiling_for("roof", roof), FollowsRoof)
        for bad in ("flat", None, 8.0, "", "Roof"):
            with self.subTest(bad=bad):
                with self.assertRaises(RoofError):
                    ceiling_for(bad, roof)


if __name__ == "__main__":
    unittest.main()
