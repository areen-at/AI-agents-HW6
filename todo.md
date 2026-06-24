# Implementation TODO: Dual AI Agent Race via MCP Servers

## Usage and non-negotiable scope

- [ ] Use PRD.md and PLAN.md as the design baseline.
- [ ] Treat normal mode as required and bonus mode as optional.
- [ ] Build only our Cop server, our Thief server, local engine/orchestrator, and reports.
- [ ] Connect bonus mode to a real external class team.
- [ ] Never build a second production team locally.
- [ ] Allow mocks only in explicit test-only bonus-mock mode.
- [ ] Finish simple local heuristics before considering Q-learning.
- [ ] Prefer a reliable terminal board over a fancy GUI.
- [ ] Do not rewrite unrelated files.
- [ ] Do not delete anything without explicit approval.
- [ ] Keep parameters in config.json or config.yaml.
- [ ] Keep secrets outside tracked files.
- [ ] After every phase stop and report files, commands, expected output, and tests.
- [ ] Mark a checkbox complete only when evidence exists.

## Required commands and outputs to preserve

- [ ] Support python main.py --mode internal --config config.json or documented equivalent.
- [ ] Support python main.py --mode bonus --config config.json or documented equivalent.
- [ ] Support python main.py --mode bonus-mock --config config.json or documented equivalent.
- [ ] Write reports/internal_game_report.json.
- [ ] Write reports/bonus_game_report.json only for real bonus mode.
- [ ] Send final JSON-only Gmail body to rmisegal+uoh26b@gmail.com when authorized.

## Phase 0 - Repository inspection and decisions

### Tasks

- [x] T0001 Confirm workspace root and inventory every existing file and directory.
- [x] T0002 Record uncommitted user changes and preserve them.
- [x] T0003 Identify existing Python, tests, configs, reports, MCP, Gmail, and deployment files.
- [x] T0004 Read PRD.md, PLAN.md, and this checklist completely.
- [x] T0005 Confirm normal mode is mandatory and bonus mode is optional.
- [x] T0006 Confirm only our Cop and Thief servers are production-owned.
- [x] T0007 Confirm opponent bonus servers are external URLs.
- [x] T0008 Confirm heuristic strategies precede Q-learning.
- [x] T0009 Confirm terminal visualization is sufficient for baseline.
- [x] T0010 Document missing components without writing implementation code.
- [x] T0011 Choose and document coordinate orientation.
- [x] T0012 Confirm distinct starting cells.
- [x] T0013 Resolve the partial-observation sensor rule.
- [x] T0014 Resolve barrier placement range and trapping rule.
- [x] T0015 Confirm barrier placement consumes Cop action.
- [x] T0016 Confirm Thief acts first in every round.
- [x] T0017 Confirm capture precedence on the final round.
- [x] T0018 Define invalid-action repair and technical-failure policy.
- [x] T0019 Define exact internal sub_games schema.
- [x] T0020 Define maximum technical retry safety limit.
- [x] T0021 Propose package and test structure.
- [x] T0022 Identify files that must remain untouched.
- [x] T0023 Produce phase file-change report.
- [x] T0024 Produce phase run-command report.
- [x] T0025 Produce phase expected-output report.
- [x] T0026 Produce phase test instructions and stop before next phase.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 1 - Project foundation and configuration

### Tasks

- [x] T0027 Select Python 3.10+ and uv unless existing tooling requires otherwise.
- [x] T0028 Create or validate pyproject.toml.
- [x] T0029 Add only necessary runtime dependencies.
- [x] T0030 Add formatter, linter, type checker, and pytest configuration.
- [x] T0031 Create src/domain, src/application, src/contracts, src/agents, and src/mcp_servers.
- [x] T0032 Create src/reporting, src/infrastructure, src/ui, and tests hierarchy.
- [x] T0033 Create config.json example with no real secrets.
- [x] T0034 Set grid_size default to [5,5].
- [x] T0035 Set max_moves default to 25.
- [x] T0036 Set num_games default to 6.
- [x] T0037 Set max_barriers default to 5.
- [x] T0038 Set scoring defaults 20,10,5,5.
- [x] T0039 Set timezone default to Asia/Jerusalem.
- [x] T0040 Add deterministic random_seed setting.
- [x] T0041 Add observation, timeout, retry, and logging settings.
- [x] T0042 Add real-group metadata placeholders.
- [x] T0043 Add my_servers Cop and Thief URL fields.
- [x] T0044 Add bonus_opponent metadata fields without invented values.
- [x] T0045 Add report output paths.
- [x] T0046 Implement typed configuration loading.
- [x] T0047 Reject malformed JSON with field-specific errors.
- [x] T0048 Require exactly six games in production modes.
- [x] T0049 Require opponent fields only in production bonus mode.
- [x] T0050 Create .env.example with names only.
- [x] T0051 Ignore .env, credentials.json, token.json, logs, and secret artifacts.
- [x] T0052 Run a tracked-file secret scan.
- [x] T0053 Verify clean dependency installation.
- [x] T0054 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 2 - Core domain model

