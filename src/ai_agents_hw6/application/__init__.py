"""Application services for orchestration, replay, and series control."""

from ai_agents_hw6.application.evidence import build_evidence_manifest, write_evidence_manifest
from ai_agents_hw6.application.mcp_client import (
    LocalMcpDecisionProvider,
    McpClientConfig,
    McpClientError,
    RoleMcpClient,
    preflight_clients,
    run_local_mcp_series,
)
from ai_agents_hw6.application.series import (
    SeriesObserver,
    SeriesResult,
    SeriesSettings,
    TechnicalFailure,
    first_legal_action_provider,
    run_series,
    write_engine_only_series,
    write_engine_only_series_with_policy,
)

__all__ = [
    "SeriesResult",
    "SeriesObserver",
    "SeriesSettings",
    "TechnicalFailure",
    "first_legal_action_provider",
    "run_series",
    "write_engine_only_series",
    "write_engine_only_series_with_policy",
    "LocalMcpDecisionProvider",
    "McpClientConfig",
    "McpClientError",
    "RoleMcpClient",
    "preflight_clients",
    "run_local_mcp_series",
    "build_evidence_manifest",
    "write_evidence_manifest",
]
