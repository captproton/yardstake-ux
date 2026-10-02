"""
adu_kit/gatelog.py -- the pass/fail bookkeeping every model's build gates share (#169).

Plain Python; no Blender, so it can be tested anywhere.

A GATE PRINTS ONE LINE AND LEAVES A RECORD. `gate()` is what a build script's
report calls for each check: it prints `[PASS]` or `[FAIL]` with the label (and the
detail, only on a failure), and remembers the labels of the failures. `skip()` is a
gate that CANNOT be judged on this run, said out loud, and remembered separately.
`run_gates.py` reads these lines, so the format is part of the contract: a Blender
gate must print a PASS line or it is treated as not having run.

Laurel's build.py used to define `gate`, `skip`, `FAILED` and `SKIPPED` itself, and
the barn cabin has its own. This is Laurel's, moved unchanged; the barn cabin's is
not touched here.
"""
from __future__ import annotations


class GateLog:
    def __init__(self):
        self.failed: list = []
        self.skipped: list = []

    def gate(self, ok, label, detail=""):
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not ok else ""))
        if not ok:
            self.failed.append(label)

    def skip(self, label, why):
        """A gate that CANNOT be judged on this run, said out loud.

        `--no-openings` builds an uncut model on purpose, and the opening gate
        read its evidence from the volumes recorded while cutting. With no cuts
        that mapping is empty, every loop over it runs zero times, and the gate
        printed PASS on a model with no openings in it at all. A gate with
        nothing to look at has not passed; it has not run.
        """
        print(f"  [SKIP] {label} -- {why}")
        self.skipped.append(label)
