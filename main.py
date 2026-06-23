from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ai_agents_hw6.config import ConfigError, load_config, validate_for_mode
from ai_agents_hw6.cli import build_parser
from ai_agents_hw6.application import write_engine_only_series
from ai_agents_hw6.reporting import build_internal_report, write_internal_report


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        validate_for_mode(config, args.mode)
    except ConfigError as exc:
        parser.exit(status=2, message=f"Configuration error: {exc}\n")

    print(f"Config validation passed for mode {args.mode}.")
    print(f"Group: {config.group.name}")
    print(f"Grid: {config.game.grid_size[0]}x{config.game.grid_size[1]}")
    print(f"Sub-games: {config.game.num_games}")

    if args.engine_only:
        if args.mode != "internal":
            parser.exit(status=2, message="--engine-only is only supported with --mode internal\n")
        result = write_engine_only_series(config)
        report = build_internal_report(config, result)
        write_internal_report(config.reports.internal_game_report, report)
        print("Engine-only series completed.")
        print(f"Valid sub-games: {len(result.valid_sub_games)}")
        print(f"Totals: cop={result.totals['cop']} thief={result.totals['thief']}")
        print(f"Report: {config.reports.internal_game_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
