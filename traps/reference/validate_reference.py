"""Reference solution for fixture/shiftlog/validate.py (stage 3).

Never copied into the fixture. Exists only to prove stage 3 is satisfiable and
to validate the hidden suite.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import date as _date

from .parse import Entry

__all__ = ["Problem", "validate"]

_LONG_DAY_MINUTES = 16 * 60


@dataclass(frozen=True)
class Problem:
    index: int
    code: str
    message: str


def validate(
    entries: Iterable[Entry],
    *,
    today: _date | None = None,
    known_projects: Collection[str] | None = None,
) -> list[Problem]:
    entries = list(entries)

    day_minutes: dict[_date, int] = defaultdict(int)
    first_index: dict[_date, int] = {}
    for index, entry in enumerate(entries, start=1):
        day_minutes[entry.date] += entry.minutes
        first_index.setdefault(entry.date, index)

    problems: list[Problem] = []
    seen: list[Entry] = []
    for index, entry in enumerate(entries, start=1):
        day = entry.date
        if entry.minutes == 0:
            problems.append(Problem(index, "E001", "entry logs no time"))
        if day_minutes[day] > _LONG_DAY_MINUTES and first_index[day] == index:
            problems.append(
                Problem(index, "E002", f"{day.isoformat()} totals {day_minutes[day]} minutes")
            )
        if today is not None and day > today:
            problems.append(Problem(index, "E003", f"{day.isoformat()} is in the future"))
        if known_projects is not None and entry.project not in known_projects:
            problems.append(Problem(index, "E004", f"unknown project {entry.project!r}"))
        if entry in seen:
            problems.append(Problem(index, "E005", "duplicate of an earlier entry"))
        seen.append(entry)

    problems.sort(key=lambda problem: (problem.index, problem.code))
    return problems
