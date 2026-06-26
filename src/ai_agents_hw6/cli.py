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
        help="Run mode: required internal series, real external bonus, or test-only bonus mock.",
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
        choices=("heuristic", "first-legal", "q-learning"),
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
        help=(
            "Render committed state snapshots from a previously written event log, "
            "without MCP calls."
        ),
    )
    parser.add_argument(
        "--gmail-preflight",
        action="store_true",
        help="Validate the existing internal report and Gmail OAuth readiness without sending.",
    )
    parser.add_argument(
        "--gmail-authorize",
        action="store_true",
        help="Run the interactive Desktop OAuth flow and store the token at GOOGLE_TOKEN_FILE.",
    )
    parser.add_argument(
        "--send-report",
        action="store_true",
        help="Send the existing internal JSON report through Gmail after strict validation.",
    )
    parser.add_argument(
        "--bonus-preflight-only",
        action="store_true",
        help="Validate all four bonus endpoints and the shared agreement without starting games.",
    )
    parser.add_argument(
        "--bonus-fastmcp-host-client",
        action="store_true",
        help=(
            "Drive our selected role against a shared authoritative FastMCP host using "
            "BONUS_FASTMCP_HOST_URL and BONUS_FASTMCP_HOST_TOKEN."
        ),
    )
    parser.add_argument(
        "--bonus-role",
        choices=("cop", "thief"),
        help="Our role when --bonus-fastmcp-host-client is used.",
    )
    parser.add_argument(
        "--bonus-fastmcp-dry-run",
        action="store_true",
        help=(
            "Connect to the shared FastMCP host and compute the next action without "
            "submitting it."
        ),
    )
    parser.add_argument(
        "--bonus-fastmcp-max-polls",
        type=int,
        default=300,
        help="Maximum host-status polls for --bonus-fastmcp-host-client.",
    )
    parser.add_argument(
        "--bonus-fastmcp-poll-seconds",
        type=float,
        default=1.0,
        help="Delay between host-status polls for --bonus-fastmcp-host-client.",
    )
    parser.add_argument(
        "--build-bonus-report",
        action="store_true",
        help="Build the canonical unapproved bonus report candidate from verified match evidence.",
    )
    parser.add_argument(
        "--finalize-bonus-report",
        action="store_true",
        help="Finalize the bonus report only after both groups approve the exact candidate hash.",
    )
    parser.add_argument(
        "--verify-bonus-report",
        action="store_true",
        help="Validate and print the checksum of the finalized bonus report.",
    )
    parser.add_argument(
        "--evaluate-learning",
        action="store_true",
        help="Compare optional Q-learning tables with the fixed heuristic baseline.",
    )
    return parser
