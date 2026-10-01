#!/usr/bin/env python3
"""
new_model.py -- start a model from a plan set: intake first, then a directory.

    python3 new_model.py PLANS.pdf --id willow_a2_460 --name "Willow" --issue 170
    python3 new_model.py PLANS.pdf --id willow_a2_460 --name "Willow" --intake-only

Run from anywhere. Needs poppler (`pdftotext`, `pdfinfo`) and the kit's
harvester; no Blender, no PyYAML.

WHAT IT DOES. The first hours of a model are the same every time (they were
for the barn cabin and for Laurel): find out whether the sheets have a text
layer, list the sheets, harvest the dimension candidates, and lay down the
files every model has. This does exactly that and nothing about the building.

  1. INTAKE. Pages, characters of text per page, the sheet ids it can read, and
     how many dimension candidates the harvester finds. A plan set with no text
     layer (the barn cabin's) says so and stops the scaffold unless
     --allow-raster is given: its dimensions are read by eye, which is the slow
     path, and the schedule should know before the work starts.
     It also counts the words that say what class of building this is (LOFT,
     GABLE, SHED, DORMER, CRAWL...), as a hint. It is a hint: a word on a sheet
     is not a roof, and the spec's citations are where a roof gets decided.
  2. FILES, in models/<id>/ (refused if the directory exists):
       spec.yaml         meta and sheet_index only; every number still to be cited
       docs/INTAKE.md    the report above
       docs/candidates.yaml  the harvester's output, never read back
       docs/PLAN.md      the tiered plan (ship first, then upgrade), to be edited
       gates.json        the gates that exist now; add each one as it is written
       EXPORT_PENDING    names --issue, so verify_index.py accepts a model with
                         a spec and no export yet
       .gitignore        the per-model set
     The plan set itself is NOT copied or committed. `example plans/` is
     ignored on purpose, and a 13 MB PDF is committed only when a test needs it.

WHAT IT DOES NOT DO. It writes no dimension into a spec. The harvester's rule
holds (adu_kit/sheets.py): a machine-read number that lands in a spec unchecked
carries false confidence. It also writes no build.py; there is not yet a
builder that is not one model's (docs/KIT-AUDIT.md says what would be).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from adu_kit import sheets  # noqa: E402

ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
# "text layer" threshold: the barn cabin's whole set yields 7 bytes; Laurel's
# yields 86 KB over 20 pages. Anything under this per page is a scan.
MIN_CHARS_PER_PAGE = 200
CLASS_WORDS = ("LOFT", "GABLE", "SHED", "HIP", "DORMER", "CRAWL", "SLAB", "STUCCO",
               "SIDING", "PORCH", "GARAGE", "STAIR", "VAULTED", "MEZZANINE", "2ND FLOOR")


class ScaffoldError(Exception):
    pass


def _need(tool):
    if not shutil.which(tool):
        raise ScaffoldError(f"`{tool}` is not on PATH (brew install poppler)")


def intake(pdf: Path) -> dict:
    """Facts about a plan set, from its own text. Never a dimension in a spec."""
    if not pdf.is_file():
        raise ScaffoldError(f"{pdf}: no such file")
    _need("pdfinfo")
    _need("pdftotext")
    pages = sheets.page_count(pdf)
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout
    chars = len(re.sub(r"\s", "", text))       # -layout pads with spaces; count ink
    parsed = sheets.read_pages(pdf)
    ids = [(p.number if hasattr(p, "number") else i + 1, sheets.sheet_id(p))
           for i, p in enumerate(parsed)]
    cands = sheets.harvest(pdf) if chars >= MIN_CHARS_PER_PAGE * pages else []
    upper = text.upper()
    words = {w: len(re.findall(r"\b" + re.escape(w) + r"\b", upper)) for w in CLASS_WORDS}
    return {"pdf": pdf, "pages": pages, "chars": chars,
            "raster": chars < MIN_CHARS_PER_PAGE * pages,
            "sheets": ids, "candidates": cands,
            "words": {w: n for w, n in words.items() if n}}


def report(info: dict, model_id: str) -> str:
    lines = [f"# Intake: {model_id}", "",
             f"Source: `{info['pdf'].name}` -- {info['pages']} pages, "
             f"{info['chars']:,} characters of text (spaces excluded).", ""]
    if info["raster"]:
        lines += ["**No usable text layer.** This plan set is scanned. The harvester has "
                  "nothing to read, so every dimension is read by eye, as the barn cabin's "
                  "were (2,927 spec lines). Budget for the slow path: the harvester was the "
                  "biggest saving on Laurel and this model does not get it.", ""]
    else:
        lines += [f"**Text layer present.** The harvester found {len(info['candidates'])} "
                  "feet-and-inches candidates (`docs/candidates.yaml`). P1 is a review of "
                  "machine output, not a transcription.", ""]
    named = [(pg, sid) for pg, sid in info["sheets"] if sid]
    lines += [f"Sheets the harvester could name: {len(named)} of {info['pages']}.", ""]
    lines += ["| PDF page | Sheet |", "|---|---|"]
    lines += [f"| {pg} | {sid or '(not read)'} |" for pg, sid in info["sheets"]]
    lines += ["", "## Class hints", "",
              "Words on the sheets that bear on what kind of building this is. A hint "
              "only: the spec's citations decide the roof, the storeys and the foundation.", ""]
    if info["words"]:
        lines += [f"- `{w}`: {n}" for w, n in sorted(info["words"].items(), key=lambda kv: -kv[1])]
    else:
        lines += ["- none of the watched words appear"]
    lines += ["", "Laurel's class (what `models/laurel_a1_460/build.py` already builds, "
              "with one roof class to swap): one storey, slab on grade, a rectangle, "
              "one roof plane. `LOFT`, `DORMER`, `CRAWL` or `2ND FLOOR` here means the "
              "barn cabin's class, which has no spec-driven builder yet.", ""]
    return "\n".join(lines)


SPEC = '''# {title} -- dimensional spec (started by new_model.py; nothing in it is measured yet)
# Source plan set: {pdf_name}
#
# EVERY NUMBER IS CITED. `source` names a sheet listed in sheet_index and where on
# it; `derived` shows the arithmetic; `assumed` says why no sheet says it.
# adu_kit/spec_lint.py fails any number without one. Candidates are in
# docs/candidates.yaml: check each on its sheet, then copy what you accept here.
# Read models/laurel_a1_460/spec.yaml for the shape; its keys are what
# adu_kit and the page read.

meta:
  model_id: {model_id}
  display_name: {name}
  source_pdf_pages: {{count: {pages}, derived: "pdfinfo reports {pages} pages"}}

sheet_index:
  source: "{index_sheet} SHEET INDEX for ids and titles; each page's title block for its id"
  sheets:
{sheet_rows}
'''

GITIGNORE = "spec.json\n__pycache__/\n*.blend\n*.blend1\nrenders/\n"

GATES = '''{{
  "gates": [
    {{
      "name": "spec lint (every number cited)",
      "tier": "fast",
      "requires": ["yaml"],
      "cmd": ["{{python}}", "-m", "adu_kit.spec_lint", "models/{model_id}/spec.yaml"]
    }}
  ]
}}
'''

PLAN = '''# {model_id} -- build plan

Source: `{pdf_name}` ({pages} pages). See [`INTAKE.md`](INTAKE.md) for what the
plan set is and whether it has a text layer.

**Written from `new_model.py`'s template, then edited.** The template is
tiered on purpose. A model is *on the page* when Tier A is done; Tier B is
detail that makes it more faithful, and each item can wait or be dropped
without the page noticing. Laurel took 12 steps; it was on the page at step 7.

## Tier A -- ships (the model is on the page)

1. **Spec.** Cite every number; settle the roof form, the option and the frame
   in `spec.yaml` (`docs/candidates.yaml` is the raw material). Gate: `spec_lint`.
2. **Build.** Slab, walls, partitions, roof, every opening cut. Gate: a
   `build` gate per claim, and no dimension literal in the script.
3. **Overlay.** Hold the model to the elevations' ink, by named features.
4. **Export.** Materials (one finish), three levels of detail, manifest, index
   row, front declared. Delete `EXPORT_PENDING`. The page needs no code.

## Tier B -- upgrades (each optional, each its own PR)

5. Interior overlay against the floor plan's ink. 6. Trim. 7. Finish choices
(stucco/siding) and textures. 8. Fixtures and equipment. 9. Furniture.
10. Optional structures (canopy, porch).

## Decisions this model inherits

Trim defaults are `assumed` from the barn cabin, exterior finish is a presence
group, furniture arrangements are reused, "assumed" carries a reason. See
`models/laurel_a1_460/docs/PLAN.md` for why. Override in the spec, not the code.

## Sequence

One line per pull request; mark each Done with its number.

'''


def scaffold(pdf: Path, model_id: str, name: str, issue: int, models_dir: Path,
             allow_raster: bool, intake_only: bool) -> int:
    if not ID_RE.match(model_id):
        raise ScaffoldError(f"--id {model_id!r}: use lower_snake with an area, like willow_a2_460")
    info = intake(pdf)
    text = report(info, model_id)
    if intake_only:
        print(text)
        return 0
    if info["raster"] and not allow_raster:
        print(text)
        raise ScaffoldError("no text layer; nothing was written. Re-run with --allow-raster "
                            "to start a by-eye model anyway")
    target = models_dir / model_id
    if target.exists():
        raise ScaffoldError(f"{target} exists; this never overwrites")
    (target / "docs").mkdir(parents=True)
    rows = "\n".join(f'  - {{pdf_page: {pg}, id: {sid}, title: "(fill in)"}}'
                     for pg, sid in info["sheets"] if sid) \
        or "    []   # no sheet id could be read; fill in by hand"      # indented under `sheets:`
    (target / "spec.yaml").write_text(SPEC.format(
        # A NAME IS FREE TEXT: as the YAML value it is JSON-quoted (a valid YAML
        # scalar, so `A "Plus"` cannot break the file); in a comment, one line.
        name=json.dumps(name), title=" ".join(name.split()),
        pdf_name=" ".join(pdf.name.split()), model_id=model_id, pages=info["pages"], sheet_rows=rows,
        index_sheet=next((sid for _, sid in info["sheets"] if sid), "the title sheet")))
    (target / "docs" / "INTAKE.md").write_text(text)
    # ALWAYS WRITTEN: spec.yaml, PLAN.md and INTAKE.md all point at this file, so
    # a scan (where harvesting found nothing to read) gets the valid empty document.
    sheets.write_candidates(sheets.to_yaml(info["candidates"], pdf.name),
                            target / "docs" / "candidates.yaml")
    (target / "docs" / "PLAN.md").write_text(PLAN.format(
        model_id=model_id, pdf_name=pdf.name, pages=info["pages"]))
    (target / "gates.json").write_text(GATES.format(model_id=model_id))
    (target / "EXPORT_PENDING").write_text(
        f"No export yet: the spec is being written.\nissue: #{issue}\n")
    (target / ".gitignore").write_text(GITIGNORE)
    print(f"wrote {target}")
    print(f"  {len(info['candidates'])} dimension candidates, "
          f"{'NO text layer' if info['raster'] else 'text layer present'}")
    print("next: python3 verify_index.py && python3 run_gates.py --model " + model_id)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Intake a plan set and start a model directory.")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--id", required=True, dest="model_id", help="e.g. willow_a2_460")
    ap.add_argument("--name", help='display name, e.g. "Willow"')
    ap.add_argument("--issue", type=int, help="the issue that closes the export (EXPORT_PENDING)")
    ap.add_argument("--intake-only", action="store_true", help="print the report; write nothing")
    ap.add_argument("--allow-raster", action="store_true", help="scaffold a scanned plan set too")
    ap.add_argument("--models-dir", type=Path, default=ROOT / "models", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    try:
        if not a.intake_only and (not a.name or not a.issue or a.issue < 1):
            raise ScaffoldError("--name and --issue N are required (the issue goes in "
                                "EXPORT_PENDING, which verify_index.py demands)")
        return scaffold(a.pdf, a.model_id, a.name or a.model_id, a.issue or 0, a.models_dir,
                        a.allow_raster, a.intake_only)
    except (ScaffoldError, sheets.SheetsError, subprocess.CalledProcessError) as e:
        print(f"new_model.py: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
