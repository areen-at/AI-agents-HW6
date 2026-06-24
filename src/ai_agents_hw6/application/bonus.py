from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from ai_agents_hw6.application.mcp_client import McpClientError, RoleMcpClient, preflight_clients
from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.domain import Role


class BonusPreflightError(RuntimeError):
    """Raised before any bonus game when the external boundary is unsafe."""


@dataclass(frozen=True)
class BonusCredentials:
    opponent_cop_token: str
    opponent_thief_token: str

    @classmethod
    def from_environment(cls) -> BonusCredentials:
        missing: list[str] = []
        cop_token = os.environ.get("OPPONENT_COP_MCP_TOKEN", "").strip()
        thief_token = os.environ.get("OPPONENT_THIEF_MCP_TOKEN", "").strip()
        if not cop_token:
            missing.append("OPPONENT_COP_MCP_TOKEN")
        if not thief_token:
            missing.append("OPPONENT_THIEF_MCP_TOKEN")
        if missing:
            raise BonusPreflightError(
                "missing opponent authentication environment variables: " + ", ".join(missing)
            )
        return cls(opponent_cop_token=cop_token, opponent_thief_token=thief_token)


ClientFactory = Callable[..., RoleMcpClient]


def preflight_bonus_opponent(
    config: AppConfig,
    *,
    credentials: BonusCredentials | None = None,
    client_factory: ClientFactory = RoleMcpClient,
) -> None:
    """Verify external authentication, role identity, and protocol before games exist."""

    auth = credentials or BonusCredentials.from_environment()
    opponent = config.bonus_opponent
    cop_client = client_factory(
        role=Role.COP,
        base_url=opponent.cop_mcp_url.rstrip("/"),
        token=auth.opponent_cop_token,
        timeout_seconds=config.runtime.decision_timeout_seconds,
    )
    thief_client = client_factory(
        role=Role.THIEF,
        base_url=opponent.thief_mcp_url.rstrip("/"),
        token=auth.opponent_thief_token,
        timeout_seconds=config.runtime.decision_timeout_seconds,
    )
    try:
        preflight_clients(cop_client, thief_client)
    except McpClientError as exc:
        raise BonusPreflightError(f"opponent MCP preflight failed: {exc}") from exc
