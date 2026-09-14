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
   every source cites a drawing someone can open, not a file path.
3. A WRITTEN LENGTH AGREES WITH ITS FEET. Where a mapping has `raw` and `ft`
   and the raw string is a length, they agree to within 0.0005 ft.
4. A DRAWN LENGTH IS ON ITS SHEET (with --pdf). A feet-and-inches `raw`
   whose `source` names sheets must be one of the dimensions adu_kit.sheets
   harvests from those sheets' pages. Inch-only strings are not harvested and
   are not checked here.

It reads the spec and reports. It writes nothing.
"""
from __future__ import annotations

import argparse
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


def sheet_pages(spec) -> dict:
    """{sheet id: pdf page} from `sheet_index.sheets`."""
    index = spec.get("sheet_index") if isinstance(spec, dict) else None
    rows = index.get("sheets") if isinstance(index, dict) else None
    out = {}
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and isinstance(row.get("id"), str) and _is_number(row.get("pdf_page")):
            out[row["id"]] = int(row["pdf_page"])
    return out


def _named_sheets(text: str, ids) -> list:
    return [i for i in ids if re.search(rf"(?<![\w.-]){re.escape(i)}(?![\w-]|\.\d)", text)]


def lint(spec, harvested: Optional[dict] = None) -> list:
    """Every problem in a parsed spec. `harvested` is {pdf page: set of exact
    feet} from the plan set, for rule 4; None skips rule 4."""
    if not isinstance(spec, dict):
        return [f"the spec must be a mapping, found {type(spec).__name__}"]
    ids = sheet_pages(spec)
    problems = []
    if not ids:
        problems.append("sheet_index.sheets lists no sheet with an id and a pdf_page, "
                        "so no source can name a sheet")

    def walk(node, path, mappings):
        if isinstance(node, dict):
            here = mappings + [node]
            own = node.get("source")
            if isinstance(own, str) and ids and not _named_sheets(own, ids):
                problems.append(f"{path}.source names no sheet in sheet_index: {own!r}")
            # A length's sheet comes from its own source, or the mapping above
            # it -- a schedule row cites the schedule once for its width,
            # height and sill.
            src = own if isinstance(own, str) else (
                mappings[-1].get("source") if mappings and isinstance(mappings[-1], dict) else None)
            if "raw" in node and "ft" in node and isinstance(node["raw"], str) and _is_number(node["ft"]):
                feet = sheets.parse_length(node["raw"])
                if feet is not None and abs(float(feet) - node["ft"]) > FT_TOLERANCE:
                    problems.append(f"{path}: raw {node['raw']} is {float(feet):.4f} ft, not ft {node['ft']}")
                if (feet is not None and harvested is not None and isinstance(src, str)
                        and "'" in node["raw"] and '"' in node["raw"]):
                    pages = [ids[i] for i in _named_sheets(src, ids)]
                    if pages and not any(feet in harvested.get(p, ()) for p in pages):
                        problems.append(f"{path}: raw {node['raw']} is not a dimension on "
                                        f"{', '.join(_named_sheets(src, ids))} (pages {pages})")
            for key, value in node.items():
                child = f"{path}.{key}" if path else str(key)
                if _is_number(value):
                    if not (len(here) > 1 and (_cites(here[-1]) or (len(here) > 2 and _cites(here[-2])))):
                        problems.append(f"{child} = {value} has no source, derived or assumed")
                else:
                    walk(value, child, here)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                child = f"{path}[{i}]"
                if _is_number(value):
                    if not (len(mappings) > 1 and (_cites(mappings[-1]) or (len(mappings) > 2 and _cites(mappings[-2])))):
                        problems.append(f"{child} = {value} has no source, derived or assumed")
                else:
                    walk(value, child, mappings)

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
