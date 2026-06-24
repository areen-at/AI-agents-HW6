from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_agents_hw6.application.events import atomic_write_json
from ai_agents_hw6.application.mcp_client import (
    LocalMcpDecisionProvider,
    McpClientError,
    RoleMcpClient,
    preflight_clients,
)
from ai_agents_hw6.application.series import (
    SeriesObserver,
    SeriesResult,
    SeriesSettings,
    run_series,
)
from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.domain import Role, ScoreMatrix
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION


class BonusPreflightError(RuntimeError):
    """Raised before any bonus game when the external boundary is unsafe."""


@dataclass(frozen=True)
class BonusCredentials:
    owned_cop_token: str | None
    owned_thief_token: str | None
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
        return cls(
            owned_cop_token=os.environ.get("COP_MCP_TOKEN"),
            owned_thief_token=os.environ.get("THIEF_MCP_TOKEN"),
            opponent_cop_token=cop_token,
            opponent_thief_token=thief_token,
        )


@dataclass(frozen=True)
class BonusMatchup:
    index: int
    cop_group: str
    thief_group: str
    cop_url: str
    thief_url: str


@dataclass(frozen=True)
class BonusMatchResult:
    series: SeriesResult
    schedule: tuple[BonusMatchup, ...]
    totals_by_group: dict[str, int]
    agreement_sha256: str


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


def build_bonus_schedule(config: AppConfig) -> tuple[BonusMatchup, ...]:
    ours = config.group.name
    opponent = config.bonus_opponent.group_name
    schedule = tuple(
        BonusMatchup(
            index=index,
            cop_group=ours if index <= 3 else opponent,
            thief_group=opponent if index <= 3 else ours,
            cop_url=(
                config.my_servers.cop_mcp_url if index <= 3 else config.bonus_opponent.cop_mcp_url
            ),
            thief_url=(
                config.bonus_opponent.thief_mcp_url
                if index <= 3
                else config.my_servers.thief_mcp_url
            ),
        )
        for index in range(1, 7)
    )
    validate_bonus_schedule(config, schedule)
    return schedule


def validate_bonus_schedule(
    config: AppConfig,
    schedule: tuple[BonusMatchup, ...],
) -> None:
    if len(schedule) != 6 or [item.index for item in schedule] != list(range(1, 7)):
        raise BonusPreflightError("bonus schedule must contain ordered game slots 1 through 6")
    ours = config.group.name
    opponent = config.bonus_opponent.group_name
    expected = [(ours, opponent)] * 3 + [(opponent, ours)] * 3
    actual = [(item.cop_group, item.thief_group) for item in schedule]
    if actual != expected:
        raise BonusPreflightError("bonus schedule must use the required 3+3 role assignment")
    expected_urls = [(config.my_servers.cop_mcp_url, config.bonus_opponent.thief_mcp_url)] * 3 + [
        (config.bonus_opponent.cop_mcp_url, config.my_servers.thief_mcp_url)
    ] * 3
    actual_urls = [(item.cop_url, item.thief_url) for item in schedule]
    if actual_urls != expected_urls:
        raise BonusPreflightError("bonus schedule endpoint ownership is reversed or duplicated")


