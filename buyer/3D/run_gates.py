#!/usr/bin/env python3
"""
run_gates.py -- run every gate a model has, by one command, and say what ran.

    python3 run_gates.py                    fast + blender tiers, every model
    python3 run_gates.py --tier fast        no Blender; seconds. A subset of CI, not
                                            CI: the workflow keeps its own step list
                                            and runs the full probe suite, which here
                                            is the opt-in `probes` tier
    python3 run_gates.py --model laurel_a1_460 --tier blender
    python3 run_gates.py --tier probes      the break-one-thing suite (slow)
    python3 run_gates.py --list             what would run, and run nothing

Run from anywhere; paths resolve from this file. Plain Python, no packages.

WHERE THE LIST LIVES. Each model declares its own gates in
`models/<id>/gates.json`, and the checks that belong to no model in
`gates.json` beside this file. A new model adds one file and this script
needs no edit. Each gate is

    {"name": "...", "tier": "fast" | "blender" | "probes",
     "cmd":  ["{python}", "-m", "unittest", ...]        (fast, probes)
     "script": "build.py", "blend": "x.blend" | null    (blender)
     "args": ["--out", "{tmp}"]                        (blender; {tmp} is a fresh temp dir)
     "requires": ["yaml", "bin:pdftotext"]              (optional)}

A Blender gate runs in its model's directory (the scripts open files by
relative name); every other gate runs from buyer/3D, as CI does. A command may
use `{python}` and `{blender}`.

A GATE THAT DID NOT RUN HAS NOT PASSED. That is the lesson of #151 and of four
review rounds on #147 and #149, so this runner holds itself to it:
  * a missing requirement (PyYAML for this interpreter, `pdftotext`, Blender
    itself) is a SKIP, and any skip fails the run unless --allow-skip is given;
  * a Blender gate that exits 0 but printed no PASS line, or printed FAIL, or a
    Traceback, fails: Blender exits 0 on an uncaught exception without
    --python-exit-code 1, and this passes it, but a script that dies before its
    first gate must not read as green either.

Blender is found by $BLENDER, then `blender` on PATH, then the macOS app. An
alias (as in ~/.zshrc) does not reach a subprocess, so this does not use one.

WHICH PYTHON. Three are in play on the maintainer's machine, and a bare
`python3` can resolve to Apple's, which has no PyYAML. This runs the fast tier
with the interpreter that runs this script, checks the requirements first, and
prints that interpreter, so a red run says which Python it was.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
TIERS = ("fast", "blender", "probes")
DEFAULT_TIERS = ("fast", "blender")          # probes take 7-30 minutes
MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
GATE_KEYS = {"name", "tier", "cmd", "script", "blend", "args", "requires", "timeout"}
PASS_RE =re.compile(r"\[PASS\]|\bPASS\b")
FAIL_RE = re.compile(r"\[FAIL\]|\bFAIL\b")


def find_blender():
    for cand in (os.environ.get("BLENDER"), shutil.which("blender"), MAC_BLENDER):
        if cand and Path(cand).is_file() and os.access(cand, os.X_OK):
            return cand
    return None


def _strings(f, g, key, nonempty=False):
    v = g[key]
    if not (isinstance(v, list) and all(isinstance(x, str) and x for x in v)
            and (v or not nonempty)):
        raise SystemExit(f"{f}: gate {g['name']!r}: {key!r} must be "
                         f"{'a non-empty ' if nonempty else 'a '}list of non-empty strings, "
                         f"found {v!r}")


def _shape(f, g):
    """The fields a gate is run from, checked as untrusted disk input, so a
    malformed manifest is a readable error here and never a traceback later."""
    unknown = set(g) - GATE_KEYS
    if unknown:
        # An unrecognised key is a typo or an escape hatch; neither is honoured.
        raise SystemExit(f"{f}: gate {g.get('name')!r}: unknown key(s) {sorted(unknown)}; "
                         f"the keys are {sorted(GATE_KEYS)}")
    if not (isinstance(g["name"], str) and g["name"]):
        raise SystemExit(f"{f}: a gate's 'name' must be a non-empty string, found {g['name']!r}")
    if g["tier"] == "blender":
        if not (isinstance(g["script"], str) and g["script"]):
            raise SystemExit(f"{f}: gate {g['name']!r}: 'script' must be a non-empty string")
        if g.get("blend") is not None and not (isinstance(g["blend"], str) and g["blend"]):
            raise SystemExit(f"{f}: gate {g['name']!r}: 'blend' must be a file name or null")
    else:
        _strings(f, g, "cmd", nonempty=True)
    for key in ("args", "requires"):
        if key in g:
            _strings(f, g, key)
    if "timeout" in g and not (isinstance(g["timeout"], int) and not isinstance(g["timeout"], bool)
                               and g["timeout"] > 0):
        raise SystemExit(f"{f}: gate {g['name']!r}: 'timeout' must be a positive integer")


def load_gates(only_model=None):
    """[(owner, cwd, gate)] from gates.json files, in a stable order."""
    files = [("shared", ROOT, ROOT / "gates.json")]
    for d in sorted(p for p in MODELS.iterdir() if p.is_dir()) if MODELS.is_dir() else []:
        files.append((d.name, d, d / "gates.json"))
    out = []
    for owner, cwd, f in files:
        if only_model and owner not in (only_model, "shared"):
            continue
        if not f.is_file():
            if owner == "shared":
                # The repository-wide checks are not optional: a deleted or
                # renamed list must not turn every one of them into silence.
                raise SystemExit(f"{f} is missing; the shared gate list is required")
            if (cwd / "spec.yaml").is_file():
                out.append((owner, cwd, {"name": "(no gates.json)", "tier": "fast",
                                         "missing": True}))
            continue
        try:
            doc = json.loads(f.read_text())
            gates = doc["gates"]
            assert isinstance(gates, list)
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as e:
            raise SystemExit(f"{f}: not a gate list ({e}); expected {{\"gates\": [...]}}")
        for g in gates:
            if not isinstance(g, dict):
                raise SystemExit(f"{f}: a gate must be an object, found {g!r}")
            for key in ("name", "tier"):
                if key not in g:
                    raise SystemExit(f"{f}: a gate has no {key!r}: {g}")
            if g["tier"] not in TIERS:
                raise SystemExit(f"{f}: gate {g['name']!r} has tier {g['tier']!r}; use {TIERS}")
            if g["tier"] == "blender" and "script" not in g:
                raise SystemExit(f"{f}: blender gate {g['name']!r} has no 'script'")
            if g["tier"] != "blender" and "cmd" not in g:
                raise SystemExit(f"{f}: gate {g['name']!r} has no 'cmd'")
            _shape(f, g)
            out.append((owner, cwd, g))
    return out


def missing_requirement(gate, blender):
    reqs = list(gate.get("requires", []))
    if gate["tier"] == "blender":
        reqs.append("blender")
    for r in reqs:
        if r == "blender":
            if not blender:
                return "Blender not found (set $BLENDER)"
        elif r.startswith("bin:"):
            if not shutil.which(r[4:]):
                return f"`{r[4:]}` is not on PATH"
        elif importlib.util.find_spec(r) is None:
            return f"{sys.executable} cannot import {r}"
    return None


def command(gate, blender, tmp=None):
    if gate["tier"] == "blender":
        cmd = [blender, "--background"]
        if gate.get("blend"):
            cmd.append(gate["blend"])
        # --python-exit-code must come before --python (#151)
        cmd += ["--python-exit-code", "1", "--python", gate["script"]]
        if gate.get("args"):
            cmd += ["--"] + [a.replace("{tmp}", tmp or "") for a in gate["args"]]
        return cmd
    return [c.replace("{python}", sys.executable).replace("{blender}", blender or "blender")
            for c in gate["cmd"]]


def run(owner, cwd, gate, blender, log_dir, timeout):
    """-> (status, note, seconds). status: pass | fail | skip."""
    with tempfile.TemporaryDirectory(prefix="run_gates_") as tmp:
        return _run(owner, cwd, gate, blender, log_dir, timeout, tmp)


def _run(owner, cwd, gate, blender, log_dir, timeout, tmp):
    if gate.get("missing"):
        return "fail", "the model has a spec.yaml and no gates.json", 0.0
    why = missing_requirement(gate, blender)
    if why:
        return "skip", why, 0.0
    cmd = command(gate, blender, tmp)
    if gate["tier"] != "blender":
        cwd = ROOT
    # adu_kit.kernel.load_spec shells out to `python3` from inside Blender; put
    # this interpreter first so it is the one with PyYAML, not Apple's.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""))
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace",
                           timeout=gate.get("timeout", timeout), env=env)
    except subprocess.TimeoutExpired:
        return "fail", "timed out", time.time() - t0
    except (OSError, ValueError) as e:
        # the command could not be started at all: not executable, bad cwd (OSError),
        # or an argument subprocess refuses, such as an embedded NUL (ValueError)
        return "fail", f"could not launch {cmd[0]!r}: {e}", time.time() - t0
    dt = time.time() - t0
    out = r.stdout + r.stderr
    if log_dir:
        (log_dir / f"{owner}__{re.sub(r'[^A-Za-z0-9_.-]+', '_', gate['name'])}.log").write_text(out)
    note = ""
    if gate["tier"] == "blender":
        # BOTH STREAMS: a script may report a failure on stderr and exit 0.
        n_pass, n_fail = len(PASS_RE.findall(out)), len(FAIL_RE.findall(out))
        note = f"PASS {n_pass} FAIL {n_fail}"
        if r.returncode:
            return "fail", f"exit {r.returncode}; {note}", dt
        if "Traceback" in out:
            return "fail", f"a traceback, and exit 0; {note}", dt
        if n_fail:
            return "fail", note, dt
        if not n_pass:                       # unconditional: there is no way to opt out
            return "fail", "exit 0 but printed no PASS line: it may not have run", dt
        return "pass", note, dt
    if r.returncode:
        tail = " | ".join([ln for ln in out.strip().splitlines() if ln.strip()][-2:])
        return "fail", f"exit {r.returncode}: {tail[:160]}", dt
    return "pass", note, dt


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run every gate a model declares.")
    ap.add_argument("--model", help="one model directory name, plus the shared gates")
    ap.add_argument("--tier", action="append", choices=TIERS,
                    help=f"repeatable; default {' + '.join(DEFAULT_TIERS)}")
    ap.add_argument("-k", dest="match", help="only gates whose name contains this")
    ap.add_argument("--list", action="store_true", help="list, do not run")
    ap.add_argument("--allow-skip", action="store_true",
                    help="a missing requirement is reported but does not fail the run")
    ap.add_argument("--log-dir", type=Path, help="write each gate's full output here")
    ap.add_argument("--timeout", type=int, default=3600, help="seconds per gate")
    args = ap.parse_args(argv)

    tiers = tuple(args.tier or DEFAULT_TIERS)
    gates = [(o, c, g) for o, c, g in load_gates(args.model)
             if g["tier"] in tiers and (not args.match or args.match in g["name"])]
    # A TYPOED FILTER MUST NOT READ AS GREEN: "0 passed of 0" exits 0 otherwise.
    if not gates:
        raise SystemExit(f"no gates match (model {args.model!r}, tiers {tiers}, "
                         f"-k {args.match!r}); nothing was run")
    if args.model and not any(o == args.model for o, _, _ in gates):
        raise SystemExit(f"no gates for model {args.model!r} in tiers {tiers}")
    if args.list:
        for o, _, g in gates:
            print(f"{g['tier']:8s} {o}/{g['name']}")
        return 0

    blender = find_blender()
    if args.log_dir:
        args.log_dir.mkdir(parents=True, exist_ok=True)
    print(f"python  {sys.executable} ({sys.version.split()[0]})")
    print(f"blender {blender or 'NOT FOUND'}")
    counts = {"pass": 0, "fail": 0, "skip": 0}
    for o, cwd, g in gates:
        status, note, dt = run(o, cwd, g, blender, args.log_dir, args.timeout)
        counts[status] += 1
        print(f"{status.upper():4s}  {g['tier']:7s} {o}/{g['name']}  {note}  ({dt:.0f}s)")
    print(f"\n{counts['pass']} passed, {counts['fail']} failed, {counts['skip']} skipped"
          f" of {len(gates)}")
    if counts["fail"] or (counts["skip"] and not args.allow_skip):
        if counts["skip"] and not args.allow_skip:
            print("a skipped gate has not passed; fix the requirement or pass --allow-skip")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
