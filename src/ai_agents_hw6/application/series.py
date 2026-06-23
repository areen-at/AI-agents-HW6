from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ai_agents_hw6.application.events import (
    EventLog,
    action_to_json,
    atomic_write_json,
    role_action_to_json,
    score_to_json,
    state_hash,
    state_to_json,
)
from ai_agents_hw6.agents import heuristic_protocol_decision_provider
from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.domain import (
    AttemptId,
    GameAction,
    GameState,
    GridSize,
    Role,
    ScoreMatrix,
    SeriesId,
    SubGameId,
    TechnicalFailureReason,
    apply_action,
    create_initial_state,
    legal_actions,
    replay_actions,
    score_state,
)


DecisionProvider = Callable[[GameState], GameAction]


class TechnicalFailure(RuntimeError):
    def __init__(self, reason: TechnicalFailureReason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class AttemptRecord:
    attempt_id: AttemptId
    attempt_number: int
    seed: int
    valid: bool
    failure_reason: TechnicalFailureReason | None
    failure_detail: str | None
    event_log_path: str | None = None


@dataclass(frozen=True)
class SubGameRecord:
    index: int
    sub_game_id: SubGameId
    attempt_id: AttemptId
    attempt_number: int
    seed: int
    move_count: int
    outcome: str
    terminal_reason: str
    cop_score: int
    thief_score: int
    final_state_hash: str
    accepted_actions: tuple[tuple[Role, GameAction], ...]
    event_log_path: str | None = None


@dataclass(frozen=True)
class SeriesResult:
    series_id: SeriesId
    valid_sub_games: tuple[SubGameRecord, ...]
    invalid_attempts: tuple[AttemptRecord, ...]
    events: tuple[dict, ...]
    totals: dict[str, int]


@dataclass(frozen=True)
class SeriesSettings:
    grid: GridSize
    num_games: int = 6
    max_moves: int = 25
    max_barriers: int = 5
    random_seed: int = 12345
    technical_attempt_limit_per_slot: int = 10
    event_log_path: str | None = None

    @classmethod
    def from_config(cls, config: AppConfig) -> "SeriesSettings":
        return cls(
            grid=GridSize(*config.game.grid_size),
            num_games=config.game.num_games,
            max_moves=config.game.max_moves,
            max_barriers=config.game.max_barriers,
            random_seed=config.runtime.random_seed,
            technical_attempt_limit_per_slot=config.runtime.technical_attempt_limit_per_slot,
            event_log_path=str(Path(config.logging.event_log_dir) / "engine_only_events.json"),
        )


def run_series(
    *,
    settings: SeriesSettings,
    scoring: ScoreMatrix,
    decision_provider: DecisionProvider,
) -> SeriesResult:
    if settings.num_games != 6:
        raise ValueError("Phase 4 production series requires exactly six valid games")
    if settings.technical_attempt_limit_per_slot <= 0:
        raise ValueError("technical attempt limit must be positive")

    series_id = SeriesId.new()
    event_log = EventLog()
    valid_games: list[SubGameRecord] = []
    invalid_attempts: list[AttemptRecord] = []

    for valid_game_index in range(1, settings.num_games + 1):
        sub_game_id = SubGameId.new()
        completed = False

        for attempt_number in range(1, settings.technical_attempt_limit_per_slot + 1):
            attempt_id = AttemptId.new()
            seed = _attempt_seed(settings.random_seed, valid_game_index, attempt_number)
            state = create_initial_state(
                grid=settings.grid,
                seed=seed,
                series_id=series_id,
                sub_game_id=sub_game_id,
                attempt_id=attempt_id,
            )
            accepted_actions: list[tuple[Role, GameAction]] = []
            event_log.append(
                event_type="attempt_started",
                state=state,
                valid_game_index=valid_game_index,
                attempt_number=attempt_number,
                payload={"state_hash": state_hash(state), "state": state_to_json(state)},
            )

            try:
                while not state.is_terminal:
                    role = state.active_role
                    before = state
                    action = decision_provider(state)
                    after = apply_action(
                        state,
                        role=role,
                        action=action,
                        max_moves=settings.max_moves,
                        max_barriers=settings.max_barriers,
                    )
                    accepted_actions.append((role, action))
                    event_log.append(
                        event_type="action_applied",
                        state=after,
                        valid_game_index=valid_game_index,
                        attempt_number=attempt_number,
                        payload={
                            "request_id": None,
                            "correlation_id": None,
                            "role": role.value,
                            "action": action_to_json(action),
                            "validation": "accepted",
                            "before_state_hash": state_hash(before),
                            "after_state_hash": state_hash(after),
                        },
                    )
                    state = after
            except TechnicalFailure as exc:
                invalid_attempts.append(
                    _record_invalid_attempt(
                        attempt_id=attempt_id,
                        attempt_number=attempt_number,
                        seed=seed,
                        reason=exc.reason,
                        detail=exc.detail,
                        event_log_path=settings.event_log_path,
                    )
                )
                event_log.append(
                    event_type="attempt_invalid",
                    state=state,
                    valid_game_index=valid_game_index,
                    attempt_number=attempt_number,
                    payload={"failure_reason": exc.reason.value, "failure_detail": exc.detail},
                )
                continue
            except Exception as exc:
                invalid_attempts.append(
                    _record_invalid_attempt(
                        attempt_id=attempt_id,
                        attempt_number=attempt_number,
                        seed=seed,
                        reason=TechnicalFailureReason.APPLICATION_ERROR,
                        detail=str(exc),
                        event_log_path=settings.event_log_path,
                    )
                )
                event_log.append(
                    event_type="attempt_invalid",
                    state=state,
                    valid_game_index=valid_game_index,
                    attempt_number=attempt_number,
                    payload={
                        "failure_reason": TechnicalFailureReason.APPLICATION_ERROR.value,
                        "failure_detail": str(exc),
                    },
                )
                continue

            score = score_state(state, scoring)
            replayed = replay_actions(
                create_initial_state(
                    grid=settings.grid,
                    seed=seed,
                    series_id=series_id,
                    sub_game_id=sub_game_id,
                    attempt_id=attempt_id,
                ),
                tuple(accepted_actions),
                max_moves=settings.max_moves,
                max_barriers=settings.max_barriers,
            )
            if state_hash(replayed) != state_hash(state):
                raise RuntimeError("replay verification failed for valid sub-game")

            event_log.append(
                event_type="sub_game_finished",
                state=state,
                valid_game_index=valid_game_index,
                attempt_number=attempt_number,
                payload={
                    "state_hash": state_hash(state),
                    "terminal_outcome": state.terminal_outcome.value if state.terminal_outcome else None,
                    "terminal_reason": state.terminal_reason.value if state.terminal_reason else None,
                    "move_count": state.move_round,
                    "score": score_to_json(score),
                    "accepted_actions": [
                        role_action_to_json(role, action) for role, action in accepted_actions
                    ],
                },
            )
            valid_games.append(
                SubGameRecord(
                    index=valid_game_index,
                    sub_game_id=sub_game_id,
                    attempt_id=attempt_id,
                    attempt_number=attempt_number,
                    seed=seed,
                    move_count=state.move_round,
                    outcome=state.terminal_outcome.value if state.terminal_outcome else "",
                    terminal_reason=state.terminal_reason.value if state.terminal_reason else "",
                    cop_score=score.cop,
                    thief_score=score.thief,
                    final_state_hash=state_hash(state),
                    accepted_actions=tuple(accepted_actions),
                    event_log_path=settings.event_log_path,
                )
            )
            completed = True
            break

        if not completed:
            raise RuntimeError(
                f"technical attempt limit reached for valid game slot {valid_game_index}"
            )

    result = SeriesResult(
        series_id=series_id,
        valid_sub_games=tuple(valid_games),
        invalid_attempts=tuple(invalid_attempts),
        events=tuple(event_log.to_json()),
        totals={
            "cop": sum(game.cop_score for game in valid_games),
            "thief": sum(game.thief_score for game in valid_games),
        },
    )

    if settings.event_log_path:
        atomic_write_json(settings.event_log_path, result.events)
    return result


def first_legal_action_provider(state: GameState) -> GameAction:
    actions = legal_actions(state)
    if not actions:
        raise TechnicalFailure(
            TechnicalFailureReason.APPLICATION_ERROR,
            "no legal actions available",
        )
    return actions[0]


def write_engine_only_series(config: AppConfig) -> SeriesResult:
    return write_engine_only_series_with_policy(config, policy_name="heuristic")


def write_engine_only_series_with_policy(config: AppConfig, *, policy_name: str) -> SeriesResult:
    settings = SeriesSettings.from_config(config)
    scoring = ScoreMatrix.from_config(config.game.scoring)
    if policy_name == "first-legal":
        decision_provider = first_legal_action_provider
    elif policy_name == "heuristic":
        decision_provider = heuristic_protocol_decision_provider(max_barriers=settings.max_barriers)
    else:
        raise ValueError(f"unknown engine-only policy: {policy_name}")
    return run_series(
        settings=settings,
        scoring=scoring,
        decision_provider=decision_provider,
    )


def _attempt_seed(base_seed: int, valid_game_index: int, attempt_number: int) -> int:
    return base_seed + (valid_game_index * 1000) + attempt_number


def _record_invalid_attempt(
    *,
    attempt_id: AttemptId,
    attempt_number: int,
    seed: int,
    reason: TechnicalFailureReason,
    detail: str,
    event_log_path: str | None,
) -> AttemptRecord:
    return AttemptRecord(
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        seed=seed,
        valid=False,
        failure_reason=reason,
        failure_detail=detail,
        event_log_path=event_log_path,
    )