### Tasks

- [x] T0055 Define Role COP and THIEF.
- [x] T0056 Define orthogonal Direction values.
- [x] T0057 Define MOVE and PLACE_BARRIER action types.
- [x] T0058 Define terminal outcomes and reason codes.
- [x] T0059 Define technical-failure reason codes.
- [x] T0060 Create immutable Coordinate value object.
- [x] T0061 Create immutable GridSize value object.
- [x] T0062 Implement coordinate serialization.
- [x] T0063 Implement direction-to-delta conversion.
- [x] T0064 Implement bounded orthogonal neighbor generation.
- [x] T0065 Define immutable authoritative GameState.
- [x] T0066 Include grid, positions, barriers, active role, counter, terminal metadata, and seed.
- [x] T0067 Prevent mutable collection leakage from GameState.
- [x] T0068 Create unique series, sub-game, attempt, and request identifiers.
- [x] T0069 Implement seeded initial placement.
- [x] T0070 Place both agents inside board bounds.
- [x] T0071 Guarantee distinct initial positions.
- [x] T0072 Start with empty barriers and Thief active.
- [x] T0073 Validate player positions never overlap barriers.
- [x] T0074 Validate barriers are unique and in bounds.
- [x] T0075 Validate move and barrier counts are non-negative.
- [x] T0076 Validate terminal state invariants.
- [x] T0077 Test corners, edges, and interior coordinates.
- [x] T0078 Test same-seed initialization reproducibility.
- [x] T0079 Ensure domain layer imports no MCP, UI, Gmail, or provider code.
- [x] T0080 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 3 - Game rules, scoring, and small-board checks

### Tasks

- [x] T0081 Generate legal Cop moves.
- [x] T0082 Generate legal Thief moves.
- [x] T0083 Reject out-of-bounds moves.
- [x] T0084 Reject diagonal and unsupported stay moves.
- [x] T0085 Reject moves onto barriers.
- [x] T0086 Guarantee invalid actions do not mutate state.
- [x] T0087 Enforce Thief-first turn order.
- [x] T0088 Prevent repeated or out-of-turn actions.
- [x] T0089 Switch to Cop after valid non-terminal Thief action.
- [x] T0090 Switch to Thief after valid non-terminal Cop action.
- [x] T0091 Detect capture only on exact cell equality.
- [x] T0092 Stop all actions immediately after capture.
- [x] T0093 Declare Thief win at configured move limit.
- [x] T0094 Implement approved round-counter semantics.
- [x] T0095 Apply capture precedence on final round.
- [x] T0096 Permit barrier placement only by Cop.
- [x] T0097 Make barrier placement consume Cop turn.
- [x] T0098 Reject barrier on a player, existing barrier, or invalid cell.
- [x] T0099 Enforce five-barrier default maximum.
- [x] T0100 Make barriers impassable to both roles.
- [x] T0101 Implement score lookup from configuration.
- [x] T0102 Award 20/5 on Cop capture by default.
- [x] T0103 Award 5/10 on Thief survival by default.
- [x] T0104 Ignore any score supplied by an agent.
- [x] T0105 Exhaustively test 2x2 behavior where practical.
- [x] T0106 Run sanity suites on 3x2, 3x3, 4x3, 4x4, and 5x5.
- [x] T0107 Test terminal-state immutability and deterministic transitions.
- [x] T0108 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 4 - Series control, events, replay, and internal report

### Tasks

- [x] T0109 Create series controller independent of MCP.
- [x] T0110 Create unique series ID and six valid game slots.
- [x] T0111 Create a new attempt ID for every attempt.
- [x] T0112 Keep attempt count separate from valid-game count.
- [x] T0113 Stop after exactly six valid sub-games.
- [x] T0114 Prevent a seventh valid sub-game.
- [x] T0115 Define failures that invalidate an attempt.
- [x] T0116 Exclude invalid attempts from counts and scores.
- [x] T0117 Preserve invalid-attempt evidence.
- [x] T0118 Retry invalid attempts within configured safety limit.
- [x] T0119 Never convert infrastructure failure into strategic loss.
- [x] T0120 Aggregate Cop and Thief scores from terminal records.
- [x] T0121 Define versioned append-only event schema.
- [x] T0122 Log IDs, timestamps, seed, role, action, validation, state hash, result, and score.
- [x] T0123 Redact secrets from events.
- [x] T0124 Implement atomic event persistence.
- [x] T0125 Implement offline replay from seed and accepted actions.
- [x] T0126 Make replay independent of MCP and models.
- [x] T0127 Verify every replay state hash and final score.
- [x] T0128 Define full internal sub_game report entry.
- [x] T0129 Populate group_name, students, github_repo, owned URLs, and timezone.
- [x] T0130 Calculate report totals rather than trusting callers.
- [x] T0131 Validate exactly six internal sub-games.
- [x] T0132 Serialize JSON without surrounding prose.
- [x] T0133 Write reports/internal_game_report.json atomically.
- [x] T0134 Add engine-only internal CLI test command.
- [x] T0135 Inject timeouts and malformed actions to test replacement attempts.
- [x] T0136 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 5 - Simple heuristic agents

