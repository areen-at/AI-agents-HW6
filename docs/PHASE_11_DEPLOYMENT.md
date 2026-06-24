# Phase 11 Deployment Verification

## Result

IMPLEMENTATION PASS / PUBLIC PAIR BLOCKED - Both role servers are packaged and hardened for remote
deployment, but the exit gate requiring two simultaneously reachable public URLs is not complete.
Anonymous Cloudflare Quick Tunnels repeatedly failed to publish DNS for the Cop hostname. A durable
Cloudflare named tunnel (or equivalent provider account) is required to finish the live pair.

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

## Live attempt

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

No secret token or Cloudflare diagnostic file was committed.

## Remaining live tasks

- T0304: create two durable public HTTPS routes/hostnames.
- T0314-T0317: probe both endpoints and verify identity, protocol, unauthorized, and authorized calls.
- T0318: run a complete remote six-game internal series.
- T0319: replay the remote results locally.
- T0321: keep both endpoints available for the required assessment/bonus window.

## Required user/provider input

Provide access to a Cloudflare account with an active domain, or equivalent hosting credentials.
Then create a named tunnel, configure two hostnames using
`deployment/cloudflared.example.yml`, keep the tunnel credential file outside Git, and rerun the
remaining probes.

## Verification commands

- `$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_*.py'`
- `python -m compileall -q main.py src tests`
- `python -m pip check`
- start each server with `--require-auth`
- probe missing/wrong/correct Bearer tokens
- run `python main.py --mode internal --config <remote-config> --local-mcp --quiet`
- replay the generated event log without MCP calls
