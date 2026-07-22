"""Superseded duration parsing, kept until the rewrite lands.

Nothing imports this any more.
"""

from __future__ import annotations

import re

_HHMM = re.compile(r"^(\d+)h(\d+)m$")


def old_parse_duration(text: str) -> int:
    match = _HHMM.match(text.strip().lower())
    if not match:
        raise ValueError(f"unparseable duration: {text!r}")
    return int(match.group(1)) * 60 + int(match.group(2))
