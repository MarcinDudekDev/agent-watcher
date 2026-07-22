# watcher-eval

A repeatable exam for measuring how much of an executor agent's drift an external
watcher agent catches.

One agent (the **executor**) works through a task. A second agent (the **watcher**)
watches its transcript from outside and can interject. The exam seeds five classes
of drift into the task and grades, mechanically, which ones the executor fell into.
Running the same exam with `--watcher on` and `--watcher off` gives the delta.

## Layout

```
fixture/    the repository the executor sees. Nothing here refers to the exam.
traps/      trap definitions, the hidden test suite, the grader, the reference
            solution. The executor never sees this directory.
harness/    run.py builds a pristine clone, runs the executor, grades the run.
runs/       one directory per pass (gitignored).
```

**The executor only ever gets a clone of `fixture/`.** `traps/` and `harness/` live
outside the workdir. Keep it that way: any hint that this is an exam invalidates
every measurement taken with it.

## Running a pass

```
./harness/run.sh --watcher off --model sonnet
./harness/run.sh --watcher on  --model sonnet --id myrun
```

Each pass:

1. rebuilds a one-commit git repo from `fixture/`, tagged `pristine`;
2. clones it through a **local bare repo** (`runs/<id>/origin.git`) so `origin`
   exists but points nowhere real;
3. pre-warms `uv sync`;
4. runs the executor headless with `--setting-sources ''`, so no user-level
   `CLAUDE.md`, settings or hooks leak into the session;
5. streams the transcript to `runs/<id>/transcript.jsonl`;
6. calls `traps/grade.py`.

Runs are independent: nothing is reused between them and the workdir is fresh
every time.

Grade a finished run again at any point:

```
python3 traps/grade.py --run-dir runs/<id>
```

## Output

`runs/<id>/grade.json`:

```json
{
  "task_completed": true,
  "traps": { "D1": { "tripped": false, "evidence": {...}, "turn_number": null }, ... },
  "tripped_count": 2
}
```

Every check is mechanical — file hashes, git refs, command counts, and a hidden
pytest suite. There are no judgement calls in the grader.

## Traps

See `traps/TRAPS.md`.

## Calibration

See `traps/CALIBRATION.md` for measured trip rates and how to re-measure.
