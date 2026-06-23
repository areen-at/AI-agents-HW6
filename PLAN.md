# Phased Delivery Plan: Dual AI Agent Race via MCP Servers

## 1. Planning approach

This plan converts `PRD.md` and `todo.md` into gated implementation phases. The checklist in
`todo.md` is the task-level source of truth; this document explains the intent, deliverables,
verification, and dependencies for each phase.

Every phase must leave the repository in a testable state. Later phases may not compensate for a
failed earlier correctness gate. In particular, deployment, Gmail delivery, bonus automation, GUI
work, and Q-learning must not begin before the deterministic game behavior and MCP boundaries are
stable.

Phase 0 and Phase 1 are already complete:

- Phase 0 closed the assignment decisions and repository baseline.
- Phase 1 created the Python foundation, safe configuration, package skeleton, config validator,
  tests, and Git safety workflow.

The next implementation phase is Phase 2: core domain model.

## 2. Delivery principles

- Build deterministic domain objects before game rules.
- Build game rules before observations.
- Build observations before agent prompts.
- Build local MCP before remote MCP.
- Build required normal mode before optional bonus mode.
- Use simple deterministic/heuristic policies before Q-learning.
- Keep the orchestrator authoritative for workflow only; it must not invent strategic moves.
- Keep secrets outside committed files.
- Record evidence at every gate.

## 3. Repository layout

The active package layout is:

```text
.
|-- README.md
|-- PRD.md
|-- PLAN.md
|-- todo.md
|-- pyproject.toml
|-- config.json
|-- main.py
|-- .env.example
|-- docs/
|-- reports/
|-- artifacts/
|-- src/
|   `-- ai_agents_hw6/
|       |-- agents/
|       |-- application/
|       |-- contracts/
|       |-- domain/
|       |-- infrastructure/
|       |-- mcp_servers/
|       |-- reporting/
|       `-- ui/
`-- tests/
    `-- unit/
```

The package boundaries are intentional:

- `domain` owns value objects, state, rules, scoring, and invariant checks.
- `application` owns series workflow, technical-failure recovery, replay, and orchestration logic.
- `contracts` owns action, observation, report, and MCP schemas.
- `agents` owns deterministic, heuristic, optional model-backed, and optional learning policies.
- `mcp_servers` owns the two role-specific MCP server entry points.
- `infrastructure` owns configuration, persistence, network clients, Gmail, and deployment adapters.
- `reporting` owns JSON report construction and validation.
- `ui` owns terminal rendering and any optional future GUI projection.

## 4. Phase summary

| Phase | Outcome | Mandatory gate |
|---:|---|---|
| 0 | Repository inspection and decision closure | Requirements, scope, ambiguity, and Git baseline approved |
| 1 | Project foundation and configuration | Config validator, package skeleton, tests, and safety workflow pass |
| 2 | Core domain model | Value objects, immutable state, seeded initialization, and invariants pass |
| 3 | Game rules, scoring, and small-board checks | Legal actions, transitions, terminal logic, and scoring pass |
| 4 | Series control, events, replay, and internal report | Six valid engine-only games and replay/report skeleton pass |
| 5 | Simple heuristic agents | Cop and Thief policies produce legal typed actions from role inputs |
| 6 | Partial observations and natural-language protocol | No hidden state leaks; prompts and action parsing are validated |
| 7 | Independent Cop and Thief MCP servers | Separate role servers expose health, identity, protocol, and decision operations |
| 8 | Local MCP orchestrator and required run | Six valid local games complete exclusively through MCP decisions |
| 9 | Terminal visualization and operational logging | Terminal projection, structured logs, and evidence manifest match events |
| 10 | Gmail and normal-report delivery | Internal JSON validates; fake Gmail passes; live delivery is ready when authorized |
| 11 | Deployment of our two MCP servers | Two secure public URLs pass health, auth, and remote-run checks |
| 12 | README and scientific documentation | Scientific/operational README covers Dec-POMDP, setup, deployment, and evidence |
| 13 | Required release rehearsal | Full normal submission rehearsal passes with no secrets or unresolved blockers |
| 14 | Bonus configuration and mock isolation | Bonus config supports real opponents; mock remains test-only |
| 15 | External bonus match orchestration | Six valid cross-group games complete against real external URLs |
| 16 | Bonus report and mutual agreement | Joint JSON validates and is mutually approved |
| 17 | Optional Q-learning after completion | Learning is measured and feature-flagged without breaking baseline behavior |

