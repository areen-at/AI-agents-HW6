from __future__ import annotations

import unittest
from typing import Any

from ai_agents_hw6.application.rest_decide_bonus import (
    MixedRestDecideProvider,
    RestDecideSettings,
)
from ai_agents_hw6.domain import (
    AttemptId,
    GridSize,
    MoveAction,
    Role,
    SeriesId,
    SubGameId,
    create_initial_state,
)


class FakeRestDecideClient:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(payload)
        legal_moves = [
            action
            for action in payload["observation"]["legal_actions"]
            if action.get("type") == "move"
        ]
        return {
            "protocol_version": "1.0",
            "request_id": payload["request_id"],
            "correlation_id": payload["request_id"],
            "role": payload["role"],
            "decision": {
                "protocol_version": "1.0",
                "request_id": payload["request_id"],
                "role": payload["role"],
                "action": legal_moves[0],
            },
        }


class RestDecideBonusTests(unittest.TestCase):
    def test_mixed_provider_calls_rest_decide_for_opponent_role(self) -> None:
        state = create_initial_state(
            grid=GridSize(5, 5),
            seed=123,
            series_id=SeriesId.new(),
            sub_game_id=SubGameId.new(),
            attempt_id=AttemptId.new(),
        )
        client = FakeRestDecideClient()
        provider = MixedRestDecideProvider(
            opponent_client=client,  # type: ignore[arg-type]
            opponent_role=Role.THIEF,
            max_moves=25,
            max_barriers=5,
            manhattan_radius=2,
            max_retries=0,
        )

        action = provider.decide(state)

        self.assertIsInstance(action, MoveAction)
        self.assertEqual(len(client.payloads), 1)
        self.assertEqual(client.payloads[0]["role"], "thief")
        self.assertEqual(
            client.payloads[0]["observation"]["request_id"],
            client.payloads[0]["request_id"],
        )

    def test_rest_decide_settings_require_url(self) -> None:
        settings = RestDecideSettings(
            decide_url="https://decide.example/decide",
            token=None,
            timeout_seconds=20,
            max_retries=2,
        )

        self.assertEqual(settings.decide_url, "https://decide.example/decide")


if __name__ == "__main__":
    unittest.main()
