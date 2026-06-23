# Phase 7 Independent Cop and Thief MCP Server Verification

## Result

PASS - Phase 7 independent role decision servers are complete. The project now has dedicated Cop and
Thief server entry points, role identity, health/capabilities/version operations, a natural-language
decision operation, role/request/protocol validation, optional bearer-token authentication, duplicate
request rejection, bounded timeout handling, and tests proving that stopping one local server does
not stop the other.

The Phase 7 transport is intentionally stdlib-only JSON-over-HTTP. No external FastMCP dependency is
introduced yet. The server contract is isolated behind `mcp_servers` so Phase 8 can add the local MCP
client/orchestrator and a later deployment phase can swap or wrap the transport with FastMCP if the
course environment requires that exact package.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/mcp_servers/protocol.py` | Shared protocol version, capabilities, and dependency note |
| `src/ai_agents_hw6/mcp_servers/service.py` | Role decision service with health, identity, capabilities, and decide operations |
| `src/ai_agents_hw6/mcp_servers/http_server.py` | Lightweight stdlib JSON HTTP server transport |
| `src/ai_agents_hw6/mcp_servers/cop_server.py` | Dedicated Cop server entry point |
| `src/ai_agents_hw6/mcp_servers/thief_server.py` | Dedicated Thief server entry point |
| `src/ai_agents_hw6/mcp_servers/__init__.py` | Public server exports |
| `src/ai_agents_hw6/contracts/actions.py` | Public action-payload parser for request deserialization |
| `src/ai_agents_hw6/contracts/observation.py` | Public observation deserialization from JSON |
| `src/ai_agents_hw6/contracts/__init__.py` | Public deserialization exports |
| `tests/unit/test_mcp_servers.py` | Role service and local HTTP server tests |
| `README.md` | Updated status and Phase 7 validation summary |
| `todo.md` | Phase 7 tasks and gate marked complete |

## Dependency decision

- External FastMCP package: not installed in Phase 7.
- Runtime dependency change: none.
- Transport used for this phase: Python stdlib `ThreadingHTTPServer`.
- Rationale: keep the baseline installable, deterministic, and dependency-light while preserving a
  clean role-service seam for Phase 8 client work and later FastMCP/cloud wrapping if required.

## Implemented operations

Each role server exposes:

- `GET /health`
- `GET /identity`
- `GET /capabilities`
- `POST /decide`

The in-process service exposes the same logical operations for unit tests and later client adapters.

## Implemented validation

- Shared protocol version is `1.0`.
- Cop server identity is fixed to `cop`.
- Thief server identity is fixed to `thief`.
- Decision requests require:
  - `protocol_version`;
  - `request_id`;
  - `correlation_id`;
  - matching server role; and
  - role-specific observation payload.
- Observation role, request ID, and protocol version must match the request.
- Duplicate request IDs are rejected.
- Protocol mismatch is rejected.
- Role mismatch is rejected.
- Malformed observations are rejected.
- Optional bearer-token authentication rejects missing or invalid credentials.
- Decision timeout path is present and tested.
- Server decision uses the Phase 6 observation/prompt/JSON-response/parser contract.
- The public HTTP response removes internal Python action objects and returns JSON only.
- Servers receive observations only and cannot mutate authoritative `GameState`.

## Entry points

Local role server modules:

```powershell
python -m ai_agents_hw6.mcp_servers.cop_server
python -m ai_agents_hw6.mcp_servers.thief_server
```

Generic role server module:

```powershell
python -m ai_agents_hw6.mcp_servers.http_server --role cop --host 127.0.0.1 --port 8001
python -m ai_agents_hw6.mcp_servers.http_server --role thief --host 127.0.0.1 --port 8002
```

## Commands run

Codex bundled runtime:

- `$env:PYTHONPATH='src'; C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p 'test_*.py'`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall -q main.py src tests`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --engine-only --policy heuristic`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json --engine-only --policy first-legal`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode internal --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus-mock --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe main.py --mode bonus --config config.json`
- `C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip check`

## Expected output

- Unit tests report `Ran 82 tests` and `OK`.
- Bytecode compilation exits successfully.
- Engine-only heuristic run still completes six valid games.
- Engine-only first-legal run still completes six valid games.
- Internal and bonus-mock config validation pass.
- Real bonus mode exits with status `2` because placeholder opponent data is intentionally rejected.
- Dependency check reports no broken requirements.

## Test coverage

The Phase 7 tests verify:

- health responses;
- identity responses;
- capabilities and protocol version;
- valid Cop decision request;
- valid Thief decision request;
- malformed observation rejection;
- missing request ID rejection;
- duplicate request ID rejection;
- role mismatch rejection;
- protocol mismatch rejection;
- optional bearer-token auth rejection and success;
- timeout error path;
- service cannot mutate authoritative game state;
- public response excludes internal action object;
- two local HTTP servers can run independently; and
- stopping one server does not stop the other.

## Phase 8 boundary

Phase 8 may implement the local client/orchestrator that connects to these two server endpoints,
performs preflight checks, requests decisions in turn order, validates responses, and completes six
valid games exclusively through the server boundary.
