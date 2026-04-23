"""MCP-verktyg för Koladas metadata (KPI:er, kommuner, grupper, OU:er)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from kolada_mcp.clients.kolada import KoladaClient


def _get_client(ctx: Context) -> KoladaClient:
    return ctx.request_context.lifespan_context.kolada


def register(mcp: FastMCP) -> None:
    """Registrera alla metadata-verktyg på MCP-servern."""

    # -- KPI:er --

    @mcp.tool()
    async def search_kpis(
        ctx: Context,
        title: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök Koladas KPI:er (nyckeltal) på titel.

        Returnerar `{values: [{id, title, description, is_divided_by_gender,
        municipality_type, operating_area, perspective, publication_date,
        publ_period, has_ou_data, ...}], count, next_url, previous_url}`.
        Använd `id`-fältet för efterföljande data-anrop.

        Args:
            title: Mellanslagsseparerad lista med filterord (matchas mot titel).
            page: Sidnummer (från 1).
            per_page: Antal poster per sida (max 5000).
        """
        client = _get_client(ctx)
        return await client.list_kpis(title=title, page=page, per_page=per_page)

    @mcp.tool()
    async def get_kpi(
        ctx: Context,
        kpi_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta specifika KPI:er via ID.

        Args:
            kpi_id: Kommaseparerad lista med KPI-ID:n. Ett ID består av 'N'
                eller 'U' följt av fem siffror (t.ex. 'N01951' Invånare
                totalt, 'N11800' Lärarbehörighet, eller flera:
                'N01951,N11800'). Använd `search_kpis` om du inte har ID -
                gamla koder som N00914 finns inte i v3.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_kpi(kpi_id, page=page, per_page=per_page)

    @mcp.tool()
    async def search_kpi_groups(
        ctx: Context,
        title: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök KPI-grupper på titel.

        Returnerar `{values: [{id, title, members: [...]}], count}`.
        Grupp-ID har format `G2KPI` följt av siffror (t.ex. 'G2KPI110397').
        En grupp samlar tematiskt relaterade KPI:er.

        Args:
            title: Filterord mot gruppens titel.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.list_kpi_groups(title=title, page=page, per_page=per_page)

    @mcp.tool()
    async def get_kpi_group(
        ctx: Context,
        kpi_group_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta en KPI-grupp via ID.

        Returnerar gruppen med `members`-lista som innehåller KPI-ID:n att
        använda i efterföljande data-anrop.

        Args:
            kpi_group_id: Grupp-ID, format `G2KPI` + siffror (t.ex.
                'G2KPI110397'). Hämta giltiga via `search_kpi_groups`.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_kpi_group(
            kpi_group_id, page=page, per_page=per_page
        )

    # -- Kommuner och regioner --

    @mcp.tool()
    async def search_municipalities(
        ctx: Context,
        title: str | None = None,
        type: str | None = None,
        region_type: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök kommuner och regioner på titel.

        Returnerar `{values: [{id, title, type, region_type, ...}], count}`.
        `id` är fyrsiffrig SCB-kod för kommuner (t.ex. `1466`). Regioner/län
        har formatet `00XX` (t.ex. `0014` Västra Götaland). `0000` = Riket.

        Args:
            title: Filterord mot kommun/regionens titel (t.ex. 'Herrljunga').
            type: Filtrera på typ ('K' = kommun, 'L' = region/län).
            region_type: Filtrera på region-typ.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.list_municipalities(
            title=title,
            type=type,
            region_type=region_type,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_municipality(
        ctx: Context,
        municipality_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta kommun eller region via exakt ID.

        Args:
            municipality_id: Fyrsiffrig SCB-kod för kommun (t.ex. '1466'
                Herrljunga, '1440' Ale, '1489' Alingsås) eller fyrsiffrig
                region-/länskod '00XX' (t.ex. '0014' Västra Götaland,
                '0000' Riket). Kommaseparerat stöds.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_municipality(
            municipality_id, page=page, per_page=per_page
        )

    @mcp.tool()
    async def search_municipality_groups(
        ctx: Context,
        title: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök kommungrupper på titel.

        Returnerar `{values: [{id, title, members: [...]}], count}`.
        Grupp-ID har format `G` + siffror (t.ex. 'G114418'). Används för att
        jämföra en kommun mot en grupp av liknande kommuner.

        Args:
            title: Filterord mot gruppens titel.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.list_municipality_groups(
            title=title, page=page, per_page=per_page
        )

    @mcp.tool()
    async def get_municipality_group(
        ctx: Context,
        municipality_group_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta en kommungrupp via ID.

        Returnerar gruppen med `members`-lista som innehåller kommun-ID:n.

        Args:
            municipality_group_id: Grupp-ID, format `G` + siffror (t.ex.
                'G114418'). Hämta giltiga via `search_municipality_groups`.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_municipality_group(
            municipality_group_id, page=page, per_page=per_page
        )

    # -- Organisationsenheter (OU) --

    @mcp.tool()
    async def search_ous(
        ctx: Context,
        title: str | None = None,
        municipality: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök organisationsenheter (t.ex. skolor, äldreboenden) på titel och kommun.

        Returnerar `{values: [{id, title, municipality}], count}`. OU-ID
        börjar med 'V' följt av siffror/bokstäver (t.ex. 'V60E10011',
        'V11E155490'). Filtrera alltid på `municipality` - listan utan
        filter är stor.

        Args:
            title: Filterord mot enhetens titel.
            municipality: Kommun-ID att filtrera på (fyrsiffrig SCB-kod).
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.list_ous(
            title=title,
            municipality=municipality,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_ou(
        ctx: Context,
        ou_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta organisationsenhet via ID.

        Returnerar `{values: [{id, title, municipality}], count}`.

        Args:
            ou_id: OU-ID, börjar med 'V' (t.ex. 'V11E155490', 'V60E10011').
                Kommaseparerat stöds. Hämta via `search_ous`.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou(ou_id, page=page, per_page=per_page)
