from __future__ import annotations

import base64
import json
import os
import tempfile
import unittest
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import patch

from ai_agents_hw6.config import load_config
from ai_agents_hw6.infrastructure import (
    FINAL_RECIPIENT,
    GMAIL_SEND_SCOPE,
    GmailDeliveryError,
    GmailPaths,
    build_gmail_message,
    canonicalize_report,
    deliver_report,
    load_canonical_report,
    validate_internal_report,
    validate_production_metadata,
)
from ai_agents_hw6.infrastructure.gmail_delivery import _refresh_existing_credentials


class FakeGmailTransport:
    def __init__(self, response: dict | None = None, error: Exception | None = None) -> None:
        self.response = response or {"id": "gmail-message-123"}
        self.error = error
        self.raw_messages: list[str] = []

    def send(self, *, raw_message: str) -> dict:
        self.raw_messages.append(raw_message)
        if self.error is not None:
            raise self.error
        return self.response


class GmailDeliveryTests(unittest.TestCase):
    def test_canonical_message_has_exact_json_only_body_and_final_recipient(self) -> None:
        report = _report()
        canonical = canonicalize_report(report)
        raw, digest = build_gmail_message(canonical)
        message = BytesParser(policy=policy.default).parsebytes(
            base64.urlsafe_b64decode(raw.encode("ascii"))
        )

        self.assertEqual(message["To"], FINAL_RECIPIENT)
        self.assertEqual(message.get_content().rstrip("\r\n"), canonical)
        self.assertEqual(json.loads(message.get_content()), report)
        self.assertNotIn("Hello", message.get_content())
        self.assertNotIn("```", message.get_content())
        self.assertEqual(len(digest), 64)

    def test_delivery_records_message_id_timestamp_and_prevents_duplicate_send(self) -> None:
        transport = FakeGmailTransport()
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            first = deliver_report(
                canonical_payload=canonicalize_report(_report()),
                transport=transport,
                receipt_path=receipt_path,
            )
            second = deliver_report(
                canonical_payload=canonicalize_report(_report()),
                transport=transport,
                receipt_path=receipt_path,
            )
            stored = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(first.message_id, "gmail-message-123")
        self.assertTrue(first.sent_at)
        self.assertFalse(first.already_sent)
        self.assertTrue(second.already_sent)
        self.assertEqual(len(transport.raw_messages), 1)
        self.assertEqual(stored["message_id"], first.message_id)

    def test_different_payload_is_not_sent_over_existing_receipt(self) -> None:
        transport = FakeGmailTransport()
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            deliver_report(
                canonical_payload=canonicalize_report(_report()),
                transport=transport,
                receipt_path=receipt_path,
            )
            changed = _report()
            changed["series_id"] = "different"
            with self.assertRaisesRegex(GmailDeliveryError, "different payload"):
                deliver_report(
                    canonical_payload=canonicalize_report(changed),
                    transport=transport,
                    receipt_path=receipt_path,
                )
        self.assertEqual(len(transport.raw_messages), 1)

    def test_send_failure_is_separate_and_does_not_create_receipt(self) -> None:
        transport = FakeGmailTransport(error=RuntimeError("token=private-value"))
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            with self.assertRaises(GmailDeliveryError) as context:
                deliver_report(
                    canonical_payload=canonicalize_report(_report()),
                    transport=transport,
                    receipt_path=receipt_path,
                )
            self.assertFalse(receipt_path.exists())
        self.assertNotIn("private-value", str(context.exception))

    def test_report_validation_rejects_wrong_count_and_wrong_totals(self) -> None:
        report = _report()
        report["sub_games"] = report["sub_games"][:5]
        with self.assertRaisesRegex(GmailDeliveryError, "exactly six"):
            validate_internal_report(report)
        report = _report()
        report["totals"]["cop"] += 1
        with self.assertRaisesRegex(GmailDeliveryError, "totals"):
            validate_internal_report(report)

    def test_report_is_loaded_and_canonicalized_immediately_before_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "internal_game_report.json"
            path.write_text(json.dumps(_report(), indent=2), encoding="utf-8")
            loaded, canonical = load_canonical_report(path)
        self.assertEqual(loaded, _report())
        self.assertEqual(canonical, canonicalize_report(_report()))

    def test_environment_paths_are_required_and_external(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(GmailDeliveryError, "GOOGLE_CREDENTIALS_FILE"):
                GmailPaths.from_environment()
        with patch.dict(
            os.environ,
            {
                "GOOGLE_CREDENTIALS_FILE": "C:/private/google/credentials.json",
                "GOOGLE_TOKEN_FILE": "C:/private/google/token.json",
            },
            clear=True,
        ):
            paths = GmailPaths.from_environment()
        self.assertEqual(paths.credentials_file.name, "credentials.json")
        self.assertEqual(paths.token_file.name, "token.json")
        with patch.dict(
            os.environ,
            {
                "GOOGLE_CREDENTIALS_FILE": "credentials.json",
                "GOOGLE_TOKEN_FILE": "token.json",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(GmailDeliveryError, "outside"):
                GmailPaths.from_environment()

    def test_placeholder_group_metadata_blocks_production_send(self) -> None:
        config = load_config("config.json")
        with self.assertRaisesRegex(GmailDeliveryError, "real group name"):
            validate_production_metadata(config, _report())

    def test_least_privilege_scope_is_send_only(self) -> None:
        self.assertEqual(GMAIL_SEND_SCOPE, "https://www.googleapis.com/auth/gmail.send")

    def test_expired_token_refreshes_and_refresh_failure_is_actionable(self) -> None:
        class FakeCredentials:
            valid = False
            expired = True
            refresh_token = "present"

            def __init__(self, *, fail: bool = False) -> None:
                self.fail = fail

            def refresh(self, request: object) -> None:
                if self.fail:
                    raise RuntimeError("revoked")
                self.valid = True

        refreshed = _refresh_existing_credentials(
            FakeCredentials(),
            request_factory=object,
            interactive=False,
        )
        self.assertTrue(refreshed.valid)
        with self.assertRaisesRegex(GmailDeliveryError, "authorize again"):
            _refresh_existing_credentials(
                FakeCredentials(fail=True),
                request_factory=object,
                interactive=False,
            )


def _report() -> dict:
    sub_games = [
        {
            "index": index,
            "sub_game_id": f"game-{index}",
            "attempt_id": f"attempt-{index}",
            "attempt_number": 1,
            "seed": index,
            "move_count": 5,
            "outcome": "thief_win",
            "terminal_reason": "move_limit",
            "scores": {"cop": 5, "thief": 10},
            "final_state_hash": "hash",
            "event_log_path": "artifacts/logs/events.json",
        }
        for index in range(1, 7)
    ]
    return {
        "group_name": "Real Group",
        "students": ["Student One"],
        "github_repo": "https://github.com/areen-at/AI-agents-HW6",
        "cop_mcp_url": "http://127.0.0.1:8001/mcp",
        "thief_mcp_url": "http://127.0.0.1:8002/mcp",
        "timezone": "Asia/Jerusalem",
        "series_id": "series",
        "sub_games": sub_games,
        "invalid_attempts": [],
        "totals": {"cop": 30, "thief": 60},
    }


if __name__ == "__main__":
    unittest.main()
