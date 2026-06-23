from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from ai_agents_hw6.domain import Coordinate, GameAction, GameState, GridSize, Role, legal_actions


@dataclass(frozen=True)
class Observation:
    protocol_version: str
    request_id: str
    role: Role
    grid: GridSize
    self_position: Coordinate
    visible_opponent: Coordinate | None
    visible_barriers: frozenset[Coordinate]
    legal_actions: tuple[GameAction, ...]
    move_round: int
    max_moves: int
    barriers_placed: int
    max_barriers: int
    history_summary: tuple[str, ...] = ()

    def to_public_json(self) -> dict:
        return {
            "protocol_version": self.protocol_version,
            "request_id": self.request_id,
            "role": self.role.value,
            "grid_size": self.grid.to_json(),
            "self_position": self.self_position.to_json(),
            "visible_opponent": self.visible_opponent.to_json()
            if self.visible_opponent is not None
            else None,
            "visible_barriers": [barrier.to_json() for barrier in sorted(self.visible_barriers)],
            "legal_actions": [_action_public_json(action) for action in self.legal_actions],
            "move_round": self.move_round,
            "max_moves": self.max_moves,
            "barriers_placed": self.barriers_placed,
            "max_barriers": self.max_barriers,
            "history_summary": list(self.history_summary),
        }


def build_observation(
    state: GameState,
    *,
    request_id: str,
    role: Role,
    protocol_version: str = "1.0",
    manhattan_radius: int = 2,
    max_moves: int = 25,
    max_barriers: int = 5,
    history_summary: tuple[str, ...] = (),
) -> Observation:
    if manhattan_radius < 0:
        raise ValueError("manhattan_radius must be non-negative")
    self_position = state.cop_position if role is Role.COP else state.thief_position
    opponent_position = state.thief_position if role is Role.COP else state.cop_position
    visible_opponent = (
        opponent_position
        if manhattan_distance(self_position, opponent_position) <= manhattan_radius
        else None
    )
    visible_barriers = frozenset(
        barrier
        for barrier in state.barriers
        if manhattan_distance(self_position, barrier) <= manhattan_radius
    )
    return Observation(
        protocol_version=protocol_version,
        request_id=request_id,
        role=role,
        grid=state.grid,
        self_position=self_position,
        visible_opponent=visible_opponent,
        visible_barriers=visible_barriers,
        legal_actions=legal_actions(state, role=role, max_barriers=max_barriers),
        move_round=state.move_round,
        max_moves=max_moves,
        barriers_placed=state.barriers_placed,
        max_barriers=max_barriers,
        history_summary=history_summary,
    )


def observation_from_public_json(payload: dict[str, Any]) -> Observation:
    from ai_agents_hw6.contracts.actions import parse_action_payload

    if not isinstance(payload, dict):
        raise ValueError("observation must be an object")
    role = Role(payload["role"])
    return Observation(
        protocol_version=str(payload["protocol_version"]),
        request_id=str(payload["request_id"]),
        role=role,
        grid=GridSize.from_json(payload["grid_size"]),
        self_position=Coordinate.from_json(payload["self_position"]),
        visible_opponent=Coordinate.from_json(payload["visible_opponent"])
        if payload.get("visible_opponent") is not None
        else None,
        visible_barriers=frozenset(
            Coordinate.from_json(item) for item in payload.get("visible_barriers", [])
        ),
        legal_actions=tuple(
            parse_action_payload(item, role) for item in payload.get("legal_actions", [])
        ),
        move_round=_require_int(payload, "move_round"),
        max_moves=_require_int(payload, "max_moves"),
        barriers_placed=_require_int(payload, "barriers_placed"),
        max_barriers=_require_int(payload, "max_barriers"),
        history_summary=tuple(str(item) for item in payload.get("history_summary", [])),
    )


def manhattan_distance(first: Coordinate, second: Coordinate) -> int:
    return abs(first.row - second.row) + abs(first.column - second.column)


def _action_public_json(action: GameAction) -> dict:
    from ai_agents_hw6.domain import MoveAction, PlaceBarrierAction

    if isinstance(action, MoveAction):
        return {"type": action.type.value, "direction": action.direction.value}
    if isinstance(action, PlaceBarrierAction):
        return {"type": action.type.value, "target": action.target.to_json()}
    raise TypeError(f"unsupported action: {action!r}")


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"observation.{key} must be an integer")
    return value
