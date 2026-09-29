"""
cases_furniture.py — the studio's furniture stands where a buyer can live
with it, and ships with its disclosure (#135).

build.py's _furniture_placed gates the barn cabin's arrangements, reused and
placed in Laurel, on the built mesh; finish.py resolves each presence option's
`arrangement` to the nodes the export carries. These cases break the BUILD or
the EXPORT, never the spec (rule 19):

  * the sofa moved into the walk between the two doors      must FAIL
  * the bed pushed half a foot into the X 0 wall            must FAIL
  * the sofa moved over the bed: two groups shown at once   must FAIL
  * the furniture as built                                  must PASS
  * lod0 exported without the Furniture collection          must FAIL
  * the manifest written without its disclosure             must FAIL

The third is why the two groups are checked against each other: a buyer can
show the bed and the sofa together, so they may not share a floor.
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir

G = "furniture"
BUILD = "build.py"
FINISH = "finish.py"
RULE = ("the furniture stands in the room: clear of walls, partitions, fixtures, "
        "walkways and door swings, one group clear of the other")
PLACE = '            by_mat.setdefault(pc["material"], []).append(place_box(pc, arr["place"]))\n'


def _patch(work: Path, name: str, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / name
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in {name} "
                             f"exactly once (found {text.count(old)}). The case is stale.")
    path.write_text(text.replace(old, new))


def _shifted(arr_id: str, dx: float, dy: float) -> str:
    """PLACE, with one arrangement's every box moved by (dx, dy) in plan."""
    return ('            x0, x1, y0, y1, z0, z1 = place_box(pc, arr["place"])\n'
            f'            if arr["id"] == {arr_id!r}:\n'
            f'                x0, x1, y0, y1 = x0 + {dx}, x1 + {dx}, y0 + {dy}, y1 + {dy}\n'
            '            by_mat.setdefault(pc["material"], []).append((x0, x1, y0, y1, z0, z1))\n')


def _sofa_in_the_walk(work: Path) -> None:
    # Eight feet along X puts it across D-6's route to D-1.
    _patch(work, BUILD, PLACE, _shifted("living_sofa", 8.0, 0.0), "the sofa moved into the walk")


def _bed_into_the_wall(work: Path) -> None:
    _patch(work, BUILD, PLACE, _shifted("sleep_bed", -0.5, 0.0), "the bed pushed into the X 0 wall")


def _sofa_over_the_bed(work: Path) -> None:
    # Seven feet toward the rear lands the sofa on the bed's floor.
    _patch(work, BUILD, PLACE, _shifted("living_sofa", 0.0, -7.0), "the sofa moved over the bed")


def _lod0_without_furniture(work: Path) -> None:
    _patch(work, FINISH,
           '                + list(colls["Fixtures"].objects) + list(colls["Furniture"].objects)\n',
           '                + list(colls["Fixtures"].objects)\n',
           "lod0 exported without the furniture")


def _no_disclosure(work: Path) -> None:
    _patch(work, FINISH,
           '            manifest[key] = variants[key]\n',
           '            pass\n',
           "the manifest written without its disclosure")


CASES = [
    Case(G, "laurel: the sofa moved into the walk between the doors",
         _sofa_in_the_walk,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="stands in rear_door_to_front_door"),
    Case(G, "laurel: the bed pushed half a foot into the X 0 wall",
         _bed_into_the_wall,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="runs into an exterior wall"),
    Case(G, "laurel: the sofa moved over the bed, both groups shown at once",
         _sofa_over_the_bed,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="overlap, and both can be shown at once"),
    Case(G, "laurel: the furniture as built stands in the room",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {RULE}"),
    Case(G, "laurel: lod0 exported without the Furniture collection",
         _lod0_without_furniture,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="names arrangement 'sleep_bed', which no exported node is"),
    Case(G, "laurel: the manifest written without its disclosure",
         _no_disclosure,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="disclosure is required"),
]