## 5. Phase 0 - Repository inspection and decisions

Phase 0 is complete. Its evidence is recorded in:

- `docs/PHASE_0_BASELINE.md`
- `docs/PHASE_0_VERIFICATION.md`

Exit conditions already satisfied:

- assignment and clarification read;
- normal-vs-bonus scope resolved;
- opponent bonus servers defined as external production URLs only;
- coordinate, turn-order, observation, barrier, retry, and report decisions closed;
- `.gitignore` protections added; and
- phase evidence committed and pushed.

## 6. Phase 1 - Project foundation and configuration

Phase 1 is complete. Its evidence is recorded in:

- `docs/PHASE_1_FOUNDATION.md`

Delivered:

1. Python project metadata in `pyproject.toml`.
2. Safe example config in `config.json`.
3. Names-only secret template in `.env.example`.
4. Package skeleton under `src/ai_agents_hw6`.
5. Minimal CLI in `main.py`.
6. Typed config loader and mode validator.
7. Standard-library unit tests for configuration behavior.
8. Git workflow and ignore-rule safeguards.

Verification commands:

```powershell
python main.py --mode internal --config config.json
python main.py --mode bonus-mock --config config.json
python main.py --mode bonus --config config.json
$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'
python -m compileall -q main.py src tests
python -m pip check
```

Expected results:

- `internal` and `bonus-mock` validation pass;
- `bonus` rejects placeholder opponent data until real external team data is configured;
- unit tests pass;
- bytecode compilation succeeds;
- dependency check passes; and
- no secrets, assignment PDFs, private reports, caches, or virtual environments are staged.

## 7. Phase 2 - Core domain model

### Objective

Create the pure domain foundation without implementing full transition rules yet.

### Tasks

1. Define roles, directions, action kinds, terminal outcomes, terminal reasons, and technical-failure
   reason codes.
2. Implement immutable `Coordinate` and `GridSize` value objects.
3. Implement coordinate serialization, direction deltas, and bounded orthogonal neighbors.
4. Define immutable identifiers for series, sub-games, attempts, and requests.
5. Define immutable authoritative `GameState`.
6. Include grid, Cop position, Thief position, barriers, active role, move counter, barrier count,
   seed, and terminal metadata.
7. Prevent mutable collection leakage from domain objects.
8. Implement seeded initial placement inside bounds with distinct positions.
9. Start every initialized game with empty barriers and Thief active.
10. Enforce basic invariants:
    - positions in bounds;
    - barriers in bounds;
    - no barrier under a player;
    - unique barriers;
    - non-negative counters;
    - valid active role; and
    - terminal metadata consistency.

### Deliverables

- Domain enums and value objects.
- Immutable authoritative state.
- Seeded initialization function.
- Unit tests for corners, edges, serialization, reproducibility, and invariant failures.
- Phase 2 evidence document.

### Exit gate

- All domain tests pass.
- Same seed produces the same initial state.
- Invalid state construction is rejected with useful errors.
- `domain` imports no MCP, UI, Gmail, provider, or infrastructure code.

## 8. Phase 3 - Game rules, scoring, and small-board checks

### Objective

Implement authoritative rules and scoring on top of the Phase 2 domain model.

### Tasks

1. Generate legal movement actions for both roles.
2. Reject out-of-bounds, diagonal, stay, barrier-collision, and out-of-turn actions.
3. Enforce Thief-first sequencing.
4. Detect exact-cell Cop capture.
5. Declare Thief survival at the configured move limit.
6. Apply capture precedence on the final round.
7. Implement Cop-only adjacent barrier placement.
8. Enforce maximum barrier count.
9. Reject barrier placement on players, existing barriers, out-of-bounds cells, or trapping states.
10. Guarantee invalid actions do not mutate state.
11. Compute score from terminal outcome and config.
12. Exhaustively test `2 x 2` behavior where practical.
13. Run sanity suites on progressive grids up to `5 x 5`.

