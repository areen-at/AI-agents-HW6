from __future__ import annotations

from ai_agents_hw6.application.series import SeriesResult


def render_series_summary(result: SeriesResult) -> str:
    lines = ["Series summary:"]
    for game in result.valid_sub_games:
        lines.append(
            "Game "
            f"{game.index}: outcome={game.outcome} reason={game.terminal_reason} "
            f"moves={game.move_count} score=cop:{game.cop_score},thief:{game.thief_score}"
        )
    lines.append(f"Totals: cop={result.totals['cop']} thief={result.totals['thief']}")
    return "\n".join(lines)
