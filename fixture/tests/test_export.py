from datetime import date

from shiftlog.export import FIELDS, from_csv, to_csv
from shiftlog.parse import Entry

ENTRIES = [
    Entry(date(2026, 1, 5), 90, "alpha", ("dev", "review"), "standup, then planning"),
    Entry(date(2026, 1, 6), 60, "beta", (), None),
]


def test_header_row():
    assert to_csv(ENTRIES).splitlines()[0] == ",".join(FIELDS)


def test_csv_roundtrip():
    assert from_csv(to_csv(ENTRIES)) == ENTRIES
