# Product Requirements Document: Dual AI Agent Conversation via MCP Servers

## 1. Document control

| Field | Value |
|---|---|
| Product | Dual AI Agent Cop-and-Thief Race via MCP Servers |
| Assignment | Exercise 06 / Lesson L09 |
| Source specification | `ex06-Dual AI agent race via MCP servers.pdf`, version 1.0, 2026-06-19 |
| Product document status | Phase 0 baseline approved; deferred deployment choices are tracked in Section 19 |
| Primary audience | Student development team, reviewers, course assessor, and operators |
| Default timezone | `Asia/Jerusalem` |

## 2. Purpose

Build a reproducible multi-agent system in which two autonomous AI agents play a partially observable Cop-and-Thief game. One agent acts as the Cop and the other as the Thief. Each agent must make decisions independently through natural-language interactions exposed by its own Model Context Protocol (MCP) server.

The product is not merely a board-game simulation. Its principal learning objective is to demonstrate a complete distributed-agent architecture:

1. deterministic game rules and authoritative state management;
2. two isolated agent services with separate MCP endpoints;
3. natural-language decision requests and structured tool responses;
4. local and remote execution;
5. secure access to public MCP endpoints;
6. terminal visual observability and machine-readable logs;
7. simple heuristic policies first, with optional adaptive strategy later;
8. automated JSON reporting through Gmail API; and
9. a scientifically grounded Dec-POMDP description.

## 3. Goals

### 3.1 Primary goals

- Implement a correct, deterministic, testable Cop-and-Thief game engine.
- Run a complete series of six valid sub-games, each capped at 25 moves.
- Host the Cop and Thief as two independent MCP servers with distinct URLs.
- Make each action decision through the MCP/agent decision path rather than a hard-coded game policy in the orchestrator.
- support local development and secure remote deployment.
- Display the live game and results in a readable terminal interface.
- Persist enough structured evidence to replay and audit every valid game.
- Email the exact required JSON report through Gmail API.
- Publish an appropriately documented GitHub repository.

### 3.2 Secondary goals

- Improve agent behavior over repeated play using a lightweight Q-learning mechanism.
- Support an inter-group bonus series without changing the core engine.
- Make game rules, scoring, endpoints, and operational values configurable.
- Provide clear failure recovery so technical faults do not contaminate competitive results.

### 3.3 Non-goals

- Training a foundation model.
- Building a general-purpose tournament platform.
- Implementing a large-scale or computationally expensive reinforcement-learning stack.
- Giving either agent direct access to hidden authoritative state.
- Allowing the terminal UI, optional GUI, email layer, or remote deployment mechanism to determine game outcomes.
- Replacing MCP communication with direct in-process policy calls in the final system.
- Requiring a graphical desktop UI for baseline compliance.
- Requiring an external LLM or Q-learning before the heuristic baseline works.

## 4. Stakeholders and users

| Stakeholder | Need |
|---|---|
| Student development team | Clear interfaces, phased implementation, reproducible tests, and low-friction local operation |
| Course assessor | Evidence that all game, MCP, deployment, terminal visualization, reporting, and documentation requirements are satisfied |
| Game operator | A simple way to configure, launch, monitor, stop, resume, and report a six-game series |
| Opposing group | Stable public MCP URLs, authentication instructions, compatible protocol contracts, and mutually verifiable results |
| System maintainer | Structured logs, health checks, secret isolation, and deterministic replay artifacts |

## 5. Definitions

| Term | Definition |
|---|---|
| Game / series | The complete required run containing six valid sub-games |
| Sub-game | One Cop-versus-Thief episode, limited to 25 move rounds |
| Move round | One ordered decision cycle in which the Thief acts first and the Cop acts second, unless the game ends after the Thief action |
| Valid sub-game | A sub-game completed under game rules without a disqualifying technical failure |
| Technical loss/failure | A run invalidated by infrastructure or software failure; it must be replayed and does not count toward the six valid games |
| Authoritative engine | The only component allowed to validate actions, mutate game state, determine terminal conditions, and calculate scores |
| Agent | The autonomous Cop or Thief decision-maker |
| MCP server | A role-specific service exposing the agent's tools/resources/prompts through MCP |
| Orchestrator/client | The component that owns series flow, requests agent decisions, invokes the engine, and records results |
| Observation | The role-appropriate partial view delivered to one agent for one decision |
| Barrier | A blocked grid cell placed by the Cop as an action, impassable to both roles |
| Internal report | JSON report for a group's own Cop and Thief run |
| Bonus report | Joint JSON report for an inter-group bonus series |

