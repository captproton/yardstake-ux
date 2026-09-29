"""
adu_kit/test_spec_lint.py — the spec-lint gate's tests (#128).

    python3 -m unittest adu_kit.test_spec_lint -v        (from buyer/3D)

Each rule is shown catching its case on a small spec, and Laurel's real spec
is shown passing every rule, including the checks that need the plan set
(needs pdftotext).
"""
import shutil
import subprocess
import sys
import tempfile
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
        self.assertEqual(problems, ["envelope.width.ft = 24.0 has no source, derived, assumed or published",
                                    "envelope.width: raw 24'-0\" is a drawn length with no source naming a sheet"])

    def test_derived_and_assumed_cite_numbers(self):
        self.assertEqual(spec_lint.lint(spec(a={"x": {"ft": 1.0, "derived": "24 - 23"}},
                                             b={"y": {"ft": 0.4583, "raw": "5 1/2\"",
                                                      "assumed": "2x6 actual depth"}})), [])

    def test_a_published_figure_cites_with_its_url(self):
        # #134: equipment the plans name by model is built at its maker's
        # published size, which no sheet in the set carries.
        self.assertEqual(spec_lint.lint(spec(heater={"height": {"ft": 5.1927, "raw": "62 5/16\"",
            "published": "Rheem spec sheet, https://media.rheem.com/x.pdf, column A"}})), [])

    def test_a_published_figure_without_a_url_fails(self):
        problems = spec_lint.lint(spec(heater={"height": {"ft": 5.1927, "published": "the maker's sheet"}}))
        self.assertEqual(problems, ["heater.height.published names no URL to open: \"the maker's sheet\""])

    def test_published_does_not_excuse_a_drawn_length(self):
        problems = spec_lint.lint(spec(heater={"height": {"ft": 5.25, "raw": "5'-3\"",
            "published": "https://media.rheem.com/x.pdf"}}))
        self.assertIn("heater.height: raw 5'-3\" is a drawn length with no source naming a sheet", problems)

    def test_the_mapping_above_cites(self):
        self.assertEqual(spec_lint.lint(spec(schedule={"source": "A-1.0 window schedule",
                                                       "rows": [{"mark": "A", "count": 2}]})), [])

    def test_two_mappings_up_does_not_cite(self):
        problems = spec_lint.lint(spec(block={"source": "A-1.0", "inner": {"deeper": {"n": 3}}}))
        self.assertEqual(problems, ["block.inner.deeper.n = 3 has no source, derived, assumed or published"])

    def test_the_root_does_not_cite(self):
        problems = spec_lint.lint({"source": "A-1.0", "sheet_index": SHEETS, "n": 7})
        self.assertIn("n = 7 has no source, derived, assumed or published", problems)

    def test_numbers_in_lists_and_not_booleans(self):
        problems = spec_lint.lint(spec(a={"box": [1, 2]}, b={"flag": True}))
        self.assertEqual(problems, ["a.box[0] = 1 has no source, derived, assumed or published",
                                    "a.box[1] = 2 has no source, derived, assumed or published"])

    def test_an_empty_citation_is_not_one(self):
        problems = spec_lint.lint(spec(a={"n": 1, "source": "   "}))
        self.assertIn("a.n = 1 has no source, derived, assumed or published", problems)

    def test_nan_and_infinity_are_not_measurements(self):
        # Found by review: `ft: .nan` passed the raw/ft check, because every
        # comparison with NaN is false.
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=bad):
                problems = spec_lint.lint(spec(a={"ft": bad, "raw": "24'-0\"", "source": "A-1.0"}), {4: {Fraction(24)}})
                self.assertEqual(problems, [f"a.ft = {bad} is not a finite number"])


