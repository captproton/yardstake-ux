"""
cases_plan.py — Laurel's interior is held to A-1.0's ink (#132, P3b).

build.py's gate "the built partitions and interior doors sit where A-1.0
draws them" compares the MESH with spec.plan_overlay, the ink read off the
PDF's vectors. These cases move things in the BUILD, never the spec (rule 19),
so the only thing that can object is a gate holding the mesh to the drawing:

  * P_block_W built a foot toward +Y           must FAIL
  * door 2's opening built half a foot along   must FAIL
  * the build as it is                          must PASS
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir

BUILD = "build.py"
GATE = "the built partitions and interior doors sit where A-1.0 draws them"


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in "
                             f"{BUILD} exactly once (found {text.count(old)}). "
                             f"The case is stale — re-read build.py.")
    path.write_text(text.replace(old, new))


def _block_wall_moved(work: Path) -> None:
    _patch(work,
           '        near = row["at_ft"]\n        far = near + it if',
           '        near = row["at_ft"] + (1.0 if row["id"] == "P_block_W" else 0.0)\n'
           '        far = near + it if',
           "P_block_W moved")


def _door_2_moved(work: Path) -> None:
    _patch(work,
           '    for d in layout["door_openings"]:\n        ty = dt[str(d["type"])]\n',
           '    for d in layout["door_openings"]:\n'
           '        if d["id"] == "D-2":\n'
           '            d = dict(d, a_ft=d["a_ft"] + 0.5, b_ft=d["b_ft"] + 0.5)\n'
           '        ty = dt[str(d["type"])]\n',
           "door 2 moved")


CASES = [
    Case("plan", "laurel: P_block_W built a foot off where A-1.0 draws it",
         _block_wall_moved,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="P_block_W is built"),
    Case("plan", "laurel: door 2 built half a foot along its wall",
         _door_2_moved,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="D-2's leaf centres on"),
    Case("plan", "laurel: the interior as built sits where A-1.0 draws it",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {GATE}"),
]