## 6. Product principles

1. **The engine is authoritative.** Agents propose actions; the engine validates and applies them.
2. **Agents are isolated.** The Cop and Thief run behind separate MCP servers and never share memory directly.
3. **Hidden state stays hidden.** Each agent receives only its permitted observation.
4. **Natural language is part of the protocol.** Decisions are requested through human-readable role prompts, with structured outputs for reliable execution.
5. **Everything important is replayable.** Seeds, configurations, observations, actions, outcomes, and errors are recorded.
6. **Technical faults do not become game strategy.** Invalid technical runs are excluded and replayed.
7. **Secrets never enter source control or reports.** OAuth credentials, tokens, API keys, and MCP authentication secrets are externalized.
8. **Configuration beats hard-coding.** All assignment-level parameters must come from a configuration file.

## 7. End-to-end user journey

1. The operator prepares configuration and secrets.
2. The operator starts the Cop MCP server and Thief MCP server.
3. The orchestrator verifies server health, authentication, protocol compatibility, and role identity.
4. The operator starts a series through the CLI; an optional future GUI may call the same application service.
5. The engine initializes a seeded board, agent positions, and empty barrier set.
6. For each move round, the orchestrator sends the current permitted observation to the Thief MCP server.
7. The Thief returns a structured action derived from its decision process.
8. The engine validates and applies the action, then checks the terminal condition.
9. If play continues, the orchestrator sends the Cop's permitted observation to the Cop MCP server.
10. The Cop returns either a movement action or a barrier-placement action.
11. The engine validates and applies it, checks capture and move limits, updates the terminal view, and writes an event record.
12. At sub-game end, the engine computes role scores and records the outcome.
13. Technical failures are marked invalid and replayed with a new attempt identifier until six valid sub-games exist.
14. At series end, the system builds and validates the required JSON report.
15. The operator reviews the summary and authorizes or triggers Gmail delivery.
16. The Gmail integration sends a JSON-only message body to the required address.

## 8. Functional requirements

### 8.1 Game engine

#### FR-GAME-001: Board

- The default board is a two-dimensional `5 x 5` grid.
- Coordinates must use one documented, consistent convention.
- Grid dimensions must be configurable through `grid_size`.
- The engine must reject out-of-bounds movement and placement.

#### FR-GAME-002: Initial state

- The Cop and Thief must be placed in valid initial cells using a seeded random generator.
- Initial positions must not be blocked by barriers.
- Initial placement collision behavior must be explicitly configured and tested; the recommended default is distinct cells.
- The seed and resolved initial state must be logged.

#### FR-GAME-003: Turn order

- The Thief acts first in every move round.
- The Cop acts second if the Thief's action did not end the sub-game.
- Each role may perform at most one action on its turn.
- The orchestrator must never request or apply actions concurrently within one sub-game.

#### FR-GAME-004: Movement

- Movement is orthogonal: up, down, left, or right.
- Diagonal movement is prohibited.
- Staying in place is prohibited unless explicitly approved as a configured extension; it is not part of the baseline assignment.
- An agent cannot move outside the board or onto a barrier.
- Invalid actions must not mutate state.

#### FR-GAME-005: Cop capture

- The Cop wins immediately when the Cop occupies the same cell as the Thief after a valid Cop movement.
- Capture determination belongs exclusively to the authoritative engine.
- A capture must emit a terminal event and no later action may be applied.

#### FR-GAME-006: Thief survival

- The Thief wins by surviving the configured maximum of 25 move rounds without capture.
- `max_moves` must default to `25` and be configurable.
- The exact counter semantics must be documented in code and tests: a round is counted after the ordered Thief/Cop cycle, except when a terminal result occurs earlier.

#### FR-GAME-007: Barriers

- The Cop may place a barrier instead of moving.
- Barrier placement consumes the Cop's action for that turn.
- A barrier must be placed in a valid, unoccupied, unblocked cell allowed by the documented placement rule.
- Barriers are impassable to both Cop and Thief.
- A maximum of five Cop-placed barriers is allowed per sub-game by default.
- `max_barriers` must default to `5` and be configurable.
- The engine must reject placement on either player's current cell, on an existing barrier, or outside the permitted placement range.
- A barrier target must be an orthogonally adjacent empty cell.
- A placement must be rejected when it would leave either player with no legal movement action, avoiding an undefined no-move state.