class DuplicateKeys(unittest.TestCase):

    def test_a_repeated_key_is_found(self):
        text = "a:\n  width: 24\n  width: {ft: 24.0, derived: x}\nb:\n  c: 1\n"
        self.assertEqual(spec_lint.duplicate_keys(text), [(3, "width")])

    def test_the_command_line_fails_on_one(self):
        # Found by review: the uncited `width: 24` was shadowed by the second
        # key and the lint passed.
        text = ("sheet_index:\n  source: A-0.0\n  sheets:\n  - {pdf_page: 1, id: A-0.0}\n"
                "envelope:\n  width: 24\n  width: {ft: 24.0, derived: x}\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.yaml"
            path.write_text(text)
            r = subprocess.run([sys.executable, "-m", "adu_kit.spec_lint", str(path)],
                               cwd=THREE_D, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("duplicate key 'width' at line 7", r.stdout)

    def test_a_key_yaml_cannot_use_is_reported_not_a_traceback(self):
        # Found by Copilot: a list as a key crashed the duplicate-key scan.
        text = "sheet_index:\n  sheets: []\n? [a, b]\n: 1\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.yaml"
            path.write_text(text)
            r = subprocess.run([sys.executable, "-m", "adu_kit.spec_lint", str(path)],
                               cwd=THREE_D, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn(f"cannot read {path}", r.stderr)
        self.assertIn("unhashable key", r.stderr)


def _cli(text):
    """Run the command line on a spec written to a temporary file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "spec.yaml"
        path.write_text(text)
        return subprocess.run([sys.executable, "-m", "adu_kit.spec_lint", str(path)],
                              cwd=THREE_D, capture_output=True, text=True)


INDEX = "sheet_index:\n  source: A-0.0\n  sheets:\n  - {pdf_page: 1, id: A-0.0}\n"
FLOOR = {"base_color_linear": [0.5, 0.5, 0.5], "assumed": "a grey"}


class NumericKeys(unittest.TestCase):
    """Rule 6 (#143): the walk checks values, so a number used as a key was
    never checked, and a spec with one passed."""

    def test_a_numeric_key_fails(self):
        self.assertEqual(spec_lint.lint(spec(envelope={42: "wide"})),
                         ["envelope.42: the key 42 is a number, and a key is never checked "
                          "for a citation; name it, or make it a cited value"])

    def test_a_float_key_fails_and_a_boolean_key_is_not_a_number(self):
        problems = spec_lint.lint(spec(envelope={2.5: "wide", True: "yes"}))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("the key 2.5 is a number", problems[0])

    def test_face_slots_are_numbered_by_slot(self):
        """Laurel's materials.face_slots: polygon material indexes, not measurements."""
        self.assertEqual(spec_lint.lint(spec(materials={"library": {"floor": FLOOR, "trim": FLOOR},
                                                        "face_slots": {1: "floor", 2: "trim"}})), [])

    def test_face_slots_are_held_to_their_own_rule(self):
        """The exemption is no hiding place: a slot must be 1..n, no gap,
        naming a library material, as adu_kit.manifest.face_slots requires."""
        problems = spec_lint.lint(spec(materials={"library": {"floor": FLOOR},
                                                  "face_slots": {1: "floor", 42: "floor"}}))
        self.assertEqual(problems, ["materials.face_slots must be numbered 1..2 with no gap, found [1, 42]"])
        problems = spec_lint.lint(spec(materials={"library": {"floor": FLOOR}, "face_slots": {1: "carpet"}}))
        self.assertEqual(problems, ["materials.face_slots slot 1 names 'carpet', which materials.library does not define"])

    def test_the_exemption_is_that_path_only(self):
        problems = spec_lint.lint(spec(finishes={"face_slots": {1: "floor"}}))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("finishes.face_slots.1: the key 1 is a number", problems[0])

    def test_a_key_spelt_like_the_path_is_not_the_exemption(self):
        """Found by review: matched by its printed path, a top-level key
        named "materials.face_slots" was exempt, and checked by nothing."""
        problems = spec_lint.lint(spec(**{"materials.face_slots": {42: "wide"}}))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("materials.face_slots.42: the key 42 is a number", problems[0])

    def test_the_command_line_fails_on_one(self):
        # The issue's own case: this passed, "1 number(s), every one cited".
        r = _cli(INDEX + "envelope:\n  42: wide\n")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("envelope.42: the key 42 is a number", r.stdout)


class SelfContaining(unittest.TestCase):
    """Rule 7 (#143): PyYAML loads an alias inside its own anchor as a
    container that holds itself, and walking it recursed without end."""

    def _looped(self):
        a = {"ft": 1.0}
        a["self"] = a
        b = [2.0]
        b.append(b)
        return spec(a=a, b=b)

    def test_lint_names_it_instead_of_recursing(self):
        problems = spec_lint.lint(self._looped())
        for where in ("a.self", "b[1]"):
            with self.subTest(where=where):
                self.assertIn(f"{where} is a YAML alias back to a container it sits inside; the walk "
                              f"stops there, having checked that container once", problems)
        # and what it holds is still checked, once
        self.assertIn("a.ft = 1.0 has no source, derived, assumed or published", problems)

    def test_count_numbers_counts_each_once(self):
        # the index's three pages, a.ft and b[0]: each once, however often looped
        self.assertEqual(spec_lint.count_numbers(self._looped()), len(SHEETS["sheets"]) + 2)

    def test_a_shared_alias_is_not_a_loop(self):
        """An anchor used twice, never inside itself, is checked in each place."""
        shared = {"ft": 3.0}
        problems = spec_lint.lint(spec(a=shared, b=shared))
        self.assertEqual(problems, ["a.ft = 3.0 has no source, derived, assumed or published",
                                    "b.ft = 3.0 has no source, derived, assumed or published"])

    def test_the_command_line_reports_it_not_a_traceback(self):
        """The file, as a block alias. Today the duplicate-key loader refuses
        it before the walk; the command line must say so readably either way."""
        r = _cli(INDEX + "a: &a\n  self: *a\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertRegex(r.stdout + r.stderr, r"recursive|alias back to a container")


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

    def test_a_length_in_a_list_is_looked_up(self):
        harvested = {4: {Fraction(24), Fraction(7, 2)}}
        s = spec(wall={"source": "A-1.0 floor plan", "string": ["24'-0\"", "3'-11\""]})
        self.assertEqual(spec_lint.lint(s, harvested),
                         ["wall.string[1]: 3'-11\" is not a dimension on A-1.0 (pages [4])"])

    def test_a_raw_without_ft_is_looked_up(self):
        harvested = {4: {Fraction(24)}}
        self.assertEqual(spec_lint.lint(spec(a={"raw": "3'-11\"", "source": "A-1.0"}), harvested),
                         ["a: raw 3'-11\" is not a dimension on A-1.0 (pages [4])"])

    def test_a_feet_only_length_is_looked_up(self):
        # Found by review: `25'` carries no inch mark and was never checked.
        harvested = {4: {Fraction(24)}}
        self.assertEqual(spec_lint.lint(spec(a={"raw": "24'", "source": "A-1.0"}), harvested), [])
        self.assertEqual(spec_lint.lint(spec(a={"raw": "25'", "source": "A-1.0"}), harvested),
                         ["a: raw 25' is not a dimension on A-1.0 (pages [4])"])

    def test_a_drawn_length_needs_a_sheet_even_without_the_pdf(self):
        # Found by review: a drawn length with no source, or only `assumed`,
        # skipped the sheet check entirely.
        self.assertEqual(spec_lint.lint(spec(a={"raw": "3'-11\"", "note": "x"})),
                         ["a: raw 3'-11\" is a drawn length with no source naming a sheet"])
        self.assertEqual(spec_lint.lint(spec(a={"ft": 25.0, "raw": "25'-0\"", "assumed": "I think"})),
                         ["a: raw 25'-0\" is a drawn length with no source naming a sheet"])

    def test_a_raw_beside_ft_must_be_a_length(self):
        problems = spec_lint.lint(spec(a={"ft": 24.0, "raw": "24'-0", "source": "A-1.0"}), {4: {Fraction(24)}})
        self.assertEqual(problems, ["a.raw \"24'-0\" beside ft 24.0 is not a length"])

    def test_a_slope_or_a_sentence_is_not_a_drawn_length(self):
        harvested = {4: set(), 6: set()}
        self.assertEqual(spec_lint.lint(spec(
            slope={"raw": "1\" / 1'-0\"", "source": "A-2.0"},
            check={"ft": 24.0, "derived": "3'-7\" + 4'-0\" + 2'-5\" = 24'-0\" less nothing"}), harvested), [])

    def test_inch_only_lengths_are_not_looked_up(self):
        self.assertEqual(spec_lint.lint(spec(a={"ft": 0.0417, "raw": "1/2\"", "source": "A-1.0"}), {4: set()}), [])


class SheetIndex(unittest.TestCase):
    """The index every source is checked against must itself be sound."""

    def _index(self, *rows):
        return {"sheet_index": {"source": "A-0.0", "sheets": [{"pdf_page": 1, "id": "A-0.0"}, *rows]}}

    def test_an_empty_id_is_refused_and_names_nothing(self):
        s = self._index({"pdf_page": 4, "id": ""})
        s["a"] = {"n": 1, "source": "a note (in brackets)"}
        problems = spec_lint.lint(s)
        self.assertIn("sheet_index.sheets[1].id must be a non-empty sheet id or null, found ''", problems)
        self.assertIn("a.source names no sheet in sheet_index: 'a note (in brackets)'", problems)
        self.assertNotIn("", spec_lint.sheet_pages(s))

    def test_a_page_must_be_a_whole_number(self):
        for page in (4.9, float("nan"), True, "4", 0, -1):
            with self.subTest(page=page):
                s = self._index({"pdf_page": page, "id": "A-1.0"})
                problems = spec_lint.lint(s)   # must not raise
                self.assertTrue(any("sheet_index.sheets[1].pdf_page must be a whole number" in p for p in problems), problems)
                self.assertNotIn("A-1.0", spec_lint.sheet_pages(s))

    def test_a_whole_float_page_is_a_page(self):
        self.assertEqual(spec_lint.sheet_pages(self._index({"pdf_page": 4.0, "id": "A-1.0"}))["A-1.0"], 4)

    def test_an_id_listed_twice_is_refused(self):
        problems = spec_lint.lint(self._index({"pdf_page": 4, "id": "A-1.0"}, {"pdf_page": 5, "id": "A-1.0"}))
        self.assertIn("sheet_index.sheets[2].id A-1.0 is listed more than once", problems)

    def test_a_null_id_is_allowed(self):
        self.assertEqual(spec_lint.lint(self._index({"pdf_page": 13, "id": None, "title": "no id"})), [])

    def test_a_page_whose_title_block_reads_another_id(self):
        s = self._index({"pdf_page": 5, "id": "A-1.0"})
        self.assertEqual(spec_lint.lint(s, {1: set(), 5: set()}, {1: "A-0.0", 5: "A-1.1"}),
                         ["sheet_index: A-1.0 is listed on page 5, whose title block reads A-1.1"])

    def test_a_page_with_no_readable_id_is_not_compared(self):
        s = self._index({"pdf_page": 14, "id": "S1.0"})
        self.assertEqual(spec_lint.lint(s, {1: set(), 14: set()}, {1: "A-0.0", 14: None}), [])


@unittest.skipUnless(LAUREL.is_file(), "Laurel's spec is not here")
class LaurelSpec(unittest.TestCase):

    def test_every_number_is_cited_and_no_key_repeats(self):
        import yaml
        text = LAUREL.read_text()
        self.assertEqual(spec_lint.duplicate_keys(text), [])
        self.assertEqual(spec_lint.lint(yaml.safe_load(text)), [])

    @unittest.skipUnless(shutil.which("pdftotext") and LAUREL_PDF.is_file(), "needs pdftotext and the sheet set")
    def test_every_drawn_length_and_page_against_the_plan_set(self):
        r = subprocess.run([sys.executable, "-m", "adu_kit.spec_lint", str(LAUREL), "--pdf", str(LAUREL_PDF)],
                           cwd=THREE_D, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("every drawn length found on its sheet, every listed page's title block agrees", r.stdout)


if __name__ == "__main__":
    unittest.main()
