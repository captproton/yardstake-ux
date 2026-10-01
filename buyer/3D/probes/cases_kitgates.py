"""
cases_kitgates.py -- the gates in adu_kit/gates.py still refuse what they must (#169, #177).

These perturb Laurel's BUILD, not its spec (a red test that moves the spec proves
nothing, because the build would move with it), and require a gate in the kit to say no.

  * an exterior opening recorded under a block the gate does not know   must FAIL

That is the hole a reviewer found in the first cut of the move: a block that is present
but misspelled was skipped as if it were an interior door, so the gate had nothing to
look at on that opening and still printed PASS.
"""
from pathlib import Path

from suite import Case, LAUREL, Run, model_dir

G = "kitgates"
BUILD = "build.py"


def _patch(work: Path, old: str, new: str, what: str) -> None:
    path = model_dir(work, LAUREL) / BUILD
    text = path.read_text()
    if text.count(old) != 1:
        raise AssertionError(
            f"{what}: the line this case perturbs is not in {BUILD} exactly once "
            f"(found {text.count(old)}). The case is stale -- re-read build.py.")
    path.write_text(text.replace(old, new))


def _a_block_the_gate_does_not_know(work: Path) -> None:
    """Record every exterior opening under "<block>_typo". The wall and the geometry are
    untouched, so the only thing wrong is a block name no gate can place."""
    _patch(work,
           "z0=z0, z1=z1, along=along, row=row, block=block))",
           'z0=z0, z1=z1, along=along, row=row, block=block + "_typo"))',
           "an exterior opening under an unknown block")


CASES = [
    Case(G, "laurel: an exterior opening recorded under a block no gate knows",
         _a_block_the_gate_does_not_know,
         [Run(BUILD, fails=True, blender=True, model=LAUREL)],
         contains="every exterior opening is on the wall its spec block names"),
]