### Tasks

- [x] T0137 Define policy input as role observation rather than true state.
- [x] T0138 Define policy output as one typed action.
- [x] T0139 Include current legal actions in policy input.
- [x] T0140 Implement Cop Manhattan-distance pursuit.
- [x] T0141 Use only observable or remembered Thief estimates.
- [x] T0142 Prefer legal Cop moves that reduce estimated distance.
- [x] T0143 Use deterministic or seeded tie breaking.
- [x] T0144 Define a small measurable barrier-usefulness rule.
- [x] T0145 Place a Cop barrier only when legal and useful.
- [x] T0146 Fall back to a legal Cop move when barrier is not useful.
- [x] T0147 Implement Thief Manhattan-distance escape.
- [x] T0148 Use only observable or remembered Cop estimates.
- [x] T0149 Prefer legal Thief moves that increase estimated distance.
- [x] T0150 Avoid traps and barriers when a safer move exists.
- [x] T0151 Never permit Thief barrier actions.
- [x] T0152 Handle no-visible-opponent cases deterministically.
- [x] T0153 Handle no-legal-move cases according to approved rule.
- [x] T0154 Test pursuit in open grid.
- [x] T0155 Test pursuit around barriers.
- [x] T0156 Test escape in open grid.
- [x] T0157 Test escape around barriers.
- [x] T0158 Test barrier maximum behavior.
- [x] T0159 Test every heuristic result against engine legal actions.
- [x] T0160 Run six engine-only games with heuristics.
- [x] T0161 Keep Q-learning and expensive search out of this phase.
- [x] T0162 Document every tie breaker and assumption.
- [x] T0163 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 6 - Partial observations and natural-language protocol

### Tasks

- [x] T0164 Implement approved role-specific observation function.
- [x] T0165 Include own position and allowed local information.
- [x] T0166 Include visible barriers only.
- [x] T0167 Include opponent data only when observable.
- [x] T0168 Include move number and allowed budgets.
- [x] T0169 Exclude hidden coordinates and full state.
- [x] T0170 Return immutable observation DTOs.
- [x] T0171 Create separate Cop and Thief natural-language templates.
- [x] T0172 State each role objective in plain language.
- [x] T0173 Describe current observation in text.
- [x] T0174 Describe permitted action vocabulary.
- [x] T0175 Include bounded relevant history.
- [x] T0176 Require exactly one action response.
- [x] T0177 Define strict move response schema.
- [x] T0178 Define strict Cop barrier response schema.
- [x] T0179 Require protocol version and request ID.
- [x] T0180 Reject unknown action types and oversized output.
- [x] T0181 Parse JSON safely.
- [x] T0182 Validate proposed action against current legal actions.
- [x] T0183 Allow one bounded correction request.
- [x] T0184 Classify unrecoverable malformed response as technical failure.
- [x] T0185 Test messages for hidden coordinate leakage.
- [x] T0186 Test errors and transport logs for hidden state leakage.
- [x] T0187 Keep terminal renderer output out of agent inputs.
- [x] T0188 Make heuristic adapter use the same message contract.
- [x] T0189 Capture sanitized natural-language decision traces.
- [x] T0190 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 7 - Independent Cop and Thief MCP servers

### Tasks

- [x] T0191 Confirm FastMCP version and minimal dependency set.
- [x] T0192 Define shared MCP protocol version 1.0.
- [x] T0193 Create dedicated Cop server entry point.
- [x] T0194 Create dedicated Thief server entry point.
- [x] T0195 Run each server in its own process and port.
- [x] T0196 Give Cop server fixed Cop identity.
- [x] T0197 Give Thief server fixed Thief identity.
- [x] T0198 Expose health operation on each server.
- [x] T0199 Expose capabilities and protocol-version operations.
- [x] T0200 Expose natural-language decision operation on each server.
- [x] T0201 Accept only validated role-specific observations.
- [x] T0202 Invoke only the matching role policy.
- [x] T0203 Return one schema-valid action.
- [x] T0204 Reject role mismatch requests.
- [x] T0205 Add request and correlation IDs.
- [x] T0206 Add bounded request timeout handling.
- [x] T0207 Add token-authentication integration point.
- [x] T0208 Prevent shared mutable policy state.
- [x] T0209 Verify stopping one server does not stop the other.
- [x] T0210 Test both health and identity responses.
- [x] T0211 Test valid Cop and Thief requests.
- [x] T0212 Test malformed observations.
- [x] T0213 Test missing and duplicate request IDs.
- [x] T0214 Test protocol mismatch.
- [x] T0215 Test unauthorized requests when auth is enabled.
- [x] T0216 Verify MCP servers cannot mutate game state.
- [x] T0217 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 8 - Local MCP orchestrator and required run

