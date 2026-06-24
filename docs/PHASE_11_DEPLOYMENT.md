# Phase 11 Deployment Verification

## Result

PASS - Both role servers are packaged, hardened, and deployed as separate Render Web Services.
Their distinct public HTTPS URLs pass authentication, health, identity, protocol, capability,
six-game remote execution, and offline replay checks.

## Public endpoints

- Cop: `https://salareen-cop.onrender.com/mcp`
- Thief: `https://salareen-thief.onrender.com/mcp`

The endpoints are intentionally public metadata. Their different Bearer tokens remain only in
Render's private environment configuration and the ignored local `.env`.

## Completed

- Selected Cloudflare Tunnel for outbound-only HTTPS exposure.
- Added one reusable container image parameterized by `MCP_ROLE`.
- Added distinct reproducible Cop and Thief start commands.
- Tokens come only from `COP_MCP_TOKEN` and `THIEF_MCP_TOKEN`.
- `--require-auth` fails startup when the matching secret is missing.
- GET and POST operations require the Bearer token when authentication is configured.
- Missing, wrong, and cross-role tokens return HTTP 401 without server internals.
- Request bodies default to 64 KiB maximum.
- Per-client request rate defaults to 1,000 per minute, enough for a six-game series while still
  bounding abuse.
- Unexpected exceptions return a generic internal error.
- Ports, URLs, tokens, timeouts, logging level, request size, and rate limit remain configurable.
- Local policy dependencies stay behind localhost; Cloudflare connectors make outbound connections.
- TLS terminates at Cloudflare for public hostnames.
- `.dockerignore` excludes credentials, tokens, reports, artifacts, virtual environments, and PDFs.
- Production configuration validation requires two different HTTPS URLs.
- Token rotation/revocation, firewall behavior, named tunnel setup, and Docker commands are documented.

## Live verification

Observed on June 24, 2026:

- both authenticated `/mcp/health` requests returned status `ok`;
- Cop `/mcp/identity` returned role `cop`;
- Thief `/mcp/identity` returned role `thief`;
- both identities and capabilities reported protocol version `1.0`;
- both capability documents included `decide`;
- missing-token requests returned HTTP 401;
- using the other role's token returned HTTP 401;
- correct private tokens were accepted;
- a complete remote internal series produced exactly six valid games;
- all six games ended in Thief survival at move limit;
- totals were Cop `30`, Thief `60`;
- no technical attempt was invalidated;
- the event log contained 312 committed snapshots;
- every applied action contained request and correlation IDs; and
- offline replay rendered all 312 snapshots without any MCP call.

## Earlier provider attempt

`cloudflared` version `2026.6.1` was downloaded from the official Cloudflare GitHub release.
Two authenticated localhost role servers started successfully. Two anonymous Quick Tunnels were
requested with separate origins.

Observed:

- the Thief hostname published DNS initially;
- three different Cop Quick Tunnel hostnames were assigned but never published DNS;
- later the Thief tunnel returned Cloudflare error 1033, indicating the temporary edge route was no
  longer usable;
- therefore identity, authorized decision, six-game remote series, and replay gates could not be run
  through a stable pair;
- all temporary server and tunnel processes were stopped after the failed smoke test.

No secret token or Cloudflare diagnostic file was committed. Render was selected as the working
free provider after the anonymous tunnel failure.

## Availability

Render free services may sleep after inactivity and cold-start on the next request. Both services
must remain configured in the Render account for the assessment/bonus window. A `401` request can
wake a sleeping service, but authorized health probes should be used before a timed match.

## Verification commands

- `$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'`
- `python -m compileall -q main.py src tests`
- `python -m pip check`
- start each server with `--require-auth`
- probe missing/wrong/correct Bearer tokens
- run `python main.py --mode internal --config <remote-config> --local-mcp --quiet`
- replay the generated event log without MCP calls

All commands passed for the Render endpoints.
