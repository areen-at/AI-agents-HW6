from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import URLError

from ai_agents_hw6.application import (
    LocalMcpDecisionProvider,
    McpClientError,
    RoleMcpClient,
    preflight_clients,
    run_local_mcp_series,
)
from ai_agents_hw6.application.mcp_client import McpClientConfig
from ai_agents_hw6.application.series import SeriesSettings, TechnicalFailure, run_series
from ai_agents_hw6.config import load_config
from ai_agents_hw6.domain import Coordinate, GameState, GridSize, Role, ScoreMatrix, TechnicalFailureReason
from ai_agents_hw6.domain import MoveAction
from ai_agents_hw6.mcp_servers.http_server import build_server
from ai_agents_hw6.ui import render_series_summary


class LocalServerPair:
    def __init__(self) -> None:
        self.cop_server = build_server(role=Role.COP, host="127.0.0.1", port=0)
        self.thief_server = build_server(role=Role.THIEF, host="127.0.0.1", port=0)
        self.cop_thread = threading.Thread(target=self.cop_server.serve_forever, daemon=True)
        self.thief_thread = threading.Thread(target=self.thief_server.serve_forever, daemon=True)

    def __enter__(self) -> "LocalServerPair":
        self.cop_thread.start()
        self.thief_thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cop_server.shutdown()
        self.thief_server.shutdown()
        self.cop_thread.join(timeout=5)
        self.thief_thread.join(timeout=5)
        self.cop_server.server_close()
        self.thief_server.server_close()

    @property
    def cop_url(self) -> str:
        return f"http://127.0.0.1:{self.cop_server.server_port}"

    @property
    def thief_url(self) -> str:
        return f"http://127.0.0.1:{self.thief_server.server_port}"


