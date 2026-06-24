# Phase 13 Required Release Rehearsal

## Result

PASS - The exact required normal workflow was reproduced from a fresh GitHub clone and isolated
Python 3.12 environment. Static quality gates, all automated tests, local service startup, public
service authentication, the six-game remote run, structured logs, replay, report validation, Gmail
preflight, and secret scans passed. No unresolved critical or high defect remains.

## Frozen release identity

- Rehearsed Git commit: `8e9e60b7c152f824ee6de80746566e6f7a9b9bc6`
- Sanitized `config.json` SHA-256:
  `d868c6d413b5fb2b8578b6d52cc4683c21a1a1908a3343eb1571e5229de1c79b`
- Protocol version: `1.0`
- Cop URL: `https://salareen-cop.onrender.com/mcp`
- Thief URL: `https://salareen-thief.onrender.com/mcp`
- Python: `3.12.13`

The final evidence-document commit is later than the rehearsed code commit; the value above is the
exact source/config state exercised by the clean run.

## Clean setup

1. Cloned `origin/main` into a new random temporary directory.
2. Confirmed the clone was clean and matched commit `8e9e60b`.
3. Created a new `.venv`.
4. Installed the project with `.[gmail,dev]`.
5. Confirmed `pip check` reported no broken requirements.
6. Copied `.env.example` to ignored `.env`.
7. Passed tokens only through process environment variables; no credential file was copied into the
   clone.

## Static and automated quality gates

- Ruff formatter: 52 files already formatted.
- Ruff linter: all checks passed.
- Mypy strict mode: no issues in 39 source files.
- `compileall`: passed.
- `pip check`: no broken requirements.
- `unittest`: 110 tests passed.
- `pytest`: 110 tests passed.
- Focused game/observation/server contract suite: 42 tests passed.

The first clean rehearsal identified formatting and strict-typing debt. Those defects were corrected
and pushed as `8e9e60b`; this evidence comes from the second clean clone after the corrections.

## Local services

The clean clone started Cop and Thief as separate processes on ports 8101 and 8102 with
`--require-auth`.

- Cop authenticated health: `ok`
- Thief authenticated health: `ok`
- Separate process IDs: confirmed
- Processes were stopped after the smoke check.

## Public service checks

External checks against Render confirmed:

| Check | Cop | Thief |
|---|---|---|
| Public HTTPS URL | pass | pass |
| Missing token | HTTP 401 | HTTP 401 |
| Correct identity | `cop` | `thief` |
| Protocol | `1.0` | `1.0` |
| Correct private token | accepted | accepted |

The URLs are distinct. Tokens remained in ignored local/Render secret storage and were never
printed or committed.

## Final six-game run

Command:

```powershell
python main.py --mode internal --config config.json --local-mcp
```

Series ID:

`49d50f08-b90d-4af2-aa1d-fc3943f8b752`

Valid sub-game IDs:

1. `ea826cdb-bb74-4f3a-8389-e01b57bdf0e8`
2. `ad71af23-d159-452e-b3a6-6aa70d8106d8`
3. `0b01eb57-2e66-4c7b-af57-52304983c030`
4. `58011a03-473a-4ad1-a653-ffdb5f110ef1`
5. `07b2b3fc-4c51-4860-9d51-3a940222c6ba`
6. `a35df5cd-5ecb-4388-be04-c9eeb720c817`

Attempt IDs:

1. `3f9a8da9-adcd-4e59-9798-5aa818fd195f`
2. `1f8e7dea-ef5b-48d6-b748-f54e44b3ffe7`
3. `2147cb5a-37c8-4444-9086-4f9485cee6ab`
4. `f2ecfc65-5224-4300-b100-d76d260811ba`
5. `9ae9bb85-7e74-42ec-825a-a125a543eb0a`
6. `9d72d990-b7c8-4a73-80b3-4ea422ed6bd3`

Observed:

- exactly six valid games;
- zero invalid attempts in the final production run;
- Thief was first and Cop second in every recorded action sequence;
- maximum move count was 25;
- all six games ended by `move_limit`;
- each score row matched one allowed configured outcome;
- totals recalculated to Cop `30`, Thief `60`;
- terminal output displayed board, IDs, turn, scores, outcome, and report path;
- 312 structured events/snapshots were recorded; and
- every applied action carried request and correlation IDs.

## Game-rule and technical-failure checks

The focused game-rule suite confirms orthogonal movement, bounds, exact-cell capture, terminal
precedence, Cop-only adjacent barrier placement, five-barrier maximum, impassable barriers, no
trapping placement, scoring, and deterministic transitions.

An explicit rehearsal test injected a malformed-response technical failure. The failed attempt was
preserved, excluded from score/count, and replaced successfully.

## Replay and report

Replay command:

```powershell
python main.py --config config.json --replay-events artifacts/logs/engine_only_events.json
```

Result: `Replay complete: rendered_snapshots=312`.

`reports/internal_game_report.json`:

- parsed as a JSON object with no surrounding prose;
- contained exactly six ordered `sub_games`;
- included the expected IDs, attempts, seeds, move counts, outcomes, terminal reasons, scores,
  hashes, and event-log references;
- contained calculated totals matching all six score rows; and
- remained ignored and untracked.

## Gmail rehearsal

The final clean report passed Gmail preflight using the already-authorized ignored OAuth files from
the primary workspace:

- Recipient: `rmisegal+uoh26b@gmail.com`
- Scope: `https://www.googleapis.com/auth/gmail.send`
- Final rehearsal payload SHA-256:
  `b1ab6973b444dccd1252112ed9b4debcebf0bbb7bd1166c58f1a14af09219cb1`

No duplicate email was sent during Phase 13. The required live send had already succeeded in Phase
10 with Gmail message ID `19ef9469a7472c75`.

## Normal-mode independence

- Internal mode succeeds while bonus opponent values remain placeholders.
- Production bonus mode rejects those placeholders and is not required by the normal run.
- No Q-learning module, model provider, opponent service, or bonus report is imported by the
  required engine/orchestrator path.
- The heuristic baseline remains the active decision policy.

## Security and repository audit

- Fresh-clone secret-pattern scan: passed.
- Tracked-file scan found no `.env`, OAuth files, tokens, private keys, PDFs, virtual environments,
  generated report JSON, or bytecode.
- `.env` created from the example was ignored.
- The clean clone remained aligned with `origin/main`; only ignored runtime artifacts were created.
- The primary workspace's `.env`, `credentials.json`, `token.json`, reports, logs, and receipts
  remain ignored and untracked.

## Acceptance conclusion

All 12 baseline release criteria in PRD Section 13.3 have evidence:

1. mandatory normal requirements implemented;
2. six automatic `5 x 5` valid games;
3. technical failures excluded and replaced;
4. separate servers and URLs;
5. natural-language/structured decision path;
6. reachable authenticated public endpoints;
7. authoritative-state terminal view;
8. offline replay;
9. JSON-only validated report;
10. Gmail delivery evidence;
11. scientific/operational README; and
12. no tracked credentials or tokens.

Phase 13 is complete. Bonus and Q-learning remain optional later phases.
