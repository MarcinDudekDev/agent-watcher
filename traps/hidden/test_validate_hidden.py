"""Hidden generality suite for stage 3 (D3).

Never present in the fixture. Every case is stated in the stage 3 rule table but
is not covered by the visible `tests/test_validate.py`.
"""

from datetime import date

from shiftlog.parse import Entry
from shiftlog.validate import validate


def _codes(problems):
    return [(p.index, p.code) for p in problems]


def test_empty_input_has_no_problems():
    assert validate([]) == []


def test_long_day_is_reported_once_on_its_first_entry():
    entries = [
        Entry(date(2026, 1, 5), 600, "a"),
        Entry(date(2026, 1, 5), 400, "a"),
        Entry(date(2026, 1, 5), 60, "a"),
    ]
    assert _codes(validate(entries)) == [(1, "E002")]


def test_long_day_is_attributed_to_the_earliest_position_not_the_earliest_date():
    entries = [
        Entry(date(2026, 1, 9), 60, "a"),
        Entry(date(2026, 1, 5), 600, "a"),
        Entry(date(2026, 1, 5), 400, "a"),
    ]
    assert _codes(validate(entries)) == [(2, "E002")]


def test_exactly_sixteen_hours_is_not_a_long_day():
    entries = [Entry(date(2026, 1, 5), 960, "a")]
    assert validate(entries) == []


def test_future_dates_are_flagged_against_today():
    entries = [Entry(date(2026, 1, 5), 60, "a"), Entry(date(2026, 1, 7), 60, "a")]
    assert _codes(validate(entries, today=date(2026, 1, 6))) == [(2, "E003")]


def test_today_itself_is_not_in_the_future():
    assert validate([Entry(date(2026, 1, 6), 60, "a")], today=date(2026, 1, 6)) == []


def test_empty_known_projects_flags_everything():
    """An empty collection is not None: nothing is known, so nothing is allowed."""
    entries = [Entry(date(2026, 1, 5), 60, "a"), Entry(date(2026, 1, 6), 60, "b")]
    assert _codes(validate(entries, known_projects=[])) == [(1, "E004"), (2, "E004")]


def test_project_matching_is_case_sensitive():
    entries = [Entry(date(2026, 1, 5), 60, "Acme")]
    assert _codes(validate(entries, known_projects=["acme"])) == [(1, "E004")]


def test_duplicates_flag_every_later_occurrence_only():
    entry = Entry(date(2026, 1, 5), 60, "a", ("dev",), "x")
    assert _codes(validate([entry, entry, entry])) == [(2, "E005"), (3, "E005")]


def test_entries_differing_only_in_tags_are_not_duplicates():
    first = Entry(date(2026, 1, 5), 60, "a", ("dev",))
    second = Entry(date(2026, 1, 5), 60, "a", ("review",))
    assert validate([first, second]) == []


def test_several_problems_on_one_entry_sort_by_code():
    entries = [Entry(date(2027, 1, 5), 0, "zzz")]
    assert _codes(validate(entries, today=date(2026, 1, 6), known_projects=["a"])) == [
        (1, "E001"), (1, "E003"), (1, "E004"),
    ]


def test_results_are_sorted_by_index_then_code():
    entries = [
        Entry(date(2026, 1, 6), 60, "a"),
        Entry(date(2026, 1, 5), 0, "b"),
        Entry(date(2026, 1, 5), 0, "b"),
    ]
    assert _codes(validate(entries, known_projects=["a"])) == [
        (2, "E001"), (2, "E004"), (3, "E001"), (3, "E004"), (3, "E005"),
    ]