class LocalMcpOrchestratorTests(unittest.TestCase):
    def test_preflight_accepts_healthy_role_servers(self) -> None:
        with LocalServerPair() as servers:
            preflight_clients(
                RoleMcpClient(role=Role.COP, base_url=servers.cop_url),
                RoleMcpClient(role=Role.THIEF, base_url=servers.thief_url),
            )

    def test_preflight_refuses_missing_server(self) -> None:
        with self.assertRaises(McpClientError):
            preflight_clients(
                RoleMcpClient(role=Role.COP, base_url="http://127.0.0.1:1", timeout_seconds=1),
                RoleMcpClient(role=Role.THIEF, base_url="http://127.0.0.1:1", timeout_seconds=1),
            )

    def test_preflight_refuses_wrong_role_identity(self) -> None:
        with LocalServerPair() as servers:
            with self.assertRaisesRegex(McpClientError, "identity mismatch"):
                preflight_clients(
                    RoleMcpClient(role=Role.COP, base_url=servers.thief_url),
                    RoleMcpClient(role=Role.THIEF, base_url=servers.thief_url),
                )

    def test_local_mcp_decision_provider_uses_thief_then_cop_servers(self) -> None:
        with LocalServerPair() as servers:
            provider = LocalMcpDecisionProvider(
                cop_client=RoleMcpClient(role=Role.COP, base_url=servers.cop_url),
                thief_client=RoleMcpClient(role=Role.THIEF, base_url=servers.thief_url),
                max_moves=25,
                max_barriers=5,
                manhattan_radius=2,
                max_retries=0,
            )
            state = _state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0))

            thief_action = provider.decide(state)

            self.assertIsInstance(thief_action, MoveAction)

    def test_exhausted_mcp_failures_become_invalid_attempts_and_replacements(self) -> None:
        class FlakyClient(RoleMcpClient):
            calls = 0

            def decide(self, payload: dict) -> dict:
                type(self).calls += 1
                if type(self).calls == 1:
                    raise McpClientError("simulated timeout")
                return super().decide(payload)

        with LocalServerPair() as servers:
            provider = LocalMcpDecisionProvider(
                cop_client=RoleMcpClient(role=Role.COP, base_url=servers.cop_url),
                thief_client=FlakyClient(role=Role.THIEF, base_url=servers.thief_url),
                max_moves=1,
                max_barriers=5,
                manhattan_radius=2,
                max_retries=0,
            )
            result = run_series(
                settings=SeriesSettings(
                    grid=GridSize(3, 3),
                    num_games=6,
                    max_moves=1,
                    max_barriers=5,
                    random_seed=55,
                    technical_attempt_limit_per_slot=3,
                ),
                scoring=ScoreMatrix(),
                decision_provider=provider.decide,
            )

        self.assertEqual(len(result.valid_sub_games), 6)
        self.assertEqual(len(result.invalid_attempts), 1)
        self.assertEqual(result.invalid_attempts[0].failure_reason, TechnicalFailureReason.MCP_TIMEOUT)

    def test_malformed_response_is_retried_or_marked_technical_failure(self) -> None:
        class MalformedClient(RoleMcpClient):
            def decide(self, payload: dict) -> dict:
                return {"request_id": payload["request_id"], "correlation_id": "wrong", "decision": {}}

        provider = LocalMcpDecisionProvider(
            cop_client=MalformedClient(role=Role.COP, base_url="http://unused"),
            thief_client=MalformedClient(role=Role.THIEF, base_url="http://unused"),
            max_moves=25,
            max_barriers=5,
            manhattan_radius=2,
            max_retries=0,
        )

        with self.assertRaisesRegex(TechnicalFailure, "exhausted MCP"):
            provider.decide(_state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0)))

    def test_duplicate_response_is_rejected(self) -> None:
        with LocalServerPair() as servers:
            provider = LocalMcpDecisionProvider(
                cop_client=RoleMcpClient(role=Role.COP, base_url=servers.cop_url),
                thief_client=RoleMcpClient(role=Role.THIEF, base_url=servers.thief_url),
                max_moves=25,
                max_barriers=5,
                manhattan_radius=2,
                max_retries=0,
            )
            state = _state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0))
            original_decide = provider.thief_client.decide

            def duplicate_then_return(payload: dict) -> dict:
                provider._applied_request_ids.add(payload["request_id"])
                return original_decide(payload)

            provider.thief_client.decide = duplicate_then_return  # type: ignore[method-assign]
            with self.assertRaisesRegex(TechnicalFailure, "duplicate response"):
                provider.decide(state)

    def test_complete_six_game_series_through_local_servers_and_report(self) -> None:
        with LocalServerPair() as servers, tempfile.TemporaryDirectory() as temp_dir:
            config_path = _write_temp_config(Path(temp_dir), servers.cop_url, servers.thief_url)
            config = load_config(config_path)
            result = run_local_mcp_series(config)
            summary = render_series_summary(result)

        self.assertEqual(len(result.valid_sub_games), 6)
        self.assertEqual(result.invalid_attempts, tuple())
        self.assertIn("Game 1:", summary)
        self.assertIn("Totals:", summary)


def _state(*, active: Role, cop: Coordinate, thief: Coordinate) -> GameState:
    from ai_agents_hw6.domain import AttemptId, SeriesId, SubGameId

    return GameState(
        series_id=SeriesId.new(),
        sub_game_id=SubGameId.new(),
        attempt_id=AttemptId.new(),
        grid=GridSize(5, 5),
        cop_position=cop,
        thief_position=thief,
        active_role=active,
        seed=1,
    )


def _write_temp_config(path: Path, cop_url: str, thief_url: str) -> Path:
    config = json.loads(Path("config.json").read_text(encoding="utf-8"))
    config["my_servers"]["cop_mcp_url"] = cop_url
    config["my_servers"]["thief_mcp_url"] = thief_url
    config["logging"]["event_log_dir"] = str(path / "logs")
    config["reports"]["internal_game_report"] = str(path / "reports" / "internal_game_report.json")
    config_path = path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


if __name__ == "__main__":
    unittest.main()