#### FR-GAME-008: Terminal precedence

- Capture takes precedence over survival-limit completion if both could be evaluated on the final round.
- Once terminal, state is immutable except for metadata finalization.
- Every terminal outcome must have a reason code.

#### FR-GAME-009: Series

- A normal series contains exactly six valid sub-games.
- `num_games` must default to `6` and be configurable for development tests.
- Attempts invalidated by technical failure do not increment the valid-game count.
- Each sub-game and attempt must have unique identifiers.

### 8.2 Scoring

#### FR-SCORE-001: Per-game score matrix

| Outcome | Cop score | Thief score |
|---|---:|---:|
| Cop wins by capture | 20 | 5 |
| Thief wins by survival | 5 | 10 |

- The score matrix must be configurable under `scoring`.
- Scores must be computed by the engine from the terminal result, never supplied by an agent.
- Reports must include per-sub-game scores and aggregate totals.

#### FR-SCORE-002: Aggregate interpretation

- The per-game matrix is the normative scoring source.
- A role-balanced inter-group series assigns each group three Cop games and three Thief games, producing an assignment-stated theoretical group range of 30 to 90 before bonus scoring.
- Internal reports must aggregate Cop and Thief role totals exactly from recorded sub-games.
- The assignment's sample internal totals are illustrative and must not override calculated totals.

### 8.3 Partial observability and Dec-POMDP

#### FR-OBS-001: Observation isolation

- The engine must create a separate observation for each role.
- MCP agents must not receive the engine's full mutable state object.
- Observations must contain only fields allowed by a documented visibility policy.
- Logs may retain authoritative state for audit, but agent-facing traces must clearly distinguish observations from ground truth.

#### FR-OBS-002: Visibility policy

- The visibility rule must be configurable and described in the README's Dec-POMDP formulation.
- The assignment does not prescribe a precise observation radius or sensor model; this is an explicit pre-implementation decision in Section 19.
- Tests must prove that hidden fields cannot leak through prompts, tool outputs, errors, or UI-to-agent coupling.

#### FR-OBS-003: Formal model

The README must define the game as a Decentralized Partially Observable Markov Decision Process:

`<n, S, {A_i}, P, R, {Omega_i}, O, gamma>`

It must map:

- `n` to the two agents;
- `S` to positions, barriers, turn, counters, and terminal status;
- `{A_i}` to role-specific movement and barrier actions;
- `P` to deterministic or seeded transition behavior;
- `R` to the scoring/reward scheme;
- `{Omega_i}` to each role's observation space;
- `O` to the observation function; and
- `gamma` to the selected discount factor if Q-learning is enabled.

### 8.4 MCP architecture

#### FR-MCP-001: Independent servers

- The Cop and Thief must run as two separate MCP servers.
- Each server must have its own process, role configuration, health state, authentication context, and URL.
- A single server multiplexing both roles is non-compliant for the final deployment.

#### FR-MCP-002: Client/orchestrator separation

- The orchestrator is an MCP client and game coordinator, not an agent policy.
- It may prepare observations, request decisions, validate schemas, invoke the engine, and record results.
- It must not choose strategic moves on behalf of a healthy agent.

#### FR-MCP-003: Natural-language decision flow

- Each role server must accept a role-specific natural-language decision request.
- The request must explain objective, legal action vocabulary, observation, relevant history, and output schema.
- The response must be machine-parseable and include exactly one proposed action plus optional bounded rationale/metadata.
- The system must validate responses against a strict schema before engine execution.
- Free-form text alone is insufficient for action execution.

#### FR-MCP-004: Tools and resources

At minimum, each MCP server must expose:

- a health/capabilities operation;
- a role identity operation;
- a decision operation;
- protocol/version information; and
- optional policy state import/export operations when learning is enabled.

The exact MCP primitives may be tools, resources, and/or prompts, but contracts must be documented and independently testable.

#### FR-MCP-005: Timeout and retry

- Every MCP call must have a configurable timeout.
- Retry must be bounded and safe; an action cannot be applied twice.
- Requests require correlation identifiers and idempotency protection.
- Exhausted retries produce a technical-failure event, not a strategic loss.

#### FR-MCP-006: Compatibility

