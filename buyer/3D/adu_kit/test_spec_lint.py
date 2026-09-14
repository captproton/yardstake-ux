"""
adu_kit/test_spec_lint.py — the spec-lint gate's tests (#128).

    python3 -m unittest adu_kit.test_spec_lint -v        (from buyer/3D)

Each rule is shown catching its case on a small spec, and Laurel's real spec
is shown passing every rule, including the check that each drawn length is a
dimension on the sheet it cites (needs pdftotext).
"""
import shutil
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path

from adu_kit import spec_lint

THREE_D = Path(__file__).resolve().parents[1]
LAUREL = THREE_D / "models" / "laurel_a1_460" / "spec.yaml"
LAUREL_PDF = THREE_D / "example plans" / "sacramento_adus" / "adu-plan-full-set-a1-laurel.pdf"

SHEETS = {"sheets": [{"pdf_page": 1, "id": "A-0.0"}, {"pdf_page": 4, "id": "A-1.0"}, {"pdf_page": 6, "id": "A-2.0"}],
          "source": "A-0.0 sheet index"}


def spec(**blocks):
    return {"sheet_index": SHEETS, **blocks}


class Cited(unittest.TestCase):

    def test_a_cited_number_passes(self):
        self.assertEqual(spec_lint.lint(spec(envelope={"width": {"ft": 24.0, "raw": "24'-0\"",
                                                                   "source": "A-1.0 floor plan"}})), [])

    def test_an_uncited_number_fails(self):
        problems = spec_lint.lint(spec(envelope={"width": {"ft": 24.0, "raw": "24'-0\""}}))
        self.assertEqual(problems, ["envelope.width.ft = 24.0 has no source, derived or assumed"])

    def test_derived_and_assumed_cite(self):
        self.assertEqual(spec_lint.lint(spec(a={"x": {"ft": 1.0, "derived": "24 - 23"}},
                                             b={"y": {"ft": 0.4583, "raw": "5 1/2\"",
                                                      "assumed": "2x6 actual depth"}})), [])

    def test_the_mapping_above_cites(self):
        self.assertEqual(spec_lint.lint(spec(schedule={"source": "A-1.0 window schedule",
                                                       "rows": [{"mark": "A", "count": 2}]})), [])

    def test_two_mappings_up_does_not_cite(self):
        problems = spec_lint.lint(spec(block={"source": "A-1.0", "inner": {"deeper": {"n": 3}}}))
        self.assertEqual(problems, ["block.inner.deeper.n = 3 has no source, derived or assumed"])

    def test_the_root_does_not_cite(self):
        problems = spec_lint.lint({"source": "A-1.0", "sheet_index": SHEETS, "n": 7})
        self.assertIn("n = 7 has no source, derived or assumed", problems)

    def test_numbers_in_lists_and_not_booleans(self):
        problems = spec_lint.lint(spec(a={"box": [1, 2]}, b={"flag": True}))
        self.assertEqual(problems, ["a.box[0] = 1 has no source, derived or assumed",
                                    "a.box[1] = 2 has no source, derived or assumed"])

    def test_an_empty_citation_is_not_one(self):
        problems = spec_lint.lint(spec(a={"n": 1, "source": "   "}))
        self.assertIn("a.n = 1 has no source, derived or assumed", problems)


class SheetsAndLengths(unittest.TestCase):

    def test_a_source_must_name_a_listed_sheet(self):
        problems = spec_lint.lint(spec(a={"n": 1, "source": "the floor plan"}))
        self.assertEqual(problems, ["a.source names no sheet in sheet_index: 'the floor plan'"])

    def test_a_sheet_id_is_matched_whole(self):
        # A-1.0 must not match inside A-1.05 or XA-1.0.
        problems = spec_lint.lint(spec(a={"n": 1, "source": "XA-1.0 and A-1.05"}))
        self.assertEqual(len(problems), 1)

    def test_a_sheet_index_is_required(self):
        self.assertIn("sheet_index.sheets lists no sheet with an id and a pdf_page, so no source can name a sheet",
                      spec_lint.lint({"a": {"n": 1, "source": "A-1.0"}}))

    def test_raw_and_ft_must_agree(self):
        problems = spec_lint.lint(spec(a={"ft": 19.0, "raw": "19'-2\"", "source": "A-1.0"}))
        self.assertEqual(problems, ["a: raw 19'-2\" is 19.1667 ft, not ft 19.0"])

    def test_four_places_agree(self):
        self.assertEqual(spec_lint.lint(spec(a={"ft": 19.1667, "raw": "19'-2\"", "source": "A-1.0"})), [])

    def test_a_drawn_length_must_be_on_its_sheet(self):
        harvested = {4: {Fraction(24)}, 6: {Fraction(8)}}
        ok = spec(a={"ft": 24.0, "raw": "24'-0\"", "source": "A-1.0 floor plan"})
        self.assertEqual(spec_lint.lint(ok, harvested), [])
        wrong_sheet = spec(a={"ft": 24.0, "raw": "24'-0\"", "source": "A-2.0 roof plan"})
        self.assertEqual(spec_lint.lint(wrong_sheet, harvested),
                         ["a: raw 24'-0\" is not a dimension on A-2.0 (pages [6])"])

    def test_a_length_under_a_cited_row_is_looked_up_on_that_sheet(self):
        harvested = {4: {Fraction(4)}, 6: set()}
        row = {"mark": "A", "source": "A-1.0 window schedule", "width": {"ft": 4.0, "raw": "4'-0\""}}
        self.assertEqual(spec_lint.lint(spec(windows=[row]), harvested), [])
        row["source"] = "A-2.0 front elevation"
        self.assertEqual(spec_lint.lint(spec(windows=[row]), harvested),
                         ["windows[0].width: raw 4'-0\" is not a dimension on A-2.0 (pages [6])"])

    def test_inch_only_lengths_are_not_looked_up(self):
        self.assertEqual(spec_lint.lint(spec(a={"ft": 0.0417, "raw": "1/2\"", "source": "A-1.0"}), {4: set()}), [])


@unittest.skipUnless(LAUREL.is_file(), "Laurel's spec is not here")
class LaurelSpec(unittest.TestCase):

    def test_every_number_is_cited(self):
        import yaml
        self.assertEqual(spec_lint.lint(yaml.safe_load(LAUREL.read_text())), [])

    @unittest.skipUnless(shutil.which("pdftotext") and LAUREL_PDF.is_file(), "needs pdftotext and the sheet set")
    def test_every_drawn_length_is_on_its_sheet(self):
        r = subprocess.run([sys.executable, "-m", "adu_kit.spec_lint", str(LAUREL), "--pdf", str(LAUREL_PDF)],
                           cwd=THREE_D, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("every drawn length found on its sheet", r.stdout)


if __name__ == "__main__":
    unittest.main()
