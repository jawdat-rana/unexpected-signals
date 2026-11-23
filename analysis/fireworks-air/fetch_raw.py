"""Download hourly fine dust and wind around every New Year's Eve since 2012.

For each turn of the year Y -> Y+1 ("season" Y) we keep one week, 28 December
00:00 UTC to 3 January 23:00 UTC, so the night itself can be compared with the
quiet nights around it. Sources:

- RIVM Luchtmeetnet bulk files (data.rivm.nl/data/luchtmeetnet): validated
  hourly PM10 and PM2.5 per station per year ("Vastgesteld-jaar"), and monthly
  files for the current year ("Actueel-jaar", published about six weeks after
  the month ends). Cite "RIVM Luchtmeetnet".
- Luchtmeetnet open API (api.luchtmeetnet.nl) for the newest week, which is in
  no bulk file yet. Unvalidated. It rate-limits hard, so it is used only for
  that week and only for stations that reported the season before.
- Umweltbundesamt air data API v3 (Germany): hourly PM10 and PM2.5 for all
  stations. Cite "Umweltbundesamt".
- KNMI hourly observations (uurgegevens) for every station: wind and
  temperature. CC0, "bron: KNMI".

Standard library only. Runs in GitHub Actions (these hosts are not reachable
from every environment) and writes into OUT_DIR:

    nl_locations.csv                RIVM's station metadata file, as published
    nl/<Y>.csv                      station,formula,time_utc,value,source
    de_stations.csv                 id,code,name,city,type,setting,lon,lat
    de/<Y>.csv                      station,formula,time_utc,value
    knmi/<Y>.csv                    stn,time_utc,dd,fh,ff,t   (deg, m/s, m/s, deg C)
    manifest.csv                    source,year,rows,note

time_utc is the start of the hour. Values are ug/m3.

    python analysis/fireworks-air/fetch_raw.py OUT_DIR [FIRST_YEAR]

Re-running fetches only seasons that are missing or not finished, plus the
newest one, so a run on 2 or 3 January adds the night that just passed.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

HEADERS = {
    "User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)",
    "Accept": "application/json, text/csv, */*",
}
BULK = "https://data.rivm.nl/data/luchtmeetnet"
LML = "https://api.luchtmeetnet.nl/open_api"
UBA = "https://www.umweltbundesamt.de/api/air_data/v3"
KNMI = "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"
FORMULAS = ["PM10", "PM25"]
BULK_NAME = {"PM10": "PM10", "PM25": "PM25"}
UBA_COMPONENTS = {"PM10": 1, "PM25": 9}  # UBA component ids
UBA_HOURLY = 2  # scope: one-hour average
API_PAUSE = 1.5  # seconds between Luchtmeetnet API calls
NOW = dt.datetime.now(dt.UTC).replace(tzinfo=None)


def window(year: int) -> tuple[dt.datetime, dt.datetime]:
    """Week around the turn of year -> year+1, in UTC."""
    return dt.datetime(year, 12, 28), dt.datetime(year + 1, 1, 3, 23)


def get(url: str, data: bytes | None = None, retries: int = 6) -> bytes | None:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, data=data, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=300) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (400, 404, 422):
                return None
            if error.code == 429 and attempt < retries - 1:
                print(f"429 from {url[:60]}, waiting 120s", file=sys.stderr)
                time.sleep(120)
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


# --- Luchtmeetnet bulk files -------------------------------------------------


def in_window(when: dt.datetime) -> int | None:
    """Season a UTC hour belongs to, or None if it's outside every window."""
    if when.month == 12 and when.day >= 28:
        return when.year
    if when.month == 1 and when.day <= 3:
        return when.year - 1
    return None


def read_bulk(path: str, rows: dict[int, list], label: str) -> int | None:
    """Stream one RIVM bulk CSV and keep the hourly rows inside a window.

    Returns the number of rows kept, or None if the file doesn't exist.
    """
    request = urllib.request.Request(f"{BULK}/{path}", headers=HEADERS)
    try:
        response = urllib.request.urlopen(request, timeout=600)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    kept, columns = 0, None
    with response:
        for raw in io.TextIOWrapper(response, encoding="utf-8", errors="replace"):
            if raw.startswith("#"):
                continue
            cells = raw.rstrip("\r\n").split(";")
            if columns is None:
                columns = {name: i for i, name in enumerate(cells)}
                continue
            if cells[columns["meetduur"]] != "uur":
                continue
            begin = cells[columns["begindatumtijd"]]
            # Cheap filter on the local date before parsing.
            if begin[5:7] not in ("12", "01"):
                continue
            when = dt.datetime.fromisoformat(begin).astimezone(dt.UTC).replace(tzinfo=None)
            season = in_window(when)
            value = cells[columns["waarde"]]
            if season is None or value == "":
                continue
            formula = cells[columns["component"]].replace(".", "")
            rows[season].append(
                [cells[columns["meetlocatie_id"]], formula, f"{when:%Y-%m-%d %H:%M:%S}", value, label]
            )
            kept += 1
    return kept