- Both servers and the client must advertise a protocol/schema version.
- A series must fail fast before game start when versions are incompatible.
- Public bonus endpoints must include connection and authentication instructions without disclosing secrets.

### 8.5 Language model integration

#### FR-LLM-001: Optional model deployment approaches

The required baseline uses simple deterministic or seeded heuristic policies behind the same MCP decision contract. If a model-backed policy is added later, the design may support one of these approaches:

1. **External API:** an LLM provider API called by or through the MCP agent service.
2. **Exposed local Ollama:** a local Ollama service securely published through ngrok, Localtonet, Nginx, or an equivalent gateway.
3. **Hybrid, recommended:** Ollama remains local to the orchestrator/client host, while only the MCP servers are remotely exposed; communication uses outbound calls.

#### FR-LLM-002: Policy and optional provider abstraction

- Agent decision code must depend on a policy interface rather than one vendor SDK.
- Any optional model, endpoint, timeout, temperature, and credentials must be configurable.
- A deterministic test provider must exist for automated tests.

#### FR-LLM-003: Safety and validation

- Policy/model output is untrusted input.
- Invalid schema, illegal actions, prompt injection content, or excessive output must be rejected.
- A bounded repair request may be attempted before declaring technical failure.
- Secrets and hidden state must not appear in prompts.

### 8.6 Optional Q-learning

#### FR-RL-001: Status

- Q-learning is recommended for competitive behavior but is not mandatory for baseline functional compliance.
- Enabling or disabling it must not change game rules or MCP contracts.

#### FR-RL-002: Q-table

- The default suggested representation is a tabular state-action value table.
- The implementation must define state encoding, available actions, learning rate `alpha`, discount factor `gamma`, and exploration rate `epsilon`.
- The update rule is:

  `Q(s,a) <- Q(s,a) + alpha * [r + gamma * max_a' Q(s',a') - Q(s,a)]`

- Terminal updates must not bootstrap from a future state.
- Policy persistence must be versioned and role-specific.
- Learning artifacts must not leak hidden observations between agents.

### 8.7 Terminal visualization and CLI

#### FR-UI-001: Terminal visualization

The terminal interface must display during play:

- the grid;
- Cop and Thief positions;
- barriers;
- active role and move counter;
- legal/selected action where appropriate;
- current sub-game and series progress;
- per-role scores;
- terminal outcome;
- MCP connection/health state; and
- technical failure/retry state.

The terminal renderer is read-only and must not mutate authoritative game state directly.

A graphical GUI is optional after all baseline requirements pass. If implemented, it must consume the same application events and must not duplicate game rules.

#### FR-UI-002: Operator controls

- Start a configured series.
- Pause/resume between safe state transitions.
- Stop a run cleanly.
- Inspect configuration and endpoint status.
- View the final report before sending.
- Re-run a technical failure when automatic recovery is disabled.

#### FR-UI-003: CLI

- All core functions must remain accessible headlessly.
- CI and remote execution must not require a graphical display.
- CLI and any optional GUI must use the same application services and engine.

### 8.8 Configuration

#### FR-CONFIG-001: Required configuration file

- Use one documented `config.yaml` or `config.json` as the primary non-secret configuration source.
- Configuration must be schema-validated at startup.
- Invalid or missing required values must fail fast with actionable errors.
- Environment variables may override deployment-specific values.

#### FR-CONFIG-002: Required defaults

| Key | Default |
|---|---:|
| `grid_size` | `[5, 5]` |
| `max_moves` | `25` |
| `num_games` | `6` |
| `max_barriers` | `5` |
| `scoring.cop_win` | `20` |
| `scoring.thief_win` | `10` |
| `scoring.cop_loss` | `5` |
| `scoring.thief_loss` | `5` |
| `timezone` | `Asia/Jerusalem` |

Configuration must additionally cover seeds, observation policy, MCP endpoints, timeouts, retry limits, authentication mode, optional model provider, terminal refresh, logging, reporting recipient, and optional learning parameters.

#### FR-CONFIG-003: Secret management

- MCP tokens, provider API keys, Gmail OAuth credentials, and refresh tokens must not be stored in committed configuration.
- Provide `.env.example` or equivalent names-only documentation.
- Log redaction must be automatic.

### 8.9 Local and remote deployment

#### FR-DEPLOY-001: Local stage

- Both MCP servers, orchestrator, engine, and terminal interface must run locally first.
- Local health and complete six-game execution must pass before remote deployment.
- Local development may use separate localhost ports.

