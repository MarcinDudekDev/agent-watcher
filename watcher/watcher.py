"""A supervisor that watches an agent session and speaks up when it drifts.

Standalone on purpose. It knows nothing about the exam it was extracted from: it
takes a stream of transcript events, a goal it is handed from outside, and a
callback for delivering an intervention. The exam harness is one caller of this;
so is anything else with a transcript.

    watcher = Watcher(Config(goal=Path("TASK.md").read_text()))
    for event in session:
        note = watcher.observe(event)
        if note:
            session.send(note.text)

Two modes. `alarm` reports and never speaks to the agent; `intervene` speaks.
Read-only first is deliberate — a wrong diagnosis plus an autonomous correction
multiplies the mess instead of reducing it.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .prompt import system_prompt

MAX_TEXT = 1200
MAX_TOOL_INPUT = 600
MAX_TOOL_RESULT = 800


@dataclass
class Config:
    goal: str | None = None
    model: str = "sonnet"
    every_n_turns: int = 3
    window_lines: int = 24
    mode: str = "intervene"  # "intervene" | "alarm"
    timeout: int = 120
    # When no goal is supplied, take the session's first user message as one.
    # Off by default: an opening message is often "carry on where you left off",
    # and a supervisor holding that as the goal is worse than one holding none.
    infer_goal_from_first_message: bool = False


@dataclass
class Observation:
    """One completed look at the transcript. Recorded whether or not it fired."""

    looked_at_turn: int
    delivered_at_turn: int
    fired: bool
    text: str
    events_seen: int
    seconds: float

    def as_dict(self) -> dict:
        return {
            "looked_at_turn": self.looked_at_turn,
            "delivered_at_turn": self.delivered_at_turn,
            "after_event": self.events_seen,
            "text": self.text,
            "fired": self.fired,
            "seconds": round(self.seconds, 1),
        }


def render_window(events: Iterable[dict], limit: int = 24) -> str:
    """A compact rendering of the tail of a transcript."""
    lines: list[str] = []
    for event in events:
        message = event.get("message") or {}
        role = message.get("role")
        for block in message.get("content") or []:
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "text" and block.get("text", "").strip():
                lines.append(f"{role}: {block['text'].strip()[:MAX_TEXT]}")
            elif kind == "tool_use":
                payload = json.dumps(block.get("input", {}))[:MAX_TOOL_INPUT]
                lines.append(f"assistant tool_use {block.get('name')}: {payload}")
            elif kind == "tool_result":
                content = block.get("content")
                text = content if isinstance(content, str) else json.dumps(content)
                lines.append(f"tool_result: {str(text)[:MAX_TOOL_RESULT]}")
    return "\n".join(lines[-limit:])


def parse_verdict(reply: str) -> str | None:
    """The intervention text, or None for silence.

    Read from the dedicated last line rather than the whole reply: the supervisor
    narrates its way through the checks first, and scoring the whole reply once
    counted "No, no, no, no, no" as an intervention.
    """
    for line in reversed(reply.strip().splitlines()):
        line = line.strip()
        if line.upper().startswith("VERDICT:"):
            body = line.split(":", 1)[1].strip()
            return None if body.upper().rstrip(".") == "OK" else body
    return None if reply.strip().upper().rstrip(".") == "OK" else reply.strip()


def first_user_message(events: Iterable[dict]) -> str | None:
    for event in events:
        message = event.get("message") or {}
        if message.get("role") != "user":
            continue
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "").strip() or None
            if isinstance(block, str) and block.strip():
                return block.strip()
    return None


class Watcher:
    """Supervises a session. Not tied to any particular harness."""

    def __init__(self, config: Config | None = None,
                 deliver: Callable[[str], None] | None = None) -> None:
        self.config = config or Config()
        self.deliver = deliver
        self.observations: list[Observation] = []
        self._events: list[dict] = []
        self._turns = 0
        self._busy = threading.Lock()
        self._goal = self.config.goal

    # -- introspection ----------------------------------------------------

    @property
    def alive(self) -> bool:
        """Has the supervisor actually run? A silent watcher and a broken one
        produce identical evidence, so callers must be able to tell them apart."""
        return bool(self.observations)

    @property
    def interventions(self) -> list[Observation]:
        return [o for o in self.observations if o.fired]

    def system_prompt(self) -> str:
        return system_prompt(self._goal)

    # -- driving ----------------------------------------------------------

    def observe(self, event: dict) -> Observation | None:
        """Feed one transcript event. Returns an Observation when one completes.

        Synchronous: the caller blocks for the length of a supervisor call. Use
        `observe_async` to let the agent keep working while it thinks.
        """
        self._record(event)
        if not self._due(event):
            return None
        return self._review()

    def observe_async(self, event: dict) -> None:
        """As `observe`, off-thread. At most one review runs at a time; events
        arriving while it thinks are simply included in the next window."""
        self._record(event)
        if not self._due(event) or not self._busy.acquire(blocking=False):
            return

        def run() -> None:
            try:
                self._review()
            finally:
                self._busy.release()

        threading.Thread(target=run, daemon=True).start()

    def _record(self, event: dict) -> None:
        self._events.append(event)
        if event.get("type") == "assistant":
            self._turns += 1
        if self._goal is None and self.config.infer_goal_from_first_message:
            self._goal = first_user_message(self._events)

    def _due(self, event: dict) -> bool:
        return (
            event.get("type") == "assistant"
            and self.config.every_n_turns > 0
            and self._turns % self.config.every_n_turns == 0
        )

    def _review(self) -> Observation | None:
        looked_at = self._turns
        snapshot = list(self._events)
        started = time.time()
        reply = self._ask(render_window(snapshot, self.config.window_lines))
        note = parse_verdict(reply) if reply is not None else None

        observation = Observation(
            looked_at_turn=looked_at,
            # The turn the reply actually lands on, which is later than the one it
            # looked at because the call takes time the agent spends working. Any
            # time-to-detection measured against `looked_at_turn` credits the
            # supervisor with turns it did not save.
            delivered_at_turn=self._turns,
            fired=bool(note),
            text=note or "",
            events_seen=len(snapshot),
            seconds=time.time() - started,
        )
        self.observations.append(observation)
        if note and self.deliver and self.config.mode == "intervene":
            self.deliver(f"[supervisor] {note}")
        return observation

    def _ask(self, window: str) -> str | None:
        prompt = (
            "Here is the most recent part of the agent's transcript.\n\n"
            f"<transcript>\n{window}\n</transcript>\n\n"
            "Work through the checks and answer."
        )
        # A neutral empty cwd. Run from the supervised project and the supervisor
        # picks that project up and starts describing it instead of the transcript
        # it was handed.
        with tempfile.TemporaryDirectory() as neutral:
            proc = subprocess.run(
                [
                    "claude", "-p", "--output-format", "json", "--setting-sources", "",
                    "--model", self.config.model,
                    "--append-system-prompt", self.system_prompt(),
                    "--allowedTools", "",
                ],
                # On stdin, never as a positional argument: `--allowedTools` is
                # variadic and silently swallows the next argument, so a prompt
                # passed positionally never reaches the model at all. That bug
                # produced six runs of a supervisor that answered "OK" to nothing.
                cwd=neutral, input=prompt, capture_output=True, text=True,
                timeout=self.config.timeout,
            )
        try:
            return json.loads(proc.stdout)["result"].strip()
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
