# Phase 5 Simple Heuristic Agents Verification

## Result

PASS - Phase 5 simple heuristic agents are complete. The project now has a role-scoped policy
interface, a deterministic Cop pursuit/barrier heuristic, a deterministic Thief escape heuristic,
an adapter from engine state to policy input, and engine-only six-game runs using the heuristic
provider.

Q-learning, expensive search, MCP transport, natural-language prompts, formal partial-observation
DTOs, Gmail delivery, deployment, and bonus orchestration remain intentionally outside this phase.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/agents/policy.py` | Role-scoped `PolicyInput` DTO and `Policy` protocol |
| `src/ai_agents_hw6/agents/heuristic.py` | Deterministic Cop/Thief heuristic policy |
| `src/ai_agents_hw6/agents/adapter.py` | Engine-state-to-policy-input adapter and heuristic provider |
| `src/ai_agents_hw6/agents/__init__.py` | Public agent exports |
| `src/ai_agents_hw6/application/series.py` | Engine-only policy selection and heuristic provider integration |
| `src/ai_agents_hw6/application/__init__.py` | Public series helper export |
| `src/ai_agents_hw6/cli.py` | `--policy heuristic|first-legal` option for engine-only runs |
| `main.py` | Engine-only policy selection output |
| `tests/unit/test_heuristic_agents.py` | Heuristic policy and six-game tests |
| `README.md` | Updated status and Phase 5 validation summary |
| `todo.md` | Phase 5 tasks and gate marked complete |

## Implemented policy interface

- Policies receive `PolicyInput`, not raw authoritative `GameState`.
- `PolicyInput` contains:
  - role;
  - self position;
  - visible opponent estimate, or `None`;
  - visible barriers;
  - grid size;
  - current legal actions;
  - move round; and
  - seed.
- Policy output is exactly one typed domain action.
- Legal actions are included in the input and every heuristic result is tested against engine legal
  actions.

## Cop heuristic

- If the Thief is adjacent and capture is legal, capture immediately.
- Otherwise, evaluate legal Cop barriers.
- A barrier is considered useful when it reduces the visible Thief's immediate legal movement
  degree.
- Useful barriers are chosen deterministically by:
  1. largest mobility reduction;
  2. closest barrier target to the visible Thief;
  3. lowest row;
  4. lowest column.
- If no useful barrier exists or barrier limit is reached, choose the legal move that minimizes
  Manhattan distance to the visible Thief.
- Movement ties are deterministic: up, right, down, left.
- If the opponent is not visible, choose the deterministic first legal action.

## Thief heuristic

- The Thief only returns movement actions.
- If the Cop is visible, choose the legal move that maximizes Manhattan distance from the Cop.
- If distance ties, prefer the move with more next-step movement options, reducing trap risk.
- Remaining ties are deterministic: up, right, down, left.
- If the Cop is not visible, choose the deterministic first legal movement action.
- If no legal movement exists, raise `DomainError`; the application layer can treat that as a
  technical failure.

## Commands run

Codex bundled runtime:

- `$env:PYTHONPATH='src'; C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p 'test_*.py'`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --engine-only --policy heuristic`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --engine-only --policy first-legal`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus-mock --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall -q main.py src tests`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip check`

## Expected output

- Unit tests report `Ran 60 tests` and `OK`.
- Engine-only heuristic run completes six valid sub-games.
- Engine-only first-legal run remains available for deterministic smoke tests.
- Internal and bonus-mock config validation pass.
- Real bonus mode exits with status `2` because placeholder opponent data is intentionally rejected.
- Bytecode compilation exits successfully.
- Dependency check reports no broken requirements.

## Test coverage

The Phase 5 tests verify:

- Cop pursuit in an open grid.
- Cop useful-barrier selection.
- Cop capture preference over barrier placement.
- Cop fallback to movement when the barrier limit is reached.
- Thief escape in an open grid.
- Thief avoidance of more trapped escape options.
- Thief never emits a barrier action.
- No-visible-opponent deterministic tie-breaking.
- No-legal-action failure behavior.
- Every heuristic output is accepted by engine legal-action validation across progressive grids.
- Six valid engine-only games run with the heuristic provider.

## Phase 6 boundary

Phase 6 may implement the formal partial-observation DTO and natural-language decision protocol.
Phase 5 intentionally uses a simple adapter that can see the current engine state only to construct
the smaller role-scoped `PolicyInput`.
