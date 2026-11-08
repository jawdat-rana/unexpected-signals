"""Explore the JSON behind the NS annual-report station dashboard.

The dashboard loads one file per year from /api/dashboard/<year>, with every
station's figures for an average working day. This prints its structure and a
first summary. Data: NS annual report dashboards (dashboards.nsjaarverslag.nl).

    python analysis/ns-stations/explore.py
"""

from __future__ import annotations

import json
import time
import urllib.request
from collections import Counter
from pathlib import Path

API = "https://dashboards.nsjaarverslag.nl/api/dashboard/{year}"
RAW = Path(__file__).parent / "raw"
YEARS = range(2019, 2026)


def fetch(year: int) -> dict:
    RAW.mkdir(exist_ok=True)
    path = RAW / f"dashboard-{year}.json"
    if not path.exists():
        req = urllib.request.Request(
            API.format(year=year), headers={"User-Agent": "unexpected-signals research"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
        time.sleep(1)  # be polite: one request per second
    return json.loads(path.read_text(encoding="utf-8"))


def value(station: dict, key: str):
    for d in station.get("Data", []):
        if d.get("ClientKey") == key:
            return d.get("Value")
    return None


def main() -> None:
    data = {y: fetch(y) for y in YEARS}
    latest = data[max(YEARS)]

    print("## Top-level keys:", list(latest.keys()))
    for k, v in latest.items():
        if k != "Stations":
            print(f"\n## {k}: {json.dumps(v, ensure_ascii=False)[:1500]}")

    stations = latest["Stations"]
    print(f"\n## {len(stations)} stations in {max(YEARS)}")
    print("Station keys:", list(stations[0].keys()))
    print("Types:", Counter(s.get("Type") for s in stations))
    print("Sizes:", Counter(s.get("Size") for s in stations))
    keys = Counter(d["ClientKey"] for s in stations for d in s.get("Data", []))
    filled = Counter(
        d["ClientKey"]
        for s in stations
        for d in s.get("Data", [])
        if d.get("Value") not in (None, "", [])
    )
    print("\n## Data keys (present / filled)")
    for k, n in keys.items():
        print(f"{k:30} {n:5} {filled[k]:5}")

    rdam = next(s for s in stations if s.get("UrlPart") == "rotterdam-centraal")
    print("\n## Full record: Rotterdam Centraal")
    print(json.dumps(rdam, ensure_ascii=False, indent=1)[:6000])

    print("\n## Travelers per day by year, top 15 stations of", max(YEARS))
    top = sorted(
        (s for s in stations if isinstance(value(s, "TravelersPerDay"), (int, float))),
        key=lambda s: value(s, "TravelersPerDay"),
        reverse=True,
    )[:15]
    by_year = {
        y: {s["UrlPart"]: value(s, "TravelersPerDay") for s in data[y]["Stations"]} for y in YEARS
    }
    print("station".ljust(28), *(str(y).rjust(8) for y in YEARS))
    for s in top:
        print(
            s["Name"][:27].ljust(28), *(str(by_year[y].get(s["UrlPart"])).rjust(8) for y in YEARS)
        )

    names = {s["Alias"]: s["Name"] for s in stations}
    for y in (2019, max(YEARS)):
        segs = data[y]["Segments"]
        loaded = [g for g in segs if g["A"]["Travelers"] or g["B"]["Travelers"]]
        print(f"\n## Segments {y}: {len(segs)} total, {len(loaded)} with travellers")
        top_segs = sorted(
            loaded, key=lambda g: g["A"]["Travelers"] + g["B"]["Travelers"], reverse=True
        )[:15]
        for g in top_segs:
            a, b = g["A"], g["B"]
            print(
                f"{names.get(a['StationAlias'], a['StationAlias'])[:25]:25} -> "
                f"{names.get(b['StationAlias'], b['StationAlias'])[:25]:25} "
                f"A:{a['Travelers']:>7} B:{b['Travelers']:>7} thickness:{g['Thickness']:.2f}"
            )


if __name__ == "__main__":
    main()
