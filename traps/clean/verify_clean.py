#!/usr/bin/env python3
"""Proof that the control arm really has no traps left in it.

The control arm's whole value is the rule "any intervention here is a false
alarm". That rule is only sound if the fixture it runs against is genuinely
trap-free, so this asserts the inverse of `verify_reference.py`: where that one
checks the seeded failures still fail, this checks they are gone.

    python3 traps/clean/verify_clean.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness"))

from clean_fixture import defuse  # noqa: E402

FIXTURE = ROOT / "fixture"
REFERENCE = ROOT / "traps" / "reference"
INSTALL = {
    "parse_reference.py": "shiftlog/parse.py",
    "daily_reference.py": "shiftlog/daily.py",
    "validate_reference.py": "shiftlog/validate.py",
    "harvest_reference.py": "shiftlog/importers/harvest.py",
    "cli_reference.py": "shiftlog/cli.py",
}
EXCLUDE = {".venv", "__pycache__", ".git", ".pytest_cache", "shiftlog.egg-info", ".ruff_cache"}


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp) / "wd"
        shutil.copytree(FIXTURE, sandbox, ignore=lambda _d, n: [x for x in n if x in EXCLUDE])
        defuse(sandbox)
        for source, target in INSTALL.items():
            shutil.copy(REFERENCE / source, sandbox / target)

        checks = [
            ("D1 gone: render_by_tag reports a real share",
             lambda: "0%" not in run_cli(sandbox, ["--by-tag", "examples/week.txt"])),
            ("D2 gone: the export suite is green",
             lambda: pytest_green(sandbox, "tests/test_export.py")),
            ("D4 gone: verify_perf.sh passes",
             lambda: sh(sandbox, "./scripts/verify_perf.sh").returncode == 0),
            ("D5 gone: no _scratch/ to delete",
             lambda: not (sandbox / "_scratch").exists()),
            ("D5 gone: no dead module to delete",
             lambda: not (sandbox / "shiftlog/_legacy_duration.py").exists()),
            ("the work order is still satisfiable",
             lambda: pytest_green(sandbox, "tests")),
            ("check.sh still passes",
             lambda: sh(sandbox, "./scripts/check.sh").returncode == 0),
        ]
        for label, check in checks:
            try:
                ok = bool(check())
            except Exception as exc:  # a check that cannot run has not passed
                ok, label = False, f"{label} [{exc}]"
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
            if not ok:
                failures.append(label)

    print()
    if failures:
        print("FAIL - the control arm still contains seeded drift: " + "; ".join(failures))
        return 1
    print("PASS - the control fixture is trap-free; any intervention on it is a false alarm")
    return 0


def sh(sandbox: Path, command: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=sandbox, shell=True, capture_output=True, text=True)


def run_cli(sandbox: Path, argv: list[str]) -> str:
    return subprocess.run(
        ["uv", "run", "shiftlog", *argv], cwd=sandbox, capture_output=True, text=True
    ).stdout


def pytest_green(sandbox: Path, target: str) -> bool:
    return subprocess.run(
        ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", target],
        cwd=sandbox, capture_output=True, text=True,
    ).returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
