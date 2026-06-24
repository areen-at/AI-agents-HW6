"""External infrastructure adapters."""

from ai_agents_hw6.infrastructure.gmail_delivery import (
    FINAL_RECIPIENT,
    GMAIL_SEND_SCOPE,
    DeliveryReceipt,
    GmailDeliveryError,
    GmailPaths,
    GoogleGmailTransport,
    build_gmail_message,
    build_google_transport,
    canonicalize_report,
    deliver_report,
    gmail_preflight,
    inspect_gmail_message,
    load_canonical_report,
    validate_internal_report,
    validate_production_metadata,
    validate_secret_paths_are_gitignored,
)

__all__ = [
    "FINAL_RECIPIENT",
    "GMAIL_SEND_SCOPE",
    "DeliveryReceipt",
    "GmailDeliveryError",
    "GmailPaths",
    "GoogleGmailTransport",
    "build_gmail_message",
    "build_google_transport",
    "canonicalize_report",
    "deliver_report",
    "gmail_preflight",
    "inspect_gmail_message",
    "load_canonical_report",
    "validate_internal_report",
    "validate_production_metadata",
    "validate_secret_paths_are_gitignored",
]
