"""#118 — the controls under the viewer: `views` and `dimensions`, checked
against the .glb (verify_index.py gates 7 and 8) and whole or refused, and the
unit list the page and the contract share (verify_prototype.py gate 4)."""
from suite import (Case, app_js, edit, fixture_export, index_gates, manifest,
                   page_gates, replace)

G = "#118 views and dimensions"


def _no_footprints(m) -> None:
    for key in ("main_body", "with_porch", "overall"):
        m["dimensions"].pop(key)


CASES = [
    Case(G, "views is not a list", edit(manifest, lambda m: m.__setitem__("views", 5)),
         index_gates(), "`views` is not a list of objects"),
    Case(G, "a view hides a node the .glb lacks",
         edit(manifest, lambda m: m["views"][1]["hide"].append("Ghost_node")),
         index_gates(), "node Ghost_node is named by presence or views but not in"),
    Case(G, "a view's hide list holds a number",
         edit(manifest, lambda m: m["views"][1]["hide"].append(7)),
         index_gates(), "`views[].hide` is not a list of strings"),
    Case(G, "a view with no label", edit(manifest, lambda m: m["views"][1].pop("label")),
         index_gates(), "views[1].label must be a non-empty string"),
    Case(G, "two default views", edit(manifest, lambda m: m["views"][2].__setitem__("default", True)),
         index_gates(), "has 2 defaults"),
    Case(G, "a footprint width that is a string",
         edit(manifest, lambda m: m["dimensions"]["with_porch"].__setitem__("width", "22")),
         index_gates(), "dimensions.with_porch.width must be a positive number"),
    Case(G, "an unknown unit", edit(manifest, lambda m: m["dimensions"].__setitem__("units", "cubits")),
         index_gates(), "dimensions.units must be one of"),
    Case(G, "no footprints at all", edit(manifest, _no_footprints),
         index_gates(), "dimensions has no footprint"),
    Case(G, "a dimensions entry that is a number",
         edit(manifest, lambda m: m["dimensions"].__setitem__("extra", 5)),
         index_gates(), "dimensions.extra is neither a footprint object"),
    Case(G, "a fixture view whose hide is a string",
         edit(lambda root: fixture_export(root) / "variants.json",
              lambda m: m["views"][0].__setitem__("hide", "fixture_roof")),
         page_gates(), "views[0].hide must be a list of strings"),
    Case(G, "app.js accepts a unit the contract does not",
         replace(app_js, ("const UNITS = {\n", "const UNITS = {\n  cubits: { metres: 0.4572, label: 'cubit' },\n")),
         page_gates(), "only app.js: ['cubits']"),
]
