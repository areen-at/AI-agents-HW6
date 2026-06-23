# AI Agents HW6 - Dual MCP Cop and Thief

This repository will implement a two-agent Cop-and-Thief game in which our Cop and Thief operate through separate MCP servers. A local authoritative engine keeps the true game state, sends each agent a partial natural-language observation, validates the returned structured action, and produces auditable JSON results.

## Current status

Phase 2 is complete. The repository now contains the polished Phase 1 foundation plus a pure domain model with immutable coordinates, grid sizes, identifiers, authoritative state snapshots, seeded initialization, and invariant tests.

The next authorized implementation phase is Phase 3: game rules, scoring, and small-board checks.

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
