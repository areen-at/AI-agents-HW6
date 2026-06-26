from __future__ import annotations

import unittest

from ai_agents_hw6.application.fastmcp_host_client import (
    FastMcpHostSettings,
    action_to_fastmcp_submit_args,
    observation_from_fastmcp_json,
)
from ai_agents_hw6.domain import Direction, MoveAction, Role


class FastMcpHostClientTests(unittest.TestCase):
    def test_observation_converts_xy_coordinates_to_internal_row_col(self) -> None:
        observation = observation_from_fastmcp_json(
            {
                "grid_size": [7, 5],
                "self_position": [3, 1],
                "visible_opponent": [4, 2],
                "visible_barriers": [[2, 1]],
                "legal_actions": [{"kind": "move", "dx": 0, "dy": -1}],
                "move_round": 4,
                "max_moves": 25,
                "barriers_placed": 1,
                "max_barriers": 5,
            },
            Role.COP,
        )

        self.assertEqual(observation.grid.to_json(), [5, 7])
        self.assertEqual(observation.self_position.to_json(), [1, 3])
        self.assertEqual(observation.visible_opponent.to_json(), [2, 4])
        self.assertEqual([item.to_json() for item in observation.visible_barriers], [[1, 2]])
        self.assertEqual(observation.legal_actions, (MoveAction(Direction.UP),))

    def test_move_action_converts_to_fastmcp_dx_dy(self) -> None:
        observation = observation_from_fastmcp_json(
            {
                "grid_size": [5, 5],
                "self_position": [2, 2],
                "visible_opponent": None,
                "visible_barriers": [],
                "legal_actions": [{"type": "move", "direction": "left"}],
            },
            Role.THIEF,
        )

        payload = action_to_fastmcp_submit_args(MoveAction(Direction.LEFT), observation)

        self.assertEqual(payload, {"kind": "move", "dx": -1, "dy": 0})

    def test_host_url_is_normalized_to_mcp_path(self) -> None:
        settings = FastMcpHostSettings(
            host_url="https://example.test/game/mcp",
            token="token",
            role=Role.COP,
        )

        self.assertEqual(settings.host_url, "https://example.test/game/mcp")


if __name__ == "__main__":
    unittest.main()
