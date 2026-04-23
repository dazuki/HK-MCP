"""MCP-verktyg för att hämta och förhandsvisa data från SCB:s tabeller."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from scb_mcp.clients import SCBClient


def _get_client(ctx: Context) -> SCBClient:
    return ctx.request_context.lifespan_context.scb


_DIMENSION_BASE_NAMES: dict[str, str] = {
    "Region": "region",
    "Alder": "age",
    "Kon": "sex",
    "Tid": "time",
    "UtbildningsNiva": "education_level",
    "ContentsCode": "observation_type",
    "Sysselsattning": "employment_status",
    "Civilstand": "marital_status",
    "Familjetyp": "family_type",
}


def _dimension_key(name: str) -> str:
    return _DIMENSION_BASE_NAMES.get(name, name.lower())


def _transform_json_stat2(
    dataset: dict[str, Any],
    selection: dict[str, list[str]] | None,
) -> dict[str, Any]:
    """Omvandla JSON-stat2 till platta rader med codes + labels per dimension."""
    dimensions = dataset.get("dimension") or {}
    values = dataset.get("value") or []
    if not dimensions or not values:
        return {
            "query": {"selection": selection or {}},
            "data": [],
            "metadata": {
                "source": dataset.get("source") or "Statistiska centralbyrån",
                "updated": dataset.get("updated"),
                "table_name": dataset.get("label"),
            },
            "summary": {"total_records": 0, "has_data": False},
        }

    dim_items = list(dimensions.items())
    dim_codes: list[list[str]] = []
    dim_labels: list[dict[str, str]] = []
    dim_sizes: list[int] = []
    for _, dim in dim_items:
        category = dim.get("category") or {}
        codes = list((category.get("index") or {}).keys())
        dim_codes.append(codes)
        dim_labels.append(category.get("label") or {})
        dim_sizes.append(len(codes))

    records: list[dict[str, Any]] = []
    for flat_index, value in enumerate(values):
        if value is None:
            continue

        record: dict[str, Any] = {}
        remaining = flat_index
        indices: list[int] = [0] * len(dim_items)
        for i in range(len(dim_items) - 1, -1, -1):
            indices[i] = remaining % dim_sizes[i]
            remaining //= dim_sizes[i]

        for i, (name, _) in enumerate(dim_items):
            code = dim_codes[i][indices[i]]
            label = dim_labels[i].get(code, code)
            base = _dimension_key(name)
            record[f"{base}_code"] = code
            record[f"{base}_name"] = label
        record["value"] = value
        records.append(record)

    extension = dataset.get("extension") or {}
    px_ext = extension.get("px") or {}
    table_id = px_ext.get("tableid") or (dataset.get("id") or [None])[0]

    return {
        "query": {
            "selection": selection or {},
            "table_id": table_id,
        },
        "data": records,
        "metadata": {
            "source": dataset.get("source") or "Statistiska centralbyrån",
            "updated": dataset.get("updated"),
            "table_name": dataset.get("label"),
            "data_shape": dataset.get("size"),
            "dimensions": [
                {
                    "name": name,
                    "label": dim.get("label"),
                    "values_count": dim_sizes[i],
                }
                for i, (name, dim) in enumerate(dim_items)
            ],
        },
        "summary": {
            "total_records": len(records),
            "has_data": bool(records),
        },
    }


def _effective_selection(dataset: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, dim in (dataset.get("dimension") or {}).items():
        result[name] = list(((dim.get("category") or {}).get("index") or {}).keys())
    return result


def register(mcp: FastMCP) -> None:
    """Registrera data-verktyg på MCP-servern."""

    @mcp.tool()
    async def get_table_data(
        ctx: Context,
        table_id: str,
        selection: dict[str, list[str]] | None = None,
        language: str = "sv",
    ) -> dict[str, Any]:
        """Hämta statistikdata från en tabell.

        Utan `selection` använder API:et smarta standardvärden (senaste
        tidsperiod, alla kategorier). Svaret omvandlas från JSON-stat2 till
        platta rader där varje dimension representeras av både kod och
        läsbart namn (t.ex. `region_code`, `region_name`).

        VIKTIGT: använd `preview_data` först om du är osäker på storleken -
        tabeller kan ha hundratusentals celler. API:et har en gräns på
        150 000 celler per förfrågan och 30 anrop per 10 sekunder.

        Urvalssyntax:
        - Specifika värden: `{"Region": ["1441", "0180"]}`
        - Alla värden: `{"Region": ["*"]}`
        - Senaste N: `{"Tid": ["TOP(5)"]}` eller `["BOTTOM(5)"]`
        - Intervall: `{"Tid": ["RANGE(2020,2024)"]}`

        Args:
            table_id: Tabell-ID (t.ex. "TAB637").
            selection: Valfritt variabelurval. Variabelnamn (nycklar) är
                skiftlägeskänsliga - använd `get_table_variables` först.
            language: Språkkod "sv" eller "en".
        """
        client = _get_client(ctx)
        dataset = await client.get_table_data(table_id, selection, lang=language)
        structured = _transform_json_stat2(dataset, selection)
        structured["query"]["effective_selection"] = _effective_selection(dataset)
        structured["query"]["language"] = language
        return structured

    @mcp.tool()
    async def preview_data(
        ctx: Context,
        table_id: str,
        selection: dict[str, list[str]] | None = None,
        language: str = "sv",
    ) -> dict[str, Any]:
        """Hämta en begränsad förhandsvisning av data (max ~50 rader).

        Säkrare än `get_table_data` för initial utforskning - begränsar
        automatiskt varje dimension till 1-2 värden och använder `TOP(1)`
        för tidsvariabler. Om `selection` anges begränsas `*`-wildcards
        och stora `TOP(N)`/`BOTTOM(N)`.

        Args:
            table_id: Tabell-ID (t.ex. "TAB637").
            selection: Valfritt variabelurval som begränsas för förhandsvisning.
            language: Språkkod "sv" eller "en".
        """
        client = _get_client(ctx)
        metadata = await client.get_table_metadata(table_id, lang=language)
        dimensions = metadata.get("dimension") or {}

        preview_selection: dict[str, list[str]] = {}
        if selection:
            for key, values in selection.items():
                new_values: list[str] = []
                for v in values:
                    if v == "*":
                        new_values.append("TOP(2)")
                    elif v.startswith("TOP(") and v.endswith(")"):
                        try:
                            n = int(v[4:-1])
                            new_values.append(f"TOP({min(n, 3)})")
                        except ValueError:
                            new_values.append(v)
                    elif v.startswith("BOTTOM(") and v.endswith(")"):
                        try:
                            n = int(v[7:-1])
                            new_values.append(f"BOTTOM({min(n, 3)})")
                        except ValueError:
                            new_values.append(v)
                    else:
                        new_values.append(v)
                preview_selection[key] = new_values[:2] if len(new_values) > 2 else new_values
        else:
            for code, dim in dimensions.items():
                index = (dim.get("category") or {}).get("index") or {}
                codes = list(index.keys())
                low = code.lower()
                if low in ("tid", "time"):
                    preview_selection[code] = ["TOP(1)"]
                elif low == "contentscode":
                    preview_selection[code] = codes[:1] or ["*"]
                elif len(codes) <= 3:
                    preview_selection[code] = codes
                else:
                    preview_selection[code] = codes[:2]

        for code, dim in dimensions.items():
            if code not in preview_selection:
                index = (dim.get("category") or {}).get("index") or {}
                codes = list(index.keys())
                preview_selection[code] = codes if len(codes) <= 3 else codes[:2]

        dataset = await client.get_table_data(
            table_id, preview_selection, lang=language
        )
        structured = _transform_json_stat2(dataset, preview_selection)
        structured["query"]["effective_selection"] = _effective_selection(dataset)
        structured["query"]["language"] = language
        structured["preview_info"] = {
            "is_preview": True,
            "original_selection": selection,
            "preview_selection": preview_selection,
            "note": (
                "Detta är en begränsad förhandsvisning. Använd `get_table_data` "
                "för fullständig dataset."
            ),
        }
        return structured
