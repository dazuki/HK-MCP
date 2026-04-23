# Mall för ny MCP-server

Kopiera denna mapp till `servers/<namn>/` och ersätt följande identifierare:

| Platshållare | Byt ut till |
|---|---|
| `hk-example` (paketnamn + `[project.scripts]`-nyckel i `pyproject.toml`) | `<namn>` eller `hk-<namn>` |
| `hk_example` (Python-modul, `src/`-katalog + `packages`-post) | modulnamn med understreck |
| `"HK Exempel"` (server.py, `name=`-argument) | serverns visningsnamn |

**Namnkonvention**: prefix `hk-` endast för servrar specifika för
Herrljunga kommun. Generella servrar (t.ex. externa API:er som
Skolverket, Kolada) namnges utan prefix. En MCP-server per extern
tjänst - samla alla API:er från samma källa.

## Steg

```bash
cp -r templates/server servers/<namn>
cd servers/<namn>
# Redigera pyproject.toml, src/<modul>/server.py
# Byt katalognamn: mv src/hk_example src/<modul>
# Radera README.md - den tillhör mallen, inte servern
rm README.md
cp ../../templates/server/mcp-config.toml.example mcp-config.toml  # anpassa
uv sync
uv run <namn>   # namnet = [project.scripts]-nyckeln i pyproject.toml
```

`mcp-config.toml.example` behålls endast i `templates/server/` -
servrarna committar bara sin egen (gitignorerade) `mcp-config.toml`.

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

- `templates/server/mcp-config.toml.example` - delad mall (committas)
- `mcp-config.toml` - din lokala konfiguration i `servers/<namn>/` (gitignorerad)
- Globala defaults ligger i `settings.toml` i monorepo-roten
- Prioritet: CLI > `HK_*`-env > `mcp-config.toml` > `settings.toml` > defaults

`package_file=__file__` måste skickas till `create_server()` för att
`mcp-config.toml` och `settings.toml` ska upptäckas. Mallen gör redan det.

## Autentisering

Vid HTTP-transport kan du kräva en Bearer-token genom att sätta
`auth_tokens` i `mcp-config.toml`:

```toml
auth_tokens = ["lång-slumpmässig-sträng"]
```

Flera tokens tillåts samtidigt för rotation utan downtime. Klienter
skickar `Authorization: Bearer <token>`. Kan även sättas via
`HK_AUTH_TOKENS` eller `--auth-tokens`. Tom lista = öppen server.

**Rekommenderas starkt vid publik exponering.** Om servern binds till
annat än localhost utan `auth_tokens` loggas en varning vid start.

Docs-endpoints (`/`, `/docs`, `/docs.json`, `/static/*`) kräver
aldrig auth - de är avsedda för snabb browserinspektion. `/mcp` och
övriga routes skyddas när `auth_tokens` är satt.

## Automatisk dokumentation

Vid HTTP-transport (`streamable-http` eller `sse`) exponerar `hk-core`
följande endpoints utöver själva `/mcp`:

- `GET /` och `GET /docs` - HTML-dokumentation över registrerade verktyg,
  resurser och prompts. Genereras live från FastMCP-introspektion, så
  docstrings och type hints räcker - ingen separat byggsteg behövs.
- `GET /docs.json` - maskinläsbar JSON med samma innehåll.
- `GET /static/*` - Bulma-CSS för HTML-sidan.
