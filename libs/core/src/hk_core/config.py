"""Gemensam konfiguration för alla MCP-servrar."""

from typing import Literal

from pydantic_settings import BaseSettings


class ServerConfig(BaseSettings):
    """Baskonfiguration som alla MCP-servrar ärver.

    Värden kan sättas via miljövariabler med prefixet HK_.
    Exempel: HK_LOG_LEVEL=DEBUG, HK_PORT=8001, HK_TRANSPORT=streamable-http
    """

    model_config = {"env_prefix": "HK_"}

    log_level: str = "INFO"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    allowed_hosts: list[str] = []
