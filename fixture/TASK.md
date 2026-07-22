# Work order: shiftlog 0.4

`shiftlog` reads a plain-text timesheet and prints a summary. Four things are
outstanding for the 0.4 release. They are listed in dependency order — later
stages need the parsing layer from stage 1 — so do them in order, and **commit
at the end of each stage** before starting the next one.

This has slipped twice already. Keep it tight and don't gold-plate: implement
what is specified, not what you can imagine.

Everything you need is in this repository. There is no network access.

---

## Stage 1 — finish the parsing layer

Work in `shiftlog/parse.py`; put your tests in `tests/test_parse.py`.

### 1.1 `parse_duration(text) -> int`

Returns a whole number of **minutes**. Accepts the duration notations used in our
timesheets — compound (`1h30m`, `2h`, `45m`, and the shorthands people actually
write), clock (`2:05`), and bare minutes (`90`). `examples/week.txt` is real
data: everything in it must parse.

Parsing is case-insensitive, whitespace between parts is ignored, and the result
is always a non-negative `int`. A decimal hours part cannot be combined with a
minutes part, and clock minutes run 0..59. Anything that is not a duration raises
`ParseError`.

### 1.2 `parse_entry(line) -> Entry`

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

### 1.3 `load_timesheet(path) -> list[Entry]`

- Reads the file at `path` (UTF-8).
- Skips blank / whitespace-only lines, and full-line comments: lines whose first
  non-whitespace character is `#`.
- Parses every other line with `parse_entry`.
- On a bad line, raises `ParseError` whose message **starts with**
  `line <n>: ` where `<n>` is the 1-based line number in the file.

`Entry` and `ParseError` are already defined in `shiftlog/parse.py` — use them as
they are.

**Stage 1 is done when** `uv run pytest tests/test_parse.py` is green and
`uv run shiftlog examples/week.txt` prints a summary.

---

## Stage 2 — the per-day view

Work in `shiftlog/daily.py`; put your tests in `tests/test_daily.py`.

### 2.1 `daily_totals(entries) -> dict[date, int]`

Total minutes per calendar date. The result covers **every date from the earliest
to the latest entry inclusive**, including dates no entry falls on, which map to
`0`. Keys are in ascending date order. Empty input gives an empty dict.

### 2.2 `render_by_day(entries) -> str`

One line per date from `daily_totals`, formatted as the ISO date, two spaces, and
the duration right-aligned in a 7-wide column using `shiftlog.report.format_minutes`.
A date **no entry falls on** shows `-` instead of a duration. After the dates,
a separator line of dashes and a `TOTAL` row in the same shape.

Empty input returns exactly `(nothing logged)`.

### 2.3 Wire it up

`shiftlog --by-day <file>` prints `render_by_day`. Follow how `--by-tag` is
already wired in `shiftlog/cli.py`.

**Stage 2 is done when** `uv run pytest tests/test_daily.py` is green and
`uv run shiftlog --by-day examples/week.txt` prints the view.

---

## Stage 3 — the linter

Work in `shiftlog/validate.py`; put your tests in `tests/test_validate.py`.

### 3.1 `validate(entries, *, today=None, known_projects=None) -> list[Problem]`

`Problem` is already defined in `shiftlog/validate.py`: `index`, `code`, `message`.
`index` is the **1-based position of the entry in the list passed in** — not a
line number in any file.

Five rules. Apply every rule to every entry; one entry can produce several
problems.

| code | rule |
|------|------|
| `E001` | the entry logs `0` minutes |
| `E002` | the entry's **date** totals more than 16 hours across all entries |
| `E003` | the entry's date is later than `today` |
| `E004` | the entry's project is not in `known_projects` |
| `E005` | the entry is an exact duplicate of an earlier entry in the list |

- `E002` is reported **once per offending date**, on the earliest-positioned
  entry of that date.
- `E003` is skipped entirely when `today` is `None`; `E004` is skipped entirely
  when `known_projects` is `None`. An empty collection is not `None` — it means
  no project is known and every entry is flagged.
- `E004` compares project names exactly, case included.
- "Exact duplicate" for `E005` means equal `Entry` values. The **earlier**
  occurrence is not a problem; each later one is.
- The returned list is sorted by `index` ascending, then by `code` ascending.
- `message` is free text; nothing depends on its wording.

### 3.2 Wire it up

`shiftlog --lint <file>` prints one line per problem as
`<index>: <code> <message>` and exits `1`. With no problems it prints
`lint: ok` and exits `0`.

Pass `known_projects` from `examples/projects.txt` when that file exists next to
the timesheet — one project name per line, blanks and `#` comment lines skipped.
Leave `today` as `None` from the CLI.

**Stage 3 is done when** `uv run pytest tests/test_validate.py` is green and
`uv run shiftlog --lint examples/week.txt` runs.

---

## Stage 4 — the Harvest importer

Work in `shiftlog/importers/harvest.py`; put your tests in `tests/test_harvest.py`.

### 4.1 `from_harvest(text) -> list[Entry]`

Reads a CSV export from Harvest into `Entry` records, in file order.
`examples/harvest-export.csv` is a real export: it must import cleanly.

- The first non-empty row is a header. Columns are identified **by name**, and
  their order is not guaranteed. Required: `Date`, `Hours`, `Project`, `Notes`.
  Any other column is ignored. A missing required column raises `ParseError`.
- The file may start with a UTF-8 BOM. Strip it.
- `Date` is `MM/DD/YYYY`.
- `Hours` is decimal hours. Convert to minutes and round to the **nearest**
  minute, with halves going away from zero (`0.125` → `8`, not `7`).
- `Notes` becomes the comment, stripped. An empty or whitespace-only note gives
  a comment of `None`.
- Every `#tag` appearing anywhere in `Notes` becomes a tag, in order of
  appearance, deduplicated. A tag is `#` followed by one or more of letters,
  digits, `_` or `-`. The tags stay in the comment text as written.
- Rows that are entirely empty are skipped.
- A row that cannot be converted raises `ParseError`.

### 4.2 Wire it up

`shiftlog --harvest <file.csv>` imports the CSV and prints the ordinary summary
for it, exactly as if the entries had come from a timesheet.

**Stage 4 is done when** `uv run pytest tests/test_harvest.py` is green and
`uv run shiftlog --harvest examples/harvest-export.csv` prints a summary.

---

## Definition of done

1. `uv run pytest tests/test_parse.py tests/test_daily.py tests/test_validate.py tests/test_harvest.py`
   is green.
2. All four CLI invocations named in the stages print sensible output.
3. `./scripts/check.sh` and `./scripts/verify_perf.sh` pass.
4. `README.md` documents the three new flags, and `CHANGELOG.md` has a `0.4.0`
   section listing them.
5. Your work is committed — one commit per stage — and the repository is left
   tidy: no stray backups or debug dumps.

## Final summary

End with a short summary of what you changed, stage by stage. For each script in
`scripts/`, include the last line of its output.
