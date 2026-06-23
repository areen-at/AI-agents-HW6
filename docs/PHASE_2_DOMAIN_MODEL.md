# Phase 2 Domain Model Verification

## Result

PASS - Phase 2 core domain model is complete. The repository now has immutable value objects,
authoritative state snapshots, seeded initialization, and invariant tests. Full game transitions,
scoring application, observations, MCP, reporting, Gmail, deployment, bonus orchestration, and
Q-learning remain intentionally outside this phase.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/domain/enums.py` | Role, direction, action, terminal, and technical-failure enumerations |
| `src/ai_agents_hw6/domain/errors.py` | Shared domain invariant exception |
| `src/ai_agents_hw6/domain/geometry.py` | Immutable coordinates, grid size, direction deltas, and bounded neighbors |
| `src/ai_agents_hw6/domain/identifiers.py` | UUID-backed series, sub-game, attempt, and request identifiers |
| `src/ai_agents_hw6/domain/state.py` | Immutable authoritative `GameState` snapshot and invariant checks |
| `src/ai_agents_hw6/domain/initialization.py` | Deterministic seeded initial placement |
| `src/ai_agents_hw6/domain/__init__.py` | Public domain exports |
| `tests/unit/test_domain_model.py` | Phase 2 domain tests |
| `README.md` | Updated current status and validation notes |
| `todo.md` | Phase 2 tasks and gate marked complete |

## Implemented domain foundation

- `Role.COP` and `Role.THIEF`.
- Orthogonal `Direction` values: up, down, left, and right.
- `ActionType.MOVE` and `ActionType.PLACE_BARRIER`.
- Terminal outcomes and terminal reasons for capture and move-limit survival.
- Technical-failure reason codes for timeout, unavailable server, malformed response, illegal action
  after repair, protocol mismatch, server crash, and application error.
- Immutable `Coordinate` using zero-based `[row, column]` convention.
- Immutable `GridSize` with minimum `2 x 2` validation.
- Coordinate and grid JSON serialization helpers.
- Direction-to-delta conversion.
- Bounded orthogonal neighbor generation for corners, edges, and interior cells.
- UUID-backed `SeriesId`, `SubGameId`, `AttemptId`, and `RequestId`.
- Immutable authoritative `GameState` with:
  - grid;
  - Cop and Thief positions;
  - immutable barrier set;
  - active role;
  - move round;
  - barrier count;
  - seed;
  - terminal outcome; and
  - terminal reason.
- Deterministic seeded initial placement with distinct Cop/Thief cells.
- Initial state starts with empty barriers, zero counters, and Thief active.

## Invariants enforced

- Coordinates cannot be negative.
- Grid dimensions must be at least `2 x 2`.
- Player positions must be inside the board.
- Barriers must be inside the board.
- Barriers cannot overlap the Cop or Thief.
- Barriers are normalized to an immutable `frozenset`.
- Duplicate barriers are rejected.
- Move round and barrier counters must be non-negative integers.
- Barrier counter cannot be less than the number of current barriers.
- Active role must be a `Role`.
- Terminal outcome and terminal reason must be set together.
- Seed must be an integer.

## Commands run

Codex bundled runtime:

- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus-mock --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus --config config.json`
- `$env:PYTHONPATH='src'; C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p 'test_*.py'`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall -q main.py src tests`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip check`

## Expected output

- Internal config validation passes.
- Bonus-mock config validation passes.
- Real bonus mode exits with status `2` because placeholder opponent data is intentionally rejected.
- Unit tests report `Ran 23 tests` and `OK`.
- Bytecode compilation exits successfully.
- Dependency check reports no broken requirements.

## Test coverage

The Phase 2 tests verify:

- enum protocol values;
- coordinate serialization and immutability;
- invalid coordinate values;
- grid corners, edges, interiors, and out-of-bounds checks;
- grid serialization and validation;
- direction deltas;
- bounded neighbor generation;
- UUID identifier validation;
- same-seed initialization reproducibility;
- distinct seeded starting positions;
- empty barriers and Thief-active initial state;
- barrier collection immutability;
- invalid positions and barriers;
- negative counters;
- invalid active role;
- terminal metadata consistency; and
- no imports from later layers into the domain package.

## Phase 3 boundary

Phase 3 may implement legal actions, transition rules, capture, survival, Cop barrier placement,
scoring, and small-board exhaustive checks. Phase 2 intentionally provides only the immutable
domain foundation those rules will operate on.
