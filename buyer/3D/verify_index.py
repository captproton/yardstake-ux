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
"""
import json
from pathlib import Path

import build_index

HERE = Path(__file__).resolve().parent
INDEX = HERE / "models.json"

# Fields a page needs to render a card at all. `thumbnail` is NOT here: a
# model with no render yet is a real state (#111), and the page falls back.
REQUIRED = ("id", "name", "area_sf", "dir", "manifest", "levels")


def main():
    problems = []
    print("=" * 76)
    print("models.json — the page's index")
    print("=" * 76)

    # ── 1. the committed index still describes what is on disk ────────────
    fresh = build_index.build()["models"]
    if not INDEX.is_file():
        problems.append("models.json does not exist; run build_index.py")
        have = []
    else:
        try:
            have = json.loads(INDEX.read_text()).get("models", [])
        except ValueError as e:
            problems.append(f"models.json is not valid JSON: {e}")
            have = []

    hi = {r.get("id") for r in have}
    fi = {r.get("id") for r in fresh}
    for extra in sorted(fi - hi):
        problems.append(f"{extra} is exported on disk but missing from the "
                        f"index — an unindexed model is invisible to the page")
    for gone in sorted(hi - fi):
        problems.append(f"{gone} is in the index but not on disk")
    if hi == fi and have != fresh:
        problems.append("the index names the right models but its rows differ "
                        "from a fresh scan — re-run build_index.py")
    print(f"  [{'PASS' if not problems else 'FAIL'}] the index matches a fresh "
          f"scan — {len(fresh)} model(s): {', '.join(sorted(fi)) or 'none'}")

    # ── 2. every path resolves, checked by stat and not by the generator ──
    missing, n_paths = [], 0
    for r in have:
        for key in ("dir", "manifest", "primary", "thumbnail"):
            v = r.get(key)
            if v:
                n_paths += 1
                if not (HERE / v).exists():
                    missing.append(f"{r.get('id')}.{key} -> {v}")
        for lod, v in (r.get("levels") or {}).items():
            n_paths += 1
            if not (HERE / v).exists():
                missing.append(f"{r.get('id')}.levels.{lod} -> {v}")
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
    # A row may name its own id; the NOTE and the structure may not. This is
    # the rule the page plan states, enforced on the one file the page is
    # handed first.
    scaffold = json.loads(INDEX.read_text()) if INDEX.is_file() else {}
    leaked = [r.get("id") for r in have
              if r.get("id") and r.get("id") in (scaffold.get("note") or "")]
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
