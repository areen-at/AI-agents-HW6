from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_agents_hw6.application.events import redact, state_hash
from ai_agents_hw6.application.series import (
    SeriesSettings,
    TechnicalFailure,
    first_legal_action_provider,
    run_series,
)
from ai_agents_hw6.config import load_config
from ai_agents_hw6.domain import (
    GameAction,
    GameState,
    GridSize,
    ScoreMatrix,
    TechnicalFailureReason,
    create_initial_state,
    replay_actions,
)
from ai_agents_hw6.reporting import build_internal_report, write_internal_report


class SeriesControlTests(unittest.TestCase):
    def test_series_completes_exactly_six_valid_games_and_no_seventh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SeriesSettings(
                grid=GridSize(3, 3),
                num_games=6,
                max_moves=1,
                max_barriers=5,
                random_seed=100,
                technical_attempt_limit_per_slot=3,
                event_log_path=str(Path(temp_dir) / "events.json"),
            )

            result = run_series(
                settings=settings,
                scoring=ScoreMatrix(),
                decision_provider=first_legal_action_provider,
            )

            self.assertEqual(len(result.valid_sub_games), 6)
            self.assertEqual([game.index for game in result.valid_sub_games], [1, 2, 3, 4, 5, 6])
            self.assertEqual(result.invalid_attempts, tuple())
            self.assertEqual(
                result.totals,
                {
                    "cop": sum(game.cop_score for game in result.valid_sub_games),
                    "thief": sum(game.thief_score for game in result.valid_sub_games),
                },
            )
            self.assertTrue(Path(settings.event_log_path or "").exists())

    def test_invalid_attempt_is_preserved_and_replaced_without_scoring(self) -> None:
        failed_once = False

        def provider(state: GameState) -> GameAction:
            nonlocal failed_once
            if not failed_once:
                failed_once = True
                raise TechnicalFailure(
                    TechnicalFailureReason.MALFORMED_RESPONSE,
                    "simulated malformed response",
                )
            return first_legal_action_provider(state)

        result = run_series(
            settings=SeriesSettings(
                grid=GridSize(3, 3),
                num_games=6,
                max_moves=1,
                random_seed=200,
                technical_attempt_limit_per_slot=3,
            ),
            scoring=ScoreMatrix(),
            decision_provider=provider,
        )

        self.assertEqual(len(result.valid_sub_games), 6)
        self.assertEqual(len(result.invalid_attempts), 1)
        self.assertFalse(result.invalid_attempts[0].valid)
        self.assertEqual(
            result.invalid_attempts[0].failure_reason,
            TechnicalFailureReason.MALFORMED_RESPONSE,
        )
        self.assertEqual(result.valid_sub_games[0].attempt_number, 2)
        self.assertEqual(
            result.totals,
            {
                "cop": sum(game.cop_score for game in result.valid_sub_games),
                "thief": sum(game.thief_score for game in result.valid_sub_games),
            },
        )

    def test_attempt_limit_prevents_silent_strategy_loss(self) -> None:
        def failing_provider(state: GameState) -> GameAction:
            raise TechnicalFailure(TechnicalFailureReason.MCP_TIMEOUT, "simulated timeout")

        with self.assertRaisesRegex(RuntimeError, "technical attempt limit"):
            run_series(
                settings=SeriesSettings(
                    grid=GridSize(3, 3),
                    num_games=6,
                    max_moves=1,
                    random_seed=300,
                    technical_attempt_limit_per_slot=2,
                ),
                scoring=ScoreMatrix(),
                decision_provider=failing_provider,
            )

    def test_events_are_append_only_redacted_and_replayable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SeriesSettings(
                grid=GridSize(3, 3),
                num_games=6,
                max_moves=1,
                random_seed=400,
                technical_attempt_limit_per_slot=3,
                event_log_path=str(Path(temp_dir) / "events.json"),
            )
            result = run_series(
                settings=settings,
                scoring=ScoreMatrix(),
                decision_provider=first_legal_action_provider,
            )
            events = json.loads(Path(settings.event_log_path or "").read_text(encoding="utf-8"))

        self.assertEqual(events, list(result.events))
        self.assertGreater(len(events), 0)
        self.assertTrue(all(event["schema_version"] == "1.0" for event in events))
        self.assertEqual(
            redact({"nested": {"api_token": "abc", "safe": "ok"}}),
            {"nested": {"api_token": "[REDACTED]", "safe": "ok"}},
        )

        first_game = result.valid_sub_games[0]
        replayed = replay_actions(
            create_initial_state(
                grid=settings.grid,
                seed=first_game.seed,
                series_id=result.series_id,
                sub_game_id=first_game.sub_game_id,
                attempt_id=first_game.attempt_id,
            ),
            first_game.accepted_actions,
            max_moves=settings.max_moves,
            max_barriers=settings.max_barriers,
        )
        self.assertEqual(state_hash(replayed), first_game.final_state_hash)


class InternalReportTests(unittest.TestCase):
    def test_internal_report_contains_metadata_six_games_and_calculated_totals(self) -> None:
        config = load_config("config.json")
        result = run_series(
            settings=SeriesSettings(
                grid=GridSize(3, 3),
                num_games=6,
                max_moves=1,
                random_seed=500,
                technical_attempt_limit_per_slot=3,
            ),
            scoring=ScoreMatrix.from_config(config.game.scoring),
            decision_provider=first_legal_action_provider,
        )

        report = build_internal_report(config, result)

        self.assertEqual(report["group_name"], config.group.name)
        self.assertEqual(report["github_repo"], config.group.github_repo)
        self.assertEqual(report["cop_mcp_url"], config.my_servers.cop_mcp_url)
        self.assertEqual(report["thief_mcp_url"], config.my_servers.thief_mcp_url)
        self.assertEqual(len(report["sub_games"]), 6)
        self.assertEqual(
            report["totals"],
            {
                "cop": sum(game.cop_score for game in result.valid_sub_games),
                "thief": sum(game.thief_score for game in result.valid_sub_games),
            },
        )

    def test_internal_report_is_written_atomically_as_json_only(self) -> None:
        config = load_config("config.json")
        result = run_series(
            settings=SeriesSettings(
                grid=GridSize(3, 3),
                num_games=6,
                max_moves=1,
                random_seed=600,
                technical_attempt_limit_per_slot=3,
            ),
            scoring=ScoreMatrix.from_config(config.game.scoring),
            decision_provider=first_legal_action_provider,
        )
        report = build_internal_report(config, result)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "internal_game_report.json"
            write_internal_report(path, report)
            stored = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(stored["totals"], report["totals"])
        self.assertEqual(len(stored["sub_games"]), 6)

    def test_internal_report_rejects_incomplete_series(self) -> None:
        config = load_config("config.json")
        result = run_series(
            settings=SeriesSettings(
                grid=GridSize(3, 3),
                num_games=6,
                max_moves=1,
                random_seed=700,
                technical_attempt_limit_per_slot=3,
            ),
            scoring=ScoreMatrix(),
            decision_provider=first_legal_action_provider,
        )
        incomplete = result.__class__(
            series_id=result.series_id,
            valid_sub_games=result.valid_sub_games[:5],
            invalid_attempts=result.invalid_attempts,
            events=result.events,
            totals=result.totals,
        )

        with self.assertRaisesRegex(ValueError, "six valid"):
            build_internal_report(config, incomplete)


if __name__ == "__main__":
    unittest.main()
