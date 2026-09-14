"""
suite.py — the probe harness (#121).

A probe breaks ONE thing and says what the checks must do about it: exit
non-zero (or zero), print a particular message, and never print a traceback.
A check that stops catching its case still passes every clean run, so the
probes are the only evidence a gate still does its job. They proved every gate
in #115–#122 and caught a real defect in three of those five PRs.

EVERY CASE BREAKS A COPY, NEVER THE WORKING TREE. The runner copies what the
checks read -- about 3 MB, not buyer/3D's 450 MB of plan sets and video -- into
a base once, then gives each case a fresh copy of that base in a temporary
directory. Interrupting a run leaves the working tree exactly as it was.

WHAT A CASE IS
    Case          a setup that breaks the copy, the scripts to run in it, and a
                  message that must appear in their combined output
    ContractCase  a direct call into the copy's model_contract, which must
                  return problems (containing a message) or none, and never raise

Cases name the barn cabin, the one real model, deliberately: they break its
actual manifest and index, which is what a regression would break.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

THREE_D = Path(__file__).resolve().parents[1]  # buyer/3D
BARN = "barn_cabin_524"

# What the checks read. Anything else under buyer/3D is not needed to run them.
ROOT_FILES = ("build_index.py", "verify_index.py", "verify_prototype.py")
# model_contract, in the kit make_base() copies whole (#126).
CONTRACT = Path("adu_kit") / "schema" / "model_contract.py"
DOC_FILES = ("docs/CONFIGURATION.md", "docs/COMMERCE.md")
# A model directory for the Blender case, without what an export never reads.
BLENDER_SKIP = ("renders", "refs", "docs", "tools", "__pycache__", "*.blend", "*.blend1")


# ── paths inside a copy ─────────────────────────────────────────────────────

def barn(root: Path) -> Path:
    return root / "models" / BARN


def manifest(root: Path) -> Path:
    return barn(root) / "export" / "variants.json"


def barn_glb(root: Path, level: str = "lod0") -> Path:
    return barn(root) / "export" / f"{BARN}_{level}.glb"


def index(root: Path) -> Path:
    return root / "prototype" / "models.json"


def fixture_index(root: Path) -> Path:
    return root / "prototype" / "fixtures" / "models.json"


def fixture_export(root: Path, model_id: str = "fixture_slab_box") -> Path:
    return root / "prototype" / "fixtures" / "models" / model_id / "export"


def app_js(root: Path) -> Path:
    return root / "prototype" / "app.js"


def index_html(root: Path) -> Path:
    return root / "prototype" / "index.html"


def config_doc(root: Path) -> Path:
    return root / "docs" / "CONFIGURATION.md"


# ── setups: small composable ways to break a copy ────────────────────────────

def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def existing(path: Path) -> Path:
    """A setup's target must already exist. A setup that CREATED its target
    would still run after the real target was renamed or removed -- and report
    the gate's response to a file the case was never meant to test."""
    if not path.is_file():
        raise AssertionError(f"probe target {path} does not exist")
    return path


def write(path_of: Callable[[Path], Path], text: str):
    return lambda root: existing(path_of(root)).write_text(text)


def edit(path_of: Callable[[Path], Path], change: Callable):
    """Load the JSON at path_of(root), let `change` mutate it, write it back."""
    def setup(root: Path) -> None:
        obj = read_json(path_of(root))
        change(obj)
        write_json(path_of(root), obj)
    return setup


def replace(path_of: Callable[[Path], Path], *pairs):
    """Text replacements; each `old` must appear exactly once, or the case is stale."""
    def setup(root: Path) -> None:
        text = existing(path_of(root)).read_text()
        for old, new in pairs:
            # EXACTLY ONCE: with a second copy of the snippet elsewhere, a probe
            # would break the wrong place once the intended one was removed.
            count = text.count(old)
            if count != 1:
                raise AssertionError(f"expected probe text once in {path_of(root).name}, found {count}: {old!r}")
            text = text.replace(old, new, 1)
        path_of(root).write_text(text)
    return setup


def append(path_of: Callable[[Path], Path], text: str):
    return lambda root: existing(path_of(root)).write_text(path_of(root).read_text() + text)


def steps(*setups):
    def setup(root: Path) -> None:
        for s in setups:
            s(root)
    return setup


