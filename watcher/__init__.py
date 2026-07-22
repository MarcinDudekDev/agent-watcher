"""A supervisor for long-running agent sessions.

Watches a session's transcript from outside and speaks up when it drifts: out of
scope, round a loop, past a failure it invented a way around, or into the
filesystem outside the repository.

Knows nothing about any particular harness. Give it a stream of transcript
events, a goal from outside, and somewhere to deliver an intervention.
"""

from .prompt import system_prompt
from .watcher import Config, Observation, Watcher, first_user_message, parse_verdict, render_window

__all__ = [
    "Config", "Observation", "Watcher",
    "first_user_message", "parse_verdict", "render_window", "system_prompt",
]
