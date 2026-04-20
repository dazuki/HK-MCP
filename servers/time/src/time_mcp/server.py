"""MCP-server för tid och tidszoner."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel
from tzlocal import get_localzone_name

from hk_core import create_server, run_server


DEFAULT_LOCAL_TZ = "Europe/Stockholm"


def _detect_local_tz() -> str:
    """Upptäck lokal tidszon via tzlocal, fall tillbaka till Europe/Stockholm."""
    try:
        name = get_localzone_name()
    except Exception:
        name = None
    return name or DEFAULT_LOCAL_TZ


LOCAL_TZ = _detect_local_tz()


class TimeResult(BaseModel):
    timezone: str
    datetime: str
    day_of_week: str
    is_dst: bool


class TimeConversionResult(BaseModel):
    source: TimeResult
    target: TimeResult
    time_difference: str


def _get_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ToolError(f"Ogiltig tidszon: {name}") from exc


def _format_offset_diff(hours: float) -> str:
    if hours.is_integer():
        return f"{hours:+.1f}h"
    # För tidszoner med brutna offsets (t.ex. Asia/Kathmandu UTC+5:45)
    return f"{hours:+.2f}".rstrip("0").rstrip(".") + "h"


mcp = create_server(
    name="Tid",
    instructions=(
        "Du har verktyg för att hämta aktuell tid i valfri IANA-tidszon "
        "och konvertera tider mellan tidszoner. Tidszoner anges i IANA-"
        "format (t.ex. 'Europe/Stockholm', 'America/New_York'). Om "
        f"användaren inte anger en tidszon, använd '{LOCAL_TZ}' som lokal."
    ),
    package_file=__file__,
)


@mcp.tool()
def get_current_time(timezone: str = LOCAL_TZ) -> TimeResult:
    """Hämta aktuell tid i en angiven tidszon.

    Args:
        timezone: IANA-tidszonsnamn (t.ex. 'Europe/Stockholm',
            'America/New_York'). Default: serverns lokala tidszon.
    """
    zone = _get_zone(timezone)
    now = datetime.now(zone)
    return TimeResult(
        timezone=timezone,
        datetime=now.isoformat(timespec="seconds"),
        day_of_week=now.strftime("%A"),
        is_dst=bool(now.dst()),
    )


@mcp.tool()
def convert_time(
    source_timezone: str,
    time: str,
    target_timezone: str,
) -> TimeConversionResult:
    """Konvertera en tid mellan två tidszoner.

    Tolkar `time` som en tid idag i `source_timezone` och räknar om
    till motsvarande tid i `target_timezone`.

    Args:
        source_timezone: IANA-tidszon som `time` tolkas i.
        time: Tid i 24-timmarsformat (HH:MM).
        target_timezone: IANA-tidszon att konvertera till.
    """
    source_zone = _get_zone(source_timezone)
    target_zone = _get_zone(target_timezone)

    try:
        parsed = datetime.strptime(time, "%H:%M").time()
    except ValueError as exc:
        raise ToolError(
            "Ogiltigt tidsformat. Förväntade HH:MM (24-timmars)."
        ) from exc

    now = datetime.now(source_zone)
    source_dt = datetime(
        now.year, now.month, now.day,
        parsed.hour, parsed.minute,
        tzinfo=source_zone,
    )
    target_dt = source_dt.astimezone(target_zone)

    source_offset = source_dt.utcoffset() or timedelta()
    target_offset = target_dt.utcoffset() or timedelta()
    hours_diff = (target_offset - source_offset).total_seconds() / 3600

    return TimeConversionResult(
        source=TimeResult(
            timezone=source_timezone,
            datetime=source_dt.isoformat(timespec="seconds"),
            day_of_week=source_dt.strftime("%A"),
            is_dst=bool(source_dt.dst()),
        ),
        target=TimeResult(
            timezone=target_timezone,
            datetime=target_dt.isoformat(timespec="seconds"),
            day_of_week=target_dt.strftime("%A"),
            is_dst=bool(target_dt.dst()),
        ),
        time_difference=_format_offset_diff(hours_diff),
    )


def main():
    """Starta MCP-servern."""
    run_server(mcp)


if __name__ == "__main__":
    main()
