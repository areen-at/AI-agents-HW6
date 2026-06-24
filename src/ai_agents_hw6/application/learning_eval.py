from __future__ import annotations

from dataclasses import replace
from typing import Any

from ai_agents_hw6.agents import (
    QLearningPolicy,
    heuristic_protocol_decision_provider,
    policy_decision_provider,
)
from ai_agents_hw6.application.events import atomic_write_json
from ai_agents_hw6.application.series import SeriesResult, SeriesSettings, run_series
from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.domain import ScoreMatrix


def evaluate_learning(config: AppConfig) -> dict[str, Any]:
    """Compare optional learning against the fixed heuristic with evaluation-only seeds."""

    baseline_settings = replace(
        SeriesSettings.from_config(config),
        random_seed=config.learning.evaluation_seed,
        event_log_path=None,
    )
    scoring = ScoreMatrix.from_config(config.game.scoring)
    baseline = run_series(
        settings=baseline_settings,
        scoring=scoring,
        decision_provider=heuristic_protocol_decision_provider(
            max_barriers=baseline_settings.max_barriers
        ),
    )
    learning_policy = QLearningPolicy(replace(config.learning, enabled=True, epsilon=0.0))
    learning_policy.load()
    learned = run_series(
        settings=baseline_settings,
        scoring=scoring,
        decision_provider=policy_decision_provider(
            learning_policy,
            max_barriers=baseline_settings.max_barriers,
        ),
    )
    baseline_metrics = _metrics(baseline)
    learning_metrics = _metrics(learned)
    reliable = (
        learning_metrics["technical_failures"] <= baseline_metrics["technical_failures"]
        and learning_metrics["illegal_actions"] <= baseline_metrics["illegal_actions"]
    )
    return {
        "evaluation_seed": config.learning.evaluation_seed,
        "training_seed": config.learning.training_seed,
        "baseline": baseline_metrics,
        "learning": learning_metrics,
        "reliability_regressed": not reliable,
        "recommended_runtime_policy": "q-learning" if reliable else "heuristic",
    }


def write_learning_evaluation(path: str, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def _metrics(result: SeriesResult) -> dict[str, Any]:
    games = result.valid_sub_games
    return {
        "scores": dict(result.totals),
        "technical_failures": len(result.invalid_attempts),
        "illegal_actions": sum(
            1
            for attempt in result.invalid_attempts
            if attempt.failure_reason is not None
            and attempt.failure_reason.value == "illegal_action_after_repair"
        ),
        "average_moves": (sum(game.move_count for game in games) / len(games) if games else 0.0),
        "valid_games": len(games),
    }
