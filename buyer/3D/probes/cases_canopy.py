"""
cases_canopy.py — the optional entry canopy hangs where the plans draw it,
and switches whole (#144).

build.py's _canopy_hung gates spec.variants.canopy on the built mesh, and
finish.py ships the Canopy collection in lod0 and lod1 behind the
entry_canopy presence group. These cases break the BUILD or the EXPORT one
way each, never the spec (rule 19):

  * the canopy hung three inches low                        must FAIL
  * the canopy pushed an inch into the front wall           must FAIL
  * a brace fixed a foot above its wall plate               must FAIL
  * the frame built into the Openings collection            must FAIL
  * the canopy built three inches lower still, into the
    head trim below the ledger's allowance                  must FAIL
  * the braces offset a full radius on each axis, floating  must FAIL
  * the canopy as built                                     must PASS
  * lod0 exported without the Canopy collection             must FAIL

The sixth was found by review: offsetting a tilted rod's ends by its
radius on Y and on Z left it 0.10" off the wall and 0.05" above the frame,
inside the half-inch tolerance the gate first used. The fifth holds the one
contact the gate allows -- the ledger bearing on
door 1's siding head trim, no higher than that band's top -- to its bound.
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir

G = "canopy"
BUILD = "build.py"
FINISH = "finish.py"
RULE = ("the entry canopy hangs where A-2.0 draws it at A-3.4's size, in its own collection: "
        "outside the front wall, below the roof, clear of every opening and the siding trim")
UNDERSIDE = '    z0 = fe["underside"]\n'
SPAN = '    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, face, face + proj\n'


def _patch(work: Path, name: str, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / name
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in {name} "
                             f"exactly once (found {text.count(old)}). The case is stale.")
    path.write_text(text.replace(old, new))


def _low(work: Path) -> None:
    _patch(work, BUILD, UNDERSIDE, '    z0 = fe["underside"] - 0.25\n', "the canopy hung low")


def _into_the_wall(work: Path) -> None:
    _patch(work, BUILD, SPAN,
           '    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, face - 0.0833, face - 0.0833 + proj\n',
           "the canopy pushed into the wall")


def _brace_off_its_plate(work: Path) -> None:
    _patch(work, BUILD, '    zw = sum(fe["wall_connection"]) / 2\n',
           '    zw = sum(fe["wall_connection"]) / 2 + 1.0\n', "a brace fixed above its plate")


def _frame_in_openings(work: Path) -> None:
    _patch(work, BUILD,
           '    return [multibox("Canopy_frame", frame, coll), multibox("Canopy_slats", slats, coll)] + braces\n',
           '    return [multibox("Canopy_frame", frame, collection("Openings")), '
           'multibox("Canopy_slats", slats, coll)] + braces\n',
           "the frame built into the Openings collection")


def _into_the_head_trim(work: Path) -> None:
    # 0.3 ft down: the ledger now reaches below the band's top by far more
    # than the allowance, and the gate must say trim, not just height.
    _patch(work, BUILD, UNDERSIDE, '    z0 = fe["underside"] - 0.3\n', "the canopy into the head trim")


def _braces_floating(work: Path) -> None:
    _patch(work, BUILD,
           '    braces = [tube(f"Canopy_brace_{i}", [(bx, face + oy, zw + oz), (bx, face + land + oy, z1 + oz)], r, coll)\n',
           '    braces = [tube(f"Canopy_brace_{i}", [(bx, face + r, zw), (bx, face + land, z1 + r)], r, coll)\n',
           "the braces offset a full radius on each axis")


def _lod0_without_canopy(work: Path) -> None:
    _patch(work, FINISH,
           '              + list(colls["Canopy"].objects))\n', ')\n',
           "lod0 and lod1 exported without the canopy")


CASES = [
    Case(G, "laurel: the canopy hung three inches low",
         _low,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="its underside is at 6.7530, the elevations draw 7.003"),
    Case(G, "laurel: the canopy pushed an inch into the front wall",
         _into_the_wall,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="inside the front wall's outer face"),
    Case(G, "laurel: a brace fixed a foot above its wall plate",
         _brace_off_its_plate,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Canopy_brace_1 meets the wall at"),
    Case(G, "laurel: the canopy's frame built into the Openings collection",
         _frame_in_openings,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Canopy_frame is not in the Canopy collection"),
    Case(G, "laurel: the canopy dropped into door 1's head trim, past the ledger's allowance",
         _into_the_head_trim,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="runs into the front wall's siding trim"),
    Case(G, "laurel: the braces offset a full radius on each axis, floating off wall and frame",
         _braces_floating,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Canopy_brace_1 stops at Y"),
    Case(G, "laurel: the canopy as built hangs where drawn",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {RULE}"),
    Case(G, "laurel: lod0 exported without the Canopy collection",
         _lod0_without_canopy,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="presence entry_canopy: Canopy_brace_1 is shown but not in the export"),
]
