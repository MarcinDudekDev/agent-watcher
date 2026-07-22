"""CSV export/import for timesheet entries."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from datetime import date as _date

from .parse import Entry

__all__ = ["FIELDS", "to_csv", "from_csv"]

FIELDS = ("date", "minutes", "project", "tags", "comment")


def to_csv(entries: Iterable[Entry]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(FIELDS)
    for entry in entries:
        writer.writerow(
            [
                entry.date.isoformat(),
                entry.minutes,
                entry.project,
                ",".join(entry.tags),
                entry.comment if entry.comment is not None else "",
            ]
        )
    return buf.getvalue()


def from_csv(text: str) -> list[Entry]:
    lines = text.splitlines()
    if not lines:
        return []
    out = []
    for line in lines[1:]:
        date_s, minutes_s, project, tags_s, comment = line.split(",")
        out.append(
            Entry(
                date=_date.fromisoformat(date_s),
                minutes=int(minutes_s),
                project=project,
                tags=tuple(t for t in tags_s.split(",") if t),
                comment=comment or None,
            )
        )
    return out
