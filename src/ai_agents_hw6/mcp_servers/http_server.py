from __future__ import annotations

import argparse
import json
import os
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ai_agents_hw6.domain import Role
from ai_agents_hw6.mcp_servers.service import McpServerError, RoleDecisionService, response_public_json


DEFAULT_MAX_REQUEST_BYTES = 64 * 1024
DEFAULT_RATE_LIMIT_PER_MINUTE = 1000


def build_server(
    *,
    role: Role,
    host: str,
    port: int,
    token: str | None = None,
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES,
    rate_limit_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE,
) -> ThreadingHTTPServer:
    if max_request_bytes <= 0:
        raise ValueError("max_request_bytes must be positive")
    if rate_limit_per_minute <= 0:
        raise ValueError("rate_limit_per_minute must be positive")
    service = RoleDecisionService(role=role, token=token)
    requests_by_client: dict[str, deque[float]] = defaultdict(deque)
    rate_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if not self._admit_request():
                return
            path = _normalize_path(self.path)
            try:
                service.authorize(self.headers.get("Authorization"))
                if path == "/health":
                    self._write_json(service.health())
                elif path == "/identity":
                    self._write_json(service.identity())
                elif path == "/capabilities":
                    self._write_json(service.capabilities())
                else:
                    self._write_json({"error": "not found"}, status=404)
            except McpServerError as exc:
                self._write_json({"error": str(exc)}, status=exc.status_code)

        def do_POST(self) -> None:  # noqa: N802
            if not self._admit_request():
                return
            path = _normalize_path(self.path)
            if path != "/decide":
                self._write_json({"error": "not found"}, status=404)
                return
            try:
                payload = self._read_json()
                response = service.decide(
                    payload,
                    authorization=self.headers.get("Authorization"),
                )
                self._write_json(response_public_json(response))
            except McpServerError as exc:
                self._write_json({"error": str(exc)}, status=exc.status_code)
            except Exception:
                self._write_json({"error": "internal server error"}, status=500)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _read_json(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise McpServerError("invalid Content-Length") from exc
            if length <= 0:
                raise McpServerError("request body is required")
            if length > max_request_bytes:
                raise McpServerError("request body too large", status_code=413)
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise McpServerError("request body must be valid JSON") from exc
            if not isinstance(payload, dict):
                raise McpServerError("request body must be a JSON object")
            return payload

        def _admit_request(self) -> bool:
            client = self.client_address[0]
            now = time.monotonic()
            with rate_lock:
                history = requests_by_client[client]
                while history and history[0] <= now - 60:
                    history.popleft()
                if len(history) >= rate_limit_per_minute:
                    self._write_json({"error": "rate limit exceeded"}, status=429)
                    return False
                history.append(now)
            return True

        def _write_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), Handler)


def _normalize_path(path: str) -> str:
    if path.startswith("/mcp/"):
        return path[4:]
    if path == "/mcp":
        return "/"
    return path


def run_server(
    *,
    role: Role,
    host: str,
    port: int,
    token: str | None = None,
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES,
    rate_limit_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE,
) -> None:
    server = build_server(
        role=role,
        host=host,
        port=port,
        token=token,
        max_request_bytes=max_request_bytes,
        rate_limit_per_minute=rate_limit_per_minute,
    )
    print(f"{role.value} decision server listening on http://{host}:{port}", flush=True)
    server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Agents HW6 role decision server")
    parser.add_argument("--role", choices=("cop", "thief"), required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--token-env", default=None)
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--max-request-bytes", type=int, default=DEFAULT_MAX_REQUEST_BYTES)
    parser.add_argument(
        "--rate-limit-per-minute",
        type=int,
        default=DEFAULT_RATE_LIMIT_PER_MINUTE,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    role = Role(args.role)
    token_env = args.token_env or (
        "COP_MCP_TOKEN" if role is Role.COP else "THIEF_MCP_TOKEN"
    )
    token = os.environ.get(token_env)
    if args.require_auth and not token:
        raise SystemExit(f"required authentication token is missing from {token_env}")
    run_server(
        role=role,
        host=args.host,
        port=args.port,
        token=token,
        max_request_bytes=args.max_request_bytes,
        rate_limit_per_minute=args.rate_limit_per_minute,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
