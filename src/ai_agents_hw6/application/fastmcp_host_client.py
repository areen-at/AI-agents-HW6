from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from ai_agents_hw6.agents import HeuristicPolicy
from ai_agents_hw6.agents.adapter import policy_input_from_observation
from ai_agents_hw6.contracts import Observation, observation_from_public_json
from ai_agents_hw6.domain import (
    Coordinate,
    Direction,
    GameAction,
    GridSize,
    MoveAction,
    PlaceBarrierAction,
    Role,
)
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION


class FastMcpHostClientError(RuntimeError):
    """Raised when the shared FastMCP host cannot be driven safely."""


@dataclass(frozen=True)
class FastMcpHostSettings:
    host_url: str
    token: str
    role: Role
    max_polls: int = 300
    poll_seconds: float = 1.0
    dry_run: bool = False

    @classmethod
    def from_environment(
        cls,
        *,
        role: Role,
        max_polls: int = 300,
        poll_seconds: float = 1.0,
        dry_run: bool = False,
    ) -> FastMcpHostSettings:
        host_url = os.environ.get("BONUS_FASTMCP_HOST_URL", "").strip()
        token = os.environ.get("BONUS_FASTMCP_HOST_TOKEN", "").strip()
        missing: list[str] = []
        if not host_url:
            missing.append("BONUS_FASTMCP_HOST_URL")
        if not token:
            missing.append("BONUS_FASTMCP_HOST_TOKEN")
        if missing:
            raise FastMcpHostClientError(
                "missing shared FastMCP host environment variables: " + ", ".join(missing)
            )
        return cls(
            host_url=_normalize_mcp_url(host_url),
            token=token,
            role=role,
            max_polls=max_polls,
            poll_seconds=poll_seconds,
            dry_run=dry_run,
        )


@dataclass(frozen=True)
class FastMcpHostRunResult:
    role: Role
    polls: int
    submitted_actions: int
    final_status: dict[str, Any]
    dry_run: bool


def run_fastmcp_host_client(settings: FastMcpHostSettings) -> FastMcpHostRunResult:
    """Drive one local role against a shared authoritative FastMCP game host."""

    return asyncio.run(_run_fastmcp_host_client_async(settings))


async def _run_fastmcp_host_client_async(
    settings: FastMcpHostSettings,
) -> FastMcpHostRunResult:
    client_cls, bearer_auth_cls = _load_fastmcp_client()
    auth = bearer_auth_cls(settings.token)
    submitted_actions = 0
    final_status: dict[str, Any] = {}

    async with client_cls(settings.host_url, auth=auth) as client:
        for poll_index in range(1, settings.max_polls + 1):
            status = _as_object(await _call_tool(client, "get_game_status"))
            final_status = status
            if _status_is_done(status):
                return FastMcpHostRunResult(
                    role=settings.role,
                    polls=poll_index,
                    submitted_actions=submitted_actions,
                    final_status=status,
                    dry_run=settings.dry_run,
                )
            active_role = _status_active_role(status)
            if active_role is None or active_role is not settings.role:
                await _receive_message_if_available(client, settings.role)
                await asyncio.sleep(settings.poll_seconds)
                continue

            observation_payload = _as_object(
                await _call_tool(client, "get_observation", {"role": settings.role.value})
            )
            observation = observation_from_fastmcp_json(observation_payload, settings.role)
            action = HeuristicPolicy().choose_action(policy_input_from_observation(observation))
            submission = action_to_fastmcp_submit_args(action, observation)
            submission["role"] = settings.role.value
            if settings.dry_run:
                final_status = {
                    **status,
                    "dry_run_next_action": dict(submission),
                }
                return FastMcpHostRunResult(
                    role=settings.role,
                    polls=poll_index,
                    submitted_actions=submitted_actions,
                    final_status=final_status,
                    dry_run=True,
                )
            await _call_tool(client, "submit_action", submission)
            submitted_actions += 1

        raise FastMcpHostClientError(
            f"shared FastMCP host did not finish within {settings.max_polls} polls"
        )


def observation_from_fastmcp_json(payload: dict[str, Any], role: Role) -> Observation:
    """Convert the opponent host's [x,y]=[col,row] observation into our internal model."""

    normalized = dict(payload)
    normalized.setdefault("protocol_version", PROTOCOL_VERSION)
    normalized.setdefault("request_id", str(payload.get("request_id", "fastmcp-host")))
    normalized["role"] = role.value
    normalized["grid_size"] = _grid_size_from_payload(payload)
    normalized["self_position"] = _xy_to_row_col(
        payload.get("self_position", payload.get("self"))
    )
    visible_opponent = payload.get("visible_opponent", payload.get("opponent"))
    normalized["visible_opponent"] = (
        _xy_to_row_col(visible_opponent) if visible_opponent is not None else None
    )
    normalized["visible_barriers"] = [
        _xy_to_row_col(item) for item in payload.get("visible_barriers", [])
    ]
    normalized["legal_actions"] = _legal_actions_from_fastmcp(payload, role)
    normalized.setdefault("move_round", _int_from_any(payload, ("move_round", "round", "turn"), 0))
    normalized.setdefault("max_moves", _int_from_any(payload, ("max_moves",), 25))
    normalized.setdefault("barriers_placed", _int_from_any(payload, ("barriers_placed",), 0))
    normalized.setdefault("max_barriers", _int_from_any(payload, ("max_barriers",), 5))
    normalized.setdefault("history_summary", payload.get("history_summary", []))
    return observation_from_public_json(normalized)


