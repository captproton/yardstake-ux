"""#111 — the fixtures that stand in for a model with parts missing, and the
rule that they are exactly what make_fixtures.py generates (verify_prototype.py
gate 3 and `make_fixtures.py --check`)."""
from pathlib import Path

from suite import (Case, ContractCase, Run, edit, existing, fixture_export,
                   manifest, page_gates, read_json)

G = "#111 fixtures"


def _reduced(root: Path) -> Path:
    return fixture_export(root, "fixture_barn_reduced") / "variants.json"


def _bare(root: Path) -> Path:
    return fixture_export(root, "fixture_bare_box") / "variants.json"


def _check(fails: bool = True) -> list:
    return [Run("prototype/fixtures/make_fixtures.py", ("--check",), fails)]


def _bare_is_only_model(mc, root: Path) -> list:
    keys = sorted(read_json(_bare(root)))
    return [] if keys == ["model"] else [f"the identity-only fixture has keys {keys}"]


CASES = [
    Case(G, "the reduced fixture is hand-edited",
         edit(_reduced, lambda m: m["views"].pop()),
         page_gates(), "fixture models/fixture_barn_reduced/export/variants.json is missing or differs"),
    Case(G, "the barn cabin manifest changes and the fixtures are not regenerated",
         edit(manifest, lambda m: m["sets"][0].__setitem__("label", "Colour scheme")),
         page_gates(), "fixture models/fixture_barn_reduced/export/variants.json is missing or differs"),
    Case(G, "the identity-only fixture gains a block",
         edit(_bare, lambda m: m.__setitem__("sets", [])),
         page_gates(), "fixture models/fixture_bare_box/export/variants.json is missing or differs"),
    Case(G, "a generated fixture file is deleted",
         lambda root: existing(_reduced(root)).unlink(),
         page_gates(), "is missing or differs from what make_fixtures.py generates"),
    Case(G, "make_fixtures.py --check names a stale fixture",
         edit(_reduced, lambda m: m["views"].pop()),
         _check(), "models/fixture_barn_reduced/export/variants.json"),
    Case(G, "the barn cabin no longer has what the reduced fixture removes",
         edit(manifest, lambda m: m.__setitem__(
             "presence", [g for g in m["presence"] if g["id"] != "porch_layout"])),
         _check(), "no longer has a `porch_layout` layout group"),
    Case(G, "clean: every fixture matches make_fixtures.py", None,
         _check(fails=False), "fixture file(s) match make_fixtures.py"),
    ContractCase(G, "the identity-only fixture is only `model`", _bare_is_only_model),
]
