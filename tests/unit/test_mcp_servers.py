from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ai_agents_hw6.contracts import build_observation
from ai_agents_hw6.domain import (
    AttemptId,
    Coordinate,
    GameState,
    GridSize,
    Role,
    SeriesId,
    SubGameId,
    legal_actions,
)
from ai_agents_hw6.mcp_servers import PROTOCOL_VERSION, McpServerError, RoleDecisionService
from ai_agents_hw6.mcp_servers.http_server import build_server
from ai_agents_hw6.mcp_servers.service import response_public_json


def _state(*, active: Role, cop: Coordinate, thief: Coordinate) -> GameState:
    return GameState(
        series_id=SeriesId.new(),
        sub_game_id=SubGameId.new(),
        attempt_id=AttemptId.new(),
        grid=GridSize(5, 5),
        cop_position=cop,
        thief_position=thief,
        active_role=active,
        seed=101,
    )


def _decision_payload(state: GameState, *, role: Role, request_id: str = "req-1") -> dict:
    observation = build_observation(state, request_id=request_id, role=role)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "correlation_id": "corr-1",
        "role": role.value,
        "observation": observation.to_public_json(),
    }


class RoleDecisionServiceTests(unittest.TestCase):
    def test_health_identity_and_capabilities_are_role_specific(self) -> None:
        cop = RoleDecisionService(Role.COP)
        thief = RoleDecisionService(Role.THIEF)

        self.assertEqual(cop.health()["status"], "ok")
        self.assertEqual(cop.identity()["role"], "cop")
        self.assertEqual(thief.identity()["role"], "thief")
        self.assertEqual(cop.capabilities()["protocol_version"], "1.0")
        self.assertIn("decide", cop.capabilities()["operations"])

    def test_valid_cop_and_thief_decisions_return_schema_valid_actions(self) -> None:
        cop_state = _state(active=Role.COP, cop=Coordinate(1, 0), thief=Coordinate(0, 0))
        thief_state = _state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0))

        cop_response = RoleDecisionService(Role.COP).decide(
            _decision_payload(cop_state, role=Role.COP, request_id="cop-1")
        )
        thief_response = RoleDecisionService(Role.THIEF).decide(
            _decision_payload(thief_state, role=Role.THIEF, request_id="thief-1")
        )

        self.assertEqual(cop_response["decision"]["role"], "cop")
        self.assertEqual(thief_response["decision"]["role"], "thief")
        self.assertIn(cop_response["action"], legal_actions(cop_state))
        self.assertIn(thief_response["action"], legal_actions(thief_state))

    def test_rejects_role_mismatch_protocol_mismatch_and_malformed_observation(self) -> None:
        state = _state(active=Role.COP, cop=Coordinate(1, 0), thief=Coordinate(0, 0))
        service = RoleDecisionService(Role.COP)

        role_mismatch = _decision_payload(state, role=Role.COP, request_id="bad-role")
        role_mismatch["role"] = "thief"
        with self.assertRaisesRegex(McpServerError, "role mismatch"):
            service.decide(role_mismatch)

        protocol_mismatch = _decision_payload(state, role=Role.COP, request_id="bad-version")
        protocol_mismatch["protocol_version"] = "2.0"
        with self.assertRaisesRegex(McpServerError, "protocol version"):
            service.decide(protocol_mismatch)

        malformed = _decision_payload(state, role=Role.COP, request_id="bad-observation")
        malformed["observation"] = {"role": "cop"}
        with self.assertRaisesRegex(McpServerError, "malformed observation"):
            service.decide(malformed)

    def test_rejects_missing_and_duplicate_request_ids(self) -> None:
        state = _state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0))
        service = RoleDecisionService(Role.THIEF)
        payload = _decision_payload(state, role=Role.THIEF, request_id="dup-1")

        missing = dict(payload)
        missing["request_id"] = ""
        with self.assertRaisesRegex(McpServerError, "request_id"):
            service.decide(missing)

        service.decide(payload)
        with self.assertRaisesRegex(McpServerError, "duplicate"):
            service.decide(payload)

    def test_auth_and_timeout_integration_points(self) -> None:
        state = _state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0))
        payload = _decision_payload(state, role=Role.THIEF, request_id="auth-1")

        authed = RoleDecisionService(Role.THIEF, token="local-token")
        with self.assertRaisesRegex(McpServerError, "unauthorized"):
            authed.decide(payload)
        self.assertEqual(
            authed.decide(payload, authorization="Bearer local-token")["role"],
            "thief",
        )

        timeout = RoleDecisionService(Role.THIEF, timeout_seconds=-1)
        with self.assertRaisesRegex(McpServerError, "timeout"):
            timeout.decide(_decision_payload(state, role=Role.THIEF, request_id="timeout-1"))

    def test_decision_service_cannot_mutate_game_state(self) -> None:
        state = _state(active=Role.COP, cop=Coordinate(1, 0), thief=Coordinate(0, 0))
        before = state

        RoleDecisionService(Role.COP).decide(
            _decision_payload(state, role=Role.COP, request_id="mut-1")
        )

        self.assertEqual(state, before)

    def test_public_response_removes_internal_action_object(self) -> None:
        state = _state(active=Role.COP, cop=Coordinate(1, 0), thief=Coordinate(0, 0))
        response = RoleDecisionService(Role.COP).decide(
            _decision_payload(state, role=Role.COP, request_id="public-1")
        )

        public = response_public_json(response)

        self.assertNotIn("action", public)
        self.assertIn("decision", public)