### Tasks

- [x] T0218 Create MCP client connection for owned Cop server.
- [x] T0219 Create MCP client connection for owned Thief server.
- [x] T0220 Read URLs from config and tokens from environment.
- [x] T0221 Run health, role, and version preflight.
- [x] T0222 Refuse start when either owned server is unavailable.
- [x] T0223 Keep authoritative game state local.
- [x] T0224 Send Thief observation and natural-language request first.
- [x] T0225 Validate and apply Thief response through engine.
- [x] T0226 Check terminal state before contacting Cop.
- [x] T0227 Send Cop observation and natural-language request.
- [x] T0228 Validate and apply Cop response through engine.
- [x] T0229 Repeat until terminal.
- [x] T0230 Never let orchestrator choose strategic fallback move.
- [x] T0231 Generate one idempotency key per decision.
- [x] T0232 Reuse idempotency key only for safe retry.
- [x] T0233 Apply each response at most once.
- [x] T0234 Record and reject duplicate responses.
- [x] T0235 Turn exhausted MCP failures into invalid attempts.
- [x] T0236 Schedule replacement attempts until six valid games.
- [x] T0237 Add python main.py --mode internal --config config.json or equivalent.
- [x] T0238 Render terminal board during the run.
- [x] T0239 Print each game result and aggregate totals.
- [x] T0240 Generate required internal report.
- [x] T0241 Test missing Cop and Thief servers.
- [x] T0242 Test timeout, malformed response, duplicate response, and version mismatch.
- [x] T0243 Complete six valid games exclusively through MCP.
- [x] T0244 Replay the completed series offline.
- [x] T0245 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 9 - Terminal visualization and operational logging

### Tasks

- [x] T0246 Render a rectangular grid for configured dimensions.
- [x] T0247 Render Cop as an unambiguous symbol.
- [x] T0248 Render Thief as an unambiguous symbol.
- [x] T0249 Render barriers and empty cells distinctly.
- [x] T0250 Add row and column labels where useful.
- [x] T0251 Document coordinate orientation.
- [x] T0252 Avoid color-only meaning and support no-color output.
- [x] T0253 Display series, sub-game, and attempt identifiers.
- [x] T0254 Display move-round count and active role.
- [x] T0255 Display placed and remaining Cop barriers.
- [x] T0256 Display selected action and validation status.
- [x] T0257 Display current score totals.
- [x] T0258 Display terminal result and reason.
- [x] T0259 Display technical failures and replacement attempts.
- [x] T0260 Display report output path at completion.
- [x] T0261 Render only committed authoritative state.
- [x] T0262 Keep renderer read-only.
- [x] T0263 Keep all rule logic out of renderer.
- [x] T0264 Never feed rendered board to agents.
- [x] T0265 Support quiet/headless mode for tests.
- [x] T0266 Emit structured JSON logs.
- [x] T0267 Emit concise human-readable logs.
- [x] T0268 Redact tokens, credentials, and authorization headers.
- [x] T0269 Add configurable log level.
- [x] T0270 Keep a fancy GUI deferred until baseline passes.
- [x] T0271 Verify humans can follow a complete 5x5 game.
- [x] T0272 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 10 - Gmail and normal-report delivery

### Tasks

- [x] T0273 Finalize real group metadata in safe configuration.
- [x] T0274 Validate exactly six internal sub-games and calculated totals.
- [x] T0275 Confirm report path reports/internal_game_report.json.
- [x] T0276 Enable Gmail API in the intended Google Cloud project.
- [x] T0277 Configure consent screen, audience, and test user.
- [x] T0278 Create Desktop OAuth client.
- [x] T0279 Store credentials.json outside tracked source.
- [x] T0280 Configure credential and token paths through environment.
- [x] T0281 Use least-privilege Gmail sending scope.
- [x] T0282 Complete interactive authorization once.
- [x] T0283 Store token.json outside tracked source.
- [x] T0284 Implement token refresh and revocation handling.
- [x] T0285 Build Gmail MIME message from canonical JSON.
- [x] T0286 Set final recipient rmisegal+uoh26b@gmail.com.
- [x] T0287 Put JSON only in message body.
- [x] T0288 Add no greeting, signature, Markdown fence, or prose.
- [x] T0289 Validate JSON immediately before sending.
- [x] T0290 Preserve canonical payload before sending.
- [x] T0291 Capture Gmail message ID and timestamp.
- [x] T0292 Make send retry idempotent where possible.
- [x] T0293 Keep send failure separate from game result.
- [x] T0294 Unit-test Gmail adapter with fake client.
- [x] T0295 Test missing credentials and expired token.
- [x] T0296 Perform a permitted fake-transport smoke test.
- [x] T0297 Inspect decoded fake-client body for exact JSON-only content.
- [x] T0298 Document final send procedure.
- [x] T0299 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 11 - Deployment of our two MCP servers

