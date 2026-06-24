# Phase 16 — Bonus Report and Mutual Agreement

## Status

The canonical report, checksum-comparison, mutual-approval, and finalization workflow is
implemented and tested. No production report was generated because Phase 15 has no real opponent
match evidence or explicit opponent approval. The repository therefore remains truthfully
fail-closed.

## Canonical report workflow

Phase 16 consumes only the verified
`artifacts/reports/bonus_match_evidence.json` from Phase 15. It recalculates the evidence checksum
before trusting any field and requires the opponent to confirm the same checksum through
`OPPONENT_BONUS_EVIDENCE_SHA256`.

Build the unapproved candidate:

```powershell
$env:OPPONENT_BONUS_EVIDENCE_SHA256="<opponent-confirmed evidence hash>"
python main.py --mode bonus --config config.json --build-bonus-report
```

The candidate includes:

- `report_type: bonus_game`;
- both real group names, repositories, and student arrays;
- all four real MCP URLs;
- timezone `Asia/Jerusalem`;
- exactly six valid sub-games with 3+3 endpoint ownership;
- game totals by owning group;
- bonus claims separate from game totals;
- agreement and match-evidence checksums;
- `mutual_agreement: false`.

Claims are deterministic: the higher-total group receives 10, the lower-total group receives 7,
and a draw gives 5 to each group.

## Exact two-party approval

Both groups inspect the exact JSON candidate and compare its printed SHA-256. Each group must
explicitly approve that same hash:

```powershell
$env:BONUS_GROUP_1_APPROVAL_SHA256="<candidate hash>"
$env:BONUS_GROUP_2_APPROVAL_SHA256="<candidate hash>"
python main.py --mode bonus --config config.json --finalize-bonus-report
```

Missing, different, or stale approvals fail. Successful finalization changes only the agreement
state and records `approved_candidate_sha256`; it then validates and atomically writes:

- `reports/bonus_game_report.json`;
- `artifacts/reports/bonus_report_approval.json`.

Verify the finalized checksum:

```powershell
python main.py --mode bonus --config config.json --verify-bonus-report
```

The report files contain JSON only. Mock output remains on its separate path. An unapproved
candidate cannot overwrite the production report, and bonus-mode Gmail commands are refused.

## Discrepancy procedure

If evidence or candidate checksums differ:

1. do not approve or finalize;
2. compare the six game identifiers, role ownership, seeds, outcomes, scores, and totals;
3. replay `artifacts/logs/bonus_events.json`;
4. resolve the source discrepancy with the opponent;
5. regenerate evidence and the candidate;
6. approve only the newly matching candidate hash.

Never edit totals, claims, agreement state, or checksums by hand.

## Verification coverage

Tests cover:

- required production metadata and placeholder rejection;
- six-game canonical report construction;
- 3+3 ownership preservation;
- winner/loser claims of 10/7;
- draw claims of 5/5;
- separation of totals and claims;
- initial `mutual_agreement: false`;
- evidence checksum validation and explicit opponent confirmation;
- exact approval by both groups;
- refusal to finalize or write without both approvals;
- final `mutual_agreement: true`;
- approval evidence and final checksum;
- atomic, JSON-only candidate/final/evidence files;
- independent mock report isolation.

Release verification:

- Ruff format check: 58 files formatted;
- Ruff lint: passed;
- strict mypy: 42 source files passed;
- unittest: 134 tests passed;
- pytest: 134 tests passed;
- compileall: passed;
- pip dependency check: no broken requirements;
- internal-mode configuration validation: passed;
- production candidate command with placeholders: expected status `2`, listing all unresolved
  opponent metadata before reading evidence or writing a report;
- bonus-mode Gmail delivery: explicitly refused.

## Real-world blocker

Tasks requiring actual real-team metadata, real Phase 15 games, evidence exchange, discrepancy
resolution, explicit approvals, final report creation, and final checksum validation with the
opponent remain unchecked in `todo.md`. Completing them requires external data and consent that
have not been supplied.
