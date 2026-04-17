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
            kpi_id: Kommaseparerad lista med KPI-ID:n. Ett ID består av 'N' eller 'U'
                följt av fem siffror (t.ex. 'N00914' eller 'N00914,N00945').
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

        Args:
            kpi_group_id: Grupp-ID.
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
            municipality_id: Fyra-siffrigt kommun-/region-ID (t.ex. '1466' för Herrljunga).
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

        Args:
            municipality_group_id: Gruppens ID.
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

        Args:
            title: Filterord mot enhetens titel.
            municipality: Kommun-ID att filtrera på.
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

        Args:
            ou_id: Enhetens ID.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou(ou_id, page=page, per_page=per_page)
