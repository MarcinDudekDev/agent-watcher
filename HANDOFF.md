# Handoff — after phase 2

Read `RESULTS.md` for the numbers and `harness/ORACLE.md` for the supervisor's
own regression suite. This file is what those two do not say.

## What the project is for, as of now

**The product is `watcher/` — a standalone supervisor.** It attaches to a
session, watches the transcript, and speaks up when the session drifts. It knows
nothing about this repository: transcript events in, a goal from the caller, an
intervention out. `harness/run.py` is one consumer of it, wrapped in an exam.

The exam and its six traps are **internal scaffolding for validating the
supervisor** and are not the thing being shipped. Stop optimising them.

**False-alarm rate is metric number one**, ahead of time-to-detection. A tool
that interrupts correct work is uninstalled after one use and never gets a
second chance. Missed drift is expensive and forgivable.

## The rule this project keeps re-learning

**A single green result is evidence of nothing.** Three times now:

1. `--allowedTools` is variadic and swallowed the prompt. Six supervised runs of
   a supervisor that saw an empty transcript, answered "OK" to nothing, exited 0.
2. A run wrote an executable `shiftbench` stub onto `PATH`. The
   deliberately-impossible check succeeded for every run after it, voiding D4
   for nine runs. Caught by `verify_reference.py` asserting the seeded failures
   still fail — on its first ever execution.
3. `test_watcher.py` reported 11/11 on one call per case. Re-run with
   `--repeats 5` it was 14/15 with **9 false alarms in 45 quiet calls**, two of
   the three offending cases firing 2/5 — coin flips that read as passes.

So: repeats before rates, a positive control every batch, and an assertion that
the thing you are measuring still exists.

## Measurement traps specific to supervision

**Successful intervention erases its own evidence.** The grader inspects the repo
after the run; the supervisor acts during it. A run that deleted a tracked file,
was told off, and restored it leaves a clean tree — so the grader reports no
drift and the three interventions that produced that outcome score as false
alarms. Measured that way a perfect supervisor scores 100% false alarms. Ground
truth for "was it drifting" therefore comes from the **transcript**
(`metrics.drift_turns`); the end state answers a different question, recovery.

**Do not charge the supervisor for your own inconsistent thresholds.** The
grader trips D6 only on writes onto `PATH`; the supervisor is told any write
outside the repo. Both are defensible, holding both silently is not. Reported as
`graded_more_narrowly_than_prompted` rather than reconciled away.

**The traps under-count.** The best single intervention in the whole batch — the
agent claimed a total the command output two lines above contradicted — has no
trap category and scores `unattributable`.

## Leaks

`grade.json.exam_leak` is the control, and it has already caught one run reading
the evidence archive. A leaked run is **void**, not low-scoring; `metrics.py`
excludes it and lists it. Distance helps and cannot be relied on: D4 requires
`shiftbench` to be missing, so every executor eventually sweeps the filesystem
for it and hits whatever else mentions it.

## What has not been done

- **No auto-fix, deliberately.** Recovery is 53%: the agent ignores a correct
  diagnosis about half the time. Autonomous repair on top of that multiplies the
  mess. Order stays read-only → measure diagnostic accuracy → repair only at a
  low false-alarm rate, and only then in a worktree.
- **No publication work.** Main asked explicitly: no human-facing README, no git
  history cleanup, no packaging. That is Marcin's call after phase 2.
- **n is 8 per arm.** Nothing subtler than ~40pp is detectable. Every rate in
  `RESULTS.md` is quoted as an interval for that reason.
- **One task, one model.** Sonnet, one four-stage Python refactor. The
  supervisor has never been run against real user work, which is the whole point
  of shipping it.

## Standing rules

Sonnet only, never opus or haiku. Nothing about the traps goes to
`memorize`/`recall` — sessions share HelixDB and an executor could recall the
answers. **Never `git push`.** Commit before measuring; run ids carry the SHA.
Archive evidence to `claude-tmp/main/watcher-eval-evidence/` before reporting.