def glb(json_text: str) -> bytes:
    """A binary glTF holding only a JSON chunk -- enough to be read, or refused."""
    data = json_text.encode()
    data += b" " * (-len(data) % 4)
    return (b"glTF" + struct.pack("<II", 2, 12 + 8 + len(data))
            + struct.pack("<I", len(data)) + b"JSON" + data)


# ── cases ──────────────────────────────────────────────────────────────────

@dataclass
class Run:
    script: str
    args: tuple = ()
    fails: bool = True
    blender: bool = False  # run inside Blender, from the barn cabin's directory
    timeout: int = 900  # seconds; a run that exceeds it is a failed case, not a hang


def both(build_fails: bool = True, verify_fails: bool = True) -> list:
    return [Run("build_index.py", ("--check",), build_fails),
            Run("verify_index.py", fails=verify_fails)]


def index_gates(fails: bool = True) -> list:
    return [Run("verify_index.py", fails=fails)]


def page_gates(fails: bool = True) -> list:
    return [Run("verify_prototype.py", fails=fails)]


@dataclass
class Case:
    group: str
    name: str
    setup: Optional[Callable[[Path], None]]
    runs: list
    contains: Optional[str] = None

    @property
    def needs_blender(self) -> bool:
        return any(r.blender for r in self.runs)


@dataclass
class ContractCase:
    group: str
    name: str
    call: Callable  # (model_contract module, base root) -> list of problems
    contains: Optional[str] = None  # None: there must be no problems

    needs_blender = False


@dataclass
class Result:
    case: object
    ok: bool
    skipped: bool = False
    reason: str = ""
    detail: list = field(default_factory=list)


# ── the workspace ───────────────────────────────────────────────────────────

