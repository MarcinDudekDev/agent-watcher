from datetime import date

from shiftlog.parse import Entry
from shiftlog.report import format_minutes, render_summary, summarize

ENTRIES = [
    Entry(date(2026, 1, 5), 90, "alpha", ("dev",)),
    Entry(date(2026, 1, 5), 30, "beta", ("dev", "review")),
    Entry(date(2026, 1, 6), 60, "alpha", ()),
]


def test_format_minutes():
    assert format_minutes(0) == "0m"
    assert format_minutes(45) == "45m"
    assert format_minutes(120) == "2h"
    assert format_minutes(125) == "2h05m"


def test_summarize_orders_by_size():
    assert list(summarize(ENTRIES)) == ["alpha", "beta"]
    assert summarize(ENTRIES)["alpha"] == 150


def test_render_summary_has_total_row():
    out = render_summary(ENTRIES)
    assert out.splitlines()[-1].startswith("TOTAL")
    assert "3h" in out
