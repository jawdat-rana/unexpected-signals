"""Live bridge openings across the Netherlands, for the boats-go-first explainer.

NDW's bridge feed also carries openings as they happen (probability
"certain"). A record appears when a bridge starts to open and disappears when
it closes, and has no end time, so the collector's first and last sighting
bound how long it was open. This script counts openings per bridge over whole
local days and writes small chart CSVs.

    git fetch origin data
    git worktree add data-branch origin/data
    python analysis/ndw-bridges/live.py data-branch/data 2026-11-23 2026-11-29

Place names come from the UN/LOCODE in each record id (nl_locodes.csv, from
UNECE's UN/LOCODE list via github.com/datasets/un-locode).
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "stories" / "boats-go-first" / "data"
AMS = ZoneInfo("Europe/Amsterdam")
RUSH_HOURS = {7, 8, 16, 17}


def local(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")[:19] + "+00:00").astimezone(AMS)


def place_names() -> dict[str, str]:
    with (HERE / "nl_locodes.csv").open(newline="", encoding="utf-8") as fh:
        return {row["code"]: row["name"] for row in csv.DictReader(fh)}


def write_csv(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {(OUT / name).relative_to(HERE.parent.parent)}")


def main(data: Path, first: date, last: date) -> None:
    names = place_names()
    days = (last - first).days + 1
    latest: dict[str, dict[str, str]] = {}
    for path in sorted((data / "bridges").rglob("*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["probability"] != "certain":
                    continue
                old = latest.get(row["record_id"])
                if old is None or int(row["version"]) > int(old["version"]):
                    latest[row["record_id"]] = row

    by_bridge: dict[str, list[dict]] = defaultdict(list)
    for row in latest.values():
        start = local(row["start_time"])
        if not first <= start.date() <= last:
            continue
        lat, lon = float(row["latitude"]), float(row["longitude"])
        # Records of one bridge share coordinates; round to group them.
        key = f"{lat:.3f},{lon:.3f}"
        code = row["situation_id"].split("_")[1][2:5]
        minutes = (local(row["last_seen"]) - start).total_seconds() / 60
        by_bridge[key].append(
            {
                "lat": lat,
                "lon": lon,
                "place": names.get(code, code),
                "start": start,
                "minutes": max(0.0, minutes),
            }
        )

    bridges = []
    for key, rows in by_bridge.items():
        weekdays = [r for r in rows if r["start"].weekday() < 5]
        bridges.append(
            {
                "bridge": key,
                "place": Counter(r["place"] for r in rows).most_common(1)[0][0],
                "latitude": rows[0]["lat"],
                "longitude": rows[0]["lon"],
                "openings": len(rows),
                "openings_per_day": round(len(rows) / days, 1),
                "rush_hour_openings": sum(r["start"].hour in RUSH_HOURS for r in weekdays),
                "night_openings": sum(r["start"].hour >= 23 or r["start"].hour < 6 for r in rows),
                # Last sighting minus start: a lower bound on how long it was open.
                "median_minutes_seen": round(statistics.median(r["minutes"] for r in rows), 1),
            }
        )
    bridges.sort(key=lambda b: -b["openings"])
    write_csv("live_bridges.csv", bridges)

    hours = Counter(r["start"].hour for rows in by_bridge.values() for r in rows)
    write_csv(
        "live_hours.csv",
        [{"hour": h, "openings_per_day": round(hours[h] / days, 1)} for h in range(24)],
    )

    total = sum(b["openings"] for b in bridges)
    print(f"{first}..{last}: {len(bridges)} bridges, {total} openings, {total / days:.0f} a day")
    rush = sum(b["rush_hour_openings"] for b in bridges)
    print(
        f"weekday rush-hour openings: {rush}; night openings: "
        f"{sum(b['night_openings'] for b in bridges)}"
    )
    for b in bridges[:12]:
        print(f"  {b['place']:<22} {b['openings']:>4}  {b['openings_per_day']}/day")


if __name__ == "__main__":
    data_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data-branch/data")
    start = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today() - timedelta(7)
    end = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else date.today() - timedelta(1)
    main(data_dir, start, end)
