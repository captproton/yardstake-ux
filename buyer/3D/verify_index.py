"""
verify_index.py — gates on models.json, the page's list of what exists.

    python3 verify_index.py

Needs no Blender: the index is JSON about files, and every question here can
be answered from the filesystem.

WHAT IS ACTUALLY AT RISK. Not the scan -- `build_index.py` walks the
directory, so it cannot miss a model it can see. The risk is that the index is
a COMMITTED FILE and the models move underneath it: somebody adds Laurel and
does not re-run the generator, or renames an export and the index goes on
naming the old path. So the gates here are (1) does the committed file still
match a fresh scan, and (2) does every path in it resolve.

THE WITNESS IS NOT THE THING UNDER TEST (rule 40). Gate 2 deliberately does
not call build_index.py: it re-reads `models.json` as published and stats each
path itself, which is what a browser will do. A gate that asked the generator
whether the generator was right would pass on any index the generator could
produce, including a wrong one.

A BROKEN INDEX IS A FAILED GATE, NOT A TRACEBACK. The file is parsed once and
its shape checked before any gate touches it; every later gate works from that
one parsed value.
"""
import json
from pathlib import Path

import build_index

HERE = Path(__file__).resolve().parent
INDEX = HERE / "models.json"

# Fields a page needs to render a card at all. `thumbnail` is NOT here: a
# model with no render yet is a real state (#111), and the page falls back.
REQUIRED = ("id", "name", "area_sf", "storeys", "dir", "manifest", "levels")

# Paths a browser fetches as files. `dir` is the one directory; a directory
# named `x.glb` satisfies `.exists()` and still cannot be fetched.
FILE_KEYS = ("manifest", "primary", "thumbnail")


def load_index(problems):
    """Parse models.json once and check its shape. Returns (doc, rows)."""
    if not INDEX.is_file():
        problems.append("models.json does not exist; run build_index.py")
        return {}, []
    try:
        doc = json.loads(INDEX.read_text())
    except (ValueError, OSError) as e:
        problems.append(f"models.json is not valid JSON: {e}")
        return {}, []
    if not isinstance(doc, dict):
        problems.append(f"models.json's root is a {type(doc).__name__}, "
                        f"not an object")
        return {}, []
    rows = doc.get("models")
    if not isinstance(rows, list):
        problems.append(f"models.json's `models` is a {type(rows).__name__}, "
                        f"not a list")
        return doc, []
    bad = [i for i, r in enumerate(rows) if not isinstance(r, dict)]
    if bad:
        problems.append(f"models.json rows {bad} are not objects")
    return doc, [r for r in rows if isinstance(r, dict)]


