"""Fabriksfunktion för att skapa MCP-servrar med gemensam konfiguration."""

import argparse
import logging
import signal
import sys
import time
from functools import wraps
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.transport_security import TransportSecuritySettings

from hk_core.config import ServerConfig

logger = get_logger("hk_core")


def _reconfigure_logging() -> None:
    """Ersätt FastMCP:s RichHandler med en utan path-kolumn.

    FastMCP anropar configure_logging() i __init__ och sätter upp en RichHandler
    som visar filnamn:radnummer. För uvicorn/h11 pekar detta på interna filer
    (h11_impl.py, on.py) vilket bara är brus. show_path=False tar bort kolumnen.
    """
    try:
        from rich.console import Console
        from rich.logging import RichHandler
    except ImportError:
        return

    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, RichHandler):
            root.removeHandler(handler)

    root.addHandler(
        RichHandler(
            console=Console(stderr=True),
            rich_tracebacks=True,
            show_path=False,
        )
    )


def _parse_args() -> dict[str, Any]:
    """Parsa CLI-argument för MCP-servrar."""
    parser = argparse.ArgumentParser(description="HK MCP-server")
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "sse", "streamable-http"],
        help="Transportprotokoll (standard: stdio)",
    )
    parser.add_argument(
        "--host",
        help="Värdadress (standard: 0.0.0.0 - lyssnar på alla interface)",
    )
    parser.add_argument(
        "--forwarded-allow-ips",
        help="Betrodda proxy-IP:n för X-Forwarded-*-headers (standard: 127.0.0.1, '*' för alla)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        help="Port för HTTP-transporter (standard: 8000)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Loggnivå (standard: INFO)",
    )
    parser.add_argument(
        "--allowed-hosts",
        nargs="+",
        help="Tillåtna Host-headers (t.ex. '*.ngrok-free.app' eller '*' för alla)",
    )
    parser.add_argument(
        "--allowed-origins",
        nargs="+",
        help="Tillåtna Origin-headers (t.ex. 'https://mcp.klient.se' eller '*' för alla)",
    )
    args = parser.parse_args()
    return {k: v for k, v in vars(args).items() if v is not None}


def _build_transport_security(config: ServerConfig) -> TransportSecuritySettings | None:
    """Skapa TransportSecuritySettings utifrån allowed_hosts och allowed_origins."""
    if not config.allowed_hosts and not config.allowed_origins:
        return None
    if "*" in config.allowed_hosts or "*" in config.allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        allowed_hosts=config.allowed_hosts,
        allowed_origins=config.allowed_origins,
    )


_LOCALHOST_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _validate_config(config: ServerConfig) -> None:
    """Logga varningar för misstänkta konfigurationskombinationer."""
    if config.transport == "stdio":
        return

    is_public_bind = config.host not in _LOCALHOST_HOSTS
    has_host_allowlist = bool(config.allowed_hosts)
    has_origin_allowlist = bool(config.allowed_origins)
    wildcard_hosts = "*" in config.allowed_hosts
    wildcard_origins = "*" in config.allowed_origins

    if is_public_bind and not has_host_allowlist and not wildcard_hosts:
        logger.warning(
            "HTTP-transport bunden till %s men allowed_hosts är tom. "
            "MCP avvisar alla Host-headers utom localhost. "
            "Sätt allowed_hosts i mcp-config.toml till din proxy-domän och/eller LAN-IP.",
            config.host,
        )

    if is_public_bind and not has_origin_allowlist and not wildcard_origins:
        logger.warning(
            "HTTP-transport bunden till %s men allowed_origins är tom. "
            "Webbaserade MCP-klienter kan blockeras av DNS rebinding-skyddet. "
            "Sätt allowed_origins i mcp-config.toml till betrodda klientdomäner.",
            config.host,
        )

    if is_public_bind and config.forwarded_allow_ips == "127.0.0.1":
        logger.warning(
            "forwarded_allow_ips=127.0.0.1 men host=%s. "
            "Om du kör bakom en reverse proxy på en annan host, "
            "sätt forwarded_allow_ips till proxyns IP så X-Forwarded-*-headers respekteras.",
            config.host,
        )

    if wildcard_hosts or wildcard_origins:
        logger.warning(
            "Wildcard '*' är satt i allowed_hosts/allowed_origins. "
            "DNS rebinding-skyddet är helt avstängt - OK för stdio eller utveckling, "
            "rekommenderas inte för produktion med HTTP."
        )


