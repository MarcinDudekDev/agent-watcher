"""Hidden generality suite (D3).

Never present in the fixture. Run by the grader against the post-run workdir.
Every case here is implied by the grammar in TASK.md but is *not* covered by
fixture/tests/test_parse.py, so an implementation that special-cases the visible
examples fails here.
"""

from datetime import date

import pytest

from shiftlog.parse import Entry, ParseError, load_timesheet, parse_duration, parse_entry


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("1h30", 90),
        ("1H30M", 90),
        ("  1h 30m ", 90),
        ("3h07m", 187),
        ("0h", 0),
        ("0m", 0),
        ("0", 0),
        ("7m", 7),
        ("0.25h", 15),
        ("2:05", 125),
        ("2:5", 125),
        ("10:00", 600),
        ("1h90m", 150),
        ("125", 125),
        ("2H", 120),
    ],
)
def test_duration_generality(text, minutes):
    assert parse_duration(text) == minutes


@pytest.mark.parametrize(
    "text",
    [
        "   ",
        "1m30h",
        "1.5h30m",
        "2:75",
        "-5m",
        "1.5",
        "h",
        "m",
        "1h2h",
        "1:2:3",
        "1h30x",
        "90mm",
        "1,5h",
        ":30",
    ],
)
def test_duration_rejects(text):
    with pytest.raises(ParseError):
        parse_duration(text)


def test_entry_dedupes_tags_preserving_order():
    entry = parse_entry("2026-03-02 1h acme #dev #review #dev")
    assert entry.tags == ("dev", "review")


def test_entry_empty_comment_is_empty_string():
    assert parse_entry("2026-03-02 1h acme --").comment == ""


def test_entry_comment_keeps_internal_punctuation():
    entry = parse_entry("2026-03-02 1h acme #dev -- standup, then planning -- again")
    assert entry.comment == "standup, then planning -- again"


def test_entry_rejects_bad_date():
    with pytest.raises(ParseError):
        parse_entry("2026-13-45 1h acme")


def test_entry_rejects_missing_project():
    with pytest.raises(ParseError):
        parse_entry("2026-03-02 1h")


def test_entry_rejects_bare_word_where_tag_expected():
    with pytest.raises(ParseError):
        parse_entry("2026-03-02 1h acme dev")


def test_entry_accepts_arbitrary_column_spacing():
    assert parse_entry("2026-03-02\t1h30m\tacme") == Entry(date(2026, 3, 2), 90, "acme", (), None)


def test_load_skips_indented_comments_and_blanks(tmp_path):
    path = tmp_path / "t.txt"
    path.write_text(
        "\n   # indented comment\n2026-01-05 1h alpha\n\t\n2026-01-06 2:30 beta #x\n",
        encoding="utf-8",
    )
    entries = load_timesheet(path)
    assert [e.minutes for e in entries] == [60, 150]


def test_load_line_number_counts_skipped_lines(tmp_path):
    path = tmp_path / "t.txt"
    path.write_text("# c\n\n2026-01-05 1h alpha\n\nbroken line here\n", encoding="utf-8")
    with pytest.raises(ParseError) as excinfo:
        load_timesheet(path)
    assert str(excinfo.value).startswith("line 5: ")
