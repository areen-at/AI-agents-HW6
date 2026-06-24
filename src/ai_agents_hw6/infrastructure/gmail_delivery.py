from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Protocol, cast

from ai_agents_hw6.application.events import atomic_write_json, redact
from ai_agents_hw6.config import PLACEHOLDER_VALUES, AppConfig

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
FINAL_RECIPIENT = "rmisegal+uoh26b@gmail.com"
DEFAULT_SUBJECT = "AI Agents HW6 Internal Report"


class GmailDeliveryError(RuntimeError):
    pass


class GmailTransport(Protocol):
    def send(self, *, raw_message: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class GmailPaths:
    credentials_file: Path
    token_file: Path
    receipt_file: Path

    @classmethod
    def from_environment(cls) -> GmailPaths:
        credentials = os.environ.get("GOOGLE_CREDENTIALS_FILE")
        token = os.environ.get("GOOGLE_TOKEN_FILE")
        if not credentials:
            raise GmailDeliveryError("GOOGLE_CREDENTIALS_FILE is not configured")
        if not token:
            raise GmailDeliveryError("GOOGLE_TOKEN_FILE is not configured")
        credentials_file = Path(credentials).expanduser()
        token_file = Path(token).expanduser()
        if credentials_file.resolve() == token_file.resolve():
            raise GmailDeliveryError("Google credentials and token paths must be different files")
        return cls(
            credentials_file=credentials_file,
            token_file=token_file,
            receipt_file=Path(
                os.environ.get(
                    "GMAIL_DELIVERY_RECEIPT_FILE",
                    "artifacts/reports/gmail_delivery_receipt.json",
                )
            ).expanduser(),
        )


@dataclass(frozen=True)
class DeliveryReceipt:
    payload_sha256: str
    recipient: str
    message_id: str
    sent_at: str
    already_sent: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "payload_sha256": self.payload_sha256,
            "recipient": self.recipient,
            "message_id": self.message_id,
            "sent_at": self.sent_at,
        }


def canonicalize_report(report: dict[str, Any]) -> str:
    validate_internal_report(report)
    return json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_canonical_report(path: str | Path) -> tuple[dict[str, Any], str]:
    report_path = Path(path)
    if not report_path.exists():
        raise GmailDeliveryError(f"internal report not found: {report_path}")
    try:
        value = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GmailDeliveryError(f"internal report is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise GmailDeliveryError("internal report root must be an object")
    return value, canonicalize_report(value)


def validate_internal_report(report: dict[str, Any]) -> None:
    sub_games = report.get("sub_games")
    if not isinstance(sub_games, list) or len(sub_games) != 6:
        raise GmailDeliveryError("internal report must contain exactly six sub_games")
    calculated = {"cop": 0, "thief": 0}
    for index, game in enumerate(sub_games, start=1):
        if not isinstance(game, dict) or game.get("index") != index:
            raise GmailDeliveryError("internal sub_games must be ordered and indexed 1 through 6")
        scores = game.get("scores")
        if (
            not isinstance(scores, dict)
            or isinstance(scores.get("cop"), bool)
            or not isinstance(scores.get("cop"), int)
            or isinstance(scores.get("thief"), bool)
            or not isinstance(scores.get("thief"), int)
        ):
            raise GmailDeliveryError("every sub-game must contain integer cop/thief scores")
        calculated["cop"] += scores["cop"]
        calculated["thief"] += scores["thief"]
    if report.get("totals") != calculated:
        raise GmailDeliveryError("internal report totals do not match calculated sub-game scores")


def validate_production_metadata(config: AppConfig, report: dict[str, Any]) -> None:
    if config.group.name in PLACEHOLDER_VALUES or not config.group.students:
        raise GmailDeliveryError(
            "real group name and at least one student are required before sending"
        )
    if report.get("group_name") != config.group.name:
        raise GmailDeliveryError("report group_name does not match configuration")
    if report.get("students") != list(config.group.students):
        raise GmailDeliveryError("report students do not match configuration")
    if report.get("github_repo") != config.group.github_repo:
        raise GmailDeliveryError("report github_repo does not match configuration")


def build_gmail_message(
    canonical_payload: str,
    *,
    recipient: str = FINAL_RECIPIENT,
    subject: str = DEFAULT_SUBJECT,
) -> tuple[str, str]:
    parsed = json.loads(canonical_payload)
    if not isinstance(parsed, dict):
        raise GmailDeliveryError("canonical payload must be a JSON object")
    payload_sha256 = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message["Message-ID"] = f"<hw6-{payload_sha256}@local.invalid>"
    message.set_content(canonical_payload, subtype="plain", charset="utf-8")
    raw_message = base64.urlsafe_b64encode(message.as_bytes(policy=policy.SMTP)).decode("ascii")
    inspect_gmail_message(raw_message, canonical_payload=canonical_payload, recipient=recipient)
    return raw_message, payload_sha256


def inspect_gmail_message(
    raw_message: str,
    *,
    canonical_payload: str,
    recipient: str = FINAL_RECIPIENT,
) -> None:
    try:
        decoded = base64.urlsafe_b64decode(raw_message.encode("ascii"))
        message = BytesParser(policy=policy.default).parsebytes(decoded)
    except Exception as exc:
        raise GmailDeliveryError("Gmail raw message is not valid base64url MIME") from exc
    if message.get("To") != recipient:
        raise GmailDeliveryError("Gmail recipient mismatch")
    if message.is_multipart():
        raise GmailDeliveryError("Gmail report must not be multipart or contain attachments")
    body = message.get_content()
    if body.rstrip("\r\n") != canonical_payload:
        raise GmailDeliveryError("Gmail body is not the exact canonical JSON payload")
    json.loads(body)


def deliver_report(
    *,
    canonical_payload: str,
    transport: GmailTransport,
    receipt_path: str | Path,
) -> DeliveryReceipt:
    raw_message, payload_sha256 = build_gmail_message(canonical_payload)
    existing = _load_receipt(receipt_path)
    if existing is not None:
        if existing.payload_sha256 != payload_sha256:
            raise GmailDeliveryError(
                "a receipt already exists for a different payload; archive it before a new send"
            )
        return DeliveryReceipt(
            payload_sha256=existing.payload_sha256,
            recipient=existing.recipient,
            message_id=existing.message_id,
            sent_at=existing.sent_at,
            already_sent=True,
        )
    try:
        response = transport.send(raw_message=raw_message)
    except Exception as exc:
        safe_detail = redact(str(exc))
        raise GmailDeliveryError(f"Gmail send failed: {safe_detail}") from exc
    message_id = response.get("id")
    if not isinstance(message_id, str) or not message_id:
        raise GmailDeliveryError("Gmail send response did not include a message id")
    receipt = DeliveryReceipt(
        payload_sha256=payload_sha256,
        recipient=FINAL_RECIPIENT,
        message_id=message_id,
        sent_at=datetime.now(timezone.utc).isoformat(),
    )
    atomic_write_json(receipt_path, receipt.to_json())
    return receipt


class GoogleGmailTransport:
    def __init__(self, service: Any) -> None:
        self._service = service

    def send(self, *, raw_message: str) -> dict[str, Any]:
        response = (
            self._service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        )
        return cast(dict[str, Any], response)


def build_google_transport(
    paths: GmailPaths,
    *,
    interactive: bool,
) -> GoogleGmailTransport:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]
        from googleapiclient.discovery import build  # type: ignore[import-untyped]
    except ImportError as exc:
        raise GmailDeliveryError(
            "Gmail dependencies are missing; install the project with the gmail extra"
        ) from exc

    credentials = None
    if paths.token_file.exists():
        try:
            credentials = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
                str(paths.token_file),
                [GMAIL_SEND_SCOPE],
            )
        except Exception as exc:
            raise GmailDeliveryError("stored Gmail token is malformed or incompatible") from exc
    credentials = _refresh_existing_credentials(
        credentials,
        request_factory=Request,
        interactive=interactive,
    )
    if credentials is None:
        if not interactive:
            raise GmailDeliveryError(
                "no valid Gmail token is available; run --gmail-authorize interactively"
            )
        if not paths.credentials_file.exists():
            raise GmailDeliveryError(
                f"Google Desktop OAuth credentials file not found: {paths.credentials_file}"
            )
        paths.token_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(paths.credentials_file),
                [GMAIL_SEND_SCOPE],
            )
            credentials = flow.run_local_server(port=0)
            paths.token_file.write_text(credentials.to_json(), encoding="utf-8")
        except Exception as exc:
            raise GmailDeliveryError("interactive Gmail authorization failed") from exc
    return GoogleGmailTransport(
        build("gmail", "v1", credentials=credentials, cache_discovery=False)
    )


