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
        "\n\n"
        "Verktygen är grupperade i tre API:er:\n"
        "- **Syllabus** (`list_subjects`, `get_subject`, `list_courses`, "
        "`list_curriculums` m.fl.) - läroplaner, ämnen, kurser, program.\n"
        "- **School registry** (`registry_*`, `list_organizers`, "
        "`list_education_providers`) - skolenheter, huvudmän, anordnare.\n"
        "- **Planned educations** (`search_school_units`, "
        "`search_education_events`, `search_adult_education`, "
        "`get_admission_stats`) - utbildningsutbud och antagningsstatistik.\n"
        "\n"
        "Typiska arbetsflöden:\n"
        "1. Skola -> utbildningar: `search_school_units` -> "
        "`search_education_events` för utbildningsutbud.\n"
        "2. Ämne -> kursplan: `list_subjects` -> `get_subject` för "
        "kunskapskrav och centralt innehåll.\n"
        "3. Huvudman -> skolor: `list_organizers` -> "
        "`registry_list_school_units` filtrerat på huvudman.\n"
        "\n"
        "Regler för datahämtning:\n"
        "- **Filtrera alltid listanrop.** Använd aldrig `list_*` eller "
        "`search_*` utan filter (kommun, huvudman, skoltyp, titel) om inte "
        "användaren uttryckligen ber om rikstäckande listor - svaren blir "
        "för stora.\n"
        "- **Gör inte om sökningar.** Har du redan ett ID (skola, huvudman, "
        "ämne, kurs), återanvänd det istället för att söka igen.\n"
        "- **Välj en träff och gå vidare.** Om ett steg ger flera relevanta "
        "träffar, välj den bästa och fortsätt - fråga inte användaren.\n"
        "- **Stanna när du har svaret.** Tre till fyra verktygsanrop räcker "
        "för de flesta frågor. Över-hämta inte relaterad data 'för säkerhets "
        "skull'."
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
