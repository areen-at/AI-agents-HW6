from __future__ import annotations

import unittest

from ai_agents_hw6.agents import (
    HeuristicPolicy,
    heuristic_decision_provider,
    policy_input_from_state,
)
from ai_agents_hw6.agents.policy import PolicyInput
from ai_agents_hw6.application.series import SeriesSettings, run_series
from ai_agents_hw6.domain import (
    AttemptId,
    Coordinate,
    Direction,
    DomainError,
    GameState,
    GridSize,
    MoveAction,
    PlaceBarrierAction,
    Role,
    ScoreMatrix,
    SeriesId,
    SubGameId,
    legal_actions,
)

DEFAULT_GRID = GridSize(5, 5)
DEFAULT_COP = Coordinate(2, 2)
DEFAULT_THIEF = Coordinate(0, 2)


def _state(
    *,
    grid: GridSize = DEFAULT_GRID,
    cop: Coordinate = DEFAULT_COP,
    thief: Coordinate = DEFAULT_THIEF,
    active: Role = Role.COP,
    barriers: frozenset[Coordinate] = frozenset(),
    barriers_placed: int = 0,
) -> GameState:
    return GameState(
        series_id=SeriesId.new(),
        sub_game_id=SubGameId.new(),
        attempt_id=AttemptId.new(),
        grid=grid,
        cop_position=cop,
        thief_position=thief,
        active_role=active,
        seed=42,
        barriers=barriers,
        barriers_placed=barriers_placed,
    )


class HeuristicPolicyTests(unittest.TestCase):
    def test_cop_pursues_visible_thief_with_best_legal_move(self) -> None:
        policy = HeuristicPolicy()
        state = _state(cop=Coordinate(2, 2), thief=Coordinate(0, 2), active=Role.COP)
        policy_input = PolicyInput(
            role=Role.COP,
            self_position=state.cop_position,
            visible_opponent=state.thief_position,
            visible_barriers=frozenset(),
            grid=state.grid,
            legal_actions=tuple(
                action for action in legal_actions(state) if isinstance(action, MoveAction)
            ),
            move_round=0,
            seed=state.seed,
        )

        self.assertEqual(policy.choose_action(policy_input), MoveAction(Direction.UP))

    def test_cop_places_useful_barrier_before_non_capture_move(self) -> None:
        policy = HeuristicPolicy()
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(0, 2), active=Role.COP)

        action = policy.choose_action(policy_input_from_state(state))

        self.assertIsInstance(action, PlaceBarrierAction)
        self.assertIn(action, legal_actions(state))

    def test_cop_prefers_capture_over_barrier(self) -> None:
        policy = HeuristicPolicy()
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(1, 2), active=Role.COP)

        self.assertEqual(
            policy.choose_action(policy_input_from_state(state)), MoveAction(Direction.RIGHT)
        )

    def test_cop_falls_back_to_move_when_barrier_limit_reached(self) -> None:
        policy = HeuristicPolicy()
        state = _state(
            cop=Coordinate(2, 2),
            thief=Coordinate(0, 2),
            active=Role.COP,
            barriers=frozenset({Coordinate(4, 4)}),
            barriers_placed=5,
        )

        action = policy.choose_action(policy_input_from_state(state, max_barriers=5))

        self.assertIsInstance(action, MoveAction)
        self.assertEqual(action, MoveAction(Direction.UP))

    def test_thief_escapes_visible_cop_with_distance_and_safety_tie_break(self) -> None:
        policy = HeuristicPolicy()
        state = _state(cop=Coordinate(2, 2), thief=Coordinate(2, 3), active=Role.THIEF)

        action = policy.choose_action(policy_input_from_state(state))

        self.assertEqual(action, MoveAction(Direction.UP))

    def test_thief_avoids_more_trapped_escape_when_distance_ties(self) -> None:
        policy = HeuristicPolicy()
        state = _state(
            grid=GridSize(4, 4),
            cop=Coordinate(1, 1),
            thief=Coordinate(1, 2),
            active=Role.THIEF,
            barriers=frozenset({Coordinate(0, 3), Coordinate(2, 3)}),
            barriers_placed=2,
        )

        action = policy.choose_action(policy_input_from_state(state))

        self.assertNotEqual(action, MoveAction(Direction.RIGHT))
        self.assertIn(action, legal_actions(state))

    def test_thief_never_returns_barrier_action(self) -> None:
        policy = HeuristicPolicy()
        state = _state(cop=Coordinate(2, 2), thief=Coordinate(0, 2), active=Role.THIEF)

        self.assertIsInstance(policy.choose_action(policy_input_from_state(state)), MoveAction)

    def test_no_visible_opponent_uses_deterministic_tie_break(self) -> None:
        policy = HeuristicPolicy()
        state = _state(cop=Coordinate(2, 2), thief=Coordinate(0, 2), active=Role.THIEF)
        policy_input = policy_input_from_state(state)
        hidden_input = PolicyInput(
            role=policy_input.role,
            self_position=policy_input.self_position,
            visible_opponent=None,
            visible_barriers=policy_input.visible_barriers,
            grid=policy_input.grid,
            legal_actions=policy_input.legal_actions,
            move_round=policy_input.move_round,
            seed=policy_input.seed,
        )

        self.assertEqual(policy.choose_action(hidden_input), MoveAction(Direction.RIGHT))

    def test_no_legal_action_raises_domain_error(self) -> None:
        policy = HeuristicPolicy()
        with self.assertRaisesRegex(DomainError, "no legal"):
            policy.choose_action(
                PolicyInput(
                    role=Role.THIEF,
                    self_position=Coordinate(0, 0),
                    visible_opponent=None,
                    visible_barriers=frozenset(),
                    grid=GridSize(2, 2),
                    legal_actions=tuple(),
                    move_round=0,
                    seed=1,
                )
            )

    def test_every_heuristic_output_is_engine_legal_across_grid_sanity_states(self) -> None:
        policy = HeuristicPolicy()
        states = []
        for rows, columns in ((3, 2), (3, 3), (4, 3), (4, 4), (5, 5)):
            grid = GridSize(rows, columns)
            for role in (Role.COP, Role.THIEF):
                states.append(
                    _state(
                        grid=grid,
                        cop=Coordinate(rows - 1, columns - 1),
                        thief=Coordinate(0, 0),
                        active=role,
                    )
                )

        for state in states:
            action = policy.choose_action(policy_input_from_state(state))
            self.assertIn(action, legal_actions(state))

    def test_six_engine_only_games_run_with_heuristics(self) -> None:
        result = run_series(
            settings=SeriesSettings(
                grid=GridSize(5, 5),
                num_games=6,
                max_moves=25,
                max_barriers=5,
                random_seed=12345,
                technical_attempt_limit_per_slot=10,
            ),
            scoring=ScoreMatrix(),
            decision_provider=heuristic_decision_provider(max_barriers=5),
        )

        self.assertEqual(len(result.valid_sub_games), 6)
        self.assertEqual(result.invalid_attempts, tuple())
        self.assertEqual(
            result.totals,
            {
                "cop": sum(game.cop_score for game in result.valid_sub_games),
                "thief": sum(game.thief_score for game in result.valid_sub_games),
            },
        )


if __name__ == "__main__":
    unittest.main()
