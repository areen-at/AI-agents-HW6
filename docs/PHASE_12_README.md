# Phase 12 Scientific and Operational README

## Result

PASS - The repository README is now a complete assessor-oriented scientific and operational guide.
It explains the required system, formal Dec-POMDP model, architecture and trust boundaries,
installation, configuration, local and remote operation, terminal/replay behavior, report and Gmail
workflow, deployment authentication, optional bonus boundary, tests, security, and troubleshooting.

## Coverage

The README now includes:

- project goal and required internal six-game mode;
- optional bonus mode as a separate later workflow;
- explicit ownership of only our Cop and Thief services;
- real external opponent requirements and test-only mock isolation;
- Mermaid architecture diagram including engine, orchestrator, services, reports, Gmail, and bonus
  links;
- MCP client/server and authoritative-engine boundaries;
- natural-language observation plus structured JSON action flow;
- formal `<n, S, {A_i}, P, R, {Omega_i}, O, gamma>` definition and implementation mapping;
- state, actions, transitions, rewards, observation radius, hidden fields, and heuristic/Q-learning
  status;
- Python, editable, Gmail, and optional developer dependency installation;
- every `config.json` group and `.env` secret category;
- reproducible Cop and Thief server commands;
- internal, engine-only, quiet, JSON log, and replay commands;
- internal report schema and path;
- Gmail authorization, preflight, exact JSON-only send, and idempotency;
- Render deployment URLs, authentication behavior, cold starts, rate/request limits, and evidence;
- opponent information, bonus/bonus-mock commands, 3+3 order, and mutual-agreement procedure;
- test inventory, known limitations, evidence links, security rules, and troubleshooting.

## Verification

Commands run:

- `python main.py --help`
- `python main.py --mode internal --config config.json`
- `python main.py --mode bonus-mock --config config.json`
- `python main.py --mode bonus --config config.json`
- `$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'`
- `python -m compileall -q main.py src tests`
- `python -m pip check`
- Markdown local-link existence scan
- README secret-pattern scan
- `git diff --check`

Observed:

- CLI help matches implemented options.
- Internal and bonus-mock configuration validation pass.
- Real bonus mode exits `2` because opponent placeholders are intentionally rejected.
- 110 tests pass.
- Compilation succeeds.
- Dependencies are consistent.
- All 16 README Markdown links resolve; all local targets exist.
- README contains no credential/token/private-key pattern.

Previously verified README workflows remain evidenced in their owning phases:

- engine-only and terminal/replay runs: Phases 4, 5, 6, and 9;
- local authenticated MCP series: Phases 8 and 11;
- Gmail authorization, preflight, and send: Phase 10;
- public Render authorization matrix, six-game run, and replay: Phase 11.

## Files changed

- `README.md`
- `src/ai_agents_hw6/cli.py`
- `todo.md`
- `docs/PHASE_12_README.md`

All unrelated files and ignored private/runtime artifacts were preserved.

## Next phase

Phase 13 performs the required clean release rehearsal. Bonus orchestration and Q-learning remain
later optional phases.
