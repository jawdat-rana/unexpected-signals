"""Weekly health report for the collectors.

Reads the `data` branch and, optionally, the collect workflow's recent runs, and
writes a Markdown report: when each feed last succeeded, rows stored per day for
the last week, and the longest gap between workflow runs. A feed counts as
quiet when its last success is older than three of its intervals and at least
six hours, so one slow GitHub schedule doesn't raise an alarm.

    python -m unexpected_signals health --data data-branch/data --runs runs.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from . import state

# The folders under data/ each feed writes its dated CSVs to.
FOLDERS = {
    "bridges": ["bridges"],
    "traffic": ["traffic_summary", "traffic_roads", "traffic_sites"],
    "parking": ["parking"],
    "apple_charts": ["apple_charts"],
    "google_trending": ["google_trending"],
    "ovfiets": ["ovfiets"],
    "shazam": ["shazam"],
}
WORKFLOW_MINUTES = 5  # how often cron-job.org fires the collect workflow
MIN_QUIET = timedelta(hours=6)


@dataclass
class FeedHealth:
    name: str
    every: timedelta
    last_success: datetime | None
    rows: dict[str, dict[date, int]]  # folder -> day -> rows

    def quiet(self, now: datetime) -> bool:
        if self.last_success is None:
            return True
        return now - self.last_success > max(3 * self.every, MIN_QUIET)


def count_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return max(0, sum(1 for _ in handle) - 1)  # minus the header


def feed_health(config: dict, data: Path, days: list[date]) -> list[FeedHealth]:
    schedule = state.load(data, "schedule")
    feeds = []
    for name, folders in FOLDERS.items():
        feed = config.get(name, {})
        if not feed.get("enabled", False):
            continue
        every = timedelta(minutes=max(feed.get("every_minutes", 0), WORKFLOW_MINUTES))
        stamp = schedule.get(name)
        rows = {}
        for folder in folders:
            per_day = {}
            for day in days:
                path = data / folder / f"{day:%Y}" / f"{day:%m}" / f"{day.isoformat()}.csv"
                per_day[day] = count_rows(path) if path.exists() else 0
            rows[folder] = per_day
        feeds.append(FeedHealth(name, every, state.parse_time(stamp) if stamp else None, rows))
    return feeds


def run_gaps(runs: list[dict], since: datetime) -> tuple[int, int, timedelta | None]:
    """Runs, failed runs and the longest gap between two runs since `since`."""
    recent = sorted(
        state.parse_time(r["created_at"])
        for r in runs
        if state.parse_time(r["created_at"]) >= since
    )
    failed = sum(
        1
        for r in runs
        if state.parse_time(r["created_at"]) >= since and r.get("conclusion") == "failure"
    )
    gaps = [b - a for a, b in zip(recent, recent[1:], strict=False)]
    return len(recent), failed, max(gaps) if gaps else None


def hours(delta: timedelta) -> str:
    total = delta.total_seconds() / 3600
    return f"{total:.1f} h" if total < 48 else f"{total / 24:.1f} days"


def report(
    config: dict, data: Path, now: datetime, runs: list[dict] | None = None, days: int = 7
) -> tuple[str, list[str]]:
    """The Markdown report and the names of quiet feeds."""
    day_list = [(now - timedelta(days=n)).date() for n in range(days, 0, -1)]
    feeds = feed_health(config, data, day_list)
    quiet = [f.name for f in feeds if f.quiet(now)]

    lines = [f"## Collector health, {now:%Y-%m-%d %H:%M} UTC", ""]
    if quiet:
        lines += [f"**Quiet feeds:** {', '.join(quiet)}", ""]
    else:
        lines += ["All feeds succeeded recently.", ""]

    lines += ["| Feed | Last success | Ago | Expected every |", "| --- | --- | --- | --- |"]
    for f in feeds:
        last = f"{f.last_success:%Y-%m-%d %H:%M}" if f.last_success else "never"
        ago = hours(now - f.last_success) if f.last_success else "-"
        flag = " ⚠️" if f.name in quiet else ""
        lines.append(f"| {f.name}{flag} | {last} | {ago} | {hours(f.every)} |")

    header = " | ".join(f"{d:%a %d}" for d in day_list)
    lines += ["", "Rows stored per day (UTC):", "", f"| Folder | {header} |"]
    lines.append("| --- |" + " ---: |" * len(day_list))
    for f in feeds:
        for folder, per_day in f.rows.items():
            cells = " | ".join(f"{per_day[d]:,}" for d in day_list)
            lines.append(f"| {folder} | {cells} |")

    if runs is not None:
        count, failed, gap = run_gaps(runs, now - timedelta(days=days))
        lines += [
            "",
            f"Collect workflow, last {days} days: {count} runs, {failed} failed, "
            f"longest gap between runs {hours(gap) if gap else '-'}.",
        ]
    return "\n".join(lines) + "\n", quiet


def load_runs(path: Path | None) -> list[dict] | None:
    if path is None or not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Either the API reply ({"workflow_runs": [...]}) or pages of it as a list.
    if isinstance(raw, dict):
        return raw.get("workflow_runs", [])
    return [run for page in raw for run in page.get("workflow_runs", [])]


def now_utc() -> datetime:
    return datetime.now(UTC)
