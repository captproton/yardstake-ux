"""
cases_trim.py — Laurel's Tier 1 trim is held to what spec.trim says (#132).

build.py's trim gates ask the MESH whether a point is inside it, at places
worked out from spec.trim and the openings. These cases break the BUILD,
never the spec (rule 19), one member at a time:

  * the window-side casing skipped on the X 0 wall         must FAIL
  * baseboard run straight across every doorway            must FAIL
  * the siding trim put in the collection lod0 exports     must FAIL
  * finish.py exporting the held-back siding trim in lod0  must FAIL
  * the trim as built                                      must PASS
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir

BUILD = "build.py"
FINISH = "finish.py"
CASED = "every opening is cased on each room side"
BASEBOARD = "every room face carries baseboard, and no doorway is blocked by it"
SIDING = "the siding exterior trim is built on every exterior opening, as its own node"


def _patch(work: Path, name: str, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / name
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in "
                             f"{name} exactly once (found {text.count(old)}). "
                             f"The case is stale — re-read {name}.")
    path.write_text(text.replace(old, new))


def _x0_uncased(work: Path) -> None:
    _patch(work, BUILD,
           '        for face in faces[host]:\n            trim_parts[host] += members(',
           '        for face in (faces[host] if host != "Wall_x0" else []):\n'
           '            trim_parts[host] += members(',
           "the X 0 wall's casing skipped")


def _baseboard_across_doors(work: Path) -> None:
    _patch(work, BUILD,
           '        doors = sorted((a0 - cw, a1 + cw) for (h, a0, a1), g in stacks.items()\n'
           '                       if h == host and not stack_span(g)[2])\n',
           '        doors = []\n',
           "baseboard run across every doorway")


def _siding_in_trim(work: Path) -> None:
    _patch(work, BUILD,
           '    siding = multibox("Trim_ext_siding", siding_parts, siding_coll)\n',
           '    siding = multibox("Trim_ext_siding", siding_parts, trim_coll)\n',
           "the siding trim put in the Trim collection")


def _siding_exported(work: Path) -> None:
    _patch(work, FINISH,
           '                + list(colls["Partitions"].objects) + list(colls["Trim"].objects)\n',
           '                + list(colls["Partitions"].objects) + list(colls["Trim"].objects)\n'
           '                + list(colls["SidingTrim"].objects)\n',
           "the siding trim exported in lod0")


CASES = [
    Case("trim", "laurel: the X 0 wall's windows built with no interior casing",
         _x0_uncased,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Wall_x0 2.5000..7.5000 on its face at 0.4583: no left jamb, right jamb, head, sill, apron"),
    Case("trim", "laurel: baseboard run straight across every doorway",
         _baseboard_across_doors,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="baseboard runs across the doorway in P_pantry_N"),
    Case("trim", "laurel: the siding trim built into the collection lod0 exports",
         _siding_in_trim,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Trim_ext_siding is in the Trim collection"),
    Case("trim", "laurel: finish.py ships the held-back siding trim in lod0",
         _siding_exported,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="laurel_a1_460_lod0.glb carries ['Trim_ext_siding']"),
    Case("trim", "laurel: the trim as built passes every trim gate",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {BASEBOARD}"),
]
