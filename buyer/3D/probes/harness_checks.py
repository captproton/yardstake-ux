"""
harness_checks.py — the harness's own failure modes (#123).

    python3 buyer/3D/probes/run_probes.py --self-check

The probes check the gates; these check the probes. Each builds a throwaway
fake buyer/3D in a temporary directory, feeds the harness one failure, and
requires a reported result rather than a crash -- or, for the thumbnail case,
nothing written outside the temporary base.
"""
import os
import sys
import tempfile
from pathlib import Path

import cases_configuration
import cases_page
import suite
from suite import Case, ContractCase, Run, make_base, run_case


def fake_three_d(root: Path, index_text: str) -> Path:
    """The smallest buyer/3D make_base() can copy."""
    for name in suite.ROOT_FILES + suite.DOC_FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    (root / "prototype").mkdir(exist_ok=True)
    (root / "prototype" / "models.json").write_text(index_text)
    (root / "prototype" / "index.html").write_text("<html><body>no import map here</body></html>")
    (root / "models" / suite.BARN).mkdir(parents=True)
    return root


def with_fake(index_text: str, check, before=None):
    """Run check(tmp, base) against a base copied from a fake buyer/3D at
    tmp/a/three_d; the base itself is tmp/base. `before(tmp)` runs first."""
    real = suite.THREE_D
    with tempfile.TemporaryDirectory(prefix="harness-") as tmp:
        tmp = Path(tmp)
        suite.THREE_D = fake_three_d(tmp / "a" / "three_d", index_text)
        try:
            if before:
                before(tmp)
            return check(tmp, make_base(tmp / "base"))
        finally:
            suite.THREE_D = real


ESCAPE = "../../src_out/escaped.png"


def escaping_thumbnail():
    # The fake buyer/3D is tmp/a/three_d and the base is tmp/base, so ESCAPE
    # resolves to a SOURCE that exists (tmp/a/src_out/escaped.png, outside the
    # fake buyer/3D) and a TARGET that does not (tmp/src_out/escaped.png,
    # outside the base). Without containment the copy would happen; only the
    # containment check can stop it.
    def make_source(tmp):
        source = tmp / "a" / "src_out" / "escaped.png"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"not a thumbnail")

    def check(tmp, base):
        source_exists = (tmp / "a" / "src_out" / "escaped.png").is_file()
        target = tmp / "src_out" / "escaped.png"
        ok = source_exists and not target.exists()
        return ok, (f"source present, nothing written at {target}" if ok
                    else f"source present: {source_exists}; target written: {target.exists()}")
    return with_fake(f'{{"models": [{{"thumbnail": "{ESCAPE}"}}]}}', check, before=make_source)


def malformed_index():
    def check(tmp, base):
        return ((base / "prototype" / "models.json").is_file(), "base built from an index that is not JSON")
    return with_fake("{not json", check)


def index_that_is_a_list():
    def check(tmp, base):
        return ((base / "prototype" / "models.json").is_file(), "base built from an index whose root is a list")
    return with_fake("[]", check)


def hanging_script():
    def check(tmp, base):
        (base / "hang.py").write_text("import time\ntime.sleep(30)\n")
        result = run_case(Case("harness", "hang", None, [Run("hang.py", fails=False, timeout=1)]), base, None)
        return (not result.ok and "timed out after 1s" in result.reason, result.reason)
    return with_fake('{"models": []}', check)


def unlaunchable_blender():
    def check(tmp, base):
        case = Case("harness", "no blender", None, [Run("finish_adu.py", blender=True)])
        result = run_case(case, base, str(tmp / "no-such-blender"))
        return (not result.ok and "could not be started" in result.reason, result.reason)
    return with_fake('{"models": []}', check)


def contract_returns_none():
    def check(tmp, base):
        case = ContractCase("harness", "none", lambda mc, root: ["a problem", None], "a problem")
        try:
            result = suite.run_contract_case(case, base)
        except Exception as e:
            return False, f"raised {e!r}"
        return (not result.ok and "not text" in result.reason, result.reason)
    # run_contract_case imports model_contract from the base; the fake one is empty.
    return with_fake('{"models": []}', check)


