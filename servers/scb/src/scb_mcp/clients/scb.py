"""HTTP-klient för Statistiska centralbyråns PxWebAPI 2.0.

Dokumentation: https://www.scb.se/en/services/open-data-api/pxwebapi/
OpenAPI-spec: https://github.com/PxTools/PxApiSpecs/blob/master/PxAPI-2.yml
"""

from typing import Any

import httpx

BASE_URL = "https://api.scb.se/OV0104/v2beta/api/v2"
USER_AGENT = "HK-SCB-MCP/0.1"


class SCBClient:
    """Klient för SCB:s PxWebAPI 2.0."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        clean = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.get(path, params=clean)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: Any, **params: Any) -> dict[str, Any]:
        clean = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.post(path, params=clean, json=json)
        resp.raise_for_status()
        return resp.json()

    # --- API-metadata ---

    async def get_config(self) -> dict[str, Any]:
        """Hämta API-konfiguration (version, språk, rate limits, licens)."""
        return await self._get("/config")

    # --- Tabellsökning ---

    async def search_tables(
        self,
        query: str | None = None,
        past_days: int | None = None,
        include_discontinued: bool | None = None,
        page_number: int | None = None,
        page_size: int | None = None,
        lang: str = "sv",
    ) -> dict[str, Any]:
        """Sök statistiktabeller.

        Args:
            query: Sökfras. Svenska termer ger bäst resultat (t.ex. "befolkning").
            past_days: Endast tabeller uppdaterade de senaste N dagarna.
            include_discontinued: Inkludera nedlagda tabeller.
            page_number: Sidnummer (1-baserat).
            page_size: Antal per sida (max 100).
            lang: Språkkod "sv" eller "en".
        """
        return await self._get(
            "/tables",
            query=query,
            pastDays=past_days,
            includeDiscontinued=(
                str(include_discontinued).lower()
                if include_discontinued is not None
                else None
            ),
            pageNumber=page_number,
            pageSize=page_size,
            lang=lang,
        )

    async def get_table_metadata(
        self,
        table_id: str,
        lang: str = "sv",
    ) -> dict[str, Any]:
        """Hämta komplett metadata (dimensioner + värden) för en tabell.

        Returnerar JSON-stat2-format med fältet `dimension` som innehåller
        alla variabler och deras tillåtna värdekoder.
        """
        return await self._get(f"/tables/{table_id}/metadata", lang=lang)

    # --- Data ---

    async def get_table_data(
        self,
        table_id: str,
        selection: dict[str, list[str]] | None = None,
        lang: str = "sv",
    ) -> dict[str, Any]:
        """Hämta data från en tabell.

        Args:
            table_id: Tabell-ID (t.ex. "TAB637").
            selection: Valfri variabelurval. Format:
                `{"Region": ["1441"], "Tid": ["TOP(5)"]}`. Om None används
                API:ets standardurval (senaste tidsperiod, alla kategorier).
            lang: Språkkod "sv" eller "en".

        Returnerar JSON-stat2-dataset.
        """
        params = {"lang": lang, "outputFormat": "json-stat2"}

        if not selection:
            return await self._get(
                f"/tables/{table_id}/data",
                **params,
            )

        selection_array = [
            {"variableCode": code, "valueCodes": list(values)}
            for code, values in selection.items()
        ]
        return await self._post(
            f"/tables/{table_id}/data",
            json={"selection": selection_array},
            **params,
        )
