"""Small JSON state files kept next to the data, in data/_state/<name>.json.

Used for two things: remembering when a slow feed last ran (so it can run less
often than the workflow fires), and remembering the last value seen per item
(so feeds that barely change only store a row when something changed).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def path_for(root: Path, name: str) -> Path:
    return root / "_state" / f"{name}.json"


def load(root: Path, name: str) -> dict:
    path = path_for(root, name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:  # a half-written file should not stop collection
        return {}


def save(root: Path, name: str, data: dict) -> None:
    path = path_for(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def parse_time(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def is_due(last_run: str | None, now: str, every_minutes: float) -> bool:
    """True when at least `every_minutes` have passed since `last_run`.

    Two minutes of slack, because the workflow fires at uneven times and a run
    that comes 30 seconds early should not push a feed back a whole interval.
    """
    if not last_run or every_minutes <= 0:
        return True
    elapsed = (parse_time(now) - parse_time(last_run)).total_seconds() / 60
    return elapsed >= every_minutes - 2
