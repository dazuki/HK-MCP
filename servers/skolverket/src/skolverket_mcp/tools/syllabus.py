"""MCP-verktyg för Skolverkets Syllabus API (läroplaner, kurs- och ämnesplaner)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from skolverket_mcp.clients.syllabus import SyllabusClient


def _get_client(ctx: Context) -> SyllabusClient:
    return ctx.request_context.lifespan_context.syllabus


def register(mcp: FastMCP) -> None:
    """Registrera alla syllabus-verktyg på MCP-servern."""

    # -- Ämnen --

    @mcp.tool()
    async def list_subjects(
        ctx: Context,
        school_type: str | None = None,
        type_of_syllabus: str = "ALL",
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med ämnen från Skolverket.

        Returnerar `{subjects: [{code, name, schoolTypes, typeOfSyllabus, version, ...}], totalElements}`.

        Args:
            school_type: Filtrera på skoltyp (t.ex. 'GR', 'GRAN', 'GY', 'GYAN',
                'VUX', 'VUXGY', 'VUXSFI'). Se `list_school_types` för alla.
            type_of_syllabus: 'ALL', 'COURSE_SYLLABUS', 'SUBJECT_SYLLABUS'.
            date: Sökdatum (YYYY-MM-DD). Standard: senaste gällande.
        """
        client = _get_client(ctx)
        return await client.list_subjects(
            school_type=school_type,
            type_of_syllabus=type_of_syllabus,
            date=date,
        )

    @mcp.tool()
    async def get_subject(
        ctx: Context,
        code: str,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta ett specifikt ämne med ämneskod.

        Args:
            code: Ämneskod. Formatet är prefix efter skolform, t.ex.
                'GRGRBIL01' (Bild, grundskola), 'GRGRSVE01' (Svenska, GR),
                'GRGRANMAT01' (anpassad grundskola), 'GRNSVA'
                (vuxenutbildning). Hämta giltiga koder via `list_subjects`.
            date: Sökdatum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_subject(code, date=date)

    @mcp.tool()
    async def list_subject_versions(ctx: Context, code: str) -> dict[str, Any]:
        """Hämta alla versioner av ett ämne.

        Args:
            code: Ämneskod.
        """
        client = _get_client(ctx)
        return await client.list_subject_versions(code)

    # -- Kurser --

    @mcp.tool()
    async def list_courses(
        ctx: Context,
        school_type: str | None = None,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med kurser från Skolverket.

        Returnerar `{courses: [{code, name, schoolTypes, ...}], totalElements}`.

        Args:
            school_type: Filtrera på skoltyp (t.ex. 'GY', 'GYAN', 'VUXGY').
            date: Sökdatum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.list_courses(school_type=school_type, date=date)

    @mcp.tool()
    async def get_course(
        ctx: Context,
        code: str,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta en specifik kurs med kurskod.

        Args:
            code: Kurskod, format `<ÄMNE><NIVÅ>` (t.ex. 'MATMAT01a',
                'SVESVE01', 'ENGENG06'). Hämta giltiga via `list_courses`.
            date: Sökdatum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_course(code, date=date)

    @mcp.tool()
    async def list_course_versions(ctx: Context, code: str) -> dict[str, Any]:
        """Hämta alla versioner av en kurs.

        Args:
            code: Kurskod.
        """
        client = _get_client(ctx)
        return await client.list_course_versions(code)

    # -- Program --

    @mcp.tool()
    async def list_programs(
        ctx: Context,
        school_type: str | None = None,
        date: str | None = None,
        type_of_study_path: str = "ALL",
    ) -> dict[str, Any]:
        """Hämta lista med program och vidareutbildningar.

        Returnerar `{programs: [{code, name, ...}], totalElements}`.

        Args:
            school_type: Filtrera på skoltyp (t.ex. 'GY', 'GYAN').
            date: Sökdatum (YYYY-MM-DD).
            type_of_study_path: Typ av studieväg ('ALL', 'PROGRAM', 'FURTHER_EDUCATION').
        """
        client = _get_client(ctx)
        return await client.list_programs(
            school_type=school_type,
            date=date,
            type_of_study_path=type_of_study_path,
        )

    @mcp.tool()
    async def get_program(
        ctx: Context,
        code: str,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta ett specifikt program med programkod.

        Args:
            code: Programkod (t.ex. 'TE' Teknikprogrammet, 'NA'
                Naturvetenskap, 'BA' Bygg och anläggning, 'EE' El och
                energi). Introduktionsprogram har längre koder t.ex.
                'IMVEEG'.
            date: Sökdatum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_program(code, date=date)

    @mcp.tool()
    async def list_program_versions(ctx: Context, code: str) -> dict[str, Any]:
        """Hämta alla versioner av ett program.

        Args:
            code: Programkod.
        """
        client = _get_client(ctx)
        return await client.list_program_versions(code)

    # -- Läroplaner --

    @mcp.tool()
    async def list_curriculums(
        ctx: Context,
        school_type: str | None = None,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med läroplaner.

        Args:
            school_type: Filtrera på skoltyp.
            date: Sökdatum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.list_curriculums(school_type=school_type, date=date)

    @mcp.tool()
    async def get_curriculum(
        ctx: Context,
        code: str,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta en specifik läroplan.

        Args:
            code: Läroplanskod.
            date: Sökdatum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_curriculum(code, date=date)

    @mcp.tool()
    async def list_curriculum_versions(ctx: Context, code: str) -> dict[str, Any]:
        """Hämta alla versioner av en läroplan.

        Args:
            code: Läroplanskod.
        """
        client = _get_client(ctx)
        return await client.list_curriculum_versions(code)

    # -- Värdeförråd (uppslagsvärden) --

    @mcp.tool()
    async def list_school_types(ctx: Context) -> dict[str, Any]:
        """Hämta alla aktiva skoltyper (t.ex. GR, GY, VUXGY)."""
        client = _get_client(ctx)
        return await client.list_school_types()

    @mcp.tool()
    async def list_syllabus_types(ctx: Context) -> dict[str, Any]:
        """Hämta typer av läroplaner/kursplaner."""
        client = _get_client(ctx)
        return await client.list_type_of_syllabus()

    @mcp.tool()
    async def list_subject_and_course_codes(ctx: Context) -> dict[str, Any]:
        """Hämta komplett lista på alla ämnes- och kurskoder."""
        client = _get_client(ctx)
        return await client.list_subject_and_course_codes()
