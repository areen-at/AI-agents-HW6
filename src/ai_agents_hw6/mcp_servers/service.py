from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from ai_agents_hw6.agents import HeuristicPolicy, heuristic_protocol_decision
from ai_agents_hw6.contracts import (
    ActionProtocolError,
    observation_from_public_json,
    parse_action_response,
    render_decision_prompt,
)
from ai_agents_hw6.domain import Role
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION, capabilities


class McpServerError(ValueError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class RoleDecisionService:
    role: Role
    token: str | None = None
    timeout_seconds: float = 10.0
    _seen_request_ids: set[str] = field(default_factory=set)

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "role": self.role.value,
            "protocol_version": PROTOCOL_VERSION,
        }

    def identity(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "server_name": f"ai-agents-hw6-{self.role.value}",
            "protocol_version": PROTOCOL_VERSION,
        }

    def capabilities(self) -> dict[str, Any]:
        return capabilities(self.role)

    def authorize(self, authorization: str | None) -> None:
        self._check_auth(authorization)

    def decide(self, payload: dict[str, Any], *, authorization: str | None = None) -> dict[str, Any]:
        started = time.monotonic()
        self._check_auth(authorization)
        request_id = _require_text(payload, "request_id")
        correlation_id = _require_text(payload, "correlation_id")
        if request_id in self._seen_request_ids:
            raise McpServerError("duplicate request_id", status_code=409)
        self._seen_request_ids.add(request_id)

        if payload.get("protocol_version") != PROTOCOL_VERSION:
            raise McpServerError("protocol version mismatch", status_code=409)
        if payload.get("role") != self.role.value:
            raise McpServerError("role mismatch", status_code=409)
        observation_payload = payload.get("observation")
        if not isinstance(observation_payload, dict):
            raise McpServerError("observation must be an object")

        try:
            observation = observation_from_public_json(observation_payload)
        except Exception as exc:
            raise McpServerError(f"malformed observation: {exc}") from exc

        if observation.role is not self.role:
            raise McpServerError("observation role mismatch", status_code=409)
        if observation.request_id != request_id:
            raise McpServerError("observation request_id mismatch", status_code=409)
        if observation.protocol_version != PROTOCOL_VERSION:
            raise McpServerError("observation protocol version mismatch", status_code=409)

        prompt = render_decision_prompt(observation)
        raw_response = heuristic_protocol_decision(observation, policy=HeuristicPolicy())
        try:
            parsed = parse_action_response(raw_response, observation)
        except ActionProtocolError as exc:
            raise McpServerError(f"policy returned invalid action: {exc}") from exc

        elapsed = time.monotonic() - started
        if elapsed > self.timeout_seconds:
            raise McpServerError("decision timeout", status_code=504)

        return {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "role": self.role.value,
            "prompt": prompt,
            "decision": json.loads(raw_response),
            "action": parsed.action,
            "elapsed_seconds": elapsed,
        }

    def _check_auth(self, authorization: str | None) -> None:
        if self.token is None:
            return
        expected = f"Bearer {self.token}"
        if authorization != expected:
            raise McpServerError("unauthorized", status_code=401)


def response_public_json(response: dict[str, Any]) -> dict[str, Any]:
    public = dict(response)
    public.pop("action", None)
    return public


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise McpServerError(f"{key} is required")
    return value.strip()
