"""MCP-verktyg för regionuppslagning (lokal databas, offline)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from scb_mcp.clients import SCBClient
from scb_mcp.data import ALL_REGIONS, normalize_for_search
from scb_mcp.data import search_regions as _search_regions_db


def _get_client(ctx: Context) -> SCBClient:
    return ctx.request_context.lifespan_context.scb


def _region_dict(region: Any) -> dict[str, Any]:
    county = None
    if region.county_code:
        for r in ALL_REGIONS:
            if r.code == region.county_code:
                county = r.name
                break
    return {
        "code": region.code,
        "name": region.name,
        "type": region.type,
        "county": county,
    }


def register(mcp: FastMCP) -> None:
    """Registrera regionrelaterade verktyg på MCP-servern."""

    @mcp.tool()
    async def search_regions(
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Sök svenska regioner (land, län, kommuner) med fuzzy matching.

        Använder en lokal databas med 312 regioner - ingen API-begäran.
        Fuzzy matching stöder svenska tecken: "Goteborg" matchar "Göteborg".

        Returnerar `{query, total_matches, regions: [{code, name, type, county}]}`
        där `code` är SCB-regionkoden att använda i data-urval som
        `{"Region": ["1480"]}`.

        Kodformat:
        - "00" = Riket (hela Sverige)
        - 2 siffror (t.ex. "14") = län
        - 4 siffror (t.ex. "1480") = kommun

        Args:
            query: Regionnamn eller kod att söka efter (t.ex. "Göteborg",
                "Stockholm", "1480", "Goteborg").
            limit: Max antal träffar att returnera (standard: 20).
        """
        matches = _search_regions_db(query)
        return {
            "query": query,
            "total_matches": len(matches),
            "regions": [_region_dict(r) for r in matches[:limit]],
        }

    @mcp.tool()
    async def find_region_code(
        ctx: Context,
        query: str,
        table_id: str | None = None,
        language: str = "sv",
    ) -> dict[str, Any]:
        """Hitta exakt regionkod för en kommun eller län.

        Försöker först en lokal databas (snabb, ingen API-begäran). Om
        `table_id` anges verifieras koden mot tabellens faktiska Region-
        dimension - nödvändigt eftersom inte alla tabeller innehåller alla
        regioner.

        Returnerar `{query, matches: [{code, name, type, ...}], primary_match,
        usage_example}`. `usage_example` är färdigt att skicka som
        `selection` till `get_table_data`.

        Args:
            query: Kommun- eller regionnamn (t.ex. "Lerum", "Stockholm",
                "Goteborg"). Fuzzy matching stöder svenska tecken.
            table_id: Valfritt tabell-ID för att verifiera att koden finns i
                tabellens Region-dimension (t.ex. "TAB637").
            language: Språkkod "sv" eller "en".
        """
        local_matches = _search_regions_db(query)

        if local_matches and not table_id:
            results = [_region_dict(r) for r in local_matches[:10]]
            primary = results[0]
            return {
                "query": query,
                "matches": results,
                "total_matches": len(local_matches),
                "primary_match": primary,
                "usage_example": {"Region": [primary["code"]]},
                "source": "local_database",
            }

        if table_id:
            client = _get_client(ctx)
            try:
                metadata = await client.get_table_metadata(table_id, lang=language)
            except Exception as exc:
                if local_matches:
                    results = [_region_dict(r) for r in local_matches[:10]]
                    return {
                        "query": query,
                        "matches": results,
                        "primary_match": results[0],
                        "usage_example": {"Region": [results[0]["code"]]},
                        "source": "local_database",
                        "warning": f"Kunde inte hämta tabell {table_id}: {exc}",
                    }
                return {
                    "query": query,
                    "matches": [],
                    "error": f"Kunde inte hämta tabell {table_id}: {exc}",
                }

            region_dim = (metadata.get("dimension") or {}).get("Region")
            if not region_dim:
                if local_matches:
                    results = [_region_dict(r) for r in local_matches[:10]]
                    return {
                        "query": query,
                        "matches": results,
                        "primary_match": results[0],
                        "usage_example": {"Region": [results[0]["code"]]},
                        "source": "local_database",
                        "warning": f"Tabell {table_id} saknar Region-dimension.",
                    }
                return {
                    "query": query,
                    "matches": [],
                    "error": f"Tabell {table_id} saknar Region-dimension.",
                }

            labels = (region_dim.get("category") or {}).get("label") or {}
            normalized = normalize_for_search(query)

            table_matches = []
            for code, label in labels.items():
                nlabel = normalize_for_search(label)
                if normalized in nlabel or code == query or query in code:
                    table_matches.append({"code": code, "name": label})

            if table_matches:
                primary = table_matches[0]
                return {
                    "query": query,
                    "matches": table_matches[:10],
                    "total_matches": len(table_matches),
                    "primary_match": primary,
                    "usage_example": {"Region": [primary["code"]]},
                    "source": "table_metadata",
                    "table_id": table_id,
                }

            if local_matches:
                results = [_region_dict(r) for r in local_matches[:5]]
                return {
                    "query": query,
                    "matches": results,
                    "primary_match": results[0],
                    "usage_example": {"Region": [results[0]["code"]]},
                    "source": "local_database",
                    "warning": (
                        f"Ingen match i tabell {table_id}. Visar träffar "
                        "från lokala databasen - verifiera kompatibilitet."
                    ),
                }

        return {
            "query": query,
            "matches": [],
            "error": f"Ingen region hittades för \"{query}\".",
            "tips": [
                "Fuzzy matching stöds: \"Goteborg\" matchar \"Göteborg\".",
                "Använd delnamn: \"kung\" matchar \"Kungälv\".",
                "Använd `search_regions_tool` för bredare sökning.",
            ],
        }
