"""MCP-verktyg för SCB:s tabellmetadata och API-status."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from scb_mcp.clients import SCBClient


def _get_client(ctx: Context) -> SCBClient:
    return ctx.request_context.lifespan_context.scb


# Kategorinyckelord (svenska + engelska) för klientsidofiltrering av
# `search_tables`-resultat. Matchas mot label + description + variableNames.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "population": [
        "population", "befolkning", "invånare", "folk", "demographic",
        "demografi", "födelse", "birth", "död", "death", "migration",
        "flyttning", "ålder", "age", "kön", "sex", "gender",
    ],
    "labour": [
        "labour", "labor", "employment", "arbete", "arbets", "sysselsättning",
        "sysselsatt", "arbetslös", "unemployment", "yrke", "occupation",
        "lön", "wage", "salary",
    ],
    "economy": [
        "gdp", "bnp", "income", "inkomst", "ekonomi", "economy", "economic",
        "finans", "finance", "skatt", "tax", "pris", "price", "inflation",
        "handel", "trade", "export", "import", "företag", "business",
        "närings",
    ],
    "housing": [
        "housing", "bostad", "boende", "dwelling", "lägenhet", "apartment",
        "hus", "house", "hyra", "rent", "fastighet", "property", "byggnation",
        "construction",
    ],
    "environment": [
        "miljö", "environment", "utsläpp", "emission", "klimat", "climate",
        "energi", "energy", "avfall", "waste", "vatten", "water", "luft",
        "air",
    ],
    "education": [
        "utbildning", "education", "skola", "school", "student", "elev",
        "universitet", "university", "högskola", "examen", "degree",
    ],
    "health": [
        "hälsa", "health", "sjukvård", "healthcare", "sjukdom", "disease",
        "vård", "care", "dödsorsak", "cause of death",
    ],
    "transport": [
        "transport", "trafik", "traffic", "fordon", "vehicle", "bil", "car",
        "kollektivtrafik", "public transport", "flyg", "aviation", "järnväg",
        "railway", "resa", "travel", "gods", "freight", "infrastruktur",
        "infrastructure",
    ],
}


def register(mcp: FastMCP) -> None:
    """Registrera metadata-verktyg på MCP-servern."""

    @mcp.tool()
    async def get_api_status(ctx: Context) -> dict[str, Any]:
        """Hämta SCB:s API-konfiguration: version, språk, rate limits och licens.

        Returnerar `{apiVersion, appVersion, languages, defaultLanguage,
        maxDataCells, maxCallsPerTimeWindow, timeWindow, license, ...}`.
        Bra för att verifiera att API:et är tillgängligt och kontrollera
        aktuella gränsvärden (normalt 30 anrop per 10 sekunder).
        """
        client = _get_client(ctx)
        return await client.get_config()

    @mcp.tool()
    async def search_tables(
        ctx: Context,
        query: str | None = None,
        category: str | None = None,
        past_days: int | None = None,
        include_discontinued: bool = False,
        page_number: int = 1,
        page_size: int = 20,
        language: str = "sv",
    ) -> dict[str, Any]:
        """Sök statistiktabeller i SCB:s databas.

        VIKTIGT: svenska söktermer ger betydligt bättre resultat. Använd
        "befolkning" istället för "population", "arbetslöshet" istället för
        "unemployment", "inkomst" istället för "income".

        Returnerar `{query, tables: [{id, title, description, period,
        variables, updated, ...}], pagination, metadata}`. Använd `id`-
        fältet för efterföljande anrop till `get_table_info`,
        `get_table_variables` eller `get_table_data`.

        Args:
            query: Sökfras (svenska termer rekommenderas).
            category: Valfri kategoriskategori för klientsidofiltrering.
                Tillåtna värden: "population", "labour", "economy", "housing",
                "environment", "education", "health", "transport".
            past_days: Endast tabeller uppdaterade de senaste N dagarna.
            include_discontinued: Inkludera nedlagda tabeller.
            page_number: Sidnummer (1-baserat).
            page_size: Antal per sida (max 100).
            language: Språkkod "sv" eller "en" (standard: "sv").
        """
        if category and category.lower() not in CATEGORY_KEYWORDS:
            return {
                "error": f"Ogiltig kategori \"{category}\".",
                "valid_categories": list(CATEGORY_KEYWORDS.keys()),
            }

        page_size = min(max(page_size, 1), 100)
        client = _get_client(ctx)
        result = await client.search_tables(
            query=query,
            past_days=past_days,
            include_discontinued=include_discontinued,
            page_number=page_number,
            page_size=page_size,
            lang=language,
        )

        tables = result.get("tables", [])

        filtered = tables
        if category:
            keywords = CATEGORY_KEYWORDS[category.lower()]
            filtered = []
            for t in tables:
                haystack = " ".join(
                    [
                        t.get("label", "") or "",
                        t.get("description", "") or "",
                        *(t.get("variableNames") or []),
                    ]
                ).lower()
                if any(kw in haystack for kw in keywords):
                    filtered.append(t)

        return {
            "query": {
                "search_term": query,
                "category_filter": category,
                "language": language,
                "page_number": page_number,
                "page_size": page_size,
            },
            "tables": [
                {
                    "id": t.get("id"),
                    "title": t.get("label"),
                    "description": t.get("description"),
                    "period": {
                        "start": t.get("firstPeriod"),
                        "end": t.get("lastPeriod"),
                    },
                    "variables": t.get("variableNames") or [],
                    "updated": t.get("updated"),
                    "source": t.get("source"),
                    "discontinued": t.get("discontinued", False),
                }
                for t in filtered
            ],
            "pagination": result.get("page", {}),
            "metadata": {
                "total_returned": len(tables),
                "total_filtered": len(filtered),
                "has_category_filter": bool(category),
            },
        }

    @mcp.tool()
    async def get_table_info(
        ctx: Context,
        table_id: str,
        language: str = "sv",
    ) -> dict[str, Any]:
        """Hämta översiktlig metadata om en tabell (variabler, källa, storlek).

        Returnerar `{table_id, table_name, source, updated, total_cells,
        variables: [{code, label, value_count}], contacts, notes}`. Bra
        första steg innan `get_table_variables` eller `get_table_data`.

        Args:
            table_id: Tabell-ID (t.ex. "TAB637", "TAB4552").
            language: Språkkod "sv" eller "en".
        """
        client = _get_client(ctx)
        metadata = await client.get_table_metadata(table_id, lang=language)

        dimensions = metadata.get("dimension") or {}
        variables = [
            {
                "code": code,
                "label": dim.get("label"),
                "value_count": len((dim.get("category") or {}).get("index") or {}),
            }
            for code, dim in dimensions.items()
        ]

        size = metadata.get("size") or []
        total_cells = 1
        for s in size:
            total_cells *= s

        extension = metadata.get("extension") or {}
        return {
            "table_id": table_id,
            "table_name": metadata.get("label"),
            "source": metadata.get("source") or "Statistiska centralbyrån",
            "updated": metadata.get("updated"),
            "total_cells": total_cells,
            "variables": variables,
            "contacts": [
                {
                    "name": c.get("name"),
                    "email": c.get("mail"),
                    "phone": c.get("phone"),
                }
                for c in extension.get("contact") or []
            ],
            "notes": [
                {"text": n.get("text"), "mandatory": n.get("mandatory", False)}
                for n in extension.get("notes") or []
            ],
        }

    @mcp.tool()
    async def get_table_variables(
        ctx: Context,
        table_id: str,
        variable_name: str | None = None,
        language: str = "sv",
        sample_size: int = 20,
    ) -> dict[str, Any]:
        """Hämta tillgängliga variabler och deras värden för en tabell.

        Nödvändigt före `get_table_data` för att veta vilka värdekoder som
        kan användas i `selection`. Varje variabel returneras med ett urval
        värden + totalt antal.

        Args:
            table_id: Tabell-ID (t.ex. "TAB637").
            variable_name: Valfritt filter - visa bara denna variabel (t.ex.
                "Region", "Tid").
            language: Språkkod "sv" eller "en".
            sample_size: Antal värden att inkludera per variabel (standard: 20).
        """
        client = _get_client(ctx)
        metadata = await client.get_table_metadata(table_id, lang=language)

        dimensions = metadata.get("dimension") or {}
        if not dimensions:
            return {
                "table_id": table_id,
                "error": "Ingen variabelinformation tillgänglig.",
            }

        items = list(dimensions.items())
        if variable_name:
            vn = variable_name.lower()
            items = [
                (code, dim)
                for code, dim in items
                if code.lower() == vn
                or vn in (dim.get("label") or "").lower()
            ]
            if not items:
                return {
                    "table_id": table_id,
                    "error": f"Variabel \"{variable_name}\" hittades inte.",
                    "available_variables": [
                        {"code": c, "label": d.get("label")}
                        for c, d in dimensions.items()
                    ],
                }

        variables: list[dict[str, Any]] = []
        for code, dim in items:
            category = dim.get("category") or {}
            index_map: dict[str, int] = category.get("index") or {}
            labels: dict[str, str] = category.get("label") or {}
            codes = list(index_map.keys())

            sample = [
                {"code": c, "label": labels.get(c, c)}
                for c in codes[:sample_size]
            ]
            variables.append(
                {
                    "code": code,
                    "label": dim.get("label"),
                    "total_values": len(codes),
                    "sample_values": sample,
                    "has_more": len(codes) > sample_size,
                    "usage_example": {code: [codes[0]] if codes else []},
                }
            )

        return {
            "table_id": table_id,
            "table_name": metadata.get("label"),
            "variables": variables,
            "metadata": {
                "total_variables": len(dimensions),
                "filtered": variable_name,
                "source": metadata.get("source") or "Statistiska centralbyrån",
                "updated": metadata.get("updated"),
            },
        }
