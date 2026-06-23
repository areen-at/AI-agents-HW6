from __future__ import annotations

import unittest
from dataclasses import replace

from ai_agents_hw6.config import load_config
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
    TerminalOutcome,
    TerminalReason,
    apply_action,
    create_initial_state,
    legal_actions,
    legal_barrier_actions,
    legal_move_actions,
    replay_actions,
    score_state,
)


def _state(
    *,
    grid: GridSize = GridSize(3, 3),
    cop: Coordinate = Coordinate(1, 1),
    thief: Coordinate = Coordinate(0, 0),
    active: Role = Role.THIEF,
    move_round: int = 0,
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
        seed=1,
        move_round=move_round,
        barriers=barriers,
        barriers_placed=barriers_placed,
    )


class MovementRuleTests(unittest.TestCase):
    def test_generates_legal_cop_and_thief_moves(self) -> None:
        state = _state()

        self.assertEqual(
            {action.direction for action in legal_move_actions(state, Role.THIEF)},
            {Direction.DOWN, Direction.RIGHT},
        )
        self.assertEqual(
            {action.direction for action in legal_move_actions(state, Role.COP)},
            {Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT},
        )

    def test_rejects_out_of_bounds_and_barrier_moves_without_mutation(self) -> None:
        state = _state(
            thief=Coordinate(0, 0),
            active=Role.THIEF,
            barriers=frozenset({Coordinate(1, 0)}),
            barriers_placed=1,
        )

        with self.assertRaisesRegex(DomainError, "illegal move"):
            apply_action(state, role=Role.THIEF, action=MoveAction(Direction.UP))
        with self.assertRaisesRegex(DomainError, "illegal move"):
            apply_action(state, role=Role.THIEF, action=MoveAction(Direction.DOWN))

        self.assertEqual(state.thief_position, Coordinate(0, 0))
        self.assertEqual(state.active_role, Role.THIEF)
        self.assertEqual(state.barriers, frozenset({Coordinate(1, 0)}))

    def test_unsupported_stay_or_diagonal_action_is_not_representable(self) -> None:
        self.assertNotIn("stay", {direction.value for direction in Direction})
        self.assertNotIn("diagonal", {direction.value for direction in Direction})
        with self.assertRaisesRegex(DomainError, "Direction"):
            MoveAction("stay")  # type: ignore[arg-type]

    def test_enforces_thief_first_and_turn_switching(self) -> None:
        state = _state(thief=Coordinate(0, 0), active=Role.THIEF)

        with self.assertRaisesRegex(DomainError, "out-of-turn"):
            apply_action(state, role=Role.COP, action=MoveAction(Direction.UP))

        after_thief = apply_action(state, role=Role.THIEF, action=MoveAction(Direction.RIGHT))
        self.assertEqual(after_thief.thief_position, Coordinate(0, 1))
        self.assertEqual(after_thief.active_role, Role.COP)
        self.assertEqual(after_thief.move_round, 0)

        after_cop = apply_action(after_thief, role=Role.COP, action=MoveAction(Direction.DOWN))
        self.assertEqual(after_cop.active_role, Role.THIEF)
        self.assertEqual(after_cop.move_round, 1)

    def test_capture_only_after_cop_move_and_blocks_later_actions(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(1, 2), active=Role.COP)

        captured = apply_action(state, role=Role.COP, action=MoveAction(Direction.RIGHT))

        self.assertTrue(captured.is_terminal)
        self.assertEqual(captured.terminal_outcome, TerminalOutcome.COP_WIN)
        self.assertEqual(captured.terminal_reason, TerminalReason.CAPTURE)
        self.assertEqual(captured.cop_position, captured.thief_position)
        with self.assertRaisesRegex(DomainError, "terminal state"):
            apply_action(captured, role=Role.COP, action=MoveAction(Direction.LEFT))

    def test_thief_survives_at_configured_move_limit_after_cop_action(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(0, 0), active=Role.COP)

        survived = apply_action(state, role=Role.COP, action=MoveAction(Direction.DOWN), max_moves=1)

        self.assertTrue(survived.is_terminal)
        self.assertEqual(survived.move_round, 1)
        self.assertEqual(survived.terminal_outcome, TerminalOutcome.THIEF_WIN)
        self.assertEqual(survived.terminal_reason, TerminalReason.MOVE_LIMIT)

    def test_capture_takes_precedence_on_final_round(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(1, 2), active=Role.COP)

        captured = apply_action(state, role=Role.COP, action=MoveAction(Direction.RIGHT), max_moves=1)

        self.assertEqual(captured.terminal_outcome, TerminalOutcome.COP_WIN)
        self.assertEqual(captured.terminal_reason, TerminalReason.CAPTURE)


