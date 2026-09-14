"""
adu_kit/sheets.py — harvest dimension CANDIDATES from a plan set's PDF (#127).

    python3 -m adu_kit.sheets PLANS.pdf [--pages 4,6] [--out candidates.yaml]

Run from buyer/3D. Needs poppler's `pdftotext`. Plain Python; no Blender.

A PLAN SET EXPORTED FROM CAD KEEPS ITS TEXT, and `pdftotext -bbox` returns
every word with its box on the page. Dimension strings come out in PIECES:
`24'`, `-`, `0"` for a horizontal dimension, and the same three pieces stacked
for one drawn vertically; `9'`, `-`, `7`, `1/2"` for a fraction. This module
stitches the pieces back together by position, converts each to feet, and
records where it sits and which sheet it is on. Laurel's floor plan (A-1.0)
yields 67 feet-and-inches dimensions, which is exactly what a plain
`pdftotext -layout` search finds.

A scanned plan set has no text to read. The barn cabin's is scanned: its
measurements were read by eye, and they are this module's known answers
(test_sheets.py), not its input.

IT NEVER WRITES A SPEC. It produces candidates. A person checks each one on the
sheet and copies what they accept into spec.yaml with a `source:` citation.
A machine-read dimension that lands in a spec unchecked carries false
confidence, which is worse than reading by hand. So `write_candidates()` and
the command line refuse any file named spec.yaml, spec.yml or spec.json, and
refuse to overwrite anything. Its own output is untrusted input too: nothing
here reads a candidates file back.

WHAT IS HARVESTED: strings with a foot mark and an inch mark (`4'-11"`,
`9' - 7 1/2"`, `-0' - 6"`). Inch-only strings (`6"`, `1/4":12"`) are not: on
these sheets they are mostly notes, fastener spacings and slopes, and a
candidate list full of them hides the dimensions.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional

# Typographic marks a CAD export may use, folded to plain ones before parsing.
_FOLD = str.maketrans({"’": "'", "′": "'", "‘": "'", "”": '"', "″": '"', "“": '"',
                       "–": "-", "—": "-", "−": "-"})

_LENGTH = re.compile(r"""
    (?P<sign>-)?
    (?:(?P<ft>\d+)'(?:\s*-\s*|\s*))?                 # feet, then an optional dash
    (?:
        (?P<inch>\d+)(?:(?:\s+|\s*-\s*)(?P<fn>\d+)/(?P<fd>\d+))?   # 7, 7 1/2, 7-1/2
      | (?P<bn>\d+)/(?P<bd>\d+)                                    # 3/8
    )?
    (?P<imark>")?
    """, re.X)


def parse_length(raw: str) -> Optional[Fraction]:
    """Feet, exactly, for a written length, or None if it is not one.

    Accepts 22'-0", 9' - 7 1/2", 8'-10 1/4", 1'-2-1/4", 10 1/4", 1-1/2", 3/8",
    4', and a leading minus. Refuses a bare number, lumber sizes (6x6), slopes
    (1/4":12"), inches of 12 or more after feet, and improper fractions."""
    if not isinstance(raw, str):
        return None
    text = raw.translate(_FOLD).strip()
    m = _LENGTH.fullmatch(text)
    if not m:
        return None
    has_inches = m["inch"] is not None or m["bn"] is not None
    if m["ft"] is None and not has_inches:
        return None
    if has_inches != (m["imark"] is not None):
        return None                      # 7 with no inch mark, or 4'" with no inches
    inches = Fraction(0)
    if m["inch"] is not None:
        inches = Fraction(int(m["inch"]))
        if m["ft"] is not None and inches >= 12:
            return None                  # 0'-13" is not how a length is written
    for num, den in ((m["fn"], m["fd"]), (m["bn"], m["bd"])):
        if num is not None:
            num, den = int(num), int(den)
            if den == 0 or num >= den:
                return None
            inches += Fraction(num, den)
    feet = Fraction(int(m["ft"] or 0)) + inches / 12
    return -feet if m["sign"] else feet


# ── reading a PDF ───────────────────────────────────────────────────────────

class SheetsError(Exception):
    """A problem the command line reports as a message, not a traceback."""


@dataclass(frozen=True)
class Word:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


@dataclass(frozen=True)
class Page:
    number: int
    width: float
    height: float
    words: tuple


_PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', re.S)
_WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')


def read_pages(pdf: Path, first: Optional[int] = None, last: Optional[int] = None) -> list:
    """Every word with its box, per page, from `pdftotext -bbox`. Boxes are PDF
    points from the page's top-left."""
    exe = shutil.which("pdftotext")
    if exe is None:
        raise SheetsError("pdftotext is not installed (poppler: `brew install poppler`, "
                          "`apt-get install poppler-utils`)")
    if not Path(pdf).is_file():
        raise SheetsError(f"{pdf} is not a file")
    cmd = [exe, "-bbox"]
    if first is not None:
        cmd += ["-f", str(first)]
    if last is not None:
        cmd += ["-l", str(last)]
    r = subprocess.run(cmd + [str(pdf), "-"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SheetsError(f"pdftotext could not read {pdf}: {r.stderr.strip() or 'exit ' + str(r.returncode)}")
    pages = []
    for i, (width, height, body) in enumerate(_PAGE.findall(r.stdout)):
        number = (first or 1) + i
        words = tuple(Word(number, float(a), float(b), float(c), float(d), html.unescape(t))
                      for a, b, c, d, t in _WORD.findall(body))
        pages.append(Page(number, float(width), float(height), words))
    return pages


# ── the sheet id ────────────────────────────────────────────────────────────

_SHEET_ID = re.compile(r"[A-Z]{1,2}-?\d+(?:\.\d+)?|T24-\d+")


def sheet_id(page: Page) -> Optional[str]:
    """The sheet id in the title block, or None. The title block's id is the
    largest id-shaped word in the page's bottom-right corner. A sheet laid out
    another way -- the structural pages in the Laurel set are portrait, with
    the title block turned -- gets None rather than a guess."""
    corner = [w for w in page.words
              if _SHEET_ID.fullmatch(w.text)
              and w.x0 > page.width * 0.85 and w.y0 > page.height * 0.80]
    if not corner:
        return None
    return max(corner, key=lambda w: (w.y1 - w.y0, w.x0 + w.y0)).text


# ── stitching dimensions ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Candidate:
    raw: str
    feet: Fraction
    page: int
    sheet: Optional[str]
    orientation: str        # horizontal | vertical
    box: tuple              # x0, y0, x1, y1 in PDF points from the top-left


_FEET_PIECE = re.compile(r"-?\d+'-?")
_TRAILING_LENGTH = re.compile(r"(?<![\d'.])(\d+'-\d+(?:-\d+/\d+)?\")$")
_INCH_PIECE = re.compile(r'\d+"|\d+/\d+"|\d+')
_WRAP_LEFT = "([{"
_WRAP_RIGHT = ")]},;:."


def _core(text: str) -> str:
    return text.translate(_FOLD).lstrip(_WRAP_LEFT).rstrip(_WRAP_RIGHT)


def _near(a: Word, b: Word) -> bool:
    """b is the next piece of the same dimension: within a few character sizes
    of a along both axes. Pieces are consecutive in the content stream, so this
    only has to reject a word that happens to follow from elsewhere."""
    size = max(a.x1 - a.x0, a.y1 - a.y0, b.x1 - b.x0, b.y1 - b.y0)
    return abs(b.x0 - a.x0) <= 3 * size and abs(b.y0 - a.y0) <= 3 * size


def _box(words: Iterable[Word]) -> tuple:
    words = list(words)
    return (min(w.x0 for w in words), min(w.y0 for w in words),
            max(w.x1 for w in words), max(w.y1 for w in words))


def stitch(page: Page, sheet: Optional[str] = None) -> list:
    """Every feet-and-inches dimension on a page, in content order."""
    words, out, i = page.words, [], 0
    while i < len(words):
        w = words[i]
        text = _core(w.text)
        # Already one word: 1'-0", (6'-1", 10'-0"). Or a length at the end of a
        # word, as in a rebar callout: 2-NO.5X4'-0" is two #5 bars, 4'-0" long.
        if "'" in text and '"' in text and not _FEET_PIECE.fullmatch(text):
            feet = parse_length(text)
            if feet is None:
                tail = _TRAILING_LENGTH.search(text)
                if tail:
                    text, feet = tail[1], parse_length(tail[1])
            if feet is not None:
                horizontal = (w.x1 - w.x0) >= (w.y1 - w.y0)
                out.append(Candidate(text, feet, page.number, sheet,
                                     "horizontal" if horizontal else "vertical", _box([w])))
            i += 1
            continue
        if not _FEET_PIECE.fullmatch(text):
            i += 1
            continue
        # In pieces: 24' - 0", 9' - 7 1/2", -0' - 6", vertical or horizontal.
        pieces, texts, j = [w], [text], i + 1
        if not text.endswith("-") and j < len(words) and _core(words[j].text) == "-" \
                and _near(pieces[-1], words[j]):
            pieces.append(words[j]); texts.append("-"); j += 1
        while j < len(words) and not texts[-1].endswith('"') and len(texts) < 5:
            nxt = _core(words[j].text)
            if not (_INCH_PIECE.fullmatch(nxt) and _near(pieces[-1], words[j])):
                break
            pieces.append(words[j]); texts.append(nxt); j += 1
        raw = " ".join(texts)
        feet = parse_length(raw) if texts[-1].endswith('"') else None
        if feet is None:
            i += 1
            continue
        first, last = pieces[0], pieces[-1]
        dx = abs((last.x0 + last.x1) - (first.x0 + first.x1))
        dy = abs((last.y0 + last.y1) - (first.y0 + first.y1))
        out.append(Candidate(raw, feet, page.number, sheet,
                             "horizontal" if dx >= dy else "vertical", _box(pieces)))
        i = j
    return out


def page_count(pdf: Path) -> int:
    """The PDF's page count, from poppler's `pdfinfo`."""
    exe = shutil.which("pdfinfo")
    if exe is None:
        raise SheetsError("pdfinfo is not installed (it comes with pdftotext, in poppler)")
    if not Path(pdf).is_file():
        raise SheetsError(f"{pdf} is not a file")
    r = subprocess.run([exe, str(pdf)], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
    if r.returncode != 0 or not m:
        raise SheetsError(f"pdfinfo could not read {pdf}: {r.stderr.strip() or 'no page count'}")
    return int(m[1])


def harvest(pdf: Path, pages: Optional[Iterable[int]] = None) -> list:
    """Candidates from the given pages (1-based), or from every page."""
    wanted = sorted(set(pages)) if pages is not None else None
    if wanted is not None:
        if not wanted or wanted[0] < 1:
            raise SheetsError(f"pages must be 1 or more, got {wanted}")
        have = page_count(pdf)
        if wanted[-1] > have:
            raise SheetsError(f"{pdf} has no page {wanted[-1]} (it has {have})")
    read = read_pages(pdf, wanted[0], wanted[-1]) if wanted else read_pages(pdf)
    out = []
    for page in read:
        if wanted is None or page.number in wanted:
            out += stitch(page, sheet_id(page))
    return out


# ── output: a YAML fragment of candidates, never a spec ─────────────────────

SPEC_NAMES = frozenset({"spec.yaml", "spec.yml", "spec.json"})


def to_yaml(candidates: list, pdf_name: str) -> str:
    """Candidates as a YAML fragment. Strings are JSON-quoted, which YAML reads
    as double-quoted scalars, so no YAML library is needed."""
    q = json.dumps
    lines = [
        f"# Dimension CANDIDATES from {pdf_name}, harvested by adu_kit/sheets.py.",
        "# NOT A SPEC. Nothing here has been checked. Copy a value into spec.yaml",
        "# only after reading it on the sheet, with a `source:` naming the sheet",
        "# and where on it. `box` is PDF points from the page's top-left.",
        f"source_pdf: {q(pdf_name)}",
        f"count: {len(candidates)}",
        "candidates:" + ("" if candidates else " []"),
    ]
    for c in candidates:
        lines += [
            f"  - raw: {q(c.raw)}",
            f"    ft: {round(float(c.feet), 4)}",
            f"    page: {c.page}",
            f"    sheet: {q(c.sheet) if c.sheet else 'null'}",
            f"    orientation: {c.orientation}",
            f"    box: [{', '.join(f'{v:.1f}' for v in c.box)}]",
        ]
    return "\n".join(lines) + "\n"


def refuse_spec_path(out: Path) -> None:
    """Raise if `out` is, or links to, a spec. Checked before anything is read,
    so no amount of work ends in a spec."""
    out = Path(out)
    for name in (out.name, out.resolve().name):
        if name.lower() in SPEC_NAMES:
            raise SheetsError(f"refusing to write {out}: candidates never go into a spec. "
                              f"A person copies each accepted value into spec.yaml with a source: citation")


def write_candidates(text: str, out: Path) -> None:
    """Write candidates to a NEW file that is not a spec."""
    out = Path(out)
    refuse_spec_path(out)
    try:
        with out.open("x") as f:        # "x": fails if anything is already there
            f.write(text)
    except FileExistsError:
        raise SheetsError(f"refusing to overwrite {out}") from None
    except OSError as e:
        raise SheetsError(f"cannot write {out}: {e}") from None


def _pages_arg(text: str) -> list:
    pages = []
    for part in text.split(","):
        part = part.strip()
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not m:
            raise SheetsError(f"--pages takes numbers and ranges like 4,6 or 4-6, got {text!r}")
        a, b = int(m[1]), int(m[2] or m[1])
        if b < a:
            raise SheetsError(f"--pages range {part!r} runs backwards")
        pages += range(a, b + 1)
    return pages


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m adu_kit.sheets",
                                 description="Harvest dimension candidates from a plan set PDF. "
                                             "Writes candidates, never a spec.")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--pages", help="e.g. 4,6 or 4-6 (default: every page)")
    ap.add_argument("--out", type=Path, help="a new file for the YAML (default: print it)")
    args = ap.parse_args(argv)
    try:
        if args.out:
            refuse_spec_path(args.out)
        pages = _pages_arg(args.pages) if args.pages else None
        text = to_yaml(harvest(args.pdf, pages), args.pdf.name)
        if args.out:
            write_candidates(text, args.out)
            print(f"wrote {text.count(chr(10) + '  - raw:')} candidate(s) to {args.out}", file=sys.stderr)
        else:
            sys.stdout.write(text)
    except SheetsError as e:
        print(f"sheets.py: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
