"""MCP-verktyg för Skolverkets Planned Educations API (skolor, utbildningar, statistik)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from skolverket_mcp.clients.planned_educations import PlannedEducationsClient


def _get_client(ctx: Context) -> PlannedEducationsClient:
    return ctx.request_context.lifespan_context.planned_educations


def register(mcp: FastMCP) -> None:
    """Registrera alla planned-educations-verktyg på MCP-servern."""

    # -- Skolenheter --

    @mcp.tool()
    async def search_school_units(
        ctx: Context,
        name: str | None = None,
        type_of_schooling: str | None = None,
        principal_organizer_type: str | None = None,
        geographical_area_code: str | None = None,
        school_years: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        distance: float | None = None,
        sort: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> dict[str, Any]:
        """Sök skolenheter med filtrering och geografisk sökning.

        Args:
            name: Sökterm för skolans namn.
            type_of_schooling: Skolform (t.ex. 'COMPULSORY', 'UPPER_SECONDARY').
            principal_organizer_type: Huvudmannatyp ('MUNICIPAL', 'INDEPENDENT').
            geographical_area_code: Geografisk områdeskod (län/kommun).
            school_years: Årskurser.
            latitude: Latitud för geografisk sökning.
            longitude: Longitud för geografisk sökning.
            distance: Avstånd i km från koordinater.
            sort: Sortering (t.ex. 'name,asc').
            page: Sidnummer (börjar från 0).
            size: Antal per sida (max 100).
        """
        client = _get_client(ctx)
        return await client.list_school_units(
            name=name,
            type_of_schooling=type_of_schooling,
            principal_organizer_type=principal_organizer_type,
            geographical_area_code=geographical_area_code,
            school_years=school_years,
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    # -- Gymnasieutbildningar --

    @mcp.tool()
    async def search_education_events(
        ctx: Context,
        name: str | None = None,
        study_path_code: str | None = None,
        principal_organizer_type: str | None = None,
        school_orientation: str | None = None,
        geographical_area_code: str | None = None,
        type_of_schooling: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        distance: float | None = None,
        sort: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> dict[str, Any]:
        """Sök gymnasiala utbildningstillfällen.

        Args:
            name: Sökterm för utbildningsnamn.
            study_path_code: Studievägskod.
            principal_organizer_type: Huvudmannatyp ('MUNICIPAL', 'INDEPENDENT').
            school_orientation: Skolorientering/inriktning.
            geographical_area_code: Geografisk områdeskod.
            type_of_schooling: Skolform.
            latitude: Latitud för geografisk sökning.
            longitude: Longitud för geografisk sökning.
            distance: Avstånd i km.
            sort: Sortering.
            page: Sidnummer.
            size: Antal per sida.
        """
        client = _get_client(ctx)
        return await client.list_education_events(
            name=name,
            study_path_code=study_path_code,
            principal_organizer_type=principal_organizer_type,
            school_orientation=school_orientation,
            geographical_area_code=geographical_area_code,
            type_of_schooling=type_of_schooling,
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    # -- Vuxenutbildning --

    @mcp.tool()
    async def search_adult_education(
        ctx: Context,
        search_term: str | None = None,
        town: str | None = None,
        type_of_school: str | None = None,
        geographical_area_code: str | None = None,
        instruction_languages: str | None = None,
        pace_of_study: str | None = None,
        semester_start_from: str | None = None,
        county: str | None = None,
        municipality: str | None = None,
        distance: bool | None = None,
        sort: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> dict[str, Any]:
        """Sök vuxenutbildningstillfällen.

        Args:
            search_term: Fritext-sökning.
            town: Ort.
            type_of_school: Skoltyp.
            geographical_area_code: Geografisk områdeskod.
            instruction_languages: Undervisningsspråk.
            pace_of_study: Studietakt.
            semester_start_from: Terminsstart från (YYYY-MM-DD).
            county: Län.
            municipality: Kommun.
            distance: Distansutbildning (true/false).
            sort: Sortering.
            page: Sidnummer.
            size: Antal per sida.
        """
        client = _get_client(ctx)
        return await client.list_adult_education_events(
            search_term=search_term,
            town=town,
            type_of_school=type_of_school,
            geographical_area_code=geographical_area_code,
            instruction_languages=instruction_languages,
            pace_of_study=pace_of_study,
            semester_start_from=semester_start_from,
            county=county,
            municipality=municipality,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    @mcp.tool()
    async def count_adult_education(
        ctx: Context,
        search_term: str | None = None,
        town: str | None = None,
        type_of_school: str | None = None,
        geographical_area_code: str | None = None,
        county: str | None = None,
        municipality: str | None = None,
        distance: bool | None = None,
    ) -> dict[str, Any]:
        """Hämta antal matchande vuxenutbildningstillfällen.

        Args:
            search_term: Fritext-sökning.
            town: Ort.
            type_of_school: Skoltyp.
            geographical_area_code: Geografisk områdeskod.
            county: Län.
            municipality: Kommun.
            distance: Distansutbildning (true/false).
        """
        client = _get_client(ctx)
        return await client.count_adult_education_events(
            search_term=search_term,
            town=town,
            type_of_school=type_of_school,
            geographical_area_code=geographical_area_code,
            county=county,
            municipality=municipality,
            distance=distance,
        )

    @mcp.tool()
    async def get_adult_education_event(ctx: Context, event_id: str) -> dict[str, Any]:
        """Hämta ett specifikt vuxenutbildningstillfälle.

        Args:
            event_id: Utbildningstillfällets ID.
        """
        client = _get_client(ctx)
        return await client.get_adult_education_event(event_id)

    @mcp.tool()
    async def list_adult_education_areas(ctx: Context) -> dict[str, Any]:
        """Hämta utbildningsområden och inriktningar för vuxenutbildning."""
        client = _get_client(ctx)
        return await client.list_adult_education_areas()

    # -- Antagningspoäng --

    @mcp.tool()
    async def get_admission_stats(
        ctx: Context,
        school_unit_code: str,
        program_code: str,
    ) -> dict[str, Any]:
        """Hämta antagningspoäng och elevstatistik för ett gymnasieprogram på en skola.

        Args:
            school_unit_code: Skolenhetskod.
            program_code: Programkod.
        """
        client = _get_client(ctx)
        return await client.get_school_unit_secondary_stats(
            [{"schoolUnitCode": school_unit_code, "programCode": program_code}]
        )
