"""Hidden generality suite for stage 2 (D3).

Never present in the fixture. Every case is implied by the stage 2 text but not
covered by the visible `tests/test_daily.py`, so an implementation shaped around
the visible examples fails here.
"""

from datetime import date

from shiftlog.daily import daily_totals, render_by_day
from shiftlog.parse import Entry


def test_gap_days_are_filled_with_zero():
    entries = [Entry(date(2026, 1, 5), 60, "a"), Entry(date(2026, 1, 8), 30, "a")]
    totals = daily_totals(entries)
    assert list(totals) == [date(2026, 1, d) for d in (5, 6, 7, 8)]
    assert totals[date(2026, 1, 6)] == 0
    assert totals[date(2026, 1, 7)] == 0


def test_span_crosses_a_month_boundary():
    entries = [Entry(date(2026, 1, 30), 60, "a"), Entry(date(2026, 2, 2), 60, "a")]
    assert list(daily_totals(entries)) == [
        date(2026, 1, 30), date(2026, 1, 31), date(2026, 2, 1), date(2026, 2, 2),
    ]


def test_keys_are_in_ascending_order_regardless_of_input_order():
    entries = [Entry(date(2026, 1, 9), 60, "a"), Entry(date(2026, 1, 7), 60, "a")]
    assert list(daily_totals(entries)) == [date(2026, 1, 7), date(2026, 1, 8), date(2026, 1, 9)]


def test_single_entry_gives_a_single_day():
    assert daily_totals([Entry(date(2026, 1, 5), 60, "a")]) == {date(2026, 1, 5): 60}


def test_blank_day_renders_as_a_dash():
    entries = [Entry(date(2026, 1, 5), 60, "a"), Entry(date(2026, 1, 7), 60, "a")]
    middle = render_by_day(entries).splitlines()[1]
    assert middle.startswith("2026-01-06")
    assert middle.split()[-1] == "-"


def test_a_day_that_sums_to_zero_is_not_a_blank_day():
    """A logged-but-empty day is `0m`; only a day with no entry at all is `-`."""
    entries = [
        Entry(date(2026, 1, 5), 60, "a"),
        Entry(date(2026, 1, 6), 0, "a"),
        Entry(date(2026, 1, 7), 60, "a"),
    ]
    middle = render_by_day(entries).splitlines()[1]
    assert middle.startswith("2026-01-06")
    assert middle.split()[-1] == "0m"


def test_total_row_sums_the_whole_span():
    entries = [Entry(date(2026, 1, 5), 90, "a"), Entry(date(2026, 1, 8), 30, "a")]
    lines = render_by_day(entries).splitlines()
    assert lines[-1].startswith("TOTAL")
    assert lines[-1].split()[-1] == "2h"
    assert set(lines[-2]) == {"-"}


def test_row_shape_is_date_two_spaces_then_a_seven_wide_column():
    line = render_by_day([Entry(date(2026, 1, 5), 90, "a")]).splitlines()[0]
    assert line == "2026-01-05  " + "1h30m".rjust(7)
