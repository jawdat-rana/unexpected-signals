"""Turn raw data into the small CSVs the SLUG story's charts read.

Keep raw downloads in analysis/SLUG/raw/ (git ignores it) and write only
chart-ready, aggregated data into stories/SLUG/data/, which is published.

    python analysis/SLUG/prepare.py
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw"
OUT = HERE.parent.parent / "stories" / "SLUG" / "data"

SOURCE_URL = "https://example.org/data.csv"  # replace with the real source


def download(url: str, name: str) -> Path:
    """Download once and cache, so reruns are fast and polite to the source."""
    RAW.mkdir(exist_ok=True)
    path = RAW / name
    if not path.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "unexpected-signals"})
        with urllib.request.urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
    return path


def write_csv(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {(OUT / name).relative_to(HERE.parent.parent)}")


def main() -> None:
    raw = download(SOURCE_URL, "source.csv")
    with raw.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    # Aggregate here. Publish the numbers behind the chart, not the raw dump.
    write_csv("chart.csv", rows)


if __name__ == "__main__":
    main()
