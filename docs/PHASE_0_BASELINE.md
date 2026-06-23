# Phase 0 Baseline: Repository Inspection and Decisions

## Status

- Phase: 0 - repository inspection and decisions
- Implementation code written: no
- Required mode: internal six-game Cop-versus-Thief series
- Optional mode: external-team bonus series
- Repository target: `https://github.com/areen-at/AI-agents-HW6`
- Default branch: `main`
- Decision status: polished and approved baseline for Phase 1 implementation

## 1. Repository inventory

### Tracked or phase-candidate files

| Path | Purpose | Phase 0 treatment |
|---|---|---|
| `.gitignore` | Secret, generated-file, report, PDF, and workspace exclusions | Extended and verified |
| `README.md` | GitHub repository landing page | Polished with scope, status, decisions, links, and Git workflow |
| `PRD.md` | Detailed product requirements | Reconciled with Phase 0 decisions and the heuristic/terminal baseline |
| `PLAN.md` | Phased delivery plan and Git workflow | Aligned so Phase 0 is inspection/decision closure only |
| `todo.md` | Executable task checklist | Phase 0 items marked complete |
| `docs/PHASE_0_BASELINE.md` | Phase 0 evidence and resolved decisions | Created |
| `docs/PHASE_0_VERIFICATION.md` | Repeatable Phase 0 closure evidence | Created during polish audit |

### Local-only paths

| Path | Observation | Git treatment |
|---|---|---|
| `.git/` | Newly initialized valid local Git metadata | Never committed |
| `.git.onedrive-placeholder/` | Preserved unusable OneDrive reparse placeholder that previously occupied `.git` | Ignored; not deleted |
| `.agents/` | Local agent/runtime metadata reparse directory | Ignored |
| `tmp/` | Temporary workspace directory | Ignored |

### Existing remote repository state

- Remote `origin` points to `https://github.com/areen-at/AI-agents-HW6.git`.
- Remote branch `origin/main` existed before Phase 0.
- Its current base commit is `07f70da` (`Initial commit`).
- The remote contained `.gitignore` and `README.md`.
- Local `main` was attached to this existing history without overwriting it.
- The existing `README.md` was restored and preserved.

## 2. Missing implementation components

No implementation existed at the Phase 0 baseline. The following remain for later phases:

- Python project metadata and dependency lock.
- `src/` application packages.
- Authoritative game engine.
- Configuration model and example configuration.
- Unit, contract, integration, and end-to-end tests.
- Cop heuristic policy.
- Thief heuristic policy.
- Partial-observation construction.
- Natural-language message and structured action contracts.
- Cop MCP server.
- Thief MCP server.
- Local MCP client/orchestrator.
- Terminal board visualization.
- Structured event logs and replay support.
- Internal JSON report generator.
- Gmail API adapter and OAuth setup.
- Remote deployment definitions and endpoints.
- External-team bonus mode.
- Optional test-only bonus opponent mock.
- Optional Q-learning extension.

Phase 0 intentionally implements none of these components.

## 3. Scope decisions

### Required part

The required product owns and implements:

1. one local authoritative game engine;
2. one local orchestrator/MCP client;
3. this group's Cop MCP server;
4. this group's Thief MCP server;
5. simple heuristic Cop and Thief policies;
6. terminal visualization;
7. event logging, replay, and internal JSON reporting;
8. deployment preparation for the two owned servers; and
9. Gmail API delivery of the final JSON-only report.

### Bonus part

- Bonus mode is optional and begins only after the required system passes.
- This repository will not implement a second production team.
- The other team provides real group metadata, repository URL, Cop MCP URL, and Thief MCP URL.
- Production bonus mode connects to those external endpoints.
- A deterministic opponent mock may exist only in clearly labeled test mode.
- Mock mode cannot send the production report or set `mutual_agreement` to `true`.

### Deferred work

- Q-learning is deferred until the complete required system works.
- A graphical GUI is deferred; a readable terminal board satisfies the baseline.
- Complex AI, search, or tournament functionality is outside the required critical path.

## 4. Game-rule decisions

### Coordinates

- Coordinates use zero-based `[row, column]` order.
- `[0, 0]` is the top-left cell.
- Rows increase downward.
- Columns increase to the right.
- Movement is orthogonal only: up, down, left, right.
- The same representation is used in configuration, contracts, events, replay, and reports.

### Initial state

- Cop and Thief positions are selected by a seeded random generator.
- Starting positions must be distinct.
- Starting positions must be in bounds and not blocked.
- The Thief acts first.

### Move-round counter

- One move round begins with the Thief action.
- If that action does not terminate the game, the Cop then acts.
- A completed non-terminal Thief/Cop cycle increments the round counter by one.
- If the Cop captures on the final allowed round, capture wins before survival is declared.
- No sub-game may continue beyond the configured 25-round default.

### Capture

- Capture occurs only when a valid Cop movement ends on the exact Thief cell.
- Adjacency is not capture.
- The engine, not an agent, determines capture and scoring.

### Barriers

- Only the Cop may place a barrier.
- Barrier placement replaces movement and consumes the complete Cop action.
- The target must be an orthogonally adjacent empty cell.
- The target cannot be outside the board, occupied by either player, or already blocked.
- Barriers are impassable to both roles.
- The default maximum is five barriers per sub-game.
- A placement is rejected if it would leave either player with no legal movement action, avoiding an undefined no-move state.

### Scoring

| Outcome | Cop | Thief |
|---|---:|---:|
| Cop captures Thief | 20 | 5 |
| Thief survives move limit | 5 | 10 |

- The per-game matrix is normative.
- Totals are calculated from immutable valid sub-game results.
- Invalid technical attempts contribute no score.

## 5. Partial-observation decision