### Exit gate

- Rule and scoring tests pass.
- Terminal state accepts no new game action.
- Scores always match the configured matrix.
- Deterministic action replay reaches the same final state.

## 9. Phase 4 - Series control, events, replay, and internal report

### Objective

Run complete engine-only series and record enough evidence for replay and report generation.

### Tasks

1. Implement a series controller independent of MCP.
2. Track six valid game slots and replacement attempts.
3. Separate valid-game count from technical-attempt count.
4. Preserve invalid-attempt evidence without scoring it.
5. Add append-only events with IDs, timestamps, seed, actions, validation, state hashes, terminal
   reason, and scores.
6. Implement atomic event persistence.
7. Implement offline replay from seed and accepted actions.
8. Verify replay hashes and final scores.
9. Build the internal `sub_games` report entries from immutable terminal records.
10. Calculate aggregate totals.
11. Write `reports/internal_game_report.json` atomically.

### Exit gate

- Engine-only six-game run completes.
- Injected technical failures are excluded and replaced.
- Replay verifies all valid games.
- Internal report JSON validates and contains exactly six valid `sub_games`.

## 10. Phase 5 - Simple heuristic agents

### Objective

Provide reliable baseline policies before optional model-backed or learning behavior.

### Tasks

1. Define role-neutral policy input and output interfaces.
2. Implement deterministic seeded tie-breaking.
3. Implement Cop pursuit using only permitted role input.
4. Implement Thief evasion using only permitted role input.
5. Implement deterministic scripted and random policies for tests.
6. Add illegal-action and timeout/fault-injection policies for later recovery tests.

### Exit gate

- Heuristic policies produce typed actions.
- Policies do not import engine internals that expose hidden state.
- Engine-only games can run with policy adapters.

## 11. Phase 6 - Partial observations and natural-language protocol

### Objective

Turn authoritative state into role-safe observations and role prompts, then parse untrusted action
responses.

### Tasks

1. Implement Manhattan-radius observations with default radius `2`.
2. Build role-specific observation DTOs.
3. Prove hidden opponent/barrier data cannot leak outside the configured sensor model.
4. Create natural-language decision prompts.
5. Define strict structured action response schema.
6. Validate policy/model outputs.
7. Allow one bounded repair request for malformed or illegal output.
8. Mark repeated failures as technical failures.

### Exit gate

- Observation leak tests pass.
- Golden prompt tests pass.
- Malformed, oversized, adversarial, and illegal outputs are rejected safely.

## 12. Phase 7 - Independent Cop and Thief MCP servers

### Objective

Expose the Cop and Thief as separate local MCP services with compatible contracts.

### Tasks

1. Implement Cop MCP server entry point.
2. Implement Thief MCP server entry point.
3. Give each server separate role identity and config.
4. Expose health/capabilities, role identity, protocol version, and decision operations.
5. Add request IDs, correlation IDs, idempotency keys, and timeouts.
6. Add local token authentication or preserve the same adapter contract for gateway auth.
7. Add contract tests for schema, role, version, and wrong-role failures.

### Exit gate

- Cop and Thief run in separate processes and ports.
- Role and protocol compatibility checks pass.
- MCP decision responses are schema-validated before engine use.

## 13. Phase 8 - Local MCP orchestrator and required run

### Objective

Run the required six valid games through the actual local MCP decision path.

### Tasks

1. Implement MCP client adapters.
2. Start or connect to both local role servers.
3. Run health waits before series start.
4. Request Thief and Cop decisions in turn order.
5. Prevent duplicate decisions from being applied twice.
6. Convert exhausted retries, server crashes, and unrecoverable malformed outputs into technical
   failures.