#### FR-DEPLOY-002: Remote stage

- Both MCP servers must be deployed or exposed through publicly reachable HTTPS endpoints.
- The Cop and Thief must use separate public URLs.
- Prefect Cloud is an acceptable example, not the only permitted host.
- Public endpoints must remain usable by an authorized external client for the assessment/bonus window.

#### FR-DEPLOY-003: Network access

- Remote servers must not rely on inbound access to a private localhost-only LLM unless a secure tunnel/gateway is deliberately configured.
- The preferred hybrid design uses outbound calls from reachable components to the model integration.
- Firewall, proxy, TLS termination, and tunnel requirements must be documented.

#### FR-DEPLOY-004: Authentication

- Remote MCP endpoints require token-based authentication or an equivalently strong mechanism.
- Tokens must be revocable and rotatable.
- Authentication failures must not expose server internals.
- Transport must use HTTPS outside local development.

### 8.10 Logging, replay, and technical failures

#### FR-LOG-001: Event log

Every attempt must produce append-only structured events containing:

- series, sub-game, attempt, request, and correlation identifiers;
- timestamp and timezone;
- configuration digest and code version;
- seed;
- authoritative state hash;
- role observation hash or redacted observation;
- MCP request/response metadata;
- proposed action and validation result;
- applied action and resulting state hash;
- score changes;
- terminal reason; and
- technical error details with secrets removed.

#### FR-LOG-002: Replay

- A valid sub-game must be reproducible from configuration, seed, and accepted action sequence.
- Replay must not call live models or MCP servers.
- Replay output must verify state hashes and final score.

#### FR-LOG-003: Technical-failure policy

- Infrastructure faults, server unavailability, exhausted timeouts, unrecoverable malformed responses, and application crashes are technical failures.
- A technical failure invalidates that attempt.
- Invalid attempts must not contribute scores or count toward six valid sub-games.
- The orchestrator must continue/retry until six valid sub-games finish or a configured safety limit requires operator intervention.
- Technical failure records remain in audit logs.

### 8.11 Gmail API reporting

#### FR-REPORT-001: Recipient and transport

- Send the final report through Gmail API to `rmisegal+uoh26b@gmail.com`.
- Use OAuth credentials and token handling consistent with the supplied Google API setup guide.
- Gmail authentication must be testable before a competitive run.

#### FR-REPORT-002: JSON-only message

- The email body must contain only the required JSON document.
- Do not add greetings, Markdown fences, signatures, explanations, or free text.
- JSON must be schema-validated immediately before sending.
- A canonical copy and the Gmail message identifier must be stored locally.

#### FR-REPORT-003: Internal report schema

The internal report must contain at least:

```json
{
  "group_name": "Team-Alpha",
  "students": [],
  "github_repo": "https://github.com/team-alpha/marl-cop-thief",
  "cop_mcp_url": "https://cop-mcp-alpha.example",
  "thief_mcp_url": "https://thief-mcp-alpha.example",
  "timezone": "Asia/Jerusalem",
  "sub_games": [],
  "totals": {
    "cop": 0,
    "thief": 0
  }
}
```

Each `sub_games` entry must be formally specified by the implementation schema and include identifiers, attempt number, seed, start/end timestamps, move count, outcome, terminal reason, role scores, and an integrity reference to the event log.

#### FR-REPORT-004: Bonus report schema

The inter-group bonus report must contain at least:

```json
{
  "report_type": "bonus_game",
  "groups": {
    "group_1": "Team-Alpha",
    "group_2": "Team-Beta"
  },
  "github_repo_group_1": "https://github.com/team-alpha/marl-cop-thief",
  "github_repo_group_2": "https://github.com/team-beta/marl-cop-thief",
  "mcp_url_group_1_cop": "https://cop-mcp-alpha.example",
  "mcp_url_group_1_thief": "https://thief-mcp-alpha.example",
  "mcp_url_group_2_cop": "https://cop-mcp-beta.example",
  "mcp_url_group_2_thief": "https://thief-mcp-beta.example",
  "timezone": "Asia/Jerusalem",
  "students_group_1": [],
  "students_group_2": [],
  "sub_games": [],
  "totals_by_group": {
    "Team-Alpha": 0,
    "Team-Beta": 0
  },
  "bonus_claim": {
    "Team-Alpha": 0,
    "Team-Beta": 0
  },
  "mutual_agreement": true
}
```

