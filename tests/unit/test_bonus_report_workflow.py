from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from ai_agents_hw6.config import BonusOpponentConfig, load_config
from ai_agents_hw6.reporting import (
    BonusReportError,
    build_bonus_report_candidate,
    calculate_bonus_claim,
    finalize_bonus_report,
    load_bonus_match_evidence,
    load_final_bonus_report,
    payload_sha256,
    require_matching_evidence_confirmation,
    validate_bonus_report,
    write_bonus_approval_evidence,
    write_bonus_candidate,
    write_production_bonus_report,
)

ROOT = Path(__file__).resolve().parents[2]


def real_config():
    config = load_config(ROOT / "config.json")
    return replace(
        config,
        bonus_opponent=BonusOpponentConfig(
            group_name="real-opponent",
            github_repo="https://github.com/example/real-opponent",
            students=("Opponent Student - 123456789",),
            cop_mcp_url="https://opponent-cop.example.net/mcp",
            thief_mcp_url="https://opponent-thief.example.net/mcp",
        ),
    )


def match_evidence(
    *,
    ours: int = 60,
    opponent: int = 30,
) -> dict:
    evidence = {
        "evidence_type": "bonus_match_result",
        "agreement_sha256": "a" * 64,
        "series_id": "series-123",
        "sub_games": [
            {
                "index": index,
                "cop_group": "salareen" if index <= 3 else "real-opponent",
                "thief_group": "real-opponent" if index <= 3 else "salareen",
                "cop_url": "https://cop.example/mcp",
                "thief_url": "https://thief.example/mcp",
                "scores": {"cop": 10, "thief": 5},
            }
            for index in range(1, 7)
        ],
        "invalid_attempts": [],
        "totals_by_group": {"salareen": ours, "real-opponent": opponent},
        "event_log_path": "artifacts/logs/bonus_events.json",
    }
    evidence["evidence_sha256"] = payload_sha256(evidence)
    return evidence


class BonusReportWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = real_config()
        self.evidence = match_evidence()

    def test_claims_assign_winner_loser_and_draw_points(self) -> None:
        self.assertEqual(
            calculate_bonus_claim({"salareen": 60, "real-opponent": 30}),
            {"salareen": 10, "real-opponent": 7},
        )
        self.assertEqual(
            calculate_bonus_claim({"salareen": 40, "real-opponent": 40}),
            {"salareen": 5, "real-opponent": 5},
        )

    def test_candidate_contains_real_metadata_six_games_and_false_agreement(self) -> None:
        candidate = build_bonus_report_candidate(self.config, self.evidence)

        self.assertEqual(candidate["report_type"], "bonus_game")
        self.assertEqual(candidate["groups"]["group_1"], "salareen")
        self.assertEqual(candidate["groups"]["group_2"], "real-opponent")
        self.assertEqual(candidate["timezone"], "Asia/Jerusalem")
        self.assertEqual(len(candidate["sub_games"]), 6)
        self.assertFalse(candidate["mutual_agreement"])
        self.assertEqual(candidate["bonus_claim"]["salareen"], 10)
        self.assertEqual(candidate["bonus_claim"]["real-opponent"], 7)
        self.assertEqual(candidate["totals_by_group"]["salareen"], 60)

    def test_candidate_rejects_placeholder_config(self) -> None:
        placeholder = replace(
            self.config,
            bonus_opponent=BonusOpponentConfig(
                group_name="OTHER_TEAM_NAME",
                github_repo="https://example.com/other-team-repo",
                students=(),
                cop_mcp_url="OTHER_TEAM_COP_MCP_URL",
                thief_mcp_url="OTHER_TEAM_THIEF_MCP_URL",
            ),
        )
        with self.assertRaisesRegex(BonusReportError, "real opponent metadata"):
            build_bonus_report_candidate(placeholder, self.evidence)

    def test_evidence_checksum_must_match_and_be_confirmed_by_opponent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "evidence.json"
            path.write_text(json.dumps(self.evidence), encoding="utf-8")
            loaded = load_bonus_match_evidence(path)

            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaisesRegex(BonusReportError, "not confirmed"):
                    require_matching_evidence_confirmation(loaded)
            with patch.dict(
                "os.environ",
                {"OPPONENT_BONUS_EVIDENCE_SHA256": loaded["evidence_sha256"]},
                clear=True,
            ):
                self.assertEqual(
                    require_matching_evidence_confirmation(loaded),
                    loaded["evidence_sha256"],
                )

            tampered = dict(self.evidence)
            tampered["series_id"] = "changed"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(BonusReportError, "checksum mismatch"):
                load_bonus_match_evidence(path)

    def test_finalization_requires_both_exact_candidate_approvals(self) -> None:
        candidate = build_bonus_report_candidate(self.config, self.evidence)
        digest = payload_sha256(candidate)

        with self.assertRaisesRegex(BonusReportError, "both groups"):
            finalize_bonus_report(candidate, group_1_approval=digest, group_2_approval="wrong")

        final, approval = finalize_bonus_report(
            candidate,
            group_1_approval=digest,
            group_2_approval=digest,
        )

        self.assertTrue(final["mutual_agreement"])
        self.assertEqual(final["approved_candidate_sha256"], digest)
        self.assertEqual(approval["candidate_sha256"], digest)
        self.assertEqual(approval["final_report_sha256"], payload_sha256(final))
        validate_bonus_report(final, require_agreement=True)

    def test_unapproved_candidate_cannot_overwrite_production_report(self) -> None:
        candidate = build_bonus_report_candidate(self.config, self.evidence)
        with self.assertRaisesRegex(ValueError, "mutual_agreement true"):
            write_production_bonus_report(self.config, candidate)

    def test_final_report_and_approval_evidence_are_json_only_and_reloadable(self) -> None:
        candidate = build_bonus_report_candidate(self.config, self.evidence)
        digest = payload_sha256(candidate)
        final, approval = finalize_bonus_report(
            candidate,
            group_1_approval=digest,
            group_2_approval=digest,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate_path = Path(temp_dir) / "candidate.json"
            final_path = Path(temp_dir) / "final.json"
            approval_path = Path(temp_dir) / "approval.json"
            config = replace(
                self.config,
                reports=replace(self.config.reports, bonus_game_report=str(final_path)),
            )

            self.assertEqual(write_bonus_candidate(candidate_path, candidate), digest)
            write_production_bonus_report(config, final)
            write_bonus_approval_evidence(approval_path, approval)

            self.assertEqual(json.loads(candidate_path.read_text(encoding="utf-8")), candidate)
            self.assertEqual(load_final_bonus_report(final_path), final)
            self.assertEqual(json.loads(approval_path.read_text(encoding="utf-8")), approval)

    def test_bonus_mode_refuses_gmail_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
            raw["bonus_opponent"] = {
                "group_name": self.config.bonus_opponent.group_name,
                "github_repo": self.config.bonus_opponent.github_repo,
                "students": list(self.config.bonus_opponent.students),
                "cop_mcp_url": self.config.bonus_opponent.cop_mcp_url,
                "thief_mcp_url": self.config.bonus_opponent.thief_mcp_url,
            }
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps(raw), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--mode",
                    "bonus",
                    "--config",
                    str(config_path),
                    "--send-report",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("Bonus report delivery is blocked from Gmail", completed.stderr)


if __name__ == "__main__":
    unittest.main()
