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
        "Du har tillgång till Koladas öppna API (v3) för svensk kommunal "
        "statistik. Använd verktygen för att söka KPI:er (nyckeltal), slå "
        "upp kommuner och regioner, hitta organisationsenheter (skolor, "
        "äldreboenden m.m.) och hämta statistikdata på kommun- eller "
        "enhetsnivå.\n"
        "\n"
        "ID-format:\n"
        "- **Kommun-ID**: fyrsiffrig SCB-kod (t.ex. `1466` Herrljunga, "
        "`1440` Ale, `1489` Alingsås).\n"
        "- **Region-/läns-ID**: fyrsiffrigt format `00XX` (t.ex. `0014` "
        "Västra Götaland, `0001` Stockholm). `0000` = Riket (hela Sverige).\n"
        "- **KPI-ID**: `N` eller `U` + fem siffror, t.ex. `N01951` "
        "(Invånare totalt, antal), `N11800` (Lärarbehörighet), `N17813`. "
        "OBS: gamla koder som `N00914` finns **inte** i v3 - använd "
        "`search_kpis` om du är osäker.\n"
        "- **OU-ID**: börjar med `V` följt av siffror/bokstäver, 9-11 "
        "tecken (t.ex. `V60E10011`, `V11E155490`).\n"
        "- **År**: YYYY. Flera år kommaseparerat (t.ex. `2022,2023`).\n"
        "\n"
        "Svarstruktur:\n"
        "- Metadata (`list_*`/`get_*`): `{values: [...], count, next_url, "
        "previous_url}`.\n"
        "- Data (kommunnivå): `{values: [{values: [{gender, count, status, "
        "value, isdeleted}], kpi, period, municipality}], count}`. "
        "Observera **dubbla `values`-nivåer**: yttre = en post per "
        "KPI/kommun/år, inre = en post per kön (`T` total, `M` män, `K` "
        "kvinnor).\n"
        "- OU-data: samma struktur men fältet heter `ou` istället för "
        "`municipality`.\n"
        "\n"
        "Typiskt arbetsflöde:\n"
        "1. `search_municipalities(title='...')` -> kommun-ID.\n"
        "2. `search_kpis(title='...')` -> KPI-ID.\n"
        "3. `get_data_by_kpi_municipality_year(kpi_id, municipality_id, "
        "year)` -> värde. Path-parametrar accepterar kommaseparerade värden "
        "för flera KPI:er/kommuner/år samtidigt.\n"
        "4. För skol-/enhetsnivå: `search_ous(municipality=...)` -> "
        "`get_ou_data_by_kpi_ou_year` eller `get_ou_data_by_municipality_year`.\n"
        "\n"
        "Regler för datahämtning:\n"
        "- **Framtida år finns inte.** Senast publicerade år är oftast året "
        "före innevarande. Vissa KPI:er släpps ännu senare (publ_period i "
        "KPI-metadatan visar när). Prova tidigare år om svaret är tomt.\n"
        "- **Hämta inte riksdata.** Använd aldrig `get_data_by_kpi_year` "
        "eller `get_ou_data_by_kpi_year` utan kommunfilter om inte "
        "användaren uttryckligen ber om nationell jämförelse - svaren blir "
        "för stora.\n"
        "- **OU-data kräver rätt KPI.** Bara KPI:er där `has_ou_data=true` "
        "ger träffar på enhetsnivå. Kolla fältet i `search_kpis`-svaret "
        "innan du anropar `get_ou_data_*`.\n"
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
