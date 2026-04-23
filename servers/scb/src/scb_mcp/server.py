"""MCP-server för Statistiska centralbyråns (SCB) PxWebAPI 2.0."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from hk_core import create_server, run_server
from scb_mcp.clients import SCBClient
from scb_mcp.tools import data as data_tools
from scb_mcp.tools import metadata as metadata_tools
from scb_mcp.tools import regions as regions_tools


@dataclass
class AppContext:
    scb: SCBClient


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Hantera livscykeln - skapa och stäng HTTP-klienten."""
    scb = SCBClient()
    try:
        yield AppContext(scb=scb)
    finally:
        await scb.close()


mcp = create_server(
    name="SCB",
    instructions=(
        "Du har tillgång till Statistiska centralbyråns (SCB) PxWebAPI 2.0 "
        "med officiell svensk statistik: 1 200+ tabeller om befolkning, "
        "ekonomi, arbetsmarknad, miljö, utbildning, bostäder m.m. Data "
        "sträcker sig från 1950-talet till idag med månatliga/kvartalsvisa "
        "uppdateringar.\n"
        "\n"
        "ID-format:\n"
        "- **Tabell-ID**: 'TAB' + siffror (t.ex. 'TAB637' medelålder, "
        "'TAB4552' befolkning). Hämta via `search_tables`.\n"
        "- **Regionkod**: '00' = Riket, 2 siffror = län (t.ex. '14' Västra "
        "Götaland), 4 siffror = kommun (t.ex. '1480' Göteborg, '1441' "
        "Lerum, '0180' Stockholm).\n"
        "- **Tidskod**: 'YYYY' för år (t.ex. '2024'), 'YYYYMMM' för månad "
        "(t.ex. '2024M12'), 'YYYYKk' för kvartal (t.ex. '2024K1').\n"
        "\n"
        "Typiskt arbetsflöde:\n"
        "1. `search_tables(query='...')` - använd SVENSKA söktermer "
        "(befolkning, arbetslöshet, inkomst) för bäst resultat.\n"
        "2. `find_region_code(query='...')` - få SCB-kod för kommun/län. "
        "Fuzzy matching stöder 'Goteborg' -> 'Göteborg'.\n"
        "3. `get_table_variables(table_id='...')` - se alla variabler och "
        "tillåtna värdekoder (obligatoriskt innan data-hämtning).\n"
        "4. `preview_data(table_id='...')` - verifiera struktur innan full "
        "hämtning. Säkrare än `get_table_data` vid utforskning.\n"
        "5. `get_table_data(table_id='...', selection={...})` - hämta "
        "datat. Variabelnamn i selection är skiftlägeskänsliga.\n"
        "\n"
        "Urvalssyntax för `selection`:\n"
        "- Specifika värden: `{'Region': ['1441', '0180']}`\n"
        "- Alla värden: `{'Region': ['*']}` (riskerar stora svar)\n"
        "- Senaste N: `{'Tid': ['TOP(5)']}`\n"
        "- Äldsta N: `{'Tid': ['BOTTOM(5)']}`\n"
        "- Intervall: `{'Tid': ['RANGE(2020,2024)']}`\n"
        "\n"
        "Regler:\n"
        "- **Svenska söktermer ger bäst resultat.** 'befolkning' ger "
        "betydligt fler träffar än 'population'.\n"
        "- **Kolla variabler innan hämtning.** Värdekoder varierar mellan "
        "tabeller - `get_table_variables` visar exakt vad som gäller.\n"
        "- **Förhandsvisa stora datamängder.** API:et har en gräns på "
        "150 000 celler per förfrågan. Vid osäkerhet: `preview_data` först.\n"
        "- **Rate limit: 30 anrop / 10 sekunder.** Återanvänd hämtade "
        "tabell-ID:n och regionkoder istället för att söka på nytt.\n"
        "- **`find_region_code` och `search_regions` använder en lokal "
        "databas** med alla 312 svenska regioner - det är snabbt och kräver "
        "inget API-anrop. Skicka `table_id` till `find_region_code` för att "
        "verifiera kod mot tabellens faktiska Region-dimension."
    ),
    lifespan=lifespan,
    package_file=__file__,
)

metadata_tools.register(mcp)
data_tools.register(mcp)
regions_tools.register(mcp)


def main() -> None:
    """Starta MCP-servern."""
    run_server(mcp)


if __name__ == "__main__":
    main()
