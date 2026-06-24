from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from ai_agents_hw6.config import AppConfig, bonus_configuration_errors

BONUS_REPORT_TYPE = "bonus_game"
BONUS_MOCK_REPORT_TYPE = "bonus_game_mock"
BONUS_MOCK_WARNING = "TEST-ONLY BONUS MOCK - NOT PRODUCTION EVIDENCE"


class BonusReportError(ValueError):
    """Raised when bonus evidence, approval, or final report data is unsafe."""


def _atomic_write_json(path: str | Path, payload: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
        suffix=".tmp",
    ) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def load_bonus_match_evidence(path: str | Path) -> dict[str, Any]:
    evidence_path = Path(path)
    if not evidence_path.exists():
        raise BonusReportError(f"bonus match evidence not found: {evidence_path}")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BonusReportError(f"bonus match evidence is invalid JSON: {exc}") from exc
    if not isinstance(evidence, dict):
        raise BonusReportError("bonus match evidence root must be an object")
    claimed = evidence.get("evidence_sha256")
    unsigned = dict(evidence)
    unsigned.pop("evidence_sha256", None)
    actual = payload_sha256(unsigned)
    if claimed != actual:
        raise BonusReportError("bonus match evidence checksum mismatch")
    if len(evidence.get("sub_games", [])) != 6:
        raise BonusReportError("bonus match evidence must contain exactly six games")
    return evidence


def calculate_bonus_claim(totals: dict[str, int]) -> dict[str, int]:
    if len(totals) != 2:
        raise BonusReportError("bonus totals must contain exactly two groups")
    first, second = list(totals)
    if totals[first] == totals[second]:
        return {first: 5, second: 5}
    winner, loser = (first, second) if totals[first] > totals[second] else (second, first)
    return {winner: 10, loser: 7}


