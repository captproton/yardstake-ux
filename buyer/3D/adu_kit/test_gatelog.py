"""
test_gatelog.py -- adu_kit/gatelog.py and adu_kit/specread.py, with no Blender (#169).

    python3 -m unittest adu_kit.test_gatelog -v          (from buyer/3D)
"""
import contextlib
import io
import unittest

from adu_kit.gatelog import GateLog
from adu_kit.specread import AXES, DIRECTIONS, axis, sign


def capture(fn, *a):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fn(*a)
    return out.getvalue()


class Log(unittest.TestCase):
    def test_a_pass_prints_one_pass_line_and_records_nothing(self):
        log = GateLog()
        self.assertEqual(capture(log.gate, True, "the walls close"), "  [PASS] the walls close\n")
        self.assertEqual(log.failed, [])

    def test_a_fail_prints_its_detail_and_is_recorded(self):
        log = GateLog()
        self.assertEqual(capture(log.gate, False, "the roof meets the plates", "2 in low"),
                         "  [FAIL] the roof meets the plates -- 2 in low\n")
        self.assertEqual(log.failed, ["the roof meets the plates"])

    def test_detail_is_shown_only_on_a_failure(self):
        """The detail argument is the failure's explanation; a PASS has none to give."""
        self.assertEqual(capture(GateLog().gate, True, "x", "ignored"), "  [PASS] x\n")

    def test_a_fail_with_no_detail_prints_no_dash(self):
        self.assertEqual(capture(GateLog().gate, False, "x"), "  [FAIL] x\n")

    def test_a_skip_is_not_a_pass_and_is_recorded_apart(self):
        log = GateLog()
        self.assertEqual(capture(log.skip, "every opening cut", "built with --no-openings"),
                         "  [SKIP] every opening cut -- built with --no-openings\n")
        self.assertEqual((log.failed, log.skipped), ([], ["every opening cut"]))

    def test_two_logs_do_not_share_state(self):
        a, b = GateLog(), GateLog()
        capture(a.gate, False, "only a")
        self.assertEqual(b.failed, [])

    def test_the_run_gates_contract(self):
        """run_gates.py counts these markers on stdout; the format is load-bearing."""
        import re
        text = capture(GateLog().gate, True, "a") + capture(GateLog().gate, False, "b")
        self.assertEqual(len(re.findall(r"\[PASS\]", text)), 1)
        self.assertEqual(len(re.findall(r"\[FAIL\]", text)), 1)


class SpecRead(unittest.TestCase):
    def test_known_words_pass(self):
        for a in AXES:
            self.assertEqual(axis("P1", a), a)
        for d, v in DIRECTIONS.items():
            self.assertEqual(sign("P1", d), v)

    def test_unknown_words_are_a_readable_failure_naming_who_and_what(self):
        for bad in ("Z", "x", "", None, 0):
            with self.subTest(bad=bad):
                with self.assertRaises(SystemExit) as cm:
                    axis("P_block_W", bad)
                self.assertIn("P_block_W: runs_along is", str(cm.exception))
        for bad in ("north", "+Z", "", None, 1):
            with self.subTest(bad=bad):
                with self.assertRaises(SystemExit) as cm:
                    sign("P_block_W", bad)
                self.assertIn("P_block_W: studs_toward is", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
