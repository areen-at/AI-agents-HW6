from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from ai_agents_hw6.application.events import redact, state_from_json
from ai_agents_hw6.application.series import SeriesResult
from ai_agents_hw6.domain import GameAction, GameState, MoveAction, PlaceBarrierAction, Role

SYMBOLS = {"cop": "C", "thief": "T", "barrier": "#", "empty": "."}
COORDINATE_HELP = "Coordinates are zero-based [row,column]; row 0 is top, column 0 is left."


def render_board(state: GameState) -> str:
    """Return a read-only rectangular projection of an authoritative state."""

    column_width = max(1, len(str(state.grid.columns - 1)))
    prefix_width = max(1, len(str(state.grid.rows - 1)))
    header = " " * (prefix_width + 2) + " ".join(
        f"{column:>{column_width}}" for column in range(state.grid.columns)
    )
    rows = [header]
    for row in range(state.grid.rows):
        cells: list[str] = []
        for column in range(state.grid.columns):
            coordinate = (row, column)
            if coordinate == (state.cop_position.row, state.cop_position.column):
                symbol = SYMBOLS["cop"]
            elif coordinate == (state.thief_position.row, state.thief_position.column):
                symbol = SYMBOLS["thief"]
            elif any(barrier.row == row and barrier.column == column for barrier in state.barriers):
                symbol = SYMBOLS["barrier"]
            else:
                symbol = SYMBOLS["empty"]
            cells.append(f"{symbol:>{column_width}}")
        rows.append(f"{row:>{prefix_width}} | " + " ".join(cells))
    rows.append("Legend: C=Cop T=Thief #=barrier .=empty")
    return "\n".join(rows)


def render_state(
    state: GameState,
    *,
    valid_game_index: int,
    attempt_number: int,
    max_barriers: int,
    action: GameAction | None = None,
    validation: str | None = None,
    totals: dict[str, int] | None = None,
) -> str:
    action_text = _action_text(action) if action is not None else "none"
    total_scores = totals or {"cop": 0, "thief": 0}
    lines = [
        f"Series {state.series_id}",
        (
            f"Game {valid_game_index}/6 | Sub-game {state.sub_game_id} | "
            f"Attempt {attempt_number} ({state.attempt_id})"
        ),
        f"Move round: {state.move_round} | Active role: {state.active_role.value}",
        (
            f"Cop barriers: placed={state.barriers_placed} "
            f"remaining={max(0, max_barriers - state.barriers_placed)}"
        ),
        f"Selected action: {action_text} | Validation: {validation or 'pending'}",
        f"Series score: Cop={total_scores['cop']} Thief={total_scores['thief']}",
        (
            "View: authoritative committed state; agent visibility remains partial and this "
            "rendered text is never supplied to agents"
        ),
        render_board(state),
        COORDINATE_HELP,
    ]
    if state.is_terminal:
        assert state.terminal_outcome is not None
        assert state.terminal_reason is not None
        lines.append(
            f"Terminal: outcome={state.terminal_outcome.value} reason={state.terminal_reason.value}"
        )
    return "\n".join(lines)


