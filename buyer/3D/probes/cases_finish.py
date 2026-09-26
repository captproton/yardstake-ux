"""
cases_finish.py — Laurel's exterior finish is a choice the page can make (#133).

A finish is geometry as well as colour: a stucco skin, or a lap-siding skin
with its exterior trim, swapped by one presence group. These cases break the
BUILD or the EXPORT one way each and require the refusal:

  * the siding skins built into the Shell collection           must FAIL
  * the siding trim built into the Trim collection              must FAIL
  * a siding skin left uncut                                    must FAIL
  * the siding reveals left untagged                            must FAIL
  * only the first opening on each wall given its reveal        must FAIL
  * lod0 exported without the siding collection                 must FAIL
  * a presence block that is a list of numbers                  must FAIL, readably
  * a presence group that furnishes no room, with no disclosure must PASS
  * the finish as built                                         must PASS

Exporting lod0 without the siding is the manifest naming nodes the file
lacks, which would be a button that shows nothing. The room-less group is
the contract change #133 made: a finish group is not furniture, so it asks
for no "not included" line -- while a group that names a `room` still does
(cases_rail).
"""
from pathlib import Path

from suite import LAUREL, Case, Run, edit, index_gates, manifest, model_dir

G = "finish"
BUILD = "build.py"
FINISH = "finish.py"
SKINS = "each wall's siding skin is its stucco skin's solid, with trim reveals and UVs"


def _patch(work: Path, name: str, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / name
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in {name} "
                             f"exactly once (found {text.count(old)}). The case is stale.")
    path.write_text(text.replace(old, new))


def _siding_in_shell(work: Path) -> None:
    _patch(work, BUILD,
           '            walls[name] = weld(name, [geom], siding_coll)\n',
           '            walls[name] = weld(name, [geom], shell)\n',
           "the siding skins built into Shell")


def _siding_trim_in_trim(work: Path) -> None:
    # Found by review: lod0 exports Trim, so the trim still showed there, but
    # lod1 exports only Siding, and the street view lost it silently.
    _patch(work, BUILD,
           '    siding = [multibox(host.replace("Wall_", "Trim_ext_siding_"), parts, siding_coll)\n',
           '    siding = [multibox(host.replace("Wall_", "Trim_ext_siding_"), parts, trim_coll)\n',
           "the siding trim built into Trim")


def _siding_uncut(work: Path) -> None:
    _patch(work, BUILD,
           '            cutter(f"cut_siding_{o[\'id\']}", siding_of[o["wall"]], o["a0"], o["a1"],\n'
           '                   o["z0"], o["z1"], o["along"], depth=sheath)\n',
           '            if o["wall"] != "Wall_front":\n'
           '                cutter(f"cut_siding_{o[\'id\']}", siding_of[o["wall"]], o["a0"], o["a1"],\n'
           '                       o["z0"], o["z1"], o["along"], depth=sheath)\n',
           "the front siding skin left uncut")


def _reveals_untagged(work: Path) -> None:
    _patch(work, BUILD,
           '                poly.material_index = trim_slot\n',
           '                pass\n',
           "the siding reveals left untagged")


def _reveals_partly_tagged(work: Path) -> None:
    # Found by review: the gate asked for one tagged face per skin, so every
    # opening after a wall's first could lose its reveal and still pass.
    _patch(work, BUILD,
           '        rects = [(o["a0"], o["a1"], o["z0"], o["z1"]) for o in built if o["wall"] == wall]\n',
           '        rects = [(o["a0"], o["a1"], o["z0"], o["z1"]) for o in built if o["wall"] == wall][:1]\n',
           "only each wall's first opening given its reveal")


def _lod0_without_siding(work: Path) -> None:
    _patch(work, FINISH,
           '        return (keep + siding + list(colls["Openings"].objects)\n',
           '        return (keep + list(colls["Openings"].objects)\n',
           "lod0 exported without the siding")


def _presence_is_numbers(work: Path) -> None:
    # Found by review: presence_block dereferenced each group as a mapping,
    # so a malformed spec raised mid-export instead of naming the problem.
    _patch(work, "spec.yaml",
           '  presence:\n    - id: exterior_finish\n',
           '  presence: [1]\n  presence_moved_aside:\n    - id: exterior_finish\n',
           "presence replaced by a list of numbers")


def _a_room_less_group_without_disclosure(m):
    for g in m["presence"]:
        g.pop("room", None)
    m.pop("disclosure", None)
    m.pop("disclosure_note", None)


CASES = [
    Case(G, "laurel: the siding skins built into the Shell collection",
         _siding_in_shell,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Siding_front is not in the Siding collection alone"),
    Case(G, "laurel: the siding trim built into the Trim collection",
         _siding_trim_in_trim,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Trim_ext_siding_front is in ['Trim'], not the Siding collection alone"),
    Case(G, "laurel: the front siding skin left uncut",
         _siding_uncut,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Siding_front holds"),
    Case(G, "laurel: the siding reveals left untagged",
         _reveals_untagged,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="has no trim reveal at its"),
    Case(G, "laurel: only the first opening on each wall given its reveal",
         _reveals_partly_tagged,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="has no trim reveal at its"),
    Case(G, "laurel: lod0 exported without the siding collection",
         _lod0_without_siding,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="presence exterior_finish: Siding_front is shown but not in the export"),
    Case(G, "laurel: a presence block that is a list of numbers is a named problem",
         _presence_is_numbers,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="variants.presence[0] must be an object, found int"),
    Case(G, "a presence group that furnishes no room needs no disclosure",
         edit(manifest, _a_room_less_group_without_disclosure),
         index_gates(fails=False)),
    Case(G, "laurel: the finish as built passes",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {SKINS}"),
]
