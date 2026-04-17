"""MCP-verktyg för Koladas OU-data (organisationsenhets-nivå)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from kolada_mcp.clients.kolada import KoladaClient


def _get_client(ctx: Context) -> KoladaClient:
    return ctx.request_context.lifespan_context.kolada


def register(mcp: FastMCP) -> None:
    """Registrera alla OU-dataverktyg på MCP-servern."""

    @mcp.tool()
    async def get_ou_data(
        ctx: Context,
        kpi_id: str | None = None,
        ou_id: str | None = None,
        year: str | None = None,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta OU-data med minst två av kpi_id, ou_id och year.

        Args:
            kpi_id: Kommaseparerade KPI-ID:n.
            ou_id: Kommaseparerade enhets-ID:n.
            year: Kommaseparerade årtal.
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou_data(
            kpi_id=kpi_id,
            ou_id=ou_id,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_ou_data_by_kpi_ou_year(
        ctx: Context,
        kpi_id: str,
        ou_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta OU-data för en kombination av KPI, enhet och år.

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            ou_id: Ett eller flera enhets-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou_data_by_kpi_ou_year(
            kpi_id=kpi_id,
            ou_id=ou_id,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_ou_data_by_kpi_year(
        ctx: Context,
        kpi_id: str,
        year: str,
        municipality_id: str | None = None,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta OU-data för en KPI och ett år, valfritt filtrerat per kommun.

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat).
            municipality_id: Valfritt kommun-ID för att begränsa enheterna.
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou_data_by_kpi_year(
            kpi_id=kpi_id,
            year=year,
            municipality_id=municipality_id,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_ou_data_by_kpi_ou(
        ctx: Context,
        kpi_id: str,
        ou_id: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta tidsserie för en KPI på en enhet (alla år).

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            ou_id: Ett eller flera enhets-ID:n (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou_data_by_kpi_ou(
            kpi_id=kpi_id,
            ou_id=ou_id,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_ou_data_by_ou_year(
        ctx: Context,
        ou_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta alla KPI-värden för en enhet ett visst år.

        Args:
            ou_id: Ett eller flera enhets-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou_data_by_ou_year(
            ou_id=ou_id,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    @mcp.tool()
    async def get_ou_data_by_municipality_year(
        ctx: Context,
        municipality: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta OU-data för alla enheter i en kommun ett visst år.

        Args:
            municipality: Kommun-ID.
            year: Ett eller flera år (kommaseparerat).
            from_date: YYYY-MM-DD för senaste uppdateringsfilter.
            page: Sidnummer.
            per_page: Antal poster per sida.
        """
        client = _get_client(ctx)
        return await client.get_ou_data_by_municipality_year(
            municipality=municipality,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )
