"""Netflix's weekly Top 10 (netflix.com/tudum/top10).

Netflix keeps the full history in its own downloadable files, so this only
mirrors the latest week, as a backup in case those files change or disappear.
The files list the newest week first, and Netflix's server sometimes cuts a
download short, so a partial file is still used: its last, unfinished line is
dropped, and the newest week is complete as long as the cut comes after it.
"""

from __future__ import annotations

import csv
import io


def latest_week(raw: bytes) -> tuple[str, list[str], list[dict[str, str]]]:
    """The newest week in a Netflix TSV: (week, columns, rows of that week)."""
    text = raw.decode("utf-8-sig", errors="replace")
    cut = bool(text) and not text.endswith("\n")
    if cut:
        text = text[: text.rfind("\n") + 1]  # drop a line cut off mid-download
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    rows = list(reader)
    if not rows:
        return "", list(reader.fieldnames or []), []
    week = max(r["week"] for r in rows)
    if cut and rows[-1]["week"] == week:
        # The cut came inside the newest week, so it may be incomplete.
        raise ValueError(f"download ended inside the newest week ({week})")
    return week, list(reader.fieldnames or []), [r for r in rows if r["week"] == week]
