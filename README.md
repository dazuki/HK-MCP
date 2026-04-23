## Konfigurera en server

Två konfigurationsnivåer:

1. **Globala defaults**: kopiera rotens `settings.toml.example` till
   `settings.toml`. Gäller för alla servrar.
2. **Per server**: kopiera `templates/server/mcp-config.toml.example`
   till `servers/<namn>/mcp-config.toml` och anpassa.

Bägge är gitignorerade. Prioritet (högst först):

```
CLI-argument > HK_*-miljövariabler > servers/<namn>/mcp-config.toml
             > settings.toml > inbyggda defaults
```

### Minsta konfiguration för HTTP-transport

```toml
# servers/<namn>/mcp-config.toml
transport = "streamable-http"
port = 8000
allowed_hosts = ["<namn>.mcp.exempel.se", "127.0.0.1"]
allowed_origins = ["https://klient.exempel.se"]
auth_tokens = ["lång-slumpmässig-sträng-minst-32-tecken"]
```

**Bearer-token rekommenderas vid publik exponering.** Utan
`auth_tokens` loggas en varning och alla som når `/mcp` kan använda
verktygen.

## Köra en server

Varje server registrerar en `main`-entry point med sitt paketnamn:

```bash
# Startar med konfiguration från mcp-config.toml
uv run <namn>

# Tvinga stdio-transport (för lokal MCP-klient som Claude Desktop)
uv run <namn> --transport stdio

# Binda specifik port och auth-token
uv run <namn> --transport streamable-http --port 8000 \
  --auth-tokens "hemlig-token"
```

Alla flaggor kan även sättas via miljövariabler med prefix `HK_`
(t.ex. `HK_PORT=8000`, `HK_AUTH_TOKENS="a,b"`).

## Docker

En gemensam `Dockerfile` i roten parametriseras via `--build-arg SERVER=<namn>`
och producerar en image per server. uv workspace syncar bara det valda paketet
plus dess beroenden (inkl. `hk-core`), så varje image blir ~170 MB.

Kräver `docker buildx` (BuildKit) för cache-mount under `uv sync`.

### Bygga en enskild image

```bash
docker build --build-arg SERVER=skolverket -t hk-mcp/skolverket:latest .
```

Giltiga `SERVER`-värden matchar katalognamnen under `servers/`
(`skolverket`, `kolada`, `time`, `scb`, ...).

### Köra alla servrar via compose

`docker-compose.yml` bygger och kör alla servrar med healthcheck mot
`/docs.json`:

```bash
docker compose build                     # bygg alla images
docker compose up -d                     # starta alla
docker compose up -d --build skolverket  # bara en server
docker compose logs -f skolverket
docker compose down
```

Standardportar: `3070` skolverket, `3071` kolada, `3072` time, `3073` scb.
Ändra i `docker-compose.yml` vid portkonflikt.

### Konfiguration via miljövariabler

Containrarna läser **inte** `settings.toml`/`mcp-config.toml` - all konfiguration
sker via `HK_*`-env vars i compose-filen. Listvärden måste vara JSON-strängar:

```yaml
environment:
  HK_ALLOWED_HOSTS: '["mcp.example.org","127.0.0.1"]'
  HK_AUTH_TOKENS: '["lång-slumpmässig-token"]'
  HK_FORWARDED_ALLOW_IPS: "172.16.0.0/12"
```

Auth-tokens läses från miljövariabler på värden (t.ex. via `.env`-fil som
docker compose plockar upp automatiskt). Checka **aldrig** in `.env` i git:

```bash
# .env (gitignorerad)
SKOLVERKET_AUTH_TOKENS=["lång-slumpmässig-token"]
KOLADA_AUTH_TOKENS=["annan-token"]
```

### Reverse proxy

Images innehåller ingen TLS-terminering. Sätt upp nginx/Caddy/Traefik på värden
som terminerar HTTPS och vidarebefordrar till containrarnas exponerade portar.
Kom ihåg att lägga proxyns publika domän i `HK_ALLOWED_HOSTS` (DNS rebinding-
skydd) och proxyns IP i `HK_FORWARDED_ALLOW_IPS` (för korrekt client-IP i loggar).

### Färdigbyggda images från GHCR

En GitHub Actions-workflow ([.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml))
bygger och pushar alla servrar till GitHub Container Registry vid push till `main`
och vid git-taggar `v*.*.*`. Images publiceras som:

```
ghcr.io/<ägare>/hk-mcp-skolverket:latest
ghcr.io/<ägare>/hk-mcp-kolada:latest
ghcr.io/<ägare>/hk-mcp-time:latest
ghcr.io/<ägare>/hk-mcp-scb:latest
```

Driftmiljöer som inte ska bygga lokalt (t.ex. Windows Server) kan då kopiera
`docker-compose.yml`, byta ut `build:`-block mot `image:` och köra
`docker compose pull && docker compose up -d`:

```yaml
services:
  skolverket:
    image: ghcr.io/<ägare>/hk-mcp-skolverket:latest
    # ta bort build:-blocket
    ...
```

**Första gången** paketen publiceras är de privata. Gå till repots
`Packages`-flik på GitHub och ändra synligheten till `Public` om de ska
kunna dras utan autentisering.

## Använda servrarna från en MCP-klient

### stdio (lokal)

I t.ex. Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "<namn>": {
      "command": "uv",
      "args": ["run", "--project", "/absolut/sökväg/till/hk-mcp",
               "<namn>", "--transport", "stdio"]
    }
  }
}
```

### HTTP (remote)

Klienter som stöder `streamable-http`:

```
URL:    https://<namn>.mcp.exempel.se/mcp
Header: Authorization: Bearer <din-token>
```

## Inbyggd dokumentation

Vid HTTP-transport exponerar `hk-core` live-genererad dokumentation
utöver själva `/mcp`-endpointen:

- `GET /` eller `GET /docs` - HTML-översikt av verktyg, resurser, prompts
- `GET /docs.json` - samma innehåll som JSON

Dokumentationen genereras från docstrings och type hints via FastMCP-
introspektion - inget byggsteg behövs. Docs-endpoints kräver aldrig
auth (så operatörer kan inspektera i webbläsaren), medan `/mcp` och
övriga routes skyddas av `auth_tokens` när satt.

## Projektstruktur

```
hk-mcp/
├── libs/
│   └── core/               # hk-core: delad MCP-runtime (create_server, run_server)
├── servers/
│   └── <namn>/             # en mapp per MCP-server (workspace-medlem)
├── templates/
│   └── server/             # mall för ny server (exkluderad från workspace)
├── settings.toml.example   # globala defaults
└── pyproject.toml          # workspace-koordinator (inget rotpaket)
```

## Lägga till en ny server

Se [templates/server/README.md](templates/server/README.md). Kort version:

```bash
cp -r templates/server servers/<namn>
# Ersätt hk-example/hk_example-identifierare, byt src/-modulnamn
uv sync
uv run <namn>
```

Uppdatera även rotens `pyproject.toml` under `[tool.pyright].extraPaths`
så att editorn hittar modulen.
