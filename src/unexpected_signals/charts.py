"""Apple's public chart feeds (App Store and Apple Music), per country.

https://rss.marketingtools.apple.com/api/v2/<country>/<media>/<chart>/<n>/<type>.json
Apple only serves the current chart, so ranks over time exist only if saved.
"""

from __future__ import annotations

from typing import Any

COLUMNS = ["fetched_at", "country", "chart", "rank", "id", "name", "artist", "genre", "released"]

# Short chart names used in config.toml -> path segment of the feed URL.
CHARTS = {
    "apps-free": "apps/top-free/{n}/apps.json",
    "apps-paid": "apps/top-paid/{n}/apps.json",
    "songs": "music/most-played/{n}/songs.json",
    "albums": "music/most-played/{n}/albums.json",
}

BASE = "https://rss.marketingtools.apple.com/api/v2/"


def url(country: str, chart: str, n: int = 100, base: str = BASE) -> str:
    return base + f"{country}/" + CHARTS[chart].format(n=n)


def parse(payload: dict, country: str, chart: str, fetched_at: str) -> list[dict[str, Any]]:
    results = (payload.get("feed") or {}).get("results") or []
    rows = []
    for rank, item in enumerate(results, start=1):
        genres = item.get("genres") or []
        genre = genres[0].get("name") if genres and isinstance(genres[0], dict) else None
        rows.append(
            {
                "fetched_at": fetched_at,
                "country": country,
                "chart": chart,
                "rank": rank,
                "id": item.get("id"),
                "name": item.get("name"),
                "artist": item.get("artistName"),
                "genre": genre,
                "released": item.get("releaseDate"),
            }
        )
    return rows
