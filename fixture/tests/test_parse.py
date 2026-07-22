from datetime import date

import pytest

from shiftlog.parse import Entry, ParseError, load_timesheet, parse_duration, parse_entry


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("1h30m", 90),
        ("1h30", 90),
        ("90m", 90),
        ("2h", 120),
        ("1.5h", 90),
        ("0:45", 45),
        ("90", 90),
    ],
)
def test_parse_duration(text, minutes):
    assert parse_duration(text) == minutes


@pytest.mark.parametrize("text", ["", "abc"])
def test_parse_duration_rejects(text):
    with pytest.raises(ParseError):
        parse_duration(text)


def test_parse_entry_full():
    entry = parse_entry("2026-03-02  1h30m  acme  #dev #review  -- parser rewrite")
    assert entry == Entry(
        date=date(2026, 3, 2),
        minutes=90,
        project="acme",
        tags=("dev", "review"),
        comment="parser rewrite",
    )


def test_parse_entry_minimal():
    entry = parse_entry("2026-03-02 45m acme")
    assert entry.project == "acme"
    assert entry.minutes == 45
    assert entry.tags == ()
    assert entry.comment is None


def test_load_timesheet(tmp_path):
    path = tmp_path / "t.txt"
    path.write_text("# header\n\n2026-01-05 1h alpha\n2026-01-06 2h beta #x\n", encoding="utf-8")
    entries = load_timesheet(path)
    assert [e.project for e in entries] == ["alpha", "beta"]


def test_load_timesheet_reports_line_number(tmp_path):
    path = tmp_path / "t.txt"
    path.write_text("2026-01-05 1h alpha\nnope\n", encoding="utf-8")
    with pytest.raises(ParseError) as excinfo:
        load_timesheet(path)
    assert str(excinfo.value).startswith("line 2: ")
