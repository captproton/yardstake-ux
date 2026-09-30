"""
test_new_model.py -- new_model.py's intake and scaffold, against the two plan
sets we know the answers for: Laurel's (live text) and the barn cabin's (a scan).

    python3 -m unittest test_new_model -v          (from buyer/3D; needs pdftotext)

The barn cabin's PDF is not committed (`example plans/` is ignored), so that
case skips, and says so, when the file is absent. Laurel's is committed.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import new_model

ROOT = Path(__file__).resolve().parent
LAUREL = ROOT / "example plans/sacramento_adus/adu-plan-full-set-a1-laurel.pdf"
BARN = ROOT / "example plans/thataduguy/Barn-Cabin-524sf-ADU-1.0-.pdf"


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = new_model.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class Scaffold(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.models = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def go(self, pdf=LAUREL, model_id="test_a1_460", extra=()):
        return run(pdf, "--id", model_id, "--name", "Test", "--issue", "170",
                   "--models-dir", self.models, *extra)

    def test_text_layer_set_gets_every_file(self):
        code, out, err = self.go()
        self.assertEqual(code, 0, err)
        d = self.models / "test_a1_460"
        for name in ("spec.yaml", "gates.json", "EXPORT_PENDING", ".gitignore",
                     "docs/INTAKE.md", "docs/PLAN.md", "docs/candidates.yaml"):
            self.assertTrue((d / name).is_file(), name)
        self.assertRegex((d / "EXPORT_PENDING").read_text(), r"(?m)^issue: #170$")
        gates = json.loads((d / "gates.json").read_text())["gates"]
        self.assertEqual(gates[0]["tier"], "fast")
        self.assertIn("models/test_a1_460/spec.yaml", gates[0]["cmd"])
        self.assertIn("Text layer present", (d / "docs/INTAKE.md").read_text())

    def test_the_spec_holds_no_dimension(self):
        self.go()
        spec = (self.models / "test_a1_460/spec.yaml").read_text()
        body = [ln for ln in spec.splitlines() if ln.strip() and not ln.startswith("#")]
        self.assertFalse([ln for ln in body if "'" in ln.replace('"', "'") and "ft" in ln],
                         "a scaffolded spec must not carry a measured length")
        self.assertIn("A-1.0", spec)              # the sheet index is the one thing it carries

    def test_the_scaffolded_spec_passes_the_lint_it_will_be_held_to(self):
        pytest_yaml = __import__("importlib.util").util.find_spec("yaml")
        if pytest_yaml is None:
            self.skipTest("PyYAML is not installed for this interpreter")
        from adu_kit import spec_lint
        self.go()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = spec_lint.main([str(self.models / "test_a1_460/spec.yaml")])
        self.assertEqual(code, 0)

    def test_never_overwrites(self):
        self.assertEqual(self.go()[0], 0)
        (self.models / "test_a1_460/spec.yaml").write_text("mine")
        code, _, err = self.go()
        self.assertEqual(code, 1)
        self.assertIn("never overwrites", err)
        self.assertEqual((self.models / "test_a1_460/spec.yaml").read_text(), "mine")

    def test_refuses_a_bad_id_and_a_missing_issue(self):
        code, _, err = self.go(model_id="Laurel")
        self.assertEqual(code, 1)
        self.assertIn("lower_snake", err)
        code, _, err = run(LAUREL, "--id", "test_a1_460", "--name", "T",
                           "--models-dir", self.models)
        self.assertEqual(code, 1)
        self.assertIn("--issue", err)
        self.assertEqual(list(self.models.iterdir()), [])

    def test_intake_only_writes_nothing(self):
        code, out, _ = run(LAUREL, "--id", "test_a1_460", "--intake-only",
                           "--models-dir", self.models)
        self.assertEqual(code, 0)
        self.assertIn("# Intake: test_a1_460", out)
        self.assertEqual(list(self.models.iterdir()), [])

    def test_missing_pdf_is_a_message_not_a_traceback(self):
        code, _, err = self.go(pdf=self.models / "nope.pdf")
        self.assertEqual(code, 1)
        self.assertIn("no such file", err)

    @unittest.skipUnless(BARN.is_file(), "the barn cabin's scanned PDF is not in this checkout")
    def test_a_scan_stops_the_scaffold(self):
        code, out, err = self.go(pdf=BARN)
        self.assertEqual(code, 1)
        self.assertIn("No usable text layer", out)
        self.assertIn("--allow-raster", err)
        self.assertEqual(list(self.models.iterdir()), [], "a refused scan wrote files")
        code, _, err = self.go(pdf=BARN, extra=("--allow-raster",))
        self.assertEqual(code, 0, err)
        self.assertFalse((self.models / "test_a1_460/docs/candidates.yaml").exists())


if __name__ == "__main__":
    unittest.main()
