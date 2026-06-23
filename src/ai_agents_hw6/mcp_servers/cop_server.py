from __future__ import annotations

from ai_agents_hw6.domain import Role
from ai_agents_hw6.mcp_servers.http_server import run_server


def main() -> int:
    run_server(role=Role.COP, host="127.0.0.1", port=8001)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
