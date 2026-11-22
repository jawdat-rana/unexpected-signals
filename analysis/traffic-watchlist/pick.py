"""Pick traffic sensors to store in full: next to busy bridges and at borders.

Reads the site catalogue and the collected bridge openings from a checkout of
the `data` branch and writes watchlist.csv next to this script. Copy the ids
into config.toml under [traffic] sites.

    python analysis/traffic-watchlist/pick.py path/to/data-branch/data
"""

from __future__ import annotations

import csv
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent

# Motorway border crossings into Germany and Belgium, a point just on the Dutch
# side of each. Sensors are taken from that road, nearest the border first.
BORDERS = [
    ("A7 Nieuweschans (DE)", "A7", 53.185, 7.195),
    ("A37 Zwartemeer (DE)", "A37", 52.715, 7.050),
    ("A1 De Lutte (DE)", "A1", 52.305, 7.040),
    ("A35 Glanerbrug (DE)", "A35", 52.215, 6.975),
    ("A12 Babberich (DE)", "A12", 51.905, 6.120),
    ("A77 Gennep (DE)", "A77", 51.690, 6.005),
    ("A67 Venlo (DE)", "A67", 51.390, 6.205),
    ("A76 Bocholtz (DE)", "A76", 50.860, 6.015),
    ("A2 Eijsden (BE)", "A2", 50.775, 5.705),
    ("A67 Budel (BE)", "A67", 51.285, 5.440),
    ("A58 Sluiskil tunnel side (BE)", "N62", 51.235, 3.800),
    ("A16 Hazeldonk (BE)", "A16", 51.495, 4.745),
    ("A4 Hoogerheide (BE)", "A4", 51.420, 4.320),
]
BORDER_RADIUS_M = 8000
PER_DIRECTION = 2  # nearest sensors in each direction of travel

BRIDGE_RADIUS_M = 400
BRIDGE_COUNT = 10  # busiest bridges by weekday rush-hour openings that have sensors
LIVE_BRIDGE_COUNT = 5  # bridges most often seen opening live that have sensors
SIDE = re.compile(r"hr([lr])|_([LR])P$|([LR])$")


def side_of(site_id: str) -> str:
    """'l' or 'r' for the carriageway a sensor is on, '?' when the id doesn't say."""
    match = SIDE.search(site_id)
    return next((g.lower() for g in match.groups() if g), "?") if match else "?"


def metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6_371_000 * math.hypot(dlat, dlon)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def bridges(data: Path) -> tuple[list[tuple[float, float, int]], list[tuple[float, float, int]]]:
    latest: dict[str, dict[str, str]] = {}
    for path in sorted((data / "bridges").rglob("*.csv")):
        for row in load_csv(path):
            old = latest.get(row["record_id"])
            if old is None or int(row["version"]) > int(old["version"]):
                latest[row["record_id"]] = row
    rush: Counter[tuple[float, float]] = Counter()
    live: Counter[tuple[float, float]] = Counter()
    for row in latest.values():
        key = (round(float(row["latitude"]), 5), round(float(row["longitude"]), 5))
        start = datetime.fromisoformat(row["start_time"][:19])
        local_hour = (start.hour + 1) % 24  # CET; good enough for picking sites
        if row["probability"] == "certain":
            live[key] += 1
        elif start.weekday() < 5 and local_hour in (7, 8, 16, 17):
            rush[key] += 1
    return [(*k, n) for k, n in rush.most_common()], [(*k, n) for k, n in live.most_common()]


def main(data: Path) -> None:
    catalogue = load_csv(data / "traffic_sites_catalogue.csv")
    located = [s for s in catalogue if s["latitude"] and s["longitude"]]
    picked: dict[str, dict[str, object]] = {}

    def add(site: dict[str, str], group: str, place: str, distance: float) -> None:
        if site["site_id"] not in picked:
            picked[site["site_id"]] = {
                "site_id": site["site_id"],
                "group": group,
                "place": place,
                "road": site["road"],
                "carriageway": site["carriageway"],
                "distance_m": round(distance),
                "latitude": site["latitude"],
                "longitude": site["longitude"],
            }

    rush, live = bridges(data)
    # MONICA ids are per-lane duplicates of the MONIBAS site at the same spot.
    main_lanes = [
        s
        for s in located
        if s["carriageway"] == "mainCarriageway" and "_MONICA_" not in s["site_id"]
    ]
    for group, chosen, wanted in (
        ("bridge_rush_hour", rush, BRIDGE_COUNT),
        ("bridge_live", live, LIVE_BRIDGE_COUNT),
    ):
        found = 0
        for lat, lon, openings in chosen:
            if found == wanted:
                break
            near = [
                (metres(lat, lon, float(s["latitude"]), float(s["longitude"])), s)
                for s in main_lanes
            ]
            near = [(d, s) for d, s in near if d <= BRIDGE_RADIUS_M]
            if not near:
                continue
            found += 1
            place = f"bridge {lat:.4f},{lon:.4f} ({openings} openings)"
            for distance, site in sorted(near, key=lambda x: x[0]):
                add(site, group, place, distance)

    for place, road, lat, lon in BORDERS:
        on_road = sorted(
            (
                (metres(lat, lon, float(s["latitude"]), float(s["longitude"])), s)
                for s in main_lanes
                if s["road"] == road
            ),
            key=lambda x: x[0],
        )
        per_side: Counter[str] = Counter()
        for distance, site in on_road:
            side = side_of(site["site_id"])
            if distance <= BORDER_RADIUS_M and per_side[side] < PER_DIRECTION:
                per_side[side] += 1
                add(site, "border", place, distance)

    rows = list(picked.values())
    with (HERE / "watchlist.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    per_place: dict[str, int] = defaultdict(int)
    for row in rows:
        per_place[f"{row['group']}: {row['place']}"] += 1
    for place, n in per_place.items():
        print(f"{n:3d}  {place}")
    print(f"{len(rows)} sites written to {HERE / 'watchlist.csv'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
