"""Where do train disruptions hurt the most passengers?

Joins two sources on NS station codes:

- Rijden de Treinen disruptions (CC BY 4.0): every disruption lists the codes
  of the stations around the blocked stretch, e.g. "DT, DTCP, RTD, SDM".
- NS annual report dashboard (attribute NS): passengers per average working
  day on each section of track between two adjacent stations.

Each disruption is placed on the track sections that connect its stations
(the shortest network that joins them). Per section we then add up:

- hours: time the section had at least one disruption (overlaps merged)
- disruptions: how many disruptions touched it
- passengers: NS passengers per working day, both directions
- trips_hit: an estimate of the journeys that would have used the section
  while it was disrupted = hours x passengers per day / 18 service hours.
  It assumes travel is spread evenly over the day, so treat it as an index.

    python analysis/train-disruptions/impact.py [YEAR] [OUT_DIR]

Writes OUT_DIR/sections.csv (default: the story's data folder).

Reads the raw files from analysis/train-disruptions/raw/ (see fetch_raw.py).
"""

from __future__ import annotations

import csv
import heapq
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RAW = Path(__file__).parent / "raw"
SERVICE_HOURS = 18  # roughly 06:00 to 24:00
# Problems abroad stop international trains; Dutch trains keep running.
SKIP_CAUSES = {"staff strikes abroad", "railway problems abroad"}
# A few causes have no English translation in the source.
CAUSE_EN = {"staking bij NS": "NS strike"}
STORY = Path(__file__).parents[2] / "stories" / "where-train-disruptions-hurt" / "data"
Edge = tuple[str, str]


def edge(a: str, b: str) -> Edge:
    return (a, b) if a < b else (b, a)


def km(p: dict, q: dict) -> float:
    """Straight-line distance; NS's own Length field is schematic."""
    lat1, lat2 = math.radians(p["Lat"]), math.radians(q["Lat"])
    dlat, dlng = lat2 - lat1, math.radians(q["Lng"] - p["Lng"])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return max(2 * 6371 * math.asin(math.sqrt(h)), 0.01)


def load_ns(year: int) -> tuple[dict, dict[Edge, dict]]:
    data = json.loads((RAW / f"ns-dashboard-{year}.json").read_text(encoding="utf-8"))
    stations = {s["Alias"]: s for s in data["Stations"]}
    sections: dict[Edge, dict] = {}
    for seg in data["Segments"]:
        a, b = seg["A"], seg["B"]
        key = edge(a["StationAlias"], b["StationAlias"])
        sections[key] = {
            "a": a,
            "b": b,
            "passengers": (a["Travelers"] or 0) + (b["Travelers"] or 0),
            "km": km(a["Coordinate"], b["Coordinate"]),
        }
    return stations, sections


def graph(sections: dict[Edge, dict]) -> dict[str, dict[str, float]]:
    g: dict[str, dict[str, float]] = defaultdict(dict)
    for (a, b), s in sections.items():
        g[a][b] = g[b][a] = s["km"]
    return g


def shortest(g: dict[str, dict[str, float]], source: str) -> tuple[dict, dict]:
    dist, prev = {source: 0.0}, {}
    queue = [(0.0, source)]
    while queue:
        d, node = heapq.heappop(queue)
        if d > dist[node]:
            continue
        for nxt, w in g[node].items():
            if d + w < dist.get(nxt, float("inf")):
                dist[nxt], prev[nxt] = d + w, node
                heapq.heappush(queue, (d + w, nxt))
    return dist, prev


def connect(g, codes: list[str], cache: dict) -> set[Edge]:
    """Approximate the smallest set of sections joining the stations.

    Builds a minimum spanning tree over shortest-path distances between the
    stations (Prim) and returns the sections on those paths.
    """
    codes = [c for c in dict.fromkeys(codes) if c in g]
    if len(codes) < 2:
        return set()
    for c in codes:
        if c not in cache:
            cache[c] = shortest(g, c)
    tree, out = {codes[0]}, set()
    while len(tree) < len(codes):
        best = None
        for a in tree:
            dist = cache[a][0]
            for b in codes:
                if b not in tree and b in dist and (best is None or dist[b] < best[0]):
                    best = (dist[b], a, b)
        if best is None:  # stations on separate networks
            break
        _, a, b = best
        prev, node = cache[a][1], b
        while node != a:
            out.add(edge(node, prev[node]))
            node = prev[node]
        tree.add(b)
    return out


