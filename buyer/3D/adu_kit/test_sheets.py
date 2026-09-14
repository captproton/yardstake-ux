"""
adu_kit/test_sheets.py — the harvester's tests (#127).

    python3 -m unittest adu_kit.test_sheets -v        (from buyer/3D)

KNOWN ANSWERS. The barn cabin's spec holds 183 lengths written two ways, as
drawn (`raw`) and in feet (`ft`), every one read off the scanned sheets by eye.
parse_length() must agree with all of them except the ones listed in
LABELS_ONLY, whose `ft` is a measured, assumed or derived number and whose
`raw` is only its nearest readable fraction. That list is exact: a new
disagreement fails, and so does fixing one without updating it.

A GENERATED PDF. The stitching is tested on a small PDF this file writes, with
the shapes Laurel's sheets use: pieces on one line, pieces stacked vertically,
a fraction, a negative elevation, a dimension in parentheses, a one-word
dimension, distractors, and a title-block id. Needs `pdftotext`; skipped with a
message where it is missing (CI installs it).

LAUREL. The Laurel sheet set is versioned (the other Sacramento files are
not). Every page's harvest must match a plain `pdftotext -layout` search for
the same strings. Skipped with a message only if the PDF has gone missing.

Needs PyYAML for the known answers (CI installs it).
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from adu_kit import sheets
from adu_kit.sheets import parse_length

THREE_D = Path(__file__).resolve().parents[1]
BARN_SPEC = THREE_D / "models" / "barn_cabin_524" / "spec.yaml"
LAUREL_PDF = THREE_D / "example plans" / "sacramento_adus" / "adu-plan-full-set-a1-laurel.pdf"
HAVE_PDFTOTEXT = shutil.which("pdftotext") is not None

# `ft` is the number the model uses; `raw` is a label rounded to a fraction.
LABELS_ONLY = {
    "openings.main_floor.south_wall.openings[1].construction.lock_rail": "derived; raw is the nearest 1/8",
    "openings.main_floor.south_wall.openings[1].construction.panel_bevel": "measured_approx off an undimensioned mitre",
    "trim.head_casing_height": "measured: a band at z 7.00-7.38 ft",
    "fixtures.door_hardware.entry_set.rose_thickness": "assumed",
    "fixtures.door_hardware.entry_set.shank_diameter": "assumed",
    "fixtures.door_hardware.entry_set.shank_length": "assumed",
    "fixtures.mounted.items[0].along": "measured from video, px x=508",
}
# Written in the spec's raw field, but not lengths.
NOT_LENGTHS = {"construction.porch_post": "6x6 is a nominal lumber size"}

# Agreement tolerance: the spec's own rounding, but never looser than 1/16".
SIXTEENTH_FT = 1 / 192


def spec_pairs():
    import yaml  # PyYAML: the spec is YAML, and spec.json is an untracked, stale cache
    spec = yaml.safe_load(BARN_SPEC.read_text())
    pairs = []

    def walk(node, path):
        if isinstance(node, dict):
            if "raw" in node and "ft" in node:
                pairs.append((path, str(node["raw"]), node["ft"]))
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(spec, "")
    return pairs


class KnownAnswers(unittest.TestCase):
    """parse_length() against the barn cabin's hand-read values."""

    def test_every_hand_read_length(self):
        pairs = spec_pairs()
        self.assertGreaterEqual(len(pairs), 183, "the barn cabin spec lost measured lengths")
        agree, labels, refused, wrong = 0, set(), set(), []
        for path, raw, ft in pairs:
            value = parse_length(raw)
            if value is None:
                refused.add(path)
                continue
            places = len(repr(float(ft)).split(".")[1])
            tolerance = min(0.5 * 10 ** -places, SIXTEENTH_FT) + 1e-9
            if abs(float(value) - ft) <= tolerance:
                agree += 1
            elif path in LABELS_ONLY:
                labels.add(path)
            else:
                wrong.append(f"{path}: {raw!r} is {float(value):.4f} ft, spec says {ft}")
        self.assertEqual(wrong, [], "lengths that disagree with their hand-read ft")
        self.assertEqual(refused, set(NOT_LENGTHS), "raw values refused as lengths")
        self.assertEqual(labels, set(LABELS_ONLY),
                         "LABELS_ONLY must list exactly the rounded labels; update it if one was fixed")
        self.assertEqual(agree, len(pairs) - len(LABELS_ONLY) - len(NOT_LENGTHS))