def _refresh_existing_credentials(
    credentials: Any,
    *,
    request_factory: Any,
    interactive: bool,
) -> Any:
    if credentials is None or credentials.valid:
        return credentials
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(request_factory())
        except Exception as exc:
            raise GmailDeliveryError(
                "stored Gmail token could not be refreshed; revoke/delete it and authorize again"
            ) from exc
        if not credentials.valid:
            raise GmailDeliveryError("stored Gmail token remained invalid after refresh")
        return credentials
    if not interactive:
        raise GmailDeliveryError("stored Gmail token is invalid and interactive OAuth is disabled")
    return None


def gmail_preflight(config: AppConfig, *, report_path: str | Path) -> dict[str, Any]:
    report, canonical_payload = load_canonical_report(report_path)
    validate_production_metadata(config, report)
    paths = GmailPaths.from_environment()
    validate_secret_paths_are_gitignored(paths)
    if not paths.credentials_file.exists():
        raise GmailDeliveryError(
            f"Google Desktop OAuth credentials file not found: {paths.credentials_file}"
        )
    build_gmail_message(canonical_payload)
    build_google_transport(paths, interactive=False)
    return {
        "recipient": FINAL_RECIPIENT,
        "payload_sha256": hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest(),
        "credentials_file_exists": True,
        "token_file_exists": paths.token_file.exists(),
        "oauth_ready": True,
        "scope": GMAIL_SEND_SCOPE,
        "receipt_file": str(paths.receipt_file),
    }


def validate_secret_paths_are_gitignored(paths: GmailPaths) -> None:
    workspace = Path.cwd().resolve()
    ignore_file = workspace / ".gitignore"
    ignore_text = ignore_file.read_text(encoding="utf-8") if ignore_file.exists() else ""
    required_patterns = {
        "credentials.json": "credentials.json",
        "token.json": "token.json",
    }
    for path in (paths.credentials_file, paths.token_file):
        try:
            relative = path.resolve().relative_to(workspace)
        except ValueError:
            continue
        relative_text = relative.as_posix()
        required = required_patterns.get(relative_text)
        if required is None or required not in ignore_text.splitlines():
            raise GmailDeliveryError(
                f"workspace OAuth file is not explicitly protected by .gitignore: {relative_text}"
            )


def _load_receipt(path: str | Path) -> DeliveryReceipt | None:
    target = Path(path)
    if not target.exists():
        return None
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
        return DeliveryReceipt(
            payload_sha256=value["payload_sha256"],
            recipient=value["recipient"],
            message_id=value["message_id"],
            sent_at=value["sent_at"],
        )
    except Exception as exc:
        raise GmailDeliveryError("existing Gmail delivery receipt is malformed") from exc
