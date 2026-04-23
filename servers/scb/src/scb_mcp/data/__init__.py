"""Lokal data: komplett databas över svenska regioner för offline-uppslagning."""

from scb_mcp.data.regions import (
    ALL_REGIONS,
    Region,
    find_region,
    normalize_for_search,
    search_regions,
)

__all__ = [
    "ALL_REGIONS",
    "Region",
    "find_region",
    "normalize_for_search",
    "search_regions",
]
