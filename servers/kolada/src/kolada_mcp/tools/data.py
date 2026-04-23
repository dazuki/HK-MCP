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

        Returnerar `{values: [{values: [{gender, count, status, value,
        isdeleted}], kpi, period, municipality}], count}`. Yttre `values` =
        en post per KPI/kommun/år. Inre `values` = en post per kön ('T'
        total, 'M' män, 'K' kvinnor). Läs `value`-fältet för siffran.

        Args:
            kpi_id: Kommaseparerade KPI-ID:n (t.ex. 'N01951,N11800').
            municipality_id: Kommaseparerade kommun-/region-ID:n.
            year: Kommaseparerade årtal (YYYY).
            from_date: Returnera bara poster uppdaterade efter datum (YYYY-MM-DD).
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

        Ger en post per kommun som rapporterat värdet - potentiellt ~290
        poster per KPI och år. Använd bara när användaren uttryckligen vill
        jämföra alla kommuner; annars använd `get_data_by_kpi_municipality_year`.

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

        Returnerar `{values: [{values: [{gender, value, ...}], kpi, period,
        municipality}], count}`. Det vanligaste verktyget för att svara på
        konkreta frågor om en kommun.

        Args:
            kpi_id: Ett eller flera KPI-ID:n (kommaseparerat).
            municipality_id: Ett eller flera kommun-/region-ID:n (kommaseparerat).
            year: Ett eller flera år (kommaseparerat, t.ex. '2022,2023').
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

        Ger stora svar (hundratals KPI:er per kommun/år). Använd
        `from_date` eller paginera med `per_page` för att begränsa.

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

        Returnerar en post per år i `values`-listan. Sortera själv på
        `period`-fältet.

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
