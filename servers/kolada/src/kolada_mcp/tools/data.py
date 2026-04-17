"""MCP-verktyg för Koladas data på kommun-/regionnivå."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from kolada_mcp.clients.kolada import KoladaClient


def _get_client(ctx: Context) -> KoladaClient:
    return ctx.request_context.lifespan_context.kolada


def register(mcp: FastMCP) -> None:
    """Registrera alla dataverktyg på MCP-servern."""

    @mcp.tool()
    async def get_data(
        ctx: Context,
        kpi_id: str | None = None,
        municipality_id: str | None = None,
        year: str | None = None,
        from_date: str | None = None,
        region_type: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data med minst två av kpi_id, municipality_id och year.

        Args:
            kpi_id: Kommaseparerade KPI-ID:n.
            municipality_id: Kommaseparerade kommun-/region-ID:n.
            year: Kommaseparerade årtal (YYYY).
            from_date: Returnera bara poster uppdaterade efter detta datum (YYYY-MM-DD).
            region_type: Filter på region-typ.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_data(
            kpi_id=kpi_id,
            municipality_id=municipality_id,
            year=year,
            from_date=from_date,
            region_type=region_type,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_data_by_kpi_year(
        ctx: Context,
        kpi_id: str,
        year: str,
        from_date: str | None = None,
        region_type: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data för en KPI och ett år (alla kommuner).

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            region_type: Filter på region-typ.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_data_by_kpi_year(
            kpi_id=kpi_id,
            year=year,
            from_date=from_date,
            region_type=region_type,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_data_by_kpi_municipality_year(
        ctx: Context,
        kpi_id: str,
        municipality_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data för en kombination av KPI, kommun och år.

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            municipality_id: Ett eller flera kommun-/region-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_data_by_kpi_municipality_year(
            kpi_id=kpi_id,
            municipality_id=municipality_id,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_data_by_municipality_year(
        ctx: Context,
        municipality_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta alla KPI-värden för en kommun och år.

        Args:
            municipality_id: Ett eller flera kommun-/region-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_data_by_municipality_year(
            municipality_id=municipality_id,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_data_by_kpi_municipality(
        ctx: Context,
        kpi_id: str,
        municipality_id: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta tidsserie för en KPI i en kommun (alla år).

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            municipality_id: Ett eller flera kommun-/region-ID:n (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_data_by_kpi_municipality(
            kpi_id=kpi_id,
            municipality_id=municipality_id,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )
