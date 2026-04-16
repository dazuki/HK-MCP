"""Fabriksfunktion för att skapa MCP-servrar med gemensam konfiguration."""

import argparse
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
        help="Värdadress (standard: 127.0.0.1)",
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
    args = parser.parse_args()
    return {k: v for k, v in vars(args).items() if v is not None}


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
    **kwargs: Any,
) -> FastMCP:
    """Skapa en MCP-server med standardkonfiguration för HK.

    Args:
        name: Serverns namn.
        instructions: Valfria instruktioner till AI-modellen.
        config: Valfri konfiguration. Skapas automatiskt om den inte anges.
        **kwargs: Extra argument till FastMCP.

    Returns:
        En konfigurerad FastMCP-instans.
    """
    if config is None:
        config = ServerConfig()

    transport_security = None
    if config.allowed_hosts:
        if "*" in config.allowed_hosts:
            transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=False,
            )
        else:
            transport_security = TransportSecuritySettings(
                allowed_hosts=config.allowed_hosts,
            )

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
    if "allowed_hosts" in cli_args:
        config.allowed_hosts = cli_args["allowed_hosts"]
        if "*" in config.allowed_hosts:
            server.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=False,
            )
        else:
            server.settings.transport_security = TransportSecuritySettings(
                allowed_hosts=config.allowed_hosts,
            )

    def _shutdown(sig: int, frame: Any) -> None:
        logger.info("Stänger ner '%s'...", server.name)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "Startar '%s' (transport=%s, host=%s, port=%d)",
        server.name, config.transport, config.host, config.port,
    )

    try:
        server.run(transport=config.transport)
    except SystemExit:
        pass
