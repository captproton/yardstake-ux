"""
cases_equipment.py — the ground-mounted placement rule holds (#134, PR C).

build.py's _ground_mounted gates spec.fixtures.condenser.placement_rule on
the built mesh. These cases break the BUILD, never the spec (rule 19), one
clause each:

  * the condenser built where the rear elevation draws it   must FAIL
  * the condenser pushed half a foot into the wall          must FAIL
  * the pad built three inches low, so the unit floats      must FAIL
  * the condenser before window W-D1, above its sill        must FAIL
  * the condenser as built                                  must PASS

The first is the discrepancy the spec records: the rear elevation's reading
is the one two other drawings outvote, and building it must not pass.
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir

G = "equipment"
BUILD = "build.py"
RULE = "the condenser keeps the ground-mounted placement rule"
RETURN = ('    return outer, outer + (x1 - x0), y0, y1, c["pad"]["top"]["ft"], '
          'c["pad"]["top"]["ft"] + se["top"] - se["base"]\n')


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"{what}: the line this case perturbs is not in {BUILD} "
                             f"exactly once (found {text.count(old)}). The case is stale.")
    path.write_text(text.replace(old, new))


def _where_the_rear_elevation_draws_it(work: Path) -> None:
    # Behind the rear wall at X 14.6..16.3, as A-2.0's rear elevation has it.
    _patch(work, RETURN,
           '    rx = c["rear_elevation"]["x"]\n'
           '    return rx[0], rx[1], -(x1 - x0) - 1.0, -1.0, c["pad"]["top"]["ft"], '
           'c["pad"]["top"]["ft"] + se["top"] - se["base"]\n',
           "the condenser built where the rear elevation draws it")


def _into_the_wall(work: Path) -> None:
    _patch(work, RETURN,
           '    return outer - 0.5, outer - 0.5 + (x1 - x0), y0, y1, c["pad"]["top"]["ft"], '
           'c["pad"]["top"]["ft"] + se["top"] - se["base"]\n',
           "the condenser pushed into the wall")


def _pad_low(work: Path) -> None:
    _patch(work,
           '            box("Equip_pad", x0, x1 + m, y0 - m, y1 + m, pad["bottom"]["ft"], pad["top"]["ft"], coll)]\n',
           '            box("Equip_pad", x0, x1 + m, y0 - m, y1 + m, pad["bottom"]["ft"], pad["top"]["ft"] - 0.25, coll)]\n',
           "the pad built three inches low")


def _before_window_d1(work: Path) -> None:
    # Moved along the wall to window W-D1 (Y 10.75..14.25, sill 3.5) and
    # made tall enough to reach past the sill.
    _patch(work, RETURN,
           '    return outer, outer + (x1 - x0), 11.5, 11.5 + (y1 - y0), c["pad"]["top"]["ft"], 4.5\n',
           "the condenser before window W-D1")


CASES = [
    Case(G, "laurel: the condenser built where the rear elevation draws it",
         _where_the_rear_elevation_draws_it,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="A-1.1 draws"),
    Case(G, "laurel: the condenser pushed half a foot into the X 24 wall",
         _into_the_wall,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="inside the X 24 wall's outer face"),
    Case(G, "laurel: the pad built three inches low, the unit floating",
         _pad_low,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="the unit stands at 0.0000, its pad's top is -0.2500"),
    Case(G, "laurel: the condenser before window W-D1, above its sill",
         _before_window_d1,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="it rises above W-D1's sill in front of it"),
    Case(G, "laurel: the condenser as built keeps the rule",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains=f"[PASS] {RULE}"),
]
