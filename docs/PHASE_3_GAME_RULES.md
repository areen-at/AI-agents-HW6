# Phase 3 Game Rules, Scoring, and Small-Board Verification

## Result

PASS - Phase 3 authoritative game rules, scoring, and small-board checks are complete. The domain
layer can now generate legal actions, reject invalid actions without mutation, apply valid
transitions, detect terminal outcomes, enforce Cop barriers, calculate configured scores, and replay
deterministic action streams.

MCP, observations, natural-language prompts, series orchestration, event persistence, reporting,
Gmail, deployment, bonus orchestration, and Q-learning remain intentionally outside this phase.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/domain/actions.py` | Immutable typed move and barrier actions |
| `src/ai_agents_hw6/domain/rules.py` | Legal-action generation, validation, transitions, terminal logic, and replay |
| `src/ai_agents_hw6/domain/scoring.py` | Score matrix and terminal-state score lookup |
| `src/ai_agents_hw6/domain/__init__.py` | Public exports for Phase 3 domain APIs |
| `tests/unit/test_game_rules.py` | Movement, turn, capture, survival, barrier, scoring, replay, and grid sanity tests |
| `README.md` | Updated project status and Phase 3 validation summary |
| `todo.md` | Phase 3 tasks and gate marked complete |

## Implemented rules

- Legal Cop movement generation.
- Legal Thief movement generation.
- Rejection of out-of-bounds moves.
- Rejection of movement onto barriers.
- Unsupported stay and diagonal moves remain unrepresentable by the action vocabulary.
- Invalid actions raise `DomainError` before any new state is returned.
- Thief-first turn order is enforced by active-role validation.
- Non-terminal Thief movement switches the active role to Cop.
- Non-terminal Cop movement switches the active role to Thief and increments the move round.
- Exact-cell Cop capture is detected after valid Cop movement.
- Terminal states reject all further actions.
- Thief survival is declared when the configured move limit is reached after the Cop action.
- Capture takes precedence over survival-limit completion on the final round.
- Only the Cop may place barriers.
- Barrier placement consumes the Cop turn and increments the move round.
- Barriers must target adjacent orthogonal empty cells.
- Barriers cannot be placed on players, existing barriers, non-adjacent cells, or out-of-bounds cells.
- The configured maximum barrier count is enforced, defaulting to five.
- Barrier placement is rejected if it would leave either player with no legal movement action.
- Barriers are impassable to both roles.
- Scores are calculated from immutable terminal outcomes using a configured score matrix.
- Caller or agent-supplied scores are ignored because score calculation has no score-input field.
- Deterministic replay applies a role/action sequence from an initial state.

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
- Unit tests report `Ran 42 tests` and `OK`.
- Bytecode compilation exits successfully.
- Dependency check reports no broken requirements.

## Test coverage

The Phase 3 tests verify:

- legal Cop and Thief moves;
- out-of-bounds rejection;
- barrier collision rejection;
- invalid actions do not mutate the original state;
- stay and diagonal moves are not in the supported action vocabulary;
- Thief-first turn order;
- role switching after valid non-terminal actions;
- capture on exact-cell Cop movement;
- terminal-state immutability;
- Thief survival at configured move limit;
- capture precedence on the final move;
- Cop-only barrier placement;
- barrier turn consumption;
- barrier placement rejection on player, existing barrier, non-adjacent target, and trapping target;
- maximum barrier count;
- barriers impassable to both roles;
- default score matrix values `20/5` for Cop capture and `5/10` for Thief survival;
- score matrix construction from loaded config;
- non-terminal states cannot be scored;
- deterministic replay of the same action stream;
- exhaustive `2 x 2` legal-action sanity; and
- progressive `3 x 2`, `3 x 3`, `4 x 3`, `4 x 4`, and `5 x 5` sanity checks.

## Phase 4 boundary

Phase 4 may build the series controller, valid-game slots, technical-failure attempt replacement,
append-only events, replay persistence, and internal report skeleton. Phase 3 intentionally stops at
single-attempt domain rules and deterministic in-memory replay.