### 8.12 GitHub and scientific README

#### FR-DOC-001: Repository

- Publish the completed project in a GitHub repository accessible to the assessor.
- Do not commit secrets, local tokens, or private logs.
- Include installation, configuration, local execution, remote deployment, testing, and report-generation instructions.

#### FR-DOC-002: README scientific content

The README must include:

- problem statement and architecture;
- formal Dec-POMDP tuple and mapping;
- state, action, transition, reward, observation, and discount definitions;
- partial-observation rationale;
- MCP server/client boundaries;
- natural-language decision protocol;
- Q-learning design if implemented;
- configuration reference;
- terminal/CLI usage and optional GUI usage if implemented;
- local and remote deployment;
- authentication and secret handling;
- technical-failure semantics;
- report schema and Gmail workflow;
- testing evidence and known limitations; and
- exact public MCP URLs during the required availability window.

## 9. Inter-group bonus requirements

### 9.1 Eligibility and schedule

- The bonus series is optional and occurs after the primary submission.
- The assignment describes a one-week window after publication/submission.
- Both groups must agree on scheduling, versions, authentication, and report content.

### 9.2 Match structure

- Run six valid sub-games.
- In three games, Group A's Cop plays Group B's Thief.
- In three games, Group B's Cop plays Group A's Thief.
- Technical failures are replayed under the same validity policy.
- Both groups must receive the same final result data and agree to one bonus JSON report.

### 9.3 Bonus score

- Winner: `10` bonus points.
- Loser: `7` bonus points.
- Draw: `5` bonus points for each group.
- The assignment describes the final bonus as the average over valid bonus series where applicable.
- Missing mutual agreement invalidates the bonus and awards zero bonus points to both sides for that disputed series.

## 10. Non-functional requirements

### 10.1 Correctness

- All state changes must pass engine validation.
- Scoring must be derived from immutable terminal records.
- Automated tests must cover all boundary and terminal cases.

### 10.2 Reliability

- A single MCP timeout must not crash the process.
- Partial report writes must be atomic.
- Resume must never duplicate an applied action or sent email.

### 10.3 Performance

- Terminal state updates should appear promptly after an action is committed locally.
- Orchestrator overhead excluding model latency should remain below 500 ms per action under normal local conditions.
- Timeout values must accommodate remote model/MCP latency and remain configurable.

### 10.4 Security

- TLS for all public traffic.
- Token authentication for public MCP endpoints.
- Least-privilege Gmail scopes.
- No secret values in Git, terminal UI, optional GUI, reports, prompts, or logs.
- Dependency and configuration checks before deployment.

### 10.5 Maintainability

- Separate domain, application, infrastructure, UI, and reporting layers.
- Typed schemas at every external boundary.
- Role-neutral shared code where behavior is identical; role-specific policy code where necessary.
- No game-rule duplication in UI or agents.

### 10.6 Portability

- Support Windows PowerShell for local development.
- Keep core execution cross-platform where dependencies permit.
- Headless operation must work without a display server.

### 10.7 Accessibility and usability

- Do not rely on color alone to distinguish Cop, Thief, barriers, and errors.
- Show textual status and scores.
- Controls must disable invalid transitions.

## 11. Proposed logical architecture

```text
Terminal UI / CLI
    |
Application Orchestrator (MCP client, series controller)
    |                         |
    |                         +--> Report Builder --> Gmail API
    |
    +--> Authoritative Game Engine --> Event Store / Replay
    |
    +--> Cop MCP Client  ----HTTPS----> Cop MCP Server --> Policy/LLM/Q-table
    |
    +--> Thief MCP Client ----HTTPS---> Thief MCP Server --> Policy/LLM/Q-table
```

### 11.1 Boundary rules

- Engine contains rules and scoring only.
- Orchestrator contains workflow and resilience only.
- MCP servers contain decision policy only.
- Optional LLM provider adapters contain vendor/network details only.
- Terminal UI renders application state and sends operator commands only.
- Gmail adapter sends an already validated report only.

## 12. Core data contracts

### 12.1 Action

```json
{
  "protocol_version": "1.0",
  "request_id": "uuid",
  "role": "cop",
  "action": {
    "type": "move",
    "direction": "up"
  },
  "policy_metadata": {
    "provider": "deterministic-test",
    "model": "test"
  }
}
```

Cop barrier action:

