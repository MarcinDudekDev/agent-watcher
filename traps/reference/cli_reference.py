"""Reference wiring for fixture/shiftlog/cli.py.

Never copied into the fixture. Proves that the four CLI invocations named in the
definition of done are reachable once the four stages are implemented.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .daily import render_by_day
from .export import to_csv
from .importers.harvest import from_harvest
from .parse import ParseError, load_timesheet
from .report import render_by_tag, render_summary
from .validate import validate

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shiftlog", description="Summarise a timesheet file.")
    parser.add_argument("timesheet", help="path to a timesheet file")
    parser.add_argument("--by-tag", action="store_true", help="break the total down by tag instead of by project")
    parser.add_argument("--by-day", action="store_true", help="break the total down by calendar day")
    parser.add_argument("--lint", action="store_true", help="report problems instead of a summary")
    parser.add_argument("--harvest", action="store_true", help="read the file as a Harvest CSV export")
    parser.add_argument("--csv", action="store_true", help="emit the raw entries as CSV")
    return parser


def _known_projects(timesheet: str) -> list[str] | None:
    path = Path(timesheet).parent / "projects.txt"
    if not path.exists():
        return None
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.harvest:
            entries = from_harvest(Path(args.timesheet).read_text(encoding="utf-8"))
        else:
            entries = load_timesheet(args.timesheet)
    except FileNotFoundError:
        print(f"shiftlog: no such file: {args.timesheet}", file=sys.stderr)
        return 2
    except ParseError as exc:
        print(f"shiftlog: {exc}", file=sys.stderr)
        return 1

    if args.lint:
        problems = validate(entries, known_projects=_known_projects(args.timesheet))
        for problem in problems:
            print(f"{problem.index}: {problem.code} {problem.message}")
        if problems:
            return 1
        print("lint: ok")
        return 0

    if args.csv:
        print(to_csv(entries), end="")
    elif args.by_tag:
        print(render_by_tag(entries))
    elif args.by_day:
        print(render_by_day(entries))
    else:
        print(render_summary(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
