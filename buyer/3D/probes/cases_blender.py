"""
cases_blender.py — a Blender script that crashes FAILS (#151).

Blender exits 0 when a `--python` script raises an uncaught exception. It
prints the traceback, then reports success. Every Blender gate in buyer/3D
exits 1 on a failed gate, but a CRASH -- a missing key, a renamed object, a
typo -- went out as a pass to anything reading the exit code.

`--python-exit-code 1` fixes it for every script at once, and the harness now
passes it. This case is the proof: a build that raises before doing anything
must exit non-zero, judged by the exit code alone. It is the one case that
expects a traceback, so it cannot pass on the traceback check instead.
"""
from pathlib import Path

from suite import BARN, Case, Run, model_dir

BUILD = "build_adu.py"
ANCHOR = "def main():\n"
CRASH = "probe #151: a deliberate crash"


def _crash_first(work: Path) -> None:
    path = model_dir(work, BARN) / BUILD
    text = path.read_text()
    if text.count(ANCHOR) != 1:
        raise AssertionError(f"{BUILD} does not define main() exactly once "
                             f"(found {text.count(ANCHOR)}). The case is stale.")
    path.write_text(text.replace(ANCHOR, f"{ANCHOR}    raise RuntimeError({CRASH!r})\n"))


CASES = [
    Case("blender", "a Blender script that crashes exits non-zero",
         _crash_first,
         [Run(BUILD, fails=True, blender=True, model=BARN, traceback_expected=True)],
         contains=CRASH),
]
