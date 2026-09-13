"""#116 — the page's own gates: verify_prototype.py. The import map, the
fixtures, and the rule that the page names nothing a model publishes."""
import re
from pathlib import Path

from suite import (Case, app_js, append, edit, fixture_export, fixture_index,
                   index, index_html, page_gates, steps, write)

G = "#116 page"


def _import_map(body: str):
    def setup(root: Path) -> None:
        html = index_html(root).read_text()
        index_html(root).write_text(re.sub(
            r'(<script type="importmap">)(.*?)(</script>)',
            lambda m: m.group(1) + body + m.group(3), html, flags=re.S))
    return setup


def _prose_says_full_detail(root: Path) -> None:
    # The clean case below is only meaningful while app.js says "full detail"
    # in prose, since `full` is also a view id matched only as a quoted string.
    if "full detail" not in app_js(root).read_text():
        raise AssertionError("app.js no longer says 'full detail'; pick another prose word to guard")


def _coarse_level_only_name(root: Path) -> None:
    source = fixture_export(root) / "fixture_slab_box_lod0.glb"
    data = source.read_bytes()
    if b"fixture_roof" not in data:
        raise AssertionError("the fixture no longer has a node named fixture_roof")
    # Same byte length, so the JSON chunk header stays valid.
    (root / "prototype" / "fixtures" / "zz_probe_lod1.glb").write_bytes(
        data.replace(b"fixture_roof", b"probe_roof__"))


CASES = [
    Case(G, "the import map lacks three/addons/",
         _import_map('{"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.module.js"}}'),
         page_gates(), "no 'three/addons/' entry"),
    Case(G, "the import map is empty", _import_map('{"imports": {}}'),
         page_gates(), "pins no three.js release"),
    Case(G, "the import map is not JSON", _import_map("{imports: nope"),
         page_gates(), "not valid JSON"),
    Case(G, "the fixture index is not JSON", write(fixture_index, "{oops"),
         page_gates(), "fixture index prototype/fixtures/models.json is unreadable"),
    Case(G, "a fixture index row is a number", write(fixture_index, '{"models": [7]}'),
         page_gates(), "must be an object, found int"),
    Case(G, "a fixture manifest is not JSON",
         lambda root: (fixture_export(root) / "variants.json").write_text("[not json"),
         page_gates(), "is unreadable"),
    Case(G, "app.js hard-codes a view id", append(app_js, "\nconst probe = 'dollhouse';\n"),
         page_gates(), "names view id 'dollhouse'"),
    Case(G, "app.js hard-codes an option id", append(app_js, '\nconst probe = "sandstone";\n'),
         page_gates(), "names option id 'sandstone'"),
    Case(G, "clean, and 'full detail' in prose is not a leak", _prose_says_full_detail,
         page_gates(fails=False), "all prototype gates pass"),
    Case(G, "the fixture index lists no models", write(fixture_index, '{"models": []}'),
         page_gates(), "lists no models, so it proves nothing"),
    Case(G, "the real index's models is a number",
         edit(index, lambda d: d.__setitem__("models", 5)),
         page_gates(), "has no `models` list"),
    Case(G, "a real index row id that is a list",
         edit(index, lambda d: d["models"][0].__setitem__("id", [])),
         page_gates(), "id must be a non-empty string, found []"),
    Case(G, "a name only a coarse level has",
         steps(_coarse_level_only_name,
               edit(index, lambda d: d["models"][0]["levels"].__setitem__("lod1", "fixtures/zz_probe_lod1.glb")),
               append(app_js, "\n// probe_roof__\n")),
         page_gates(), "'probe_roof__'"),
    Case(G, "a name only the manifest's model block has",
         steps(edit(lambda root: fixture_export(root) / "variants.json",
                    lambda m: m["model"].__setitem__("name", "Probe Manifest Only")),
               append(app_js, "\n// Probe Manifest Only\n")),
         page_gates(), "'Probe Manifest Only'"),
]
