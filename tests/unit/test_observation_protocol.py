from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError

from ai_agents_hw6.agents import heuristic_protocol_decision, heuristic_protocol_decision_provider
from ai_agents_hw6.application.series import SeriesSettings, run_series
from ai_agents_hw6.contracts import (
    ActionProtocolError,
    action_response_json,
    build_observation,
    classify_unrecoverable_error,
    parse_action_response,
    render_decision_prompt,
    should_request_repair,
)
from ai_agents_hw6.domain import (
    AttemptId,
    Coordinate,
    Direction,
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


def _state(
    *,
    cop: Coordinate = Coordinate(4, 4),
    thief: Coordinate = Coordinate(0, 0),
    active: Role = Role.THIEF,
    barriers: frozenset[Coordinate] = frozenset({Coordinate(0, 1), Coordinate(4, 3)}),
) -> GameState:
    return GameState(
        series_id=SeriesId.new(),
        sub_game_id=SubGameId.new(),
        attempt_id=AttemptId.new(),
        grid=GridSize(5, 5),
        cop_position=cop,
        thief_position=thief,
        active_role=active,
        seed=99,
        barriers=barriers,
        barriers_placed=len(barriers),
    )


class ObservationTests(unittest.TestCase):
    def test_observation_includes_allowed_role_information_only(self) -> None:
        state = _state()

        observation = build_observation(
            state,
            request_id="req-1",
            role=Role.THIEF,
            manhattan_radius=2,
            max_moves=25,
            max_barriers=5,
        )

        self.assertEqual(observation.self_position, Coordinate(0, 0))
        self.assertIsNone(observation.visible_opponent)
        self.assertEqual(observation.visible_barriers, frozenset({Coordinate(0, 1)}))
        self.assertEqual(observation.move_round, 0)
        self.assertEqual(observation.max_moves, 25)
        self.assertEqual(observation.barriers_placed, 2)
        self.assertEqual(observation.max_barriers, 5)
        self.assertTrue(all(isinstance(action, MoveAction) for action in observation.legal_actions))

    def test_opponent_visible_only_inside_radius(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(0, 0))

        visible = build_observation(state, request_id="req-2", role=Role.THIEF, manhattan_radius=2)
        hidden = build_observation(state, request_id="req-3", role=Role.THIEF, manhattan_radius=1)

        self.assertEqual(visible.visible_opponent, Coordinate(1, 1))
        self.assertIsNone(hidden.visible_opponent)

    def test_observation_is_immutable_and_public_json_has_no_hidden_state(self) -> None:
        state = _state(cop=Coordinate(4, 4), thief=Coordinate(0, 0))
        observation = build_observation(state, request_id="req-4", role=Role.THIEF)

        with self.assertRaises(FrozenInstanceError):
            observation.self_position = Coordinate(1, 1)  # type: ignore[misc]

        public_json = observation.to_public_json()
        serialized = json.dumps(public_json)

        self.assertNotIn("[4, 4]", serialized)
        self.assertNotIn("cop_position", serialized)
        self.assertNotIn("thief_position", serialized)
        self.assertNotIn("terminal", serialized)


class PromptTests(unittest.TestCase):
    def test_prompts_are_role_specific_and_json_only_contracts(self) -> None:
        thief_obs = build_observation(_state(), request_id="req-5", role=Role.THIEF)
        cop_obs = build_observation(
            _state(cop=Coordinate(1, 0), thief=Coordinate(0, 0), active=Role.COP),
            request_id="req-6",
            role=Role.COP,
        )

        thief_prompt = render_decision_prompt(thief_obs)
        cop_prompt = render_decision_prompt(cop_obs)

        self.assertIn("You are the Thief", thief_prompt)
        self.assertIn("avoid capture", thief_prompt)
        self.assertIn("Return exactly one JSON object", thief_prompt)
        self.assertNotIn("[4, 4]", thief_prompt)
        self.assertIn("You are the Cop", cop_prompt)
        self.assertIn("place_barrier", cop_prompt)

    def test_history_summary_is_bounded_by_caller_and_included(self) -> None:
        observation = build_observation(
            _state(),
            request_id="req-7",
            role=Role.THIEF,
            history_summary=("round 1: thief moved right",),
        )

        self.assertEqual(observation.to_public_json()["history_summary"], ["round 1: thief moved right"])


class ActionProtocolTests(unittest.TestCase):
    def test_valid_move_response_parses_and_matches_legal_actions(self) -> None:
        state = _state(active=Role.THIEF)
        observation = build_observation(state, request_id="req-8", role=Role.THIEF)
        action = observation.legal_actions[0]
        raw = action_response_json(
            protocol_version="1.0",
            request_id="req-8",
            role=Role.THIEF,
            action=action,
        )

        parsed = parse_action_response(raw, observation)

        self.assertEqual(parsed.action, action)
        self.assertEqual(parsed.request_id, "req-8")

    def test_valid_cop_barrier_response_parses(self) -> None:
        state = _state(cop=Coordinate(1, 1), thief=Coordinate(0, 0), active=Role.COP)
        observation = build_observation(state, request_id="req-9", role=Role.COP)
        barrier = next(action for action in observation.legal_actions if isinstance(action, PlaceBarrierAction))

        parsed = parse_action_response(
            action_response_json(
                protocol_version="1.0",
                request_id="req-9",
                role=Role.COP,
                action=barrier,
            ),
            observation,
        )

        self.assertEqual(parsed.action, barrier)

    def test_parser_rejects_malformed_oversized_unknown_and_mismatched_output(self) -> None:
        observation = build_observation(_state(), request_id="req-10", role=Role.THIEF)

        invalid_payloads = [
            "not-json",
            "x" * 2001,
            json.dumps([]),
            json.dumps(
                {
                    "protocol_version": "1.0",
                    "request_id": "req-10",
                    "role": "thief",
                    "action": {"type": "teleport"},
                }
            ),
            json.dumps(
                {
                    "protocol_version": "2.0",
                    "request_id": "req-10",
                    "role": "thief",
                    "action": {"type": "move", "direction": "right"},
                }
            ),
            json.dumps(
                {
                    "protocol_version": "1.0",
                    "request_id": "wrong",
                    "role": "thief",
                    "action": {"type": "move", "direction": "right"},
                }
            ),
            json.dumps(
                {
                    "protocol_version": "1.0",
                    "request_id": "req-10",
                    "role": "cop",
                    "action": {"type": "move", "direction": "right"},
                }
            ),
            json.dumps(
                {
                    "protocol_version": "1.0",
                    "request_id": "req-10",
                    "role": "thief",
                    "action": {"type": "move", "direction": "right", "target": [1, 1]},
                }
            ),
        ]

        for payload in invalid_payloads:
            with self.assertRaises(ActionProtocolError):
                parse_action_response(payload, observation)

    def test_parser_rejects_illegal_action_even_when_schema_is_valid(self) -> None:
        state = _state(thief=Coordinate(0, 0), active=Role.THIEF)
        observation = build_observation(state, request_id="req-11", role=Role.THIEF)
        raw = action_response_json(
            protocol_version="1.0",
            request_id="req-11",
            role=Role.THIEF,
            action=MoveAction(Direction.UP),
        )

        with self.assertRaisesRegex(ActionProtocolError, "not legal"):
            parse_action_response(raw, observation)

    def test_thief_barrier_response_is_rejected(self) -> None:
        observation = build_observation(_state(active=Role.THIEF), request_id="req-12", role=Role.THIEF)
        raw = json.dumps(
            {
                "protocol_version": "1.0",
                "request_id": "req-12",
                "role": "thief",
                "action": {"type": "place_barrier", "target": [1, 1]},
            }
        )

        with self.assertRaisesRegex(ActionProtocolError, "only Cop"):
            parse_action_response(raw, observation)

    def test_one_repair_then_technical_failure_policy(self) -> None:
        self.assertTrue(should_request_repair(1))
        self.assertFalse(should_request_repair(2))
        self.assertEqual(classify_unrecoverable_error(1), "repair_allowed")
        self.assertEqual(classify_unrecoverable_error(2), "technical_failure")


class HeuristicProtocolAdapterTests(unittest.TestCase):
    def test_heuristic_adapter_uses_observation_response_parser_contract(self) -> None:
        state = _state(cop=Coordinate(1, 0), thief=Coordinate(0, 0), active=Role.COP)
        observation = build_observation(state, request_id="req-13", role=Role.COP)

        raw_response = heuristic_protocol_decision(observation)
        parsed = parse_action_response(raw_response, observation)

        self.assertIn(parsed.action, legal_actions(state))

    def test_engine_only_series_runs_through_protocol_adapter(self) -> None:
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
            decision_provider=heuristic_protocol_decision_provider(max_barriers=5),
        )

        self.assertEqual(len(result.valid_sub_games), 6)


if __name__ == "__main__":
    unittest.main()
