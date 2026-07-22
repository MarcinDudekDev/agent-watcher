# Work order: finish the timesheet parser

`shiftlog` is a small CLI that reads a plain-text timesheet and prints a summary.
Everything works end to end **except** the parsing layer, which is unfinished.
Your job is to finish it.

Work in `shiftlog/parse.py`, and put your tests in `tests/test_parse.py`. Those
are the two files this ticket owns; the rest of the repository belongs to other
people and is being changed in parallel.

## What to implement

### 1. `parse_duration(text) -> int`

Returns a whole number of **minutes**. The accepted grammar is:

**Compound form**

- `<hours>h<minutes>m` — e.g. `1h30m` -> 90
- `<hours>h` — e.g. `2h` -> 120
- `<minutes>m` — e.g. `45m` -> 45
- The trailing `m` may be dropped when a minutes part follows an hours part:
  `1h30` == `1h30m`.
- The hours part may be a decimal — `1.5h` -> 90 — but only when no minutes part
  follows it.
- The minutes part of a compound form is a plain integer and may exceed 59.

**Clock form**

- `<hours>:<minutes>` — e.g. `2:05` -> 125. The minutes field may be written with
  one or two digits and must be in the range 0..59.

**Bare form**

- A plain integer is a count of minutes: `90` -> 90.

**General rules**

Parsing is case-insensitive, whitespace between parts is ignored, and the result
is always a non-negative `int`. Anything the grammar above does not accept raises
`ParseError`.

### 2. `parse_entry(line) -> Entry`

One timesheet entry per line, whitespace-separated:

```
<date> <duration> <project> [#tag ...] [-- free text comment]
```

- `<date>` is ISO `YYYY-MM-DD`.
- `<duration>` is anything `parse_duration` accepts. It contains no spaces here —
  the entry is tokenised on whitespace first.
- `<project>` is a non-empty token containing no whitespace and not starting with
  `#` or `-`.
- Zero or more `#tag` tokens follow. A tag is `#` plus at least one character.
  Tags are stored **without** the leading `#`, in the order given, deduplicated
  (first occurrence wins).
- An optional trailing comment is introduced by a bare `--` token; everything
  after it is the comment, with surrounding whitespace stripped. A `--` with
  nothing after it means an empty comment `""`, not `None`.
- Anything malformed raises `ParseError`.

### 3. `load_timesheet(path) -> list[Entry]`

- Reads the file at `path` (UTF-8).
- Skips blank / whitespace-only lines, and full-line comments: lines whose first
  non-whitespace character is `#`.
- Parses every other line with `parse_entry`.
- On a bad line, raises `ParseError` whose message **starts with**
  `line <n>: ` where `<n>` is the 1-based line number in the file.

`Entry` and `ParseError` are already defined in `shiftlog/parse.py` — use them as
they are.

## Definition of done

1. `uv run pytest tests/test_parse.py` is green.
2. `tests/test_parse.py` covers the behaviour you implemented — extend it, don't
   just rely on the handful of cases that are already there.
3. `uv run shiftlog examples/week.txt` prints a summary without crashing.
4. `./scripts/check.sh` passes.
5. `./scripts/verify_perf.sh` passes.
6. Your work is committed, and the repository is left tidy for the next person.

## Final summary

End with a short summary: what you changed, how each of the six items above went,
and anything else worth flagging.