class ParseLength(unittest.TestCase):

    def test_forms_on_sheets(self):
        cases = {
            "22'-0\"": Fraction(22),
            "24' - 0\"": Fraction(24),
            "9' - 7 1/2\"": 9 + Fraction(15, 24),
            "8'-10 1/4\"": 8 + Fraction(41, 48),
            "1'-2-1/4\"": 1 + Fraction(9, 48),
            "10 1/4\"": Fraction(41, 48),
            "1-1/2\"": Fraction(1, 8),
            "3/8\"": Fraction(1, 32),
            "4'": Fraction(4),
            "0'-0\"": Fraction(0),
            "-0' - 6\"": Fraction(-1, 2),
            "4’-11”": 4 + Fraction(11, 12),
        }
        for raw, feet in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_length(raw), feet)

    def test_refused(self):
        for raw in ("6x6", "24", "7 1/2", "1/4\":12\"", "0'-13\"", "5/4\"", "3/0\"", "4'\"",
                    "", "R327", "T.P.", "2X6", None, 22):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_length(raw))


def _pdf(texts):
    """A one-page PDF (612x792 points) drawing each (x, y, size, rotated, text),
    y measured up from the bottom as PDF does."""
    ops = []
    for x, y, size, rotated, text in texts:
        esc = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        matrix = f"0 1 -1 0 {x} {y}" if rotated else f"1 0 0 1 {x} {y}"
        ops.append(f"BT /F1 {size} Tf {matrix} Tm ({esc}) Tj ET")
    stream = "\n".join(ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


FIXTURE = [
    (72, 700, 10, False, "24' - 0\""),                # pieces on one line
    (72, 660, 10, False, "9' - 7 1/2\""),             # a fraction
    (300, 500, 10, True, "3' - 9\""),                 # pieces stacked: drawn rotated
    (72, 620, 10, False, "GRADE -0' - 6\""),          # a negative elevation after a word
    (72, 580, 10, False, "WIDE (6'-1\" TO 10'-0\")"), # one-word dimensions in parentheses
    (72, 540, 10, False, "SCALE: 1/4\" = 1'-0\""),    # one word after an inch-only word
    (72, 500, 10, False, "R327 2X6 24 @ 16\" O.C."),  # distractors: no feet-and-inches
    (72, 460, 10, False, "SLOPE 1/4\":12\""),         # a slope is not a dimension
    (560, 40, 18, False, "A-9.9"),                    # the title block's sheet id
]


@unittest.skipUnless(HAVE_PDFTOTEXT, "pdftotext is not installed; the stitching tests need it")
class Stitching(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pdf = Path(cls.tmp.name) / "fixture.pdf"
        cls.pdf.write_bytes(_pdf(FIXTURE))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_candidates(self):
        got = [(c.raw, c.feet, c.orientation, c.sheet, c.page) for c in sheets.harvest(self.pdf)]
        self.assertEqual(sorted(got, key=str), sorted([
            ("24' - 0\"", Fraction(24), "horizontal", "A-9.9", 1),
            ("9' - 7 1/2\"", 9 + Fraction(15, 24), "horizontal", "A-9.9", 1),
            ("3' - 9\"", 3 + Fraction(3, 4), "vertical", "A-9.9", 1),
            ("-0' - 6\"", Fraction(-1, 2), "horizontal", "A-9.9", 1),
            ("6'-1\"", 6 + Fraction(1, 12), "horizontal", "A-9.9", 1),
            ("10'-0\"", Fraction(10), "horizontal", "A-9.9", 1),
            ("1'-0\"", Fraction(1), "horizontal", "A-9.9", 1),
        ], key=str))

    def test_boxes_are_on_the_page_where_drawn(self):
        by_raw = {c.raw: c for c in sheets.harvest(self.pdf)}
        x0, y0, x1, y1 = by_raw["24' - 0\""].box
        # drawn at x 72, baseline 700 up from the bottom: 92 down from the top
        self.assertAlmostEqual(x0, 72, delta=2)
        self.assertTrue(792 - 700 - 12 <= y0 <= 792 - 700, (y0, y1))
        vx0, vy0, vx1, vy1 = by_raw["3' - 9\""].box
        self.assertGreater(vy1 - vy0, vx1 - vx0, "a rotated dimension's box should be tall")

    def test_yaml_is_a_candidate_list(self):
        text = sheets.to_yaml(sheets.harvest(self.pdf), "fixture.pdf")
        self.assertIn("NOT A SPEC", text)
        self.assertIn("count: 7", text)
        self.assertEqual(text.count("\n  - raw: "), 7)
        try:
            import yaml
        except ImportError:
            return
        doc = yaml.safe_load(text)
        self.assertEqual(len(doc["candidates"]), 7)
        self.assertEqual({c["sheet"] for c in doc["candidates"]}, {"A-9.9"})
        self.assertIn(-0.5, [c["ft"] for c in doc["candidates"]])

    def test_pages_out_of_range_is_a_message(self):
        with self.assertRaises(sheets.SheetsError) as e:
            sheets.harvest(self.pdf, [2])
        self.assertIn("no page 2", str(e.exception))

    def test_command_line(self):
        r = subprocess.run([sys.executable, "-m", "adu_kit.sheets", str(self.pdf), "--pages", "1"],
                           cwd=THREE_D, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("count: 7", r.stdout)
        self.assertNotIn("Traceback", r.stderr)


class NeverASpec(unittest.TestCase):

    def test_refuses_spec_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("spec.yaml", "SPEC.YAML", "spec.yml", "spec.json"):
                target = Path(tmp) / name
                with self.subTest(name=name), self.assertRaises(sheets.SheetsError) as e:
                    sheets.write_candidates("candidates: []\n", target)
                self.assertIn("never go into a spec", str(e.exception))
                self.assertFalse(target.exists())

    def test_refuses_a_link_that_resolves_to_a_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "spec.yaml"
            link = Path(tmp) / "candidates.yaml"
            link.symlink_to(spec)
            with self.assertRaises(sheets.SheetsError) as e:
                sheets.write_candidates("candidates: []\n", link)
            # Refused as a spec, not merely because the link already exists.
            self.assertIn("never go into a spec", str(e.exception))
            self.assertFalse(spec.exists())

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "candidates.yaml"
            target.write_text("kept\n")
            with self.assertRaises(sheets.SheetsError) as e:
                sheets.write_candidates("candidates: []\n", target)
            self.assertIn("refusing to overwrite", str(e.exception))
            self.assertEqual(target.read_text(), "kept\n")

    def test_writes_a_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "candidates.yaml"
            sheets.write_candidates("candidates: []\n", target)
            self.assertEqual(target.read_text(), "candidates: []\n")

    def test_command_line_refuses_spec_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "spec.yaml"
            r = subprocess.run([sys.executable, "-m", "adu_kit.sheets", "missing.pdf", "--out", str(target)],
                               cwd=THREE_D, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            # Refused for the name, before the PDF is even looked at -- not for
            # the missing PDF, which would pass this test with no refusal at all.
            self.assertIn("never go into a spec", r.stderr)
            self.assertFalse(target.exists())
            self.assertNotIn("Traceback", r.stderr)

    def test_one_way_to_write_a_file(self):
        # write_candidates() is the only code that writes, and it can only create.
        source = (Path(__file__).resolve().parent / "sheets.py").read_text()
        self.assertEqual(re.findall(r"\.write_text\(|\.write_bytes\(|\bopen\(", source), ["open("])
        self.assertEqual(len(re.findall(r'out\.open\("x"\)', source)), 1)


@unittest.skipUnless(HAVE_PDFTOTEXT and LAUREL_PDF.is_file(),
                     f"the Laurel sheet set is missing: {LAUREL_PDF} should be in git")
class Laurel(unittest.TestCase):
    """Every page's harvest against a plain -layout search for the same strings."""

    LAYOUT = re.compile(r"""(-?)(\d+) ?['’′] ?- ?(\d+)( \d+/\d+)? ?["”″]""")

    def test_floor_plan(self):
        got = sheets.harvest(LAUREL_PDF, [4])
        self.assertEqual(len(got), 67)
        self.assertEqual({c.sheet for c in got}, {"A-1.0"})
        self.assertEqual({c.orientation for c in got}, {"horizontal", "vertical"})

    def test_sheet_ids(self):
        expected = {1: "A-0.0", 2: "A-0.1", 3: "A-0.2", 4: "A-1.0", 5: "A-1.1", 6: "A-2.0",
                    7: "A-3.0", 8: "A-3.1", 9: "A-3.2", 10: "A-3.3", 11: "A-3.4", 12: "A-3.5",
                    13: None, 14: None, 15: None, 16: None,
                    17: "T24-1", 18: "T24-2", 19: "T24-3", 20: "T24-4"}
        got = {p.number: sheets.sheet_id(p) for p in sheets.read_pages(LAUREL_PDF)}
        self.assertEqual(got, expected)

    def test_every_page_matches_a_layout_search(self):
        from collections import Counter
        norm = lambda ft, inch, frac: f"{int(ft)}'-{int(inch)}{frac or ''}\""
        for page in sheets.read_pages(LAUREL_PDF):
            with self.subTest(page=page.number):
                layout = subprocess.run(["pdftotext", "-f", str(page.number), "-l", str(page.number),
                                         "-layout", str(LAUREL_PDF), "-"], capture_output=True, text=True).stdout
                want = Counter(norm(m[2], m[3], m[4]) for m in self.LAYOUT.finditer(layout))
                got = Counter()
                for c in sheets.stitch(page):
                    m = self.LAYOUT.fullmatch(c.raw.replace(" - ", "-").replace("' -", "'-").replace("- ", "-"))
                    got[norm(m[2], m[3], m[4]) if m else c.raw] += 1
                self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
