"""
models/laurel_a1_460/test_verify_spec.py — verify_spec.py's gates catch what
they exist for (#128).

    python3 -m unittest discover -s models/laurel_a1_460 -v      (from buyer/3D)

Plain Python; needs PyYAML. Each test breaks a COPY of Laurel's spec in one
way and requires the gate written for that mistake to fail, with no
traceback. The real spec is shown passing every gate. A gate switched off in
verify_spec.py fails its test here, so CI notices, not just a scratch script.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = HERE / "verify_spec.py"
SPEC = HERE / "spec.yaml"


def run(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "spec.yaml"
        path.write_text(text)
        return subprocess.run([sys.executable, str(VERIFY), str(path)], capture_output=True, text=True, timeout=120)


class VerifySpec(unittest.TestCase):

    def broken(self, old, new):
        text = SPEC.read_text()
        self.assertEqual(text.count(old), 1, f"test target not found once in spec.yaml: {old!r}")
        return run(text.replace(old, new))

    def assertGateFails(self, r, label):
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        failed = [line for line in r.stdout.splitlines() if line.startswith("  [FAIL] ")]
        self.assertTrue(any(line[len("  [FAIL] "):].startswith(label) for line in failed),
                        f"expected [FAIL] {label!r}, got:\n{r.stdout}")

    def test_the_real_spec_passes(self):
        r = run(SPEC.read_text())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all gates pass", r.stdout)
        self.assertNotIn("[FAIL]", r.stdout)

    def test_the_front_wall_mirrored(self):
        r = self.broken("{id: W-A1, type: A, x0: 16.4167, x1: 20.4167,", "{id: W-A1, type: A, x0: 3.5833, x1: 7.5833,")
        self.assertGateFails(r, "front openings follow from the string")

    def test_d_moved_to_the_x0_wall(self):
        r = self.broken("{id: W-C1, type: C,", "{id: W-C1, type: D,")
        self.assertGateFails(r, "not mirrored")

    def test_the_sidelite_on_the_x0_side(self):
        r = self.broken("sidelite_x: [13.0, 14.0], leaf_x: [10.0, 13.0],", "sidelite_x: [10.0, 11.0], leaf_x: [11.0, 14.0],")
        self.assertGateFails(r, "door 1's sidelite is on the X 24 side")

    def test_two_openings_overlap(self):
        r = self.broken("x0: 1.5833, x1: 6.5833,", "x0: 1.5833, x1: 9.0,")
        self.assertGateFails(r, "no two openings on a wall overlap")

    def test_an_opening_outside_its_wall(self):
        r = self.broken("x0: 1.5833, x1: 6.5833,", "x0: -1.0, x1: 6.5833,")
        self.assertGateFails(r, "every opening sits inside its wall")

    def test_a_window_count_that_disagrees(self):
        r = self.broken("windows_drawn: {A: 2, B: 2, C: 3,", "windows_drawn: {A: 2, B: 2, C: 2,")
        self.assertGateFails(r, "the drawn window counts match the openings")

    # ── the partition gates (#129) ───────────────────────────────────────

    def test_a_partition_face_that_stops_matching_its_string(self):
        # P_pantry_N moved 6" toward the kitchen: the 6'-6 1/2", 2'-6" and
        # 6'-2" strings no longer measure between the faces they read.
        r = self.broken("      at_ft: 17.1667\n", "      at_ft: 17.6667\n")
        self.assertGateFails(r, "the partition faces follow from the interior strings")

    # ── A-2.0's ink against A-1.0's strings (#130) ───────────────────────

    def test_deleting_the_overlay_block_does_not_delete_its_gate(self):
        """Found by review. The block was reached through .get(), so removing
        it removed the whole cross-sheet check while verify_spec still exited
        0 -- nineteen green gates and no mention of the twentieth."""
        text = SPEC.read_text()
        i = text.index("elevation_overlay:")
        j = text.index("\nwindows:", i)
        r = run(text[:i] + text[j + 1:])
        self.assertGateFails(r, "the spec has the blocks these gates read")

    def test_emptying_the_overlay_block_does_not_skip_its_gate(self):
        """Found by review, after the fix above: an `if ov:` guard still let
        an empty or null block skip the cross-sheet check silently."""
        text = SPEC.read_text()
        i = text.index("elevation_overlay:")
        j = text.index("\nwindows:", i)
        for empty in ("elevation_overlay: {}\n", "elevation_overlay:\n"):
            with self.subTest(block=empty.strip()):
                r = run(text[:i] + empty + text[j + 1:])
                self.assertGateFails(r, "the spec has the blocks these gates read")

    def test_the_elevation_and_the_schedule_disagree_on_a_sill(self):
        """The overlay's whole point: two sheets read independently, compared.
        A sill the elevation draws a foot off the one the schedule gives is a
        question for a human, not something to average away."""
        r = self.broken("window_c_sill: {ft: 4.9881,", "window_c_sill: {ft: 5.9881,")
        self.assertGateFails(r, "A-2.0's drawn geometry agrees with A-1.0's dimension strings")

    def test_the_drawn_roof_sits_below_its_own_plate_label(self):
        # The ink is allowed to sit a fraction below the label it carries --
        # it does, by 0.14" -- but not by half a foot.
        r = self.broken("roof_underside_at_rear_wall:\n      ft: 7.9884",
                        "roof_underside_at_rear_wall:\n      ft: 7.5000")
        self.assertGateFails(r, "A-2.0's drawn geometry agrees with A-1.0's dimension strings")

    def test_the_drawn_overhang_disagrees_with_the_roof_plan(self):
        r = self.broken("    front_overhang:\n      ft: 4.9801",
                        "    front_overhang:\n      ft: 6.0000")
        self.assertGateFails(r, "A-2.0's drawn geometry agrees with A-1.0's dimension strings")

    # ── A-1.0's ink against the layout (#132, P3b) ───────────────────────

    def test_p_block_w_back_where_129_read_it(self):
        """Half an inch toward the rear, where #129 put it. The 5'-2" string
        and the ink both refuse it."""
        r = self.broken("      at_ft: 11.4583\n", "      at_ft: 11.4167\n")
        self.assertGateFails(r, "A-1.0's drawn partitions and interior doors agree with the layout")

    def test_door_2_back_against_the_closet_wall(self):
        """Where #129 put it, 4 1/2" from where A-1.0 draws it."""
        r = self.broken("      a_ft: 6.7478\n      b_ft: 10.7478\n",
                        "      a_ft: 7.125\n      b_ft: 11.125\n")
        self.assertGateFails(r, "A-1.0's drawn partitions and interior doors agree with the layout")

    def test_a_borrowed_trim_value_that_drifts_from_the_barn_cabin(self):
        r = self.broken('  casing_width:\n    ft: 0.2917\n    raw: "3 1/2\\""\n',
                        '  casing_width:\n    ft: 0.3333\n    raw: "4\\""\n')
        self.assertGateFails(r, "the ten borrowed trim values are the barn cabin's, "
                                "each assumed and naming its key")

    def test_a_borrowed_trim_value_claiming_a_laurel_source(self):
        # Confidence does not cross buildings: a value the barn cabin measured
        # is still only assumed on Laurel, whose sheets never measured it.
        r = self.broken('    assumed: "the head band over each opening, borrowed from the barn cabin"\n',
                        '    source: "A-1.0, measured"\n')
        self.assertGateFails(r, "the ten borrowed trim values are the barn cabin's, "
                                "each assumed and naming its key")

    def test_a_casing_reveal_the_skin_no_longer_matches(self):
        r = self.broken('    casing_reveal: {ft: 0.0313, raw: "3/8\\""',
                        '    casing_reveal: {ft: 0.0417, raw: "1/2\\""')
        self.assertGateFails(r, "the stucco reveal is the sheathing skin's cut face, "
                                "at the same thickness")

    def test_an_empty_plan_overlay_does_not_skip_its_gate(self):
        text = SPEC.read_text()
        i = text.index("plan_overlay:")
        j = text.index("\n# ---", i)
        r = run(text[:i] + "plan_overlay: {}\n" + text[j + 1:])
        self.assertGateFails(r, "the spec has the blocks these gates read")

    def test_an_interior_string_that_changes_axis(self):
        # Found by review: the gate compared raw text only, so 7'-3" could be
        # recorded as running along X -- an axis the faces it is read between
        # are not measured on -- and still pass.
        r = self.broken('''{raw: "7'-3\\"",     drawn: "below the CLOSET and W/D", runs_along: Y''',
                        '''{raw: "7'-3\\"",     drawn: "below the CLOSET and W/D", runs_along: X''')
        self.assertGateFails(r, "the partition faces follow from the interior strings")

    def test_a_partition_outside_the_envelope(self):
        r = self.broken("      to_ft: 23.5417\n", "      to_ft: 25.0\n")
        self.assertGateFails(r, "every partition lies inside the envelope")

    def test_one_partition_running_through_another(self):
        # P_laundry_W extended past P_block_W into the living room.
        r = self.broken("      at_ft: 7.6667\n", "      at_ft: 11.25\n")
        self.assertGateFails(r, "no partition runs through another")

    def test_an_interior_door_that_is_not_its_schedule_width(self):
        r = self.broken("      a_ft: 6.7478\n", "      a_ft: 7.7478\n")
        self.assertGateFails(r, "every interior door is its schedule width")

    def test_an_interior_door_outside_its_wall(self):
        r = self.broken("      a_ft: 0.75\n      b_ft: 3.75\n",
                        "      a_ft: 15.0\n      b_ft: 18.0\n")
        self.assertGateFails(r, "every interior door is its schedule width")

    def test_an_interior_door_in_a_wall_that_does_not_exist(self):
        r = self.broken("      in: P_block_S\n", "      in: P_nowhere\n")
        self.assertGateFails(r, "every interior door is its schedule width")

    def test_a_schedule_row_nobody_built(self):
        # Door 4 dropped from the layout: the laundry has no door.
        r = self.broken("      type: \"4\"\n", "      type: \"4x\"\n")
        self.assertGateFails(r, "every row of the door schedule is built")

    def test_a_duplicate_key(self):
        r = self.broken("  end_wall_x24:\n", "  end_wall_x24: {}\n  end_wall_x24:\n")
        self.assertGateFails(r, "no duplicate keys")

    def test_a_missing_block(self):
        r = self.broken("  end_wall_x24:\n", "  end_wall_xtmp:\n")
        self.assertGateFails(r, "the spec has the blocks these gates read")

    def test_malformed_yaml(self):
        # Found by Copilot: a spec YAML cannot parse crashed with a traceback.
        r = run(SPEC.read_text() + "openings: [\n")
        self.assertGateFails(r, "the spec is valid YAML")


if __name__ == "__main__":
    unittest.main()
