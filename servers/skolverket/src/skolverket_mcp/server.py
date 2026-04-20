"""Samlad MCP-server för Skolverkets öppna API:er."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from hk_core import create_server, run_server
from skolverket_mcp.clients.planned_educations import PlannedEducationsClient
from skolverket_mcp.clients.school_registry import SchoolRegistryClient
from skolverket_mcp.clients.syllabus import SyllabusClient
from skolverket_mcp.tools import planned_educations as pe_tools
from skolverket_mcp.tools import school_registry as registry_tools
from skolverket_mcp.tools import syllabus as syllabus_tools


@dataclass
class AppContext:
    syllabus: SyllabusClient
    planned_educations: PlannedEducationsClient
    school_registry: SchoolRegistryClient


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Hantera livscykeln - skapa och stäng HTTP-klienterna."""
    syllabus = SyllabusClient()
    planned_educations = PlannedEducationsClient()
    school_registry = SchoolRegistryClient()
    try:
        yield AppContext(
            syllabus=syllabus,
            planned_educations=planned_educations,
            school_registry=school_registry,
        )
    finally:
        await syllabus.close()
        await planned_educations.close()
        await school_registry.close()


mcp = create_server(
    name="Skolverket",
    instructions=(
        "Du har tillgång till Skolverkets öppna API:er. "
        "Använd verktygen för att söka och hämta information om "
        "Sveriges utbildningssystem: läroplaner, kursplaner, ämnesplaner, "
        "skolor, utbildningar, huvudmän, utbildningsanordnare och statistik."
    ),
    lifespan=lifespan,
    package_file=__file__,
)

syllabus_tools.register(mcp)
pe_tools.register(mcp)
registry_tools.register(mcp)


def main():
    """Starta MCP-servern."""
    run_server(mcp)


if __name__ == "__main__":
    main()
