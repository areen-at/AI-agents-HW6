# AI Agents HW6 - Dual MCP Cop and Thief

This repository will implement a two-agent Cop-and-Thief game in which our Cop and Thief operate through separate MCP servers. A local authoritative engine keeps the true game state, sends each agent a partial natural-language observation, validates the returned structured action, and produces auditable JSON results.

## Current status

Phase 7 is complete. The repository now contains the polished Phase 1 foundation, Phase 2 immutable domain model, Phase 3 authoritative game rules, Phase 4 engine-only series control, Phase 5 heuristic agents, Phase 6 observations/protocol, and Phase 7 independent Cop/Thief local decision servers.

The next authorized implementation phase is Phase 8: local MCP orchestrator and required run.

## Required baseline

- Default `5 x 5` board.
- Six valid sub-games per internal series.
- At most 25 move rounds per sub-game.
- Exact-cell Cop capture.
- Thief victory by surviving the move limit.
- Cop-only barriers, with a maximum of five per sub-game.
- Configurable rules and scoring; no hard-coded assignment parameters.
- Simple heuristic Cop and Thief policies before any Q-learning.
- Separate Cop and Thief MCP servers.
- Natural-language observations plus schema-validated actions.
- Readable terminal visualization.
- Structured logs, replay evidence, and an internal JSON report.
- Gmail API delivery of a JSON-only final report.

## Bonus boundary

The optional bonus mode will not build a second production team. It will connect our existing Cop and Thief services to another real class team's external MCP URLs:

- games 1-3: our Cop versus opponent Thief;
- games 4-6: opponent Cop versus our Thief.

An opponent mock may be used only in explicit test mode. Real opponent data will never be invented, and `mutual_agreement` remains `false` until both teams approve the same canonical bonus report.

## Phase 0 decisions

- Coordinates are zero-based `[row, column]`, with `[0, 0]` at the top-left.
- The Thief acts first in every move round.
- Starting positions are distinct and seeded.
- The default partial-observation radius is Manhattan distance `2`.
- Cop barriers target adjacent orthogonal empty cells.
- A barrier cannot leave either player without a legal movement action.
- One invalid-action correction is allowed; a second failure invalidates the attempt.
- Up to ten technical attempts are allowed per valid game slot by default.
- Heuristic policies are the baseline; graphical GUI, model-backed policy, and Q-learning are optional later work.

## Documentation

- [Product requirements](PRD.md)
- [Phased delivery plan](PLAN.md)
- [Executable task checklist](todo.md)
- [Phase 0 baseline and decision evidence](docs/PHASE_0_BASELINE.md)
- [Phase 0 closure verification](docs/PHASE_0_VERIFICATION.md)
- [Phase 1 foundation evidence](docs/PHASE_1_FOUNDATION.md)
- [Phase 2 domain model evidence](docs/PHASE_2_DOMAIN_MODEL.md)
- [Phase 3 game rules evidence](docs/PHASE_3_GAME_RULES.md)
- [Phase 4 series/replay/report evidence](docs/PHASE_4_SERIES_REPLAY_REPORT.md)
- [Phase 5 heuristic agents evidence](docs/PHASE_5_HEURISTIC_AGENTS.md)
- [Phase 6 observation/protocol evidence](docs/PHASE_6_OBSERVATION_PROTOCOL.md)
- [Phase 7 MCP server evidence](docs/PHASE_7_MCP_SERVERS.md)

## Phase 1 validation commands

The Codex workspace uses a bundled Python executable. On a normal development machine, replace that full path with python after installing Python 3.10 or newer.

Commands:

- python main.py --mode internal --config config.json
- python main.py --mode bonus-mock --config config.json
- python main.py --mode bonus --config config.json
- $env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'
- python -m compileall -q main.py src tests

Expected:

- internal and bonus-mock config validation pass;
- bonus mode rejects placeholder opponent data until a real class team is configured;
- all unit tests pass, including malformed JSON, URL, logging-level, and blank-student validation;
- bytecode compilation succeeds.

## Phase 2 domain validation

The Phase 2 unit suite adds coverage for immutable domain objects, seeded initialization, state
invariants, and domain-layer dependency boundaries.

Expected:

- 23 total unit tests pass;
- same-seed initialization is reproducible;
- initialized games start with distinct positions, empty barriers, and Thief active;
- invalid state construction is rejected; and
- the domain package imports no MCP, UI, Gmail, provider, reporting, or infrastructure modules.

## Phase 3 rules validation

The Phase 3 unit suite adds coverage for legal actions, invalid-action rejection, turn switching,
capture, survival, Cop barriers, scoring, deterministic replay, `2 x 2` exhaustive sanity, and
progressive grid sanity.

Expected:

- 42 total unit tests pass;
- invalid actions raise `DomainError` without mutating the original immutable state;
- capture and survival terminal outcomes use the documented precedence;
- default scores are `20/5` for Cop capture and `5/10` for Thief survival; and
- barriers are adjacent, Cop-only, bounded by the max count, impassable, and cannot trap either
  player.

## Phase 4 engine-only validation

Phase 4 adds an engine-only internal smoke command:

- python main.py --mode internal --config config.json --engine-only

Expected:

- six valid sub-games complete;
- technical failures are replaced in tests without becoming strategic losses;
- event logs and internal reports are written atomically;
- replay verification checks final state hashes; and
- 49 total unit tests pass.

## Phase 5 heuristic validation

Phase 5 makes the engine-only run use simple heuristic agents by default:

- python main.py --mode internal --config config.json --engine-only --policy heuristic
- python main.py --mode internal --config config.json --engine-only --policy first-legal

Expected:

- six valid sub-games complete with the heuristic policy;
- Cop pursues visible Thief positions and places only useful legal barriers;
- Thief returns only movement actions and prefers safer escape moves;
- every heuristic output is validated against engine legal actions; and
- 60 total unit tests pass.

## Phase 6 observation/protocol validation

Phase 6 makes the heuristic path use the same observation and JSON-response contract planned for
MCP:

- python main.py --mode internal --config config.json --engine-only --policy heuristic

Expected:

- observations expose only role-allowed visible information;
- prompts instruct one JSON object with no prose;
- strict parser rejects malformed, oversized, mismatched, unknown, and illegal actions;
- one repair is allowed before technical-failure classification; and
- 73 total unit tests pass.

## Phase 7 server validation

Phase 7 adds local role server entry points:

- python -m ai_agents_hw6.mcp_servers.http_server --role cop --host 127.0.0.1 --port 8001
- python -m ai_agents_hw6.mcp_servers.http_server --role thief --host 127.0.0.1 --port 8002

Expected:

- Cop and Thief expose separate health, identity, capabilities, and decision operations;
- each server rejects role/protocol/request mismatches;
- optional bearer-token authentication is supported;
- stopping one local server does not stop the other; and
- 82 total unit tests pass.

## Git workflow

After every completed phase, Codex will:

1. run the phase tests and checks;
2. inspect Git status and the staged diff;
3. verify ignore rules and scan for secrets or generated junk;
4. commit only the phase files with a clear message;
5. show an informational pre-push summary;
6. push automatically to `origin/main`; and
7. verify local and remote synchronization.

Ordinary phase pushes are pre-authorized. Force-pushes, history rewrites, destructive Git operations, or a different target still require explicit authorization.

## Security

The repository must never contain real `.env` files, API keys, MCP tokens, OAuth tokens, downloaded credential files, private keys, private report data, virtual environments, caches, or assignment PDFs unless a specific exception is explicitly approved.
