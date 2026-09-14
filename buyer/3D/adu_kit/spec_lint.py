"""
adu_kit/spec_lint.py — every number in a model spec is cited (#128).

    python3 -m adu_kit.spec_lint models/laurel_a1_460/spec.yaml --pdf PLANS.pdf

Run from buyer/3D. Plain Python; needs PyYAML, and pdftotext for --pdf.

A SPEC IS A LIST OF CLAIMS ABOUT A DRAWING. A number with no citation is a
claim nobody can check, and the barn cabin's history is the record of what
that costs: a ridge datum wrong twice, a wall measured as ink. So this gate
makes every number say where it came from, and checks what it can:

1. EVERY NUMBER IS CITED. A number (not a boolean) needs a non-empty `source`,
   `derived` or `assumed` string in its own mapping or in the mapping directly
   above it, looking through lists. The document root never counts: a
   `source` at the top of the file cannot cite everything below it.
2. A SOURCE NAMES A SHEET the spec lists in `sheet_index.sheets[].id`, so
   every source cites a drawing someone can open, not a file path. The index
   itself must be sound: each id non-empty and listed once, each `pdf_page` a
   whole number of 1 or more. A row whose id is null (a sheet with no id) is
   allowed and can be named by no source.
3. A WRITTEN LENGTH AGREES WITH ITS FEET. Where a mapping has a `raw` beside a
   numeric `ft`, the raw string must be a length, and they agree to within
   0.0005 ft.
4. EVERY DRAWN LENGTH IS ON ITS SHEET (with --pdf). Any string in the spec
   that is a feet-and-inches length -- a `raw`, with or without `ft`, or an
   item in a list such as a wall's dimension string -- must be one of the
   dimensions adu_kit.sheets harvests from the sheets its source names: the
   source of its own mapping, else the mapping directly above. Inch-only
   strings are not harvested and are not checked here, and a length inside a
   sentence (a `derived` note) is not a drawn length.

It reads the spec and reports. It writes nothing.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Optional

from adu_kit import sheets

CITATIONS = ("source", "derived", "assumed")
FT_TOLERANCE = 0.0005


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _cites(mapping) -> bool:
    return isinstance(mapping, dict) and any(
        isinstance(mapping.get(k), str) and mapping[k].strip() for k in CITATIONS)


def _page(v) -> Optional[int]:
    """A pdf_page as a whole number of 1 or more, or None. 4.0 is page 4;
    4.9, NaN, True and "4" are not pages."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if isinstance(v, float) and (not math.isfinite(v) or not v.is_integer()):
        return None
    return int(v) if v >= 1 else None


def _rows(spec) -> list:
    index = spec.get("sheet_index") if isinstance(spec, dict) else None
    rows = index.get("sheets") if isinstance(index, dict) else None
    return rows if isinstance(rows, list) else []


def sheet_pages(spec) -> dict:
    """{sheet id: pdf page} for the sound rows of `sheet_index.sheets`."""
    out = {}
    for row in _rows(spec):
        if not isinstance(row, dict):
            continue
        sid, page = row.get("id"), _page(row.get("pdf_page"))
        if isinstance(sid, str) and sid.strip() and page is not None and sid not in out:
            out[sid] = page
    return out


def sheet_index_problems(spec) -> list:
    problems, seen = [], set()
    for i, row in enumerate(_rows(spec)):
        at = f"sheet_index.sheets[{i}]"
        if not isinstance(row, dict):
            problems.append(f"{at} is not a mapping")
            continue
        sid = row.get("id")
        if sid is not None:
            if not isinstance(sid, str) or not sid.strip():
                problems.append(f"{at}.id must be a non-empty sheet id or null, found {sid!r}")
            elif sid in seen:
                problems.append(f"{at}.id {sid} is listed more than once")
            else:
                seen.add(sid)
        if _page(row.get("pdf_page")) is None:
            problems.append(f"{at}.pdf_page must be a whole number of 1 or more, found {row.get('pdf_page')!r}")
    return problems


def _named_sheets(text: str, ids) -> list:
    return [i for i in ids if i.strip() and re.search(rf"(?<![\w.-]){re.escape(i)}(?![\w-]|\.\d)", text)]


def _is_drawn_length(value) -> bool:
    return (isinstance(value, str) and "'" in value.translate(sheets._FOLD)
            and '"' in value.translate(sheets._FOLD) and sheets.parse_length(value) is not None)


