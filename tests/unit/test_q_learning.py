from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_agents_hw6.agents import (
    LearningSettings,
    QLearningPolicy,
    action_index,
    encode_observation_state,
    load_q_table,
)
from ai_agents_hw6.agents.policy import PolicyInput
from ai_agents_hw6.domain import (
    Coordinate,
    Direction,
    GridSize,
    MoveAction,
    PlaceBarrierAction,
    Role,
)


def _input(
    role: Role = Role.THIEF,
    *,
    visible_opponent: Coordinate | None = None,
) -> PolicyInput:
    actions = (MoveAction(Direction.RIGHT), MoveAction(Direction.DOWN))
    return PolicyInput(
        role=role,
        self_position=Coordinate(0, 0),
        visible_opponent=visible_opponent,
        visible_barriers=frozenset({Coordinate(1, 1)}),
        grid=GridSize(5, 5),
        legal_actions=actions,
        move_round=3,
        seed=999,
    )


class QLearningTests(unittest.TestCase):
    def test_state_encoding_uses_only_policy_input_and_is_stable(self) -> None:
        first = _input(visible_opponent=None)
        second = _input(visible_opponent=None)

        encoded = encode_observation_state(first)

        self.assertEqual(encoded, encode_observation_state(second))
        self.assertNotIn("cop_position", encoded)
        self.assertNotIn("thief_position", encoded)
        self.assertIn('"opponent":null', encoded)

    def test_role_specific_action_indices(self) -> None:
        self.assertEqual(action_index(Role.THIEF, MoveAction(Direction.UP), 5), 0)
        self.assertEqual(action_index(Role.COP, MoveAction(Direction.RIGHT), 5), 1)
        self.assertEqual(
            action_index(Role.COP, PlaceBarrierAction(Coordinate(2, 3)), 5),
            17,
        )
        with self.assertRaisesRegex(Exception, "Thief"):
            action_index(Role.THIEF, PlaceBarrierAction(Coordinate(2, 3)), 5)

    def test_disabled_learning_preserves_heuristic_fallback(self) -> None:
        policy = QLearningPolicy(LearningSettings(enabled=False))
        policy_input = _input(visible_opponent=Coordinate(4, 4))

        self.assertEqual(policy.choose_action(policy_input), MoveAction(Direction.RIGHT))

    def test_epsilon_greedy_selects_highest_valued_legal_action(self) -> None:
        settings = LearningSettings(enabled=True, epsilon=0.0)
        policy = QLearningPolicy(settings)
        policy_input = _input()
        state = encode_observation_state(policy_input)
        policy.thief_table[state] = {
            action_index(Role.THIEF, MoveAction(Direction.RIGHT), 5): 1.0,
            action_index(Role.THIEF, MoveAction(Direction.DOWN), 5): 4.0,
        }

        self.assertEqual(policy.choose_action(policy_input), MoveAction(Direction.DOWN))

    def test_terminal_update_does_not_bootstrap(self) -> None:
        settings = LearningSettings(enabled=True, alpha=0.5, gamma=0.9, epsilon=0.0)
        policy = QLearningPolicy(settings)
        policy_input = _input()
        action = MoveAction(Direction.RIGHT)

        policy.update(
            current=policy_input,
            action=action,
            reward=10.0,
            next_input=None,
            terminal=True,
        )

        value = policy.thief_table[encode_observation_state(policy_input)][
            action_index(Role.THIEF, action, 5)
        ]
        self.assertEqual(value, 5.0)

    def test_non_terminal_update_bootstraps_only_same_role_table(self) -> None:
        settings = LearningSettings(enabled=True, alpha=1.0, gamma=0.5, epsilon=0.0)
        policy = QLearningPolicy(settings)
        current = _input()
        next_input = PolicyInput(
            role=current.role,
            self_position=Coordinate(0, 1),
            visible_opponent=None,
            visible_barriers=current.visible_barriers,
            grid=current.grid,
            legal_actions=current.legal_actions,
            move_round=4,
            seed=current.seed,
        )
        policy.thief_table[encode_observation_state(next_input)] = {
            action_index(Role.THIEF, MoveAction(Direction.DOWN), 5): 8.0
        }

        policy.update(
            current=current,
            action=MoveAction(Direction.RIGHT),
            reward=2.0,
            next_input=next_input,
            terminal=False,
        )

        self.assertEqual(
            policy.thief_table[encode_observation_state(current)][
                action_index(Role.THIEF, MoveAction(Direction.RIGHT), 5)
            ],
            6.0,
        )
        self.assertEqual(policy.cop_table, {})

    def test_tables_persist_separately_and_reject_bad_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            settings = LearningSettings(
                enabled=True,
                cop_table_path=str(root / "cop.json"),
                thief_table_path=str(root / "thief.json"),
            )
            policy = QLearningPolicy(settings)
            policy.cop_table = {"cop-state": {0: 1.5}}
            policy.thief_table = {"thief-state": {1: -2.0}}
            policy.save()

            restored = QLearningPolicy(settings)
            restored.load()
            self.assertEqual(restored.cop_table, policy.cop_table)
            self.assertEqual(restored.thief_table, policy.thief_table)

            (root / "cop.json").write_text(
                json.dumps({"version": 999, "role": "cop", "values": {}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "incompatible"):
                load_q_table(root / "cop.json", Role.COP)

    def test_training_and_evaluation_seeds_must_differ(self) -> None:
        with self.assertRaisesRegex(ValueError, "distinct"):
            LearningSettings(training_seed=7, evaluation_seed=7)


if __name__ == "__main__":
    unittest.main()
