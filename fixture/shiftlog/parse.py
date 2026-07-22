"""Reading timesheet files into `Entry` records.

The public surface is `parse_duration`, `parse_entry`, `load_timesheet`,
`Entry` and `ParseError`; the rest of the package depends only on those.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

__all__ = ["Entry", "ParseError", "parse_duration", "parse_entry", "load_timesheet"]


class ParseError(ValueError):
    """Raised when a timesheet line (or part of one) cannot be understood."""


@dataclass(frozen=True)
class Entry:
    date: _date
    minutes: int
    project: str
    tags: tuple[str, ...] = ()
    comment: str | None = None


def parse_duration(text: str) -> int:
    """Return the number of minutes described by `text`.

    See the duration grammar in the work order.
    """
    raise NotImplementedError


def parse_entry(line: str) -> Entry:
    """Parse a single timesheet line into an `Entry`."""
    raise NotImplementedError


def load_timesheet(path: str | Path) -> list[Entry]:
    """Parse every entry line of the timesheet at `path`."""
    raise NotImplementedError
