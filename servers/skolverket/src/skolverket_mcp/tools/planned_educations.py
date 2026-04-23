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

        Returnerar `{body: {_embedded: {listedSchoolUnits: [{schoolUnitCode,
        name, ...}]}, page: {totalElements, number, size}}}`.

        Args:
            name: Sökterm för skolans namn.
            type_of_schooling: Skolform, lowercase (t.ex. 'gr', 'fsk', 'gy',
                'gyan', 'vuxgy', 'vuxgyan', 'vuxgr', 'vuxgran').
            principal_organizer_type: Huvudmannatyp. Värden: 'KOMMUNAL',
                'ENSKILD' (svenska, stora bokstäver). OBS: inte
                MUNICIPAL/INDEPENDENT.
            geographical_area_code: Kommun- eller länskod (t.ex. '1466'
                Herrljunga, '1440' Ale). Se `list_geographical_areas`.
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

        Returnerar `{body: {_embedded: {educationEvents: [{id, schoolUnitCode,
        schoolUnitName, studyPathCode, studyPathName, startDate, endDate,
        typeOfSchooling, ...}]}, page: {totalElements}}}`.

        Args:
            name: Sökterm för skolenhetens namn.
            study_path_code: Studievägskod (t.ex. 'TE', 'NA', 'IMVEEG').
            principal_organizer_type: Huvudmannatyp: 'KOMMUNAL' eller
                'ENSKILD' (svenska, stora bokstäver).
            school_orientation: Skolorientering/inriktning.
            geographical_area_code: Kommun- eller länskod.
            type_of_schooling: Skolform: 'gy' (gymnasieskolan) eller 'gyan'
                (anpassad gymnasieskolan). Endast gymnasial.
            latitude: Latitud för geografisk sökning.
            longitude: Longitud för geografisk sökning.
            distance: Avstånd i km.
            sort: Sortering (default 'relevance,desc').
            page: Sidnummer (börjar från 0).
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

        Returnerar `{body: {_embedded: {listedAdultEducationEvents:
        [{educationEventId, titleSv, providerName, typeOfSchool, municipality,
        semesterStartFrom, distance, ...}]}, page: {totalElements}}}`.
        Använd `educationEventId` för `get_adult_education_event`.

        Args:
            search_term: Fritext-sökning.
            town: Ort/studieort, kommaseparerad för flera (ex. 'Solna,Göteborg').
            type_of_school: Utbildningsform: 'coursebasic' (grundläggande
                kurs), 'courseadvanced' (gymnasial kurs), 'programbasic',
                'programadvanced', 'forutbildning', 'yh'.
            geographical_area_code: Kommun- eller länskod.
            instruction_languages: Undervisningsspråk.
            pace_of_study: Studietakt (t.ex. '25', '50', '100', '0-25',
                '25-75').
            semester_start_from: Terminsstart (ex.
                '2020-01-01TO2020-05-31,2020-08-01TO2020-12-31').
            county: Län.
            municipality: Kommun(er).
            distance: Distansutbildning (true/false).
            sort: Sortering (t.ex. 'titleSv:asc', 'typeOfSchool:desc').
            page: Sidnummer (börjar från 0).
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

        Returnerar `{body: <antal>}` med antalsvärdet som heltal. Användbart
        för att kontrollera sökningens storlek innan full listning.

        Args:
            search_term: Fritext-sökning.
            town: Ort.
            type_of_school: 'coursebasic', 'courseadvanced', 'programbasic',
                'programadvanced', 'forutbildning', 'yh'.
            geographical_area_code: Kommun- eller länskod.
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
            event_id: Utbildningstillfällets ID (fältet `educationEventId`
                från `search_adult_education`, t.ex. 'e.uoh.uu.hsv2m.p5655').
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
        study_path_code: str,
        type_of_schooling: str = "gy",
    ) -> dict[str, Any]:
        """Hämta antagningspoäng och elevstatistik för ett gymnasieprogram på en skola.

        Returnerar `{body: [{schoolUnitCode, studyPathCode,
        admissionPointsMin, admissionPointsAverage, studentsInProgram,
        studentsInSemester, typeOfSchooling, ...}]}`. Fält kan vara null om
        statistik saknas för kombinationen (för ny/liten utbildning).

        Args:
            school_unit_code: Skolenhetskod (8 siffror, t.ex. '18451445').
            study_path_code: Studievägs-/programkod (t.ex. 'TE', 'NA',
                'IMVEEG'). Hämtas från `search_education_events` fältet
                `studyPathCode`.
            type_of_schooling: Skolform: 'gy' (gymnasieskolan) eller 'gyan'
                (anpassad gymnasieskolan).
        """
        client = _get_client(ctx)
        return await client.get_school_unit_secondary_stats(
            [
                {
                    "schoolUnitCode": school_unit_code,
                    "studyPathCode": study_path_code,
                    "typeOfSchooling": type_of_schooling,
                }
            ]
        )
