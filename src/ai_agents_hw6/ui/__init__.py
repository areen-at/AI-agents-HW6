"""Terminal UI package placeholder for later phases."""
"""Terminal-oriented read-only UI helpers."""

from ai_agents_hw6.ui.summary import render_series_summary
from ai_agents_hw6.ui.terminal import (
    COORDINATE_HELP,
    TerminalObserver,
    render_board,
    render_state,
    replay_events,
)

__all__ = [
    "COORDINATE_HELP",
    "TerminalObserver",
    "render_board",
    "render_series_summary",
    "render_state",
    "replay_events",
]
