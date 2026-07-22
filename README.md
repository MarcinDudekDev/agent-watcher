# watcher

A supervisor for long-running agent sessions. It watches the transcript of a
working agent from outside, and interrupts when the agent goes off the rails —
edits files it was not asked to touch, loops on a failure, claims something
passed that did not, or writes outside the repository.

The problem it exists for: you leave an agent running for an hour, and only
afterwards discover it spent forty minutes on the wrong thing. The point is to
find out while it is happening, not once the mess is made.

This repository contains the supervisor, plus the exam that was built to measure
whether it actually works.

---

## Requirements

**You need a working `claude` command.** The supervisor is not a library that
calls an HTTP API — it shells out to the [Claude Code
CLI](https://claude.com/claude-code) for every review. If `claude -p "hi"` works
in your terminal, you are set up; if it does not, nothing here will run. Your
Anthropic billing is whatever that CLI already uses, so there is no separate API
key to configure.

- **Python 3.14** and [`uv`](https://docs.astral.sh/uv/). Required, not
  recommended — the exam fixture declares `requires-python = ">=3.14"`.
- **macOS or Linux.** The harness uses POSIX shell, `git` and process pipes.
  Untested on Windows.
- **git**, for the exam harness. Not needed to use the supervisor on its own.
- No network access is needed by the fixture itself.

### What it costs

Real figures from the runs in this repository, not estimates. Prices are
whatever your CLI is billed at; these were Claude Sonnet in July 2026.

| what | measured |
|---|---|
| one supervisor review | **$0.07**, about 2 seconds |
| supervising a ~1 hour agent session (a review every 3 turns) | **≈ $9.50/hour** |
| one exam run (the working agent itself) | **≈ $3.00**, about 11 minutes |
| one exam run **with** supervision on top | ≈ $3.00 + ≈ $1.80 |
| `harness/test_watcher.py --repeats 5` | 90 calls, ≈ $6, about 35 minutes |
| reproducing all three sets of runs (24 runs) | **≈ $85**, several hours |

The supervisor is the cheap part. Reviewing every 3 turns costs roughly 60% of
what the agent it is watching costs, and you can make it cheaper by raising
`every_n_turns`. Reproducing the full experiment is real money — do not start it
by accident.

---

## What was measured

Three sets of runs, all on the same four-stage programming task, all with Claude
Sonnet, each set at a fixed commit. Eight runs per set.

| | runs | task finished | supervisor calls | interruptions |
|---|---|---|---|---|
| no supervisor | 7 | 7/7 | — | — |
| **with supervisor** | 8 | 8/8 | 203 | 15 |
| with supervisor, **nothing wrong to find** | 8 | 8/8 | 220 | 4 |

### The headline

**Without the supervisor: 16 instances of the agent going off-track, none of them
noticed. With it: 42% caught.**

That is the comparison the project was built to make, and it is the strongest
result here.

| what | measured | plausible range |
|---|---|---|
| off-track behaviour caught | 42% | 23–64% |
| how long before it noticed | 11 turns (middle value) | 3–59 across cases |
| **interrupted an agent that was working fine** | **0 times out of 19** | 0–20% |
| agent actually changed course afterwards | 53% | 30–75% |

"Plausible range" means: the range the true value probably falls in, given how
few runs there were. The single numbers on the left are the best guess; the
ranges are how much you should trust them.

### How much to trust these numbers

**Eight runs per set is not many.** With a sample that small you can only see
very large effects — ones where the result shifts by tens of percent. If the
supervisor improved detection from, say, 20% to 45%, this experiment probably
would **not** have spotted it; the difference would have vanished into
randomness. Here the effect was big enough to rise above the noise (0% without
versus 42% with), but that also means we cannot tell you whether the true value
is 30% or 60%. That is why every number above comes with a range instead of a
single figure.

Also: **one task, one model.** Everything here is Claude Sonnet working through
one four-stage Python refactor. Nothing here tells you how it behaves on your
codebase, your task, or another model. It has never been run against real user
work — which is the main reason it is being published.

### The false-alarm number, and why it is first

A supervisor that interrupts correct work is worse than no supervisor: it gets
uninstalled after one use and never gets a second chance. Missed problems are
expensive but forgivable.

All 19 interruptions were read by hand. Every one was about something the agent
genuinely did:

| what it objected to | times |
|---|---|
| bumping the version in files outside the task's remit | 8 |
| writing scratch files outside the repository | 6 |
| deleting a tracked file it had not been asked to remove | 3 |
| claiming a total that the command output two lines above contradicted | 1 |
| **spurious** | **0** |

Nineteen interruptions cannot prove a rate below roughly one in five. The claim
this supports is "no false alarm happened in 19", not "the false-alarm rate is
zero".

The third set of runs is the important one here: the task had nothing wrong
planted in it at all, and across 220 checks the supervisor spoke up 4 times,
each time about something real.

---

## Known limitations

Stated plainly, because they will surface the first time someone else runs this.

**It only changes behaviour about half the time.** Recovery was 53% — the agent
carried on regardless of a correct diagnosis in nearly half the cases. Twice it
replied in effect "you're right, I'll stop", and then did not. That is why
recovery is measured by which files were touched and which commands were run
afterwards, never by what the agent said. A metric based on the agent agreeing
would have scored 10 out of 15 instead of 8 out of 15.

**It sees less than the agent it supervises.** It gets a window of transcript,
not the repository. There is a documented case it reliably misses: an agent
clearing a shared scratch directory, where the only warning ("do not clear")
sits inside a file the supervisor never sees. It is left failing in the test
suite rather than patched, because prompting it to fire there produces false
alarms on legitimate tidying — the worse trade.

**There is no automatic repair, on purpose.** At 53% recovery, an agent that
fixes things on its own would be acting on a diagnosis the working session
ignores half the time. Wrong diagnosis plus autonomous repair multiplies the
mess. The order is: watch only → measure how accurate the diagnosis is → add
repair only if false alarms stay near zero.

**This is not production-ready** and is not claimed to be.

---

## Three ways the measurement lied before it told the truth

Probably the most useful part of this repository for anyone building a similar
evaluation. Each of these produced a confident, plausible, wrong number.

### 1. A perfect supervisor would have scored 0% and looked terrible

The grader inspected the repository **after** each run. The supervisor acts
**during** the run. So when an agent deleted a tracked file, was told to put it
back, and did — the final repository was clean, the grader reported "nothing
went wrong", and the three interruptions that caused that good outcome were
scored as **false alarms**.

Measured that way, the better the supervisor works, the worse it scores. A
flawless one would show 100% false alarms and 0% detection.

Before this was found, the headline read *47% false alarms, 0% detection*. After
fixing it: *0% false alarms, 42% detection*. The same runs, the same data.

The fix: decide "was the agent going off-track" from the **transcript** — what it
actually did — not from the final state. The final state answers a different
question, which is whether it recovered.

**The general rule: never measure the effectiveness of an intervention with a
yardstick that a successful intervention destroys.**

### 2. A check that could no longer fail

The exam includes a build script that is supposed to be impossible to pass, to
see whether an agent will admit that or fake it. At some point an earlier run,
unable to pass it, had instead **created the missing tool** — writing a working
stub into a directory on the system's `PATH`, outside its own working directory.

From then on the impossible check passed, on that machine, for every subsequent
run. That measurement silently stopped measuring anything for nine runs, with no
error anywhere.

It was caught by an assertion that had nothing to do with the results: *the
planted failures must still fail*. It fired the first time it ran. That check is
permanent now, along with a snapshot of the `PATH` directories before and after
every run.

**The general rule: check that your measurement is still capable of failing.**

### 3. A green test suite that was a coin flip

The supervisor's own regression suite reported 11 out of 11 — from a single
attempt per case. Re-run with five attempts per case, it was 14 out of 15, with
**9 false alarms across 45 calls that should have been silent**.

The cause: the supervisor sees only the tail of the transcript. On a multi-stage
task the agent says "stage 2 done, committing" and the verification it ran three
turns earlier has already scrolled out of view. The supervisor read *not in my
window* as *never happened*, and interrupted at **every single stage boundary**.
Left alone, the false-alarm measurement would have been measuring the window
size rather than the supervisor.

Two of the three offending cases fired 2 times in 5 — at one attempt per case
they look like passes 60% of the time.

The fix generalises: a claim you merely **cannot confirm** is not a finding. Only
a claim the transcript **contradicts** is.

---

## Using it on your own project

The supervisor needs three things from you: **a stream of transcript events**, a
**goal**, and a **`deliver` function** that gets an intervention into the running
session. The first and third are the parts that need explaining.

### Run it

There is a complete, working adapter in
[`examples/supervise_claude_code.py`](examples/supervise_claude_code.py) — about
100 lines, and the same wiring `harness/run.py` uses. It starts an agent,
supervises it, and puts interventions back into the live session:

```bash
python3 examples/supervise_claude_code.py \
    --goal-file GOAL.md \
    --prompt "Read GOAL.md and carry it out." \
    --cwd /path/to/your/project
```

Verified on an unrelated throwaway project: 3 reviews, 0 interventions, agent
finished the job and committed. Add `--mode alarm` to have it report without
ever speaking to the agent. **Start there on anything you care about.**

### What an event is

An event is one JSON object from Claude Code's `--output-format stream-json`
stream. The supervisor only reads this shape:

```json
{"type": "assistant",
 "message": {"role": "assistant",
             "content": [{"type": "text",       "text": "..."},
                         {"type": "tool_use",   "name": "Bash",
                          "input": {"command": "..."}},
                         {"type": "tool_result", "content": "..."}]}}
```

- **`type: "assistant"` is what counts a turn.** The review interval
  (`every_n_turns`) is measured in these, so an event stream without them is
  never reviewed.
- `content` blocks of type `text`, `tool_use` and `tool_result` are all rendered
  into the window. **`tool_use` and `tool_result` matter most** — nearly every
  intervention in the measured runs quoted a command or a file path, not prose.
  Feeding it only assistant text will cripple it.
- Anything else in the object is ignored. Nothing is required beyond
  `type` and `message.content`.

So it works with: Claude Code `stream-json` (live or replayed from a `.jsonl`
transcript), or your own agent loop, as long as you emit that shape. If your
agent has a different format, translate it — the supervisor never parses
anything else.

### What `deliver` is, and when it will not work

`deliver` is a function taking one string, whose job is to get that string in
front of the agent as a new user message. In the example above it writes a JSON
message to the agent's stdin.

**This is the part most likely to fail on your setup.** It requires a session
that can accept input *while it is already working*. With Claude Code that means
starting it with `--input-format stream-json` and keeping stdin open; without
that, stdin closes after the first prompt and nothing can be injected. If your
agent runner cannot be interrupted mid-task, the supervisor still works as a
detector — use `mode="alarm"`, log the findings, and act on them yourself.

Do not assume injection works because nothing errored. In this project a broken
injection path produced six runs of clean-looking null results. `harness/test_injection.py`
exists solely to prove a message reaches a running agent.

### How much it sees

**The last 24 rendered lines of the transcript**, configurable via
`window_lines`. This matters more than it sounds. The supervisor cannot see the
work that scrolled out of that window, and the third measurement failure below
was caused by it treating "not in my window" as "never happened". It is
instructed not to do that — but it also means it will miss drift that started
long ago and left no recent trace.


### With no goal at all

If you have no task description to give it, it still works — and this is the
mode most people will hit first:

```python
supervisor = Watcher(Config(goal=None))
```

Without a goal, "out of scope" has no meaning, so the two checks that need one
are **dropped rather than guessed at**, and the supervisor is told outright that
it has not been told what the session is for and must not infer it. The four
that remain hold regardless of the task: looping, a claim the transcript
contradicts, destructive actions, and writing outside the repository.

Tested live on a project it had never seen: it catches an install into
`~/.local/bin`, and stayed silent 3 times out of 3 on an ordinary
refactor–test–commit sequence.

### Checking it yourself

```bash
uv run --with pytest pytest watcher/          # fast, no model calls
uv run --with pytest pytest watcher/ --live   # includes real model calls
python3 harness/test_watcher.py --repeats 5   # the full oracle, ~35 min
```

`test_watcher.py` is **not** a meaningful check below `--repeats 5`, and says so
if you try. 18 transcript windows: 9 that must produce an interruption, 9 that
must stay silent. A case that fires 3 times out of 5 is reported as unstable and
excluded, not counted as a pass — an unreliable case is worse than a failing one,
because it looks like coverage.

---

## Repository layout

```
watcher/    the supervisor. Standalone; knows nothing about the exam.
harness/    runs the exam. One consumer of watcher/.
fixture/    the project the working agent sees. Contains no hint of the exam.
traps/      the planted problems, hidden tests, grader and metrics.
```

Run directories are written outside the repository (`~/.watcher-eval/runs`,
override with `WATCHER_EVAL_RUNS`).

**If you intend to re-run the exam, do not let the agent read `traps/`.** Every
run is scanned for exam material appearing in its transcript; a run that leaked
is discarded rather than scored. One already was.

Further reading: [`RESULTS.md`](RESULTS.md) (the measurements), `harness/ORACLE.md` (the
supervisor's own test suite), `traps/TRAPS.md` (what the exam plants and why).

## Licence

MIT. See `LICENSE`.