def _source_for(stack) -> Optional[str]:
    """The source a length is checked against: its own mapping's, else the one above."""
    for mapping in reversed(stack[-2:]):
        src = mapping.get("source") if isinstance(mapping, dict) else None
        if isinstance(src, str) and src.strip():
            return src
    return None


def lint(spec, harvested: Optional[dict] = None) -> list:
    """Every problem in a parsed spec. `harvested` is {pdf page: set of exact
    feet} from the plan set, for rule 4; None skips rule 4."""
    if not isinstance(spec, dict):
        return [f"the spec must be a mapping, found {type(spec).__name__}"]
    ids = sheet_pages(spec)
    problems = sheet_index_problems(spec)
    if not ids:
        problems.append("sheet_index.sheets lists no sheet with an id and a pdf_page, "
                        "so no source can name a sheet")

    def cited(stack) -> bool:
        return len(stack) > 1 and (_cites(stack[-1]) or (len(stack) > 2 and _cites(stack[-2])))

    def on_sheet(value, where, stack, is_raw=False):
        if harvested is None:
            return
        src = _source_for(stack)
        named = _named_sheets(src, ids) if src else []
        pages = [ids[i] for i in named]
        if pages and not any(sheets.parse_length(value) in harvested.get(p, ()) for p in pages):
            label = f"raw {value}" if is_raw else value
            problems.append(f"{where}: {label} is not a dimension on {', '.join(named)} (pages {pages})")

    def walk(node, path, stack):
        if isinstance(node, dict):
            here = stack + [node]
            own = node.get("source")
            if isinstance(own, str) and ids and not _named_sheets(own, ids):
                problems.append(f"{path}.source names no sheet in sheet_index: {own!r}")
            if "raw" in node and _is_number(node.get("ft")):
                feet = sheets.parse_length(node["raw"]) if isinstance(node["raw"], str) else None
                if feet is None:
                    problems.append(f"{path}.raw {node['raw']!r} beside ft {node['ft']} is not a length")
                elif abs(float(feet) - node["ft"]) > FT_TOLERANCE:
                    problems.append(f"{path}: raw {node['raw']} is {float(feet):.4f} ft, not ft {node['ft']}")
            for key, value in node.items():
                child = f"{path}.{key}" if path else str(key)
                if _is_number(value):
                    if not cited(here):
                        problems.append(f"{child} = {value} has no source, derived or assumed")
                elif _is_drawn_length(value):
                    on_sheet(value, path if key == "raw" else child, here, is_raw=(key == "raw"))
                else:
                    walk(value, child, here)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                child = f"{path}[{i}]"
                if _is_number(value):
                    if not cited(stack):
                        problems.append(f"{child} = {value} has no source, derived or assumed")
                elif _is_drawn_length(value):
                    on_sheet(value, child, stack)
                else:
                    walk(value, child, stack)

    walk(spec, "", [])
    return problems


def harvest_by_page(pdf: Path, pages) -> dict:
    out = {}
    for c in sheets.harvest(pdf, sorted(set(pages))):
        out.setdefault(c.page, set()).add(c.feet)
    return out


def count_numbers(node) -> int:
    if _is_number(node):
        return 1
    if isinstance(node, dict):
        return sum(count_numbers(v) for v in node.values())
    if isinstance(node, list):
        return sum(count_numbers(v) for v in node)
    return 0


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m adu_kit.spec_lint",
                                 description="Check that every number in a model spec is cited.")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--pdf", type=Path, help="the plan set, to check drawn lengths are on their sheets")
    args = ap.parse_args(argv)
    try:
        import yaml
    except ImportError:
        print("spec_lint.py: PyYAML is not installed", file=sys.stderr)
        return 1
    try:
        spec = yaml.safe_load(args.spec.read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as e:
        print(f"spec_lint.py: cannot read {args.spec}: {e}", file=sys.stderr)
        return 1
    harvested = None
    if args.pdf:
        try:
            harvested = harvest_by_page(args.pdf, sheet_pages(spec).values() or [1])
        except sheets.SheetsError as e:
            print(f"spec_lint.py: {e}", file=sys.stderr)
            return 1
    problems = lint(spec, harvested)
    if problems:
        print(f"FAIL  {args.spec}: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"PASS  {args.spec}: {count_numbers(spec)} number(s), every one cited"
          + ("; every drawn length found on its sheet" if harvested is not None else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
