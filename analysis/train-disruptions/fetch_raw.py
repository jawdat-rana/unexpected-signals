"""Download the raw sources for the passenger-impact story.

- Rijden de Treinen disruptions, one CSV per year (CC BY 4.0)
- NS annual report dashboard JSON, one file per year: stations and the
  passengers per track section between adjacent stations (attribute NS)

Only downloads; impact.py does the analysis. Standard library only.

    python analysis/train-disruptions/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path

RDT = "https://opendata.rijdendetreinen.nl/public/disruptions/disruptions-{year}.csv"
NS = "https://dashboards.nsjaarverslag.nl/api/dashboard/{year}"
HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}

SOURCES = [(f"disruptions-{y}.csv", RDT.format(year=y)) for y in range(2019, 2026)] + [
    (f"ns-dashboard-{y}.json", NS.format(year=y)) for y in range(2019, 2026)
]


def get(url: str, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES:
        payload = get(url)
        (out / name).write_bytes(payload)
        print(f"{name}\t{len(payload):,} bytes")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "raw"))