### Tasks

- [x] T0300 Keep ports, URLs, tokens, timeouts, and log levels configurable.
- [x] T0301 Define reproducible Cop server start command.
- [x] T0302 Define reproducible Thief server start command.
- [x] T0303 Select the simplest suitable cloud or tunnel provider.
- [x] T0304 Assign separate public HTTPS URLs.
- [x] T0305 Configure token authentication on both endpoints.
- [x] T0306 Reject missing and invalid tokens.
- [x] T0307 Accept valid scoped tokens.
- [x] T0308 Document token rotation and revocation.
- [x] T0309 Configure TLS termination through the selected tunnel boundary.
- [x] T0310 Redact authorization headers.
- [x] T0311 Apply request-size and rate limits where supported.
- [x] T0312 Ensure local heuristic dependencies are reachable by chosen architecture.
- [x] T0313 Prefer outbound or hybrid connectivity over unsafe inbound localhost exposure.
- [x] T0314 Probe Cop health externally.
- [x] T0315 Probe Thief health externally.
- [x] T0316 Verify remote role identities and protocol versions.
- [x] T0317 Test unauthorized and authorized remote decisions.
- [x] T0318 Run one complete remote internal series.
- [x] T0319 Replay remote results locally.
- [x] T0320 Record sanitized deployment evidence.
- [x] T0321 Keep public endpoints available for required window.
- [x] T0322 Document firewall, proxy, or tunnel behavior.
- [x] T0323 Fail fast on missing production secrets.
- [x] T0324 Verify no secrets are tracked.
- [x] T0325 Add validation that production URLs are HTTPS and distinct.
- [x] T0326 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 12 - README and scientific documentation

### Tasks

- [x] T0327 Explain project goal and required normal mode.
- [x] T0328 Explain optional bonus mode separately.
- [x] T0329 State repository owns only our Cop and Thief servers.
- [x] T0330 State opponent bonus servers are real external services.
- [x] T0331 State opponent mocks are test-only.
- [x] T0332 Diagram engine, orchestrator, both MCP servers, reports, and external bonus links.
- [x] T0333 Explain MCP client/server boundaries.
- [x] T0334 Explain natural-language plus structured action flow.
- [x] T0335 Explain why engine alone mutates state.
- [x] T0336 Define Dec-POMDP tuple n,S,{Ai},P,R,{Omega_i},O,gamma.
- [x] T0337 Map every Dec-POMDP element to implementation.
- [x] T0338 Explain partial observability and hidden fields.
- [x] T0339 Document Python and dependency installation.
- [x] T0340 Document config.json and .env setup.
- [x] T0341 Document both server start commands.
- [x] T0342 Document internal mode command and expected output.
- [x] T0343 Document test and replay commands.
- [x] T0344 Document every configuration group.
- [x] T0345 Document internal report schema and path.
- [x] T0346 Document Gmail JSON-only workflow.
- [x] T0347 Document deployment and authentication.
- [x] T0348 List all opponent information needed for bonus.
- [x] T0349 Document bonus and bonus-mock commands.
- [x] T0350 Document 3+3 matchup order.
- [x] T0351 Document mutual-agreement procedure.
- [x] T0352 Verify all required README commands actually work.
- [x] T0353 Verify README contains no secrets.
- [x] T0354 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 13 - Required release rehearsal

### Tasks

- [x] T0355 Set up from a clean checkout or clean environment.
- [x] T0356 Install dependencies using README commands.
- [x] T0357 Create configuration and environment from examples.
- [x] T0358 Start owned Cop and Thief MCP servers.
- [x] T0359 Verify both health checks.
- [x] T0360 Run final internal mode command.
- [x] T0361 Confirm Thief acts first and Cop second.
- [x] T0362 Confirm barriers and movement rules.
- [x] T0363 Confirm no game exceeds 25 rounds.
- [x] T0364 Confirm exactly six valid sub-games.
- [x] T0365 Confirm score matrix in every result.
- [x] T0366 Inject and replace at least one technical failure in rehearsal.
- [x] T0367 Verify terminal output.
- [x] T0368 Verify structured logs.
- [x] T0369 Replay all six valid games.
- [x] T0370 Verify internal report schema and totals.
- [x] T0371 Run formatter check.
- [x] T0372 Run linter and type checker.
- [x] T0373 Run unit, contract, integration, and end-to-end tests.
- [x] T0374 Run secret scan.
- [x] T0375 Record commit ID and sanitized config digest.
- [x] T0376 Record six valid game IDs and replay result.
- [x] T0377 Record public owned MCP URLs.
- [x] T0378 Send or rehearse final Gmail JSON procedure as authorized.
- [x] T0379 Confirm no bonus or Q-learning dependency exists.
- [x] T0380 Confirm no critical defect remains.
- [x] T0381 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 14 - Bonus configuration and mock isolation

