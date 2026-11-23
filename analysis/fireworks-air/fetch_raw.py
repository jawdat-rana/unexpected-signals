"""Download hourly fine dust and wind around every New Year's Eve since 2012.

For each turn of the year Y -> Y+1 we keep one week, 28 December 00:00 UTC to
3 January 23:00 UTC, so every night can be compared with the quiet days
around it. Three open sources:

- RIVM Luchtmeetnet open API (NL, every station measuring PM10 or PM2.5).
  Open data, cite "RIVM Luchtmeetnet". Recent hours are unvalidated.
- Umweltbundesamt air data API v3 (Germany, which has no consumer ban): hourly
  PM10 and PM2.5 for all stations. Cite "Umweltbundesamt".
- KNMI hourly observations (uurgegevens) for every station: wind speed and
  direction, temperature. CC0, "bron: KNMI".

Standard library only. Runs in GitHub Actions (these hosts are not reachable
from every environment) and writes into OUT_DIR:

    nl_stations.csv                 number,name,municipality,type,lon,lat,components
    nl/<Y>.csv                      station,formula,time_utc,value     (ug/m3)
    de_stations.csv                 id,code,name,city,type,setting,lon,lat
    de/<Y>.csv                      station,formula,time_utc,value     (ug/m3)
    knmi/<Y>.csv                    stn,time_utc,dd,fh,ff,t   (deg, m/s, m/s, deg C)
    manifest.csv                    source,year,rows,note

    python analysis/fireworks-air/fetch_raw.py OUT_DIR [FIRST_YEAR]

Re-running refetches only years whose window had not finished last time,
plus the newest year, so the run on 1 January adds the night that just passed.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HEADERS = {
    "User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)",
    "Accept": "application/json",
}
LML = "https://api.luchtmeetnet.nl/open_api"
UBA = "https://www.umweltbundesamt.de/api/air_data/v3"
KNMI = "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"
FORMULAS = ["PM10", "PM25"]
UBA_COMPONENTS = {"PM10": 1, "PM25": 9}  # UBA component ids
UBA_HOURLY = 2  # scope: one-hour average
PAUSE = 0.25  # seconds between Luchtmeetnet calls; it answers 429 when rushed
SHOWN = False
DEADLINE = time.monotonic() + 75 * 60  # stop early and keep what we have
NOW = dt.datetime.now(dt.UTC).replace(tzinfo=None)


def window(year: int) -> tuple[dt.datetime, dt.datetime]:
    """Week around the turn of year -> year+1, in UTC."""
    return dt.datetime(year, 12, 28), dt.datetime(year + 1, 1, 3, 23)


def get(url: str, data: bytes | None = None, retries: int = 8) -> bytes | None:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, data=data, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (400, 404, 422):
                print(f"HTTP {error.code} {url[:160]}", file=sys.stderr)
                return None
            if error.code == 429 and attempt < retries - 1:
                wait = int(error.headers.get("Retry-After") or 30)
                print(f"429, waiting {wait}s ({dict(error.headers)})", file=sys.stderr)
                time.sleep(min(wait, 300))
                continue
            if attempt == retries - 1:
                raise
        except Exception:
            if attempt == retries - 1:
                raise
        time.sleep(2 ** (attempt + 1))
    return None


def get_json(url: str):
    payload = get(url)
    return None if payload is None else json.loads(payload)


# --- Luchtmeetnet -----------------------------------------------------------


def lml_stations() -> list[dict]:
    numbers, page = [], 1
    while True:
        reply = get_json(f"{LML}/stations?page={page}&order_by=number")
        numbers += [s["number"] for s in reply["data"]]
        if page >= reply["pagination"]["last_page"]:
            break
        page += 1

    def detail(number: str) -> dict:
        data = get_json(f"{LML}/stations/{number}")["data"]
        lon, lat = (data.get("geometry") or {}).get("coordinates", ["", ""])[:2]
        return {
            "number": number,
            "name": data.get("location", ""),
            "municipality": data.get("municipality") or "",
            "type": data.get("type") or "",
            "lon": lon,
            "lat": lat,
            "components": " ".join(data.get("components") or []),
        }

    rows = []
    for number in numbers:
        rows.append(detail(number))
        time.sleep(PAUSE)
    return rows


def lml_series(number: str, formula: str, start: dt.datetime, end: dt.datetime) -> list[list]:
    rows, page = [], 1
    while True:
        query = urllib.parse.urlencode(
            {
                "station_number": number,
                "formula": formula,
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "page": page,
                "order_by": "timestamp_measured",
                "order_direction": "asc",
            }
        )
        reply = get_json(f"{LML}/measurements?{query}")
        time.sleep(PAUSE)
        global SHOWN
        if not SHOWN and reply and reply.get("data"):
            SHOWN = True
            print(f"First reply: pagination {reply.get('pagination')}", file=sys.stderr)
        if not reply:
            return rows
        for m in reply.get("data", []):
            stamp = m["timestamp_measured"][:19]  # 2026-01-01T00:00:00+00:00
            rows.append([number, formula, stamp.replace("T", " "), m["value"]])
        if page >= (reply.get("pagination") or {}).get("last_page", 1):
            return rows
        page += 1


def fetch_nl(out: Path, years: list[int], stations: list[dict]) -> list[list]:
    pm = [s for s in stations if any(f in s["components"].split() for f in FORMULAS)]
    manifest = []
    for year in years:
        if time.monotonic() > DEADLINE:
            print(f"Out of time before NL {year}; the next run continues from here.")
            break
        start, end = window(year)
        jobs = [
            (s["number"], f)
            for s in pm
            for f in FORMULAS
            if f in s["components"].split()
        ]
        rows = sorted(r for j in jobs for r in lml_series(j[0], j[1], start, end))
        write(out / "nl" / f"{year}.csv", ["station", "formula", "time_utc", "value"], rows)
        with_data = len({(r[0], r[1]) for r in rows})
        print(f"| NL | {year} | {len(rows):,} | {with_data} station-series of {len(jobs)} |")
        manifest.append(["luchtmeetnet", year, len(rows), f"{with_data}/{len(jobs)} series"])
    return manifest


# --- Umweltbundesamt --------------------------------------------------------


def de_stations() -> list[dict]:
    reply = get_json(f"{UBA}/stations/json?use=measure&lang=en")
    if not reply:
        return []
    index = {name: i for i, name in enumerate(reply.get("indices", []))}
    rows = []
    for sid, cells in reply.get("data", {}).items():
        def cell(key, fallback):
            i = index.get(key, fallback)
            return cells[i] if i is not None and i < len(cells) else ""

        rows.append(
            {
                "id": sid,
                "code": cell("station code", 1),
                "name": cell("station name", 2),
                "city": cell("station city", 3),
                "type": cell("station type name", 16),
                "setting": cell("station setting name", 15),
                "lon": cell("station longitude", 7),
                "lat": cell("station latitude", 8),
            }
        )
    if not rows:
        print("UBA stations reply:", json.dumps(reply)[:800], file=sys.stderr)
    return rows


def fetch_de(out: Path, years: list[int]) -> list[list]:
    manifest = []
    for year in years:
        start, end = window(year)
        rows = []
        for formula, component in UBA_COMPONENTS.items():
            # UBA hours run 1..24 in local time (CET); ask for a day either side.
            query = urllib.parse.urlencode(
                {
                    "date_from": (start - dt.timedelta(days=1)).strftime("%Y-%m-%d"),
                    "time_from": 1,
                    "date_to": (end + dt.timedelta(days=1)).strftime("%Y-%m-%d"),
                    "time_to": 24,
                    "component": component,
                    "scope": UBA_HOURLY,
                }
            )
            reply = get_json(f"{UBA}/measures/json?{query}")
            if not reply or not isinstance(reply.get("data"), dict):
                print(f"UBA {year} {formula}: {json.dumps(reply)[:400]}", file=sys.stderr)
                continue
            for sid, series in reply["data"].items():
                for stamp, cells in series.items():
                    # cells: [component, scope, value, date_end, index]; stamp is
                    # the start of the hour in CET.
                    value = cells[2] if len(cells) > 2 else None
                    if value is None:
                        continue
                    utc = dt.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S") - dt.timedelta(hours=1)
                    if start <= utc <= end:
                        rows.append([sid, formula, utc.strftime("%Y-%m-%d %H:%M:%S"), value])
            time.sleep(1)
        rows.sort()
        write(out / "de" / f"{year}.csv", ["station", "formula", "time_utc", "value"], rows)
        print(f"| DE | {year} | {len(rows):,} | {len({(r[0], r[1]) for r in rows})} station-series |")
        manifest.append(["umweltbundesamt", year, len(rows), ""])
    return manifest


# --- KNMI -------------------------------------------------------------------


def fetch_knmi(out: Path, years: list[int]) -> list[list]:
    manifest = []
    for year in years:
        start, end = window(year)
        # KNMI hours are 1..24 UT, hour 1 = 00:00-01:00. Ask whole days.
        form = urllib.parse.urlencode(
            {
                "stns": "ALL",
                "vars": "DD:FH:FF:T",
                "start": start.strftime("%Y%m%d") + "01",
                "end": end.strftime("%Y%m%d") + "24",
            }
        ).encode()
        text = (get(KNMI, data=form) or b"").decode("latin-1")
        rows, columns = [], None
        for line in text.splitlines():
            if "YYYYMMDD" in line:
                columns = [c.strip().lstrip("#").strip() for c in line.split(",")]
                continue
            if columns is None or not line.strip() or line.startswith("#"):
                continue
            cells = dict(zip(columns, [c.strip() for c in line.split(",")], strict=False))
            day, hour = cells.get("YYYYMMDD", ""), cells.get("HH", "")
            if not (day.isdigit() and hour.isdigit()):
                continue
            # Hour HH covers (HH-1):00 to HH:00 UT; label it by its start.
            when = dt.datetime.strptime(day, "%Y%m%d") + dt.timedelta(hours=int(hour) - 1)

            def tenth(key):
                v = cells.get(key, "")
                return "" if v in ("", None) else round(int(v) / 10, 1)

            rows.append(
                [
                    cells.get("STN", ""),
                    when.strftime("%Y-%m-%d %H:%M:%S"),
                    cells.get("DD", ""),
                    tenth("FH"),
                    tenth("FF"),
                    tenth("T"),
                ]
            )
        if not rows:
            print(f"KNMI {year}: {text[:600]}", file=sys.stderr)
        write(out / "knmi" / f"{year}.csv", ["stn", "time_utc", "dd", "fh", "ff", "t"], rows)
        print(f"| KNMI | {year} | {len(rows):,} | {len({r[0] for r in rows})} stations |")
        manifest.append(["knmi", year, len(rows), ""])
    return manifest


# --- main -------------------------------------------------------------------


def write(path: Path, header: list[str], rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def years_to_fetch(out: Path, first: int) -> list[int]:
    last = NOW.year if NOW >= window(NOW.year)[0] else NOW.year - 1
    years = []
    for year in range(first, last + 1):
        done = window(year)[1] + dt.timedelta(days=2) < NOW  # allow late hours
        have = (out / "nl" / f"{year}.csv").exists()
        if not (done and have) or year == last:
            years.append(year)
    return years


def main(out: Path, first: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    years = years_to_fetch(out, first)
    print(f"Years to fetch: {years}\n")
    print("| source | year | rows | coverage |\n| --- | --- | --- | --- |")

    stations = lml_stations()
    write(
        out / "nl_stations.csv",
        ["number", "name", "municipality", "type", "lon", "lat", "components"],
        [list(s.values()) for s in stations],
    )
    manifest = fetch_nl(out, years, stations)

    try:
        de = de_stations()
        if de:
            write(out / "de_stations.csv", list(de[0].keys()), [list(s.values()) for s in de])
        manifest += fetch_de(out, years)
    except Exception as error:  # noqa: BLE001 - Germany is the control, not the story
        print(f"UBA failed: {error}", file=sys.stderr)

    manifest += fetch_knmi(out, years)

    old = out / "manifest.csv"
    keep = []
    if old.exists():
        with open(old) as handle:
            keep = [r for r in csv.reader(handle)][1:]
    fetched = {(m[0], str(m[1])) for m in manifest}
    keep = [r for r in keep if (r[0], r[1]) not in fetched] + manifest
    write(old, ["source", "year", "rows", "note"], sorted(keep, key=lambda r: (r[0], str(r[1]))))
    print(f"\n{len(stations)} Luchtmeetnet stations, fetched at {NOW:%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 2012)
