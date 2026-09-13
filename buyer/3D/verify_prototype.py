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
from urllib.parse import parse_qs, urlsplit

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
    """{name: what it is} for every model in an index: identity from the row
    AND from the manifest's own `model` block (the header reads the latter),
    manifest blocks, and the material and node names inside EVERY level's
    .glb -- the page loads the coarse level too, and nothing requires its
    names to be a subset of full detail's.
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
            ident = manifest.get("model")
            if isinstance(ident, dict):
                add(ident.get("id"), "model id")
                add(ident.get("name"), "model name")
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

        glbs = list(dict.fromkeys(
            [*r["levels"].values(), *([r["primary"]] if r["primary"] else [])]))
        for glb in glbs:
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
    elif isinstance(rows, list) and not rows:
        fixture_problems.append("the fixture index lists no models, so it "
                                "proves nothing about a second model")
    rows = rows if isinstance(rows, list) else []
    root = FIXTURE_INDEX.parent
    for i, r in enumerate(rows):
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
            fixture_problems += [f"fixture {r['id']}: {p}"
                                 for p in model_contract.display_problems(manifest)]
    def string_ids(v):
        # Only well-formed ids: a list id is unhashable, and gate 1 already
        # reports a malformed row.
        items = v if isinstance(v, list) else []
        return {x["id"] for x in items
                if isinstance(x, dict) and isinstance(x.get("id"), str)}

    real = load_json(build_index.INDEX, fixture_problems, "index")
    real_ids = string_ids(real.get("models") if isinstance(real, dict) else None)
    fixture_problems += [f"fixture id {c} collides with a real model"
                         for c in sorted(real_ids & string_ids(rows))]
    problems += fixture_problems
    print(f"  [{'PASS' if not fixture_problems else 'FAIL'}] the fixture index "
          f"meets the model contract")

    # ── 4. the page and the contract accept the same units ────────────────
    # A unit only one side knows is a manifest one side passes and the other
    # refuses: verify_index.py green, and no dimensions control on the page.
    m = re.search(r"const UNITS = \{(.*?)\n\};", (PROTO / "app.js").read_text(), re.S)
    page_units = set(re.findall(r"^\s*(\w+):", m.group(1), re.M)) if m else set()
    contract_units = set(model_contract.DIMENSION_UNITS)
    unit_problems = []
    if not m:
        unit_problems.append("app.js has no `const UNITS = { ... };` block to compare")
    elif page_units != contract_units:
        unit_problems.append(
            f"units differ — only app.js: {sorted(page_units - contract_units)}, "
            f"only model_contract: {sorted(contract_units - page_units)}")
    # The same for the disclosure's length limit: a limit only one side
    # enforces is copy one side accepts and the other refuses to show.
    lim = re.search(r"const DISCLOSURE_MAX_CHARS = (\d+);", (PROTO / "app.js").read_text())
    page_limit = int(lim.group(1)) if lim else None
    if page_limit != model_contract.DISCLOSURE_MAX_CHARS:
        unit_problems.append(
            f"DISCLOSURE_MAX_CHARS differs — app.js: {page_limit}, "
            f"model_contract: {model_contract.DISCLOSURE_MAX_CHARS}")
    problems += unit_problems
    print(f"  [{'PASS' if not unit_problems else 'FAIL'}] app.js and model_contract "
          f"agree on units and the disclosure limit — "
          f"{', '.join(sorted(page_units)) or 'no units found'}; {page_limit} characters")

    # ── 5. the documented configuration is one the real manifest accepts ──
    # docs/CONFIGURATION.md is the contract with Rails (#110). Its example must
    # be valid for the manifest it names, and its link must decode to the same
    # object -- otherwise the document quietly describes a page that no
    # longer exists.
    config_doc = HERE / "docs" / "CONFIGURATION.md"
    config_problems = []
    text = config_doc.read_text() if config_doc.is_file() else ""
    json_block = re.search(r"```json\n(.*?)\n```", text, re.S)
    link_block = re.search(r"```text\n(/prototype/\?.*?)\n```", text, re.S)
    example = None
    if not config_doc.is_file():
        config_problems.append("docs/CONFIGURATION.md is missing")
    elif not json_block or not link_block:
        config_problems.append("docs/CONFIGURATION.md needs a ```json example and a ```text link")
    else:
        try:
            example = json.loads(json_block.group(1))
        except ValueError as e:
            config_problems.append(f"the example configuration is not JSON: {e}")
    if isinstance(example, dict):
        real = load_json(build_index.INDEX, config_problems, "index")
        rows = real.get("models") if isinstance(real, dict) else None
        row = next((r for r in rows or [] if isinstance(r, dict)
                    and r.get("id") == example.get("model")), None)
        if row is None:
            config_problems.append(f"the example names model {example.get('model')!r}, "
                                   f"which the index does not have")
        else:
            manifest = load_json(build_index.INDEX.parent / row["manifest"],
                                 config_problems, "manifest")
            if isinstance(manifest, dict):
                config_problems += model_contract.configuration_problems(
                    example, manifest, "the documented configuration")
        query = parse_qs(urlsplit(link_block.group(1)).query)
        decoded = {"sets": {}, "presence": {}}
        for key, values in query.items():
            if key in ("model", "view"):
                decoded[key] = values[0]
            elif key.startswith("set."):
                decoded["sets"][key[4:]] = values[0]
            elif key.startswith("presence."):
                decoded["presence"][key[9:]] = values[0]
        if decoded != example:
            config_problems.append("the documented link does not decode to the "
                                   "documented configuration")
    problems += config_problems
    print(f"  [{'PASS' if not config_problems else 'FAIL'}] the documented "
          f"configuration is valid for its manifest, and its link matches")

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
