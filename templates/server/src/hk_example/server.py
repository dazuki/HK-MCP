"""Exempelserver som visar hur man bygger en MCP-server med hk-core."""

from hk_core import create_server, run_server

mcp = create_server(
    name="HK Exempel",
    instructions="Du är en hjälpsam assistent för Herrljunga Kommun.",
    package_file=__file__,
)


@mcp.tool()
def hello(name: str = "världen") -> str:
    """Hälsa på någon."""
    return f"Hej, {name}! Välkommen till Herrljunga Kommuns AI-plattform."


@mcp.tool()
def add(a: int, b: int) -> int:
    """Addera två tal."""
    return a + b


def main():
    """Starta servern."""
    run_server(mcp)


if __name__ == "__main__":
    main()
