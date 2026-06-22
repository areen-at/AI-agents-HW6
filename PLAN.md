# Phased Delivery Plan: Dual AI Agent Race via MCP Servers

## 1. Planning approach

This plan converts `PRD.md` into gated increments. Each phase must leave the repository in a testable state. Later phases may not compensate for a failed earlier correctness gate; in particular, remote deployment, GUI work, and Q-learning must not begin before the authoritative game engine and MCP contracts are stable.

### 1.1 Delivery principles

- Build the deterministic core before any model integration.
- Keep policy, transport, orchestration, engine, UI, and reporting separate.
- Add one distributed boundary at a time.
- Use progressive board sizes: `2x2`, `3x2/3x3`, `4x3/4x4`, then `5x5`.
- Preserve evidence at every gate.
- Treat Q-learning and bonus automation as extensions, not blockers for baseline compliance.
- Never commit real secrets.

### 1.2 Proposed repository layout

```text
.
|-- README.md
|-- PRD.md
|-- PLAN.md
|-- pyproject.toml
|-- config/
|   |-- config.example.yaml
|   `-- schemas/
|-- src/
|   |-- domain/
|   |-- application/
|   |-- contracts/
|   |-- agents/
|   |-- mcp_servers/
|   |-- infrastructure/
|   |-- reporting/
|   |-- ui/
|   `-- cli/
|-- tests/
|   |-- unit/
|   |-- contract/
|   |-- integration/
|   |-- e2e/
|   `-- fixtures/
|-- artifacts/
|   |-- logs/
|   |-- replays/
|   `-- reports/
|-- scripts/
`-- deploy/
```

The exact package names may change, but the boundaries must remain.

## 2. Phase summary

| Phase | Outcome | Mandatory gate |
|---:|---|---|
| 0 | Decisions, schemas, and project skeleton | Requirements and ambiguity review approved |
| 1 | Deterministic 2x2 engine | Exhaustive rule tests pass |
| 2 | Full configurable 5x5 game and replay | Game/scoring invariants pass through progressive grids |
| 3 | Agent policy and natural-language decision contracts | Deterministic provider and malformed-output tests pass |
| 4 | Two local MCP servers and orchestrator | Six valid local games complete through MCP |
| 5 | GUI, observability, report builder, and Gmail adapter | Replay, GUI, JSON, and fake-email tests pass |
| 6 | Secure remote deployment | Two authenticated public URLs pass external probes |
| 7 | Full release rehearsal and submission | End-to-end acceptance and secret scan pass |
| 8 | Optional Q-learning hardening | Strategy improves without breaking contracts |
| 9 | Optional inter-group bonus | Joint six-game report is mutually validated |

## 3. Phase 0 - Requirements closure and foundation

### Objective

Turn the assignment and PRD into frozen contracts before implementation.

### Tasks

1. Review `PRD.md` with the team.
2. Resolve open decisions `OD-01` through `OD-08` or assign owners and deadlines.
3. Decide the baseline Python version and dependency manager; Python 3.10+ with `uv` is recommended.
4. Define package/module boundaries.
5. Create `pyproject.toml` with lint, type-check, and test tooling.
6. Create the example configuration and its validation schema.
7. Define typed schemas for:
   - game configuration;
   - authoritative state;
   - role observation;
   - action request/response;
   - MCP health/capabilities;
   - event log;
   - terminal result;
   - internal report; and
   - bonus report.
8. Define error codes and technical-failure taxonomy.
9. Establish logging and artifact directory conventions.
10. Add `.gitignore`, `.env.example`, and a secret-handling policy.
11. Configure CI for formatting, linting, type checking, and tests.
12. Create a requirements-to-test traceability file or section in the README.

### Deliverables

- Approved PRD and closed decision log.
- Project skeleton.
- Configuration and JSON schemas.
- CI workflow.
- Empty but runnable CLI entry point.

### Verification

- Configuration defaults match PRD Section 8.8.
- Bad configuration fails fast.
- Schema fixtures include valid and invalid examples.
- CI runs without external secrets or network access.
- Secret scan reports no findings.

### Exit gate

- No unresolved rule ambiguity blocks the game engine.
- Interfaces have named owners and version `1.0` drafts.
- The team can explain which component owns every state transition.

## 4. Phase 1 - Deterministic game engine on 2x2

### Objective

Prove the game model and transition rules in the smallest exhaustively testable environment.

### Tasks

1. Implement immutable/value domain objects:
   - coordinates;
   - grid dimensions;
   - roles;
   - directions;
   - barriers;
   - actions;
   - score values;
   - terminal reasons; and
   - game identifiers.
2. Implement seeded initialization with distinct valid positions.
3. Implement legal movement generation.
4. Implement action validation without mutation.
5. Implement Thief-first turn sequencing.
6. Implement Cop capture.
7. Implement move-limit survival.
8. Implement barrier placement and maximum count.
9. Implement terminal-state immutability.
10. Implement score calculation from terminal result.
11. Implement authoritative state serialization and hashing.
12. Write exhaustive `2x2` state/action tests.

### Required invariants

- Exactly one active role at any non-terminal transition.
- Positions and barriers always remain within bounds.
- No player occupies a barrier.
- A barrier cannot be duplicated.
- Invalid actions leave the state byte-for-byte equivalent.
- Cop capture occurs only under the approved capture rule.
- Terminal state accepts no new game action.
- Scores always match the configured matrix.

### Deliverables

- Pure game-domain package with no MCP, model, GUI, or Gmail dependency.
- Unit/property test suite.
- Minimal text simulation using scripted actions.

### Verification

- Exhaust all reachable `2x2` states where practical.
- Test all boundary movements and barrier placements.
- Test terminal precedence on the final move.
- Test all four score outputs.
- Test identical replay from seed and action sequence.

### Exit gate

- 100% branch coverage for rule and scoring modules is the target.
- No unresolved high-severity engine defect.
- The engine is deterministic under a fixed seed and action stream.

## 5. Phase 2 - Full configurable game, observations, and replay

### Objective

Scale the verified engine to the assignment game while preserving determinism and partial observability.

### Tasks

1. Implement the approved observation function from `OD-01`.
2. Create role-specific observation DTOs with no reference to mutable engine state.
3. Add observation-leak tests.
4. Scale through `3x2`, `3x3`, `4x3`, `4x4`, and `5x5` fixtures.
5. Implement the six-valid-game series state machine.
6. Assign unique series, sub-game, and attempt IDs.
7. Implement append-only event records.
8. Implement deterministic replay without MCP or models.
9. Add state and event integrity hashes.
10. Implement technical-attempt invalidation and replacement.
11. Add safety limits for repeated technical failures without counting them as valid games.
12. Implement aggregate scoring directly from immutable terminal records.
13. Add configuration digest and code-version metadata.

### Progressive verification

#### 3x2 / 3x3

- Verify turn synchronization and barrier edge cases.
- Run deterministic scripted agents through full episodes.
- Confirm no duplicate action application.

#### 4x3 / 4x4

- Verify partial observations across positions and barriers.
- Verify replay integrity for longer games.
- Fuzz legal/illegal action sequences.

#### 5x5

- Run six scripted valid games at 25-move cap.
- Inject technical failures and confirm replacements.
- Confirm final totals equal the sum of immutable sub-game records.

### Deliverables

- Full configurable engine.
- Observation service.
- Series controller independent of transport.
- Event log and offline replay command.

### Exit gate

- All progressive board stages pass.
- Six valid games complete after injected invalid attempts.
- Every valid game replays to the same terminal state and score.
- No hidden authoritative field reaches an agent observation.

## 6. Phase 3 - Agent policy and natural-language protocol

### Objective

Create a provider-independent decision layer that turns role observations into schema-valid action proposals.

### Tasks

1. Define a role-neutral `Policy` interface.
2. Implement deterministic policies for tests:
   - fixed action;
   - seeded random legal action;
   - scripted action sequence; and
   - malformed/timeout fault injectors.
3. Build role-specific prompt templates describing:
   - identity and objective;
   - current observation;
   - legal action vocabulary;
   - known history;
   - barrier rules for the Cop;
   - output JSON schema; and
   - prohibition on inventing hidden state.
4. Implement strict output parsing and schema validation.
5. Implement one bounded repair round for malformed or illegal proposals.
6. Implement the approved repeated-illegal-action policy from `OD-04`.
7. Add an LLM provider abstraction.
8. Implement the selected baseline provider.
9. Add a local Ollama adapter or external provider adapter according to `OD-08`.
10. Add prompt/output redaction and size limits.
11. Record latency, provider, model, validation, and repair metadata.

### Security checks

- Prompt contains no secret or full authoritative state.
- Model output cannot invoke arbitrary code.
- Only schema-approved actions can reach the engine.
- Provider errors do not reveal credentials.

### Deliverables

- Policy abstraction and deterministic providers.
- Natural-language prompt templates.
- Validated action parser.
- At least one real model provider adapter.

### Verification

- Golden prompt tests for Cop and Thief.
- Valid, malformed, oversized, adversarial, and illegal output tests.
- Provider timeout and retry tests.
- Deterministic test provider completes a full series.

### Exit gate

- No raw model output can bypass validation.
- A valid role observation produces one typed action.
- Repair and failure semantics match the PRD.

## 7. Phase 4 - Local dual MCP architecture

### Objective

Run both agents through separate local MCP servers and prove the distributed control path.

### Tasks

1. Implement Cop MCP server entry point.
2. Implement Thief MCP server entry point.
3. Give each server separate configuration and role identity.
4. Expose MCP operations for:
   - health/capabilities;
   - role identity;
   - protocol version;
   - decision request; and
   - optional policy import/export.
5. Implement the orchestrator's MCP client adapter.
6. Add request IDs, correlation IDs, idempotency keys, and timeouts.
7. Prevent duplicate decision responses from applying twice.
8. Implement startup compatibility checks.
9. Add local token authentication if supported by the selected transport; otherwise enforce it at the gateway and preserve the same client contract.
10. Provide commands/scripts to launch both servers and the orchestrator.
11. Add health wait/retry before starting a series.
12. Capture protocol traces with sensitive data redacted.

### Deliverables

- Two independently runnable MCP servers.
- MCP client/orchestrator integration.
- Local launch documentation.
- Contract and integration tests.

### Failure injection matrix

| Fault | Expected behavior |
|---|---|
| One server absent at startup | Series does not start |
| Timeout before action commit | Bounded retry with same idempotency key |
| Duplicate response | Apply once |
| Wrong role server | Compatibility failure |
| Schema version mismatch | Fail fast |
| Malformed action after repair | Attempt marked technical failure |
| Server crash mid-game | Attempt preserved as invalid and replacement scheduled |

### Exit gate

- Cop and Thief run in separate processes and ports.
- Six valid games complete exclusively through MCP decisions.
- Fault-injected attempts are excluded and replaced.
- Offline replay verifies the final series.

## 8. Phase 5 - GUI, observability, reports, and Gmail

### Objective

Make the system operable, auditable, and capable of producing the exact required submission report.

### 8.1 GUI tasks

1. Select a lightweight GUI framework compatible with headless core execution.
2. Implement a read-only board projection driven by committed events.
3. Render distinct Cop, Thief, barrier, visible/hidden information, and status elements.
4. Display move counter, active role, game count, scores, endpoint health, and failure state.
5. Add start, safe pause/resume, stop, and report-preview controls.
6. Ensure controls call application services rather than the engine directly.
7. Add accessibility labels and non-color indicators.

### 8.2 Observability tasks

1. Emit structured JSON logs.
2. Add human-readable console logs without secrets.
3. Expose operational counters and final summary.
4. Add a replay viewer or replay-to-console mode.
5. Produce an evidence manifest linking tests, logs, replays, reports, code version, and configuration digest.

### 8.3 Report tasks

1. Finalize the `sub_games` schema under `OD-05`.
2. Implement internal report construction from immutable records.
3. Implement bonus report construction separately.
4. Calculate totals; never trust caller-provided totals.
5. Validate against JSON Schema.
6. Serialize canonical JSON with no surrounding prose.
7. Store the payload atomically before send.

### 8.4 Gmail tasks

1. Follow the supplied Google API installation guide.
2. Configure the Google Auth consent screen and test user.
3. Enable Gmail API with least-privilege scopes suitable for sending.
4. Obtain local OAuth client credentials without committing them.
5. Implement a Gmail transport adapter.
6. Implement token refresh and redacted error handling.
7. Add fake-transport tests.
8. Perform one authorized live smoke email to a safe test destination if allowed.
9. Add final recipient `rmisegal+uoh26b@gmail.com` through validated configuration.
10. Record the Gmail message ID after final delivery.

### Deliverables

- GUI and headless CLI parity.
- Structured logs and replay evidence.
- Valid internal and bonus report builders.
- Gmail API adapter and operator procedure.

### Exit gate

- GUI projection always matches the engine event stream.
- Internal JSON validates and contains no free text.
- Fake Gmail tests pass and live OAuth preflight succeeds.
- Reporting failure can retry without rerunning games or sending duplicates.

## 9. Phase 6 - Secure remote deployment

### Objective

Publish the two MCP servers at separate secure, externally reachable endpoints.

### Tasks

1. Select cloud/tunnel architecture under `OD-07`.
2. Package both role servers reproducibly.
3. Create separate deployment definitions and environment configurations.
4. Provision separate Cop and Thief URLs.
5. Configure HTTPS/TLS.
6. Configure token authentication, rotation, and revocation.
7. Configure rate limits and request-size limits.
8. Verify logs redact authorization headers.
9. Add remote health probes.
10. Document firewall, proxy, Nginx, ngrok/Localtonet, or Prefect settings used.
11. Verify the selected LLM network path:
    - external provider API; or
    - securely tunneled local Ollama; or
    - hybrid outbound architecture.
12. Run external authorized and unauthorized client probes.
13. Run a remote six-valid-game series.
14. Preserve endpoint availability instructions for assessment and bonus use.

### Deployment acceptance checklist

- [ ] Cop and Thief URLs are different.
- [ ] Both use HTTPS.
- [ ] Requests without credentials fail.
- [ ] Requests with valid scoped credentials succeed.
- [ ] Tokens can be revoked and rotated.
- [ ] Role and protocol versions are correct.
- [ ] No inbound dependency on inaccessible localhost exists.
- [ ] Six valid remote games complete.
- [ ] Remote results replay locally.

### Exit gate

- Two authenticated public MCP URLs pass external probes.
- A complete remote series succeeds.
- Threat and secret reviews have no unresolved critical findings.

## 10. Phase 7 - Release rehearsal and primary submission

### Objective

Execute the exact final workflow and produce a complete, auditable submission.

### Tasks

1. Freeze code, schemas, configuration defaults, and protocol version.
2. Run formatting, linting, type checking, unit, property, contract, integration, and end-to-end tests.
3. Run dependency and secret scans.
4. Verify GitHub repository visibility and README completeness.
5. Verify public endpoints and credentials from a clean external client.
6. Run the final six-valid-game series.
7. Confirm any technical attempts were excluded and replaced.
8. Replay all six valid games offline.
9. Compare replay state hashes and scores.
10. Build the internal JSON report.
11. Review group/student/repository/URL metadata.
12. Validate JSON and confirm the email body contains JSON only.
13. Send through Gmail API to `rmisegal+uoh26b@gmail.com`.
14. Record the message ID and timestamp.
15. Archive the final configuration digest, code commit, logs, replays, report, and delivery receipt.
16. Keep public endpoints available for the required assessment/bonus period.

### Final evidence bundle

- Git commit identifier.
- Public GitHub URL.
- Cop MCP URL and Thief MCP URL.
- Sanitized configuration.
- Test summary.
- Six valid sub-game event logs.
- Replay verification summary.
- Canonical JSON report.
- Gmail message ID.
- Screenshots or recording of the GUI and remote endpoint status, if requested.

### Release gate

- Every Must requirement in `PRD.md` has evidence.
- No unresolved critical/high defect.
- No tracked secret.
- Gmail delivery is confirmed.

## 11. Phase 8 - Optional Q-learning hardening

### Objective

Improve strategic quality without destabilizing the compliant baseline.

### Tasks

1. Define separate state encodings for Cop and Thief observations.
2. Define role-specific action masks.
3. Implement Q-table initialization and update.
4. Handle terminal rewards without bootstrapping.
5. Add epsilon-greedy selection.
6. Make `alpha`, `gamma`, and epsilon schedule configurable.
7. Version and persist role-specific tables.
8. Prevent table sharing between agents unless explicitly permitted.
9. Compare against seeded random and heuristic baselines.
10. Visualize aggregate performance, not hidden per-turn state.
11. Keep a feature flag to revert to the baseline policy.

### Evaluation

- Fixed evaluation seeds separate from training seeds.
- Win rate and score by role.
- Illegal-action rate.
- Average moves to capture/survival.
- Stability across repeated runs.
- No regression in protocol, security, replay, or reporting tests.

### Exit gate

- Learning demonstrates measurable benefit or is disabled for release.
- Baseline compliance remains unchanged.

## 12. Phase 9 - Optional inter-group bonus

### Objective

Run a fair, mutually verifiable six-game series against another group's MCP agents.

### Preparation

1. Exchange GitHub URLs, MCP URLs, protocol versions, and authentication procedure.
2. Agree on schedule, config, seeds, observation policy, barrier interpretation, timeouts, and retry policy.
3. Verify all four endpoints independently.
4. Freeze both code versions and record commit IDs.
5. Agree on one report builder/schema version.

### Match execution

1. Run three games with Group A Cop versus Group B Thief.
2. Run three games with Group B Cop versus Group A Thief.
3. Exclude and replay technical failures.
4. Give both groups the same event/result artifacts.
5. Recalculate scores independently.
6. Resolve discrepancies before report generation.

### Reporting

1. Build the bonus JSON report.
2. Set `mutual_agreement` to `true` only after both groups approve the exact payload.
3. Apply bonus claim values: winner 10, loser 7, or draw 5 each.
4. Validate JSON-only formatting.
5. Send one mutually agreed report as instructed.

### Exit gate

- Six valid cross-group games exist.
- Both groups agree on scores and payload.
- The report contains all four MCP URLs and both GitHub URLs.

## 13. Cross-cutting test matrix

| Layer | Tests | Runs in CI | Requires network/secrets |
|---|---|---:|---:|
| Domain | Unit, property, exhaustive small-board | Yes | No |
| Observation | Leak and visibility tests | Yes | No |
| Policy | Prompt golden, parser, invalid output | Yes | No |
| MCP contracts | Schema, role, version, idempotency | Yes | No/local |
| Local integration | Two servers plus orchestrator | Yes where practical | No |
| GUI | Projection and smoke tests | Yes/headless | No |
| Replay | State-hash equivalence | Yes | No |
| Reports | JSON Schema and canonical serialization | Yes | No |
| Gmail | Fake adapter | Yes | No |
| Gmail live | OAuth/send smoke | Manual gated | Yes |
| Remote MCP | Auth, TLS, health, full series | Manual/release | Yes |
| Bonus | Four-endpoint interoperability | Manual | Yes |

## 14. Milestone-level definition of done

Every phase is complete only when:

- code and documentation are updated together;
- new external contracts have schemas and examples;
- tests cover success, failure, and boundary behavior;
- logs contain correlation IDs and no secrets;
- acceptance evidence is stored or linked;
- known issues are recorded with severity and owner; and
- the next phase does not need to reinterpret completed behavior.

## 15. Dependency order

```text
Requirements and decisions
    -> schemas/configuration
    -> deterministic engine
    -> observations and replay
    -> policy/model abstraction
    -> local MCP servers
    -> GUI/reporting/Gmail
    -> secure remote deployment
    -> release submission
    -> optional Q-learning and bonus competition
