"""MCP-server för Koladas öppna API (svensk kommunal statistik)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from hk_core import create_server, run_server
from kolada_mcp.clients.kolada import KoladaClient
from kolada_mcp.tools import data as data_tools
from kolada_mcp.tools import metadata as metadata_tools
from kolada_mcp.tools import ou_data as ou_data_tools


@dataclass
class AppContext:
    kolada: KoladaClient


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Hantera livscykeln - skapa och stäng HTTP-klienten."""
    kolada = KoladaClient()
    try:
        yield AppContext(kolada=kolada)
    finally:
        await kolada.close()


mcp = create_server(
    name="Kolada",
    instructions=(
        "Du har tillgång till Koladas öppna API för svensk kommunal statistik. "
        "Använd verktygen för att söka KPI:er (nyckeltal), slå upp kommuner och "
        "regioner, hitta organisationsenheter (skolor, äldreboenden m.m.) och "
        "hämta statistikdata på kommun- eller enhetsnivå. "
        "Kommun-ID:n är fyrsiffriga (t.ex. 1466 för Herrljunga). "
        "KPI-ID:n har formatet 'N' eller 'U' följt av fem siffror."
        "\n\n"
        "Typiskt arbetsflöde för en statistikfråga:\n"
        "1. Hitta kommun-ID med `search_municipalities` (filtrera på titel).\n"
        "2. Hitta relevant KPI med `search_kpis` (filtrera på titel).\n"
        "3. Hämta värden med `get_data_by_kpi_municipality_year`. Ange alltid "
        "`municipality_id` när frågan gäller en specifik kommun.\n"
        "4. För skol-/enhetsnivå: använd `search_ous` och `get_ou_data_*` "
        "istället för kommunnivå.\n"
        "\n"
        "Regler för datahämtning:\n"
        "- **Framtida år finns inte.** Senast tillgängliga år är oftast "
        "föregående kalenderår. Om ett år ger tomt svar, prova året innan.\n"
        "- **Hämta inte riksdata.** Använd aldrig `get_data_by_kpi_year` utan "
        "`municipality_id` om inte användaren uttryckligen ber om jämförelse "
        "mellan alla kommuner - svaret blir för stort.\n"
        "- **Gör inte om sökningar.** Har du redan ett KPI-ID eller kommun-ID, "
        "återanvänd det istället för att söka igen.\n"
        "- **Stanna när du har svaret.** Tre till fyra verktygsanrop räcker "
        "för de flesta frågor om en kommun."
    ),
    lifespan=lifespan,
    package_file=__file__,
)

metadata_tools.register(mcp)
data_tools.register(mcp)
ou_data_tools.register(mcp)


def main():
    """Starta MCP-servern."""
    run_server(mcp)


if __name__ == "__main__":
    main()