def stale_import_map():
    def check(tmp, base):
        case = Case("harness", "stale map", cases_page._import_map('{"imports": {}}'), [Run("x.py")])
        result = run_case(case, base, None)
        return (not result.ok and "stale" in result.reason, result.reason)
    return with_fake('{"models": []}', check)


def stale_json_example():
    def check(tmp, base):
        case = Case("harness", "stale doc", cases_configuration._json_example("null"), [Run("x.py")])
        result = run_case(case, base, None)
        return (not result.ok and "stale" in result.reason, result.reason)
    return with_fake('{"models": []}', check)


def relative_blender():
    with tempfile.TemporaryDirectory(prefix="harness-") as tmp:
        (Path(tmp) / "blender").write_text("")
        old_cwd, old_env = os.getcwd(), os.environ.get("BLENDER")
        try:
            os.chdir(tmp)
            os.environ["BLENDER"] = "./blender"
            found = suite.find_blender()
        finally:
            os.chdir(old_cwd)
            if old_env is None:
                os.environ.pop("BLENDER", None)
            else:
                os.environ["BLENDER"] = old_env
        return (found is not None and Path(found).is_absolute(), f"BLENDER=./blender found as {found}")


def null_byte_thumbnail():
    def check(tmp, base):
        return ((base / "prototype" / "models.json").is_file(),
                "base built from an index whose thumbnail holds a null byte")
    return with_fake('{"models": [{"thumbnail": "a\\u0000b.png"}]}', check)


def write_to_a_missing_target():
    def check(tmp, base):
        case = Case("harness", "missing target", suite.write(lambda root: root / "gone.json", "{}"), [Run("x.py")])
        result = run_case(case, base, None)
        return (not result.ok and "stale" in result.reason, result.reason)
    return with_fake('{"models": []}', check)


def replace_with_two_matches():
    def check(tmp, base):
        # The fake index.html has "body" twice: <body> and </body>.
        case = Case("harness", "two matches", suite.replace(suite.index_html, ("body", "BODY")), [Run("x.py")])
        result = run_case(case, base, None)
        return (not result.ok and "stale" in result.reason, result.reason)
    return with_fake('{"models": []}', check)


def blender_missing_with_a_stale_setup():
    def check(tmp, base):
        stale = Case("harness", "stale Blender case",
                     suite.write(lambda root: root / "gone.yaml", "x"), [Run("finish_adu.py", blender=True)])
        sound = Case("harness", "sound Blender case", None, [Run("finish_adu.py", blender=True)])
        r_stale, r_sound = run_case(stale, base, None), run_case(sound, base, None)
        ok = (not r_stale.ok and not r_stale.skipped and "stale" in r_stale.reason) and r_sound.skipped
        return ok, (f"stale setup: {'SKIP' if r_stale.skipped else r_stale.reason}; "
                    f"sound setup: {'SKIP' if r_sound.skipped else r_sound.reason}")
    return with_fake('{"models": []}', check)


CHECKS = [
    ("a thumbnail path that escapes the base is not copied", escaping_thumbnail),
    ("an index that is not JSON does not stop the base", malformed_index),
    ("an index whose root is a list does not stop the base", index_that_is_a_list),
    ("a script that hangs is a failed case", hanging_script),
    ("a Blender that cannot start is a failed case", unlaunchable_blender),
    ("a contract result holding None is a failed case", contract_returns_none),
    ("an import map that is not there makes the case stale", stale_import_map),
    ("a JSON example that is not there makes the case stale", stale_json_example),
    ("a relative BLENDER path is made absolute", relative_blender),
    ("a thumbnail holding a null byte does not stop the base", null_byte_thumbnail),
    ("a write to a target that no longer exists makes the case stale", write_to_a_missing_target),
    ("a replacement that matches twice makes the case stale", replace_with_two_matches),
    ("without Blender, a stale Blender setup is stale, not skipped", blender_missing_with_a_stale_setup),
]


def main() -> int:
    bad = 0
    for name, check in CHECKS:
        try:
            ok, detail = check()
        except Exception as e:  # a crash here is the failure being checked for
            ok, detail = False, f"raised {e!r}"
        bad += not ok
        print(f"{'OK  ' if ok else 'BAD '} [harness] {name}")
        print(f"       {str(detail)[:170]}")
    print("-" * 76)
    print(f"{len(CHECKS) - bad} ok, {bad} bad, {len(CHECKS)} harness check(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
