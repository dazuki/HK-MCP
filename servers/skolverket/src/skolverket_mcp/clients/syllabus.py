"""HTTP-klient för Skolverkets Syllabus API (läroplaner, kurs- och ämnesplaner)."""

from typing import Any

import httpx

BASE_URL = "https://api.skolverket.se/syllabus/v1"


class SyllabusClient:
    """Klient för Skolverkets Syllabus API."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    # --- Ämnen ---

    async def list_subjects(
        self,
        school_type: str | None = None,
        timespan: str = "LATEST",
        type_of_syllabus: str = "ALL",
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med ämnen."""
        return await self._get(
            "/subjects",
            schooltype=school_type,
            timespan=timespan,
            typeOfSyllabus=type_of_syllabus,
            date=date,
        )

    async def get_subject(self, code: str, date: str | None = None) -> dict[str, Any]:
        """Hämta ett specifikt ämne."""
        return await self._get(f"/subjects/{code}", date=date)

    async def list_subject_versions(self, code: str) -> dict[str, Any]:
        """Hämta alla versioner av ett ämne."""
        return await self._get(f"/subjects/{code}/versions")

    # --- Kurser ---

    async def list_courses(
        self,
        school_type: str | None = None,
        timespan: str = "LATEST",
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med kurser."""
        return await self._get(
            "/courses",
            schooltype=school_type,
            timespan=timespan,
            date=date,
        )

    async def get_course(self, code: str, date: str | None = None) -> dict[str, Any]:
        """Hämta en specifik kurs."""
        return await self._get(f"/courses/{code}", date=date)

    async def list_course_versions(self, code: str) -> dict[str, Any]:
        """Hämta alla versioner av en kurs."""
        return await self._get(f"/courses/{code}/versions")

    # --- Program ---

    async def list_programs(
        self,
        school_type: str | None = None,
        timespan: str = "LATEST",
        date: str | None = None,
        type_of_study_path: str = "ALL",
    ) -> dict[str, Any]:
        """Hämta lista med program och vidareutbildningar."""
        return await self._get(
            "/programs",
            schooltype=school_type,
            timespan=timespan,
            date=date,
            typeOfStudyPath=type_of_study_path,
        )

    async def get_program(self, code: str, date: str | None = None) -> dict[str, Any]:
        """Hämta ett specifikt program."""
        return await self._get(f"/programs/{code}", date=date)

    async def list_program_versions(self, code: str) -> dict[str, Any]:
        """Hämta alla versioner av ett program."""
        return await self._get(f"/programs/{code}/versions")

    # --- Läroplaner ---

    async def list_curriculums(
        self,
        school_type: str | None = None,
        timespan: str = "LATEST",
        date: str | None = None,
    ) -> dict[str, Any]:
        """Hämta lista med läroplaner."""
        return await self._get(
            "/curriculums",
            schooltype=school_type,
            timespan=timespan,
            date=date,
        )

    async def get_curriculum(
        self, code: str, date: str | None = None
    ) -> dict[str, Any]:
        """Hämta en specifik läroplan."""
        return await self._get(f"/curriculums/{code}", date=date)

    async def list_curriculum_versions(self, code: str) -> dict[str, Any]:
        """Hämta alla versioner av en läroplan."""
        return await self._get(f"/curriculums/{code}/versions")

    # --- Värdeförråd ---

    async def list_school_types(self) -> dict[str, Any]:
        """Hämta aktiva skoltyper."""
        return await self._get("/valuestore/schooltypes")

    async def list_type_of_syllabus(self) -> dict[str, Any]:
        """Hämta typer av läroplaner."""
        return await self._get("/valuestore/typeofsyllabus")

    async def list_subject_and_course_codes(self) -> dict[str, Any]:
        """Hämta lista på ämnen och kurskoder."""
        return await self._get("/valuestore/subjectandcoursecodes")
