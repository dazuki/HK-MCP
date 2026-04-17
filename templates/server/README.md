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

## Konfiguration

- `mcp-config.toml.example` - mall för server-specifik konfiguration (committas)
- `mcp-config.toml` - din lokala konfiguration (gitignorerad)
- Globala defaults ligger i `settings.toml` i monorepo-roten
- Prioritet: CLI > `HK_*`-env > `mcp-config.toml` > `settings.toml` > defaults
