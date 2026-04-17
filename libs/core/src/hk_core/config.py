"""Gemensam konfiguration för alla MCP-servrar."""

import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

GLOBAL_CONFIG_NAME = "settings.toml"
SERVER_CONFIG_NAME = "mcp-config.toml"


def _find_upward(filename: str, start: Path) -> Path | None:
    """Leta uppåt i katalogträdet efter en fil med givet namn."""
    for parent in [start, *start.parents]:
        candidate = parent / filename
        if candidate.is_file():
            return candidate
    return None


def _load_toml(path: Path) -> dict[str, Any]:
    """Läs en TOML-fil och returnera dess innehåll som dict."""
    with path.open("rb") as f:
        return tomllib.load(f)


def discover_config_files(start: Path | None = None) -> tuple[Path | None, Path | None]:
    """Hitta global settings.toml och server-specifik mcp-config.toml.

    Båda söks uppåt från startpunkten. Server-filen hittas typiskt närmare,
    den globala längre upp i trädet.

    Returns:
        (global_path, server_path) - någon kan vara None om den saknas.
    """
    start = (start or Path.cwd()).resolve()
    if start.is_file():
        start = start.parent

    server_path = _find_upward(SERVER_CONFIG_NAME, start)
    global_start = server_path.parent.parent if server_path else start
    global_path = _find_upward(GLOBAL_CONFIG_NAME, global_start)
    return global_path, server_path


class ServerConfig(BaseSettings):
    """Baskonfiguration som alla MCP-servrar ärver.

    Prioritet (hög till låg):
        1. CLI-argument (sätts av run_server)
        2. Miljövariabler med prefix HK_
        3. Server-specifik mcp-config.toml
        4. Global settings.toml
        5. Standardvärden
    """

    model_config = SettingsConfigDict(env_prefix="HK_", extra="ignore")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    allowed_hosts: list[str] = []
    allowed_origins: list[str] = []
    cors_origins: list[str] = ["*"]
    forwarded_allow_ips: str = "127.0.0.1"
    access_log: bool = False

    @classmethod
    def load(cls, start: Path | str | None = None) -> "ServerConfig":
        """Läs konfiguration med upptäckt av TOML-filer från en startpunkt."""
        start_path = Path(start) if start is not None else None
        global_path, server_path = discover_config_files(start_path)

        toml_data: dict[str, Any] = {}
        if global_path:
            toml_data.update(_load_toml(global_path))
        if server_path:
            toml_data.update(_load_toml(server_path))

        return cls(**toml_data)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Miljövariabler har högre prioritet än TOML-värden skickade via init."""
        return (env_settings, init_settings, dotenv_settings, file_secret_settings)
