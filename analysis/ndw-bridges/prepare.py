"""Planned bridge openings in North Holland, for the canal-bridges story.

Reads the bridge openings the collector stores on the `data` branch and writes
small chart CSVs to stories/canal-bridges/data/.

    git fetch origin data
    git worktree add data-branch origin/data
    python analysis/ndw-bridges/prepare.py data-branch/data

The NDW feed lists planned openings, published about a day ahead. For these
bridges they repeat almost exactly from one weekday to the next, so they work
as a timetable: the slots in which a bridge may open if a ship is waiting.
They are not confirmed openings.
"""

from __future__ import annotations

import csv
import math
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "stories" / "canal-bridges" / "data"
AMS = ZoneInfo("Europe/Amsterdam")

# Whole days of planned openings only: the collector started on 5 November and
# the feed reaches about a day and a half ahead.
FIRST, LAST = date(2026, 11, 6), date(2026, 11, 21)
RUSH_HOURS = {7, 8, 16, 17}  # 07:00-09:00 and 16:00-18:00, local time
NIGHT_HOURS = {23, 0, 1, 2, 3, 4, 5}

# The week shown as a "barcode" for one bridge, Monday to Sunday.
WEEK_START = date(2026, 11, 9)

# Towns used only to say where a bridge is ("near Alkmaar").
TOWNS = [
    ("Den Helder", 52.957, 4.760),
    ("Schagen", 52.787, 4.799),
    ("Alkmaar", 52.632, 4.748),
    ("Heiloo", 52.600, 4.700),
    ("Krommenie", 52.499, 4.763),
    ("Wormerveer", 52.491, 4.788),
    ("Zaandam", 52.439, 4.826),
    ("Spaarndam", 52.413, 4.682),
    ("Haarlem", 52.381, 4.637),
    ("Heemstede", 52.350, 4.620),
    ("Hillegom", 52.291, 4.583),
    ("Sassenheim", 52.225, 4.522),
    ("Amsterdam", 52.372, 4.880),
    ("Badhoevedorp", 52.334, 4.780),
    ("Aalsmeer", 52.264, 4.762),
    ("Leimuiden", 52.224, 4.668),
]


def route_of(lat: float, lon: float) -> str:
    """The three groups of bridges in the feed, which sit on separate waterways."""
    if lat > 52.6 or (lat > 52.42 and lon > 4.75):
        return "north"  # Den Helder - Alkmaar - Zaanstad
    if lon < 4.60 or (lon < 4.70 and lat > 52.25):
        return "haarlem"  # Spaarndam - Haarlem - Sassenheim
    return "amsterdam"  # Amsterdam - Schiphol - Leimuiden


def nearest_town(lat: float, lon: float) -> str:
    def km(t: tuple[str, float, float]) -> float:
        dlat = math.radians(t[1] - lat)
        dlon = math.radians(t[2] - lon) * math.cos(math.radians(lat))
        return 6371 * math.hypot(dlat, dlon)

    return min(TOWNS, key=km)[0]


