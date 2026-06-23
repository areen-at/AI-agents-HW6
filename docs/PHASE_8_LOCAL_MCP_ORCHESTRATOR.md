# Phase 8 Local MCP Orchestrator and Required Run Verification

## Result

PASS - Phase 8 local MCP orchestration is complete. The project can now connect to configured local
Cop and Thief decision server URLs, run role/version/capability preflight, keep authoritative game
state local, request decisions through the server boundary in Thief-then-Cop order, validate and
apply responses exactly once, replace technical-failure attempts, replay completed games, render a
readable series summary, and write the internal report.

Remote deployment, full terminal board visualization, Gmail delivery, bonus orchestration, and
Q-learning remain intentionally outside this phase.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/application/mcp_client.py` | Local HTTP/MCP-style clients, preflight, decision provider, and local MCP series runner |
| `src/ai_agents_hw6/application/__init__.py` | Public local MCP orchestration exports |
| `src/ai_agents_hw6/cli.py` | `--local-mcp` run option |
| `main.py` | Local MCP run wiring and report writing |
| `src/ai_agents_hw6/mcp_servers/http_server.py` | Supports configured `/mcp/...` URL prefix |
| `src/ai_agents_hw6/ui/summary.py` | Read-only human-readable series summary |
| `src/ai_agents_hw6/ui/__init__.py` | Public summary renderer export |
| `tests/unit/test_local_mcp_orchestrator.py` | Local client, preflight, fault, replacement, and full-series tests |
| `tests/unit/test_mcp_servers.py` | `/mcp` prefix regression coverage |
| `README.md` | Updated status and Phase 8 validation summary |
| `todo.md` | Phase 8 tasks and gate marked complete |

## Implemented local MCP orchestration

- Reads Cop and Thief server URLs from `config.json`.
- Reads optional tokens from environment variables:
  - `COP_MCP_TOKEN`
  - `THIEF_MCP_TOKEN`
- Creates separate clients for owned Cop and Thief servers.
- Runs preflight before series start:
  - health;
  - identity;
  - protocol version;
  - capabilities; and
  - decision operation presence.
- Refuses to start when either server is missing, wrong-role, wrong-version, or missing required
  capability.
- Keeps authoritative game state local.
- Sends a Thief observation first whenever the active role is Thief.
- Validates and applies Thief responses through the engine.
- Checks terminal state before contacting Cop.
- Sends Cop observations only when play continues.
- Validates and applies Cop responses through the engine.
- Repeats until terminal.
- Does not choose strategic fallback moves in the orchestrator.
- Generates one request ID and one correlation ID per decision.
- Reuses the same request payload for bounded safe retry.
- Applies each accepted response at most once.
- Rejects duplicate response request IDs.
- Turns exhausted local MCP failures into invalid attempts.
- Replaces invalid attempts until six valid games complete or the safety limit is reached.
- Writes the internal report after a successful run.

## Commands

Start local role servers:

```powershell
$env:PYTHONPATH='src'
python -m ai_agents_hw6.mcp_servers.http_server --role cop --host 127.0.0.1 --port 8001
python -m ai_agents_hw6.mcp_servers.http_server --role thief --host 127.0.0.1 --port 8002
```

Run the local MCP series:

```powershell
python main.py --mode internal --config config.json --local-mcp
```

## Commands run

Codex bundled runtime:

- `$env:PYTHONPATH='src'; C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p 'test_*.py'`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall -q main.py src tests`
- local Cop server start on `127.0.0.1:8001`
- local Thief server start on `127.0.0.1:8002`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --local-mcp`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --engine-only --policy heuristic`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --engine-only --policy first-legal`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus-mock --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip check`

## Expected output

- Unit tests report `Ran 90 tests` and `OK`.
- Local MCP run completes six valid games through configured server URLs.
- Local MCP run prints a readable series summary with each game result and aggregate totals.
- Local MCP run writes `reports/internal_game_report.json`.
- Engine-only heuristic and first-legal runs still complete six valid games.
- Internal and bonus-mock config validation pass.
- Real bonus mode exits with status `2` because placeholder opponent data is intentionally rejected.
- Bytecode compilation exits successfully.
- Dependency check reports no broken requirements.

## Generated local artifacts

The local MCP smoke command generated ignored runtime artifacts:

- `reports/internal_game_report.json`
- `artifacts/logs/engine_only_events.json`

These remain protected by `.gitignore` and were not staged.

## Test coverage

The Phase 8 tests verify:

- preflight accepts healthy role servers;
- preflight rejects missing servers;
- preflight rejects wrong-role identity;
- Thief decision path contacts the Thief server first;
- Cop and Thief clients are separate;
- exhausted local MCP failures become invalid attempts;
- replacement attempts complete the series;
- malformed responses become technical failures;
- duplicate responses are rejected;
- `/mcp` URL prefix works with configured URLs;
- six valid games complete through two local role servers;
- replay verification remains active through the existing series controller; and
- human-readable series summary includes game results and totals.

## Phase 9 boundary

Phase 9 may replace the simple series summary with a full terminal board visualization and richer
operational logging. Phase 8 intentionally keeps rendering minimal and read-only.