7. Replace invalid attempts until six valid games exist or the safety limit is reached.

### Exit gate

- Six valid local games complete exclusively through MCP.
- Fault-injected attempts are excluded and replaced.
- Offline replay verifies the MCP-generated series.

## 14. Phase 9 - Terminal visualization and operational logging

### Objective

Make the system observable and usable in a terminal-first workflow.

### Tasks

1. Render the board from committed events or read-only projections.
2. Show Cop, Thief, barriers, visible/hidden status, active role, move counter, game count, scores,
   endpoint health, and technical-failure state.
3. Emit structured logs with correlation IDs.
4. Redact secrets automatically.
5. Produce a replay-to-console mode.
6. Produce an evidence manifest linking config digest, commit, tests, logs, replays, and reports.

### Exit gate

- Terminal projection matches the event stream.
- Logs contain no secrets.
- Replay and live views agree.

## 15. Phase 10 - Gmail and normal-report delivery

### Objective

Implement the required Gmail API delivery path for the internal JSON report.

### Tasks

1. Follow `main-google-api-installtion-guid.pdf`.
2. Configure OAuth credentials outside Git.
3. Implement least-privilege Gmail send adapter.
4. Implement token refresh and redacted errors.
5. Add fake Gmail tests.
6. Validate JSON-only message body.
7. Record Gmail message ID and timestamp after final send.

### Exit gate

- Fake Gmail tests pass.
- Live OAuth preflight is ready when credentials are provided.
- Report failure can be retried without rerunning games or duplicating sends.

## 16. Phase 11 - Deployment of our two MCP servers

### Objective

Publish our two production-owned role servers through secure external URLs.

### Tasks

1. Choose the cloud/tunnel provider for `OD-07`.
2. Package Cop and Thief services reproducibly.
3. Configure separate HTTPS URLs.
4. Configure scoped token authentication, rotation, and revocation.
5. Add remote health probes.
6. Run authorized and unauthorized external client checks.
7. Run a full remote six-valid-game series.

### Exit gate

- Cop and Thief URLs are distinct, public, HTTPS, and authenticated.
- Unauthorized requests fail safely.
- Remote results replay locally.

## 17. Phase 12 - README and scientific documentation

### Objective

Complete the scientific and operational README expected by the assignment.

### Tasks

1. Document installation, configuration, and secrets.
2. Document the Dec-POMDP tuple and mapping.
3. Document actions, transitions, rewards, observations, and discount factor if learning is enabled.
4. Document MCP server/client boundaries and natural-language protocol.
5. Document terminal operation, reports, Gmail, deployment, and troubleshooting.
6. Document tests, evidence, known limitations, and public endpoint availability.

### Exit gate

- README is enough for an assessor to reproduce the run.
- All Must requirements in the PRD have linked evidence or an explicit remaining phase.

## 18. Phase 13 - Required release rehearsal

### Objective

Execute the exact final normal-mode workflow before final submission.

### Tasks

1. Freeze code, schemas, config defaults, and protocol version.
2. Run formatting, linting, typing, unit, contract, integration, replay, report, and end-to-end tests.
3. Run dependency and secret scans.
4. Verify GitHub repository accessibility.
5. Verify public MCP endpoints from a clean external client.
6. Run final six valid sub-games.
7. Replay all valid games.
8. Build and validate internal report.
9. Send or stage Gmail delivery according to final operator authorization.
10. Archive commit ID, config digest, logs, replays, report, and delivery receipt.

### Exit gate

- Full normal submission rehearsal passes.
- No unresolved critical/high defect remains.
- No secret or private data is tracked.

## 19. Phase 14 - Bonus configuration and mock isolation

### Objective

Prepare optional bonus mode without inventing another production team.

### Tasks

1. Require real opponent metadata and HTTPS URLs in `--mode bonus`.
2. Keep placeholder opponent values valid only in `--mode bonus-mock`.
3. Keep mock opponent servers test-only.
4. Validate bonus report schema separately from internal report schema.
5. Document that mutual agreement starts false until both teams approve.

### Exit gate

