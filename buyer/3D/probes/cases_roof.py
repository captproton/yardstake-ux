"""
cases_roof.py — Laurel's roof gates still catch a wrong roof (#130).

PLAN.md's P3 asks for one thing in particular: prove the plate-height gate can
fail by perturbing the BUILD, not the spec (rule 19 — a red test that moves the
spec proves nothing, because the build would move with it).

I proved both of these by hand while writing them, and a proof done by hand
once is a sentence in a commit message. These are the same two perturbations,
committed, so the suite re-proves them whenever anyone touches the roof.

WHY THEY ARE WORTH KEEPING, specifically. Both gates existed in a form that
could not fail:

  * "the roof plane meets T.P. 1 and T.P. 2" asked the `Shed` helper, which is
    the expression the roof is laid out from. `shed.under(0)` is
    `top_of_plate_rear` read straight back, so half of it compared a spec
    value to itself. A roof lifted a foot off the walls passed it.
  * nothing at all watched the roof's THICKNESS, and #129 built it from the
    framing depth instead of the depth A-2.0 draws — 2.47" too thick, on the
    most visible surface of the building, for the life of that PR.

Each case below is the exact mistake that was made, not a synthetic one.
"""
from pathlib import Path

from suite import Case, LAUREL, Run, model_dir

BUILD = "build.py"


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(
            f"{what}: the line this case perturbs is not in {BUILD} exactly once "
            f"(found {text.count(old)}). The case is stale — re-read build.py.")
    path.write_text(text.replace(old, new))


def _roof_lifted_off_the_plates(work: Path) -> None:
    """Float the roof a foot above the walls, leaving the Shed helper correct.

    Anything that asks the helper still gets the right answer, so this is the
    perturbation that tells a gate measuring the MESH from one measuring the
    expression the mesh was drawn from."""
    _patch(work,
           "    profile = [(y0, shed.under(y0)), (y1, shed.under(y1)),\n"
           "               (y1, shed.under(y1) + asm), (y0, shed.under(y0) + asm)]",
           "    _lift = 1.0\n"
           "    profile = [(y0, shed.under(y0) + _lift), (y1, shed.under(y1) + _lift),\n"
           "               (y1, shed.under(y1) + asm + _lift), (y0, shed.under(y0) + asm + _lift)]",
           "roof lifted off the plates")


def _roof_built_from_the_framing_depth(work: Path) -> None:
    """Extrude the 2x12 plus sheathing, which is what #129 did.

    S1.0 frames the roof with 2x12s and A-2.0's own section details them, but
    both elevations DRAW the edge 9 1/4" deep. This spec's authority rule gives
    the visible edge to A-2.0, and the gate that holds it is the 10'-9 1/2"
    height at the front edge — the only roof dimension that sees the
    thickness, because the plate gates only ever see the underside."""
    _patch(work,
           '    asm = rf["assembly"]["modelled_thickness"]["ft"]',
           '    asm = (rf["assembly"]["rafter_depth"]["ft"]\n'
           '           + rf["assembly"]["sheathing_ft"]["ft"])',
           "roof from the framing depth")


CASES = [
    Case("roof", "laurel: the roof floats a foot above the plates",
         _roof_lifted_off_the_plates,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="the built roof underside meets T.P. 1"),
    Case("roof", "laurel: the roof is extruded from the framing depth, not the drawn depth",
         _roof_built_from_the_framing_depth,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="the roof top at the front edge"),
    Case("roof", "laurel: the roof as built passes every roof gate",
         None,
         [Run(BUILD, fails=False, blender=True, model=LAUREL)],
         contains="the built roof underside meets T.P. 1"),
]
