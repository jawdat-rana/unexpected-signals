"""A day at the Spijkenisserbrug, replayed: bridge openings next to traffic sensors.

For the replay chart in the boats-go-first explainer. For every 5-minute
snapshot of the traffic feed it writes whether the Spijkenisserbrug and the
Botlekbrug were open, and what the nearest sensors measured:

- the Groene Kruisweg next to the Spijkenisserbrug (GRT02_MORO_2092_2), and
- the A15 main carriageway at the Botlek crossing, both directions together.

    git fetch origin data
    git worktree add data-branch origin/data
    python analysis/ndw-bridges/replay.py data-branch/data 2026-11-23 2026-11-27

An opening runs from its start time to the collector's last sighting of it,
which can be up to one collection interval (5 minutes) after the bridge
closed. A step counts as open when that window overlaps the snapshot.
"""

from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "stories" / "boats-go-first" / "data" / "replay.csv"
AMS = ZoneInfo("Europe/Amsterdam")

# Live openings carry the bridge's location code in the situation id.
BRIDGES = {
    "spijkenisserbrug": "NLSPI001110572700266",
    "botlekbrug": "NLRTM001110888700281",
}
GROENE_KRUISWEG = "GRT02_MORO_2092_2"
A15 = ("RWS01_MONIBAS_0151hrl0466ra", "RWS01_MONIBAS_0151hrr0466ra")
# Half a step either side of a snapshot.
HALF_STEP = timedelta(minutes=2, seconds=30)


def utc(stamp: str) -> datetime | None:
    if not stamp:
        return None
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")[:19] + "+00:00")


def openings(data: Path, days: list[date]) -> dict[str, list[tuple[datetime, datetime]]]:
    """Live openings per bridge, deduplicated on (start, last sighting)."""
    found: dict[str, set[tuple[datetime, datetime]]] = {name: set() for name in BRIDGES}
    # A day's file can hold openings that started late the evening before.
    for day in sorted({d + timedelta(days=k) for d in days for k in (-1, 0, 1)}):
        path = data / "bridges" / f"{day:%Y}" / f"{day:%m}" / f"{day:%Y-%m-%d}.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["probability"] != "certain":
                    continue
                for name, code in BRIDGES.items():
                    if code in row["situation_id"]:
                        start, end = utc(row["start_time"]), utc(row["last_seen"])
                        if start and end:
                            found[name].add((start, max(start, end)))
    return {name: sorted(spans) for name, spans in found.items()}


def is_open(spans: list[tuple[datetime, datetime]], at: datetime) -> int:
    return int(any(start - HALF_STEP <= at <= end + HALF_STEP for start, end in spans))


def snapshots(data: Path, day: date) -> dict[datetime, dict[str, tuple[float, float]]]:
    """Speed and flow per wanted sensor, per collector snapshot, for one local day."""
    wanted = {GROENE_KRUISWEG, *A15}
    out: dict[datetime, dict[str, tuple[float, float]]] = {}
    # A local day spans two UTC files.
    for d in (day - timedelta(days=1), day):
        path = data / "traffic_sites" / f"{d:%Y}" / f"{d:%m}" / f"{d:%Y-%m-%d}.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["site_id"] not in wanted:
                    continue
                at = utc(row["fetched_at"])
                if at.astimezone(AMS).date() != day:
                    continue
                out.setdefault(at, {})[row["site_id"]] = (
                    float(row["speed_kmh"] or 0),
                    float(row["flow_veh_h"] or 0),
                )
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    data = Path(argv[0])
    first, last = date.fromisoformat(argv[1]), date.fromisoformat(argv[2])
    days = [first + timedelta(days=k) for k in range((last - first).days + 1)]
    spans = openings(data, days)

    rows = []
    for day in days:
        snaps = snapshots(data, day)
        if not snaps:
            print(f"{day}: no traffic snapshots, skipped")
            continue
        for at in sorted(snaps):
            sensors = snaps[at]
            local = at.astimezone(AMS)
            gk = sensors.get(GROENE_KRUISWEG)
            a15 = [sensors[s] for s in A15 if s in sensors]
            a15_flow = sum(f for _, f in a15) if a15 else ""
            # Speed weighted by flow, so an empty direction doesn't pull it down.
            a15_speed = round(sum(s * f for s, f in a15) / a15_flow, 1) if a15 and a15_flow else ""
            rows.append(
                {
                    "day": f"{local:%a} {local.day} {local:%b}",
                    "time": f"{local:%H:%M}",
                    "spijkenisserbrug_open": is_open(spans["spijkenisserbrug"], at),
                    "botlekbrug_open": is_open(spans["botlekbrug"], at),
                    "groene_kruisweg_flow": round(gk[1]) if gk else "",
                    "groene_kruisweg_speed": round(gk[0], 1) if gk else "",
                    "a15_flow": round(a15_flow) if a15 else "",
                    "a15_speed": a15_speed,
                }
            )
        opened = {
            name: sum(1 for s, _ in v if s.astimezone(AMS).date() == day)
            for name, v in spans.items()
        }
        print(f"{day}: {len(snaps)} snapshots, openings {opened}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