def fetch_nl_bulk(seasons: list[int]) -> tuple[dict[int, list], set]:
    """Rows per season from the bulk files, and the (season, month) pairs covered."""
    rows: dict[int, list] = defaultdict(list)
    covered = set()
    years = sorted({y for s in seasons for y in (s, s + 1)})
    for year in years:
        for formula in FORMULAS:
            name = BULK_NAME[formula]
            kept = read_bulk(f"Vastgesteld-jaar/{year}/{year}_{name}.csv", rows, "validated")
            source = "validated"
            if kept is None:
                kept_dec = read_bulk(f"Actueel-jaar/{year}_12_{name}.csv", rows, "current")
                kept_jan = read_bulk(f"Actueel-jaar/{year}_01_{name}.csv", rows, "current")
                if kept_dec is not None:
                    covered.add((year, 12, formula))
                if kept_jan is not None:
                    covered.add((year, 1, formula))
                source = f"current months: dec={kept_dec} jan={kept_jan}"
                kept = (kept_dec or 0) + (kept_jan or 0)
            else:
                covered |= {(year, 12, formula), (year, 1, formula)}
            print(f"| bulk | {year} {formula} | {kept:,} | {source} |")
    return rows, covered


# --- Luchtmeetnet API, for the newest days -----------------------------------


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
        time.sleep(API_PAUSE)
        if not reply:
            return rows
        for m in reply.get("data", []):
            # The API stamps the END of the hour; store the start, like the bulk files.
            end_of_hour = dt.datetime.fromisoformat(m["timestamp_measured"]).astimezone(dt.UTC)
            when = end_of_hour.replace(tzinfo=None) - dt.timedelta(hours=1)
            rows.append([number, formula, f"{when:%Y-%m-%d %H:%M:%S}", m["value"], "api"])
        if page >= (reply.get("pagination") or {}).get("last_page", 1):
            return rows
        page += 1


def fetch_nl_api(season: int, formula: str, stations: list[str], part: str) -> list[list]:
    start, end = window(season)
    if part == "dec":
        end = dt.datetime(season, 12, 31, 23)
    else:
        start = dt.datetime(season + 1, 1, 1)
    end = min(end, NOW)
    if start >= end:
        return []
    rows = []
    for number in stations:
        rows += lml_series(number, formula, start, end)
    print(f"| api | {season} {formula} {part} | {len(rows):,} | {len(stations)} stations asked |")
    return rows


def fetch_nl(out: Path, seasons: list[int]) -> list[list]:
    payload = get(f"{BULK}/Metadata/luchtmeetnet_meetlocaties.csv")
    if payload:
        (out / "nl_locations.csv").write_bytes(payload)
    rows, covered = fetch_nl_bulk(seasons)
    manifest = []
    for season in seasons:
        for formula in FORMULAS:
            missing = []
            if (season, 12, formula) not in covered:
                missing.append("dec")
            if (season + 1, 1, formula) not in covered:
                missing.append("jan")
            if not missing:
                continue
            # Ask only stations that reported this formula the season before.
            before = read_rows(out / "nl" / f"{season - 1}.csv") or rows.get(season - 1, [])
            stations = sorted({r[0] for r in before if r[1] == formula})
            for part in missing:
                rows[season] += fetch_nl_api(season, formula, stations, part)
    for season in seasons:
        data = sorted(rows.get(season, []))
        write(out / "nl" / f"{season}.csv", ["station", "formula", "time_utc", "value", "source"], data)
        series = len({(r[0], r[1]) for r in data})
        sources = ",".join(sorted({r[4] for r in data}))
        print(f"| NL | {season} | {len(data):,} | {series} station-series ({sources}) |")
        manifest.append(["luchtmeetnet", season, len(data), f"{series} series; {sources}"])
    return manifest


def read_rows(path: Path) -> list[list]:
    if not path.exists():
        return []
    with open(path, newline="") as handle:
        return list(csv.reader(handle))[1:]


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




def write(path: Path, header: list[str], rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def seasons_to_fetch(out: Path, first: int) -> list[int]:
    last = NOW.year if NOW >= window(NOW.year)[0] else NOW.year - 1
    seasons = []
    for season in range(first, last + 1):
        have = out / "nl" / f"{season}.csv"
        if not _validated(have) or season == last:
            seasons.append(season)
    return seasons


def _validated(path: Path) -> bool:
    """True when every row of a stored season came from a validated file."""
    rows = read_rows(path)
    return bool(rows) and all(r[4] == "validated" for r in rows)


def main(out: Path, first: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    seasons = seasons_to_fetch(out, first)
    print(f"Seasons to fetch: {seasons}\n")
    print("| source | season | rows | coverage |\n| --- | --- | --- | --- |")
    manifest = fetch_nl(out, seasons)
    try:
        de = de_stations()
        if de:
            write(out / "de_stations.csv", list(de[0].keys()), [list(s.values()) for s in de])
        manifest += fetch_de(out, seasons)
    except Exception as error:  # noqa: BLE001 - Germany is the comparison, not the story
        print(f"UBA failed: {error}", file=sys.stderr)
    manifest += fetch_knmi(out, seasons)

    old = read_rows(out / "manifest.csv")
    fetched = {(m[0], str(m[1])) for m in manifest}
    keep = [r for r in old if (r[0], r[1]) not in fetched] + manifest
    write(out / "manifest.csv", ["source", "season", "rows", "note"], sorted(keep, key=lambda r: (r[0], str(r[1]))))
    print(f"\nFetched at {NOW:%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 2012)
