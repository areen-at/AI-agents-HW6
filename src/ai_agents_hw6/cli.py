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
    return parser
