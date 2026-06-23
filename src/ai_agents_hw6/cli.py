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
        "--policy",
        choices=("heuristic", "first-legal"),
        default="heuristic",
        help="Engine-only policy to use when --engine-only is set.",
    )
    return parser
