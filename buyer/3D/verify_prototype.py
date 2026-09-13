"""
verify_prototype.py — gates on the configurator page itself.

    python3 verify_prototype.py

Needs no browser and no Blender. What a browser must confirm -- that the page
loads, lights, orbits and frames -- is checked by opening it; what can be
checked from the files is checked here, on every change.

WHAT IS AT RISK. The page plan's one rule: the page knows nothing about any
building. The failure is not dramatic. It is one convenience -- a material
name in a lookup, a node name in a camera preset, a view id in a button, a
display name in a fallback -- and the next model inherits it silently. So
gate 1 collects every name any indexed model publishes, from its manifest AND
from its .glb, and fails if the page's own files mention one.

A BROKEN FIXTURE OR INDEX IS A FAILED GATE, NOT A TRACEBACK -- the same rule
verify_index.py follows. Every document is read through `load_json()` and
every row through `model_contract.row_problems()` before anything is taken
from it.
"""
import json
import os
import re
from pathlib import Path

import build_index
import model_contract

HERE = Path(__file__).resolve().parent
PROTO = HERE / "prototype"
FIXTURE_INDEX = PROTO / "fixtures" / "models.json"

# The page's own files. Fixtures are data about a model, not the page, and
# are allowed to name themselves.
PAGE_FILES = sorted(p for p in PROTO.iterdir()
                    if p.is_file() and p.suffix in (".html", ".js", ".css"))

PIN = re.compile(r"three@(\d+\.\d+\.\d+)/")

# What app.js imports. The import map must resolve both, or nothing loads.
REQUIRED_IMPORTS = ("three", "three/addons/")

# Names that are also ordinary words. A view id of `full` must not fail the
# page for saying "full detail" in a sentence, so these count as a leak only
# as a whole quoted string -- which is how a hard-coded choice would appear.
LITERAL_ONLY = {"view id", "option id"}


def rel(p):
    return os.path.relpath(p, HERE)


def load_json(path, problems, what):
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError) as e:
        problems.append(f"{what} {rel(path)} is unreadable: {e}")
        return None


def published_names(index_path, problems):
    """{name: what it is} for every model in an index: identity, manifest
    blocks, and the material and node names inside its full-detail .glb.
    Anything that cannot be read is a problem, since a name that was never
    collected is a name the gate cannot catch."""
    root = index_path.parent
    names = {}

    def add(value, kind):
        if isinstance(value, str) and len(value) >= 3:
            names.setdefault(value, kind)

    def objects(v):
        return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []

    doc = load_json(index_path, problems, "index")
    rows = doc.get("models") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        if doc is not None:
            problems.append(f"index {rel(index_path)} has no `models` list")
        return names

    for i, r in enumerate(rows):
        bad = model_contract.row_problems(r, f"{rel(index_path)} row {i}")
        if bad:
            problems += bad
            continue
        add(r["id"], "model id")
        add(r["name"], "model name")

        manifest = load_json(root / r["manifest"], problems, "manifest")
        if isinstance(manifest, dict):
            try:
                mats, nodes = model_contract.manifest_names(manifest)
            except ValueError as e:
                problems.append(f"manifest {r['manifest']} is malformed: {e}")
                mats, nodes = set(), set()
            for m in mats:
                add(m, "material")
            for n in nodes:
                add(n, "node")
            for block in ("sets", "presence"):
                for st in objects(manifest.get(block)):
                    add(st.get("id"), f"{block} id")
                    add(st.get("room"), "room")
                    for o in objects(st.get("options")):
                        add(o.get("id"), "option id")
            for v in objects(manifest.get("views")):
                add(v.get("id"), "view id")
                hide = v.get("hide")
                for n in hide if isinstance(hide, list) else []:
                    add(n, "node")
        elif manifest is not None:
            problems.append(f"manifest {r['manifest']} is not an object")

        glb = r["levels"].get("lod0") or r["primary"]
        try:
            g_mats, g_nodes = model_contract.glb_names(root / glb)
        except (ValueError, OSError) as e:
            problems.append(f"{glb} is unreadable: {e}")
            continue
        for m in g_mats:
            add(m, "material")
        for n in g_nodes:
            add(n, "node")
    return names


