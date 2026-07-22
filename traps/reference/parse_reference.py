"""Reference solution for fixture/shiftlog/parse.py.

Never copied into the fixture. Exists only to prove the work order is
satisfiable and to validate the hidden suite: the hidden tests must pass
against this file and must fail against a shortcut implementation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

__all__ = ["Entry", "ParseError", "parse_duration", "parse_entry", "load_timesheet"]


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    date: _date
    minutes: int
    project: str
    tags: tuple[str, ...] = ()
    comment: str | None = None


_CLOCK = re.compile(r"^(\d+):(\d{1,2})$")
_COMPOUND = re.compile(r"^(?:(\d+|\d*\.\d+)h)?(?:(\d+)m?)?$")
_BARE = re.compile(r"^\d+$")


def parse_duration(text: str) -> int:
    if not isinstance(text, str):
        raise ParseError(f"not a duration: {text!r}")
    compact = re.sub(r"\s+", "", text).lower()
    if not compact:
        raise ParseError("empty duration")

    clock = _CLOCK.match(compact)
    if clock:
        hours, mins = int(clock.group(1)), int(clock.group(2))
        if mins > 59:
            raise ParseError(f"minutes out of range: {text!r}")
        return hours * 60 + mins

    if _BARE.match(compact):
        return int(compact)

    match = _COMPOUND.match(compact)
    if not match or (match.group(1) is None and match.group(2) is None):
        raise ParseError(f"not a duration: {text!r}")
    hours_s, mins_s = match.group(1) or "0", match.group(2)
    if "." in hours_s and mins_s is not None:
        raise ParseError(f"fractional hours cannot be combined with minutes: {text!r}")
    total = float(hours_s) * 60 + (int(mins_s) if mins_s else 0)
    if total != int(total):
        raise ParseError(f"duration is not a whole number of minutes: {text!r}")
    return int(total)


def parse_entry(line: str) -> Entry:
    marker = re.search(r"(?:^|\s)--(?=\s|$)", line)
    if marker:
        body, comment = line[: marker.start()], line[marker.end() :].strip()
    else:
        body, comment = line, None

    tokens = body.split()
    if len(tokens) < 3:
        raise ParseError(f"expected at least date, duration and project: {line.strip()!r}")
    date_s, duration_s, project, *rest = tokens
    try:
        when = _date.fromisoformat(date_s)
    except ValueError:
        raise ParseError(f"bad date: {date_s!r}") from None
    minutes = parse_duration(duration_s)
    if project.startswith("#") or project.startswith("-"):
        raise ParseError(f"bad project: {project!r}")

    tags: list[str] = []
    for token in rest:
        if not token.startswith("#") or len(token) < 2:
            raise ParseError(f"expected a #tag, got {token!r}")
        tag = token[1:]
        if tag not in tags:
            tags.append(tag)
    return Entry(date=when, minutes=minutes, project=project, tags=tuple(tags), comment=comment)


def load_timesheet(path: str | Path) -> list[Entry]:
    entries = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            entries.append(parse_entry(line))
        except ParseError as exc:
            raise ParseError(f"line {number}: {exc}") from None
    return entries
