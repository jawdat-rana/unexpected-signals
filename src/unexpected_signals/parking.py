"""RDW's national parking data (SPDP): live free spaces per parking facility.

The index at npropendata.rdw.nl/parkingdata/v2/ lists about 15,000 facilities;
a few hundred have a `dynamicDataUrl` with live occupancy. Some of those need
a login (HTTP 401) and are skipped. The live feed only shows the present.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

STATUS_COLUMNS = [
    "fetched_at",
    "facility_id",
    "open",
    "full",
    "capacity",
    "vacant",
    "last_updated",
]

CATALOGUE_COLUMNS = [
    "facility_id",
    "name",
    "city",
    "province",
    "latitude",
    "longitude",
    "capacity",
    "usage",
    "operator",
    "limited_access",
]


def live_facilities(index: dict) -> list[dict[str, Any]]:
    """Facilities in the index that publish live data."""
    return [f for f in index.get("ParkingFacilities", []) if f.get("dynamicDataUrl")]


def to_iso(value: Any) -> str:
    """Unix seconds (int or numeric string) -> ISO UTC; anything else as text."""
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    return datetime.fromtimestamp(seconds, UTC).isoformat().replace("+00:00", "Z")


def parse_status(payload: dict, fetched_at: str) -> dict[str, Any] | None:
    info = payload.get("parkingFacilityDynamicInformation") or {}
    status = info.get("facilityActualStatus") or {}
    if not info.get("identifier") or not status:
        return None
    return {
        "fetched_at": fetched_at,
        "facility_id": info["identifier"],
        "open": status.get("open"),
        "full": status.get("full"),
        "capacity": status.get("parkingCapacity"),
        "vacant": status.get("vacantSpaces"),
        "last_updated": to_iso(status.get("lastUpdated")),
    }


def _first(items: Any) -> dict:
    return items[0] if isinstance(items, list) and items and isinstance(items[0], dict) else {}


def _latest(items: Any) -> dict:
    """The entry with the newest validityStartOfPeriod (RDW keeps old ones too)."""
    if not isinstance(items, list):
        return {}
    dicts = [i for i in items if isinstance(i, dict)]
    return max(dicts, key=lambda i: i.get("validityStartOfPeriod") or 0, default={})


def parse_static(payload: dict) -> dict[str, Any] | None:
    info = payload.get("parkingFacilityInformation") or {}
    if not info.get("identifier"):
        return None
    access = _first(info.get("accessPoints"))
    address = access.get("accessPointAddress") or {}
    location = _first(access.get("accessPointLocation"))
    spec = _latest(info.get("specifications"))
    operator = info.get("operator") or {}
    return {
        "facility_id": info["identifier"],
        "name": info.get("name") or info.get("description"),
        "city": address.get("city"),
        "province": address.get("province"),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "capacity": spec.get("capacity"),
        "usage": spec.get("usage"),
        "operator": operator.get("name"),
        "limited_access": info.get("limitedAccess"),
    }
