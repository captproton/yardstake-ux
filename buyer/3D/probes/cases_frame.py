"""
cases_frame.py — the barn cabin's frame gate catches a mirror image (#145).

verify_frame.py holds the built mesh to A1.1's left and right. These cases
break the BUILD, never the spec (rule 19), and do it after build_adu.py's own
report has run, so nothing that build prints can warn the gate (rule 35).

  * mirrored   the finished building reflected across its centreline, which
               is what a compass read backwards produces. Must FAIL.
  * rotated    the finished building turned 180 degrees. Not a mirror image:
               every left is still a left. Must PASS, or the gate is testing
               which way the model points rather than its handedness.
  * as built   must PASS.
"""
from pathlib import Path

from suite import BARN, Case, Run, model_dir

BUILD = "build_adu.py"
ANCHOR = ('    out.mkdir(parents=True, exist_ok=True)\n'
          '    dest = out / "barn_cabin_524.blend"\n')


def _transform_before_save(work: Path, matrix: str, what: str) -> None:
    path = model_dir(work, BARN) / BUILD
    text = path.read_text()
    if text.count(ANCHOR) != 1:
        raise AssertionError(
            f"{what}: the save in {BUILD} is not there exactly once "
            f"(found {text.count(ANCHOR)}). The case is stale — re-read main().")
    lesion = ("    import math as _math\n"
              "    import mathutils as _mu\n"
              f"    _M = {matrix}\n"
              "    for _o in bpy.data.objects:\n"
              "        if _o.parent is None:\n"
              "            _o.matrix_world = _M @ _o.matrix_world\n")
    path.write_text(text.replace(ANCHOR, lesion + ANCHOR))


def _mirrored(work: Path) -> None:
    """Reflect across x = 11, the centreline of the 22'-0" body."""
    _transform_before_save(
        work, "_mu.Matrix.Translation((22.0, 0.0, 0.0)) @ _mu.Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0))",
        "mirrored")


def _rotated(work: Path) -> None:
    """Turn 180 degrees about the vertical, about the footprint's centre."""
    _transform_before_save(
        work, "_mu.Matrix.Translation((22.0, 30.0, 0.0)) @ _mu.Matrix.Rotation(_math.pi, 4, 'Z')",
        "rotated")


def _runs(fails: bool) -> list:
    return [Run(BUILD, fails=False, blender=True, model=BARN),
            Run("verify_frame.py", fails=fails, blender=True, model=BARN)]


CASES = [
    Case("frame", "barn cabin: a mirror image of the building fails the frame gate",
         _mirrored, _runs(fails=True),
         contains="[FAIL] facing the front, W-BATH is on the viewer's LEFT wall"),
    Case("frame", "barn cabin: the building turned 180 degrees is not a mirror image",
         _rotated, _runs(fails=False),
         # Not "all frame gates pass": an untransformed build prints that too.
         # This line proves the rotation happened and the gates still passed.
         contains="front faces +Y in Blender"),
    Case("frame", "barn cabin: the building as built passes the frame gate",
         None, _runs(fails=False),
         contains="all frame gates pass"),
]
