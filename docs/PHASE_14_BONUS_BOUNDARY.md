# Phase 14 — Bonus Configuration and Mock Isolation

## Outcome

Phase 14 establishes a safe boundary for the optional inter-group bonus without inventing or
hosting a second production team. Internal mode remains independent of opponent metadata.
Production bonus mode fails before games unless real metadata, HTTPS endpoints, private
environment tokens, role identities, and protocol capabilities all pass. Mock mode is visibly
test-only and writes a separate non-claim report.

## Production bonus contract

The following values must come directly from a real class team:

- opponent group name;
- opponent student list;
- opponent GitHub repository URL;
- opponent Cop MCP HTTPS URL;
- opponent Thief MCP HTTPS URL;
- authentication-token exchange instructions; and
- confirmation that both services implement protocol `1.0` and `decide`.

Never guess, synthesize, copy from an unrelated team, or replace missing production values with
mock data. Metadata and URLs belong in `config.json`. Secrets never belong there: set only
`OPPONENT_COP_MCP_TOKEN` and `OPPONENT_THIEF_MCP_TOKEN` in the private runtime environment.

Run the production preflight with:

```powershell
python main.py --mode bonus --config config.json
```

The preflight validates all configuration fields together, requires distinct HTTPS role URLs,
sends bearer tokens only at runtime, checks `/health`, verifies `/identity` is `cop` or `thief`,
and checks `/capabilities` for protocol `1.0` plus `decide`. Any failure exits before Phase 15 game
orchestration can begin. With the repository's intentional placeholders, failure is the expected
safe result.

## Test-only mock contract

Run:

```powershell
python main.py --mode bonus-mock --config config.json
```

The isolated in-process test double always selects the first supplied legal action. Its report is
deterministic and contains exactly six entries:

- entries 1–3: our Cop versus mock Thief;
- entries 4–6: mock Cop versus our Thief.

The output is written only to `reports/bonus_game_report.mock.json`. It has
`report_type: bonus_game_mock`, `test_only: true`, zero bonus claims, a prominent warning, and
`mutual_agreement: false`. The writer refuses a shared production/mock path. The production report
validator rejects mock payloads, and mock mode refuses every Gmail command.

No opponent HTTP or MCP production server was added. The only production servers remain our Cop
and our Thief under `src/ai_agents_hw6/mcp_servers/`.

## Changed files

- `src/ai_agents_hw6/config.py`
- `src/ai_agents_hw6/application/bonus.py`
- `src/ai_agents_hw6/application/bonus_mock.py`
- `src/ai_agents_hw6/application/__init__.py`
- `src/ai_agents_hw6/reporting/bonus_report.py`
- `src/ai_agents_hw6/reporting/__init__.py`
- `main.py`
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/unit/test_bonus_boundary.py`
- `tests/unit/test_config.py`
- `README.md`
- `todo.md`
- `docs/PHASE_14_BONUS_BOUNDARY.md`

Existing secret files, generated reports, assignment PDFs, and unrelated user files are preserved
and excluded from the commit.

## Verification

Focused checks:

```powershell
python -m pytest tests/unit/test_bonus_boundary.py tests/unit/test_config.py -q
python main.py --mode bonus-mock --config config.json
python main.py --mode bonus --config config.json
```

Expected results:

- focused tests pass;
- mock mode prints `TEST-ONLY BONUS MOCK — NOT PRODUCTION EVIDENCE`;
- mock output is separate and cannot claim agreement or points;
- real bonus mode prints every unresolved opponent field and exits with status `2`;
- internal configuration remains valid without opponent data.

Release checks:

```powershell
ruff format --check .
ruff check .
mypy
python -m unittest discover -s tests -p "test_*.py"
python -m pytest
python -m compileall -q src main.py
python -m pip check
```

Recorded result:

- Ruff format check: 56 files formatted;
- Ruff lint: passed;
- strict mypy: 42 source files passed;
- unittest: 120 tests passed;
- pytest: 120 tests passed;
- compileall: passed;
- pip dependency check: no broken requirements;
- internal CLI validation: passed;
- mock CLI validation: passed with the test-only warning;
- production CLI validation: expected status `2`, listing all five unresolved opponent fields.
