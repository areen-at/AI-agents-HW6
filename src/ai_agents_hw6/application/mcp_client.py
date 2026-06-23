from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from ai_agents_hw6.application.series import SeriesResult, SeriesSettings, TechnicalFailure, run_series
from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.contracts import build_observation, parse_action_response
from ai_agents_hw6.domain import GameAction, GameState, Role, ScoreMatrix, TechnicalFailureReason
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION


class McpClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class McpClientConfig:
    cop_url: str
    thief_url: str
    cop_token: str | None = None
    thief_token: str | None = None
    timeout_seconds: int = 20
    max_retries: int = 2

    @classmethod
    def from_config(cls, config: AppConfig) -> "McpClientConfig":
        return cls(
            cop_url=config.my_servers.cop_mcp_url.rstrip("/"),
            thief_url=config.my_servers.thief_mcp_url.rstrip("/"),
            cop_token=os.environ.get("COP_MCP_TOKEN"),
            thief_token=os.environ.get("THIEF_MCP_TOKEN"),
            timeout_seconds=config.runtime.decision_timeout_seconds,
            max_retries=config.runtime.max_retries,
        )


@dataclass
class RoleMcpClient:
    role: Role
    base_url: str
    token: str | None = None
    timeout_seconds: int = 20

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def identity(self) -> dict[str, Any]:
        return self._get("/identity")

    def capabilities(self) -> dict[str, Any]:
        return self._get("/capabilities")

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/decide", payload)

    def _get(self, path: str) -> dict[str, Any]:
        return self._request(path=path, method="GET")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(path=path, method="POST", payload=payload)

    def _request(
        self,
        *,
        path: str,
        method: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("error", str(exc))
            except Exception:
                detail = str(exc)
            raise McpClientError(f"{self.role.value} server returned HTTP {exc.code}: {detail}") from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise McpClientError(f"{self.role.value} server unavailable: {exc}") from exc
        if not isinstance(decoded, dict):
            raise McpClientError(f"{self.role.value} server returned non-object JSON")
        return decoded


@dataclass
class LocalMcpDecisionProvider:
    cop_client: RoleMcpClient
    thief_client: RoleMcpClient
    max_moves: int
    max_barriers: int
    manhattan_radius: int
    max_retries: int = 2
    _applied_request_ids: set[str] = field(default_factory=set)

    def decide(self, state: GameState) -> GameAction:
        role = state.active_role
        client = self.cop_client if role is Role.COP else self.thief_client
        request_id = str(uuid4())
        correlation_id = str(uuid4())
        observation = build_observation(
            state,
            request_id=request_id,
            role=role,
            manhattan_radius=self.manhattan_radius,
            max_moves=self.max_moves,
            max_barriers=self.max_barriers,
        )
        payload = {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "role": role.value,
            "observation": observation.to_public_json(),
        }

        last_error: Exception | None = None
        for _attempt in range(self.max_retries + 1):
            try:
                response = client.decide(payload)
                if response.get("request_id") in self._applied_request_ids:
                    raise TechnicalFailure(
                        TechnicalFailureReason.PROTOCOL_MISMATCH,
                        "duplicate response request_id",
                    )
                if response.get("correlation_id") != correlation_id:
                    raise McpClientError("correlation_id mismatch")
                parsed = parse_action_response(json.dumps(response.get("decision")), observation)
                self._applied_request_ids.add(request_id)
                return parsed.action
            except TechnicalFailure:
                raise
            except Exception as exc:
                last_error = exc
        raise TechnicalFailure(
            TechnicalFailureReason.MCP_TIMEOUT,
            f"exhausted MCP decision retries for {role.value}: {last_error}",
        )


def preflight_clients(cop_client: RoleMcpClient, thief_client: RoleMcpClient) -> None:
    for expected_role, client in ((Role.COP, cop_client), (Role.THIEF, thief_client)):
        health = client.health()
        identity = client.identity()
        capabilities = client.capabilities()
        if health.get("status") != "ok":
            raise McpClientError(f"{expected_role.value} health check failed")
        if identity.get("role") != expected_role.value:
            raise McpClientError(f"{expected_role.value} identity mismatch")
        if capabilities.get("protocol_version") != PROTOCOL_VERSION:
            raise McpClientError(f"{expected_role.value} protocol mismatch")
        if "decide" not in capabilities.get("operations", []):
            raise McpClientError(f"{expected_role.value} missing decide capability")


def run_local_mcp_series(config: AppConfig) -> SeriesResult:
    client_config = McpClientConfig.from_config(config)
    cop_client = RoleMcpClient(
        role=Role.COP,
        base_url=client_config.cop_url,
        token=client_config.cop_token,
        timeout_seconds=client_config.timeout_seconds,
    )
    thief_client = RoleMcpClient(
        role=Role.THIEF,
        base_url=client_config.thief_url,
        token=client_config.thief_token,
        timeout_seconds=client_config.timeout_seconds,
    )
    preflight_clients(cop_client, thief_client)
    settings = SeriesSettings.from_config(config)
    provider = LocalMcpDecisionProvider(
        cop_client=cop_client,
        thief_client=thief_client,
        max_moves=settings.max_moves,
        max_barriers=settings.max_barriers,
        manhattan_radius=config.observation.manhattan_radius,
        max_retries=client_config.max_retries,
    )
    return run_series(
        settings=settings,
        scoring=ScoreMatrix.from_config(config.game.scoring),
        decision_provider=provider.decide,
    )
