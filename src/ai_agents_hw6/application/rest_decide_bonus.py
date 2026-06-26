from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from ai_agents_hw6.agents import heuristic_decision_provider
from ai_agents_hw6.application.bonus import (
    BonusMatchResult,
    bonus_agreement_sha256,
    build_bonus_schedule,
)
from ai_agents_hw6.application.series import (
    SeriesObserver,
    SeriesSettings,
    TechnicalFailure,
    run_series,
)
from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.contracts import build_observation, parse_action_response
from ai_agents_hw6.domain import GameAction, GameState, Role, ScoreMatrix, TechnicalFailureReason
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION


class RestDecideBonusError(RuntimeError):
    """Raised when the opponent REST /decide flow is not configured or fails."""


@dataclass(frozen=True)
class RestDecideSettings:
    decide_url: str
    token: str | None
    timeout_seconds: int
    max_retries: int

    @classmethod
    def from_environment(cls, config: AppConfig) -> RestDecideSettings:
        decide_url = os.environ.get("OPPONENT_DECIDE_URL", "").strip()
        if not decide_url:
            raise RestDecideBonusError("missing OPPONENT_DECIDE_URL")
        token = os.environ.get("OPPONENT_DECIDE_TOKEN", "").strip() or None
        return cls(
            decide_url=decide_url,
            token=token,
            timeout_seconds=config.runtime.decision_timeout_seconds,
            max_retries=config.runtime.max_retries,
        )


@dataclass
class RestDecideClient:
    settings: RestDecideSettings

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.settings.token:
            headers["Authorization"] = f"Bearer {self.settings.token}"
        request = Request(
            self.settings.decide_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RestDecideBonusError(
                f"opponent /decide returned HTTP {exc.code}: {detail[:300]}"
            ) from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise RestDecideBonusError(f"opponent /decide unavailable: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RestDecideBonusError("opponent /decide returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise RestDecideBonusError("opponent /decide returned non-object JSON")
        return decoded


@dataclass
class MixedRestDecideProvider:
    opponent_client: RestDecideClient
    opponent_role: Role
    max_moves: int
    max_barriers: int
    manhattan_radius: int
    max_retries: int
    local_decide: Any = field(init=False)
    last_request_id: str | None = None
    last_correlation_id: str | None = None

    def __post_init__(self) -> None:
        self.local_decide = heuristic_decision_provider(max_barriers=self.max_barriers)

    def decide(self, state: GameState) -> GameAction:
        self.last_request_id = None
        self.last_correlation_id = None
        if state.active_role is not self.opponent_role:
            return self.local_decide(state)

        request_id = str(uuid4())
        correlation_id = str(uuid4())
        observation = build_observation(
            state,
            request_id=request_id,
            role=state.active_role,
            manhattan_radius=self.manhattan_radius,
            max_moves=self.max_moves,
            max_barriers=self.max_barriers,
        )
        payload = {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "role": state.active_role.value,
            "observation": observation.to_public_json(),
        }

        last_error: Exception | None = None
        for _attempt in range(self.max_retries + 1):
            try:
                response = self.opponent_client.decide(payload)
                decision = response.get("decision", response)
                parsed = parse_action_response(json.dumps(decision), observation)
                self.last_request_id = request_id
                self.last_correlation_id = correlation_id
                return parsed.action
            except Exception as exc:
                last_error = exc
        raise TechnicalFailure(
            TechnicalFailureReason.MCP_TIMEOUT,
            f"exhausted opponent /decide retries for {state.active_role.value}: {last_error}",
        )


def run_rest_decide_bonus_series(
    config: AppConfig,
    *,
    observer: SeriesObserver | None = None,
    settings: RestDecideSettings | None = None,
) -> BonusMatchResult:
    schedule = build_bonus_schedule(config)
    decide_settings = settings or RestDecideSettings.from_environment(config)
    client = RestDecideClient(decide_settings)
    series_settings = SeriesSettings.from_config(config)
    series_settings = SeriesSettings(
        grid=series_settings.grid,
        num_games=series_settings.num_games,
        max_moves=series_settings.max_moves,
        max_barriers=series_settings.max_barriers,
        random_seed=series_settings.random_seed,
        technical_attempt_limit_per_slot=series_settings.technical_attempt_limit_per_slot,
        event_log_path=str(Path(config.logging.event_log_dir) / "bonus_rest_decide_events.json"),
    )
    providers: dict[int, MixedRestDecideProvider] = {}

    def provider_for_game(index: int) -> Any:
        if index not in providers:
            opponent_role = Role.THIEF if index <= 3 else Role.COP
            providers[index] = MixedRestDecideProvider(
                opponent_client=client,
                opponent_role=opponent_role,
                max_moves=series_settings.max_moves,
                max_barriers=series_settings.max_barriers,
                manhattan_radius=config.observation.manhattan_radius,
                max_retries=decide_settings.max_retries,
            )
        return providers[index].decide

    result = run_series(
        settings=series_settings,
        scoring=ScoreMatrix.from_config(config.game.scoring),
        decision_provider=provider_for_game(1),
        decision_provider_factory=provider_for_game,
        observer=observer,
    )
    totals = {config.group.name: 0, config.bonus_opponent.group_name: 0}
    for game, matchup in zip(result.valid_sub_games, schedule, strict=True):
        totals[matchup.cop_group] += game.cop_score
        totals[matchup.thief_group] += game.thief_score
    return BonusMatchResult(
        series=result,
        schedule=schedule,
        totals_by_group=totals,
        agreement_sha256=_rest_decide_agreement_sha256(config, decide_settings.decide_url),
    )


def _rest_decide_agreement_sha256(config: AppConfig, decide_url: str) -> str:
    canonical = {
        "base_agreement_sha256": bonus_agreement_sha256(config),
        "opponent_decide_url": decide_url,
        "transport": "rest-decide",
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
