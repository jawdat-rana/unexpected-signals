"""Parse NDW speed and flow measurements (DATEX II MeasuredDataPublication).

Every measurement site reports per lane (or per vehicle class) values. We
collapse those to one row per site per measurement time:

- speed_kmh: mean of the valid lane speeds (NDW uses -1 for "no data")
- flow_veh_h: sum of the valid lane flows, in vehicles per hour

Keeping every site in the country every 15 minutes would be millions of rows a
day, so the collector stores (1) a national summary per snapshot and (2) full
rows only for the sites listed in config.toml.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from statistics import fmean
from typing import IO

from .datex import find_first, iter_elements, local, text_of, to_float, xsi_type


@dataclass
class SiteMeasurement:
    site_id: str
    measured_at: str | None
    speed_kmh: float | None
    flow_veh_h: float | None
    lanes_with_speed: int
    lanes_with_flow: int


SITE_COLUMNS = [f.name for f in fields(SiteMeasurement)]
SUMMARY_COLUMNS = [
    "fetched_at",
    "sites_reporting",
    "sites_with_speed",
    "mean_speed_kmh",
    "total_flow_veh_h",
]


def _valid(value: float | None) -> bool:
    return value is not None and value >= 0


def parse(source: IO[bytes]) -> list[SiteMeasurement]:
    out: list[SiteMeasurement] = []
    for site in iter_elements(source, "siteMeasurements"):
        ref = find_first(site, "measurementSiteReference")
        site_id = ref.get("id", "") if ref is not None else ""
        measured_at = text_of(site, "measurementTimeDefault")
        speeds: list[float] = []
        flows: list[float] = []
        for basic in site.iter():
            if local(basic.tag) != "basicData":
                continue
            kind = xsi_type(basic)
            if kind == "TrafficSpeed":
                value = to_float(text_of(basic, "speed"))
                if _valid(value):
                    speeds.append(value)  # type: ignore[arg-type]
            elif kind == "TrafficFlow":
                value = to_float(text_of(basic, "vehicleFlowRate"))
                if _valid(value):
                    flows.append(value)  # type: ignore[arg-type]
        out.append(
            SiteMeasurement(
                site_id=site_id,
                measured_at=measured_at,
                speed_kmh=round(fmean(speeds), 1) if speeds else None,
                flow_veh_h=sum(flows) if flows else None,
                lanes_with_speed=len(speeds),
                lanes_with_flow=len(flows),
            )
        )
    return out


def summarise(rows: list[SiteMeasurement], fetched_at: str) -> dict[str, object]:
    speeds = [r.speed_kmh for r in rows if r.speed_kmh is not None]
    flows = [r.flow_veh_h for r in rows if r.flow_veh_h is not None]
    return {
        "fetched_at": fetched_at,
        "sites_reporting": len(rows),
        "sites_with_speed": len(speeds),
        "mean_speed_kmh": round(fmean(speeds), 2) if speeds else None,
        "total_flow_veh_h": round(sum(flows)) if flows else None,
    }


def select(rows: list[SiteMeasurement], site_ids: set[str]) -> list[dict[str, object]]:
    return [asdict(r) for r in rows if r.site_id in site_ids]