@dataclass
class TerminalObserver:
    max_barriers: int
    stream: TextIO
    quiet: bool = False
    json_logs: bool = False
    log_level: str = "INFO"
    totals: dict[str, int] = field(default_factory=lambda: {"cop": 0, "thief": 0})

    def __post_init__(self) -> None:
        self._threshold = getattr(logging, self.log_level.upper(), logging.INFO)

    def on_endpoint_status(self, role: Role, status: str, url: str) -> None:
        payload = {
            "event_type": "endpoint_status",
            "role": role.value,
            "status": status,
            "url": url,
        }
        self._log(payload, level=logging.INFO)
        if not self.quiet:
            self.stream.write(f"MCP endpoint: role={role.value} status={status} url={url}\n")

    def on_event(self, event: dict[str, Any], state: GameState) -> None:
        self._log(
            event,
            level=logging.WARNING if event.get("event_type") == "attempt_invalid" else logging.INFO,
        )
        if self.quiet:
            return
        event_type = event["event_type"]
        payload = event["payload"]
        if event_type == "attempt_started":
            self.stream.write(
                "\n"
                + render_state(
                    state,
                    valid_game_index=event["valid_game_index"],
                    attempt_number=event["attempt_number"],
                    max_barriers=self.max_barriers,
                    totals=self.totals,
                )
                + "\n"
            )
        elif event_type == "action_applied":
            self.stream.write(
                "\n"
                + render_state(
                    state,
                    valid_game_index=event["valid_game_index"],
                    attempt_number=event["attempt_number"],
                    max_barriers=self.max_barriers,
                    action=_action_from_payload(payload["action"]),
                    validation=payload["validation"],
                    totals=self.totals,
                )
                + "\n"
            )
        elif event_type == "attempt_invalid":
            self.stream.write(
                "Technical failure: "
                f"reason={payload['failure_reason']} detail={payload['failure_detail']} "
                f"replacement_attempt={event['attempt_number'] + 1}\n"
            )
        elif event_type == "sub_game_finished":
            score = payload["score"]
            self.totals["cop"] += score["cop"]
            self.totals["thief"] += score["thief"]
            self.stream.write(
                f"Result: outcome={payload['terminal_outcome']} "
                f"reason={payload['terminal_reason']} "
                f"score=Cop:{score['cop']},Thief:{score['thief']} "
                f"totals=Cop:{self.totals['cop']},Thief:{self.totals['thief']}\n"
            )

    def on_series_finished(self, result: SeriesResult) -> None:
        self._log(
            {
                "event_type": "series_finished",
                "series_id": str(result.series_id),
                "valid_games": len(result.valid_sub_games),
                "invalid_attempts": len(result.invalid_attempts),
                "totals": result.totals,
            },
            level=logging.INFO,
        )
        if not self.quiet:
            self.stream.write(
                f"Series complete: valid_games={len(result.valid_sub_games)} "
                f"technical_failures={len(result.invalid_attempts)} "
                f"totals=Cop:{result.totals['cop']},Thief:{result.totals['thief']}\n"
            )

    def _log(self, payload: dict[str, Any], *, level: int) -> None:
        if not self.json_logs or level < self._threshold:
            return
        self.stream.write(json.dumps(redact(payload), sort_keys=True) + "\n")


def replay_events(path: str | Path, *, stream: TextIO, max_barriers: int) -> int:
    events = json.loads(Path(path).read_text(encoding="utf-8"))
    rendered = 0
    totals = {"cop": 0, "thief": 0}
    for event in events:
        payload = event.get("payload", {})
        state_payload = payload.get("state")
        if not isinstance(state_payload, dict):
            continue
        state = state_from_json(state_payload)
        action_payload = payload.get("action")
        stream.write(
            render_state(
                state,
                valid_game_index=event["valid_game_index"],
                attempt_number=event["attempt_number"],
                max_barriers=max_barriers,
                action=_action_from_payload(action_payload) if action_payload else None,
                validation=payload.get("validation"),
                totals=totals,
            )
            + "\n"
        )
        if event["event_type"] == "sub_game_finished":
            totals["cop"] += payload["score"]["cop"]
            totals["thief"] += payload["score"]["thief"]
        rendered += 1
    return rendered


def _action_text(action: GameAction) -> str:
    if isinstance(action, MoveAction):
        return f"move {action.direction.value}"
    return f"place_barrier [{action.target.row},{action.target.column}]"


def _action_from_payload(payload: dict[str, Any]) -> GameAction:
    from ai_agents_hw6.domain import Coordinate, Direction

    if payload["type"] == "move":
        return MoveAction(Direction(payload["direction"]))
    return PlaceBarrierAction(Coordinate.from_json(payload["target"]))
