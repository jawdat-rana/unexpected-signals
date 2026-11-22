"""Netflix's weekly Top 10 (netflix.com/tudum/top10).

Netflix keeps the full history in its own downloadable files, so this only
mirrors the latest week, as a backup in case those files change or disappear.
"""

from __future__ import annotations

import csv
import io


def latest_week(raw: bytes) -> tuple[str, list[str], list[dict[str, str]]]:
    """The newest week in a Netflix TSV: (week, columns, rows of that week)."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter="\t")
    rows = list(reader)
    if not rows:
        return "", list(reader.fieldnames or []), []
    week = max(r["week"] for r in rows)
    return week, list(reader.fieldnames or []), [r for r in rows if r["week"] == week]
