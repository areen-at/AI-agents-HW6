from __future__ import annotations

import io
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ai_agents_hw6.application.events import redact, state_to_json
from ai_agents_hw6.application.series import SeriesSettings, run_series
from ai_agents_hw6.domain import (
    Coordinate,
    GridSize,
    MoveAction,
    ScoreMatrix,
    create_initial_state,
)
from ai_agents_hw6.domain.enums import Direction
from ai_agents_hw6.ui import (
    COORDINATE_HELP,
    TerminalObserver,
    render_board,
    render_state,
    replay_events,
)


class TerminalRenderingTests(unittest.TestCase):
    def test_rectangular_board_has_labels_and_unambiguous_symbols(self) -> None:
        state = replace(
            create_initial_state(grid=GridSize(3, 5), seed=7),
            cop_position=Coordinate(0, 0),
            thief_position=Coordinate(2, 4),
            barriers=frozenset({Coordinate(1, 2)}),
            barriers_placed=1,
        )

        rendered = render_board(state)

        self.assertIn("0 1 2 3 4", rendered)
        self.assertIn("0 | C", rendered)
        self.assertIn("1 | . . #", rendered)
        self.assertIn("2 | . . . . T", rendered)
        self.assertIn("C=Cop T=Thief #=barrier .=empty", rendered)

    def test_state_view_includes_ids_round_role_barriers_action_scores_and_orientation(
        self,
    ) -> None:
        state = create_initial_state(grid=GridSize(5, 5), seed=8)
        rendered = render_state(
            state,
            valid_game_index=2,
            attempt_number=3,
            max_barriers=5,
            action=MoveAction(Direction.RIGHT),
            validation="accepted",
            totals={"cop": 20, "thief": 5},
        )

        self.assertIn(str(state.series_id), rendered)
        self.assertIn(str(state.sub_game_id), rendered)
        self.assertIn(str(state.attempt_id), rendered)
        self.assertIn("Game 2/6", rendered)
        self.assertIn("Active role: thief", rendered)
        self.assertIn("remaining=5", rendered)
        self.assertIn("move right", rendered)
        self.assertIn("Validation: accepted", rendered)
        self.assertIn("Cop=20 Thief=5", rendered)
        self.assertIn(COORDINATE_HELP, rendered)

    def test_renderer_does_not_mutate_authoritative_state(self) -> None:
        state = create_initial_state(grid=GridSize(5, 5), seed=9)
        before = state_to_json(state)
        render_board(state)
        render_state(
            state,
            valid_game_index=1,
            attempt_number=1,
            max_barriers=5,
        )
        self.assertEqual(state_to_json(state), before)


class OperationalLoggingTests(unittest.TestCase):
    def test_quiet_mode_suppresses_human_board_but_json_mode_emits_redacted_events(self) -> None:
        stream = io.StringIO()
        observer = TerminalObserver(
            max_barriers=5,
            stream=stream,
            quiet=True,
            json_logs=True,
            log_level="INFO",
        )
        state = create_initial_state(grid=GridSize(5, 5), seed=10)
        observer.on_event(
            {
                "event_type": "attempt_invalid",
                "valid_game_index": 1,
                "attempt_number": 1,
                "payload": {
                    "failure_reason": "mcp_timeout",
                    "failure_detail": "Authorization: Bearer super-secret",
                },
            },
            state,
        )

        output = stream.getvalue()
        self.assertIn('"event_type": "attempt_invalid"', output)
        self.assertNotIn("super-secret", output)
        self.assertNotIn("Legend:", output)

    def test_redaction_covers_nested_keys_bearer_tokens_and_assignments(self) -> None:
        value = redact(
            {
                "authorization": "Bearer abc",
                "detail": "request failed Bearer xyz token=my-token password:guess",
            }
        )
        serialized = json.dumps(value)
        self.assertNotIn("abc", serialized)
        self.assertNotIn("xyz", serialized)
        self.assertNotIn("my-token", serialized)
        self.assertNotIn("guess", serialized)

    def test_log_level_suppresses_info_but_keeps_warning_events(self) -> None:
        stream = io.StringIO()
        observer = TerminalObserver(
            max_barriers=5,
            stream=stream,
            quiet=True,
            json_logs=True,
            log_level="WARNING",
        )
        state = create_initial_state(grid=GridSize(5, 5), seed=11)
        observer.on_event(
            {
                "event_type": "attempt_started",
                "valid_game_index": 1,
                "attempt_number": 1,
                "payload": {},
            },
            state,
        )
        observer.on_event(
            {
                "event_type": "attempt_invalid",
                "valid_game_index": 1,
                "attempt_number": 1,
                "payload": {"failure_reason": "mcp_timeout", "failure_detail": "safe"},
            },
            state,
        )
        self.assertNotIn("attempt_started", stream.getvalue())
        self.assertIn("attempt_invalid", stream.getvalue())

    def test_observer_reports_technical_replacement_and_terminal_totals(self) -> None:
        stream = io.StringIO()
        observer = TerminalObserver(max_barriers=5, stream=stream)
        failed = False

        def provider(state):
            nonlocal failed
            if not failed:
                failed = True
                from ai_agents_hw6.application.series import TechnicalFailure
                from ai_agents_hw6.domain import TechnicalFailureReason

                raise TechnicalFailure(TechnicalFailureReason.MCP_TIMEOUT, "simulated")
            from ai_agents_hw6.application.series import first_legal_action_provider

            return first_legal_action_provider(state)

        result = run_series(
            settings=SeriesSettings(
                grid=GridSize(3, 3),
                max_moves=1,
                technical_attempt_limit_per_slot=3,
            ),
            scoring=ScoreMatrix(),
            decision_provider=provider,
            observer=observer,
        )

        output = stream.getvalue()
        self.assertIn("Technical failure:", output)
        self.assertIn("replacement_attempt=2", output)
        self.assertIn("Terminal:", output)
        self.assertIn("Series complete: valid_games=6", output)
        self.assertEqual(observer.totals, result.totals)

    def test_replay_console_uses_committed_snapshots_without_agent_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            event_path = Path(temp_dir) / "events.json"
            run_series(
                settings=SeriesSettings(
                    grid=GridSize(3, 3),
                    max_moves=1,
                    event_log_path=str(event_path),
                ),
                scoring=ScoreMatrix(),
                decision_provider=lambda state: MoveAction(
                    Direction.RIGHT
                    if state.thief_position.column < state.grid.columns - 1
                    else Direction.LEFT
                ),
            )
            stream = io.StringIO()
            rendered = replay_events(event_path, stream=stream, max_barriers=5)

        self.assertGreaterEqual(rendered, 12)
        self.assertIn("Legend:", stream.getvalue())
        self.assertIn("authoritative committed state", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
