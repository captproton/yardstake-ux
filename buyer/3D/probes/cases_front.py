"""#117 — the model's front, declared and held to the geometry.

The page opens on the end a manifest calls the front. What could go wrong is a
building that opens from behind while every gate stays green, so each case
below is a way to declare the wrong end, or to declare one nothing can check:

  * the contract refuses a missing or impossible front
  * verify_index.py gate 9 refuses a front the entry door does not sit at, a
    row that disagrees with its manifest, and a manifest that names no entry
  * verify_prototype.py gate 4 refuses a page and contract that disagree on
    which fronts exist
  * finish_adu.py refuses to publish a spec whose declared front is wrong --
    the declaration changed, and the export must notice (the one Blender case)
"""
from pathlib import Path

from suite import (Case, ContractCase, Run, app_js, barn, barn_glb, index,
                   index_gates, manifest, page_gates, read_json, replace,
                   write_json)

G = "#117 front"
DOOR = "Door_D-FRONT"


def _identity(root: Path, **changes) -> dict:
    ident = dict(read_json(manifest(root))["model"])
    for key, value in changes.items():
        if value is ...:
            ident.pop(key, None)
        else:
            ident[key] = value
    return ident


def _declared_back_to_front(root: Path) -> None:
    """Manifest and row agree, on the wrong end: the only thing left to
    object is the geometry."""
    m = read_json(manifest(root))
    m["model"]["front"] = "-z"
    write_json(manifest(root), m)
    ix = read_json(index(root))
    ix["models"][0]["front"] = "-z"
    write_json(index(root), ix)


def _set(path_of, *keys_value):
    *keys, value = keys_value

    def setup(root: Path) -> None:
        obj = read_json(path_of(root))
        target = obj
        for k in keys[:-1]:
            target = target[k]
        if value is ...:
            target.pop(keys[-1])
        else:
            target[keys[-1]] = value
        write_json(path_of(root), obj)
    return setup


CASES = [
    ContractCase(G, "the barn cabin's identity, with its front, passes",
                 lambda mc, root: mc.identity_problems(_identity(root))),
    ContractCase(G, "an identity with no front",
                 lambda mc, root: mc.identity_problems(_identity(root, front=...)),
                 "model.front must be one of"),
    ContractCase(G, "a front of +y: up is not an end of the building",
                 lambda mc, root: mc.identity_problems(_identity(root, front="+y")),
                 "model.front must be one of"),
    ContractCase(G, "the barn cabin's door is at its +z end",
                 lambda mc, root: mc.front_problems(barn_glb(root), "+z", DOOR)),
    ContractCase(G, "declared -z: the door is at the other end",
                 lambda mc, root: mc.front_problems(barn_glb(root), "-z", DOOR),
                 "but front is declared -z"),
    ContractCase(G, "declared +x: the door is on no side at all",
                 lambda mc, root: mc.front_problems(barn_glb(root), "+x", DOOR),
                 "but front is declared +x"),
    ContractCase(G, "an entry node the file does not have",
                 lambda mc, root: mc.front_problems(barn_glb(root), "+z", "Door_D-NOWHERE"),
                 "has 0 nodes named 'Door_D-NOWHERE'"),

    Case(G, "manifest and index agree on -z, and the door disagrees",
         _declared_back_to_front, index_gates(), "sits at the +z end"),
    Case(G, "the index row says -z, the manifest +z",
         _set(index, "models", 0, "front", "-z"), index_gates(), "the row's front is '-z'"),
    Case(G, "a manifest that names no entry node",
         _set(manifest, "model", "entry_node", ...), index_gates(), "names no entry_node"),
    Case(G, "an entry node at the back of the building",
         _set(manifest, "model", "entry_node", "Wall_N"), index_gates(), "Wall_N sits at the -z end"),
    Case(G, "app.js and model_contract disagree on the fronts",
         replace(app_js, ("  '-x': [-1, 0, 0],\n", "")), page_gates(), "fronts differ"),
    Case(G, "Blender: the spec declares -z and the export refuses to publish",
         replace(lambda r: barn(r) / "spec.yaml", ('      glb: "+z"\n', '      glb: "-z"\n')),
         [Run("finish_adu.py", fails=True, blender=True)],
         "but front is declared -z"),
]
