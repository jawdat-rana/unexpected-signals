"""Plain CSV storage, partitioned by date so files stay small and diffable."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(path: Path, columns: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})
    tmp.replace(path)


def append_rows(path: Path, columns: list[str], rows: Iterable[dict[str, object]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    count = 0
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})
            count += 1
    return count


def day_path(root: Path, dataset: str, stamp: str) -> Path:
    """data/<dataset>/YYYY/MM/YYYY-MM-DD.csv for an ISO timestamp."""
    day = stamp[:10]
    return root / dataset / day[:4] / day[5:7] / f"{day}.csv"
