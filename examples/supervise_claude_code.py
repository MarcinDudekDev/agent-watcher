#!/usr/bin/env python3
"""Supervise a live Claude Code session. A complete, working adapter.

This is the whole integration in one file: start an agent, feed its transcript to
the supervisor as it arrives, and push interventions back into the running
session. `harness/run.py` does exactly this with more bookkeeping around it.

    python3 examples/supervise_claude_code.py \\
        --goal-file TASK.md \\
        --prompt "Read TASK.md and carry it out." \\
        --cwd /path/to/the/project

    # or with no goal at all - the supervisor is told it has not been told:
    python3 examples/supervise_claude_code.py --prompt "Fix the failing tests."

Add `--mode alarm` to have it report without ever speaking to the agent. Start
there on anything you care about.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from watcher import Config, Watcher  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompt", required=True, help="what the agent should do")
    ap.add_argument("--goal-file", default=None, help="file whose contents are the goal")
    ap.add_argument("--goal", default=None, help="the goal as a literal string")
    ap.add_argument("--cwd", default=".", help="where the agent works")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--mode", choices=["intervene", "alarm"], default="intervene")
    ap.add_argument("--every", type=int, default=3, help="review every N agent turns")
    ap.add_argument("--max-turns", type=int, default=200)
    ap.add_argument("--transcript", default=None, help="also write the raw stream here")
    args = ap.parse_args()

    goal = args.goal
    if args.goal_file:
        goal = Path(args.goal_file).read_text(encoding="utf-8")

    # 1. Start the agent. `--input-format stream-json` is the part that matters:
    #    without it stdin is closed after the first prompt and nothing can be
    #    injected later, which makes supervision decorative.
    agent = subprocess.Popen(
        [
            "claude", "-p",
            "--output-format", "stream-json",
            "--input-format", "stream-json",
            "--verbose",
            "--model", args.model,
            "--max-turns", str(args.max_turns),
            "--dangerously-skip-permissions",
        ],
        cwd=args.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )

    def send(text: str) -> None:
        """Push a user message into the *running* session."""
        agent.stdin.write(json.dumps({
            "type": "user",
            "message": {"role": "user", "content": [{"type": "text", "text": text}]},
        }) + "\n")
        agent.stdin.flush()

    # 2. Build the supervisor. `deliver` is how an intervention reaches the agent;
    #    in `alarm` mode it is never called.
    def deliver(text: str) -> None:
        if agent.poll() is None:
            send(text)

    supervisor = Watcher(
        Config(goal=goal, model=args.model, every_n_turns=args.every, mode=args.mode),
        deliver=deliver,
    )

    send(args.prompt)
    started = time.time()
    out = open(args.transcript, "w", encoding="utf-8") if args.transcript else None
    reported = 0

    # 3. Feed every event to the supervisor as it arrives. `observe_async` returns
    #    immediately and reviews on a background thread, so the agent is never
    #    blocked waiting for a verdict.
    for line in agent.stdout:
        line = line.strip()
        if not line:
            continue
        if out:
            out.write(line + "\n")
            out.flush()
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "result":
            break
        supervisor.observe_async(event)

        while len(supervisor.observations) > reported:
            observation = supervisor.observations[reported]
            reported += 1
            if observation.fired:
                print(f"\n  [supervisor @turn {observation.delivered_at_turn}] "
                      f"{observation.text}\n", flush=True)

    try:
        agent.stdin.close()
    except Exception:
        pass
    agent.wait(timeout=60)
    if out:
        out.close()

    # 4. Always report the call count, not just the interventions. A supervisor
    #    that never ran and one that had nothing to say look identical otherwise -
    #    a bug that cost this project six runs of meaningless evidence.
    print(f"\n{'-' * 60}")
    print(f"supervisor calls : {len(supervisor.observations)}")
    print(f"interventions    : {len(supervisor.interventions)}")
    print(f"wall clock       : {time.time() - started:.0f}s")
    if not supervisor.alive:
        print("WARNING: the supervisor never ran. Zero interventions means nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