class HttpDecisionServerTests(unittest.TestCase):
    def test_two_http_servers_are_independent(self) -> None:
        cop_server = build_server(role=Role.COP, host="127.0.0.1", port=0)
        thief_server = build_server(role=Role.THIEF, host="127.0.0.1", port=0)
        cop_thread = threading.Thread(target=cop_server.serve_forever, daemon=True)
        thief_thread = threading.Thread(target=thief_server.serve_forever, daemon=True)
        cop_thread.start()
        thief_thread.start()

        try:
            cop_base = f"http://127.0.0.1:{cop_server.server_port}"
            thief_base = f"http://127.0.0.1:{thief_server.server_port}"
            self.assertEqual(_get_json(f"{cop_base}/identity")["role"], "cop")
            self.assertEqual(_get_json(f"{cop_base}/mcp/identity")["role"], "cop")
            self.assertEqual(_get_json(f"{thief_base}/identity")["role"], "thief")

            cop_server.shutdown()
            cop_thread.join(timeout=5)

            self.assertEqual(_get_json(f"{thief_base}/health")["status"], "ok")
        finally:
            cop_server.shutdown()
            cop_thread.join(timeout=5)
            cop_server.server_close()
            thief_server.shutdown()
            thief_thread.join(timeout=5)
            thief_server.server_close()

    def test_http_decide_and_auth_failure(self) -> None:
        server = build_server(role=Role.THIEF, host="127.0.0.1", port=0, token="secret-token")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with self.assertRaises(HTTPError) as health_unauthorized:
                _get_json(f"{base}/health")
            self.assertEqual(health_unauthorized.exception.code, 401)
            self.assertEqual(
                _get_json(
                    f"{base}/health",
                    headers={"Authorization": "Bearer secret-token"},
                )["status"],
                "ok",
            )
            payload = _decision_payload(
                _state(active=Role.THIEF, cop=Coordinate(4, 4), thief=Coordinate(0, 0)),
                role=Role.THIEF,
                request_id="http-1",
            )
            with self.assertRaises(HTTPError) as unauthorized:
                _post_json(f"{base}/decide", payload)
            self.assertEqual(unauthorized.exception.code, 401)

            response = _post_json(
                f"{base}/decide",
                payload,
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response["role"], "thief")
            self.assertEqual(response["request_id"], "http-1")
            self.assertIn("decision", response)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_request_size_and_rate_limits(self) -> None:
        server = build_server(
            role=Role.THIEF,
            host="127.0.0.1",
            port=0,
            max_request_bytes=10,
            rate_limit_per_minute=2,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            self.assertEqual(_get_json(f"{base}/health")["status"], "ok")
            self.assertEqual(_get_json(f"{base}/identity")["role"], "thief")
            with self.assertRaises(HTTPError) as limited:
                _get_json(f"{base}/capabilities")
            self.assertEqual(limited.exception.code, 429)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


def _get_json(url: str, *, headers: dict[str, str] | None = None) -> dict:
    request = Request(url, headers=headers or {}, method="GET")
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict, *, headers: dict[str, str] | None = None) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
