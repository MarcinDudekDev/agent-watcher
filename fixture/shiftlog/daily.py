"""Per-day view of a timesheet.

`daily_totals` and `render_by_day` are the public surface; `cli` is the only
caller.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date as _date

from .parse import Entry

__all__ = ["daily_totals", "render_by_day"]


def daily_totals(entries: Iterable[Entry]) -> dict[_date, int]:
    """Minutes per calendar date across the whole span of `entries`.

    See stage 2 of the work order.
    """
    raise NotImplementedError


def render_by_day(entries: Iterable[Entry]) -> str:
    """The printable per-day breakdown."""
    raise NotImplementedError