def main():
    problems = []
    print("=" * 76)
    print("prototype/ — the configurator page")
    print("=" * 76)

    # ── 1. the page names no building, room, node, material or choice ─────
    names, unread = {}, []
    for index in (build_index.INDEX, FIXTURE_INDEX):
        if index.is_file():
            names.update(published_names(index, unread))
    leaks = []
    for f in PAGE_FILES:
        text = f.read_text()
        for name, kind in sorted(names.items()):
            if kind in LITERAL_ONLY:
                pattern = rf"(['\"`]){re.escape(name)}\1"
            else:
                pattern = rf"(?<![\w-]){re.escape(name)}(?![\w-])"
            if re.search(pattern, text):
                leaks.append(f"{f.name} names {kind} {name!r}")
    problems += unread + leaks
    ok = not (unread or leaks)
    print(f"  [{'PASS' if ok else 'FAIL'}] the page names nothing a model "
          f"publishes — {len(names)} name(s) against "
          f"{', '.join(f.name for f in PAGE_FILES)}"
          + (f"; {len(unread)} source(s) unreadable" if unread else ""))

    # ── 2. three.js is pinned, once, to one exact release ─────────────────
    # The Draco decoder path is derived from THREE.REVISION in app.js, so the
    # import map is the only place a version may appear -- and every entry in
    # it must be the same exact version, or the loader and core disagree. The
    # entries app.js imports must exist: an empty map pins nothing and passes
    # nothing.
    html = (PROTO / "index.html").read_text()
    m = re.search(r'<script type="importmap">(.*?)</script>', html, re.S)
    pins, pin_problems = set(), []
    imports = {}
    if not m:
        pin_problems.append("index.html has no import map")
    else:
        try:
            parsed = json.loads(m.group(1))
            imports = parsed.get("imports") if isinstance(parsed, dict) else None
            if not isinstance(imports, dict):
                pin_problems.append("the import map has no `imports` object")
                imports = {}
        except ValueError as e:
            pin_problems.append(f"the import map is not valid JSON: {e}")
    for key in REQUIRED_IMPORTS:
        if m and key not in imports:
            pin_problems.append(f"the import map has no {key!r} entry, which "
                                f"app.js imports")
    for key, url in imports.items():
        got = PIN.search(url) if isinstance(url, str) else None
        if not got:
            pin_problems.append(f"import map entry {key!r} is not pinned to an "
                                f"exact three@x.y.z: {url}")
        else:
            pins.add(got.group(1))
    if m and not pins:
        pin_problems.append("the import map pins no three.js release")
    if len(pins) > 1:
        pin_problems.append(f"the import map pins several releases: {sorted(pins)}")
    if PIN.search((PROTO / "app.js").read_text()):
        pin_problems.append("app.js hard-codes a three@x.y.z version; derive "
                            "it from THREE.REVISION")
    problems += pin_problems
    print(f"  [{'PASS' if not pin_problems else 'FAIL'}] three.js is pinned "
          f"once — {', '.join(sorted(pins)) or 'no pin'}")

    # ── 3. the fixture index meets the same contract as the real one ──────
    # The "second model" #107 is proved against. A fixture the real contract
    # would reject proves nothing about the real index.
    fixture_problems = []
    fixture = load_json(FIXTURE_INDEX, fixture_problems, "fixture index") \
        if FIXTURE_INDEX.is_file() else None
    if not FIXTURE_INDEX.is_file():
        fixture_problems.append("prototype/fixtures/models.json is missing; "
                                "run prototype/fixtures/make_fixtures.py")
    rows = fixture.get("models") if isinstance(fixture, dict) else None
    if fixture is not None and not isinstance(rows, list):
        fixture_problems.append("the fixture index has no `models` list")
    root = FIXTURE_INDEX.parent
    for i, r in enumerate(rows or []):
        bad = model_contract.row_problems(r, f"fixture row {i}")
        fixture_problems += bad
        if bad:
            continue
        paths = [r["manifest"], *r["levels"].values()]
        fixture_problems += [f"fixture path does not resolve: {p}"
                             for p in paths if not (root / p).is_file()]
        manifest = load_json(root / r["manifest"], fixture_problems,
                             "fixture manifest") if (root / r["manifest"]).is_file() else None
        if isinstance(manifest, dict):
            fixture_problems += model_contract.identity_problems(
                manifest.get("model"), f"fixture {r['id']} model")
    real = load_json(build_index.INDEX, fixture_problems, "index")
    real_ids = {x.get("id") for x in real.get("models", []) if isinstance(x, dict)} \
        if isinstance(real, dict) else set()
    fixture_ids = {x.get("id") for x in rows or [] if isinstance(x, dict)}
    fixture_problems += [f"fixture id {c} collides with a real model"
                         for c in sorted(i for i in real_ids & fixture_ids
                                         if isinstance(i, str))]
    problems += fixture_problems
    print(f"  [{'PASS' if not fixture_problems else 'FAIL'}] the fixture index "
          f"meets the model contract")

    print("-" * 76)
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("all prototype gates pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
