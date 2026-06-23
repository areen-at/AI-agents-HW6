from __future__ import annotations

import argparse

VALID_MODES = ("internal", "bonus", "bonus-mock")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Agents HW6 command line entry point.",
    )
    parser.add_argument(
        "--mode",
        choices=VALID_MODES,
        default="internal",
        help="Run mode. Phase 1 only validates configuration.",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json.",
    )
    parser.add_argument(
        "--engine-only",
        action="store_true",
        help="Run a deterministic engine-only six-game series and write the internal report.",
    )
    parser.add_argument(
        "--local-mcp",
        action="store_true",
        help="Run a six-game series through the configured local Cop and Thief decision servers.",
    )
    parser.add_argument(
        "--policy",
        choices=("heuristic", "first-legal"),
        default="heuristic",
        help="Engine-only policy to use when --engine-only is set.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable live board rendering while preserving reports and structured event logs.",
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Emit redacted operational events as JSON lines.",
    )
    parser.add_argument(
        "--replay-events",
        metavar="PATH",
        help="Render committed state snapshots from a previously written event log, without MCP calls.",
    )
    return parser
