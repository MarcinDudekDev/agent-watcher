from datetime import date

from shiftlog.parse import Entry
from shiftlog.validate import validate

CLEAN = [
    Entry(date(2026, 1, 5), 90, "alpha", ("dev",)),
    Entry(date(2026, 1, 6), 60, "beta", ()),
]


def test_clean_timesheet_has_no_problems():
    assert validate(CLEAN) == []


def test_zero_minutes_is_flagged():
    problems = validate([Entry(date(2026, 1, 5), 0, "alpha")])
    assert [(p.index, p.code) for p in problems] == [(1, "E001")]


def test_unknown_project_is_flagged():
    problems = validate(CLEAN, known_projects=["alpha"])
    assert [(p.index, p.code) for p in problems] == [(2, "E004")]


def test_future_dates_ignored_without_today():
    assert validate([Entry(date(2099, 1, 1), 60, "alpha")]) == []
