from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from ai_agents_hw6.config import AppConfig
from ai_agents_hw6.reporting.bonus_report import (
    BONUS_MOCK_REPORT_TYPE,
    BONUS_MOCK_WARNING,
    write_mock_bonus_report,
)

T = TypeVar("T")


class DeterministicBonusMock:
    """Local test double only; it never hosts or impersonates an opponent service."""

    @staticmethod
    def decide(legal_actions: Sequence[T]) -> T:
        if not legal_actions:
            raise ValueError("mock decision requires at least one legal action")
        return legal_actions[0]


def build_bonus_mock_report(config: AppConfig) -> dict[str, Any]:
    our_group = config.group.name
    mock_group = "TEST-ONLY-MOCK-OPPONENT"
    sub_games = []
    for index in range(1, 7):
        direction = "our_cop_vs_mock_thief" if index <= 3 else "mock_cop_vs_our_thief"
        sub_games.append(
            {
                "index": index,
                "seed": config.runtime.random_seed + index - 1,
                "matchup_direction": direction,
                "test_only": True,
                "valid": True,
                "outcome": "mock_no_contest",
                "scores": {our_group: 0, mock_group: 0},
            }
        )
    return {
        "report_type": BONUS_MOCK_REPORT_TYPE,
        "test_only": True,
        "warning": BONUS_MOCK_WARNING,
        "groups": {"group_1": our_group, "group_2": mock_group},
        "github_repo_group_1": config.group.github_repo,
        "github_repo_group_2": "TEST-ONLY-NO-REPOSITORY",
        "mcp_url_group_1_cop": config.my_servers.cop_mcp_url,
        "mcp_url_group_1_thief": config.my_servers.thief_mcp_url,
        "mcp_url_group_2_cop": "TEST-ONLY-IN-PROCESS-MOCK",
        "mcp_url_group_2_thief": "TEST-ONLY-IN-PROCESS-MOCK",
        "timezone": config.runtime.timezone,
        "students_group_1": list(config.group.students),
        "students_group_2": [],
        "sub_games": sub_games,
        "totals_by_group": {our_group: 0, mock_group: 0},
        "bonus_claim": {our_group: 0, mock_group: 0},
        "mutual_agreement": False,
    }


def run_bonus_mock(config: AppConfig) -> dict[str, Any]:
    report = build_bonus_mock_report(config)
    write_mock_bonus_report(config, report)
    return report