class BarrierRuleTests(unittest.TestCase):
    def test_cop_can_place_adjacent_barrier_and_consumes_turn(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(0, 0), active=Role.COP)

        barrier_actions = legal_barrier_actions(state, max_barriers=5)
        self.assertIn(PlaceBarrierAction(Coordinate(1, 2)), barrier_actions)

        next_state = apply_action(
            state,
            role=Role.COP,
            action=PlaceBarrierAction(Coordinate(1, 2)),
            max_moves=25,
            max_barriers=5,
        )

        self.assertEqual(next_state.active_role, Role.THIEF)
        self.assertEqual(next_state.move_round, 1)
        self.assertEqual(next_state.barriers, frozenset({Coordinate(1, 2)}))
        self.assertEqual(next_state.barriers_placed, 1)

    def test_only_cop_can_place_barriers(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(0, 0), active=Role.THIEF)

        with self.assertRaisesRegex(DomainError, "out-of-turn"):
            apply_action(state, role=Role.COP, action=PlaceBarrierAction(Coordinate(1, 2)))
        with self.assertRaisesRegex(DomainError, "only the Cop"):
            apply_action(state, role=Role.THIEF, action=PlaceBarrierAction(Coordinate(1, 2)))

    def test_rejects_barrier_on_player_existing_or_non_adjacent_cell(self) -> None:
        state = _state(
            cop=Coordinate(1, 1),
            thief=Coordinate(0, 0),
            active=Role.COP,
            barriers=frozenset({Coordinate(1, 2)}),
            barriers_placed=1,
        )

        for target in (
            Coordinate(1, 1),
            Coordinate(0, 0),
            Coordinate(1, 2),
            Coordinate(2, 2),
        ):
            with self.assertRaisesRegex(DomainError, "illegal barrier"):
                apply_action(state, role=Role.COP, action=PlaceBarrierAction(target))

    def test_rejects_barrier_after_maximum_count(self) -> None:
        state = _state(
            cop=Coordinate(1, 1),
            thief=Coordinate(0, 0),
            active=Role.COP,
            barriers=frozenset({Coordinate(2, 2)}),
            barriers_placed=5,
        )

        self.assertEqual(legal_barrier_actions(state, max_barriers=5), tuple())
        with self.assertRaisesRegex(DomainError, "maximum barrier"):
            apply_action(
                state,
                role=Role.COP,
                action=PlaceBarrierAction(Coordinate(1, 2)),
                max_barriers=5,
            )

    def test_rejects_barrier_that_traps_either_player(self) -> None:
        state = _state(
            grid=GridSize(3, 3),
            cop=Coordinate(1, 1),
            thief=Coordinate(0, 0),
            active=Role.COP,
            barriers=frozenset({Coordinate(0, 1)}),
            barriers_placed=1,
        )

        self.assertNotIn(
            PlaceBarrierAction(Coordinate(1, 0)),
            legal_barrier_actions(state, max_barriers=5),
        )
        with self.assertRaisesRegex(DomainError, "illegal barrier"):
            apply_action(state, role=Role.COP, action=PlaceBarrierAction(Coordinate(1, 0)))

    def test_barriers_are_impassable_to_both_roles(self) -> None:
        state = _state(
            cop=Coordinate(1, 1),
            thief=Coordinate(0, 1),
            active=Role.COP,
            barriers=frozenset({Coordinate(1, 2), Coordinate(0, 2)}),
            barriers_placed=2,
        )

        self.assertNotIn(Direction.RIGHT, {a.direction for a in legal_move_actions(state, Role.COP)})
        self.assertNotIn(Direction.RIGHT, {a.direction for a in legal_move_actions(state, Role.THIEF)})