def make_base(dst: Path, with_blender_model: bool = False) -> Path:
    """Copy what the checks read into dst."""
    dst.mkdir(parents=True)
    for name in ROOT_FILES + DOC_FILES:
        (dst / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(THREE_D / name, dst / name)
    shutil.copytree(THREE_D / "prototype", dst / "prototype",
                    ignore=shutil.ignore_patterns("__pycache__", "zz_*"))
    # The kit a model's Blender scripts import (#126). A copy without it
    # would fail the Blender case on an import, not on what it tests.
    shutil.copytree(THREE_D / "adu_kit", dst / "adu_kit",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for model in sorted(p for p in (THREE_D / "models").iterdir() if p.is_dir()):
        out = dst / "models" / model.name
        if with_blender_model and model.name == BARN:
            shutil.copytree(model, out, ignore=shutil.ignore_patterns(*BLENDER_SKIP))
            continue
        out.mkdir(parents=True)
        if (model / "spec.yaml").is_file():
            shutil.copy2(model / "spec.yaml", out / "spec.yaml")
        # A declared pending export (build_index.PENDING), which gate 6 reads.
        if (model / "EXPORT_PENDING").is_file():
            shutil.copy2(model / "EXPORT_PENDING", out / "EXPORT_PENDING")
        if (model / "export").is_dir():
            shutil.copytree(model / "export", out / "export")
    # The thumbnails the index publishes, so gate 2 can resolve them.
    #
    # THE INDEX IS INPUT, EVEN HERE. A malformed models.json is exactly what
    # the cases exist to report, so it must not stop the base being built; it
    # just means no thumbnails are copied. And a thumbnail path is contained:
    # one with enough `..` could otherwise read from outside buyer/3D or write
    # outside this temporary base -- the one thing the suite promises not to do.
    try:
        rows = read_json(dst / "prototype" / "models.json").get("models")
    except (ValueError, OSError, AttributeError):
        rows = None
    for row in rows if isinstance(rows, list) else []:
        thumb = row.get("thumbnail") if isinstance(row, dict) else None
        if not isinstance(thumb, str):
            continue
        try:
            src = (THREE_D / "prototype" / thumb).resolve()
            target = (dst / "prototype" / thumb).resolve()
        except (OSError, ValueError):  # e.g. an embedded null byte
            print(f"probes: not copying thumbnail {thumb!r}: it is not a usable path", file=sys.stderr)
            continue
        if not (inside(src, THREE_D) and inside(target, dst)):
            print(f"probes: not copying thumbnail {thumb!r}: it resolves outside "
                  f"buyer/3D or the temporary base", file=sys.stderr)
            continue
        if src.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    return dst


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def find_blender() -> Optional[str]:
    for candidate in (os.environ.get("BLENDER"), shutil.which("blender"),
                      "/Applications/Blender.app/Contents/MacOS/Blender"):
        if candidate and Path(candidate).exists():
            # Absolute: the Blender case runs from the copy's model directory,
            # where a relative BLENDER=./path no longer points anywhere.
            return str(Path(candidate).resolve())
    return None


def _text(data) -> str:
    return data.decode(errors="replace") if isinstance(data, bytes) else (data or "")


def load_contract(root: Path):
    spec = importlib.util.spec_from_file_location("probe_model_contract", root / CONTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_case(case, base: Path, blender: Optional[str]) -> Result:
    if isinstance(case, ContractCase):
        return run_contract_case(case, base)
    with tempfile.TemporaryDirectory(prefix="probe-") as tmp:
        work = Path(tmp) / "3D"
        shutil.copytree(base, work, symlinks=True)
        if case.setup:
            try:
                case.setup(work)
            except Exception:
                return Result(case, ok=False, reason="setup failed -- the case is stale",
                              detail=traceback.format_exc().splitlines()[-3:])
        # SKIP ONLY AFTER THE SETUP SUCCEEDS. Most machines have no Blender, and
        # a Blender case skipped before its setup would never report that the
        # setup had gone stale -- it would stop testing without saying so.
        if case.needs_blender and not blender:
            return Result(case, ok=True, skipped=True,
                          reason="Blender not found (set BLENDER=/path/to/blender to run it)")
        outputs, reasons = [], []
        for run in case.runs:
            if run.blender:
                cmd = [blender, "--background", "--python", run.script, "--"]
                cwd = barn(work)
            else:
                cmd = [sys.executable, run.script, *run.args]
                cwd = work
            label = " ".join([run.script, *run.args])
            # A HANG OR A LAUNCH FAILURE IS A FAILED CASE, not the end of the
            # suite: the runner's own contract is a result for every case and
            # a summary, never a traceback.
            try:
                p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=run.timeout)
            except subprocess.TimeoutExpired as e:
                outputs.append(_text(e.stdout) + _text(e.stderr))
                reasons.append(f"{label} timed out after {run.timeout}s")
                continue
            except OSError as e:
                reasons.append(f"{label} could not be started: {e}")
                continue
            out = p.stdout + p.stderr
            outputs.append(out)
            if (p.returncode != 0) != run.fails:
                reasons.append(f"{label} exited {p.returncode}, expected "
                               f"{'non-zero' if run.fails else '0'}")
            if "Traceback" in out:
                reasons.append(f"{label} printed a traceback")
        # Restore permissions a case removed, so the directory can be cleaned.
        for path in work.rglob("*"):
            try:
                path.chmod(0o755 if path.is_dir() else 0o644)
            except OSError:
                pass
    combined = "\n".join(outputs)
    hit = next((line.strip() for line in combined.splitlines()
                if case.contains and case.contains in line), None)
    if case.contains and hit is None:
        reasons.append(f"no output contains {case.contains!r}")
    detail = [hit] if hit else [l for l in combined.splitlines() if l.strip()][-6:]
    return Result(case, ok=not reasons, reason="; ".join(reasons), detail=detail)


def run_contract_case(case: ContractCase, base: Path) -> Result:
    try:
        problems = case.call(load_contract(base), base)
    except Exception as e:  # raising is the failure this kind of case exists to catch
        return Result(case, ok=False, reason=f"raised {e!r}",
                      detail=traceback.format_exc().splitlines()[-3:])
    if not isinstance(problems, list):
        return Result(case, ok=False, reason=f"returned {type(problems).__name__}, not a list")
    # Every problem is text. A contract regression that returns None among
    # them is a failed case, not a TypeError in the search below.
    strange = [p for p in problems if not isinstance(p, str)]
    if strange:
        return Result(case, ok=False, reason=f"returned {len(strange)} problem(s) that are not text",
                      detail=[repr(p) for p in strange[:3]])
    if case.contains is None:
        return Result(case, ok=not problems, reason="" if not problems else "expected no problems",
                      detail=problems[:3])
    hit = next((p for p in problems if case.contains in p), None)
    return Result(case, ok=hit is not None,
                  reason="" if hit else f"no problem contains {case.contains!r}",
                  detail=[hit] if hit else problems[:3])
