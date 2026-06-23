"""Application services package placeholder for later phases."""
"""Application services for orchestration, replay, and series control."""

from ai_agents_hw6.application.series import (
    SeriesResult,
    SeriesSettings,
    TechnicalFailure,
    first_legal_action_provider,
    run_series,
    write_engine_only_series,
)

__all__ = [
    "SeriesResult",
    "SeriesSettings",
    "TechnicalFailure",
    "first_legal_action_provider",
    "run_series",
    "write_engine_only_series",
]