The default observation policy is a configurable Manhattan-radius sensor:

- Default observation radius: `2` cells.
- Each agent always knows its own coordinate.
- An agent sees the opponent coordinate only when Manhattan distance is at most the radius.
- An agent sees barriers only in cells within that radius.
- An agent receives grid dimensions, current move round, and its legal action list.
- The Cop receives its remaining barrier budget.
- Agents may receive bounded summaries of their own prior observations and messages.
- Agents never receive the authoritative full state, hidden opponent coordinate, random-generator state, or future seeds.
- The terminal renderer may show full state to the human but is never used as agent input.

The radius remains configurable so assessors can change it without source edits.

## 6. Invalid actions and technical failures

### Invalid agent proposal

1. Validate the structured response schema.
2. Validate the proposal against the engine-provided legal action list.
3. If invalid, issue one bounded natural-language correction request using the same observation.
4. If the corrected response remains invalid, mark the attempt as a technical failure.
5. Never silently substitute an orchestrator-selected strategic action.

### Technical-failure examples

- MCP endpoint unavailable after bounded retries.
- Request timeout after bounded retries.
- Malformed response after the correction attempt.
- Repeated illegal action after the correction attempt.
- Protocol or role mismatch.
- Server crash or application invariant failure.

### Retry policy

- Invalid attempts do not count toward six valid games.
- Invalid attempts do not contribute scores.
- Every retry receives a new attempt ID.
- Default safety limit: ten technical attempts per valid sub-game slot.
- Exhausting the safety limit stops the series with an actionable error and preserves evidence.
- Gmail/report delivery failures do not rerun already valid games.

## 7. Internal report `sub_games` schema decision

Every valid internal `sub_games` entry will contain:

```json
{
  "sub_game_number": 1,
  "sub_game_id": "uuid",
  "attempt_id": "uuid",
  "seed": 1001,
  "started_at": "ISO-8601 timestamp",
  "ended_at": "ISO-8601 timestamp",
  "cop_server_url": "configured URL",
  "thief_server_url": "configured URL",
  "move_rounds": 12,
  "outcome": "cop_win",
  "terminal_reason": "capture",
  "scores": {
    "cop": 20,
    "thief": 5
  },
  "event_log_sha256": "hex digest"
}
```

Rules:

- Internal production reports contain exactly six entries.
- `sub_game_number` is 1 through 6 with no duplicate or gap.
- Timestamps use ISO 8601 with an explicit offset.
- URLs identify this group's role servers.
- Totals are calculated from the six `scores` objects.
- Technical attempts remain in audit logs but not in `sub_games`.

## 8. Proposed implementation structure

```text
.
|-- README.md
|-- PRD.md
|-- PLAN.md
|-- todo.md
|-- pyproject.toml
|-- config.json
|-- .env.example
|-- src/
|   |-- domain/
|   |-- application/
|   |-- contracts/
|   |-- agents/
|   |-- mcp_servers/
|   |-- reporting/
|   |-- infrastructure/
|   `-- ui/
|-- tests/
|   |-- unit/
|   |-- contract/
|   |-- integration/
|   |-- e2e/
|   `-- fixtures/
|-- reports/
|-- artifacts/
|-- docs/
`-- main.py
```

Boundary rules:

- `domain` owns rules and scoring.
- `application` owns series flow and technical recovery.
- `contracts` owns typed external schemas.
- `agents` owns simple role policies.
- `mcp_servers` exposes owned role services.
- `reporting` calculates and serializes reports.
- `infrastructure` owns configuration, persistence, Gmail, and network adapters.
- `ui` renders state but never mutates it.

## 9. Files protected from Phase 0 modification

- Existing README title was preserved and expanded into a Phase 0 project landing page; full operational instructions remain a later-phase deliverable.
- No source code exists to modify.
- No assignment PDF was copied or committed.
- No report JSON was generated or committed.
- No environment or credentials file was created.
- The unusable `.git` OneDrive placeholder was moved aside and ignored, not deleted.

## 10. Phase 0 commands and expected output

### Documentation checks

```powershell
Get-ChildItem -Force
rg --files -g "!.git/**"
```

Expected:

- planning documents, README, `.gitignore`, and this baseline document;
- no implementation source or test files yet;
- local-only runtime paths ignored by Git.

### Git checks

```powershell
git status --short
git remote -v
git log --oneline --decorate -5
```

Expected:

- `origin` points to `areen-at/AI-agents-HW6`;
- local `main` is based on existing `origin/main` history;
- only Phase 0 documentation and ignore changes are candidates for commit.

### Secret and junk checks

```powershell
git status --ignored --short
rg -n -i "api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|authorization:" --glob "!.git/**"
```

Expected:

- `.agents/`, `tmp/`, `.git.onedrive-placeholder/`, environments, credentials, tokens, private reports, and assignment PDFs are ignored as applicable;
- no actual secret values are found in staged content.

## 11. Phase 0 acceptance evidence

- Repository and remote history were inspected.
- Existing remote README was preserved.
- Missing implementation components were documented.
- Normal and bonus boundaries were fixed.
- Coordinate, observation, barrier, retry, and report-schema decisions were resolved.
- Proposed package structure was documented.
- No implementation code was created.
- `.gitignore` protects the required secret and generated-file categories.
- Phase-specific tests are documentation, Git, ignore, and secret checks only.
- PRD, plan, checklist, baseline evidence, and README now agree on required scope, bonus boundaries, heuristic-first policy, terminal visualization, and automatic ordinary pushes.

## 12. Next phase

Phase 1 may establish Python tooling, the directory skeleton, validated configuration, and secret-safe examples. No Phase 1 implementation begins until the polished Phase 0 is committed and automatically pushed under the required Git workflow.
