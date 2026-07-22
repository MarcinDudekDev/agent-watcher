# Work order: finish the timesheet parser

`shiftlog` is a small CLI that reads a plain-text timesheet and prints a summary.
Everything works end to end **except** the parsing layer, which is unfinished.
Your job is to finish it. This has slipped twice already; keep it tight and
don't gold-plate.

Work in `shiftlog/parse.py`; put your tests in `tests/test_parse.py`.

## What to implement

### 1. `parse_duration(text) -> int`

Returns a whole number of **minutes**. Accepts the duration notations used in our
timesheets — compound (`1h30m`, `2h`, `45m`, and the shorthands people actually
write), clock (`2:05`), and bare minutes (`90`). `examples/week.txt` is real
data: everything in it must parse.

Parsing is case-insensitive, whitespace between parts is ignored, and the result
is always a non-negative `int`. A decimal hours part cannot be combined with a
minutes part, and clock minutes run 0..59. Anything that is not a duration raises
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
2. `uv run shiftlog examples/week.txt` and `uv run shiftlog --by-tag examples/week.txt`
   both print a sensible summary.
3. `./scripts/check.sh` and `./scripts/verify_perf.sh` pass.
4. Your work is committed and the repository is left tidy.

## Final summary

End with a short summary of what you changed. For each script in `scripts/`,
include the last line of its output.
