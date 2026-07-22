"""Command line entry point for shiftlog."""

from __future__ import annotations

import argparse
import sys

from .export import to_csv
from .parse import ParseError, load_timesheet
from .report import render_by_tag, render_summary

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shiftlog", description="Summarise a timesheet file.")
    parser.add_argument("timesheet", help="path to a timesheet file")
    parser.add_argument("--by-tag", action="store_true", help="break the total down by tag instead of by project")
    parser.add_argument("--csv", action="store_true", help="emit the raw entries as CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        entries = load_timesheet(args.timesheet)
    except FileNotFoundError:
        print(f"shiftlog: no such file: {args.timesheet}", file=sys.stderr)
        return 2
    except ParseError as exc:
        print(f"shiftlog: {exc}", file=sys.stderr)
        return 1

    if args.csv:
        print(to_csv(entries), end="")
    elif args.by_tag:
        print(render_by_tag(entries))
    else:
        print(render_summary(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
