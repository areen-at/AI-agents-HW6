# Phase 9 Terminal Visualization and Operational Logging

## Result

PASS - Phase 9 is complete. Live runs can render every committed authoritative state in a
terminal-first, no-color-required view; CI can use quiet mode; operators can emit redacted JSON
lines; and recorded state snapshots can be replayed without contacting agents or MCP servers.

Gmail delivery, public deployment, bonus matches, a graphical GUI, and learning policies remain
outside this phase.

## Architecture and safety

- `SeriesObserver` receives committed event/state pairs only after engine validation and transition.
- `TerminalObserver` reads immutable `GameState` objects and owns no rule or scoring logic.
- Rendered text is never passed to an agent or used to choose an action.
- Event snapshots use the same state serialization and hash inputs as replay evidence.
- Secret redaction covers sensitive nested keys, bearer tokens, and common inline secret
  assignments.
- Generated logs, reports, replay artifacts, and evidence manifests remain ignored by Git.

## Terminal content

The live view shows:

- rectangular board with row and column labels;
- `C` Cop, `T` Thief, `#` barrier, and `.` empty cell;
- zero-based `[row,column]` orientation;
- series, sub-game, attempt, and valid-game identifiers;
- move round and active role;
- barriers placed and remaining;
- selected action and accepted validation status;
- running role totals;
- terminal outcome and reason;
- technical failure details and replacement-attempt number;
- local MCP endpoint health after preflight; and
- report and evidence-manifest paths at completion.

## CLI

```powershell
python main.py --mode internal --config config.json --engine-only
python main.py --mode internal --config config.json --engine-only --quiet
python main.py --mode internal --config config.json --engine-only --quiet --json-logs
python main.py --config config.json --replay-events artifacts/logs/engine_only_events.json
```

`logging.level` controls the JSON-lines threshold. `INFO` includes normal events; `WARNING`
suppresses normal progress while preserving technical-failure events.

## Files added or changed

| Path | Purpose |
|---|---|
| `src/ai_agents_hw6/ui/terminal.py` | Board/state rendering, terminal observer, JSON logs, replay |
| `src/ai_agents_hw6/application/evidence.py` | Ignored evidence-manifest construction |
| `src/ai_agents_hw6/application/series.py` | Read-only observer seam and committed snapshots |
| `src/ai_agents_hw6/application/events.py` | Snapshot deserialization and expanded redaction |
| `src/ai_agents_hw6/application/mcp_client.py` | Endpoint-health notifications |
| `src/ai_agents_hw6/cli.py` | Quiet, JSON-log, and replay options |
| `main.py` | Observer, replay, and evidence-manifest wiring |
| `tests/unit/test_terminal_ui.py` | Phase 9 rendering, logging, redaction, and replay tests |
| `README.md` | Phase 9 status and operator commands |
| `todo.md` | Phase 9 tasks and gate completed |

All unrelated files were preserved.

## Verification

Commands:

- `$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'`
- `python -m compileall -q main.py src tests`
- `python main.py --mode internal --config config.json --engine-only --policy heuristic --quiet`
- `python main.py --mode internal --config config.json --engine-only --policy first-legal --quiet --json-logs`
- `python main.py --config config.json --replay-events artifacts/logs/engine_only_events.json`
- `python -m pip check`
- `git diff --check`

Expected and observed:

- 98 tests pass;
- compilation succeeds;
- a complete six-game `5 x 5` run succeeds;
- quiet mode omits live board frames;
- JSON-lines mode emits structured redacted records;
- replay renders committed snapshots and finishes without MCP calls;
- heuristic and first-legal policies still produce six valid games;
- the report and Phase 9 evidence manifest are written to ignored paths;
- dependency and whitespace checks pass.

## Phase gate

- Terminal projection is derived from the exact committed state carried by the event stream.
- Live and replay rendering use the same `render_state` function.
- Logs and UI output redact credentials and do not expose environment secrets.
- The baseline remains terminal-only; a fancy GUI is intentionally deferred.