```json
{
  "type": "place_barrier",
  "target": [2, 3]
}
```

### 12.2 Observation

```json
{
  "protocol_version": "1.0",
  "series_id": "uuid",
  "sub_game_id": "uuid",
  "attempt_id": "uuid",
  "role": "thief",
  "move_round": 4,
  "grid_size": [5, 5],
  "self_position": [1, 2],
  "visible_cells": [],
  "visible_opponent": null,
  "visible_barriers": [],
  "legal_action_types": ["move"],
  "history_summary": []
}
```

The final fields depend on the approved observation policy.

### 12.3 Terminal result

```json
{
  "outcome": "cop_win",
  "reason": "capture",
  "move_rounds": 12,
  "scores": {
    "cop": 20,
    "thief": 5
  }
}
```

## 13. Test strategy and acceptance suite

### 13.1 Progressive sanity checks

| Stage | Grid | Purpose | Gate |
|---:|---|---|---|
| 1 | `2 x 2` | Basic algorithm, pipeline, transition, and observation correctness | All exhaustive state/action tests pass |
| 2 | `3 x 2` / `3 x 3` | Synchronization, turn order, and simple strategy behavior | No illegal or duplicate transitions |
| 3 | `4 x 3` / `4 x 4` | Partial observation, exploration, and initial Q-learning behavior | Deterministic replay and convergence smoke checks pass |
| 4 | `5 x 5` | Final test run, terminal visualization, report, and full six-game series | Release acceptance passes |

### 13.2 Required automated test categories

- Unit tests for every rule and scoring branch.
- Property tests for board bounds and state invariants.
- Observation-leak tests.
- MCP schema and role-identity contract tests.
- Timeout, retry, duplicate-request, and idempotency tests.
- Local two-server integration tests.
- Remote endpoint authentication and availability tests.
- Terminal rendering tests against application state.
- Deterministic replay tests.
- JSON schema and canonical serialization tests.
- Gmail adapter tests with a fake transport, followed by one authorized live smoke test.
- Full six-valid-game end-to-end test.

### 13.3 Release acceptance criteria

The baseline release is accepted only when:

1. all mandatory requirements in this PRD are implemented;
2. six valid 5x5 sub-games complete automatically;
3. technical-failure attempts are excluded and replayed;
4. the two agents use separate MCP servers and separate URLs;
5. agent decisions traverse the natural-language MCP decision path;
6. public endpoints are authenticated and reachable;
7. the terminal visualization accurately mirrors authoritative state;
8. replay reproduces all final states and scores;
9. the internal JSON report validates and contains no prose;
10. Gmail API delivery succeeds to the required recipient;
11. the GitHub README contains the complete scientific and operational documentation; and
12. no credentials or tokens are present in tracked files.

## 14. Observability and operational metrics

Track at minimum:

- valid and invalid attempt counts;
- action latency by role and component;
- model/MCP timeout and retry counts;
- malformed and illegal action counts;
- game duration and move count;
- win/loss counts and scores by role;
- barrier placements and rejected placements;
- endpoint health and authentication failures;
- replay verification success; and
- report build/send status.

## 15. Error taxonomy

| Category | Example | Treatment |
|---|---|---|
| Strategic illegal proposal | Agent requests out-of-bounds move | Bounded correction path; if unrecoverable, follow approved invalid-action policy |
| Protocol error | Missing action field | Repair request, then technical failure if exhausted |
| Infrastructure failure | MCP server unavailable | Retry, then invalidate and replay attempt |
| Authentication failure | Expired MCP token | Stop new attempts, rotate token, resume |
| Engine invariant failure | Two active turns | Abort attempt, preserve evidence, fail release test |
| Reporting failure | Gmail API unavailable | Preserve validated report and retry idempotently; do not rerun games |

One correction request is allowed for a repeated but syntactically valid illegal agent action; a second failure invalidates the attempt as a technical failure and must never be silently converted into a legal move.

## 16. Requirement priority

### Must

- Correct game engine and scoring.
- Six valid sub-games.
- Two separate MCP servers and URLs.
- Natural-language decision flow and strict structured actions.
- Local and remote execution.
- Authentication and secure secret handling.
- Terminal visualization and headless CLI.
- Config file and no hard-coded assignment parameters.
- JSON audit/reporting and Gmail API delivery.
- GitHub repository and scientific README.
- Technical-failure replay semantics.

### Should

