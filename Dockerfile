# syntax=docker/dockerfile:1.7
#
# Gemensam Dockerfile för alla HK MCP-servrar. Bygg med:
#   docker build --build-arg SERVER=skolverket -t hk-mcp/skolverket .
#
# En image per server. uv workspace syncar bara det angivna paketet plus
# dess beroenden (inkl. hk-core), så varje image innehåller minimalt.

# Pinnade versioner för reproducerbara builds.
ARG PYTHON_IMAGE=python:3.12.13-slim-bookworm

# ---------- Builder ----------
FROM ${PYTHON_IMAGE} AS builder

# Pinnad uv-version. Uppdatera medvetet, inte via latest.
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

ARG SERVER
RUN test -n "$SERVER" || (echo "ERROR: --build-arg SERVER=<namn> krävs" && exit 1)

# Workspace-metadata + lock
COPY pyproject.toml uv.lock ./

# Delat kärnbibliotek (hk-core)
COPY libs/ libs/

# Alla servrars pyproject.toml behövs så workspace-resolvern hittar medlemmarna
# som uv.lock refererar till, men bara target-serverns source kopieras (bättre
# layer-cache - ändringar i andra servrar invaliderar inte denna image).
COPY servers/ servers-meta/
RUN mkdir -p servers && \
    for d in servers-meta/*/; do \
        name=$(basename "$d"); \
        mkdir -p "servers/$name"; \
        cp "$d/pyproject.toml" "servers/$name/pyproject.toml"; \
        mkdir -p "servers/$name/src"; \
    done && \
    rm -rf servers-meta

# Target-serverns fullständiga källkod
COPY servers/${SERVER}/ servers/${SERVER}/

# --no-editable = kopiera källkod in i site-packages istället för .pth-länk.
# Krävs för att .venv ska vara flyttbar mellan build-stages.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package "${SERVER}" --no-dev --no-editable

# ---------- Runtime ----------
FROM ${PYTHON_IMAGE} AS runtime

ARG SERVER
ENV HK_SERVER_NAME=${SERVER} \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HK_TRANSPORT=streamable-http \
    HK_HOST=0.0.0.0 \
    HK_PORT=8000

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

# Kör som icke-root
RUN useradd --system --uid 1000 --no-create-home mcp
USER mcp

EXPOSE 8000

# Entry-scriptet från serverns [project.scripts] hamnar i .venv/bin/
# och matchar paketnamnet (skolverket, kolada, time, scb).
CMD ["/bin/sh", "-c", "exec \"$HK_SERVER_NAME\""]
