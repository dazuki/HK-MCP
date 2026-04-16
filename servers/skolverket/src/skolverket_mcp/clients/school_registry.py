"""HTTP-klient för Skolverkets Skolenhetsregister API v2."""

from typing import Any

import httpx

BASE_URL = "https://api.skolverket.se/skolenhetsregistret/v2"


class SchoolRegistryClient:
    """Klient för Skolverkets Skolenhetsregister API (skolenheter, huvudmän, utbildningsanordnare)."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    # --- Skolenheter ---

    async def list_school_units(
        self,
        organization_number: list[str] | None = None,
        school_type: list[str] | None = None,
        status: list[str] | None = None,
        municipality_code: list[str] | None = None,
        school_unit_type: list[str] | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med skolenheter."""
        return await self._get(
            "/school-units",
            organization_number=organization_number,
            school_type=school_type,
            status=status,
            municipality_code=municipality_code,
            school_unit_type=school_unit_type,
            meta_modified_after=meta_modified_after,
        )

    async def get_school_unit(
        self, code: str, search_date: str | None = None
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en skolenhet."""
        return await self._get(f"/school-units/{code}", search_date=search_date)

    # --- Huvudmän ---

    async def list_organizers(
        self,
        organizer_type: list[str] | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med huvudmän."""
        return await self._get(
            "/organizers",
            organizer_type=organizer_type,
            meta_modified_after=meta_modified_after,
        )

    async def get_organizer(
        self, organization_number: str, search_date: str | None = None
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en huvudman."""
        return await self._get(
            f"/organizers/{organization_number}", search_date=search_date
        )

    # --- Utbildningsanordnare ---

    async def list_education_providers(
        self,
        grading_rights: bool | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med utbildningsanordnare."""
        return await self._get(
            "/education-providers",
            grading_rights=grading_rights,
            meta_modified_after=meta_modified_after,
        )

    async def get_education_provider(
        self, code: str, search_date: str | None = None
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en utbildningsanordnare."""
        return await self._get(
            f"/education-providers/{code}", search_date=search_date
        )

    # --- Kontrakt (komvux på entreprenad) ---

    async def list_contracts(
        self,
        organizer_organization_number: str | None = None,
        education_provider_organization_number: str | None = None,
        meta_modified_after: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med komvux-entreprenader."""
        return await self._get(
            "/contracts",
            organizer_organization_number=organizer_organization_number,
            education_provider_organization_number=education_provider_organization_number,
            meta_modified_after=meta_modified_after,
        )

    async def get_contract(
        self,
        organization_number: str,
        education_provider_code: str,
        search_date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta detaljerad information om en komvux-entreprenad."""
        return await self._get(
            f"/contracts/{organization_number}/{education_provider_code}",
            search_date=search_date,
        )
