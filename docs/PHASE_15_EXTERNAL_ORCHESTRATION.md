# Phase 15 — External Bonus Match Orchestration

## Status

The production orchestration path is implemented and fully exercised with deterministic
four-endpoint test clients. A real external series has not been run because `config.json` still
contains explicit opponent placeholders. No opponent identity, URL, token, agreement, game, or
score was invented.

## Implemented production flow

`python main.py --mode bonus --config config.json` now:

1. loads both groups' metadata and all four role URLs;
2. builds and prints the required games 1–6 schedule;
3. writes `artifacts/reports/bonus_agreement.json`;
4. requires `BONUS_AGREEMENT_SHA256` to match that exact manifest;
5. reads four tokens only from the environment;
6. verifies health, authentication, role identity, protocol `1.0`, and `decide` on all endpoints;
7. runs games 1–3 with our Cop and opponent Thief;
8. runs games 4–6 with opponent Cop and our Thief;
9. keeps the local immutable engine authoritative;
10. replaces bounded technical-failure attempts without scoring them;
11. attributes role scores to the endpoint-owning group;
12. writes replayable events and canonical exchange evidence with a SHA-256.

The optional `--bonus-preflight-only` flag performs steps 1–6 and exits without starting a game.

## Agreement procedure

The agreement manifest includes both groups, repositories, student arrays, all four URLs, protocol
version, grid, move/barrier limits, observation radius, scoring, base seed, six first-attempt
seeds, timeouts, retry limits, replacement-attempt limit, and the exact 3+3 schedule.

The groups must compare the same file and hash out of band. Only after both approve it should each
operator set:

```powershell
$env:BONUS_AGREEMENT_SHA256="<approved manifest hash>"
```

Tokens remain private:

```powershell
$env:COP_MCP_TOKEN="<our Cop token, if required>"
$env:THIEF_MCP_TOKEN="<our Thief token, if required>"
$env:OPPONENT_COP_MCP_TOKEN="<opponent Cop token>"
$env:OPPONENT_THIEF_MCP_TOKEN="<opponent Thief token>"
```

The CLI never prints or serializes token values.

## Evidence exchange and discrepancy resolution

Successful execution creates:

- `artifacts/logs/bonus_events.json` — authoritative event/replay history;
- `artifacts/reports/bonus_match_evidence.json` — six games, endpoint ownership, attempts,
  outcomes, scores, state hashes, totals, agreement hash, and evidence hash.

Send the identical evidence file to the opponent through the mutually chosen private channel.
Both groups must independently compare the evidence SHA-256, six matchup assignments, seeds,
actions, terminal outcomes, scores, and totals. If anything differs, keep Phase 16 blocked and
resolve it by replaying the event evidence. Do not edit results by hand.

## Automated verification

The Phase 15 tests prove:

- ordered 3+3 schedule construction;
- rejection of reversed or duplicated assignments;
- explicit shared-agreement confirmation;
- four endpoint role/protocol preflight;
- normal authoritative rules and scoring;
- six valid games in both directions;
- ownership-based group totals;
- technical-attempt replacement;
- canonical evidence with no authentication tokens.

Release verification:

- Ruff format check: 57 files formatted;
- Ruff lint: passed;
- strict mypy: 42 source files passed;
- unittest: 126 tests passed;
- pytest: 126 tests passed;
- compileall: passed;
- pip dependency check: no broken requirements;
- internal-mode configuration validation: passed;
- production bonus preflight with repository placeholders: expected status `2`, with all five
  unresolved opponent fields listed before any endpoint or game action.

## Real-run blocker

The following real values are still required from the opponent:

- group name;
- student list;
- GitHub repository;
- Cop MCP HTTPS URL;
- Thief MCP HTTPS URL;
- Cop and Thief authentication tokens/instructions;
- explicit approval of the generated agreement hash.

Until supplied, production bonus mode correctly returns non-zero before any game. Therefore tasks
that claim real metadata exchange, real games, evidence sharing, and discrepancy resolution remain
unchecked in `todo.md`.
