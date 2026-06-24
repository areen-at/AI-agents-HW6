from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ai_agents_hw6.application import (
    BonusCredentials,
    BonusMatchup,
    BonusPreflightError,
    bonus_agreement_sha256,
    build_bonus_match_evidence,
    build_bonus_schedule,
    require_confirmed_bonus_agreement,
    run_external_bonus_series,
    validate_bonus_schedule,
)
from ai_agents_hw6.application.mcp_client import RoleMcpClient
from ai_agents_hw6.application.series import TechnicalFailure
from ai_agents_hw6.config import BonusOpponentConfig, load_config
from ai_agents_hw6.domain import TechnicalFailureReason
from ai_agents_hw6.mcp_servers.protocol import PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[2]


class DeterministicRoleClient(RoleMcpClient):
    calls: list[tuple[str, str]] = []

    def health(self) -> dict[str, Any]:
        return {"status": "ok"}

    def identity(self) -> dict[str, Any]:
        return {"role": self.role.value}

    def capabilities(self) -> dict[str, Any]:
        return {"protocol_version": PROTOCOL_VERSION, "operations": ["decide"]}

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        type(self).calls.append((self.base_url, self.role.value))
        observation = payload["observation"]
        action = observation["legal_actions"][0]
        return {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": payload["request_id"],
            "correlation_id": payload["correlation_id"],
            "role": self.role.value,
            "decision": {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": payload["request_id"],
                "role": self.role.value,
                "action": action,
            },
        }


class InitiallyUnavailableClient(DeterministicRoleClient):
    failures_remaining = 3

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        if type(self).failures_remaining:
            type(self).failures_remaining -= 1
            raise TechnicalFailure(
                TechnicalFailureReason.MCP_TIMEOUT,
                "deterministic test outage",
            )
        return super().decide(payload)


def real_bonus_config():
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
        logging=replace(
            config.logging,
            event_log_dir=tempfile.gettempdir(),
        ),
    )


class BonusOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        DeterministicRoleClient.calls = []
        InitiallyUnavailableClient.calls = []
        InitiallyUnavailableClient.failures_remaining = 3
        self.config = real_bonus_config()
        self.credentials = BonusCredentials(
            "our-cop-secret",
            "our-thief-secret",
            "opponent-cop-secret",
            "opponent-thief-secret",
        )

    def test_schedule_is_exact_required_three_plus_three_order(self) -> None:
        schedule = build_bonus_schedule(self.config)

        self.assertEqual(len(schedule), 6)
        self.assertEqual(
            [(item.cop_group, item.thief_group) for item in schedule[:3]],
            [("salareen", "real-opponent")] * 3,
        )
        self.assertEqual(
            [(item.cop_group, item.thief_group) for item in schedule[3:]],
            [("real-opponent", "salareen")] * 3,
        )

    def test_reversed_or_duplicated_schedule_is_rejected(self) -> None:
        schedule = list(build_bonus_schedule(self.config))
        schedule[3] = BonusMatchup(
            index=4,
            cop_group="salareen",
            thief_group="real-opponent",
            cop_url=self.config.my_servers.cop_mcp_url,
            thief_url=self.config.bonus_opponent.thief_mcp_url,
        )
        with self.assertRaisesRegex(BonusPreflightError, "3\\+3"):
            validate_bonus_schedule(self.config, tuple(schedule))

    def test_agreement_hash_must_be_explicitly_confirmed(self) -> None:
        expected = bonus_agreement_sha256(self.config)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(BonusPreflightError, expected):
                require_confirmed_bonus_agreement(self.config)
        with patch.dict("os.environ", {"BONUS_AGREEMENT_SHA256": expected}, clear=True):
            self.assertEqual(require_confirmed_bonus_agreement(self.config), expected)

    def test_six_games_route_roles_and_attribute_scores_to_owners(self) -> None:
        result = run_external_bonus_series(
            self.config,
            credentials=self.credentials,
            client_factory=DeterministicRoleClient,
            require_agreement=False,
        )

        self.assertEqual(len(result.series.valid_sub_games), 6)
        self.assertEqual(
            sum(result.totals_by_group.values()),
            sum(result.series.totals.values()),
        )
        decision_urls = [url for url, _role in DeterministicRoleClient.calls]
        first_half = decision_urls[: decision_urls.index(self.config.bonus_opponent.cop_mcp_url)]
        self.assertIn(self.config.my_servers.cop_mcp_url, first_half)
        self.assertIn(self.config.bonus_opponent.thief_mcp_url, first_half)
        self.assertIn(self.config.bonus_opponent.cop_mcp_url, decision_urls)
        self.assertIn(self.config.my_servers.thief_mcp_url, decision_urls)

        evidence = build_bonus_match_evidence(self.config, result)
        self.assertEqual(len(evidence["sub_games"]), 6)
        self.assertTrue(evidence["evidence_sha256"])
        self.assertEqual(
            [game["cop_group"] for game in evidence["sub_games"]],
            ["salareen"] * 3 + ["real-opponent"] * 3,
        )

    def test_evidence_is_canonical_and_contains_no_tokens(self) -> None:
        result = run_external_bonus_series(
            self.config,
            credentials=self.credentials,
            client_factory=DeterministicRoleClient,
            require_agreement=False,
        )
        serialized = json.dumps(build_bonus_match_evidence(self.config, result), sort_keys=True)
        for secret in (
            "our-cop-secret",
            "our-thief-secret",
            "opponent-cop-secret",
            "opponent-thief-secret",
        ):
            self.assertNotIn(secret, serialized)

    def test_technical_failure_attempt_is_replaced_without_scoring_it(self) -> None:
        result = run_external_bonus_series(
            self.config,
            credentials=self.credentials,
            client_factory=InitiallyUnavailableClient,
            require_agreement=False,
        )

        self.assertEqual(len(result.series.valid_sub_games), 6)
        self.assertEqual(len(result.series.invalid_attempts), 3)
        self.assertEqual(
            result.series.invalid_attempts[0].failure_reason,
            TechnicalFailureReason.MCP_TIMEOUT,
        )


if __name__ == "__main__":
    unittest.main()
