from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ai_agents_hw6.config import ConfigError, load_config, validate_for_mode
from ai_agents_hw6.cli import build_parser
from ai_agents_hw6.application import (
    McpClientError,
    build_evidence_manifest,
    run_local_mcp_series,
    write_engine_only_series_with_policy,
    write_evidence_manifest,
)
from ai_agents_hw6.reporting import build_internal_report, write_internal_report
from ai_agents_hw6.ui import TerminalObserver, render_series_summary, replay_events
from ai_agents_hw6.infrastructure import (
    GmailDeliveryError,
    GmailPaths,
    build_google_transport,
    deliver_report,
    gmail_preflight,
    load_canonical_report,
    validate_production_metadata,
)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        validate_for_mode(config, args.mode)
    except ConfigError as exc:
        parser.exit(status=2, message=f"Configuration error: {exc}\n")

    if args.replay_events:
        rendered = replay_events(
            args.replay_events,
            stream=sys.stdout,
            max_barriers=config.game.max_barriers,
        )
        print(f"Replay complete: rendered_snapshots={rendered}")
        return 0

    gmail_commands = sum(
        bool(value) for value in (args.gmail_preflight, args.gmail_authorize, args.send_report)
    )
    if gmail_commands > 1:
        parser.exit(
            status=2,
            message="Choose only one of --gmail-preflight, --gmail-authorize, or --send-report\n",
        )
    if gmail_commands:
        try:
            if args.gmail_preflight:
                preflight = gmail_preflight(
                    config,
                    report_path=config.reports.internal_game_report,
                )
                print("Gmail preflight passed.")
                print(f"Recipient: {preflight['recipient']}")
                print(f"Scope: {preflight['scope']}")
                print(f"Payload SHA-256: {preflight['payload_sha256']}")
                return 0
            if args.gmail_authorize:
                paths = GmailPaths.from_environment()
                build_google_transport(paths, interactive=True)
                print(f"Gmail authorization completed. Token: {paths.token_file}")
                return 0
            report, canonical_payload = load_canonical_report(
                config.reports.internal_game_report
            )
            validate_production_metadata(config, report)
            paths = GmailPaths.from_environment()
            transport = build_google_transport(paths, interactive=False)
            receipt = deliver_report(
                canonical_payload=canonical_payload,
                transport=transport,
                receipt_path=paths.receipt_file,
            )
            status = "already sent; existing receipt reused" if receipt.already_sent else "sent"
            print(f"Gmail report {status}.")
            print(f"Recipient: {receipt.recipient}")
            print(f"Message ID: {receipt.message_id}")
            print(f"Sent at: {receipt.sent_at}")
            print(f"Receipt: {paths.receipt_file}")
            return 0
        except GmailDeliveryError as exc:
            parser.exit(status=2, message=f"Gmail delivery error: {exc}\n")

    print(f"Config validation passed for mode {args.mode}.")
    print(f"Group: {config.group.name}")
    print(f"Grid: {config.game.grid_size[0]}x{config.game.grid_size[1]}")
    print(f"Sub-games: {config.game.num_games}")

    if args.engine_only and args.local_mcp:
        parser.exit(status=2, message="Choose either --engine-only or --local-mcp, not both\n")

    observer = TerminalObserver(
        max_barriers=config.game.max_barriers,
        stream=sys.stdout,
        quiet=args.quiet,
        json_logs=args.json_logs,
        log_level=config.logging.level,
    )

    if args.engine_only:
        if args.mode != "internal":
            parser.exit(status=2, message="--engine-only is only supported with --mode internal\n")
        result = write_engine_only_series_with_policy(
            config,
            policy_name=args.policy,
            observer=observer,
        )
        report = build_internal_report(config, result)
        write_internal_report(config.reports.internal_game_report, report)
        evidence_path = "artifacts/reports/phase9_evidence_manifest.json"
        write_evidence_manifest(
            evidence_path,
            build_evidence_manifest(
                config_path=args.config,
                event_log_path=str(
                    Path(config.logging.event_log_dir) / "engine_only_events.json"
                ),
                report_path=config.reports.internal_game_report,
            ),
        )
        print("Engine-only series completed.")
        print(f"Policy: {args.policy}")
        print(f"Valid sub-games: {len(result.valid_sub_games)}")
        print(render_series_summary(result))
        print(f"Report: {config.reports.internal_game_report}")
        print(f"Evidence manifest: {evidence_path}")
    if args.local_mcp:
        if args.mode != "internal":
            parser.exit(status=2, message="--local-mcp is only supported with --mode internal\n")
        try:
            result = run_local_mcp_series(config, observer=observer)
        except McpClientError as exc:
            parser.exit(status=2, message=f"Local MCP preflight failed: {exc}\n")
        report = build_internal_report(config, result)
        write_internal_report(config.reports.internal_game_report, report)
        evidence_path = "artifacts/reports/phase9_evidence_manifest.json"
        write_evidence_manifest(
            evidence_path,
            build_evidence_manifest(
                config_path=args.config,
                event_log_path=str(
                    Path(config.logging.event_log_dir) / "engine_only_events.json"
                ),
                report_path=config.reports.internal_game_report,
            ),
        )
        print("Local MCP series completed.")
        print(f"Valid sub-games: {len(result.valid_sub_games)}")
        print(render_series_summary(result))
        print(f"Report: {config.reports.internal_game_report}")
        print(f"Evidence manifest: {evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
