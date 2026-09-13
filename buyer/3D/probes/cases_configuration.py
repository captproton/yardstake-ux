"""#122 — the configuration: docs/CONFIGURATION.md held to the real manifest
(verify_prototype.py gate 5), and model_contract.configuration_problems(), the
check Rails will run, which must report malformed input and never raise.
Also the clean runs of every gate, so the suite shows nothing fails for
everything."""
import json
import re
from pathlib import Path

from suite import (Case, ContractCase, both, config_doc, edit, index,
                   manifest, page_gates, read_json, replace)

G = "#122 configuration"


def _example(root: Path) -> dict:
    return json.loads(re.search(r"```json\n(.*?)\n```", config_doc(root).read_text(), re.S).group(1))


def _with(d: dict, **changes) -> dict:
    out = json.loads(json.dumps(d))
    for key, value in changes.items():
        if value is ...:
            out.pop(key, None)
        else:
            out[key] = value
    return out


def _json_example(body: str):
    def setup(root: Path) -> None:
        text = config_doc(root).read_text()
        config_doc(root).write_text(re.sub(r"```json\n.*?\n```", f"```json\n{body}\n```", text, count=1, flags=re.S))
    return setup


def _row_without_manifest(d: dict) -> None:
    d["models"][0].pop("manifest")


def _manifest(root: Path) -> dict:
    return read_json(manifest(root))


CASES = [
    Case(G, "an option the manifest does not have, in example and link",
         replace(config_doc, ('"color_theme": "sage"', '"color_theme": "lilac"'),
                 ("set.color_theme=sage", "set.color_theme=lilac")),
         page_gates(), "sets.color_theme is 'lilac', which is not one of"),
    Case(G, "a group left out, in example and link",
         replace(config_doc, ('"living_layout": "sofa",\n    "porch_layout": "chairs"', '"living_layout": "sofa"'),
                 ("&presence.porch_layout=chairs", "")),
         page_gates(), "presence has no choice for 'porch_layout'"),
    Case(G, "the link out of step with the example",
         replace(config_doc, ("set.main_flooring=walnut", "set.main_flooring=light_oak")),
         page_gates(), "the documented link does not decode to the documented configuration"),
    Case(G, "a field that is not a choice",
         replace(config_doc, ('  "model": "barn_cabin_524",\n', '  "model": "barn_cabin_524",\n  "price": 1,\n')),
         page_gates(), "has an unknown field 'price'"),
    Case(G, "a model the index does not have",
         replace(config_doc, ('"model": "barn_cabin_524"', '"model": "retired_model"'),
                 ("?model=barn_cabin_524", "?model=retired_model")),
         page_gates(), "names model 'retired_model', which the index does not have"),
    Case(G, "a view the manifest does not have",
         replace(config_doc, ('"view": "dollhouse"', '"view": "xray"'), ("view=dollhouse", "view=xray")),
         page_gates(), "view 'xray' is not one of the manifest's views"),
    Case(G, "no JSON example at all", replace(config_doc, ("```json", "```js")),
         page_gates(), "needs a ```json example and a ```text link"),
    Case(G, "the JSON example is null", _json_example("null"),
         page_gates(), "the example configuration must be a JSON object, found NoneType"),
    Case(G, "the JSON example is a list", _json_example("[]"),
         page_gates(), "the example configuration must be a JSON object, found list"),
    Case(G, "the example's index row has no manifest", edit(index, _row_without_manifest),
         page_gates(), "the example's index row is missing `manifest`"),

    ContractCase(G, "the documented example is valid",
                 lambda mc, root: mc.configuration_problems(_example(root), _manifest(root))),
    ContractCase(G, "a choice that is a list, not an id",
                 lambda mc, root: mc.configuration_problems(
                     _with(_example(root), sets={**_example(root)["sets"], "color_theme": []}), _manifest(root)),
                 "sets.color_theme must be an option id, found []"),
    ContractCase(G, "a manifest whose views is a number",
                 lambda mc, root: mc.configuration_problems(_example(root), _with(_manifest(root), views=1)),
                 "view must be omitted"),
    ContractCase(G, "a manifest whose sets is a number",
                 lambda mc, root: mc.configuration_problems(_example(root), _with(_manifest(root), sets=1)),
                 "names a group the manifest does not have"),
    ContractCase(G, "a manifest group whose id is a list",
                 lambda mc, root: mc.configuration_problems(
                     _example(root), _with(_manifest(root), presence=[{"id": ["x"], "options": []}])),
                 "names a group the manifest does not have"),
    ContractCase(G, "view: null for a manifest with no views",
                 lambda mc, root: mc.configuration_problems(
                     _with(_example(root), view=None), _with(_manifest(root), views=[])),
                 "view must be omitted, not None"),
    ContractCase(G, "no view for a manifest that has views",
                 lambda mc, root: mc.configuration_problems(_with(_example(root), view=...), _manifest(root)),
                 "view is required"),
    ContractCase(G, "the manifest is not an object",
                 lambda mc, root: mc.configuration_problems(_example(root), []),
                 "the manifest is not an object"),

    Case("clean", "build_index.py --check and verify_index.py pass", None,
         both(build_fails=False, verify_fails=False), "all index gates pass"),
    Case("clean", "verify_prototype.py passes", None, page_gates(fails=False), "all prototype gates pass"),
]
