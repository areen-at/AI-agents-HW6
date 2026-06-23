# Phase 10 Gmail and Normal-Report Delivery

## Result

IMPLEMENTATION PASS / LIVE ACTIVATION PENDING - The Gmail delivery path is implemented and covered
by fake-transport tests. It validates a six-game report and calculated totals, canonicalizes the
JSON, constructs and re-inspects the MIME body, uses the send-only Gmail scope, records a delivery
receipt, and prevents a known payload from being sent twice.

No real email was sent. The repository still contains `MY_GROUP_NAME` and an empty student list,
and no private Google OAuth files were supplied. Those values must not be invented or committed.

## External prerequisites still open

- T0273: provide the real group name and student list in safe non-secret configuration.
- T0276: enable Gmail API in the intended Google Cloud project.
- T0277: configure the OAuth consent screen, audience, and sending-account test user.
- T0278: create and download a Desktop OAuth client.
- T0282: complete one interactive authorization.

These are account/user actions, not safe repository defaults. The CLI fails before sending while
the metadata is a placeholder.

## Implemented behavior

- Final recipient is `rmisegal+uoh26b@gmail.com`.
- OAuth scope is exactly `https://www.googleapis.com/auth/gmail.send`.
- Google dependencies are optional and imported only for a real OAuth/send command.
- `GOOGLE_CREDENTIALS_FILE` and `GOOGLE_TOKEN_FILE` are required environment variables.
- Credential and token paths are rejected if they resolve inside the repository.
- The internal report is reloaded and parsed immediately before delivery.
- Exactly six ordered sub-games are required.
- Aggregate Cop and Thief totals are recalculated from all six score entries.
- Group name, students, and repository must match production configuration.
- Canonical JSON uses UTF-8, sorted keys, and compact separators.
- The decoded email body contains exactly that JSON plus permitted terminal line ending.
- No greeting, signature, Markdown fence, attachment, or multipart content is added.
- A deterministic MIME `Message-ID` includes the canonical payload SHA-256.
- A successful API response must include a Gmail message ID.
- Receipt records payload SHA-256, recipient, Gmail message ID, and UTC timestamp.
- A matching receipt returns `already_sent` without another API call.
- A different payload is rejected while an old receipt exists.
- Send failures create no success receipt and never modify/rerun game results.
- Token refresh is attempted when an expired token has a refresh token.
- Refresh/revocation failures provide a safe reauthorization instruction.

## Setup and commands

Follow the provided Google API installation guide and the official Gmail documentation:

- <https://developers.google.com/workspace/gmail/api/quickstart/python>
- <https://developers.google.com/workspace/gmail/api/guides/sending>
- <https://developers.google.com/workspace/gmail/api/auth/scopes>

Install:

```powershell
python -m pip install -e ".[gmail]"
```

Use paths outside the checkout:

```powershell
$env:GOOGLE_CREDENTIALS_FILE='C:\private\google\credentials.json'
$env:GOOGLE_TOKEN_FILE='C:\private\google\token.json'
$env:GMAIL_DELIVERY_RECEIPT_FILE='artifacts\reports\gmail_delivery_receipt.json'
```

Authorize once:

```powershell
python main.py --mode internal --config config.json --gmail-authorize
```

After generating and reviewing `reports/internal_game_report.json`:

```powershell
python main.py --mode internal --config config.json --gmail-preflight
python main.py --mode internal --config config.json --send-report
```

`--gmail-authorize`, `--gmail-preflight`, and `--send-report` are mutually exclusive.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/infrastructure/gmail_delivery.py` | Report validation, canonical MIME, OAuth, Gmail transport, receipts |
| `src/ai_agents_hw6/infrastructure/__init__.py` | Public Gmail adapter exports |
| `src/ai_agents_hw6/cli.py` | Authorization, preflight, and send switches |
| `main.py` | Gmail CLI workflow and safe error handling |
| `tests/unit/test_gmail_delivery.py` | Exact-body, fake send, idempotency, error, metadata, path, scope, refresh tests |
| `pyproject.toml` | Optional Gmail dependencies |
| `.env.example` | Names-only OAuth and receipt path configuration |
| `README.md` | Operator procedure and current activation status |
| `todo.md` | Implementation tasks completed; external Google/user tasks remain open |

## Verification

- `$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'`
- `python -m compileall -q main.py src tests`
- `python -m pip check`
- `python main.py --mode internal --config config.json --gmail-preflight`
- `git diff --check`

Observed:

- 108 tests pass.
- Compilation succeeds.
- Existing dependencies are consistent.
- Fake Gmail transport returns a message ID and writes a receipt.
- Decoded MIME body equals the canonical JSON and parses successfully.
- A second same-payload call performs no send.
- Expired-token refresh success and failure paths are tested.
- Preflight currently exits safely on placeholder group metadata, before OAuth or network access.
- No live Gmail API call was made.

## Remaining live evidence

After the user supplies the real group/student metadata and private OAuth files, run authorization,
preflight, and one reviewed send. Record the returned Gmail message ID/timestamp and confirm the
received decoded body equals the preserved canonical payload. Keep the receipt and OAuth files
outside Git.
