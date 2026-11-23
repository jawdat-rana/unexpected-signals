"""Download CBS StatLine tables for the housing story.

For each table ID in tables.txt, downloads CBS's full CSV export (a ZIP with
Observations, MeasureCodes and one *Codes file per dimension) and unpacks it
into OUT_DIR/<ID>/. This is the same export a person gets from the StatLine
"download" button, so it needs no paging.

Some tables are several GB, so Observations.csv is cut down and gzipped:
- `keep=DimA,DimB` keeps every value of those dimensions; every other
  dimension is reduced to its total ("Totaal ...") where one exists.
- `regio=GM,PV,NL` keeps only regions whose code starts with those prefixes.
A line with only the ID keeps everything.

CBS open data is CC BY 4.0. Standard library only.

    python -u analysis/who-owns-homes/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

import csv
import gzip
import io
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
ZIP = "https://datasets.cbs.nl/CSV/CBS/nl/{table}"
HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}


def get(url: str, retries: int = 4) -> bytes:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=240) as response:
                return response.read()
        except Exception as error:
            print(f"  attempt {attempt + 1} failed: {error}", flush=True)
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 2))
    raise AssertionError("unreachable")


def total_code(codes_file: Path) -> str | None:
    with codes_file.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            title = (row.get("Title") or "").lower()
            if title.startswith("totaal") or title in {"mannen en vrouwen", "alle leeftijden"}:
                return row["Identifier"]
    return None


def filter_observations(folder: Path, keep: set[str], regio: tuple[str, ...]) -> None:
    source = folder / "Observations.csv"
    with source.open(encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle, delimiter=";"))
    wanted: dict[str, str] = {}
    for column in header:
        codes = folder / f"{column}Codes.csv"
        if not codes.exists() or column in keep or column == "RegioS" or column == "Perioden":
            continue
        code = total_code(codes)
        if code:
            wanted[column] = code
        else:
            print(f"  no total found for {column}; keeping all", flush=True)
    print(f"  fixed to totals: {wanted}", flush=True)
    kept = total = 0
    with source.open(encoding="utf-8-sig") as src, gzip.open(
        folder / "Observations.csv.gz", "wt", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src, delimiter=";")
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames, delimiter=";")
        writer.writeheader()
        for row in reader:
            total += 1
            if any(row.get(col) != code for col, code in wanted.items()):
                continue
            if regio and "RegioS" in row and not row["RegioS"].startswith(regio):
                continue
            writer.writerow(row)
            kept += 1
    source.unlink()
    print(f"  kept {kept:,} of {total:,} observations", flush=True)


def fetch_table(table: str, options: dict[str, str], out: Path) -> None:
    payload = get(ZIP.format(table=table))
    folder = out / table
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        archive.extractall(folder)
        names = archive.namelist()
    print(f"{table}\t{len(payload):,} bytes\t{', '.join(names)}", flush=True)
    keep = set(filter(None, options.get("keep", "").split(",")))
    regio = tuple(filter(None, options.get("regio", "").split(",")))
    filter_observations(folder, keep if options else set(open_all(folder)), regio)


def open_all(folder: Path) -> list[str]:
    with (folder / "Observations.csv").open(encoding="utf-8-sig") as handle:
        return next(csv.reader(handle, delimiter=";"))


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for line in (HERE / "tables.txt").read_text().splitlines():
        parts = line.split("#")[0].split()
        if not parts:
            continue
        table = parts[0]
        options = dict(part.split("=", 1) for part in parts[1:])
        try:
            fetch_table(table, options, out)
        except Exception as error:  # keep going; report which table failed
            print(f"{table}\tFAILED: {error}", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "raw"))
