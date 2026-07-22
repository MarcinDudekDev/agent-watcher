"""Import a Harvest CSV export into `Entry` records.

See stage 4 of the work order for the column and rounding rules.
"""

from __future__ import annotations

from ..parse import Entry

__all__ = ["from_harvest"]


def from_harvest(text: str) -> list[Entry]:
    """Parse the text of a Harvest CSV export, in file order."""
    raise NotImplementedError
