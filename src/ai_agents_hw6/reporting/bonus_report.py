from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_agents_hw6.application.events import atomic_write_json
from ai_agents_hw6.config import AppConfig

BONUS_REPORT_TYPE = "bonus_game"
BONUS_MOCK_REPORT_TYPE = "bonus_game_mock"
BONUS_MOCK_WARNING = "TEST-ONLY BONUS MOCK — NOT PRODUCTION EVIDENCE"


def validate_bonus_report(report: dict[str, Any], *, allow_mock: bool = False) -> None:
    report_type = report.get("report_type")
    expected_type = BONUS_MOCK_REPORT_TYPE if allow_mock else BONUS_REPORT_TYPE
    if report_type != expected_type:
        raise ValueError(f"bonus report_type must be {expected_type!r}")
    required = (
        "groups",
        "github_repo_group_1",
        "github_repo_group_2",
        "mcp_url_group_1_cop",
        "mcp_url_group_1_thief",
        "mcp_url_group_2_cop",
        "mcp_url_group_2_thief",
        "students_group_1",
        "students_group_2",
        "sub_games",
        "totals_by_group",
        "bonus_claim",
        "mutual_agreement",
    )
    missing = [field for field in required if field not in report]
    if missing:
        raise ValueError("bonus report missing fields: " + ", ".join(missing))
    if len(report["sub_games"]) != 6:
        raise ValueError("bonus report must contain exactly six sub_games")
    if not isinstance(report["mutual_agreement"], bool):
        raise ValueError("mutual_agreement must be a boolean")

    if allow_mock:
        if report.get("test_only") is not True:
            raise ValueError("mock bonus report must be marked test_only")
        if report["mutual_agreement"] is not False:
            raise ValueError("mock bonus report cannot claim mutual agreement")
        if any(value != 0 for value in report["bonus_claim"].values()):
            raise ValueError("mock bonus report cannot claim bonus points")
        if report.get("warning") != BONUS_MOCK_WARNING:
            raise ValueError("mock bonus report must contain the test-only warning")
    elif report.get("test_only") is True:
        raise ValueError("production bonus report cannot be marked test_only")


def write_mock_bonus_report(config: AppConfig, report: dict[str, Any]) -> None:
    validate_bonus_report(report, allow_mock=True)
    production = Path(config.reports.bonus_game_report).resolve()
    mock = Path(config.reports.bonus_mock_report).resolve()
    if production == mock:
        raise ValueError("mock report path must be distinct from production bonus report path")
    atomic_write_json(mock, report)


def write_production_bonus_report(config: AppConfig, report: dict[str, Any]) -> None:
    validate_bonus_report(report)
    atomic_write_json(config.reports.bonus_game_report, report)
