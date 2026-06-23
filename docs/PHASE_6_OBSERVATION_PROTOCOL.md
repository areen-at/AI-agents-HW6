# Phase 6 Partial Observations and Natural-Language Protocol Verification

## Result

PASS - Phase 6 partial observations and natural-language protocol are complete. The project now has
immutable role observations, Manhattan-radius visibility, role-specific prompts, strict JSON action
response parsing, legal-action validation, bounded repair semantics, leak tests, and a heuristic
adapter that uses the same observation/response contract planned for MCP.

MCP transport, server processes, authentication, remote deployment, Gmail delivery, bonus
orchestration, and Q-learning remain intentionally outside this phase.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/contracts/observation.py` | Immutable role-specific observation DTO and visibility function |
| `src/ai_agents_hw6/contracts/prompt.py` | Cop/Thief natural-language decision prompt rendering |
| `src/ai_agents_hw6/contracts/actions.py` | Strict JSON action response parser and repair classification |
| `src/ai_agents_hw6/contracts/__init__.py` | Public protocol exports |
| `src/ai_agents_hw6/agents/adapter.py` | Heuristic observation/protocol adapter |
| `src/ai_agents_hw6/agents/__init__.py` | Public protocol-aware agent exports |
| `src/ai_agents_hw6/application/series.py` | Engine-only heuristic path now goes through observation/JSON/parser contract |
| `tests/unit/test_observation_protocol.py` | Visibility, prompt, parser, repair, leak, and protocol-adapter tests |
| `README.md` | Updated status and Phase 6 validation summary |
| `todo.md` | Phase 6 tasks and gate marked complete |

## Implemented observations

- Role-specific `Observation` DTO is immutable.
- Observation includes own position.
- Observation includes grid size, move round, move limit, barrier count, barrier limit, legal actions,
  and bounded history summary.
- Observation includes only visible barriers within the configured Manhattan radius.
- Observation includes opponent position only when the opponent is within the configured Manhattan
  radius.
- Observation excludes hidden authoritative fields such as both true positions, terminal internals,
  full barrier list, state hash, score, and event log details.
- Public JSON serialization is separated from authoritative state serialization.

## Implemented natural-language protocol

- Cop and Thief prompts are role-specific.
- Prompts state the role objective in plain language.
- Prompts include current public observation JSON.
- Prompts describe permitted action vocabulary.
- Prompts require exactly one JSON object and no surrounding prose.
- Cop schema allows movement or barrier placement.
- Thief schema allows movement only.
- Prompt tests verify hidden coordinates do not leak when outside observation radius.

## Implemented action-response parsing

- Response must be valid JSON.
- Response must be a JSON object.
- Response must not exceed the configured size cap.
- Response must contain only approved top-level fields.
- Response must include matching `protocol_version`, `request_id`, and `role`.
- Unknown action types are rejected.
- Move responses require exactly `type` and `direction`.
- Barrier responses require exactly `type` and `target`.
- Thief barrier responses are rejected.
- Proposed actions must appear in the observation's legal action list.
- One repair request is allowed; the second failure is classified as technical failure.

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

- Unit tests report `Ran 73 tests` and `OK`.
- Engine-only heuristic run completes six valid games through the observation/JSON/parser adapter.
- Engine-only first-legal run remains available for deterministic smoke tests.
- Internal and bonus-mock config validation pass.
- Real bonus mode exits with status `2` because placeholder opponent data is intentionally rejected.
- Bytecode compilation exits successfully.
- Dependency check reports no broken requirements.

## Test coverage

The Phase 6 tests verify:

- role-specific observation construction;
- hidden opponent suppression outside radius;
- visible opponent inclusion inside radius;
- visible-barrier filtering;
- observation immutability;
- public observation JSON does not leak hidden coordinates;
- role-specific prompt text;
- JSON-only response instruction;
- bounded history inclusion;
- valid move parsing;
- valid Cop barrier parsing;
- malformed, oversized, unknown, mismatched, and extra-field rejection;
- legal-action validation;
- Thief barrier rejection;
- one-repair-then-technical-failure classification;
- heuristic adapter response round-trip through parser; and
- six-game engine-only series through the protocol adapter.

## Phase 7 boundary

Phase 7 may expose this protocol through independent Cop and Thief MCP servers. Phase 6 intentionally
stops at local in-process protocol contracts and does not start server processes or network
transport.
