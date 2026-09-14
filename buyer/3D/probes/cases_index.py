"""#115 — the model index: build_index.py --check, verify_index.py, and the
identity contract. Proved in PR #115; the presence-node message is the one
#118 introduced when views joined that gate."""
from pathlib import Path

from suite import (BARN, Case, ContractCase, barn, barn_glb, both, edit, glb,
                   index, manifest, read_json, steps, write, write_json)

G = "#115 index"


def _two_dirs_one_id(root: Path) -> None:
    d = root / "models" / "zz_dup" / "export"
    d.mkdir(parents=True)
    (d / "variants.json").write_text(manifest(root).read_text())


def _thumbnail_is_a_directory(root: Path) -> None:
    (barn(root) / "renders" / "zz_dir.png").mkdir(parents=True)


def _only_lod1(root: Path) -> None:
    m = read_json(manifest(root))
    m["model"]["id"] = "zz_lod1"
    d = root / "models" / "zz_lod1" / "export"
    d.mkdir(parents=True)
    write_json(d / "variants.json", m)
    (d / "zz_lod1_lod1.glb").write_bytes(barn_glb(root, "lod1").read_bytes())


def _spec_without_export(root: Path) -> None:
    d = root / "models" / "zz_probe"
    d.mkdir(parents=True)
    (d / "spec.yaml").write_text("")


def _spec_pending(text: str):
    def setup(root: Path) -> None:
        d = root / "models" / "zz_probe"
        d.mkdir(parents=True)
        (d / "spec.yaml").write_text("")
        (d / "EXPORT_PENDING").write_text(text)
    return setup


def _pending_marker_without_spec(root: Path) -> None:
    d = root / "models" / "zz_probe"
    d.mkdir(parents=True)
    (d / "EXPORT_PENDING").write_text("Exported by #131.\n")


def _stale_pending_marker(root: Path) -> None:
    (barn(root) / "EXPORT_PENDING").write_text("Exported by #131.\n")


def _identity(root: Path, **changes) -> dict:
    ident = dict(read_json(manifest(root))["model"])
    for key, value in changes.items():
        if value is ...:
            ident.pop(key, None)
        else:
            ident[key] = value
    return ident


