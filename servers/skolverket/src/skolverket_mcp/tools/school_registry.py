"""MCP-verktyg för Skolverkets Skolenhetsregister API (skolenheter, huvudmän, utbildningsanordnare)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from skolverket_mcp.clients.school_registry import SchoolRegistryClient


def _get_client(ctx: Context) -> SchoolRegistryClient:
    return ctx.request_context.lifespan_context.school_registry


def register(mcp: FastMCP) -> None:
    """Registrera alla skolenhetsregister-verktyg på MCP-servern."""

    # -- Skolenheter --

    @mcp.tool()
    async def registry_list_school_units(
        ctx: Context,
        school_type: list[str] | None = None,
        status: list[str] | None = None,
        municipality_code: list[str] | None = None,
        organization_number: list[str] | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta skolenheter från Skolenhetsregistret med filtrering.

        Returnerar `{data: {type: 'schoolunit', attributes: [{schoolUnitCode,
        name, status, ...}]}}`. Iterera över `data.attributes` och plocka
        `schoolUnitCode` för vidare anrop.

        Args:
            school_type: Skolformer (t.ex. ['GR', 'GY', 'FKLASS', 'FTH', 'VUX']).
            status: Status (['AKTIV', 'VILANDE', 'UPPHORT', 'PLANERAD']).
                OBS: 'UPPHORT' utan Ö.
            municipality_code: Kommunkoder (t.ex. ['1466'] för Herrljunga).
            organization_number: Organisationsnummer (10 siffror).
            meta_modified_after: Poster ändrade efter datum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.list_school_units(
            school_type=school_type,
            status=status,
            municipality_code=municipality_code,
            organization_number=organization_number,
            meta_modified_after=meta_modified_after,
        )

    @mcp.tool()
    async def registry_get_school_unit(
        ctx: Context,
        code: str,
        search_date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en skolenhet (adress, kontakt, rektor, skolformer).

        Returnerar `{data: {type: 'schoolunit', attributes: {displayName, status,
        url, email, phoneNumber, headMaster, address, schoolTypes, ...}}}`.
        För get-anrop är `attributes` ett objekt (inte lista).

        Args:
            code: Skolenhetskod (8 siffror).
            search_date: Historisk sökning (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_school_unit(code, search_date=search_date)

    # -- Huvudmän --

    @mcp.tool()
    async def list_organizers(
        ctx: Context,
        organizer_type: list[str] | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta huvudmän (kommuner, regioner, enskilda etc.) från Skolenhetsregistret.

        Returnerar `{data: {type: 'organizer', attributes: [{organizationNumber,
        displayName, organizerType, ...}]}}`.

        Args:
            organizer_type: Typ (['KOMMUN', 'REGION', 'STAT', 'ENSKILD']).
            meta_modified_after: Poster ändrade efter datum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.list_organizers(
            organizer_type=organizer_type,
            meta_modified_after=meta_modified_after,
        )

    @mcp.tool()
    async def get_organizer(
        ctx: Context,
        organization_number: str,
        search_date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en huvudman.

        Args:
            organization_number: Organisationsnummer (10 siffror).
            search_date: Historisk sökning (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_organizer(
            organization_number, search_date=search_date
        )

    # -- Utbildningsanordnare --

    @mcp.tool()
    async def list_education_providers(
        ctx: Context,
        grading_rights: bool | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta utbildningsanordnare från Skolenhetsregistret.

        Args:
            grading_rights: Filtrera på betygsrätt (true/false).
            meta_modified_after: Poster ändrade efter datum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.list_education_providers(
            grading_rights=grading_rights,
            meta_modified_after=meta_modified_after,
        )

    @mcp.tool()
    async def get_education_provider(
        ctx: Context,
        code: str,
        search_date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en utbildningsanordnare.

        Args:
            code: Anordnarkod (8 siffror).
            search_date: Historisk sökning (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_education_provider(code, search_date=search_date)

    # -- Kontrakt (komvux på entreprenad) --

    @mcp.tool()
    async def list_contracts(
        ctx: Context,
        organizer_organization_number: str | None = None,
        education_provider_organization_number: str | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta komvux-entreprenader från Skolenhetsregistret.

        Args:
            organizer_organization_number: Huvudmannens organisationsnummer (10 siffror).
            education_provider_organization_number: Utbildningsanordnarens organisationsnummer (10 siffror).
            meta_modified_after: Poster ändrade efter datum (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.list_contracts(
            organizer_organization_number=organizer_organization_number,
            education_provider_organization_number=education_provider_organization_number,
            meta_modified_after=meta_modified_after,
        )

    @mcp.tool()
    async def get_contract(
        ctx: Context,
        organization_number: str,
        education_provider_code: str,
        search_date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en komvux-entreprenad.

        Args:
            organization_number: Huvudmannens organisationsnummer (10 siffror).
            education_provider_code: Utbildningsanordnarens kod (8 siffror).
            search_date: Historisk sökning (YYYY-MM-DD).
        """
        client = _get_client(ctx)
        return await client.get_contract(
            organization_number, education_provider_code, search_date=search_date
        )