def action_to_fastmcp_submit_args(
    action: GameAction,
    observation: Observation,
) -> dict[str, int | str]:
    if isinstance(action, MoveAction):
        dx, dy = _direction_to_dx_dy(action.direction)
        return {"kind": "move", "dx": dx, "dy": dy}
    if isinstance(action, PlaceBarrierAction):
        dx = action.target.column - observation.self_position.column
        dy = action.target.row - observation.self_position.row
        if dx not in {-1, 0, 1} or dy not in {-1, 0, 1}:
            return {"kind": "stay", "dx": 0, "dy": 0}
        return {"kind": "place_barrier", "dx": dx, "dy": dy}
    return {"kind": "stay", "dx": 0, "dy": 0}


async def _call_tool(client: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    try:
        if arguments is None:
            result = await client.call_tool(name)
        else:
            result = await client.call_tool(name, arguments)
    except TypeError:
        result = await client.call_tool(name, arguments or {})
    return _unwrap_fastmcp_result(result)


async def _receive_message_if_available(client: Any, role: Role) -> None:
    try:
        await _call_tool(client, "receive_message", {"role": role.value})
    except Exception:
        return


def _load_fastmcp_client() -> tuple[Any, Any]:
    try:
        from fastmcp import Client
        from fastmcp.client.auth import BearerAuth
    except Exception as exc:
        raise FastMcpHostClientError(
            "FastMCP is not installed. Install it first, for example: "
            'python -m pip install "fastmcp>=2.0"'
        ) from exc
    return Client, BearerAuth


def _unwrap_fastmcp_result(result: Any) -> Any:
    for attr in ("structured_content", "structuredContent", "data"):
        value = getattr(result, attr, None)
        if value is not None:
            return value
    content = getattr(result, "content", None)
    if content:
        first = content[0]
        text = getattr(first, "text", None)
        if isinstance(text, str):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    if isinstance(result, dict):
        return result
    return result


def _as_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    raise FastMcpHostClientError(f"FastMCP tool returned non-object result: {value!r}")


def _status_is_done(status: dict[str, Any]) -> bool:
    for key in ("done", "is_done", "game_over", "finished"):
        if isinstance(status.get(key), bool):
            return bool(status[key])
    return False


def _status_active_role(status: dict[str, Any]) -> Role | None:
    for key in ("to_move", "active_role", "whose_turn", "turn", "current_turn", "role"):
        value = status.get(key)
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"cop", "thief"}:
                return Role(lowered)
    return None


def _grid_size_from_payload(payload: dict[str, Any]) -> list[int]:
    value = payload.get("grid_size", payload.get("grid"))
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, int) for item in value)
    ):
        return [5, 5]
    width, height = value
    return [height, width]


def _xy_to_row_col(value: Any) -> list[int]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, int) for item in value)
    ):
        raise FastMcpHostClientError(f"invalid [x,y] coordinate from FastMCP host: {value!r}")
    x, y = value
    return [y, x]


def _legal_actions_from_fastmcp(payload: dict[str, Any], role: Role) -> list[dict[str, Any]]:
    actions = payload.get("legal_actions")
    if isinstance(actions, list) and actions:
        converted: list[dict[str, Any]] = []
        for action in actions:
            converted_action = _convert_fastmcp_action(action)
            if converted_action is not None:
                converted.append(converted_action)
        if converted:
            return converted
    return _fallback_cardinal_moves(payload)


def _convert_fastmcp_action(action: Any) -> dict[str, Any] | None:
    if not isinstance(action, dict):
        return None
    action_type = str(action.get("type", action.get("kind", ""))).lower()
    if action_type == "stay":
        return None
    if action_type == "move":
        direction = action.get("direction")
        if isinstance(direction, str) and direction in {"up", "down", "left", "right"}:
            return {"type": "move", "direction": direction}
        dx = action.get("dx")
        dy = action.get("dy")
        direction_from_delta = _dx_dy_to_direction(dx, dy)
        if direction_from_delta is not None:
            return {"type": "move", "direction": direction_from_delta.value}
    if action_type == "place_barrier":
        target = action.get("target")
        if target is not None:
            return {"type": "place_barrier", "target": _xy_to_row_col(target)}
    return None


def _fallback_cardinal_moves(payload: dict[str, Any]) -> list[dict[str, str]]:
    grid_json = _grid_size_from_payload(payload)
    grid = GridSize.from_json(grid_json)
    self_position = Coordinate.from_json(
        _xy_to_row_col(payload.get("self_position", payload.get("self")))
    )
    barriers = {
        Coordinate.from_json(_xy_to_row_col(item))
        for item in payload.get("visible_barriers", [])
    }
    moves: list[dict[str, str]] = []
    for direction in (Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT):
        row_delta, column_delta = {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[direction]
        next_row = self_position.row + row_delta
        next_column = self_position.column + column_delta
        if next_row < 0 or next_column < 0:
            continue
        next_position = Coordinate(next_row, next_column)
        if grid.contains(next_position) and next_position not in barriers:
            moves.append({"type": "move", "direction": direction.value})
    if not moves:
        return [{"type": "move", "direction": Direction.UP.value}]
    return moves


def _direction_to_dx_dy(direction: Direction) -> tuple[int, int]:
    return {
        Direction.UP: (0, -1),
        Direction.DOWN: (0, 1),
        Direction.LEFT: (-1, 0),
        Direction.RIGHT: (1, 0),
    }[direction]


def _dx_dy_to_direction(dx: Any, dy: Any) -> Direction | None:
    mapping = {
        (0, -1): Direction.UP,
        (0, 1): Direction.DOWN,
        (-1, 0): Direction.LEFT,
        (1, 0): Direction.RIGHT,
    }
    return mapping.get((dx, dy))


def _int_from_any(payload: dict[str, Any], keys: tuple[str, ...], default: int) -> int:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return default


def _normalize_mcp_url(url: str) -> str:
    stripped = url.rstrip("/")
    return stripped if stripped.endswith("/mcp") else f"{stripped}/mcp"
