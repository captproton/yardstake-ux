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
        r = self.broken("      at_ft: 7.625\n", "      at_ft: 11.25\n")
        self.assertGateFails(r, "no partition runs through another")

    def test_an_interior_door_that_is_not_its_schedule_width(self):
        r = self.broken("      a_ft: 7.125\n", "      a_ft: 8.125\n")
        self.assertGateFails(r, "every interior door is its schedule width")

    def test_an_interior_door_outside_its_wall(self):
        r = self.broken("      a_ft: 0.7083\n      b_ft: 3.7083\n",
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