def build_bonus_report_candidate(
    config: AppConfig,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    errors = bonus_configuration_errors(config)
    if errors:
        raise BonusReportError("real opponent metadata is required: " + "; ".join(errors))
    if config.runtime.timezone != "Asia/Jerusalem":
        raise BonusReportError("bonus report timezone must be Asia/Jerusalem")
    totals = evidence.get("totals_by_group")
    if not isinstance(totals, dict) or not all(
        isinstance(key, str)
        and isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
        for key, value in totals.items()
    ):
        raise BonusReportError("bonus evidence totals_by_group must contain non-negative integers")
    expected_groups = {config.group.name, config.bonus_opponent.group_name}
    if set(totals) != expected_groups:
        raise BonusReportError("bonus evidence groups do not match configured groups")
    report = {
        "report_type": BONUS_REPORT_TYPE,
        "groups": {
            "group_1": config.group.name,
            "group_2": config.bonus_opponent.group_name,
        },
        "github_repo_group_1": config.group.github_repo,
        "github_repo_group_2": config.bonus_opponent.github_repo,
        "mcp_url_group_1_cop": config.my_servers.cop_mcp_url,
        "mcp_url_group_1_thief": config.my_servers.thief_mcp_url,
        "mcp_url_group_2_cop": config.bonus_opponent.cop_mcp_url,
        "mcp_url_group_2_thief": config.bonus_opponent.thief_mcp_url,
        "timezone": config.runtime.timezone,
        "students_group_1": list(config.group.students),
        "students_group_2": list(config.bonus_opponent.students),
        "agreement_sha256": evidence.get("agreement_sha256"),
        "match_evidence_sha256": evidence.get("evidence_sha256"),
        "series_id": evidence.get("series_id"),
        "sub_games": evidence.get("sub_games"),
        "totals_by_group": totals,
        "bonus_claim": calculate_bonus_claim(totals),
        "mutual_agreement": False,
    }
    validate_bonus_report(report)
    return report


def require_matching_evidence_confirmation(evidence: dict[str, Any]) -> str:
    expected = str(evidence.get("evidence_sha256", "")).lower()
    confirmed = os.environ.get("OPPONENT_BONUS_EVIDENCE_SHA256", "").strip().lower()
    if confirmed != expected:
        raise BonusReportError(
            "opponent evidence checksum is not confirmed; set "
            f"OPPONENT_BONUS_EVIDENCE_SHA256={expected} only after comparison"
        )
    return expected


def finalize_bonus_report(
    candidate: dict[str, Any],
    *,
    group_1_approval: str | None = None,
    group_2_approval: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_bonus_report(candidate)
    if candidate["mutual_agreement"] is not False:
        raise BonusReportError("candidate report must start with mutual_agreement false")
    candidate_hash = payload_sha256(candidate)
    first = (
        (
            group_1_approval
            if group_1_approval is not None
            else os.environ.get("BONUS_GROUP_1_APPROVAL_SHA256", "")
        )
        .strip()
        .lower()
    )
    second = (
        (
            group_2_approval
            if group_2_approval is not None
            else os.environ.get("BONUS_GROUP_2_APPROVAL_SHA256", "")
        )
        .strip()
        .lower()
    )
    if first != candidate_hash or second != candidate_hash:
        raise BonusReportError(
            f"both groups must explicitly approve the exact candidate SHA-256 {candidate_hash}"
        )
    final = dict(candidate)
    final["mutual_agreement"] = True
    final["approved_candidate_sha256"] = candidate_hash
    validate_bonus_report(final, require_agreement=True)
    approval_evidence = {
        "approval_type": "bonus_report_mutual_agreement",
        "candidate_sha256": candidate_hash,
        "group_1_approved": True,
        "group_2_approved": True,
        "final_report_sha256": payload_sha256(final),
    }
    return final, approval_evidence


def validate_bonus_report(
    report: dict[str, Any],
    *,
    allow_mock: bool = False,
    require_agreement: bool = False,
) -> None:
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
        "timezone",
    )
    missing = [field for field in required if field not in report]
    if missing:
        raise ValueError("bonus report missing fields: " + ", ".join(missing))
    if len(report["sub_games"]) != 6:
        raise ValueError("bonus report must contain exactly six sub_games")
    if not isinstance(report["mutual_agreement"], bool):
        raise ValueError("mutual_agreement must be a boolean")
    if report["timezone"] != "Asia/Jerusalem":
        raise ValueError("bonus report timezone must be Asia/Jerusalem")
    totals = report["totals_by_group"]
    claims = report["bonus_claim"]
    if not isinstance(totals, dict) or not isinstance(claims, dict):
        raise ValueError("totals_by_group and bonus_claim must be objects")
    if set(totals) != set(claims):
        raise ValueError("bonus claim groups must match totals_by_group groups")
    if not allow_mock and claims != calculate_bonus_claim(totals):
        raise ValueError("bonus claims do not match the game totals")

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
    if require_agreement:
        if report["mutual_agreement"] is not True:
            raise ValueError("final bonus report requires mutual_agreement true")
        if not isinstance(report.get("approved_candidate_sha256"), str):
            raise ValueError("final bonus report requires approved_candidate_sha256")


def write_mock_bonus_report(config: AppConfig, report: dict[str, Any]) -> None:
    validate_bonus_report(report, allow_mock=True)
    production = Path(config.reports.bonus_game_report).resolve()
    mock = Path(config.reports.bonus_mock_report).resolve()
    if production == mock:
        raise ValueError("mock report path must be distinct from production bonus report path")
    _atomic_write_json(mock, report)


def write_production_bonus_report(config: AppConfig, report: dict[str, Any]) -> None:
    validate_bonus_report(report, require_agreement=True)
    _atomic_write_json(config.reports.bonus_game_report, report)


def write_bonus_candidate(path: str | Path, report: dict[str, Any]) -> str:
    validate_bonus_report(report)
    if report["mutual_agreement"] is not False:
        raise BonusReportError("candidate output must keep mutual_agreement false")
    _atomic_write_json(path, report)
    return payload_sha256(report)


def load_bonus_report_candidate(path: str | Path) -> dict[str, Any]:
    candidate_path = Path(path)
    if not candidate_path.exists():
        raise BonusReportError(f"bonus report candidate not found: {candidate_path}")
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BonusReportError(f"bonus report candidate is invalid JSON: {exc}") from exc
    if not isinstance(candidate, dict):
        raise BonusReportError("bonus report candidate root must be an object")
    validate_bonus_report(candidate)
    if candidate["mutual_agreement"] is not False:
        raise BonusReportError("bonus report candidate must keep mutual_agreement false")
    return candidate


def load_final_bonus_report(path: str | Path) -> dict[str, Any]:
    report_path = Path(path)
    if not report_path.exists():
        raise BonusReportError(f"final bonus report not found: {report_path}")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BonusReportError(f"final bonus report is invalid JSON: {exc}") from exc
    if not isinstance(report, dict):
        raise BonusReportError("final bonus report root must be an object")
    validate_bonus_report(report, require_agreement=True)
    return report


def write_bonus_approval_evidence(path: str | Path, evidence: dict[str, Any]) -> None:
    required = {
        "approval_type",
        "candidate_sha256",
        "group_1_approved",
        "group_2_approved",
        "final_report_sha256",
    }
    if set(evidence) != required:
        raise BonusReportError("approval evidence fields are invalid")
    _atomic_write_json(path, evidence)
