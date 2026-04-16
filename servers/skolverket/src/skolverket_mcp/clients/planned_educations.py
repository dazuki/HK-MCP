"""HTTP-klient för Skolverkets Planned Educations API (skolor, utbildningar, statistik)."""

from typing import Any

import httpx

BASE_URL = "https://api.skolverket.se/planned-educations"

# Standard HAL JSON content type for v3
ACCEPT_V3 = "application/vnd.skolverket.plannededucations.api.v3.hal+json"


class PlannedEducationsClient:
    """Klient för Skolverkets Planned Educations API."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={"Accept": ACCEPT_V3},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: Any) -> dict[str, Any]:
        resp = await self._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()

    # --- Skolenheter ---

    async def list_school_units(
        self,
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
        """Hämta skolenheter med filtrering."""
        return await self._get(
            "/school-units",
            name=name,
            typeOfSchooling=type_of_schooling,
            principalOrganizerType=principal_organizer_type,
            geographicalAreaCode=geographical_area_code,
            schoolYears=school_years,
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    async def list_compact_school_units(
        self,
        type_of_schooling: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        distance: float | None = None,
        sort: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> dict[str, Any]:
        """Hämta skolenheter i kompakt format."""
        return await self._get(
            "/compact-school-units",
            typeOfSchooling=type_of_schooling,
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    # --- Gymnasieutbildningar ---

    async def list_education_events(
        self,
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
        """Hämta gymnasiala utbildningstillfällen."""
        return await self._get(
            "/education-events",
            name=name,
            studyPathCode=study_path_code,
            principalOrganizerType=principal_organizer_type,
            schoolOrientation=school_orientation,
            geographicalAreaCode=geographical_area_code,
            typeOfSchooling=type_of_schooling,
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    # --- Vuxenutbildning ---

    async def list_adult_education_events(
        self,
        town: str | None = None,
        search_term: str | None = None,
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
        """Hämta vuxenutbildningstillfällen."""
        return await self._get(
            "/adult-education-events",
            town=town,
            searchTerm=search_term,
            typeOfSchool=type_of_school,
            geographicalAreaCode=geographical_area_code,
            instructionLanguages=instruction_languages,
            paceOfStudy=pace_of_study,
            semesterStartFrom=semester_start_from,
            county=county,
            municipality=municipality,
            distance=distance,
            sort=sort,
            page=page,
            size=size,
        )

    async def count_adult_education_events(
        self,
        town: str | None = None,
        search_term: str | None = None,
        type_of_school: str | None = None,
        geographical_area_code: str | None = None,
        instruction_languages: str | None = None,
        pace_of_study: str | None = None,
        semester_start_from: str | None = None,
        county: str | None = None,
        municipality: str | None = None,
        distance: bool | None = None,
    ) -> dict[str, Any]:
        """Hämta antal matchande vuxenutbildningstillfällen."""
        return await self._get(
            "/adult-education-events-count",
            town=town,
            searchTerm=search_term,
            typeOfSchool=type_of_school,
            geographicalAreaCode=geographical_area_code,
            instructionLanguages=instruction_languages,
            paceOfStudy=pace_of_study,
            semesterStartFrom=semester_start_from,
            county=county,
            municipality=municipality,
            distance=distance,
        )

    async def get_adult_education_event(self, event_id: str) -> dict[str, Any]:
        """Hämta ett specifikt vuxenutbildningstillfälle."""
        return await self._get(f"/adult-education-events/{event_id}")

    async def list_adult_education_areas(self) -> dict[str, Any]:
        """Hämta utbildningsområden och inriktningar för vuxenutbildning."""
        return await self._get("/adult-education-events/areas")

    # --- Antagningspoäng ---

    async def get_school_unit_secondary_stats(
        self, school_unit_programs: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Hämta antagningspoäng och elevstatistik för gymnasieprogram.

        Args:
            school_unit_programs: Lista med objekt som har 'schoolUnitCode' och 'programCode'.
        """
        return await self._post("/school-unit-secondary", json=school_unit_programs)
