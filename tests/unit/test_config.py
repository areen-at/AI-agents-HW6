from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_agents_hw6.config import (
    ConfigError,
    load_config,
    validate_for_mode,
    validate_for_public_deployment,
)


def _write_config(tmp_path: Path, overrides: dict | None = None) -> Path:
    data = {
        "group": {
            "name": "MY_GROUP_NAME",
            "github_repo": "https://github.com/areen-at/AI-agents-HW6",
            "students": [],
        },
        "my_servers": {
            "cop_mcp_url": "http://127.0.0.1:8001/mcp",
            "thief_mcp_url": "http://127.0.0.1:8002/mcp",
        },
        "bonus_opponent": {
            "group_name": "OTHER_TEAM_NAME",
            "github_repo": "https://example.com/other-team-repo",
            "students": [],
            "cop_mcp_url": "https://example.com/other-team-cop-mcp",
            "thief_mcp_url": "https://example.com/other-team-thief-mcp",
        },
        "game": {
            "grid_size": [5, 5],
            "max_moves": 25,
            "num_games": 6,
            "max_barriers": 5,
            "scoring": {
                "cop_win": 20,
                "thief_win": 10,
                "cop_loss": 5,
                "thief_loss": 5,
            },
        },
        "observation": {"manhattan_radius": 2},
        "runtime": {
            "timezone": "Asia/Jerusalem",
            "random_seed": 12345,
            "decision_timeout_seconds": 20,
            "max_retries": 2,
            "technical_attempt_limit_per_slot": 10,
        },
        "reports": {
            "internal_game_report": "reports/internal_game_report.json",
            "bonus_game_report": "reports/bonus_game_report.json",
            "bonus_mock_report": "reports/bonus_game_report.mock.json",
        },
        "logging": {"level": "INFO", "event_log_dir": "artifacts/logs"},
    }
    if overrides:
        _deep_update(data, overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _deep_update(target: dict, updates: dict) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


class ConfigTests(unittest.TestCase):
    def test_malformed_json_is_rejected_with_path_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text('{"group":', encoding="utf-8")

            with self.assertRaisesRegex(ConfigError, "invalid JSON"):
                load_config(path)

    def test_default_config_loads_and_validates_for_internal_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(_write_config(Path(temp_dir)))

        validate_for_mode(config, "internal")

        self.assertEqual(config.game.grid_size, (5, 5))
        self.assertEqual(config.game.num_games, 6)
        self.assertEqual(config.game.scoring.cop_win, 20)
        self.assertEqual(config.runtime.timezone, "Asia/Jerusalem")

    def test_bonus_mode_rejects_placeholder_opponent_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(_write_config(Path(temp_dir)))

        with self.assertRaisesRegex(ConfigError, "bonus_opponent.group_name"):
            validate_for_mode(config, "bonus")

    def test_bonus_mock_mode_allows_placeholder_opponent_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(_write_config(Path(temp_dir)))

        validate_for_mode(config, "bonus-mock")

    def test_bonus_mode_requires_https_opponent_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(
                _write_config(
                    Path(temp_dir),
                    {
                        "bonus_opponent": {
                            "group_name": "Real Opponent",
                            "github_repo": "https://github.com/example/opponent",
                            "cop_mcp_url": "http://opponent.example/cop",
                            "thief_mcp_url": "https://opponent.example/thief",
                        }
                    },
                )
            )

        with self.assertRaisesRegex(ConfigError, "bonus_opponent.cop_mcp_url"):
            validate_for_mode(config, "bonus")

    def test_invalid_grid_size_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_config(Path(temp_dir), {"game": {"grid_size": [1, 5]}})

            with self.assertRaisesRegex(ConfigError, "game.grid_size"):
                load_config(path)

    def test_num_games_must_be_six_for_configured_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(_write_config(Path(temp_dir), {"game": {"num_games": 3}}))

        with self.assertRaisesRegex(ConfigError, "num_games"):
            validate_for_mode(config, "internal")

    def test_my_server_urls_must_be_valid_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(
                _write_config(
                    Path(temp_dir),
                    {"my_servers": {"cop_mcp_url": "not-a-url"}},
                )
            )

        with self.assertRaisesRegex(ConfigError, "my_servers.cop_mcp_url"):
            validate_for_mode(config, "internal")

    def test_blank_student_names_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_config(Path(temp_dir), {"group": {"students": [" "]}})

            with self.assertRaisesRegex(ConfigError, "group.students"):
                load_config(path)

    def test_logging_level_is_normalized_and_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(_write_config(Path(temp_dir), {"logging": {"level": "debug"}}))

        self.assertEqual(config.logging.level, "DEBUG")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_config(Path(temp_dir), {"logging": {"level": "LOUD"}})

            with self.assertRaisesRegex(ConfigError, "logging.level"):
                load_config(path)

    def test_public_deployment_requires_distinct_https_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            valid = load_config(
                _write_config(
                    Path(temp_dir),
                    {
                        "my_servers": {
                            "cop_mcp_url": "https://cop.example.net/mcp",
                            "thief_mcp_url": "https://thief.example.net/mcp",
                        }
                    },
                )
            )
        validate_for_public_deployment(valid)

        with tempfile.TemporaryDirectory() as temp_dir:
            duplicate = load_config(
                _write_config(
                    Path(temp_dir),
                    {
                        "my_servers": {
                            "cop_mcp_url": "https://same.example.net/mcp",
                            "thief_mcp_url": "https://same.example.net/mcp",
                        }
                    },
                )
            )
        with self.assertRaisesRegex(ConfigError, "distinct"):
            validate_for_public_deployment(duplicate)

        with self.assertRaisesRegex(ConfigError, "HTTPS"):
            validate_for_public_deployment(load_config("config.json"))


if __name__ == "__main__":
    unittest.main()