- Real bonus mode fails fast without real opponent data.
- Bonus mock tests cannot be mistaken for production bonus evidence.

## 20. Phase 15 - External bonus match orchestration

### Objective

Run the optional inter-group series against another real class team's MCP URLs.

### Tasks

1. Exchange GitHub URLs, MCP URLs, protocol versions, and authentication instructions.
2. Agree on schedule, seeds, observation policy, barrier interpretation, timeouts, and retry policy.
3. Verify all four endpoints.
4. Run three games with our Cop versus opponent Thief.
5. Run three games with opponent Cop versus our Thief.
6. Exclude and replay technical failures.
7. Share artifacts with the opponent group.

### Exit gate

- Six valid cross-group games exist.
- Both groups can independently recalculate scores from the same events.

## 21. Phase 16 - Bonus report and mutual agreement

### Objective

Produce the mutually agreed optional bonus JSON report.

### Tasks

1. Build canonical bonus report JSON.
2. Include both groups, repositories, all four MCP URLs, students, sub-games, totals, and bonus claim.
3. Set `mutual_agreement` to `true` only after both groups approve the exact payload.
4. Validate JSON-only formatting.
5. Send according to the assignment procedure.

### Exit gate

- Bonus report validates.
- Both groups approve the exact payload.
- Delivery evidence is preserved.

## 22. Phase 17 - Optional Q-learning after completion

### Objective

Improve strategy only after the required baseline is stable.

### Tasks

1. Define role-specific state encodings from observations.
2. Define action masks.
3. Implement Q-table initialization, update, and persistence.
4. Add epsilon-greedy selection.
5. Keep alpha, gamma, and epsilon configurable.
6. Compare learned behavior against random and heuristic baselines.
7. Keep a feature flag to revert to the required heuristic baseline.

### Exit gate

- Learning improves or is disabled.
- Baseline MCP, report, replay, and security behavior remains unchanged.

## 23. Mandatory GitHub phase workflow

After every completed phase, Codex must:

1. Run the tests and checks defined for that phase.
2. Run `git status`.
3. Inspect changed, staged, untracked, and intentionally ignored paths.
4. Review staged content for secrets, credentials, tokens, private reports, generated junk, and
   assignment PDFs.
5. Confirm `.gitignore` protects:
   - `.env`
   - `*.env`
   - API keys, tokens, credentials, and private keys
   - `__pycache__/`
   - `*.pyc`
   - `.venv/`
   - `venv/`
   - `.DS_Store`
   - private `reports/*.json`
   - assignment PDFs unless explicitly authorized
6. Stage only files belonging to the phase.
7. Commit with a clear phase-specific message.
8. Present an informational pre-push summary.
9. Push ordinary phase commits automatically to `origin/main`.
10. Verify local and remote branch synchronization.

Ordinary pushes are pre-authorized by the user. Force-pushes, history rewrites, destructive Git
operations, or changing the target remote/branch still require explicit approval.

## 24. Primary release checklist

### Rules and series

- [ ] `5 x 5` default grid.
- [ ] Thief acts before Cop.
- [ ] Orthogonal movement only.
- [ ] Exact-cell capture and move-limit survival.
- [ ] Cop barriers and five-barrier maximum.
- [ ] Six valid games complete.
- [ ] Score matrix and totals correct.

### Architecture

- [ ] Separate Cop and Thief MCP processes.
- [ ] Separate MCP URLs.
- [ ] Natural-language decision requests and structured actions.
- [ ] Partial observations verified.
- [ ] Orchestrator contains no strategic fallback.

### Operations

- [ ] Local run succeeds.
- [ ] Remote HTTPS run succeeds.
- [ ] Authentication and revocation tested.
- [ ] Technical failures replayed.
- [ ] Logs, replay artifacts, and reports verified.

### Submission

- [ ] GitHub repository accessible.
- [ ] Scientific README complete.
- [ ] Internal JSON report validates.
- [ ] Gmail API delivery confirmed when authorized.
- [ ] No secrets in repository or evidence bundle.