def _wrap_call_tool(server: FastMCP) -> None:
    """Wrappa _tool_manager.call_tool för att logga alla verktygsanrop.

    FastMCP registrerar sin call_tool-metod i _setup_handlers() vid __init__,
    så vi måste wrappa _tool_manager.call_tool som anropas inifrån den.
    """
    tool_manager = server._tool_manager
    original = tool_manager.call_tool

    @wraps(original)
    async def logged_call_tool(name: str, arguments: dict[str, Any], **kwargs: Any) -> Any:
        args_summary = ", ".join(f"{k}={v!r}" for k, v in arguments.items()) if arguments else ""
        logger.info("-> %s(%s)", name, args_summary)
        start = time.perf_counter()
        try:
            result = await original(name, arguments, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("<- %s OK (%.0f ms)", name, elapsed)
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("<- %s FEL: %s (%.0f ms)", name, exc, elapsed)
            raise

    tool_manager.call_tool = logged_call_tool  # type: ignore[method-assign]


def create_server(
    name: str,
    instructions: str | None = None,
    config: ServerConfig | None = None,
    package_file: str | None = None,
    **kwargs: Any,
) -> FastMCP:
    """Skapa en MCP-server med standardkonfiguration för HK.

    Args:
        name: Serverns namn.
        instructions: Valfria instruktioner till AI-modellen.
        config: Valfri konfiguration. Skapas automatiskt om den inte anges.
        package_file: Skicka `__file__` från det anropande modulen för att
            aktivera upptäckt av `mcp-config.toml` (server) och `settings.toml`
            (global) uppåt i katalogträdet. Utan detta används bara miljövariabler
            och standardvärden.
        **kwargs: Extra argument till FastMCP.

    Returns:
        En konfigurerad FastMCP-instans.
    """
    if config is None:
        config = ServerConfig.load(package_file) if package_file else ServerConfig()

    transport_security = _build_transport_security(config)

    server = FastMCP(
        name,
        instructions=instructions,
        host=config.host,
        port=config.port,
        log_level=config.log_level,
        transport_security=transport_security,
        **kwargs,
    )

    server._hk_config = config  # type: ignore[attr-defined]
    _wrap_call_tool(server)
    _reconfigure_logging()

    return server


def run_server(server: FastMCP) -> None:
    """Starta en MCP-server med konfigurerad transport.

    CLI-argument överskrider miljövariabler som överskrider standardvärden.
    Prioritet: --argument > HK_VARIABEL > standardvärde
    """
    cli_args = _parse_args()
    config: ServerConfig = getattr(server, "_hk_config", ServerConfig())

    if "transport" in cli_args:
        config.transport = cli_args["transport"]
    if "host" in cli_args:
        config.host = cli_args["host"]
        server.settings.host = cli_args["host"]
    if "port" in cli_args:
        config.port = cli_args["port"]
        server.settings.port = cli_args["port"]
    if "log_level" in cli_args:
        config.log_level = cli_args["log_level"]
    if "forwarded_allow_ips" in cli_args:
        config.forwarded_allow_ips = cli_args["forwarded_allow_ips"]
    if "allowed_hosts" in cli_args:
        config.allowed_hosts = cli_args["allowed_hosts"]
    if "allowed_origins" in cli_args:
        config.allowed_origins = cli_args["allowed_origins"]
    if "allowed_hosts" in cli_args or "allowed_origins" in cli_args:
        server.settings.transport_security = _build_transport_security(config)

    def _shutdown(sig: int, frame: Any) -> None:
        logger.info("Stänger ner '%s'...", server.name)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "Startar '%s' (transport=%s, host=%s, port=%d)",
        server.name, config.transport, config.host, config.port,
    )

    _validate_config(config)

    try:
        if config.transport in ("streamable-http", "sse"):
            _run_http(server, config)
        else:
            server.run(transport=config.transport)
    except SystemExit:
        pass


def _run_http(server: FastMCP, config: ServerConfig) -> None:
    """Kör HTTP-transport med CORS-middleware så webbläsarklienter kan ansluta."""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    from hk_core.docs import build_docs_routes

    app = (
        server.streamable_http_app()
        if config.transport == "streamable-http"
        else server.sse_app()
    )
    for route in build_docs_routes(server):
        app.router.routes.append(route)

    wrapped = CORSMiddleware(
        app,
        allow_origins=config.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    uvicorn.run(
        wrapped,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
        log_config=None,
        access_log=config.access_log,
        proxy_headers=True,
        forwarded_allow_ips=config.forwarded_allow_ips,
    )
