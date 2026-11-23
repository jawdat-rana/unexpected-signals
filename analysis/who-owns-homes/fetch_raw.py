"""Download CBS StatLine tables for the housing story.

Writes, for each table ID in tables.txt:
  <ID>/data.csv          every observation (TypedDataSet, all pages)
  <ID>/<Dimension>.csv   code -> title for each dimension
  <ID>/DataProperties.csv and TableInfos.csv (column meanings, notes)
plus catalog.csv: every CBS table (ID, title, period, last modified), used to
find the right table IDs.

CBS open data is CC BY 4.0. Standard library only.

    python analysis/who-owns-homes/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = "https://opendata.cbs.nl/ODataApi/odata/{table}/{entity}?$format=json"
FEED = "https://opendata.cbs.nl/ODataFeed/odata/{table}/{entity}?$format=json"
CATALOG = "https://opendata.cbs.nl/ODataCatalog/Tables?$format=json&$select=Identifier,Title,Period,Modified,Language"
HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}


def get_json(url: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=300) as response:
                return json.load(response)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 2))
    raise AssertionError("unreachable")


def get_all(url: str) -> list[dict]:
    rows: list[dict] = []
    while url:
        page = get_json(url)
        rows.extend(page.get("value", []))
        url = page.get("odata.nextLink") or page.get("@odata.nextLink")
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields and not key.startswith("odata."):
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()})


def fetch_table(table: str, out: Path) -> None:
    folder = out / table
    props = get_all(API.format(table=table, entity="DataProperties"))
    write_csv(folder / "DataProperties.csv", props)
    write_csv(folder / "TableInfos.csv", get_all(API.format(table=table, entity="TableInfos")))
    for prop in props:
        if prop.get("Type") in {"Dimension", "GeoDimension", "TimeDimension", "GeoDetail"}:
            write_csv(folder / f"{prop['Key']}.csv", get_all(API.format(table=table, entity=prop["Key"])))
    data = get_all(FEED.format(table=table, entity="TypedDataSet"))
    write_csv(folder / "data.csv", data)
    print(f"{table}\t{len(data):,} rows")


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "catalog.csv", get_all(CATALOG))
    print("catalog written")
    tables = [
        line.split("#")[0].strip()
        for line in (HERE / "tables.txt").read_text().splitlines()
        if line.split("#")[0].strip()
    ]
    for table in tables:
        try:
            fetch_table(table, out)
        except Exception as error:  # keep going; report which table failed
            print(f"{table}\tFAILED: {error}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "raw"))
