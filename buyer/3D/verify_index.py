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
its shape checked before any gate touches it. Each row is judged by
`model_contract.row_problems()` -- the same contract build_index.py holds
itself to -- and only rows that meet it reach the gates that read their
fields, so a malformed id or level can fail gate 3 but cannot crash gate 1.
"""
import json
from pathlib import Path

import build_index
import model_contract

INDEX = build_index.INDEX
# Paths in the index are relative to the index's own directory, which is how
# the page resolves them -- never to this script's directory.
ROOT = INDEX.parent

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
        problems.append(f"models.json is unreadable or not valid JSON: {e}")
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
    return doc, rows


def main():
    problems = []
    print("=" * 76)
    print("models.json — the page's index")
    print("=" * 76)

    doc, have = load_index(problems)
    verdicts = [model_contract.row_problems(r, f"row {i}")
                for i, r in enumerate(have)]
    # Rows that meet the contract: string id and name, relative-path strings,
    # a full-detail level. Every gate that reads a row's fields reads these.
    good = [r for r, bad in zip(have, verdicts) if not bad]

    # ── 1. the committed index still describes what is on disk ────────────
    # build() exits on a manifest it cannot index (bad identity, a duplicate
    # id, no full-detail .glb). Here that is a failed gate with the
    # generator's own message, not an exit that skips the rest of the report.
    n_before = len(problems)
    try:
        fresh_doc = build_index.build()
    except SystemExit as e:
        problems.append(f"a fresh scan failed: {e}")
        fresh_doc = None
    if fresh_doc is not None:
        hi = {r["id"] for r in good}
        fi = {r["id"] for r in fresh_doc["models"]}
        for extra in sorted(fi - hi):
            problems.append(f"{extra} is exported on disk but missing from "
                            f"the index — an unindexed model is invisible to "
                            f"the page")
        for gone in sorted(hi - fi):
            problems.append(f"{gone} is in the index but not on disk")
        # THE WHOLE DOCUMENT: the note is generated too, and a hand-edited
        # one must not pass a gate that says "matches a fresh scan".
        if hi == fi and doc != fresh_doc:
            problems.append("the index names the right models but its rows or "
                            "note differ from a fresh scan — re-run "
                            "build_index.py")
    ok = len(problems) == n_before and doc != {}
    print(f"  [{'PASS' if ok else 'FAIL'}] the index matches a fresh scan — "
          f"{len(have)} model(s): "
          f"{', '.join(sorted(r['id'] for r in good)) or 'none'}")

    # ── 1b. ids are unique ────────────────────────────────────────────────
    # The checks above compare SETS of ids, which collapse duplicates. A page
    # selecting by id reaches only one of two rows that share one.
    ids = [r["id"] for r in good]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    problems += [f"id {d} appears in more than one row" for d in dupes]
    print(f"  [{'PASS' if not dupes else 'FAIL'}] every id is unique"
          + (f" — duplicated: {', '.join(dupes)}" if dupes else ""))

    # ── 2. every path resolves, checked by stat and not by the generator ──
    missing, n_paths = [], 0
    for r in good:
        checks = [("dir", r["dir"], Path.is_dir)]
        checks += [(k, r[k], Path.is_file) for k in FILE_KEYS]
        checks += [(f"levels.{lod}", v, Path.is_file)
                   for lod, v in r["levels"].items()]
        for key, v, kind in checks:
            if v is None:
                continue
            n_paths += 1
            if not kind(ROOT / v):
                want = "directory" if kind is Path.is_dir else "file"
                missing.append(f"{r['id']}.{key} -> {v} (not a {want})")
    problems += [f"path does not resolve: {m}" for m in missing]
    print(f"  [{'PASS' if not missing else 'FAIL'}] every path resolves — "
          f"{n_paths} checked" + (f", {len(missing)} broken" if missing else ""))

    # ── 3. every row meets the index contract ─────────────────────────────
    # model_contract.row_problems: every key present; id, name, area_key and
    # area_source non-empty strings; area_sf a positive number; storeys a
    # {count, loft} block; paths relative strings; levels named lod<N>; and
    # a full-detail file, lod0 or primary. `thumbnail` may be null (#111).
    thin = [p for bad in verdicts for p in bad]
    problems += thin
    print(f"  [{'PASS' if not thin else 'FAIL'}] every row meets the index "
          f"contract" + (f" — {len(thin)} problem(s)" if thin else ""))

    # ── 4. the barn cabin is a row, not a special case ────────────────────
    # THE POINT OF THE WHOLE ISSUE, ASKED DIRECTLY. Every row must be reachable
    # by the same generic access, with no key that only one model has and no
    # field a page would have to branch on.
    shapes = {tuple(sorted(r)) for r in have if isinstance(r, dict)}
    if len(shapes) > 1:
        problems.append(f"index rows do not share a shape: {sorted(shapes)} — "
                        f"a page would have to know which model it loaded")
    print(f"  [{'PASS' if len(shapes) <= 1 else 'FAIL'}] every row has the same "
          f"shape — no model is a special case")

    # ── 5. nothing in the index names a building the page must know ───────
    # A row may name itself; the NOTE may not. Both the id and the display
    # name count -- "Barn Cabin" is a building name as much as the id is.
    note = doc.get("note") if isinstance(doc.get("note"), str) else ""
    leaked = sorted({n for r in good for n in (r["id"], r["name"])
                     if n in note})
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

    # ── 7. the manifest names only what its .glb contains ─────────────────
    # A swap set whose target material is not in the file changes nothing on
    # screen, and a presence option whose node is not in the file shows an
    # empty room; neither throws in a browser. Checked against lod0, the full-
    # detail level -- coarser levels drop furniture by design -- and read from
    # the .glb itself, since the index's promise is about what ships. The
    # contract guarantees every good row HAS a full-detail file, so the only
    # row skipped here is one whose file gate 2 already reports missing.
    unmatched, n_names = [], 0
    for r in good:
        rid = r["id"]
        glb, manifest = r["levels"].get("lod0") or r["primary"], r["manifest"]
        if not ((ROOT / glb).is_file() and (ROOT / manifest).is_file()):
            continue
        try:
            have_mats, have_nodes = model_contract.glb_names(ROOT / glb)
        except (ValueError, OSError) as e:
            unmatched.append(f"{rid}: {glb} unreadable: {e}")
            continue
        try:
            want_mats, want_nodes = model_contract.manifest_names(
                json.loads((ROOT / manifest).read_text()))
        except (ValueError, OSError) as e:
            unmatched.append(f"{rid}: {manifest} unreadable: {e}")
            continue
        n_names += len(want_mats) + len(want_nodes)
        unmatched += [f"{rid}: material {x} is a swap target but not in {glb}"
                      for x in sorted(want_mats - have_mats)]
        unmatched += [f"{rid}: node {x} is named by presence or views but not in {glb}"
                      for x in sorted(want_nodes - have_nodes)]
    problems += unmatched
    print(f"  [{'PASS' if not unmatched else 'FAIL'}] every manifest names only "
          f"what its .glb contains — {n_names} name(s) checked"
          + (f", {len(unmatched)} unmatched" if unmatched else ""))

    # ── 8. every block the page renders is whole or absent ────────────────
    # `sets`, `presence` and `disclosure` drive the option rail; `views` and
    # `dimensions` the controls under the viewer. The page refuses a block
    # that is malformed anywhere rather than acting on the entries that parse
    # (#108, #109). Catch it here, where it is a failed gate, not there, where
    # it is a missing control nobody notices.
    shapes = []
    for r in good:
        path = ROOT / r["manifest"]
        try:
            m = json.loads(path.read_text())
        except (ValueError, OSError):
            continue  # gate 7 already reports an unreadable manifest
        shapes += [f"{r['id']}: {p}" for p in model_contract.display_problems(m)]
    problems += shapes
    print(f"  [{'PASS' if not shapes else 'FAIL'}] every manifest's sets, presence, "
          f"disclosure, views and dimensions are well-formed or absent"
          + (f" — {len(shapes)} problem(s)" if shapes else ""))

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
