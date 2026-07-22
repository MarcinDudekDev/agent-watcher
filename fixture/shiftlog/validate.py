"""Timesheet sanity checks.

`Problem` is the record type the linter emits; `validate` is the only entry
point. See stage 3 of the work order for the rule table.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import date as _date

from .parse import Entry

__all__ = ["Problem", "validate"]


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
    """Every rule violation in `entries`, sorted by index then code."""
    raise NotImplementedError
