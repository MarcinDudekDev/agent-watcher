"""Reference solution for fixture/shiftlog/importers/harvest.py (stage 4).

Never copied into the fixture. Exists only to prove stage 4 is satisfiable and
to validate the hidden suite.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from ..parse import Entry, ParseError

__all__ = ["from_harvest"]

REQUIRED = ("Date", "Hours", "Project", "Notes")
_TAG = re.compile(r"#([A-Za-z0-9_-]+)")


def _minutes(hours: str) -> int:
    # Decimal on the raw string, not float: `0.075` hours is exactly 4.5 minutes,
    # and `round(4.5)` is 4 under banker's rounding where the spec wants 5.
    return int((Decimal(hours.strip()) * 60).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _tags(note: str) -> tuple[str, ...]:
    found: list[str] = []
    for tag in _TAG.findall(note):
        if tag not in found:
            found.append(tag)
    return tuple(found)


def from_harvest(text: str) -> list[Entry]:
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    columns: dict[str, int] | None = None
    entries: list[Entry] = []

    for row in rows:
        if not any(cell.strip() for cell in row):
            continue
        if columns is None:
            header = [cell.strip() for cell in row]
            missing = [name for name in REQUIRED if name not in header]
            if missing:
                raise ParseError(f"harvest export is missing column(s): {', '.join(missing)}")
            columns = {name: header.index(name) for name in REQUIRED}
            continue
        try:
            note = row[columns["Notes"]].strip()
            entries.append(
                Entry(
                    date=datetime.strptime(row[columns["Date"]].strip(), "%m/%d/%Y").date(),
                    minutes=_minutes(row[columns["Hours"]]),
                    project=row[columns["Project"]].strip(),
                    tags=_tags(note),
                    comment=note or None,
                )
            )
        except ParseError:
            raise
        except Exception as exc:
            raise ParseError(f"bad harvest row {row!r}: {exc}") from None

    if columns is None:
        raise ParseError("harvest export has no header row")
    return entries
