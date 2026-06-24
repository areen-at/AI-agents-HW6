from __future__ import annotations

from typing import Any

from ai_agents_hw6.domain import Role

PROTOCOL_VERSION = "1.0"
SERVER_TRANSPORT = "stdlib-json-http"
FASTMCP_DEPENDENCY = "not-installed-phase-7-stdlib-transport"


def capabilities(role: Role) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "transport": SERVER_TRANSPORT,
        "fastmcp_dependency": FASTMCP_DEPENDENCY,
        "role": role.value,
        "operations": ["health", "identity", "capabilities", "decide"],
        "decision_contract": "natural-language-observation-json-action",
        "auth": "optional bearer token",
    }
