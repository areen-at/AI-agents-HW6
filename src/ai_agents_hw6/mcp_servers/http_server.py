from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ai_agents_hw6.domain import Role
from ai_agents_hw6.mcp_servers.service import McpServerError, RoleDecisionService, response_public_json


def build_server(*, role: Role, host: str, port: int, token: str | None = None) -> ThreadingHTTPServer:
    service = RoleDecisionService(role=role, token=token)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._write_json(service.health())
            elif self.path == "/identity":
                self._write_json(service.identity())
            elif self.path == "/capabilities":
                self._write_json(service.capabilities())
            else:
                self._write_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/decide":
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
            except Exception as exc:
                self._write_json({"error": f"server error: {exc}"}, status=500)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise McpServerError("request body must be a JSON object")
            return payload

        def _write_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), Handler)


def run_server(*, role: Role, host: str, port: int, token: str | None = None) -> None:
    server = build_server(role=role, host=host, port=port, token=token)
    print(f"{role.value} decision server listening on http://{host}:{port}", flush=True)
    server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Agents HW6 role decision server")
    parser.add_argument("--role", choices=("cop", "thief"), required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--token", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_server(role=Role(args.role), host=args.host, port=args.port, token=args.token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
