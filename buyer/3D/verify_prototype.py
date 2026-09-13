"""
verify_prototype.py — gates on the configurator page itself.

    python3 verify_prototype.py

Needs no browser and no Blender. What a browser must confirm -- that the page
loads, lights, orbits and frames -- is checked by opening it; what can be
checked from the files is checked here, on every change.

WHAT IS AT RISK. The page plan's one rule: the page knows nothing about any
building. The failure is not dramatic. It is one convenience -- a material
name in a lookup, a node name in a camera preset, a display name in a
fallback -- and the next model inherits it silently. So gate 1 collects every
name any indexed model publishes, from its manifest AND from its .glb, and
fails if the page's own files mention one.
"""
import json
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


def published_names(index_path):
    """{name: what it is} for every model in an index: identity, manifest
    blocks, and the material and node names inside its full-detail .glb."""
    root = index_path.parent
    names = {}

    def add(value, kind):
        if isinstance(value, str) and len(value) >= 3:
            names.setdefault(value, kind)

    for r in json.loads(index_path.read_text()).get("models", []):
        add(r.get("id"), "model id")
        add(r.get("name"), "model name")
        manifest = json.loads((root / r["manifest"]).read_text())
        mats, nodes = model_contract.manifest_names(manifest)
        for m in mats:
            add(m, "material")
        for n in nodes:
            add(n, "node")
        for block in ("sets", "presence"):
            for st in manifest.get(block, []):
                add(st.get("id"), f"{block} id")
                add(st.get("room"), "room")
        for v in manifest.get("views", []):
            for n in v.get("hide", []):
                add(n, "node")
        glb = r["levels"].get("lod0") or r["primary"]
        g_mats, g_nodes = model_contract.glb_names(root / glb)
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

    # ── 1. the page names no building, room, node or material ─────────────
    names = {}
    for index in (build_index.INDEX, FIXTURE_INDEX):
        if index.is_file():
            names.update(published_names(index))
    leaks = []
    for f in PAGE_FILES:
        text = f.read_text()
        for name, kind in sorted(names.items()):
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text):
                leaks.append(f"{f.name} names {kind} {name!r}")
    problems += leaks
    print(f"  [{'PASS' if not leaks else 'FAIL'}] the page names nothing a model "
          f"publishes — {len(names)} name(s) against "
          f"{', '.join(f.name for f in PAGE_FILES)}")

    # ── 2. three.js is pinned, once, to one exact release ─────────────────
    # The Draco decoder path is derived from THREE.REVISION in app.js, so the
    # import map is the only place a version may appear -- and every entry in
    # it must be the same exact version, or the loader and core disagree.
    html = (PROTO / "index.html").read_text()
    m = re.search(r'<script type="importmap">(.*?)</script>', html, re.S)
    pins, pin_problems = set(), []
    if not m:
        pin_problems.append("index.html has no import map")
    else:
        imports = json.loads(m.group(1)).get("imports", {})
        for key, url in imports.items():
            got = PIN.search(url)
            if not got:
                pin_problems.append(f"import map entry {key!r} is not pinned "
                                    f"to an exact three@x.y.z: {url}")
            else:
                pins.add(got.group(1))
        if len(pins) > 1:
            pin_problems.append(f"import map pins several releases: {sorted(pins)}")
    js = (PROTO / "app.js").read_text()
    if PIN.search(js):
        pin_problems.append("app.js hard-codes a three@x.y.z version; derive "
                            "it from THREE.REVISION")
    problems += pin_problems
    print(f"  [{'PASS' if not pin_problems else 'FAIL'}] three.js is pinned "
          f"once — {', '.join(sorted(pins)) or 'no pin'}")

    # ── 3. the fixture index meets the same contract as the real one ──────
    # The "second model" #107 is proved against. A fixture the real contract
    # would reject proves nothing about the real index.
    fixture_problems = []
    if not FIXTURE_INDEX.is_file():
        fixture_problems.append("prototype/fixtures/models.json is missing; "
                                "run prototype/fixtures/make_fixtures.py")
    else:
        root = FIXTURE_INDEX.parent
        rows = json.loads(FIXTURE_INDEX.read_text()).get("models", [])
        for i, r in enumerate(rows):
            bad = model_contract.row_problems(r, f"fixture row {i}")
            fixture_problems += bad
            if bad:
                continue
            paths = [r["manifest"], *r["levels"].values()]
            fixture_problems += [f"fixture path does not resolve: {p}"
                                 for p in paths if not (root / p).is_file()]
            ident = json.loads((root / r["manifest"]).read_text()).get("model")
            fixture_problems += model_contract.identity_problems(
                ident, f"fixture {r['id']} model")
        real = {r["id"] for r in json.loads(build_index.INDEX.read_text())["models"]}
        clash = sorted(real & {r.get("id") for r in rows})
        fixture_problems += [f"fixture id {c} collides with a real model"
                             for c in clash]
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
