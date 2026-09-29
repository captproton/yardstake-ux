"""
cases_interior.py — Laurel's interior fixtures are built where A-1.0 draws them (#134, PR B).

build.py's fixture gates compare each fixture's MESH with spec.fixtures: the
drawn plan (PR A, re-measured off A-1.0 on every CI run), the stud-face rule
and the declared heights, and the water heater with Rheem's published size.
These cases break the BUILD, never the spec (rule 19), one way each:

  * the range built half a foot along the counter          must FAIL
  * every fixture built exactly as drawn, not to the studs  must FAIL
  * the water heater built at the plan symbol's 22"         must FAIL
  * the tub left out                                        must FAIL
  * the counter built solid across the dishwasher's opening must FAIL
  * the toilet built as one block at the tank's height      must FAIL
  * the fixtures as built                                   must PASS

The second is the gap the stud-face rule exists to close: A-1.0 draws each
fixture against the gyp board, which this model carries as a material, so a
fixture built as drawn stands half an inch off a bare stud face.
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir

G = "interior"
BUILD = "build.py"
WHERE = "every fixture is built where A-1.0 draws it, to the stud face, at its declared height"
HEATER = "the water heater stands on the drawn circle's centre, at the size Rheem publishes"


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in {BUILD} "
                             f"exactly once (found {text.count(old)}). The case is stale.")
    path.write_text(text.replace(old, new))


def _range_moved(work: Path) -> None:
    _patch(work,
           '    made.append(box("Fix_range", *slab(at["range"], 0.0, h["range"]), coll))\n',
           '    made.append(box("Fix_range", *slab(dict(at["range"], y=[at["range"]["y"][0] - 0.5,'
           ' at["range"]["y"][1] - 0.5]), 0.0, h["range"]), coll))\n',
           "the range moved along the counter")


def _built_as_drawn(work: Path) -> None:
    _patch(work,
           '    at = {k: to_stud_faces(spec, v) for k, v in fx["drawn"].items() if isinstance(v, dict)}\n',
           '    at = {k: v for k, v in fx["drawn"].items() if isinstance(v, dict)}\n',
           "every fixture built exactly as drawn")


def _heater_at_the_symbol(work: Path) -> None:
    _patch(work,
           '                     whs["diameter"]["ft"] / 2, coll, sides=WH_SIDES))\n',
           '                     (wh["x"][1] - wh["x"][0]) / 2, coll, sides=WH_SIDES))\n',
           "the water heater at the plan symbol's size")


def _no_tub(work: Path) -> None:
    _patch(work,
           '    made.append(box("Fix_tub", *slab(at["tub"], 0.0, h["tub"]), coll))\n',
           '',
           "the tub left out")


def _counter_solid(work: Path) -> None:
    # Found by review: the outer box of a solid counter is the right one's.
    _patch(work,
           '    runs = [(cnt["y"][0], dw["y"][0]), (dw["y"][1], cnt["y"][1])]\n',
           '    runs = [(cnt["y"][0], cnt["y"][1])]\n',
           "the counter built solid across the dishwasher")


def _toilet_one_block(work: Path) -> None:
    _patch(work,
           '    made.append(multibox("Fix_toilet", [slab(bowl, 0.0, h["toilet_bowl"]),\n',
           '    made.append(multibox("Fix_toilet", [slab(bowl, 0.0, h["toilet_tank"]),\n',
           "the toilet built as one block")


CASES = [
    Case(G, "laurel: the range built half a foot along the counter",
         _range_moved,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Fix_range's y lo is 15.6663, A-1.0 draws 16.1663"),
    Case(G, "laurel: every fixture built as drawn, half an inch off the studs",
         _built_as_drawn,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="off a stud face"),
    Case(G, "laurel: the water heater built at the plan symbol's 22 inches",
         _heater_at_the_symbol,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Rheem publishes 20.25 in"),
    Case(G, "laurel: the tub left out",
         _no_tub,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Fix_tub was not built"),
    Case(G, "laurel: the counter built solid across the dishwasher's opening",
         _counter_solid,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Fix_counter fills the dishwasher's opening"),
    Case(G, "laurel: the toilet built as one block at the tank's height",
         _toilet_one_block,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="Fix_toilet's bowl stands above its rim height"),
    Case(G, "laurel: the fixtures as built pass",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {WHERE}"),
]
