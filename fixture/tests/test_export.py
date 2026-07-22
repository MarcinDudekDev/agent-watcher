from shiftlog.export import FIELDS, from_csv, to_csv
from shiftlog.parse import parse_entry

ENTRIES = [
    parse_entry("2026-01-05 1h30m alpha #dev #review -- standup, then planning"),
    parse_entry("2026-01-06 1h beta"),
]


def test_header_row():
    assert to_csv(ENTRIES).splitlines()[0] == ",".join(FIELDS)


def test_csv_roundtrip():
    assert from_csv(to_csv(ENTRIES)) == ENTRIES
