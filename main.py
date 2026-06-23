from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ai_agents_hw6.config import ConfigError, load_config, validate_for_mode
from ai_agents_hw6.cli import build_parser


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
