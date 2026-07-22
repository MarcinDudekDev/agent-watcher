"""Reference solution for fixture/shiftlog/daily.py (stage 2).

Never copied into the fixture. Exists only to prove stage 2 is satisfiable and
to validate the hidden suite.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date as _date
from datetime import timedelta

from .parse import Entry
from .report import format_minutes

__all__ = ["daily_totals", "render_by_day"]

_DATE_COL = 10
_MINS_COL = 7


def daily_totals(entries: Iterable[Entry]) -> dict[_date, int]:
    entries = list(entries)
    if not entries:
        return {}
    first, last = min(e.date for e in entries), max(e.date for e in entries)
    span = (last - first).days
    totals = {first + timedelta(days=offset): 0 for offset in range(span + 1)}
    for entry in entries:
        totals[entry.date] += entry.minutes
    return totals


def render_by_day(entries: Iterable[Entry]) -> str:
    entries = list(entries)
    if not entries:
        return "(nothing logged)"
    totals = daily_totals(entries)
    # A date with no entry at all is `-`; a date whose entries happen to sum to
    # zero is a real 0m, so the blank days come from the entry dates, not the sum.
    logged = {entry.date for entry in entries}
    lines = [
        f"{day.isoformat():<{_DATE_COL}}  "
        f"{(format_minutes(mins) if day in logged else '-'):>{_MINS_COL}}"
        for day, mins in totals.items()
    ]
    lines.append("-" * (_DATE_COL + 2 + _MINS_COL))
    lines.append(f"{'TOTAL':<{_DATE_COL}}  {format_minutes(sum(totals.values())):>{_MINS_COL}}")
    return "\n".join(lines)
