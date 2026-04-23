"""MCP-server för tid och tidszoner."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field
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
    """Tid i en specifik tidszon."""

    timezone: str = Field(description="IANA-tidszon (t.ex. 'Europe/Stockholm').")
    datetime: str = Field(
        description=(
            "ISO 8601-datumtid med offset, sekundprecision "
            "(t.ex. '2026-04-23T15:00:00+02:00')."
        )
    )
    day_of_week: str = Field(
        description="Veckodag på engelska ('Monday', 'Tuesday', ..., 'Sunday')."
    )
    is_dst: bool = Field(
        description="True om sommartid gäller för tidszonen just nu."
    )


class TimeConversionResult(BaseModel):
    """Resultat av tidskonvertering mellan två tidszoner."""

    source: TimeResult = Field(description="Tid i ursprungstidszonen.")
    target: TimeResult = Field(description="Motsvarande tid i måltidszonen.")
    time_difference: str = Field(
        description=(
            "Tidsskillnad från source till target, format '+/-Nh' "
            "(t.ex. '-6.0h', '+4.75h' för halvtimmes-offsets)."
        )
    )


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
        "och konvertera tider mellan tidszoner.\n"
        "\n"
        "Format:\n"
        "- Tidszoner: IANA-namn (t.ex. 'Europe/Stockholm', "
        "'America/New_York', 'Asia/Tokyo', 'UTC'). Ogiltiga namn ger fel - "
        "använd aldrig förkortningar som 'CET' eller 'EST'.\n"
        f"- Lokal tidszon (använd när användaren inte anger någon): "
        f"`{LOCAL_TZ}`.\n"
        "- `datetime` returneras som ISO 8601 med offset "
        "(`YYYY-MM-DDTHH:MM:SS+ZZ:ZZ`).\n"
        "- `day_of_week` kommer på engelska - översätt till svenska om "
        "användarens fråga är på svenska.\n"
        "- `is_dst` (bool) visar om sommartid gäller. DST-byten hanteras "
        "automatiskt av verktygen.\n"
        "\n"
        "Regler:\n"
        "- Fråga inte efter tidszon om användarens kontext är tydlig - "
        f"anta `{LOCAL_TZ}` som default.\n"
        "- `convert_time` räknar på **dagens datum** i källzonen. Om den "
        "konverterade tiden hamnar på annat datum syns det i "
        "`target.datetime` - kontrollera det när tidsskillnaden är stor."
    ),
    package_file=__file__,
)


@mcp.tool()
def get_current_time(timezone: str = LOCAL_TZ) -> TimeResult:
    """Hämta aktuell tid i en angiven tidszon.

    Returnerar `{timezone, datetime, day_of_week, is_dst}`. `datetime` är
    ISO 8601 med offset, `day_of_week` är engelska, `is_dst` visar om
    sommartid gäller. Ogiltig tidszon kastar ToolError.

    Args:
        timezone: IANA-tidszonsnamn (t.ex. 'Europe/Stockholm',
            'America/New_York', 'UTC'). Använd inte förkortningar som
            'CET'. Default: serverns lokala tidszon.
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

    Tolkar `time` som en tid **idag** i `source_timezone` och räknar om
    till motsvarande tid i `target_timezone`. Datumet i svaret kan skilja
    sig mellan source och target om tidsskillnaden korsar midnatt
    (t.ex. Stockholm 01:00 = NYC 19:00 föregående dag).

    Returnerar `{source, target, time_difference}` där source och target
    är TimeResult-objekt och `time_difference` är en sträng på formatet
    '+/-Nh' (t.ex. '-6.0h', '+4.75h').

    Args:
        source_timezone: IANA-tidszon som `time` tolkas i
            (t.ex. 'Europe/Stockholm').
        time: Tid i 24-timmarsformat 'HH:MM' (t.ex. '15:00').
        target_timezone: IANA-tidszon att konvertera till
            (t.ex. 'America/New_York').
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
