"""Shazam's top 200 charts, from the CSV behind shazam.com/charts.

Each chart covers "performance over the past 7 days" and is replaced daily, so
earlier days exist only if saved. Shazam counts people identifying a song they
hear somewhere (a TikTok video, the radio, a shop), which makes it an early
signal of songs catching on before they climb streaming charts.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

COLUMNS = ["chart_date", "chart", "rank", "artist", "title", "fetched_at"]

BASE = "https://www.shazam.com/services/charts/csv/top-200/"


def parse(raw: bytes, chart: str, fetched_at: str) -> tuple[str, list[dict]]:
    """Return (chart date as YYYY-MM-DD, rows). The date comes from the title line."""
    lines = raw.decode("utf-8-sig").splitlines()
    chart_date = fetched_at[:10]
    for i, line in enumerate(lines):
        text = line.strip().strip('"')
        if text.lower().startswith("rank,"):
            body = "\n".join(lines[i:])
            break
        if text:
            try:  # "Monday, 23 November 2026 [performance over the past 7 days]"
                stamp = datetime.strptime(text.split("[")[0].strip(), "%A, %d %B %Y")
                chart_date = stamp.date().isoformat()
            except ValueError:
                pass
    else:
        return chart_date, []
    rows = []
    for row in csv.DictReader(io.StringIO(body)):
        rows.append(
            {
                "chart_date": chart_date,
                "chart": chart,
                "rank": row.get("Rank"),
                "artist": row.get("Artist"),
                "title": row.get("Title"),
                "fetched_at": fetched_at,
            }
        )
    return chart_date, rows


def replace_chart(existing: list[dict], chart: str, new: list[dict]) -> list[dict]:
    """Swap one chart's rows in a day file for the newest fetch of it."""
    kept = [r for r in existing if r.get("chart") != chart]
    return sorted(kept + new, key=lambda r: (str(r["chart"]), int(r["rank"] or 0)))
