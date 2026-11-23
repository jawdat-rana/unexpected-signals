"""Download CBS StatLine tables for the housing story.

For each table ID in tables.txt, downloads CBS's full CSV export (a ZIP with
Observations, MeasureCodes and one *Codes file per dimension) and unpacks it
into OUT_DIR/<ID>/. This is the same export a person gets from the StatLine
"download" button, so it needs no paging.

CBS open data is CC BY 4.0. Standard library only.

    python -u analysis/who-owns-homes/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

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


def fetch_table(table: str, out: Path) -> None:
    payload = get(ZIP.format(table=table))
    folder = out / table
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        archive.extractall(folder)
        names = archive.namelist()
    print(f"{table}\t{len(payload):,} bytes\t{', '.join(names)}", flush=True)


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    tables = [
        line.split("#")[0].strip()
        for line in (HERE / "tables.txt").read_text().splitlines()
        if line.split("#")[0].strip()
    ]
    for table in tables:
        try:
            fetch_table(table, out)
        except Exception as error:  # keep going; report which table failed
            print(f"{table}\tFAILED: {error}", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "raw"))
