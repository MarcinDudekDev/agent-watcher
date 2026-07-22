from datetime import date

from shiftlog.daily import daily_totals, render_by_day
from shiftlog.parse import Entry

ENTRIES = [
    Entry(date(2026, 1, 5), 90, "alpha", ("dev",)),
    Entry(date(2026, 1, 5), 30, "beta", ("dev", "review")),
    Entry(date(2026, 1, 6), 60, "alpha", ()),
]


def test_daily_totals_sums_each_day():
    totals = daily_totals(ENTRIES)
    assert totals[date(2026, 1, 5)] == 120
    assert totals[date(2026, 1, 6)] == 60


def test_daily_totals_of_nothing_is_empty():
    assert daily_totals([]) == {}


def test_render_has_a_total_row():
    lines = render_by_day(ENTRIES).splitlines()
    assert lines[0].startswith("2026-01-05")
    assert lines[-1].startswith("TOTAL")
    assert "3h" in lines[-1]


def test_render_of_nothing():
    assert render_by_day([]) == "(nothing logged)"