- Optional Q-table learning after baseline completion.
- Optional graphical GUI after baseline completion.
- Deterministic replay with integrity hashes.
- Automated remote deployment and endpoint probes.
- Pause/resume and crash-safe checkpoints.

### Could

- Multiple LLM provider adapters.
- Tournament dashboard.
- Policy comparison analytics.
- Bonus-series automation.

## 17. Requirement traceability matrix

| Source requirement | PRD coverage | Primary acceptance evidence |
|---|---|---|
| Cop/Thief game on 5x5 grid | Sections 8.1-8.2 | Engine tests and six-game artifact |
| 25 moves, six games, barriers | Sections 8.1 and 8.8 | Config and boundary tests |
| Partial observability / Dec-POMDP | Sections 8.3 and 8.12 | Observation tests and README |
| Separate MCP servers | Section 8.4 | Two process/URL integration test |
| Natural-language communication | Section 8.4.3 | Captured MCP decision trace |
| LLM access alternatives | Section 8.5 | Deployment documentation |
| Q-learning recommendation | Section 8.6 | Optional policy tests/artifact |
| Terminal visualization | Section 8.7 | Terminal rendering acceptance test |
| Remote cloud publication | Section 8.9 | HTTPS endpoint probes |
| Authentication | Sections 8.9 and 10.4 | Unauthorized/authorized tests |
| JSON reports | Section 8.11 | Schema validation |
| Gmail API | Section 8.11 | Gmail message ID and stored payload |
| Configuration file | Section 8.8 | Startup schema tests |
| README / scientific model | Section 8.12 | Documentation review |
| Progressive testing | Section 13.1 | Stage-gate results |
| Bonus competition | Section 9 | Joint validated bonus JSON |

## 18. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM produces illegal or malformed actions | Invalid play or stalled run | Strict schema, legal-action context, bounded repair, deterministic test provider |
| Hidden state leaks through prompts/logs | Violates partial observability | Observation DTOs, leak tests, redaction, separate agent contexts |
| Remote MCP instability | Incomplete series | Health gates, bounded retries, technical-failure replay, checkpointing |
| Duplicate requests apply twice | Corrupt game state | Correlation IDs, idempotency keys, engine transition versioning |
| Public endpoint abuse | Cost/security incident | HTTPS, scoped tokens, rate limits, rotation, audit logs |
| Gmail OAuth expires or is misconfigured | Submission failure | Preflight, least-privilege token refresh, fake adapter tests, preserved payload |
| Assignment ambiguity causes incompatible behavior | Assessment risk | Resolve Section 19 before implementation gates and document final decisions |
| Q-learning expands scope | Schedule risk | Keep optional and behind a policy interface |
| Visualization diverges from engine | Misleading evidence | Read-only event-driven projection and state-hash checks |

## 19. Phase 0 decision register

The detailed rationale and exact baseline contracts are recorded in `docs/PHASE_0_BASELINE.md`.

| ID | Decision | Status | Phase 0 resolution |
|---|---|---|---|
| OD-01 | Exact partial-observation sensor model | Closed | Configurable Manhattan radius, default `2`; explicit opponent/barrier visibility; never full-state by default |
| OD-02 | Barrier placement and no-move state | Closed | Adjacent orthogonal empty cell; reject placement leaving either player without a legal movement action |
| OD-03 | Initial Cop/Thief collision behavior | Closed | Require distinct seeded positions |
| OD-04 | Repeated schema-valid but illegal action | Closed | One correction request, then technical failure; never invent a fallback action |
| OD-05 | Exact internal `sub_games` object | Closed | Use the auditable schema in the Phase 0 baseline and validate it with JSON Schema |
| OD-06 | Aggregate-score example inconsistency | Closed | Treat the per-game score matrix as normative and calculate totals from valid terminal events |
| OD-07 | Final cloud/tunnel provider | Deferred, non-blocking | Select in deployment preparation based on available account, HTTPS, stable URLs, and token support |
| OD-08 | Baseline decision provider | Closed | Use simple heuristic Cop/Thief policies; model-backed policies and Q-learning are optional after baseline completion |

## 20. Definition of done

The product is done when the release acceptance criteria in Section 13.3 pass, all Must requirements have linked evidence, all blocking decisions are reflected in configuration/documentation, deferred deployment choices are closed before their phase, the report has been delivered successfully, and the repository contains no secrets or unresolved critical defects.
