# Phase 11 deployment

The selected deployment boundary is Cloudflare Tunnel. The connector makes outbound-only
connections to Cloudflare, so ports 8001 and 8002 remain bound to localhost and no inbound firewall
rule is required. Cloudflare terminates public HTTPS and forwards each hostname to its role server.

For a durable assessment window, create one named tunnel with two DNS hostnames using
`cloudflared.example.yml`. Quick Tunnels may be used only for a temporary smoke test because their
random `trycloudflare.com` URLs last only while the connector process runs.

## Required secrets

Set different high-entropy values outside Git:

```powershell
$env:COP_MCP_TOKEN='<random token>'
$env:THIEF_MCP_TOKEN='<different random token>'
```

Rotate a token by changing the environment value and restarting only that role server. Revoke a
token by stopping the server, replacing/unsetting it, and restarting. Never put tokens in command
arguments, config files, tunnel YAML, reports, logs, or Git.

## Reproducible local production commands

```powershell
$env:PYTHONPATH='src'
python -m ai_agents_hw6.mcp_servers.http_server --role cop --host 127.0.0.1 --port 8001 --require-auth
python -m ai_agents_hw6.mcp_servers.http_server --role thief --host 127.0.0.1 --port 8002 --require-auth
```

The commands read `COP_MCP_TOKEN` and `THIEF_MCP_TOKEN` respectively. Startup fails when a required
token is missing. Request size and rate limits default to 64 KiB and 1,000 requests/minute and can
be changed with `--max-request-bytes` and `--rate-limit-per-minute`.

## Containers

```powershell
docker build --build-arg MCP_ROLE=cop -t salareen-cop .
docker build --build-arg MCP_ROLE=thief -t salareen-thief .
docker run --rm -p 127.0.0.1:8001:8080 -e COP_MCP_TOKEN salareen-cop
docker run --rm -p 127.0.0.1:8002:8080 -e THIEF_MCP_TOKEN salareen-thief
```

## Named tunnel

Install `cloudflared`, authenticate to the intended Cloudflare account, create a named tunnel, route
two distinct DNS hostnames, and place the real tunnel credential file outside the repository.

```powershell
cloudflared tunnel login
cloudflared tunnel create salareen-ai-agents
cloudflared tunnel route dns salareen-ai-agents cop.example.com
cloudflared tunnel route dns salareen-ai-agents thief.example.com
cloudflared tunnel --config C:\private\cloudflare\config.yml run salareen-ai-agents
```

Verify `/mcp/health`, `/mcp/identity`, `/mcp/capabilities`, and `/mcp/decide` with the matching
Bearer token. Requests with no token or the wrong role token must return HTTP 401.
