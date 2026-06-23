from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from ai_agents_hw6.domain import (
    GameAction,
    GameState,
    MoveAction,
    PlaceBarrierAction,
    Role,
    ScoreResult,
    AttemptId,
    Coordinate,
    GridSize,
    SeriesId,
    SubGameId,
    TerminalOutcome,
    TerminalReason,
)


EVENT_SCHEMA_VERSION = "1.0"
SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "refresh_token",
    "secret",
    "token",
}


@dataclass(frozen=True)
class EventRecord:
    schema_version: str
    event_type: str
    timestamp: str
    series_id: str
    sub_game_id: str
    attempt_id: str
    valid_game_index: int
    attempt_number: int
    seed: int
    payload: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "series_id": self.series_id,
            "sub_game_id": self.sub_game_id,
            "attempt_id": self.attempt_id,
            "valid_game_index": self.valid_game_index,
            "attempt_number": self.attempt_number,
            "seed": self.seed,
            "payload": redact(self.payload),
        }


class EventLog:
    def __init__(self) -> None:
        self._events: list[EventRecord] = []

    @property
    def records(self) -> tuple[EventRecord, ...]:
        return tuple(self._events)

    def append(
        self,
        *,
        event_type: str,
        state: GameState,
        valid_game_index: int,
        attempt_number: int,
        payload: dict[str, Any],
    ) -> EventRecord:
        record = EventRecord(
            schema_version=EVENT_SCHEMA_VERSION,
            event_type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            series_id=str(state.series_id),
            sub_game_id=str(state.sub_game_id),
            attempt_id=str(state.attempt_id),
            valid_game_index=valid_game_index,
            attempt_number=attempt_number,
            seed=state.seed,
            payload=payload,
        )
        self._events.append(record)
        return record

    def to_json(self) -> list[dict[str, Any]]:
        return [record.to_json() for record in self._events]


def action_to_json(action: GameAction) -> dict[str, Any]:
    if isinstance(action, MoveAction):
        return {"type": action.type.value, "direction": action.direction.value}
    if isinstance(action, PlaceBarrierAction):
        return {"type": action.type.value, "target": action.target.to_json()}
    raise TypeError(f"unsupported action: {action!r}")


def role_action_to_json(role: Role, action: GameAction) -> dict[str, Any]:
    return {"role": role.value, "action": action_to_json(action)}


def state_to_json(state: GameState) -> dict[str, Any]:
    return {
        "series_id": str(state.series_id),
        "sub_game_id": str(state.sub_game_id),
        "attempt_id": str(state.attempt_id),
        "grid": state.grid.to_json(),
        "cop_position": state.cop_position.to_json(),
        "thief_position": state.thief_position.to_json(),
        "active_role": state.active_role.value,
        "seed": state.seed,
        "move_round": state.move_round,
        "barriers": [barrier.to_json() for barrier in sorted(state.barriers)],
        "barriers_placed": state.barriers_placed,
        "terminal_outcome": state.terminal_outcome.value if state.terminal_outcome else None,
        "terminal_reason": state.terminal_reason.value if state.terminal_reason else None,
    }


def state_from_json(value: dict[str, Any]) -> GameState:
    """Rebuild a committed state snapshot for replay/display, never live mutation."""

    return GameState(
        series_id=SeriesId(value["series_id"]),
        sub_game_id=SubGameId(value["sub_game_id"]),
        attempt_id=AttemptId(value["attempt_id"]),
        grid=GridSize.from_json(value["grid"]),
        cop_position=Coordinate.from_json(value["cop_position"]),
        thief_position=Coordinate.from_json(value["thief_position"]),
        active_role=Role(value["active_role"]),
        seed=value["seed"],
        move_round=value["move_round"],
        barriers=(Coordinate.from_json(item) for item in value["barriers"]),
        barriers_placed=value["barriers_placed"],
        terminal_outcome=(
            TerminalOutcome(value["terminal_outcome"]) if value["terminal_outcome"] else None
        ),
        terminal_reason=(
            TerminalReason(value["terminal_reason"]) if value["terminal_reason"] else None
        ),
    )


def state_hash(state: GameState) -> str:
    canonical = json.dumps(state_to_json(state), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def score_to_json(score: ScoreResult) -> dict[str, int]:
    return {"cop": score.cop, "thief": score.thief}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if any(fragment in key.lower() for fragment in SENSITIVE_KEYS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
        value = re.sub(
            r"(?i)\b(api[_-]?key|token|password|client[_-]?secret)\s*[:=]\s*\S+",
            r"\1=[REDACTED]",
            value,
        )
    return value


def atomic_write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as temp_file:
        temp_file.write(text)
        temp_file.write("\n")
        temp_path = Path(temp_file.name)
    temp_path.replace(target)