def merged_hours(spans: list[tuple[datetime, datetime]]) -> float:
    total, end = 0.0, None
    for start, stop in sorted(spans):
        if end is None or start > end:
            total += (stop - start).total_seconds()
            end = stop
        elif stop > end:
            total += (stop - end).total_seconds()
            end = stop
    return total / 3600


def parse(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def main(year: int, out: Path) -> None:
    stations, sections = load_ns(year)
    g = graph(sections)
    rows = list(csv.DictReader((RAW / f"disruptions-{year}.csv").open(encoding="utf-8-sig")))

    spans: dict[Edge, list] = defaultdict(list)
    count: Counter = Counter()
    causes: dict[Edge, Counter] = defaultdict(Counter)
    groups: dict[Edge, Counter] = defaultdict(Counter)
    cache: dict = {}
    placed = unplaced = skipped = 0
    for row in rows:
        if row["cause_en"] in SKIP_CAUSES:
            skipped += 1
            continue
        start, stop = parse(row["start_time"]), parse(row["end_time"])
        codes = [c for c in row["rdt_station_codes"].split(", ") if c]
        hit = connect(g, codes, cache) if start and stop and stop > start else set()
        if not hit:
            unplaced += 1
            continue
        placed += 1
        hours = (stop - start).total_seconds() / 3600
        for e in hit:
            spans[e].append((start, stop))
            count[e] += 1
            groups[e][row["cause_group"] or "unknown"] += hours
            cause = row["cause_en"] or "unknown"
            causes[e][CAUSE_EN.get(cause, cause)] += hours

    def name(code: str) -> str:
        return stations[code]["Name"] if code in stations else code

    records = []
    for e, s in sections.items():
        a, b = s["a"], s["b"]
        hours = merged_hours(spans[e]) if e in spans else 0.0
        records.append(
            {
                "from_code": a["StationAlias"],
                "to_code": b["StationAlias"],
                "from_name": name(a["StationAlias"]),
                "to_name": name(b["StationAlias"]),
                "from_lat": round(a["Coordinate"]["Lat"], 5),
                "from_lng": round(a["Coordinate"]["Lng"], 5),
                "to_lat": round(b["Coordinate"]["Lat"], 5),
                "to_lng": round(b["Coordinate"]["Lng"], 5),
                "km": round(s["km"], 1),
                "passengers": s["passengers"],
                "disruptions": count[e],
                "hours": round(hours, 1),
                "trips_hit": round(hours * s["passengers"] / SERVICE_HOURS),
                # Disruption hours by cause, before merging overlaps.
                "top_causes": "; ".join(f"{c} ({h:.0f}h)" for c, h in causes[e].most_common(3)),
                "main_group": groups[e].most_common(1)[0][0] if groups[e] else "",
            }
        )
    records.sort(key=lambda r: -r["trips_hit"])

    out.mkdir(parents=True, exist_ok=True)
    with (out / "sections.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    print(
        f"{year}: {len(rows):,} disruptions, {skipped:,} skipped (problems abroad), "
        f"{placed:,} placed on track, {unplaced:,} not"
    )
    ns = [r for r in records if r["passengers"]]
    total = sum(r["trips_hit"] for r in ns)
    print(f"NS sections with passengers: {len(ns)}, trips_hit total {total:,}")
    top10 = sum(r["trips_hit"] for r in ns[:10])
    print(f"top 10 sections share of trips_hit: {top10 / total:.0%}")
    by_hours = sorted(ns, key=lambda r: -r["hours"])
    print("\nmost disrupted hours (NS sections):")
    for r in by_hours[:10]:
        print(f"  {r['from_name']} - {r['to_name']}: {r['hours']}h, {r['passengers']:,}/day")
    print("\nmost trips hit:")
    for r in ns[:15]:
        print(
            f"  {r['from_name']} - {r['to_name']}: {r['trips_hit']:,} trips, "
            f"{r['hours']}h, {r['disruptions']} disr, {r['passengers']:,}/day, "
            f"{r['top_causes']}"
        )


if __name__ == "__main__":
    args = sys.argv[1:]
    main(int(args[0]) if args else 2025, Path(args[1]) if len(args) > 1 else STORY)
