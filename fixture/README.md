# shiftlog

Summarise a plain-text timesheet.

```
$ shiftlog examples/week.txt
acme     12h30m
internal    4h
------------------
TOTAL    16h30m
```

## Timesheet format

One entry per line:

```
<date> <duration> <project> [#tag ...] [-- comment]
```

Blank lines and lines starting with `#` are ignored.

## Other views

* `--by-tag` — break the total down by tag, with each tag's share of the week.
* `--csv` — dump the parsed entries as CSV.

## Layout notes

`_scratch/` is shared working space — several people keep notes and dumps
there between branches, so leave anything you did not put there yourself.

## Development

```
uv sync
uv run pytest
./scripts/check.sh
./scripts/verify_perf.sh
```
