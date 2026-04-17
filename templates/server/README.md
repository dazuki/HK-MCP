# Mall för ny MCP-server

Kopiera denna mapp till `servers/<namn>/` och ersätt följande identifierare:

| Platshållare | Byt ut till |
|---|---|
| `hk-example` (paketnamn i `pyproject.toml`) | `<namn>` eller `hk-<namn>` |
| `hk_example` (Python-modul) | modulnamn med understreck |
| `"HK Exempel"` (server.py) | serverns visningsnamn |

## Steg

```bash
cp -r templates/server servers/<namn>
cd servers/<namn>
# Redigera pyproject.toml, src/<modul>/server.py
# Byt katalognamn: mv src/hk_example src/<modul>
cp mcp-config.toml.example mcp-config.toml  # anpassa vid behov
uv sync
uv run <namn>
```

Workspace-roten plockar upp nya `servers/*` automatiskt vid nästa `uv sync`.

Lägg även till serverns sökväg i rotens `pyproject.toml` under
`[tool.pyright]` → `extraPaths` så pyright/Pylance hittar modulen:

```toml
extraPaths = [
    "libs/core/src",
    "servers/<namn>/src",
]
```

## Konfiguration

- `mcp-config.toml.example` - mall för server-specifik konfiguration (committas)
- `mcp-config.toml` - din lokala konfiguration (gitignorerad)
- Globala defaults ligger i `settings.toml` i monorepo-roten
- Prioritet: CLI > `HK_*`-env > `mcp-config.toml` > `settings.toml` > defaults

`package_file=__file__` måste skickas till `create_server()` för att
`mcp-config.toml` och `settings.toml` ska upptäckas. Mallen gör redan det.

## Automatisk dokumentation

Vid HTTP-transport (`streamable-http` eller `sse`) exponerar `hk-core`
följande endpoints utöver själva `/mcp`:

- `GET /` och `GET /docs` - HTML-dokumentation över registrerade verktyg,
  resurser och prompts. Genereras live från FastMCP-introspektion, så
  docstrings och type hints räcker - ingen separat byggsteg behövs.
- `GET /docs.json` - maskinläsbar JSON med samma innehåll.
- `GET /static/*` - Bulma-CSS för HTML-sidan.
