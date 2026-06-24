from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ai_agents_hw6.application.bonus import (
    BonusCredentials,
    BonusPreflightError,
    preflight_bonus_opponent,
)
from ai_agents_hw6.application.bonus_mock import (
    DeterministicBonusMock,
    build_bonus_mock_report,
    run_bonus_mock,
)
from ai_agents_hw6.application.mcp_client import RoleMcpClient
from ai_agents_hw6.config import BonusOpponentConfig, ConfigError, load_config, validate_for_mode
from ai_agents_hw6.domain import Role
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION
from ai_agents_hw6.reporting.bonus_report import (
    BONUS_MOCK_REPORT_TYPE,
    BONUS_REPORT_TYPE,
    validate_bonus_report,
    write_production_bonus_report,
)

ROOT = Path(__file__).resolve().parents[2]


class FakeRoleClient(RoleMcpClient):
    def health(self) -> dict[str, Any]:
        return {"status": "ok"}

    def identity(self) -> dict[str, Any]:
        return {"role": self.role.value}

    def capabilities(self) -> dict[str, Any]:
        return {"protocol_version": PROTOCOL_VERSION, "operations": ["decide"]}


class WrongProtocolClient(FakeRoleClient):
    def capabilities(self) -> dict[str, Any]:
        return {"protocol_version": "0.0", "operations": ["decide"]}


class BonusBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "config.json")

    def test_internal_and_mock_modes_allow_missing_opponent_data(self) -> None:
        validate_for_mode(self.config, "internal")
        validate_for_mode(self.config, "bonus-mock")

    def test_production_bonus_lists_all_missing_or_placeholder_fields(self) -> None:
        with self.assertRaises(ConfigError) as raised:
            validate_for_mode(self.config, "bonus")

        message = str(raised.exception)
        for field in (
            "bonus_opponent.group_name",
            "bonus_opponent.students",
            "bonus_opponent.github_repo",
            "bonus_opponent.cop_mcp_url",
            "bonus_opponent.thief_mcp_url",
        ):
            self.assertIn(field, message)

    def test_production_bonus_requires_distinct_https_urls(self) -> None:
        opponent = BonusOpponentConfig(
            group_name="Real Team",
            github_repo="https://github.com/example/real-team",
            students=("Student One - 123",),
            cop_mcp_url="http://services.example.net/mcp",
            thief_mcp_url="http://services.example.net/mcp",
        )
        config = replace(self.config, bonus_opponent=opponent)

        with self.assertRaises(ConfigError) as raised:
            validate_for_mode(config, "bonus")

        self.assertIn("valid HTTPS URL", str(raised.exception))
        self.assertIn("must be distinct", str(raised.exception))

    def test_opponent_tokens_are_required_from_environment(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(BonusPreflightError) as raised:
                BonusCredentials.from_environment()

        self.assertIn("OPPONENT_COP_MCP_TOKEN", str(raised.exception))
        self.assertIn("OPPONENT_THIEF_MCP_TOKEN", str(raised.exception))

        with patch.dict(
            os.environ,
            {
                "OPPONENT_COP_MCP_TOKEN": "private-cop",
                "OPPONENT_THIEF_MCP_TOKEN": "private-thief",
            },
            clear=True,
        ):
            credentials = BonusCredentials.from_environment()
        self.assertEqual(credentials.opponent_cop_token, "private-cop")
        self.assertEqual(credentials.opponent_thief_token, "private-thief")

    def test_preflight_validates_roles_protocol_and_passes_tokens(self) -> None:
        created: list[FakeRoleClient] = []

        def factory(**kwargs: Any) -> RoleMcpClient:
            client = FakeRoleClient(**kwargs)
            created.append(client)
            return client

        preflight_bonus_opponent(
            self.config,
            credentials=BonusCredentials(None, None, "cop-secret", "thief-secret"),
            client_factory=factory,
        )

        self.assertEqual([client.role for client in created], [Role.COP, Role.THIEF])
        self.assertEqual([client.token for client in created], ["cop-secret", "thief-secret"])

        with self.assertRaisesRegex(BonusPreflightError, "protocol mismatch"):
            preflight_bonus_opponent(
                self.config,
                credentials=BonusCredentials(None, None, "cop-secret", "thief-secret"),
                client_factory=WrongProtocolClient,
            )

    def test_mock_decisions_and_report_are_deterministic(self) -> None:
        mock = DeterministicBonusMock()
        self.assertEqual(mock.decide(["first", "second"]), "first")
        self.assertEqual(
            build_bonus_mock_report(self.config),
            build_bonus_mock_report(self.config),
        )

    def test_mock_report_covers_both_directions_and_cannot_claim_bonus(self) -> None:
        report = build_bonus_mock_report(self.config)
        validate_bonus_report(report, allow_mock=True)

        self.assertEqual(report["report_type"], BONUS_MOCK_REPORT_TYPE)
        self.assertEqual(
            [game["matchup_direction"] for game in report["sub_games"][:3]],
            ["our_cop_vs_mock_thief"] * 3,
        )
        self.assertEqual(
            [game["matchup_direction"] for game in report["sub_games"][3:]],
            ["mock_cop_vs_our_thief"] * 3,
        )
        self.assertFalse(report["mutual_agreement"])
        self.assertEqual(set(report["bonus_claim"].values()), {0})

        report["mutual_agreement"] = True
        with self.assertRaisesRegex(ValueError, "cannot claim mutual agreement"):
            validate_bonus_report(report, allow_mock=True)

    def test_mock_writes_only_the_separate_mock_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            production = Path(temp_dir) / "bonus.json"
            mock = Path(temp_dir) / "bonus.mock.json"
            production.write_text("production-sentinel", encoding="utf-8")
            config = replace(
                self.config,
                reports=replace(
                    self.config.reports,
                    bonus_game_report=str(production),
                    bonus_mock_report=str(mock),
                ),
            )

            run_bonus_mock(config)

            self.assertEqual(production.read_text(encoding="utf-8"), "production-sentinel")
            payload = json.loads(mock.read_text(encoding="utf-8"))
            self.assertTrue(payload["test_only"])

    def test_production_writer_rejects_mock_report(self) -> None:
        report = build_bonus_mock_report(self.config)
        with self.assertRaisesRegex(ValueError, BONUS_REPORT_TYPE):
            write_production_bonus_report(self.config, report)

    def test_cli_mock_prints_warning_and_refuses_gmail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
            raw["reports"]["bonus_mock_report"] = str(Path(temp_dir) / "mock.json")
            raw["reports"]["bonus_game_report"] = str(Path(temp_dir) / "production.json")
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps(raw), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--mode",
                    "bonus-mock",
                    "--config",
                    str(config_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            refused = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--mode",
                    "bonus-mock",
                    "--config",
                    str(config_path),
                    "--gmail-preflight",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("TEST-ONLY BONUS MOCK", completed.stdout)
        self.assertFalse((Path(temp_dir) / "production.json").exists())
        self.assertEqual(refused.returncode, 2)
        self.assertIn("cannot authorize, preflight, or send Gmail", refused.stderr)


if __name__ == "__main__":
    unittest.main()
