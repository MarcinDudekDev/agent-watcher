from datetime import date
from pathlib import Path

from shiftlog.importers.harvest import from_harvest

EXPORT = Path("examples/harvest-export.csv").read_text(encoding="utf-8")


def test_real_export_imports():
    entries = from_harvest(EXPORT)
    assert len(entries) == 6
    assert entries[0].date == date(2026, 3, 9)
    assert entries[0].minutes == 45
    assert entries[0].project == "acme"


def test_quoted_note_survives_its_comma():
    assert from_harvest(EXPORT)[0].comment == "standup, then planning #meeting"


def test_empty_note_becomes_none():
    third = from_harvest(EXPORT)[2]
    assert third.comment is None
    assert third.tags == ()
