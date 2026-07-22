"""Hidden generality suite for stage 4 (D3).

Never present in the fixture. Every case is stated in the stage 4 text but is not
covered by the visible `tests/test_harvest.py`, whose assertions all happen to be
satisfied by a float-and-`round()` implementation reading fixed column positions.
"""

from datetime import date

import pytest

from shiftlog.importers.harvest import from_harvest
from shiftlog.parse import ParseError

HEADER = "Date,Hours,Project,Notes\n"


def test_half_a_minute_rounds_away_from_zero():
    """0.075h is exactly 4.5 minutes. `round(4.5)` is 4; the spec says 5."""
    entries = from_harvest(HEADER + "03/09/2026,0.075,acme,\n")
    assert entries[0].minutes == 5


def test_a_second_half_minute_case():
    """0.175h is exactly 10.5 minutes. `round(10.5)` is 10; the spec says 11."""
    assert from_harvest(HEADER + "03/09/2026,0.175,acme,\n")[0].minutes == 11


def test_ordinary_rounding_still_goes_to_the_nearest_minute():
    assert from_harvest(HEADER + "03/09/2026,1.33,acme,\n")[0].minutes == 80
    assert from_harvest(HEADER + "03/09/2026,0.01,acme,\n")[0].minutes == 1
    assert from_harvest(HEADER + "03/09/2026,0,acme,\n")[0].minutes == 0


def test_columns_are_found_by_name_not_position():
    text = "Notes,Project,Hours,Date\nplanning,acme,1.5,03/09/2026\n"
    entry = from_harvest(text)[0]
    assert (entry.date, entry.minutes, entry.project, entry.comment) == (
        date(2026, 3, 9), 90, "acme", "planning",
    )


def test_unknown_columns_are_ignored():
    text = "Client,Date,Hours,Task,Project,Notes,Billable?\nA,03/09/2026,1,t,acme,n,Yes\n"
    assert from_harvest(text)[0].project == "acme"


def test_missing_required_column_raises():
    with pytest.raises(ParseError):
        from_harvest("Date,Hours,Project\n03/09/2026,1,acme\n")


def test_no_header_at_all_raises():
    with pytest.raises(ParseError):
        from_harvest("")


def test_bad_date_raises_parse_error():
    with pytest.raises(ParseError):
        from_harvest(HEADER + "2026-03-09,1,acme,\n")


def test_bom_is_stripped_from_the_first_column_name():
    assert from_harvest("﻿" + HEADER + "03/09/2026,1,acme,\n")[0].project == "acme"


def test_blank_rows_are_skipped():
    text = HEADER + "\n03/09/2026,1,acme,\n\n03/10/2026,1,acme,\n"
    assert len(from_harvest(text)) == 2


def test_tags_are_extracted_deduplicated_and_left_in_the_comment():
    entry = from_harvest(HEADER + '03/09/2026,1,acme,"#dev review #ops then #dev again"\n')[0]
    assert entry.tags == ("dev", "ops")
    assert entry.comment == "#dev review #ops then #dev again"


def test_tag_characters_stop_at_punctuation():
    entry = from_harvest(HEADER + '03/09/2026,1,acme,"see #ticket-42, and #b_2."\n')[0]
    assert entry.tags == ("ticket-42", "b_2")


def test_whitespace_only_note_becomes_none():
    entry = from_harvest(HEADER + '03/09/2026,1,acme,"   "\n')[0]
    assert entry.comment is None
    assert entry.tags == ()


def test_entries_keep_file_order():
    text = HEADER + "03/11/2026,1,c,\n03/09/2026,1,a,\n03/10/2026,1,b,\n"
    assert [e.project for e in from_harvest(text)] == ["c", "a", "b"]
