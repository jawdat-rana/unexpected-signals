"""OV-fiets (NS rental bike) availability per pick-up point.

Read from openOV's keyless mirror of the NS places API (fiets.openov.nl), which
lists about 300 locations with the number of bikes available right now.
"""

from __future__ import annotations

from typing import Any

from .parking import to_iso

STATUS_COLUMNS = ["fetched_at", "location", "bikes", "open", "feed_time"]

CATALOGUE_COLUMNS = ["location", "station", "name", "city", "latitude", "longitude"]


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse(payload: dict, fetched_at: str) -> tuple[list[dict], list[dict]]:
    """Return (status rows, catalogue rows)."""
    status, catalogue = [], []
    for code, loc in sorted((payload.get("locaties") or {}).items()):
        extra = loc.get("extra") or {}
        code = extra.get("locationCode") or code
        status.append(
            {
                "fetched_at": fetched_at,
                "location": code,
                "bikes": _int(extra.get("rentalBikes")),
                "open": loc.get("open"),
                "feed_time": to_iso(extra.get("fetchTime")),
            }
        )
        catalogue.append(
            {
                "location": code,
                "station": loc.get("stationCode"),
                "name": loc.get("description") or loc.get("name"),
                "city": loc.get("city"),
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
            }
        )
    return status, catalogue
