"""#112 — the commerce slots: docs/COMMERCE.md held to the real manifest, and
the page held to the contract's estimate fields, note limit and events
(verify_prototype.py gate 6); and model_contract.estimate_problems(), the
check Rails runs before sending an estimate, which must report malformed input
and never raise."""
import json
import re
from pathlib import Path

from suite import Case, ContractCase, existing, manifest, page_gates, read_json, replace

G = "#112 commerce"


def _doc(root: Path) -> Path:
    return root / "docs" / "COMMERCE.md"


def _app(root: Path) -> Path:
    return root / "prototype" / "app.js"


def _example(root: Path) -> dict:
    return json.loads(re.search(r"```json\n(.*?)\n```", _doc(root).read_text(), re.S).group(1))


def _estimate(change):
    """Replace the document's example with a changed copy of itself."""
    def setup(root: Path) -> None:
        estimate = _example(root)
        change(estimate)
        text = _doc(root).read_text()
        new, count = re.subn(r"```json\n.*?\n```",
                             lambda m: f"```json\n{json.dumps(estimate, indent=2)}\n```",
                             text, count=1, flags=re.S)
        if count != 1:
            raise AssertionError("no ```json example block in COMMERCE.md to replace")
        _doc(root).write_text(new)
    return setup


def _contract(change, contains=None):
    """estimate_problems() on a changed copy of the documented example."""
    def call(mc, root: Path) -> list:
        estimate = _example(root)
        estimate = change(estimate)
        return mc.estimate_problems(estimate, read_json(manifest(root)))
    return call


def _set(key, value):
    def change(e):
        e[key] = value
        return e
    return change


CASES = [
    # gate 6: the documented estimate
    Case(G, "the documented estimate has its low above its high",
         _estimate(lambda e: e.update(low=200000)),
         page_gates(), "the documented estimate has low 200000 above high 175000"),
    Case(G, "the documented estimate prices a model the index does not have",
         _estimate(lambda e: e.update(model="retired_model")),
         page_gates(), "names model 'retired_model', which the index does not have"),
    Case(G, "the documented estimate gains a field the contract does not have",
         _estimate(lambda e: e.update(discount=0.1)),
         page_gates(), "the documented estimate has an unknown field 'discount'"),
    Case(G, "the documented estimate's list is below its range",
         _estimate(lambda e: e.update(list={"low": 100000, "high": 120000})),
         page_gates(), "the documented estimate.list is below the estimate"),
    Case(G, "the documented estimate's currency is not a code",
         _estimate(lambda e: e.update(currency="usd")),
         page_gates(), "the documented estimate.currency must be a three-letter code"),
    Case(G, "the documented estimate priced a configuration the manifest no longer has",
         _estimate(lambda e: e["configuration"]["sets"].update(color_theme="retired")),
         page_gates(), "the documented estimate.configuration.sets.color_theme is 'retired'"),
    Case(G, "COMMERCE.md loses its estimate example",
         replace(_doc, ("```json\n", "```text\n")),
         page_gates(), "docs/COMMERCE.md needs a ```json estimate example"),
    # gate 6: the page agrees with the contract
    Case(G, "app.js drops an estimate field the contract has",
         replace(_app, ("'list', 'note', ", "'list', ")),
         page_gates(), "ESTIMATE_FIELDS differs — only app.js: [], only model_contract: ['note']"),
    Case(G, "app.js and the contract disagree on the note limit",
         replace(_app, ("const ESTIMATE_NOTE_MAX_CHARS = 200;", "const ESTIMATE_NOTE_MAX_CHARS = 280;")),
         page_gates(), "ESTIMATE_NOTE_MAX_CHARS differs — app.js: 280, model_contract: 200"),
    Case(G, "app.js uses an event the document does not name",
         replace(_app, ("quote: 'adu:quote',", "quote: 'adu:quote-request',")),
         page_gates(), "app.js uses event 'adu:quote-request', which docs/COMMERCE.md does not name"),
    Case(G, "app.js names no events at all",
         replace(_app, ("configuration: 'adu:configuration',", "configuration: 'configuration',"),
                 ("estimate: 'adu:estimate',", "estimate: 'estimate',"),
                 ("quote: 'adu:quote',", "quote: 'quote',")),
         page_gates(), "app.js names no adu: event"),
    # estimate_problems(): what Rails runs
    ContractCase(G, "estimate_problems: the documented example is valid",
                 _contract(lambda e: e)),
    ContractCase(G, "estimate_problems: no estimate is a supported state",
                 _contract(lambda e: None)),
    ContractCase(G, "estimate_problems: a list is not an estimate",
                 _contract(lambda e: [e]), "estimate must be an object or null, found list"),
    ContractCase(G, "estimate_problems: NaN is not an amount",
                 _contract(_set("low", float("nan"))), "estimate needs a positive low and high"),
    ContractCase(G, "estimate_problems: true is not an amount",
                 _contract(_set("high", True)), "estimate needs a positive low and high"),
    ContractCase(G, "estimate_problems: an estimate for another model",
                 _contract(_set("model", "another_model")), "estimate.model is 'another_model'"),
    ContractCase(G, "estimate_problems: a list that is not an object",
                 _contract(_set("list", 160000)), "estimate.list must be an object with low and high"),
    ContractCase(G, "estimate_problems: a note longer than the limit",
                 _contract(_set("note", "x" * 201)), "estimate.note is 201 characters"),
    ContractCase(G, "estimate_problems: a configuration that is not an object",
                 _contract(_set("configuration", "sage")), "estimate.configuration must be an object"),
    ContractCase(G, "estimate_problems: a currency with a trailing newline",
                 _contract(_set("currency", "USD\n")), "estimate.currency must be a three-letter code"),
    # an unreadable file is a failed gate, not a traceback (every gate's reads)
    Case(G, "an unreadable app.js is a failed gate, not a traceback",
         lambda root: existing(_app(root)).chmod(0),
         page_gates(), "prototype/app.js is unreadable"),
    Case(G, "an app.js that is not UTF-8 is a failed gate, not a traceback",
         lambda root: existing(_app(root)).write_bytes(b"\xff\xfe not text \x80"),
         page_gates(), "prototype/app.js is unreadable"),
    Case(G, "an unreadable index.html is a failed gate, not a traceback",
         lambda root: existing(root / "prototype" / "index.html").chmod(0),
         page_gates(), "prototype/index.html is unreadable"),
    Case(G, "an unreadable CONFIGURATION.md is a failed gate, not a traceback",
         lambda root: existing(root / "docs" / "CONFIGURATION.md").chmod(0),
         page_gates(), "docs/CONFIGURATION.md is unreadable"),
    Case(G, "an unreadable COMMERCE.md is a failed gate, not a traceback",
         lambda root: existing(_doc(root)).chmod(0),
         page_gates(), "docs/COMMERCE.md is unreadable"),
    ContractCase(G, "estimate_problems: a manifest that is not an object",
                 lambda mc, root: mc.estimate_problems(_example(root), []),
                 "the manifest is not an object"),
]
