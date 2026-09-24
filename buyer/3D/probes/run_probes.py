"""
run_probes.py — run every probe against a copy of buyer/3D (#121).

    python3 buyer/3D/probes/run_probes.py            every case
    python3 buyer/3D/probes/run_probes.py --only rail  cases whose group or name contains "rail"
    python3 buyer/3D/probes/run_probes.py --list     list the cases without running them
    python3 buyer/3D/probes/run_probes.py -v         show the matching output line for passing cases too
    python3 buyer/3D/probes/run_probes.py --self-check  check the harness itself (harness_checks.py)

Exits 1 if any case does not behave as expected. The Blender case is skipped,
with a message, when Blender is not found (set BLENDER to point at it).

RUN THIS BEFORE MERGING a change to verify_index.py, verify_prototype.py,
build_index.py, adu_kit/, finish_adu.py, prototype/app.js or the
fixtures. See suite.py for what a probe is and why it breaks a copy.
"""
import argparse
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cases_blender  # noqa: E402
import cases_commerce  # noqa: E402
import cases_configuration  # noqa: E402
import cases_export  # noqa: E402
import cases_frame  # noqa: E402
import cases_fixtures  # noqa: E402
import cases_front  # noqa: E402
import cases_index  # noqa: E402
import cases_page  # noqa: E402
import cases_rail  # noqa: E402
import cases_roof  # noqa: E402
import cases_views  # noqa: E402
from suite import find_blender, make_base, run_case  # noqa: E402

# In the order the checks were built, one round per PR.
MODULES = (cases_index, cases_page, cases_views, cases_rail, cases_configuration, cases_fixtures,
           cases_commerce, cases_roof, cases_frame, cases_front, cases_blender,
           cases_export)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--only", help="run cases whose group or name contains this text")
    parser.add_argument("--list", action="store_true", help="list the cases and exit")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--self-check", action="store_true",
                        help="check the harness's own failure modes instead of running the cases")
    args = parser.parse_args()

    if args.self_check:
        import harness_checks
        return harness_checks.main()

    cases = [c for m in MODULES for c in m.CASES]
    if args.only:
        needle = args.only.lower()
        cases = [c for c in cases if needle in c.group.lower() or needle in c.name.lower()]
    if args.list:
        for c in cases:
            print(f"[{c.group}] {c.name}")
        print(f"{len(cases)} case(s)")
        return 0
    if not cases:
        print("no cases match")
        return 1

    blender = find_blender()
    start = time.monotonic()
    counts = {"ok": 0, "bad": 0, "skipped": 0}
    with tempfile.TemporaryDirectory(prefix="probe-base-") as tmp:
        base = make_base(Path(tmp) / "base")
        blender_base = None
        for case in cases:
            use = base
            if case.needs_blender:
                # BUILT EVEN WHEN BLENDER IS ABSENT. run_case deliberately runs
                # a case's setup BEFORE deciding to skip, so that a case gone
                # stale still says so on a machine with no Blender -- and a
                # setup that edits a model's own scripts needs those scripts
                # present to fail honestly. Gating this on `blender` meant CI,
                # which has none, ran those setups against a base holding only
                # spec.yaml and reported two live cases as stale. Found by CI.
                blender_base = blender_base or make_base(Path(tmp) / "blender-base", with_blender_model=True)
                use = blender_base
            result = run_case(case, use, blender)
            if result.skipped:
                counts["skipped"] += 1
                print(f"SKIP [{case.group}] {case.name}: {result.reason}")
                continue
            counts["ok" if result.ok else "bad"] += 1
            print(f"{'OK  ' if result.ok else 'BAD '} [{case.group}] {case.name}"
                  + ("" if result.ok else f": {result.reason}"))
            if not result.ok or args.verbose:
                for line in result.detail:
                    print(f"       {str(line)[:170]}")

    print("-" * 76)
    print(f"{counts['ok']} ok, {counts['bad']} bad, {counts['skipped']} skipped, "
          f"{len(cases)} case(s) in {time.monotonic() - start:.0f}s")
    return 1 if counts["bad"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