### Tasks

- [x] T0382 Do not start until required Phase 13 passes.
- [x] T0383 Model opponent group name, students, repository, Cop URL, and Thief URL.
- [x] T0384 Read opponent authentication secrets only from environment.
- [x] T0385 Keep opponent fields optional in internal mode.
- [x] T0386 Require all opponent fields in production bonus mode.
- [x] T0387 Reject placeholder opponent names and URLs.
- [x] T0388 Require HTTPS external URLs in production bonus mode.
- [x] T0389 Print all missing opponent fields clearly.
- [x] T0390 Refuse games after failed bonus preflight.
- [x] T0391 Add explicit bonus-mock mode.
- [x] T0392 Keep mock code test-only or clearly isolated.
- [x] T0393 Print prominent test-only warning in mock mode.
- [x] T0394 Prevent mock mode from sending Gmail.
- [x] T0395 Prevent mock mode from setting mutual_agreement true.
- [x] T0396 Prevent mock output from overwriting production bonus report.
- [x] T0397 Use deterministic mock responses.
- [x] T0398 Test both matchup directions in mock mode.
- [x] T0399 Add python main.py --mode bonus-mock --config config.json or equivalent.
- [x] T0400 Confirm internal mode still works without opponent data.
- [x] T0401 Confirm production bonus fails without real data.
- [x] T0402 Confirm no opponent production server implementation exists.
- [x] T0403 Document how to receive data from real opponent.
- [x] T0404 Document never to invent missing data.
- [x] T0405 Validate opponent role identities before match.
- [x] T0406 Validate protocol compatibility before match.
- [x] T0407 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [x] All tasks required for this phase have evidence.
- [x] Automated and manual verification results are recorded.
- [x] Changed files and unrelated preserved files are listed.
- [x] Run commands and expected output are documented.
- [x] Work stops here for review before the next phase.

## Phase 15 - External bonus match orchestration

### Tasks

- [x] T0408 Add python main.py --mode bonus --config config.json or equivalent.
- [ ] T0409 Load both groups' real metadata.
- [x] T0410 Load all four MCP URLs.
- [x] T0411 Verify owned and opponent endpoints.
- [x] T0412 Verify authentication and role identity on all endpoints.
- [ ] T0413 Agree with opponent on configuration, seeds, timeouts, and retry policy.
- [x] T0414 Print the six-game matchup schedule.
- [ ] T0415 Run games 1-3 with our Cop versus opponent Thief.
- [ ] T0416 Run games 4-6 with opponent Cop versus our Thief.
- [x] T0417 Keep local engine authoritative for every game.
- [x] T0418 Use normal grid, barrier, move, and scoring rules.
- [x] T0419 Replace technical failure attempts.
- [x] T0420 Record endpoint ownership per sub-game.
- [x] T0421 Validate exactly six valid bonus games.
- [x] T0422 Validate first three matchup assignments.
- [x] T0423 Validate last three matchup assignments.
- [x] T0424 Reject reversed or duplicated matchup order.
- [x] T0425 Attribute role scores to owning groups.
- [x] T0426 Calculate totals_by_group from sub-games.
- [x] T0427 Return non-zero when opponent preflight fails.
- [x] T0428 Never print authentication tokens.
- [x] T0429 Preserve event and replay evidence.
- [ ] T0430 Share identical result evidence with opponent.
- [ ] T0431 Resolve discrepancies before report creation.
- [x] T0432 Run mock ordering tests before real match.
- [x] T0433 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [ ] All tasks required for this phase have evidence.
- [ ] Automated and manual verification results are recorded.
- [ ] Changed files and unrelated preserved files are listed.
- [ ] Run commands and expected output are documented.
- [ ] Work stops here for review before the next phase.

## Phase 16 - Bonus report and mutual agreement

### Tasks