def main():
    problems = []
    print("=" * 76)
    print("models.json — the page's index")
    print("=" * 76)

    doc, have = load_index(problems)

    # ── 1. the committed index still describes what is on disk ────────────
    # build() exits on a manifest it cannot index (bad shape, no id, a
    # duplicate id). Here that is a failed gate with the generator's own
    # message, not an exit that skips the rest of the report.
    n_before = len(problems)
    try:
        fresh_doc = build_index.build()
    except SystemExit as e:
        problems.append(f"a fresh scan failed: {e}")
        fresh_doc = None
    if fresh_doc is not None:
        fresh = fresh_doc["models"]
        hi = {r.get("id") for r in have}
        fi = {r.get("id") for r in fresh}
        for extra in sorted(fi - hi):
            problems.append(f"{extra} is exported on disk but missing from "
                            f"the index — an unindexed model is invisible to "
                            f"the page")
        for gone in sorted(hi - fi, key=str):
            problems.append(f"{gone} is in the index but not on disk")
        # THE WHOLE DOCUMENT: the note is generated too, and a hand-edited
        # one must not pass a gate that says "matches a fresh scan".
        if hi == fi and doc != fresh_doc:
            problems.append("the index names the right models but its rows or "
                            "note differ from a fresh scan — re-run "
                            "build_index.py")
    ok = len(problems) == n_before and not (have == [] and doc == {})
    print(f"  [{'PASS' if ok else 'FAIL'}] the index matches a fresh scan — "
          f"{len(have)} model(s): "
          f"{', '.join(sorted(str(r.get('id')) for r in have)) or 'none'}")

    # ── 1b. ids are unique ────────────────────────────────────────────────
    # The checks above compare SETS of ids, which collapse duplicates. A page
    # selecting by id reaches only one of two rows that share one.
    ids = [r.get("id") for r in have]
    dupes = sorted({str(i) for i in ids if ids.count(i) > 1})
    problems += [f"id {d} appears in more than one row" for d in dupes]
    print(f"  [{'PASS' if not dupes else 'FAIL'}] every id is unique"
          + (f" — duplicated: {', '.join(dupes)}" if dupes else ""))

    # ── 2. every path resolves, checked by stat and not by the generator ──
    missing, n_paths = [], 0
    for r in have:
        rid = r.get("id")
        checks = [("dir", r.get("dir"), Path.is_dir)]
        checks += [(k, r.get(k), Path.is_file) for k in FILE_KEYS]
        levels = r.get("levels")
        if isinstance(levels, dict):
            checks += [(f"levels.{lod}", v, Path.is_file)
                       for lod, v in levels.items()]
        for key, v, kind in checks:
            if not v:
                continue
            n_paths += 1
            if not isinstance(v, str) or not kind(HERE / v):
                want = "directory" if kind is Path.is_dir else "file"
                missing.append(f"{rid}.{key} -> {v} (not a {want})")
    problems += [f"path does not resolve: {m}" for m in missing]
    print(f"  [{'PASS' if not missing else 'FAIL'}] every path resolves — "
          f"{n_paths} checked" + (f", {len(missing)} broken" if missing else ""))

    # ── 3. a row carries what a card needs ────────────────────────────────
    thin = []
    for r in have:
        for f in REQUIRED:
            if r.get(f) in (None, "", {}, []):
                thin.append(f"{r.get('id') or '?'}.{f}")
    problems += [f"index row is missing {t}" for t in thin]
    print(f"  [{'PASS' if not thin else 'FAIL'}] every row can render a card — "
          f"{', '.join(REQUIRED)}")

    # ── 4. the barn cabin is a row, not a special case ────────────────────
    # THE POINT OF THE WHOLE ISSUE, ASKED DIRECTLY. Every row must be reachable
    # by the same generic access, with no key that only one model has and no
    # field a page would have to branch on.
    shapes = {tuple(sorted(r)) for r in have}
    if len(shapes) > 1:
        problems.append(f"index rows do not share a shape: {sorted(shapes)} — "
                        f"a page would have to know which model it loaded")
    print(f"  [{'PASS' if len(shapes) <= 1 else 'FAIL'}] every row has the same "
          f"shape — no model is a special case")

    # ── 5. nothing in the index names a building the page must know ───────
    # A row may name itself; the NOTE may not. Both the id and the display
    # name count -- "Barn Cabin" is a building name as much as the id is.
    note = doc.get("note") if isinstance(doc.get("note"), str) else ""
    leaked = sorted({n for r in have for n in (r.get("id"), r.get("name"))
                     if isinstance(n, str) and n and n in note})
    problems += [f"the index's own note names {m}" for m in leaked]
    print(f"  [{'PASS' if not leaked else 'FAIL'}] the index's scaffolding "
          f"names no building")

    # ── 6. no model is on disk and silently off the index ─────────────────
    # Gate 1 compares against a scan that, by design, skips a model with no
    # manifest. So a model whose export never landed passes gate 1 and is
    # invisible to the page. #106 names that an export failure; ask it here.
    stranded = build_index.unexported()
    problems += [f"{m} has spec.yaml but no export/variants.json — a model on "
                 f"disk that the page cannot see is an export failure"
                 for m in stranded]
    print(f"  [{'PASS' if not stranded else 'FAIL'}] every model with a spec "
          f"is exported" + (f" — unexported: {', '.join(stranded)}"
                            if stranded else ""))

    print("-" * 76)
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("all index gates pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
