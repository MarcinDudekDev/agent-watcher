"""Turning a list of entries into printable summaries."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .parse import Entry

__all__ = ["format_minutes", "summarize", "render_summary", "render_by_tag"]


def format_minutes(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h{mins:02d}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def summarize(entries: Iterable[Entry]) -> dict[str, int]:
    """Total minutes per project, highest first."""
    totals: dict[str, int] = defaultdict(int)
    for entry in entries:
        totals[entry.project] += entry.minutes
    return dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))


def render_summary(entries: Iterable[Entry]) -> str:
    entries = list(entries)
    totals = summarize(entries)
    grand = sum(totals.values())
    width = max((len(p) for p in totals), default=7)
    lines = [f"{project.ljust(width)}  {format_minutes(mins):>7}" for project, mins in totals.items()]
    lines.append("-" * (width + 9))
    lines.append(f"{'TOTAL'.ljust(width)}  {format_minutes(grand):>7}")
    return "\n".join(lines)


def render_by_tag(entries: Iterable[Entry]) -> str:
    entries = list(entries)
    totals: dict[str, int] = defaultdict(int)
    for entry in entries:
        for tag in entry.tags or ("untagged",):
            totals[tag] += entry.minutes
    grand = sum(e.minutes for e in entries)
    if not grand:
        return "(nothing logged)"
    width = max(len(t) for t in totals)
    lines = []
    for tag, mins in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])):
        share = mins * 100 // grand
        lines.append(f"{tag.ljust(width)}  {format_minutes(mins):>7}  {share:>3d}%")
    return "\n".join(lines)