- [x] T0434 Set report_type to bonus_game.
- [ ] T0435 Populate both real group names.
- [ ] T0436 Populate both real GitHub repository URLs.
- [ ] T0437 Populate all four real MCP URLs.
- [ ] T0438 Populate both real student arrays.
- [x] T0439 Set timezone to Asia/Jerusalem.
- [x] T0440 Include exactly six valid sub-games.
- [x] T0441 Include 3+3 endpoint ownership data.
- [x] T0442 Calculate totals_by_group.
- [x] T0443 Assign bonus claim 10 to winner and 7 to loser.
- [x] T0444 Assign bonus claim 5 to each group on draw.
- [x] T0445 Keep bonus claims separate from game totals.
- [x] T0446 Initialize mutual_agreement to false.
- [x] T0447 Generate canonical JSON for opponent comparison.
- [ ] T0448 Compare games, outcomes, scores, totals, and claims with opponent.
- [ ] T0449 Resolve differences using event evidence.
- [ ] T0450 Obtain explicit approval from both groups.
- [x] T0451 Set mutual_agreement true only after exact approval.
- [x] T0452 Regenerate and validate final payload.
- [x] T0453 Write reports/bonus_game_report.json atomically.
- [x] T0454 Write mock report to a separate test path.
- [x] T0455 Reject placeholder or invented opponent metadata.
- [x] T0456 Reject sending while mutual_agreement is false.
- [x] T0457 Add no prose around report JSON.
- [x] T0458 Preserve agreement evidence.
- [ ] T0459 Validate report checksum with opponent.
- [x] T0460 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [ ] All tasks required for this phase have evidence.
- [ ] Automated and manual verification results are recorded.
- [ ] Changed files and unrelated preserved files are listed.
- [ ] Run commands and expected output are documented.
- [ ] Work stops here for review before the next phase.

## Phase 17 - Optional Q-learning after completion

### Tasks

- [ ] T0461 Enter only after all required release gates pass.
- [ ] T0462 Confirm learning cannot delay submission.
- [ ] T0463 Keep heuristic strategies available as fallback.
- [ ] T0464 Define observation-based state encoding.
- [ ] T0465 Never encode hidden true state.
- [ ] T0466 Define role-specific legal action indices.
- [ ] T0467 Create separate Cop and Thief Q-tables.
- [ ] T0468 Configure alpha, gamma, epsilon, and seed.
- [ ] T0469 Implement epsilon-greedy legal-action selection.
- [ ] T0470 Implement terminal-safe Q update.
- [ ] T0471 Persist tables separately with versions.
- [ ] T0472 Reject incompatible table versions.
- [ ] T0473 Add runtime feature flag.
- [ ] T0474 Use separate training and evaluation seeds.
- [ ] T0475 Compare with fixed heuristic baseline.
- [ ] T0476 Measure scores, illegal actions, and average moves.
- [ ] T0477 Keep MCP contracts unchanged.
- [ ] T0478 Keep report schemas unchanged.
- [ ] T0479 Keep technical-failure policy unchanged.
- [ ] T0480 Disable learning if reliability regresses.
- [ ] T0481 Document learning as optional.
- [ ] T0482 Run full baseline suite with learning off.
- [ ] T0483 Run focused evaluation with learning on.
- [ ] T0484 Verify no hidden-state leakage.
- [ ] T0485 Do not make Q-learning a normal-mode dependency.
- [ ] T0486 Report phase files, commands, outputs, and tests then stop.

### Phase gate

- [ ] All tasks required for this phase have evidence.
- [ ] Automated and manual verification results are recorded.
- [ ] Changed files and unrelated preserved files are listed.
- [ ] Run commands and expected output are documented.
- [ ] Work stops here for review before the next phase.

## Cross-cutting quality and final handoff

### Tasks

- [ ] T0487 Maintain unit tests for every game rule.
- [ ] T0488 Maintain contract tests for every external schema.
- [ ] T0489 Maintain integration tests for both local MCP servers.
- [ ] T0490 Maintain end-to-end internal and bonus-mock tests.
- [ ] T0491 Maintain observation leak tests.
- [ ] T0492 Maintain timeout, retry, duplicate, and idempotency tests.
- [ ] T0493 Maintain report total and schema tests.
- [ ] T0494 Maintain fake Gmail tests.
- [ ] T0495 Maintain remote auth tests when endpoints exist.
- [ ] T0496 Map PRD game requirements to tests.
- [ ] T0497 Map PRD observation requirements to tests.
- [ ] T0498 Map PRD MCP requirements to traces.
- [ ] T0499 Map PRD reporting requirements to schemas.
- [ ] T0500 Map PRD deployment requirements to probes.
- [ ] T0501 Map bonus external-only scope to architecture evidence.
- [ ] T0502 Run all quality commands before handoff.
- [ ] T0503 List exact local startup commands.
- [ ] T0504 List exact internal, bonus, and bonus-mock commands.
- [ ] T0505 List exact test and replay commands.
- [ ] T0506 Link internal and bonus reports when applicable.
- [ ] T0507 Link sanitized logs and replay evidence.
- [ ] T0508 State owned public URLs and availability window.
- [ ] T0509 State Gmail delivery status.
- [ ] T0510 State deferred optional work and known limitations.
- [ ] T0511 Confirm no unrelated file was rewritten.
- [ ] T0512 Confirm no file was deleted without approval.
- [ ] T0513 Confirm no tracked secret and no false completion claim.

### Phase gate