def local(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")[:19] + "+00:00").astimezone(AMS)


def load(data: Path) -> list[dict]:
    """Planned openings, keeping only the latest version of each record."""
    latest: dict[str, dict[str, str]] = {}
    for path in sorted((data / "bridges").rglob("*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                old = latest.get(row["record_id"])
                if old is None or int(row["version"]) > int(old["version"]):
                    latest[row["record_id"]] = row
    out = []
    seen: set[tuple[str, str]] = set()
    for row in latest.values():
        if row["probability"] != "riskOf" or not row["end_time"]:
            continue
        start, end = local(row["start_time"]), local(row["end_time"])
        if not FIRST <= start.date() <= LAST:
            continue
        lat, lon = float(row["latitude"]), float(row["longitude"])
        # A few slots appear twice under different record ids; count them once.
        slot = (f"{lat:.4f},{lon:.4f}", row["start_time"][:16])
        if slot in seen:
            continue
        seen.add(slot)
        out.append(
            {
                "bridge": f"{lat:.4f},{lon:.4f}",
                "lat": lat,
                "lon": lon,
                "start": start,
                "minutes": (end - start).total_seconds() / 60,
            }
        )
    return out


def write_csv(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {(OUT / name).relative_to(HERE.parent.parent)}")


def main(data: Path) -> None:
    openings = load(data)
    days = [FIRST + timedelta(n) for n in range((LAST - FIRST).days + 1)]
    weekdays = sum(d.weekday() < 5 for d in days)
    weekend = len(days) - weekdays

    by_bridge: dict[str, list[dict]] = defaultdict(list)
    for o in openings:
        by_bridge[o["bridge"]].append(o)

    bridges = []
    for key, rows in by_bridge.items():
        lat, lon = rows[0]["lat"], rows[0]["lon"]
        wk = [r for r in rows if r["start"].weekday() < 5]
        bridges.append(
            {
                "bridge": key,
                "route": route_of(lat, lon),
                "near": nearest_town(lat, lon),
                "latitude": lat,
                "longitude": lon,
                "openings_per_day": round(len(rows) / len(days), 1),
                "weekday_openings": round(len(wk) / weekdays, 1),
                "weekend_openings": round((len(rows) - len(wk)) / weekend, 1),
                "rush_hour_openings": round(
                    sum(r["start"].hour in RUSH_HOURS for r in wk) / weekdays, 1
                ),
                "night_openings": round(
                    sum(r["start"].hour in NIGHT_HOURS for r in rows) / len(days), 1
                ),
                "minutes_open_per_day": round(sum(r["minutes"] for r in rows) / len(days)),
            }
        )
    bridges.sort(key=lambda b: (-b["latitude"], b["longitude"]))
    write_csv("bridges.csv", bridges)

    # Openings per bridge per hour of the day, by route.
    per_route = Counter(b["route"] for b in bridges)
    hours: Counter[tuple[str, int]] = Counter()
    for o in openings:
        hours[(route_of(o["lat"], o["lon"]), o["start"].hour)] += 1
    write_csv(
        "hours.csv",
        [
            {
                "route": route,
                "hour": hour,
                "openings": round(hours[(route, hour)] / per_route[route] / len(days), 2),
            }
            for route in ("north", "amsterdam", "haarlem")
            for hour in range(24)
        ],
    )

    # One week at the busiest bridge on the north route, every opening.
    north = [b for b in bridges if b["route"] == "north"]
    busiest = max(north, key=lambda b: b["openings_per_day"])
    week = [WEEK_START + timedelta(n) for n in range(7)]
    rows = []
    for o in sorted(by_bridge[busiest["bridge"]], key=lambda r: r["start"]):
        if o["start"].date() in week:
            start_h = o["start"].hour + o["start"].minute / 60
            rows.append(
                {
                    "date": o["start"].date().isoformat(),
                    "day": o["start"].strftime("%a %-d %b"),
                    "start_hour": round(start_h, 3),
                    "end_hour": round(min(24, start_h + o["minutes"] / 60), 3),
                }
            )
    write_csv("week.csv", rows)

    # Numbers quoted in the text.
    for route in ("north", "amsterdam", "haarlem"):
        group = [b for b in bridges if b["route"] == route]
        n = len(group)

        def mean(k: str, group: list[dict] = group, n: int = n) -> float:
            return sum(b[k] for b in group) / n

        print(
            f"{route}: {n} bridges, {mean('openings_per_day'):.1f} openings/day, "
            f"{mean('minutes_open_per_day'):.0f} min open/day, "
            f"weekday {mean('weekday_openings'):.1f} / weekend {mean('weekend_openings'):.1f}, "
            f"rush hour {mean('rush_hour_openings'):.1f}, night {mean('night_openings'):.1f}"
        )
    total_hours = sum(b["minutes_open_per_day"] for b in bridges) / 60
    print(f"all: {len(bridges)} bridges, {total_hours:.0f} bridge-hours open per day")
    print(f"busiest north bridge: {busiest['bridge']} near {busiest['near']}")

    # How much of the plan is a fixed timetable: weekday slots that recur on
    # every weekday, as a share of all weekday slots.
    common = total = 0
    for rows in by_bridge.values():
        per_day: dict[date, set[str]] = defaultdict(set)
        for o in rows:
            if o["start"].weekday() < 5:
                per_day[o["start"].date()].add(o["start"].strftime("%H:%M"))
        common += len(set.intersection(*per_day.values()))
        total += len(set.union(*per_day.values()))
    print(f"weekday slots that recur on every weekday: {common / total:.0%}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "data-branch/data"))