def build_bonus_agreement(config: AppConfig) -> dict[str, Any]:
    schedule = build_bonus_schedule(config)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "groups": {
            config.group.name: {
                "github_repo": config.group.github_repo,
                "students": list(config.group.students),
            },
            config.bonus_opponent.group_name: {
                "github_repo": config.bonus_opponent.github_repo,
                "students": list(config.bonus_opponent.students),
            },
        },
        "endpoints": {
            "our_cop": config.my_servers.cop_mcp_url,
            "our_thief": config.my_servers.thief_mcp_url,
            "opponent_cop": config.bonus_opponent.cop_mcp_url,
            "opponent_thief": config.bonus_opponent.thief_mcp_url,
        },
        "rules": {
            "grid_size": list(config.game.grid_size),
            "max_moves": config.game.max_moves,
            "max_barriers": config.game.max_barriers,
            "manhattan_radius": config.observation.manhattan_radius,
            "scoring": {
                "cop_win": config.game.scoring.cop_win,
                "thief_win": config.game.scoring.thief_win,
                "cop_loss": config.game.scoring.cop_loss,
                "thief_loss": config.game.scoring.thief_loss,
            },
        },
        "runtime": {
            "base_seed": config.runtime.random_seed,
            "valid_slot_seeds": [
                config.runtime.random_seed + (index * 1000) + 1 for index in range(1, 7)
            ],
            "decision_timeout_seconds": config.runtime.decision_timeout_seconds,
            "max_retries": config.runtime.max_retries,
            "technical_attempt_limit_per_slot": (config.runtime.technical_attempt_limit_per_slot),
        },
        "schedule": [
            {
                "index": item.index,
                "cop_group": item.cop_group,
                "thief_group": item.thief_group,
                "cop_url": item.cop_url,
                "thief_url": item.thief_url,
            }
            for item in schedule
        ],
    }


