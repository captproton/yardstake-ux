"""
cases_export.py — Laurel's export refuses what it should (#131).

finish.py publishes nothing unless every gate passes. These cases break one
thing each, in a copy, and require the refusal by name:

  * the spec declares the wrong front -- the manifest must not publish
  * the BUILD lowers the slab by a foot -- the lod2 baseline must fail. The
    build, not the spec: moving the spec's baseline would move the
    expectation with it (rule 19)
  * the export as it is -- every gate passes, so the refusals above are the
    breakage and not the harness
"""
from pathlib import Path

from suite import LAUREL, Case, Run, model_dir, replace

FINISH = "finish.py"


def _spec(root: Path) -> Path:
    return model_dir(root, LAUREL) / "spec.yaml"


def _slab_lowered(root: Path) -> None:
    path = model_dir(root, LAUREL) / "build.py"
    text = path.read_text()
    old = '    slab = box("Slab", 0.0, W, 0.0, D, -slab_t, 0.0, site)\n'
    if text.count(old) != 1:
        raise AssertionError("build.py no longer builds the slab in one line "
                             "the case can find. The case is stale.")
    path.write_text(text.replace(old, '    slab = box("Slab", 0.0, W, 0.0, D, -slab_t - 1.0, 0.0, site)\n'))


CASES = [
    Case("export", "laurel: a spec declaring the front +z publishes nothing",
         replace(_spec, ('      glb: "-z"\n', '      glb: "+z"\n')),
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="Leaf_D-1 sits at the -z end"),
    Case("export", "laurel: a slab a foot too deep fails the lod2 baseline",
         _slab_lowered,
         [Run(FINISH, fails=True, blender=True, model=LAUREL)],
         contains="floor (min y) is -0.4064 m, the baseline says -0.1016 m"),
    Case("export", "laurel: the export as built passes every gate",
         None,
         [Run(FINISH, fails=False, blender=True, model=LAUREL)],
         contains="[PASS] lod2 sits on its baseline"),
]
