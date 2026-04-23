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