```

Q-learning can begin experimentally after the policy interface is stable, but it cannot replace the Phase 4 MCP gate.

## 16. Risk-driven checkpoints

### Checkpoint A - Rules

Before Phase 2, resolve observation, barrier, and scoring interpretations.

### Checkpoint B - Distributed correctness

Before GUI work dominates the schedule, prove six local games through two MCP servers.

### Checkpoint C - Credentials

Before final week, complete Gmail OAuth and remote endpoint authentication preflights.

### Checkpoint D - Remote stability

Before final submission, complete at least one full remote rehearsal and one failure-recovery rehearsal.

### Checkpoint E - Exact reporting

Before sending, validate the canonical JSON against schema and inspect the MIME body to ensure no prose is added.

## 17. Suggested issue breakdown

Use one issue per independently verifiable outcome. Suggested epics:

1. `EPIC-ENGINE` - rules, scoring, initialization, and invariants.
2. `EPIC-OBS` - partial observations and Dec-POMDP mapping.
3. `EPIC-SERIES` - six-game orchestration, technical failures, and replay.
4. `EPIC-POLICY` - prompts, parsing, providers, and optional Q-learning.
5. `EPIC-MCP-COP` - Cop server.
6. `EPIC-MCP-THIEF` - Thief server.
7. `EPIC-CLIENT` - MCP client and coordinator.
8. `EPIC-GUI` - live visualization and operator controls.
9. `EPIC-REPORT` - JSON schemas, Gmail API, and delivery receipt.
10. `EPIC-DEPLOY` - HTTPS, authentication, public URLs, and monitoring.
11. `EPIC-DOCS` - README, operational guide, and evidence mapping.
12. `EPIC-BONUS` - cross-group interoperability and report.

Each issue should identify its PRD requirement IDs, tests, configuration changes, and evidence artifact.

## 18. Primary release checklist

### Rules and series

- [ ] 5x5 default grid.
- [ ] Thief acts before Cop.
- [ ] Orthogonal movement only.
- [ ] Capture and survival terminal conditions correct.
- [ ] Cop barrier action and five-barrier maximum correct.
- [ ] Six valid games complete.
- [ ] Score matrix and totals correct.

### Architecture

- [ ] Separate Cop and Thief MCP processes.
- [ ] Separate MCP URLs.
- [ ] MCP client/orchestrator contains no strategic fallback.
- [ ] Natural-language prompts and structured actions used.
- [ ] Partial observations verified.

### Operations

- [ ] Local run succeeds.
- [ ] Remote HTTPS run succeeds.
- [ ] Authentication, rotation, and revocation tested.
- [ ] Technical failures replayed.
- [ ] Logs and replay artifacts verified.

### Product surface

- [ ] GUI accurately displays the live state.
- [ ] Headless CLI works.
- [ ] Configuration contains no hard-coded deployment secrets.

### Submission

- [ ] GitHub repository accessible.
- [ ] Scientific README complete.
- [ ] Internal JSON report validates.
- [ ] Email body is JSON only.
- [ ] Gmail API delivery confirmed.
- [ ] No secrets in repository or evidence bundle.

## 19. Mandatory GitHub phase workflow

### Repository destination

- Target GitHub repository: `https://github.com/areen-at/AI-agents-HW6`
- The local repository should use this URL as `origin` after the workspace Git metadata is valid.
- Codex performs routine status, staging, commit, and push operations for each completed phase.
- Ordinary phase pushes are pre-authorized and run automatically after the pre-push summary and safety checks.

