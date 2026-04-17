"""HTTP-klient för Koladas öppna API (v3)."""

from typing import Any

import httpx

BASE_URL = "https://api.kolada.se/v3"


class KoladaClient:
    """Klient för Koladas öppna API."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    # --- Metadata: KPI:er ---

    async def list_kpis(
        self,
        title: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök KPI:er (nyckeltal) på titel."""
        return await self._get("/kpi", title=title, page=page, per_page=per_page)

    async def get_kpi(
        self,
        kpi_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta specifika KPI:er via kommaseparerade ID:n (t.ex. 'N00914,N00945')."""
        return await self._get(f"/kpi/{kpi_id}", page=page, per_page=per_page)

    async def list_kpi_groups(
        self,
        title: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök KPI-grupper på titel."""
        return await self._get(
            "/kpi_groups", title=title, page=page, per_page=per_page
        )

    async def get_kpi_group(
        self,
        kpi_group_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta en KPI-grupp via dess ID."""
        return await self._get(
            f"/kpi_groups/{kpi_group_id}", page=page, per_page=per_page
        )

    # --- Metadata: Kommuner ---

    async def list_municipalities(
        self,
        title: str | None = None,
        type: str | None = None,
        region_type: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök kommuner och regioner på titel."""
        return await self._get(
            "/municipality",
            title=title,
            type=type,
            region_type=region_type,
            page=page,
            per_page=per_page,
        )

    async def get_municipality(
        self,
        municipality_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta kommun/region via exakt ID (t.ex. '1489' för Herrljunga)."""
        return await self._get(
            f"/municipality/{municipality_id}", page=page, per_page=per_page
        )

    async def list_municipality_groups(
        self,
        title: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök kommungrupper på titel."""
        return await self._get(
            "/municipality_groups", title=title, page=page, per_page=per_page
        )

    async def get_municipality_group(
        self,
        municipality_group_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta kommungrupp via ID."""
        return await self._get(
            f"/municipality_groups/{municipality_group_id}",
            page=page,
            per_page=per_page,
        )

    # --- Metadata: Organisationsenheter ---

    async def list_ous(
        self,
        title: str | None = None,
        municipality: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Sök organisationsenheter (OU) på titel och/eller kommun."""
        return await self._get(
            "/ou",
            title=title,
            municipality=municipality,
            page=page,
            per_page=per_page,
        )

    async def get_ou(
        self,
        ou_id: str,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta organisationsenhet via ID."""
        return await self._get(f"/ou/{ou_id}", page=page, per_page=per_page)

    # --- Data (kommun-nivå) ---

    async def get_data(
        self,
        kpi_id: str | None = None,
        municipality_id: str | None = None,
        year: str | None = None,
        from_date: str | None = None,
        region_type: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data med minst två av kpi_id/municipality_id/year."""
        return await self._get(
            "/data/",
            kpi_id=kpi_id,
            municipality_id=municipality_id,
            year=year,
            from_date=from_date,
            region_type=region_type,
            page=page,
            per_page=per_page,
        )

    async def get_data_by_kpi_year(
        self,
        kpi_id: str,
        year: str,
        from_date: str | None = None,
        region_type: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data via kpi-id och år."""
        return await self._get(
            f"/data/kpi/{kpi_id}/year/{year}",
            from_date=from_date,
            region_type=region_type,
            page=page,
            per_page=per_page,
        )

    async def get_data_by_kpi_municipality_year(
        self,
        kpi_id: str,
        municipality_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data via kpi-id, kommun-id och år."""
        return await self._get(
            f"/data/kpi/{kpi_id}/municipality/{municipality_id}/year/{year}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_data_by_municipality_year(
        self,
        municipality_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data via kommun-id och år (alla KPI:er)."""
        return await self._get(
            f"/data/municipality/{municipality_id}/year/{year}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_data_by_kpi_municipality(
        self,
        kpi_id: str,
        municipality_id: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta data via kpi-id och kommun-id (alla år)."""
        return await self._get(
            f"/data/kpi/{kpi_id}/municipality/{municipality_id}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    # --- OU-data (enhetsnivå) ---

    async def get_ou_data(
        self,
        kpi_id: str | None = None,
        ou_id: str | None = None,
        year: str | None = None,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta enhetsdata med minst två av kpi_id/ou_id/year."""
        return await self._get(
            "/oudata/",
            kpi_id=kpi_id,
            ou_id=ou_id,
            year=year,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_ou_data_by_kpi_ou_year(
        self,
        kpi_id: str,
        ou_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta enhetsdata via kpi-id, enhets-id och år."""
        return await self._get(
            f"/oudata/kpi/{kpi_id}/ou/{ou_id}/year/{year}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_ou_data_by_kpi_year(
        self,
        kpi_id: str,
        year: str,
        municipality_id: str | None = None,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta enhetsdata via kpi-id och år (valfri kommunfilter)."""
        return await self._get(
            f"/oudata/kpi/{kpi_id}/year/{year}",
            municipality_id=municipality_id,
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_ou_data_by_kpi_ou(
        self,
        kpi_id: str,
        ou_id: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta enhetsdata via kpi-id och enhets-id (alla år)."""
        return await self._get(
            f"/oudata/kpi/{kpi_id}/ou/{ou_id}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_ou_data_by_ou_year(
        self,
        ou_id: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta enhetsdata via enhets-id och år (alla KPI:er)."""
        return await self._get(
            f"/oudata/ou/{ou_id}/year/{year}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )

    async def get_ou_data_by_municipality_year(
        self,
        municipality: str,
        year: str,
        from_date: str | None = None,
        page: int = 1,
        per_page: int = 5000,
    ) -> dict[str, Any]:
        """Hämta enhetsdata för alla OU:er i en kommun ett visst år."""
        return await self._get(
            f"/oudata/municipality/{municipality}/year/{year}",
            from_date=from_date,
            page=page,
            per_page=per_page,
        )