- [ ] All tasks required for this phase have evidence.
- [ ] Automated and manual verification results are recorded.
- [ ] Changed files and unrelated preserved files are listed.
- [ ] Run commands and expected output are documented.
- [ ] Work stops here for review before the next phase.

## Final required-mode acceptance

- [ ] Default grid is 5x5.
- [ ] Exactly six valid internal sub-games complete.
- [ ] Each sub-game uses at most 25 move rounds.
- [ ] Cop captures only on exact Thief cell.
- [ ] Cop places at most five barriers and Thief places none.
- [ ] Scores are 20/5 for capture and 5/10 for survival.
- [ ] Two owned MCP servers run independently.
- [ ] Natural-language messages cross MCP boundaries.
- [ ] Engine alone owns true state.
- [ ] Agents receive only approved observations.
- [ ] Terminal visualization shows players, barriers, moves, and results.
- [ ] Internal report validates at the required path.
- [ ] README contains Dec-POMDP and operational documentation.
- [ ] Owned servers are deployment-ready with environment-based secrets.
- [ ] No Q-learning or opponent implementation is required for baseline.

## Final bonus-mode acceptance

- [ ] Normal required mode passed first.
- [ ] Opponent data came from a real external team.
- [ ] No opponent production server was built locally.
- [ ] First three games are our Cop versus opponent Thief.
- [ ] Last three games are opponent Cop versus our Thief.
- [ ] Exactly six valid bonus sub-games complete.
- [ ] Totals and bonus claims are calculated from evidence.
- [ ] mutual_agreement remains false until both teams approve identical JSON.
- [ ] Production and mock reports use separate paths.
- [ ] Final bonus report validates at reports/bonus_game_report.json.

## Mandatory GitHub workflow after every phase

- [ ] Run all automated tests required by the completed phase.
- [ ] Run all manual checks required by the completed phase.
- [ ] Record the exact commands and results.
- [ ] Run `git status`.
- [ ] Inspect modified, deleted, staged, and untracked files.
- [ ] Confirm every changed path belongs to the phase or is intentionally left out.
- [ ] Inspect the diff before staging.
- [ ] Stage only phase-related files.
- [ ] Inspect the staged diff before committing.
- [ ] Scan staged filenames and content for secrets.
- [ ] Confirm no `.env` or `*.env` file is staged.
- [ ] Confirm no API key is staged.
- [ ] Confirm no MCP, OAuth, or provider token is staged.
- [ ] Confirm no `credentials.json` or client-secret file is staged.
- [ ] Confirm no private key or certificate is staged.
- [ ] Confirm no `__pycache__/` or `*.pyc` file is staged.
- [ ] Confirm no `.venv/` or `venv/` content is staged.
- [ ] Confirm no `.DS_Store`, editor junk, log, cache, or temporary file is staged.
- [ ] Confirm real/private `reports/*.json` files remain ignored.
- [ ] Confirm assignment PDFs remain ignored unless explicitly approved.
- [ ] Verify `.gitignore` still contains all required protections.
- [ ] Create a clear phase-scoped commit message.
- [ ] Commit only the inspected staged files.
- [ ] Run `git status` after the commit.
- [ ] Identify files intentionally ignored or left uncommitted.
- [ ] Prepare the pre-push summary.
- [ ] List files changed in the summary.
- [ ] List files committed in the summary.
- [ ] List relevant ignored files in the summary.
- [ ] List tests/checks and their results in the summary.
- [ ] Show the commit message in the summary.
- [ ] Show target remote `https://github.com/areen-at/AI-agents-HW6`.
- [ ] Show the target branch.
- [ ] Treat the pre-push summary as informational for ordinary phase pushes.
- [ ] Push the phase commit automatically after the summary and safety checks.
- [ ] Verify local and remote branches are synchronized after the push.
- [ ] Report the pushed commit ID and branch.
- [ ] Never force-push without separate explicit authorization.
- [ ] Never include unrelated user changes in a phase commit.
- [ ] Treat a phase as locally complete after its verified commit exists.
- [ ] Treat a phase as remotely complete only after a successful automatic push.

## GitHub repository setup backlog

- [ ] Repair or replace the invalid local `.git` reparse placeholder with user approval.
- [ ] Initialize this workspace as its own Git repository if no valid history exists.
- [ ] Use the default branch agreed with the user, normally `main`.
- [ ] Add `https://github.com/areen-at/AI-agents-HW6` as `origin`.
- [ ] Verify `git remote -v` shows the expected fetch and push URLs.
- [ ] Verify GitHub authentication before the first push.
- [ ] Fetch remote history before creating the first shared commit when the remote is non-empty.
- [ ] Avoid overwriting remote history.
- [ ] Reconcile existing remote files through an ordinary merge or agreed approach.
- [ ] Perform the same informational pre-push summary and automatic push for repository setup changes.