CASES = [
    Case(G, "variants.json root is a list", write(manifest, "[1, 2]"), both(), "root is a list"),
    Case(G, "model.id missing: no fallback to the folder name",
         edit(manifest, lambda m: m["model"].pop("id")), both(), "model.id must be a non-empty string"),
    Case(G, "two folders publish the same id", _two_dirs_one_id, both(), "published by both"),
    Case(G, "the index has a duplicated row",
         edit(index, lambda d: d["models"].append(d["models"][0])), both(), "every id is unique"),
    Case(G, "models.json is not JSON", write(index, "{not json"), both(), "not valid JSON"),
    Case(G, "models.json root is a list", write(index, "[]"), both(), "root is a list"),
    Case(G, "an index row is a number",
         edit(index, lambda d: d["models"].append(7)), both(), "must be an object, found int"),
    Case(G, "the index note is hand-edited",
         edit(index, lambda d: d.__setitem__("note", d["note"] + " edited")), both(), "rows or note differ"),
    Case(G, "the index note names the display name",
         edit(index, lambda d: d.__setitem__("note", d["note"] + " e.g. Barn Cabin")),
         both(), "note names Barn Cabin"),
    Case(G, "a thumbnail path that is a directory",
         steps(_thumbnail_is_a_directory,
               edit(index, lambda d: d["models"][0].__setitem__(
                   "thumbnail", f"../models/{BARN}/renders/zz_dir.png"))),
         both(), "(not a file)"),
    Case(G, "an index row with storeys: null",
         edit(index, lambda d: d["models"][0].__setitem__("storeys", None)),
         both(), "storeys must be an object"),
    Case(G, "a swap target renamed",
         edit(manifest, lambda m: m["sets"][0]["targets"].__setitem__(0, "adu_siding_RENAMED")),
         both(build_fails=False), "material adu_siding_RENAMED is a swap target"),
    Case(G, "a presence node missing from the .glb",
         edit(manifest, lambda m: m["presence"][0]["options"][0]["show"].append("Furn_ghost")),
         both(build_fails=False), "node Furn_ghost is named by presence or views but not in"),
    Case(G, "lod0 points at a file that is not a .glb",
         edit(index, lambda d: d["models"][0]["levels"].__setitem__("lod0", d["models"][0]["manifest"])),
         both(), "not a binary glTF"),
    Case(G, "a .glb whose JSON chunk is an array",
         lambda root: barn_glb(root).write_bytes(glb("[]")),
         both(build_fails=False), "JSON chunk root is a list"),
    Case(G, "a .glb whose nodes is null",
         lambda root: barn_glb(root).write_bytes(glb('{"materials": [], "nodes": null}')),
         both(build_fails=False), "`nodes` is not a list of objects"),
    Case(G, "an index row whose id is a list",
         edit(index, lambda d: d["models"][0].__setitem__("id", [])),
         both(), "id must be a non-empty string, found []"),
    Case(G, "a manifest thumbnail of 1",
         edit(manifest, lambda m: m["model"].__setitem__("thumbnail", 1)),
         both(), "thumbnail must be null or a relative path"),
    Case(G, "models.json is unreadable", lambda root: index(root).chmod(0),
         both(), "unreadable or not valid JSON"),
    Case(G, "an export with only lod1", _only_lod1, both(), "has no full-detail .glb"),
    Case(G, "an unknown level name",
         lambda root: (barn(root) / "export" / f"{BARN}_preview.glb").write_bytes(glb("{}")),
         both(), "the page cannot tell which level it is"),
    Case(G, "a directory named <id>_lod3.glb is ignored",
         lambda root: (barn(root) / "export" / f"{BARN}_lod3.glb").mkdir(),
         both(build_fails=False, verify_fails=False)),
    Case(G, "an index row with no area_source",
         edit(index, lambda d: d["models"][0].pop("area_source")), both(), "missing `area_source`"),
    Case(G, "sets[].targets is null",
         edit(manifest, lambda m: m["sets"][0].__setitem__("targets", None)),
         both(build_fails=False), "`sets[].targets` is not a list of strings"),
    Case(G, "a model with a spec and no export", _spec_without_export,
         both(build_fails=False), "has spec.yaml but no export/variants.json"),
    Case(G, "a model with a spec and a pending export that names its issue", _spec_pending("Exported by #131.\n"),
         both(build_fails=False, verify_fails=False), "zz_probe (#131)"),
    Case(G, "a pending-export marker that names no issue", _spec_pending("later\n"),
         both(build_fails=False), "zz_probe/EXPORT_PENDING names no issue (#N) that will export it"),
    Case(G, "a pending-export marker in a model directory with no spec", _pending_marker_without_spec,
         both(build_fails=False), "zz_probe/EXPORT_PENDING sits beside no spec.yaml"),
    Case(G, "a pending-export marker left behind after the export", _stale_pending_marker,
         both(build_fails=False), "barn_cabin_524/EXPORT_PENDING is stale: export/variants.json exists"),

    ContractCase(G, "the barn cabin identity passes",
                 lambda mc, root: mc.identity_problems(_identity(root))),
    ContractCase(G, "an area with no source",
                 lambda mc, root: mc.identity_problems(_identity(root, area_source=None)),
                 "model.area_source must be a non-empty string"),
    ContractCase(G, "an area with no value",
                 lambda mc, root: mc.identity_problems(_identity(root, area_sf=None)),
                 "model.area_sf must be a positive number"),
    ContractCase(G, "a display name of 123",
                 lambda mc, root: mc.identity_problems(_identity(root, name=123)),
                 "model.name must be a non-empty string"),
    ContractCase(G, "storeys missing",
                 lambda mc, root: mc.identity_problems(_identity(root, storeys=...)),
                 "model.storeys must be an object"),
    ContractCase(G, "storeys.count of true",
                 lambda mc, root: mc.identity_problems(_identity(root, storeys={"count": True, "loft": False})),
                 "model.storeys.count must be an integer"),
    ContractCase(G, "a thumbnail that climbs out of the model folder",
                 lambda mc, root: mc.identity_problems(_identity(root, thumbnail="../x.png")),
                 "model.thumbnail must be null or a relative path inside"),
]
