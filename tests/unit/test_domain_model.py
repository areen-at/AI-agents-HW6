from __future__ import annotations

import ast
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from ai_agents_hw6.domain import (
    ActionType,
    AttemptId,
    Coordinate,
    Direction,
    DomainError,
    GameState,
    GridSize,
    Role,
    SeriesId,
    SubGameId,
    TechnicalFailureReason,
    TerminalOutcome,
    TerminalReason,
    create_initial_state,
    direction_delta,
)


class DomainValueObjectTests(unittest.TestCase):
    def test_enums_use_protocol_values(self) -> None:
        self.assertEqual(Role.COP.value, "cop")
        self.assertEqual(Role.THIEF.value, "thief")
        self.assertEqual(ActionType.MOVE.value, "move")
        self.assertEqual(ActionType.PLACE_BARRIER.value, "place_barrier")
        self.assertEqual(TerminalOutcome.COP_WIN.value, "cop_win")
        self.assertEqual(TerminalReason.CAPTURE.value, "capture")
        self.assertEqual(TechnicalFailureReason.MCP_TIMEOUT.value, "mcp_timeout")

    def test_coordinate_serialization_and_immutability(self) -> None:
        coordinate = Coordinate(2, 3)

        self.assertEqual(coordinate.to_json(), [2, 3])
        self.assertEqual(Coordinate.from_json([2, 3]), coordinate)
        with self.assertRaises(FrozenInstanceError):
            coordinate.row = 4  # type: ignore[misc]

    def test_coordinate_rejects_invalid_values(self) -> None:
        with self.assertRaisesRegex(DomainError, "row"):
            Coordinate(-1, 0)
        with self.assertRaisesRegex(DomainError, "column"):
            Coordinate(0, True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(DomainError, "JSON"):
            Coordinate.from_json([1])

    def test_grid_size_contains_corners_edges_and_interior(self) -> None:
        grid = GridSize(5, 5)

        self.assertTrue(grid.contains(Coordinate(0, 0)))
        self.assertTrue(grid.contains(Coordinate(0, 4)))
        self.assertTrue(grid.contains(Coordinate(4, 0)))
        self.assertTrue(grid.contains(Coordinate(4, 4)))
        self.assertTrue(grid.contains(Coordinate(2, 2)))
        self.assertFalse(grid.contains(Coordinate(5, 0)))
        self.assertFalse(grid.contains(Coordinate(0, 5)))

    def test_grid_size_serialization_and_validation(self) -> None:
        grid = GridSize(5, 4)

        self.assertEqual(grid.to_json(), [5, 4])
        self.assertEqual(GridSize.from_json([5, 4]), grid)
        with self.assertRaisesRegex(DomainError, "at least 2 by 2"):
            GridSize(1, 5)
        with self.assertRaisesRegex(DomainError, "JSON"):
            GridSize.from_json([5, "5"])

    def test_direction_delta_and_bounded_neighbors(self) -> None:
        grid = GridSize(3, 3)

        self.assertEqual(direction_delta(Direction.UP), (-1, 0))
        self.assertEqual(direction_delta(Direction.DOWN), (1, 0))
        self.assertEqual(direction_delta(Direction.LEFT), (0, -1))
        self.assertEqual(direction_delta(Direction.RIGHT), (0, 1))
        self.assertEqual(
            set(grid.bounded_neighbors(Coordinate(1, 1))),
            {
                Coordinate(0, 1),
                Coordinate(2, 1),
                Coordinate(1, 0),
                Coordinate(1, 2),
            },
        )
        self.assertEqual(
            set(grid.bounded_neighbors(Coordinate(0, 0))),
            {Coordinate(1, 0), Coordinate(0, 1)},
        )

    def test_identifier_creation_and_validation(self) -> None:
        series_id = SeriesId.new()
        sub_game_id = SubGameId.new()
        attempt_id = AttemptId.new()

        self.assertIsInstance(str(series_id), str)
        self.assertIsInstance(str(sub_game_id), str)
        self.assertIsInstance(str(attempt_id), str)
        with self.assertRaisesRegex(DomainError, "UUID"):
            SeriesId("not-a-uuid")


class GameStateTests(unittest.TestCase):
    def test_seeded_initialization_is_reproducible_and_distinct(self) -> None:
        grid = GridSize(5, 5)
        ids = {
            "series_id": SeriesId.new(),
            "sub_game_id": SubGameId.new(),
            "attempt_id": AttemptId.new(),
        }

        first = create_initial_state(grid=grid, seed=12345, **ids)
        second = create_initial_state(grid=grid, seed=12345, **ids)

        self.assertEqual(first, second)
        self.assertEqual(first.active_role, Role.THIEF)
        self.assertEqual(first.move_round, 0)
        self.assertEqual(first.barriers, frozenset())
        self.assertEqual(first.barriers_placed, 0)
        self.assertNotEqual(first.cop_position, first.thief_position)
        self.assertTrue(grid.contains(first.cop_position))
        self.assertTrue(grid.contains(first.thief_position))

    def test_game_state_normalizes_barriers_to_immutable_frozenset(self) -> None:
        barriers = [Coordinate(1, 1)]
        state = GameState(
            series_id=SeriesId.new(),
            sub_game_id=SubGameId.new(),
            attempt_id=AttemptId.new(),
            grid=GridSize(3, 3),
            cop_position=Coordinate(0, 0),
            thief_position=Coordinate(2, 2),
            active_role=Role.THIEF,
            seed=7,
            barriers=barriers,
            barriers_placed=1,
        )

        barriers.append(Coordinate(1, 2))

        self.assertEqual(state.barriers, frozenset({Coordinate(1, 1)}))
        with self.assertRaises(AttributeError):
            state.barriers.add(Coordinate(1, 2))  # type: ignore[attr-defined]

    def test_game_state_rejects_invalid_positions_and_barriers(self) -> None:
        base = {
            "series_id": SeriesId.new(),
            "sub_game_id": SubGameId.new(),
            "attempt_id": AttemptId.new(),
            "grid": GridSize(3, 3),
            "cop_position": Coordinate(0, 0),
            "thief_position": Coordinate(2, 2),
            "active_role": Role.THIEF,
            "seed": 1,
        }

        with self.assertRaisesRegex(DomainError, "cop_position"):
            GameState(**{**base, "cop_position": Coordinate(3, 0)})
        with self.assertRaisesRegex(DomainError, "inside the grid"):
            GameState(**{**base, "barriers": [Coordinate(3, 0)], "barriers_placed": 1})
        with self.assertRaisesRegex(DomainError, "Cop"):
            GameState(**{**base, "barriers": [Coordinate(0, 0)], "barriers_placed": 1})
        with self.assertRaisesRegex(DomainError, "current barriers"):
            GameState(**{**base, "barriers": [Coordinate(1, 1)], "barriers_placed": 0})

    def test_game_state_rejects_bad_counters_and_terminal_metadata(self) -> None:
        base = {
            "series_id": SeriesId.new(),
            "sub_game_id": SubGameId.new(),
            "attempt_id": AttemptId.new(),
            "grid": GridSize(3, 3),
            "cop_position": Coordinate(0, 0),
            "thief_position": Coordinate(2, 2),
            "active_role": Role.THIEF,
            "seed": 1,
        }

        with self.assertRaisesRegex(DomainError, "move_round"):
            GameState(**{**base, "move_round": -1})
        with self.assertRaisesRegex(DomainError, "barriers_placed"):
            GameState(**{**base, "barriers_placed": -1})
        with self.assertRaisesRegex(DomainError, "active_role"):
            GameState(**{**base, "active_role": "thief"})
        with self.assertRaisesRegex(DomainError, "set together"):
            GameState(**{**base, "terminal_outcome": TerminalOutcome.COP_WIN})

    def test_terminal_state_metadata_can_be_set_together(self) -> None:
        state = GameState(
            series_id=SeriesId.new(),
            sub_game_id=SubGameId.new(),
            attempt_id=AttemptId.new(),
            grid=GridSize(3, 3),
            cop_position=Coordinate(0, 0),
            thief_position=Coordinate(2, 2),
            active_role=Role.COP,
            seed=1,
            terminal_outcome=TerminalOutcome.COP_WIN,
            terminal_reason=TerminalReason.CAPTURE,
        )

        self.assertTrue(state.is_terminal)


class DomainBoundaryTests(unittest.TestCase):
    def test_domain_layer_does_not_import_later_layers(self) -> None:
        forbidden_fragments = {
            "ai_agents_hw6.agents",
            "ai_agents_hw6.application",
            "ai_agents_hw6.contracts",
            "ai_agents_hw6.infrastructure",
            "ai_agents_hw6.mcp_servers",
            "ai_agents_hw6.reporting",
            "ai_agents_hw6.ui",
        }
        domain_root = Path("src/ai_agents_hw6/domain")

        for file_path in domain_root.glob("*.py"):
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            for imported in imports:
                self.assertNotIn(imported, forbidden_fragments, file_path)


if __name__ == "__main__":
    unittest.main()
