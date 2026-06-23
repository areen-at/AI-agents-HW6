from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_agents_hw6.application.events import atomic_write_json
from ai_agents_hw6.application.series import SeriesResult
from ai_agents_hw6.config import AppConfig


def build_internal_report(config: AppConfig, result: SeriesResult) -> dict[str, Any]:
    if len(result.valid_sub_games) != 6:
        raise ValueError("internal report requires exactly six valid sub-games")

    sub_games = [
        {
            "index": game.index,
            "sub_game_id": str(game.sub_game_id),
            "attempt_id": str(game.attempt_id),
            "attempt_number": game.attempt_number,
            "seed": game.seed,
            "move_count": game.move_count,
            "outcome": game.outcome,
            "terminal_reason": game.terminal_reason,
            "scores": {"cop": game.cop_score, "thief": game.thief_score},
            "final_state_hash": game.final_state_hash,
            "event_log_path": game.event_log_path,
        }
        for game in result.valid_sub_games
    ]
    totals = {
        "cop": sum(game.cop_score for game in result.valid_sub_games),
        "thief": sum(game.thief_score for game in result.valid_sub_games),
    }
    return {
        "group_name": config.group.name,
        "students": list(config.group.students),
        "github_repo": config.group.github_repo,
        "cop_mcp_url": config.my_servers.cop_mcp_url,
        "thief_mcp_url": config.my_servers.thief_mcp_url,
        "timezone": config.runtime.timezone,
        "series_id": str(result.series_id),
        "sub_games": sub_games,
        "invalid_attempts": [
            {
                "attempt_id": str(attempt.attempt_id),
                "attempt_number": attempt.attempt_number,
                "seed": attempt.seed,
                "valid": attempt.valid,
                "failure_reason": attempt.failure_reason.value if attempt.failure_reason else None,
                "failure_detail": attempt.failure_detail,
                "event_log_path": attempt.event_log_path,
            }
            for attempt in result.invalid_attempts
        ],
        "totals": totals,
    }


def write_internal_report(path: str | Path, report: dict[str, Any]) -> None:
    if len(report.get("sub_games", [])) != 6:
        raise ValueError("internal report must contain exactly six sub_games")
    atomic_write_json(path, report)