class ScoringAndReplayTests(unittest.TestCase):
    def test_score_lookup_uses_configured_matrix(self) -> None:
        scoring = ScoreMatrix(cop_win=20, thief_win=10, cop_loss=5, thief_loss=5)
        cop_win = replace(
            _state(active=Role.COP),
            terminal_outcome=TerminalOutcome.COP_WIN,
            terminal_reason=TerminalReason.CAPTURE,
        )
        thief_win = replace(
            _state(active=Role.COP),
            terminal_outcome=TerminalOutcome.THIEF_WIN,
            terminal_reason=TerminalReason.MOVE_LIMIT,
        )

        self.assertEqual(score_state(cop_win, scoring).cop, 20)
        self.assertEqual(score_state(cop_win, scoring).thief, 5)
        self.assertEqual(score_state(thief_win, scoring).cop, 5)
        self.assertEqual(score_state(thief_win, scoring).thief, 10)

    def test_score_matrix_can_be_built_from_loaded_config(self) -> None:
        config = load_config("config.json")
        scoring = ScoreMatrix.from_config(config.game.scoring)

        self.assertEqual(scoring.cop_win, 20)
        self.assertEqual(scoring.thief_win, 10)
        self.assertEqual(scoring.cop_loss, 5)
        self.assertEqual(scoring.thief_loss, 5)

    def test_score_rejects_agent_supplied_or_non_terminal_data(self) -> None:
        with self.assertRaisesRegex(DomainError, "non-terminal"):
            score_state(_state(), ScoreMatrix())
        with self.assertRaisesRegex(DomainError, "non-negative"):
            ScoreMatrix(cop_win=-1)

    def test_replay_is_deterministic_for_same_action_sequence(self) -> None:
        initial = _state(
            grid=GridSize(3, 3),
            cop=Coordinate(2, 2),
            thief=Coordinate(0, 0),
            active=Role.THIEF,
        )
        actions = (
            (Role.THIEF, MoveAction(Direction.RIGHT)),
            (Role.COP, MoveAction(Direction.LEFT)),
            (Role.THIEF, MoveAction(Direction.RIGHT)),
            (Role.COP, MoveAction(Direction.UP)),
        )

        first = replay_actions(initial, actions)
        second = replay_actions(initial, actions)

        self.assertEqual(first, second)
        self.assertEqual(first.move_round, 2)
        self.assertEqual(first.active_role, Role.THIEF)


class SmallBoardProgressiveTests(unittest.TestCase):
    def test_exhaustive_2x2_legal_actions_stay_in_bounds_or_terminal(self) -> None:
        grid = GridSize(2, 2)
        cells = grid.all_coordinates()

        for cop in cells:
            for thief in cells:
                for active in (Role.COP, Role.THIEF):
                    state = _state(grid=grid, cop=cop, thief=thief, active=active)
                    for action in legal_actions(state):
                        next_state = apply_action(state, role=active, action=action)
                        self.assertTrue(grid.contains(next_state.cop_position))
                        self.assertTrue(grid.contains(next_state.thief_position))
                        self.assertTrue(all(grid.contains(barrier) for barrier in next_state.barriers))

    def test_progressive_grid_sanity_for_seeded_initialization_and_legal_moves(self) -> None:
        for rows, columns in ((3, 2), (3, 3), (4, 3), (4, 4), (5, 5)):
            grid = GridSize(rows, columns)
            state = create_initial_state(grid=grid, seed=rows * 100 + columns)
            self.assertNotEqual(state.cop_position, state.thief_position)
            self.assertGreater(len(legal_move_actions(state, Role.THIEF)), 0)
            self.assertGreater(len(legal_move_actions(state, Role.COP)), 0)


if __name__ == "__main__":
    unittest.main()