def bonus_agreement_sha256(config: AppConfig) -> str:
    canonical = json.dumps(
        build_bonus_agreement(config),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def write_bonus_agreement(path: str | Path, config: AppConfig) -> str:
    agreement = build_bonus_agreement(config)
    digest = bonus_agreement_sha256(config)
    atomic_write_json(path, {"agreement_sha256": digest, "agreement": agreement})
    return digest


def require_confirmed_bonus_agreement(config: AppConfig) -> str:
    expected = bonus_agreement_sha256(config)
    confirmed = os.environ.get("BONUS_AGREEMENT_SHA256", "").strip().lower()
    if confirmed != expected:
        raise BonusPreflightError(
            "opponent agreement is not confirmed; exchange the agreement manifest and set "
            f"BONUS_AGREEMENT_SHA256={expected} only after both groups approve it"
        )
    return expected


def preflight_bonus_endpoints(
    config: AppConfig,
    *,
    credentials: BonusCredentials | None = None,
    client_factory: ClientFactory = RoleMcpClient,
) -> dict[str, RoleMcpClient]:
    auth = credentials or BonusCredentials.from_environment()
    timeout = config.runtime.decision_timeout_seconds
    clients = {
        "our_cop": client_factory(
            role=Role.COP,
            base_url=config.my_servers.cop_mcp_url.rstrip("/"),
            token=auth.owned_cop_token,
            timeout_seconds=timeout,
        ),
        "our_thief": client_factory(
            role=Role.THIEF,
            base_url=config.my_servers.thief_mcp_url.rstrip("/"),
            token=auth.owned_thief_token,
            timeout_seconds=timeout,
        ),
        "opponent_cop": client_factory(
            role=Role.COP,
            base_url=config.bonus_opponent.cop_mcp_url.rstrip("/"),
            token=auth.opponent_cop_token,
            timeout_seconds=timeout,
        ),
        "opponent_thief": client_factory(
            role=Role.THIEF,
            base_url=config.bonus_opponent.thief_mcp_url.rstrip("/"),
            token=auth.opponent_thief_token,
            timeout_seconds=timeout,
        ),
    }
    try:
        preflight_clients(clients["our_cop"], clients["our_thief"])
        preflight_clients(clients["opponent_cop"], clients["opponent_thief"])
    except McpClientError as exc:
        raise BonusPreflightError(f"four-endpoint preflight failed: {exc}") from exc
    return clients


def run_external_bonus_series(
    config: AppConfig,
    *,
    observer: SeriesObserver | None = None,
    credentials: BonusCredentials | None = None,
    client_factory: ClientFactory = RoleMcpClient,
    require_agreement: bool = True,
) -> BonusMatchResult:
    schedule = build_bonus_schedule(config)
    agreement_hash = (
        require_confirmed_bonus_agreement(config)
        if require_agreement
        else bonus_agreement_sha256(config)
    )
    clients = preflight_bonus_endpoints(
        config,
        credentials=credentials,
        client_factory=client_factory,
    )
    settings = SeriesSettings.from_config(config)
    settings = SeriesSettings(
        grid=settings.grid,
        num_games=settings.num_games,
        max_moves=settings.max_moves,
        max_barriers=settings.max_barriers,
        random_seed=settings.random_seed,
        technical_attempt_limit_per_slot=settings.technical_attempt_limit_per_slot,
        event_log_path=str(Path(config.logging.event_log_dir) / "bonus_events.json"),
    )
    providers: dict[int, LocalMcpDecisionProvider] = {}

    def provider_for_game(index: int) -> Any:
        if index not in providers:
            providers[index] = LocalMcpDecisionProvider(
                cop_client=clients["our_cop"] if index <= 3 else clients["opponent_cop"],
                thief_client=(clients["opponent_thief"] if index <= 3 else clients["our_thief"]),
                max_moves=settings.max_moves,
                max_barriers=settings.max_barriers,
                manhattan_radius=config.observation.manhattan_radius,
                max_retries=config.runtime.max_retries,
            )
        return providers[index].decide

    result = run_series(
        settings=settings,
        scoring=ScoreMatrix.from_config(config.game.scoring),
        decision_provider=provider_for_game(1),
        decision_provider_factory=provider_for_game,
        observer=observer,
    )
    if len(result.valid_sub_games) != 6:
        raise RuntimeError("bonus series did not produce exactly six valid games")
    totals = {config.group.name: 0, config.bonus_opponent.group_name: 0}
    for game, matchup in zip(result.valid_sub_games, schedule, strict=True):
        totals[matchup.cop_group] += game.cop_score
        totals[matchup.thief_group] += game.thief_score
    return BonusMatchResult(
        series=result,
        schedule=schedule,
        totals_by_group=totals,
        agreement_sha256=agreement_hash,
    )


def build_bonus_match_evidence(
    config: AppConfig,
    result: BonusMatchResult,
) -> dict[str, Any]:
    sub_games = []
    for game, matchup in zip(result.series.valid_sub_games, result.schedule, strict=True):
        sub_games.append(
            {
                "index": game.index,
                "sub_game_id": str(game.sub_game_id),
                "attempt_id": str(game.attempt_id),
                "attempt_number": game.attempt_number,
                "seed": game.seed,
                "cop_group": matchup.cop_group,
                "thief_group": matchup.thief_group,
                "cop_url": matchup.cop_url,
                "thief_url": matchup.thief_url,
                "move_count": game.move_count,
                "outcome": game.outcome,
                "terminal_reason": game.terminal_reason,
                "scores": {"cop": game.cop_score, "thief": game.thief_score},
                "final_state_hash": game.final_state_hash,
                "event_log_path": game.event_log_path,
            }
        )
    evidence = {
        "evidence_type": "bonus_match_result",
        "agreement_sha256": result.agreement_sha256,
        "series_id": str(result.series.series_id),
        "sub_games": sub_games,
        "invalid_attempts": [
            {
                "attempt_id": str(attempt.attempt_id),
                "attempt_number": attempt.attempt_number,
                "seed": attempt.seed,
                "failure_reason": (
                    attempt.failure_reason.value if attempt.failure_reason is not None else None
                ),
                "failure_detail": attempt.failure_detail,
            }
            for attempt in result.series.invalid_attempts
        ],
        "totals_by_group": result.totals_by_group,
        "event_log_path": str(Path(config.logging.event_log_dir) / "bonus_events.json"),
    }
    canonical = json.dumps(
        evidence,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    evidence["evidence_sha256"] = hashlib.sha256(canonical).hexdigest()
    return evidence


def write_bonus_match_evidence(path: str | Path, evidence: dict[str, Any]) -> None:
    if len(evidence.get("sub_games", [])) != 6:
        raise ValueError("bonus match evidence requires exactly six valid games")
    atomic_write_json(path, evidence)
