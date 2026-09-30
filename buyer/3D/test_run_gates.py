"""
test_run_gates.py -- run_gates.py refuses to read a false green.

    python3 -m unittest test_run_gates -v          (from buyer/3D; no Blender needed)
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_gates


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = run_gates.main(list(argv))
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 2
            err.write(str(e.code))
    return code, out.getvalue(), err.getvalue()


class Runner(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "models").mkdir()
        patch = mock.patch.multiple(run_gates, ROOT=self.root, MODELS=self.root / "models")
        patch.start()
        self.addCleanup(patch.stop)

    def shared(self, gates):
        (self.root / "gates.json").write_text(json.dumps({"gates": gates}))

    def ok(self, name="ok", **kw):
        return {"name": name, "tier": "fast", "cmd": ["{python}", "-c", "pass"], **kw}

    def test_a_passing_gate_passes(self):
        self.shared([self.ok()])
        self.assertEqual(run("--tier", "fast")[0], 0)

    def test_a_failing_gate_fails(self):
        self.shared([{"name": "bad", "tier": "fast", "cmd": ["{python}", "-c", "raise SystemExit(3)"]}])
        code, out, _ = run("--tier", "fast")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_a_skipped_gate_fails_unless_allowed(self):
        self.shared([self.ok(requires=["no_such_module_xyz"])])
        code, out, _ = run("--tier", "fast")
        self.assertEqual(code, 1)
        self.assertIn("SKIP", out)
        self.assertEqual(run("--tier", "fast", "--allow-skip")[0], 0)

    def test_a_null_gate_is_a_readable_error_not_a_crash(self):
        self.shared([None])
        code, _, err = run("--tier", "fast")
        self.assertNotEqual(code, 0)
        self.assertIn("must be an object", err)

    def test_a_typoed_filter_is_not_green(self):
        self.shared([self.ok("real")])
        code, out, err = run("--tier", "fast", "-k", "raal")
        self.assertNotEqual(code, 0)
        self.assertIn("nothing was run", err)
        self.assertNotIn("0 passed", out)

    def test_list_of_nothing_is_refused_too(self):
        self.shared([self.ok("real")])
        self.assertNotEqual(run("--tier", "fast", "-k", "raal", "--list")[0], 0)

    def test_a_model_with_a_spec_and_no_gates_file_fails(self):
        self.shared([self.ok()])
        d = self.root / "models" / "m_one"
        d.mkdir()
        (d / "spec.yaml").write_text("meta: {}\n")
        code, out, _ = run("--tier", "fast")
        self.assertEqual(code, 1)
        self.assertIn("no gates.json", out)

    def test_blender_gate_that_prints_no_pass_line_fails(self):
        fake = self.root / "fakeblender"
        fake.write_text("#!/bin/sh\necho nothing\nexit 0\n")
        fake.chmod(0o755)
        d = self.root / "models" / "m_one"
        d.mkdir()
        (d / "gates.json").write_text(json.dumps({"gates": [
            {"name": "b", "tier": "blender", "script": "x.py", "blend": None}]}))
        self.shared([])
        with mock.patch.object(run_gates, "find_blender", return_value=str(fake)):
            code, out, _ = run("--tier", "blender")
        self.assertEqual(code, 1)
        self.assertIn("no PASS line", out)


    def test_a_missing_shared_list_fails(self):
        # no gates.json at the root: every repository-wide check would vanish
        code, out, err = run("--tier", "fast")
        self.assertNotEqual(code, 0)
        self.assertIn("shared gate list is required", err)
        self.assertNotIn("0 passed", out)

    def test_a_wrong_top_level_shape_is_a_readable_error(self):
        for text in ("[]", "null", '"x"', "3", '{"gates": null}', '{"other": []}', "{not json"):
            with self.subTest(text=text):
                (self.root / "gates.json").write_text(text)
                code, _, err = run("--tier", "fast")
                self.assertNotEqual(code, 0)
                self.assertIn("not a gate list", err)

    def test_malformed_gate_fields_are_readable_errors(self):
        for bad in ({"name": "b", "tier": "fast", "cmd": []},
                    {"name": "b", "tier": "fast", "cmd": "python"},
                    {"name": "b", "tier": "fast", "cmd": [1]},
                    {"name": "b", "tier": "fast", "cmd": ["{python}"], "requires": "yaml"},
                    {"name": "b", "tier": "blender", "script": ""},
                    {"name": "b", "tier": "blender", "script": "x.py", "args": [None]},
                    {"name": "b", "tier": "fast", "cmd": ["{python}"], "timeout": 0},
                    {"name": "", "tier": "fast", "cmd": ["{python}"]}):
            with self.subTest(bad=bad):
                self.shared([bad])
                code, _, err = run("--tier", "fast", "--tier", "blender")
                self.assertNotEqual(code, 0)
                self.assertIn("gate", err)
                self.assertNotIn("Traceback", err)

    def test_a_blender_gate_that_fails_on_stderr_and_exits_zero_fails(self):
        fake = self.root / "fakeblender"
        fake.write_text("#!/bin/sh\necho '[PASS] one'\necho '[FAIL] two' 1>&2\nexit 0\n")
        fake.chmod(0o755)
        d = self.root / "models" / "m_one"
        d.mkdir()
        (d / "gates.json").write_text(json.dumps({"gates": [
            {"name": "b", "tier": "blender", "script": "x.py", "blend": None}]}))
        self.shared([])
        with mock.patch.object(run_gates, "find_blender", return_value=str(fake)):
            code, out, _ = run("--tier", "blender")
        self.assertEqual(code, 1)
        self.assertIn("FAIL 1", out)


if __name__ == "__main__":
    unittest.main()
