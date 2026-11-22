"""Parse NDW's measurement-site table (DATEX II MeasurementSiteTablePublication).

The table lists every traffic sensor with its name, number of lanes and
location. We keep one row per site so sensors can be picked on a map and so
live measurements can be grouped by road.

NDW does not publish the road as a field, so `road` is derived:

- Rijkswaterstaat motorway loops have ids like RWS01_MONIBAS_0021hrl0403ra,
  where the first three digits are the road number (002 -> A2).
- Other sites often name the road in their name or id: "N208 km 5.645 Li",
  "PFR07_101607_N354_Z".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from typing import IO

from .datex import find_first, iter_elements, local, text_of, to_float

MONIBAS = re.compile(r"MONIBAS_(\d{3})\d")
# "N208 km 5.645", "PFR07_101607_N354_Z", "PGL10_N787-02_hmp_12.5"
ROAD_IN_TEXT = re.compile(r"(?<![A-Za-z0-9])([AN])\s?0*(\d{1,3})(?![0-9])")


@dataclass
class Site:
    site_id: str
    name: str | None
    road: str | None
    lanes: int | None
    latitude: float | None
    longitude: float | None
    carriageway: str | None


COLUMNS = [f.name for f in fields(Site)]


def road_of(site_id: str, name: str | None) -> str | None:
    """Best guess of the road a site is on, like 'A2' or 'N208', or None."""
    match = MONIBAS.search(site_id)
    if match:
        number = int(match.group(1))
        # Rijkswaterstaat numbers motorways and the national N-roads it runs
        # in one series; 1-99 are A-roads, higher numbers are N-roads.
        return f"A{number}" if number < 100 else f"N{number}"
    for text in (name, site_id):
        match = ROAD_IN_TEXT.search(text or "")
        if match:
            return f"{match.group(1)}{int(match.group(2))}"
    return None


def parse(source: IO[bytes]) -> list[Site]:
    out: list[Site] = []
    for elem in iter_elements(source, "measurementSite"):
        site_id = elem.get("id", "")
        if not site_id:
            continue
        name_elem = find_first(elem, "measurementSiteName")
        name = text_of(name_elem, "value") if name_elem is not None else None
        lanes = text_of(elem, "measurementSiteNumberOfLanes")
        carriageway = None
        for child in elem.iter():
            if local(child.tag) == "carriageway" and child.text:
                carriageway = child.text.strip()
                break
        out.append(
            Site(
                site_id=site_id,
                name=name,
                road=road_of(site_id, name),
                lanes=int(lanes) if lanes and lanes.isdigit() else None,
                latitude=to_float(text_of(elem, "latitude")),
                longitude=to_float(text_of(elem, "longitude")),
                carriageway=carriageway,
            )
        )
    return out


def motorway_main_lanes(sites: list[dict[str, str]]) -> dict[str, str]:
    """site_id -> road for motorway sites on the main carriageway.

    Slip roads and parallel lanes are left out so a road's summary describes
    the motorway itself, not the junctions along it.
    """
    return {
        s["site_id"]: s["road"]
        for s in sites
        if s.get("road", "").startswith("A") and s.get("carriageway") == "mainCarriageway"
    }
