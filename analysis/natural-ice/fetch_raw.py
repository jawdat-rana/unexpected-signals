"""Download KNMI daily weather for every station and keep the temperatures.

KNMI serves all daily observations of a station since it opened (De Bilt
since 1901) through its daggegevens script interface, with the old per-station
zip files as a fallback. We keep only the date and the daily mean,
minimum and maximum temperature, which is all the ice story needs, plus the
station name and position from the file header. KNMI data is CC0 ("bron: KNMI").

Standard library only. Runs in GitHub Actions (the KNMI host is not reachable
from every environment) and writes into OUT_DIR:

    stations.csv          stn,name,lon,lat,alt
    daily/<stn>.csv       date,tg,tn,tx   (degrees C, empty when missing)

    python analysis/natural-ice/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

import csv
import io
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API_URL = "https://www.daggegevens.knmi.nl/klimatologie/daggegevens"
ZIP_URL = "https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/daggegevens/etmgeg_{stn}.zip"
HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}

# Every station number KNMI has used for daily data; missing ones are skipped.
STATIONS = [
    209,
    210,
    215,
    225,
    235,
    240,
    242,
    248,
    249,
    251,
    257,
    258,
    260,
    265,
    267,
    269,
    270,
    273,
    275,
    277,
    278,
    279,
    280,
    283,
    285,
    286,
    290,
    308,
    310,
    311,
    312,
    313,
    315,
    316,
    319,
    323,
    324,
    330,
    331,
    340,
    343,
    344,
    348,
    350,
    356,
    370,
    375,
    377,
    380,
    391,
]

HEADER_STATION = re.compile(
    r"^#?\s*(\d{3}):?\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(.+?)\s*$"
)


def get(url: str, data: bytes | None = None, retries: int = 3) -> bytes | None:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, data=data, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if attempt == retries - 1:
                raise
        except Exception:
            if attempt == retries - 1:
                raise
        time.sleep(2 ** (attempt + 1))
    return None


def tenths(value: str) -> str:
    value = value.strip()
    return "" if value == "" else f"{int(value) / 10:.1f}"


def parse(text: str, stn: int) -> tuple[dict | None, list[list[str]]]:
    meta, columns, rows = None, None, []
    for line in text.splitlines():
        if meta is None:
            match = HEADER_STATION.match(line)
            if match and int(match.group(1)) == stn:
                meta = {
                    "stn": stn,
                    "lon": float(match.group(2)),
                    "lat": float(match.group(3)),
                    "alt": float(match.group(4)),
                    "name": match.group(5).strip(),
                }
        if columns is None and "YYYYMMDD" in line:
            columns = [c.strip().lstrip("#").strip() for c in line.split(",")]
            continue
        if columns is None or not line.strip() or line.startswith("#"):
            continue
        cells = dict(zip(columns, line.split(","), strict=False))
        date = cells.get("YYYYMMDD", "").strip()
        if not date.isdigit():
            continue
        rows.append(
            [
                f"{date[:4]}-{date[4:6]}-{date[6:]}",
                tenths(cells.get("TG", "")),
                tenths(cells.get("TN", "")),
                tenths(cells.get("TX", "")),
            ]
        )
    return meta, rows


def download(stn: int) -> str | None:
    """Return the station's daily file as text, or None if KNMI has no data."""
    form = urllib.parse.urlencode(
        {"stns": stn, "vars": "TG:TN:TX", "start": "19010101", "end": time.strftime("%Y%m%d")}
    ).encode()
    try:
        payload = get(API_URL, data=form)
        if payload and b"YYYYMMDD" in payload and b"," in payload.split(b"YYYYMMDD")[1][:200]:
            return payload.decode("latin-1")
        print(
            f"{stn}: script interface gave {len(payload or b'')} bytes, trying zip", file=sys.stderr
        )
    except Exception as error:  # noqa: BLE001 - fall back to the zip
        print(f"{stn}: script interface failed ({error}), trying zip", file=sys.stderr)
    payload = get(ZIP_URL.format(stn=stn))
    if payload is None:
        return None
    if not payload.startswith(b"PK"):
        print(f"{stn}: zip URL returned {payload[:200]!r}", file=sys.stderr)
        return None
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        name = next(n for n in archive.namelist() if n.lower().endswith(".txt"))
        return archive.read(name).decode("latin-1")


def main(out: Path) -> None:
    (out / "daily").mkdir(parents=True, exist_ok=True)
    stations = []
    print("| station | name | first day | last day | days |\n| --- | --- | --- | --- | --- |")
    for stn in STATIONS:
        text = download(stn)
        if text is None:
            continue
        meta, rows = parse(text, stn)
        if not rows:
            print(f"| {stn} | (no rows) | | | 0 |", file=sys.stderr)
            print(text[:600], file=sys.stderr)
            continue
        meta = meta or {"stn": stn, "lon": "", "lat": "", "alt": "", "name": ""}
        stations.append(meta)
        with open(out / "daily" / f"{stn}.csv", "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["date", "tg", "tn", "tx"])
            writer.writerows(rows)
        print(f"| {stn} | {meta['name']} | {rows[0][0]} | {rows[-1][0]} | {len(rows):,} |")
    with open(out / "stations.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["stn", "name", "lon", "lat", "alt"])
        writer.writeheader()
        writer.writerows(stations)
    print(f"\n{len(stations)} stations")
    if not stations:
        sys.exit("No stations downloaded")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "raw"))