### Required sequence after every phase

1. Run all tests and checks defined by that phase.
2. Run `git status` and inspect tracked, modified, deleted, and untracked paths.
3. Review the complete staged diff before committing.
4. Scan staged content and filenames for secrets, credentials, tokens, private reports, and generated junk.
5. Confirm `.gitignore` protects environment files, credentials, Python caches, virtual environments, OS junk, private JSON reports, and assignment PDFs.
6. Stage only files belonging to the completed phase.
7. Commit with a clear phase-specific message.
8. Re-run `git status` and identify anything intentionally left uncommitted or ignored.
9. Present a concise pre-push summary containing:
   - files changed;
   - files staged/committed;
   - relevant ignored files;
   - checks and tests run;
   - commit message; and
   - target branch and remote.
10. Present the informational pre-push summary.
11. Push the phase commit to GitHub without waiting for an additional confirmation.
12. Verify local and remote branch synchronization.
13. Report the pushed branch and commit identifier.

### Git safety rules

- Never stage or commit `.env` or `*.env` files except sanitized `*.example` templates.
- Never stage or commit API keys, authorization headers, OAuth tokens, refresh tokens, or MCP tokens.
- Never stage or commit `credentials.json`, client-secret downloads, private keys, or certificates.
- Never stage generated caches, virtual environments, compiled Python files, logs, or editor junk.
- Treat `reports/*.json` as private by default; commit only sanitized examples or schemas after inspection.
- Do not commit assignment PDFs unless the user explicitly authorizes the specific files.
- Do not use broad staging as a substitute for inspection; verify every staged path.
- Do not include unrelated user changes in a phase commit.
- Do not amend, rewrite, force-push, or delete history without explicit user authorization.
- Do not pause for approval on an ordinary phase push after the displayed summary.
- Continue to require explicit authorization for force-pushes, history rewrites, destructive Git operations, or a different remote/branch target.

### Commit-message convention

Use an imperative, phase-scoped message, for example:

```text
phase 3: implement game rules and scoring
```

Optional commit body:

```text
- add capture, survival, and barrier validation
- add small-board rule tests
- document phase verification commands
```

### Phase Git gate

A phase is not fully closed until its tests pass, its approved files are committed, the ordinary push succeeds, and local and remote branches are verified as synchronized. If a push fails, report the failure and keep the verified local commit intact for a safe retry.
