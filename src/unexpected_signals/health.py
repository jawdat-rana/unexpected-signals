"""Weekly health report for the repo.

Reads the `data` branch and, optionally, recent workflow runs and open pull
requests from the API, and writes a Markdown report:

- collectors: when each feed last succeeded, rows stored per day for the last
  week, and the longest gap between collect runs. A feed counts as quiet when
  its last success is older than three of its intervals and at least six
  hours, so one slow GitHub schedule doesn't raise an alarm.
- workflows: failed runs per workflow this week. A workflow needs a look when
  its latest run on `main` failed, so a failure that has since recovered
  (a feed hiccup, a re-run) is listed but doesn't raise an alarm.
- pull requests: open ones older than a week. One needs a look when nobody has
  touched it for two weeks.

    python -m unexpected_signals health --data data-branch/data --runs runs.json \
        --workflow-runs workflow_runs.json --pulls pulls.json
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
PR_OLD = timedelta(days=7)  # listed in the report
PR_STALE = timedelta(days=14)  # no updates for this long: needs a look


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


def workflow_failures(runs: list[dict], since: datetime) -> list[dict]:
    """Per workflow with failures since `since`: count, latest failure, still broken."""
    by_name: dict[str, list[dict]] = {}
    for run in runs:
        if state.parse_time(run["created_at"]) >= since:
            by_name.setdefault(run.get("name") or run.get("path", "?"), []).append(run)
    result = []
    for name, group in sorted(by_name.items()):
        group.sort(key=lambda r: r["created_at"])
        failed = [r for r in group if r.get("conclusion") == "failure"]
        if not failed:
            continue
        on_main = [r for r in group if r.get("head_branch") == "main" and r.get("conclusion")]
        broken = bool(on_main) and on_main[-1].get("conclusion") == "failure"
        result.append({"name": name, "failed": len(failed), "latest": failed[-1], "broken": broken})
    return result


def old_pulls(pulls: list[dict], now: datetime) -> list[dict]:
    """Open pull requests older than a week, oldest first, with `stale` set."""
    result = []
    for pr in pulls:
        opened = state.parse_time(pr["created_at"])
        if now - opened < PR_OLD:
            continue
        updated = state.parse_time(pr.get("updated_at") or pr["created_at"])
        result.append({**pr, "age": now - opened, "stale": now - updated >= PR_STALE})
    return sorted(result, key=lambda p: p["created_at"])


def report(
    config: dict,
    data: Path,
    now: datetime,
    runs: list[dict] | None = None,
    days: int = 7,
    workflow_runs: list[dict] | None = None,
    pulls: list[dict] | None = None,
) -> tuple[str, list[str]]:
    """The Markdown report and what needs a look (quiet feeds first)."""
    day_list = [(now - timedelta(days=n)).date() for n in range(days, 0, -1)]
    feeds = feed_health(config, data, day_list)
    quiet = [f.name for f in feeds if f.quiet(now)]
    failures = workflow_failures(workflow_runs or [], now - timedelta(days=days))
    pull_list = old_pulls(pulls or [], now)
    alerts = list(quiet)
    alerts += [f"workflow {w['name']} is failing on main" for w in failures if w["broken"]]
    alerts += [f"PR #{p['number']} untouched for 2+ weeks" for p in pull_list if p["stale"]]

    lines = [f"## Repo health, {now:%Y-%m-%d %H:%M} UTC", ""]
    if alerts:
        lines += ["**Needs a look:**", ""] + [f"- {a}" for a in alerts] + [""]
    else:
        lines += ["Nothing needs a look this week.", ""]

    if workflow_runs is not None:
        lines += [f"### Workflows, last {days} days", ""]
        if failures:
            lines += ["| Workflow | Failed runs | Latest failure | Latest run on main |"]
            lines.append("| --- | ---: | --- | --- |")
            for w in failures:
                latest = w["latest"]
                when = f"{state.parse_time(latest['created_at']):%a %d %b %H:%M}"
                link = f"[{when}]({latest['html_url']})" if latest.get("html_url") else when
                status = "failed ⚠️" if w["broken"] else "ok"
                lines.append(f"| {w['name']} | {w['failed']} | {link} | {status} |")
        else:
            lines.append("No failed runs.")
        lines.append("")

    if pulls is not None:
        lines += ["### Pull requests open for more than a week", ""]
        if pull_list:
            for p in pull_list:
                draft = " (draft)" if p.get("draft") else ""
                flag = " ⚠️ untouched for 2+ weeks" if p["stale"] else ""
                lines.append(
                    f"- [#{p['number']} {p['title']}]({p.get('html_url', '')}){draft}, "
                    f"open {p['age'].days} days{flag}"
                )
        else:
            lines.append("None.")
        lines.append("")

    lines += ["### Collectors", ""]
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
    return "\n".join(lines) + "\n", alerts


def load_pulls(path: Path | None) -> list[dict] | None:
    """Open pull requests, as one API reply or a list of pages."""
    if path is None or not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw and isinstance(raw[0], list):
        return [pr for page in raw for pr in page]
    return raw


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
