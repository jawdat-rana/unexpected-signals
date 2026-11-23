"""Google Trends "Trending now" RSS (trends.google.com/trending/rss?geo=XX).

The feed only lists searches that spiked in roughly the last day. Snapshots are
merged into one row per trend (geo + title + start time), with the first and
last time it was seen and the highest traffic band shown.
"""

from __future__ import annotations

from datetime import UTC
from email.utils import parsedate_to_datetime
from typing import IO, Any
from xml.etree import ElementTree as ET

from .datex import local

ISO = "%Y-%m-%dT%H:%M:%SZ"

COLUMNS = [
    "geo",
    "title",
    "started",
    "approx_traffic",
    "traffic_min",
    "news_title",
    "news_source",
    "news_url",
    "first_seen",
    "last_seen",
]


def traffic_floor(band: str | None) -> int:
    """'200+' -> 200, '10K+' -> 10000, '2M+' -> 2000000."""
    if not band:
        return 0
    text = band.strip().rstrip("+").replace(",", "").upper()
    scale = {"K": 1_000, "M": 1_000_000}.get(text[-1:], 1)
    try:
        return int(float(text.rstrip("KM")) * scale)
    except ValueError:
        return 0


def _child(elem: ET.Element, name: str) -> str | None:
    for child in elem:
        if local(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def parse(source: IO[bytes], geo: str, fetched_at: str) -> list[dict[str, Any]]:
    rows = []
    for item in ET.parse(source).getroot().iter():
        if local(item.tag) != "item":
            continue
        pub = _child(item, "pubDate")
        try:
            started = parsedate_to_datetime(pub).astimezone(UTC).strftime(ISO) if pub else ""
        except (TypeError, ValueError):
            started = pub or ""
        news = next((c for c in item if local(c.tag) == "news_item"), None)
        band = _child(item, "approx_traffic")
        rows.append(
            {
                "geo": geo,
                "title": _child(item, "title"),
                "started": started,
                "approx_traffic": band,
                "traffic_min": traffic_floor(band),
                "news_title": _child(news, "news_item_title") if news is not None else None,
                "news_source": _child(news, "news_item_source") if news is not None else None,
                "news_url": _child(news, "news_item_url") if news is not None else None,
                "first_seen": fetched_at,
                "last_seen": fetched_at,
            }
        )
    return rows


def merge(existing: list[dict[str, str]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Upsert by (geo, title, started); keep the earliest first_seen and the top band."""

    def key(row: dict) -> tuple[str, str, str]:
        return (str(row["geo"]), str(row["title"]), str(row["started"]))

    by_key: dict[tuple[str, str, str], dict[str, Any]] = {key(r): dict(r) for r in existing}
    for row in new:
        old = by_key.get(key(row))
        if old is not None:
            row = dict(row)
            row["first_seen"] = old.get("first_seen") or row["first_seen"]
            if int(old.get("traffic_min") or 0) > int(row["traffic_min"] or 0):
                row["approx_traffic"] = old.get("approx_traffic")
                row["traffic_min"] = old.get("traffic_min")
        by_key[key(row)] = row
    return sorted(
        by_key.values(), key=lambda r: (str(r["geo"]), str(r["started"]), str(r["title"]))
    )
