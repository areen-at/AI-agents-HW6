FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8080 \
    MCP_MAX_REQUEST_BYTES=65536 \
    MCP_RATE_LIMIT_PER_MINUTE=1000

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

ARG MCP_ROLE
ENV MCP_ROLE=${MCP_ROLE}

CMD ["sh", "-c", "python -m ai_agents_hw6.mcp_servers.http_server --role \"$MCP_ROLE\" --host \"$MCP_HOST\" --port \"$MCP_PORT\" --require-auth --max-request-bytes \"$MCP_MAX_REQUEST_BYTES\" --rate-limit-per-minute \"$MCP_RATE_LIMIT_PER_MINUTE\""]
