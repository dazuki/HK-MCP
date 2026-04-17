"""Generera dokumentation för registrerade verktyg, resurser och prompts.

Introspekterar en FastMCP-instans och exponerar HTML + JSON-endpoints som
monteras på Starlette-appen vid HTTP-transport.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

_ARGS_LINE_RE = re.compile(r"^(\s+)(\w+): (.+)$", re.MULTILINE)

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import BaseRoute, Mount, Route
from starlette.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"


def collect_docs(server: FastMCP) -> dict[str, Any]:
    """Samla metadata från FastMCP:s interna managers."""
    tools = [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.parameters,
        }
        for t in server._tool_manager.list_tools()
    ]

    resources = []
    for r in server._resource_manager.list_resources():
        resources.append({
            "uri": str(r.uri),
            "name": r.name,
            "description": r.description or "",
            "mime_type": r.mime_type,
        })
    for t in server._resource_manager.list_templates():
        resources.append({
            "uri": t.uri_template,
            "name": t.name,
            "description": t.description or "",
            "mime_type": t.mime_type,
            "template": True,
        })

    prompts = [
        {
            "name": p.name,
            "description": p.description or "",
            "arguments": [
                {
                    "name": a.name,
                    "description": a.description or "",
                    "required": a.required,
                }
                for a in (p.arguments or [])
            ],
        }
        for p in server._prompt_manager.list_prompts()
    ]

    return {
        "server": server.name,
        "instructions": server.instructions or "",
        "tools": tools,
        "resources": resources,
        "prompts": prompts,
    }


BULMA_HREF = "./static/bulma.min.css"


def _render_schema(schema: dict[str, Any]) -> str:
    """Rendera ett JSON-schema som Bulma-tabell över parametrar."""
    props = schema.get("properties", {})
    if not props:
        return "<p class='has-text-grey is-italic'>Inga parametrar.</p>"

    required = set(schema.get("required", []))
    rows = []
    for name, spec in props.items():
        type_ = spec.get("type") or spec.get("anyOf") or spec.get("oneOf") or "?"
        if isinstance(type_, list):
            type_ = " | ".join(str(t) for t in type_)
        desc = spec.get("description", "")
        default = spec.get("default", "")
        req_tag = (
            "<span class='tag is-danger is-light'>obligatorisk</span>"
            if name in required
            else "<span class='tag is-light'>valfri</span>"
        )
        default_cell = (
            f"<code>{html.escape(str(default))}</code>" if default != "" else ""
        )
        rows.append(
            f"<tr><td><code>{html.escape(name)}</code></td>"
            f"<td><code>{html.escape(str(type_))}</code></td>"
            f"<td>{req_tag}</td>"
            f"<td>{default_cell}</td>"
            f"<td>{html.escape(str(desc))}</td></tr>"
        )

    return (
        "<table class='table is-bordered is-striped is-hoverable is-fullwidth is-size-7'>"
        "<thead><tr>"
        "<th>Namn</th><th>Typ</th><th>Krav</th><th>Standard</th><th>Beskrivning</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _render_instructions(instructions: str) -> str:
    """Rendera systemprompten som en tydligt märkt notisruta."""
    if not instructions.strip():
        return ""
    return (
        "<article class='message'>"
        "<div class='message-header'>"
        "<p>Instruktioner till AI-assistenten</p>"
        "</div>"
        "<div class='message-body'>"
        "<p class='is-size-7 has-text-grey mb-2'>"
        "Följande systemprompt skickas till AI-modellen när den ansluter till "
        "servern. Den styr hur modellen tolkar och använder verktygen nedan."
        "</p>"
        f"<div class='content'>{instructions}</div>"
        "</div>"
        "</article>"
    )


def _format_tool_description(desc: str) -> str:
    """Escapa beskrivning och fetmarkera argumentnamn i Args:-blocket."""
    escaped = html.escape(desc)
    bolded = _ARGS_LINE_RE.sub(r"\1<strong>\2:</strong> \3", escaped)
    return bolded.replace("\n", "<br>")


def _render_html(data: dict[str, Any]) -> str:
    """Rendera komplett HTML-sida med Bulma-styling."""
    tools_html = []
    for tool in data["tools"]:
        name = html.escape(tool["name"])
        desc = _format_tool_description(tool["description"])
        tools_html.append(
            f"<div class='box' id='tool-{name}'>"
            f"<h3 class='title is-5'><code>{name}</code></h3>"
            f"<div class='content'>{desc}</div>"
            f"{_render_schema(tool['input_schema'])}"
            f"</div>"
        )

    resources_html = ""
    if data["resources"]:
        items = "".join(
            f"<li><code>{html.escape(r['uri'])}</code> - "
            f"<strong>{html.escape(r['name'] or '')}</strong>: "
            f"{html.escape(r['description'])}</li>"
            for r in data["resources"]
        )
        resources_html = (
            f"<h2 class='title is-4 mt-5'>Resurser "
            f"<span class='tag is-info'>{len(data['resources'])}</span></h2>"
            f"<div class='content'><ul>{items}</ul></div>"
        )

    prompts_html = ""
    if data["prompts"]:
        items = "".join(
            f"<li><code>{html.escape(p['name'])}</code> - "
            f"{html.escape(p['description'])}</li>"
            for p in data["prompts"]
        )
        prompts_html = (
            f"<h2 class='title is-4 mt-5'>Prompts "
            f"<span class='tag is-info'>{len(data['prompts'])}</span></h2>"
            f"<div class='content'><ul>{items}</ul></div>"
        )

    instructions = html.escape(data["instructions"]).replace("\n", "<br>")
    server_name = html.escape(data["server"])

    toc_items = "".join(
        f"<li><a href='#tool-{html.escape(t['name'])}'>"
        f"<code>{html.escape(t['name'])}</code></a></li>"
        for t in data["tools"]
    )

    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{server_name} - MCP-dokumentation</title>
<link rel="stylesheet" href="{BULMA_HREF}">
<script>
  (function () {{
    var root = document.documentElement;
    var saved = localStorage.getItem('hk-theme');
    if (saved === 'light' || saved === 'dark') {{
      root.setAttribute('data-theme', saved);
    }}
    var effective = saved === 'light' || saved === 'dark'
      ? saved
      : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    root.classList.toggle('hk-dark', effective === 'dark');
  }})();
</script>
<style>
  .menu {{ position: sticky; top: 1.5rem; max-height: calc(100vh - 3rem); overflow-y: auto; }}
  .menu-list code {{ font-size: 0.8rem; }}
  .theme-switcher {{ position: fixed; top: 1rem; right: 1rem; z-index: 30; }}

  /* is-light-varianter anpassas för mörkt tema - Bulma flippar dem inte själv */
  .hk-dark .tag.is-light,
  .hk-dark .button.is-light {{
    background-color: hsl(var(--bulma-scheme-h), 10%, 20%);
    color: hsl(var(--bulma-scheme-h), 10%, 85%);
  }}
  .hk-dark .tag.is-primary.is-light,
  .hk-dark .button.is-primary.is-light {{
    background-color: hsl(var(--bulma-primary-h), 40%, 18%);
    color: hsl(var(--bulma-primary-h), 80%, 78%);
  }}
  .hk-dark .tag.is-link.is-light,
  .hk-dark .button.is-link.is-light {{
    background-color: hsl(var(--bulma-link-h), 40%, 18%);
    color: hsl(var(--bulma-link-h), 80%, 78%);
  }}
  .hk-dark .tag.is-info.is-light,
  .hk-dark .button.is-info.is-light {{
    background-color: hsl(var(--bulma-info-h), 40%, 18%);
    color: hsl(var(--bulma-info-h), 80%, 78%);
  }}
  .hk-dark .tag.is-success.is-light,
  .hk-dark .button.is-success.is-light {{
    background-color: hsl(var(--bulma-success-h), 40%, 18%);
    color: hsl(var(--bulma-success-h), 80%, 78%);
  }}
  .hk-dark .tag.is-warning.is-light,
  .hk-dark .button.is-warning.is-light {{
    background-color: hsl(var(--bulma-warning-h), 40%, 18%);
    color: hsl(var(--bulma-warning-h), 80%, 78%);
  }}
  .hk-dark .tag.is-danger.is-light,
  .hk-dark .button.is-danger.is-light {{
    background-color: hsl(var(--bulma-danger-h), 40%, 18%);
    color: hsl(var(--bulma-danger-h), 80%, 78%);
  }}
</style>
</head>
<body>
<div class="theme-switcher buttons has-addons are-small">
  <button class="button" data-theme-set="light" title="Ljust tema">Ljust</button>
  <button class="button" data-theme-set="system" title="Systemtema">Auto</button>
  <button class="button" data-theme-set="dark" title="Mörkt tema">Mörkt</button>
</div>
<section class="section">
  <div class="container">
    <h1 class="title is-2">{server_name}</h1>
    <p class="subtitle is-5">MCP-dokumentation</p>
    {_render_instructions(instructions)}
    <div class="buttons">
      <a class="button is-small is-link is-light" href="./docs.json">docs.json</a>
      <a class="button is-small is-info is-light" href="./mcp">/mcp-endpoint</a>
    </div>

    <div class="columns mt-4">
      <aside class="column is-one-quarter">
        <div class="menu">
          <p class="menu-label">
            Verktyg
            <span class="tag is-primary is-light">{len(data['tools'])}</span>
          </p>
          <ul class="menu-list">{toc_items}</ul>
        </div>
      </aside>

      <main class="column">
        {''.join(tools_html)}
        {resources_html}
        {prompts_html}
      </main>
    </div>
  </div>
</section>
<script>
  (function () {{
    var html = document.documentElement;
    var buttons = document.querySelectorAll('[data-theme-set]');

    function current() {{
      var saved = localStorage.getItem('hk-theme');
      return saved === 'light' || saved === 'dark' ? saved : 'system';
    }}

    function mark(active) {{
      buttons.forEach(function (b) {{
        b.classList.toggle('is-primary', b.dataset.themeSet === active);
      }});
    }}

    function effective(choice) {{
      if (choice === 'light' || choice === 'dark') return choice;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }}

    function apply(choice) {{
      if (choice === 'system') {{
        html.removeAttribute('data-theme');
        localStorage.removeItem('hk-theme');
      }} else {{
        html.setAttribute('data-theme', choice);
        localStorage.setItem('hk-theme', choice);
      }}
      html.classList.toggle('hk-dark', effective(choice) === 'dark');
      mark(choice);
    }}

    mark(current());
    buttons.forEach(function (b) {{
      b.addEventListener('click', function () {{ apply(b.dataset.themeSet); }});
    }});

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {{
      if (current() === 'system') html.classList.toggle('hk-dark', e.matches);
    }});
  }})();
</script>
</body>
</html>
"""


def build_docs_routes(server: FastMCP) -> list[BaseRoute]:
    """Bygg Starlette-routes för dokumentation av en FastMCP-server."""

    async def docs_json(_: Request) -> JSONResponse:
        return JSONResponse(collect_docs(server))

    async def docs_html(_: Request) -> HTMLResponse:
        return HTMLResponse(_render_html(collect_docs(server)))

    return [
        Route("/", endpoint=docs_html),
        Route("/docs", endpoint=docs_html),
        Route("/docs.json", endpoint=docs_json),
        Mount("/static", app=StaticFiles(directory=STATIC_DIR), name="static"),
    ]
