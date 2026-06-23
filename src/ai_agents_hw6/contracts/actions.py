from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

from ai_agents_hw6.contracts.observation import Observation
from ai_agents_hw6.domain import (
    Coordinate,
    Direction,
    DomainError,
    GameAction,
    MoveAction,
    PlaceBarrierAction,
    Role,
)


MAX_ACTION_RESPONSE_CHARS = 2000


class ActionProtocolError(ValueError):
    """Raised when an untrusted action response violates the protocol."""


@dataclass(frozen=True)
class ParsedActionResponse:
    protocol_version: str
    request_id: str
    role: Role
    action: GameAction


def parse_action_response(raw_response: str, observation: Observation) -> ParsedActionResponse:
    if len(raw_response) > MAX_ACTION_RESPONSE_CHARS:
        raise ActionProtocolError("action response is too large")
    try:
        payload = json.loads(raw_response)
    except JSONDecodeError as exc:
        raise ActionProtocolError("action response must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ActionProtocolError("action response must be a JSON object")
    if set(payload) != {"protocol_version", "request_id", "role", "action"}:
        raise ActionProtocolError("action response contains unknown fields")
    if payload.get("protocol_version") != observation.protocol_version:
        raise ActionProtocolError("protocol_version mismatch")
    if payload.get("request_id") != observation.request_id:
        raise ActionProtocolError("request_id mismatch")
    if payload.get("role") != observation.role.value:
        raise ActionProtocolError("role mismatch")
    action_payload = payload.get("action")
    if not isinstance(action_payload, dict):
        raise ActionProtocolError("action must be an object")

    action = _parse_action(action_payload, observation.role)
    if action not in observation.legal_actions:
        raise ActionProtocolError("action is not legal for this observation")
    return ParsedActionResponse(
        protocol_version=observation.protocol_version,
        request_id=observation.request_id,
        role=observation.role,
        action=action,
    )


def action_response_json(
    *,
    protocol_version: str,
    request_id: str,
    role: Role,
    action: GameAction,
) -> str:
    return json.dumps(
        {
            "protocol_version": protocol_version,
            "request_id": request_id,
            "role": role.value,
            "action": _action_to_payload(action),
        },
        sort_keys=True,
    )


def should_request_repair(error_count: int) -> bool:
    return error_count == 1


def classify_unrecoverable_error(error_count: int) -> str:
    return "technical_failure" if error_count >= 2 else "repair_allowed"


def _parse_action(payload: dict[str, Any], role: Role) -> GameAction:
    action_type = payload.get("type")
    if action_type == "move":
        if set(payload) != {"type", "direction"}:
            raise ActionProtocolError("move action contains unknown fields")
        direction_value = payload.get("direction")
        try:
            return MoveAction(Direction(direction_value))
        except (ValueError, DomainError) as exc:
            raise ActionProtocolError("invalid move direction") from exc
    if action_type == "place_barrier":
        if set(payload) != {"type", "target"}:
            raise ActionProtocolError("place_barrier action contains unknown fields")
        if role is not Role.COP:
            raise ActionProtocolError("only Cop may propose place_barrier")
        target = payload.get("target")
        try:
            return PlaceBarrierAction(Coordinate.from_json(target))
        except DomainError as exc:
            raise ActionProtocolError("invalid barrier target") from exc
    raise ActionProtocolError("unknown action type")


def _action_to_payload(action: GameAction) -> dict[str, Any]:
    if isinstance(action, MoveAction):
        return {"type": "move", "direction": action.direction.value}
    if isinstance(action, PlaceBarrierAction):
        return {"type": "place_barrier", "target": action.target.to_json()}
    raise TypeError(f"unsupported action: {action!r}")
