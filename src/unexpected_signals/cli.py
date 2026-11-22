"""Command line entry point: `python -m unexpected_signals collect`."""

from __future__ import annotations

import argparse
import io
import json
import sys
import tomllib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import bridges, charts, netflix, ovfiets, parking, sites, state, storage, traffic, trends
from .fetch import download


def load_config(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect_bridges(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    raw = download(cfg["url"], retries=cfg.get("retries", 3))
    if sample_dir:
        (sample_dir / "bridges.xml").write_bytes(raw)
    records = bridges.parse(io.BytesIO(raw), fetched_at)
    # Partition by the opening's own date, so only files for recent and
    # upcoming days change between snapshots.
    by_day: dict[str, list[bridges.BridgeRecord]] = defaultdict(list)
    for rec in records:
        by_day[(rec.start_time or fetched_at)[:10]].append(rec)
    for day, day_records in sorted(by_day.items()):
        path = storage.day_path(out, "bridges", day)
        storage.write_rows(
            path, bridges.COLUMNS, bridges.merge(storage.read_rows(path), day_records)
        )
    probabilities = Counter(rec.probability or "unknown" for rec in records)
    breakdown = ", ".join(f"{k}={v}" for k, v in probabilities.most_common())
    return f"bridges: {len(records)} records over {len(by_day)} days ({breakdown})"


def site_catalogue(cfg: dict, out: Path, fetched_at: str) -> list[dict[str, str]]:
    """The measurement-site table, re-downloaded when it is older than a week.

    Stored as data/traffic_sites_catalogue.csv with the time it was fetched in
    a sidecar file, so it can be browsed and mapped without parsing XML.
    """
    url = cfg.get("catalogue_url")
    if not url:
        return []
    path = out / "traffic_sites_catalogue.csv"
    stamp = out / "traffic_sites_catalogue.fetched_at"
    max_age = timedelta(days=cfg.get("catalogue_max_age_days", 7))
    now = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    if path.exists() and stamp.exists():
        last = datetime.fromisoformat(stamp.read_text().strip().replace("Z", "+00:00"))
        if now - last < max_age:
            return storage.read_rows(path)
    raw = download(url, retries=cfg.get("retries", 3))
    rows = [asdict(site) for site in sites.parse(io.BytesIO(raw))]
    rows.sort(key=lambda r: r["site_id"])
    storage.write_rows(path, sites.COLUMNS, rows)
    stamp.write_text(fetched_at + "\n")
    return storage.read_rows(path)


def collect_traffic(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    raw = download(cfg["url"], retries=cfg.get("retries", 3))
    if sample_dir:
        (sample_dir / "traffic.xml").write_bytes(raw)
    rows = traffic.parse(io.BytesIO(raw))
    summary = traffic.summarise(rows, fetched_at)
    storage.append_rows(
        storage.day_path(out, "traffic_summary", fetched_at), traffic.SUMMARY_COLUMNS, [summary]
    )
    roads = 0
    try:
        catalogue = site_catalogue(cfg, out, fetched_at)
    except Exception as exc:  # the live numbers matter more than the catalogue
        print(f"traffic: site catalogue unavailable: {exc!r}", file=sys.stderr)
        catalogue = []
    if catalogue:
        road_rows = traffic.summarise_roads(rows, sites.motorway_main_lanes(catalogue), fetched_at)
        roads = storage.append_rows(
            storage.day_path(out, "traffic_roads", fetched_at), traffic.ROAD_COLUMNS, road_rows
        )
    watchlist = set(cfg.get("sites", []))
    kept = 0
    if watchlist:
        kept = storage.append_rows(
            storage.day_path(out, "traffic_sites", fetched_at),
            traffic.SITE_COLUMNS,
            traffic.select(rows, watchlist, fetched_at),
        )
    return (
        f"traffic: {len(rows)} sites reporting, {roads} motorways summarised, "
        f"{kept} configured sites kept"
    )


def _changed_only(
    rows: list[dict], key: str, fields: list[str], seen: dict[str, str]
) -> list[dict]:
    """Rows whose `fields` differ from the last stored values; updates `seen`."""
    kept = []
    for row in rows:
        value = "|".join(str(row.get(f)) for f in fields)
        if seen.get(str(row[key])) != value:
            seen[str(row[key])] = value
            kept.append(row)
    return kept


def _is_stale(stamp: str | None, fetched_at: str, days: float) -> bool:
    if not stamp:
        return True
    age = state.parse_time(fetched_at) - state.parse_time(stamp)
    return age.total_seconds() >= days * 86400


def collect_parking(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    retries = cfg.get("retries", 3)
    index = json.loads(download(cfg["url"], retries=retries))
    live = parking.live_facilities(index)
    if not cfg.get("include_limited_access", False):
        # These answer 401 without an RDW account.
        live = [f for f in live if not f.get("limitedAccess")]

    def fetch(url: str) -> dict | None:
        try:
            return json.loads(download(url, retries=1, timeout=20))
        except Exception:
            return None

    with ThreadPoolExecutor(cfg.get("workers", 16)) as pool:
        payloads = list(pool.map(fetch, [f["dynamicDataUrl"] for f in live]))
    if sample_dir:
        (sample_dir / "parking.json").write_text(json.dumps(payloads[:20], indent=1))
    rows = [r for p in payloads if p for r in [parking.parse_status(p, fetched_at)] if r]
    if live and not rows:
        raise RuntimeError(f"none of {len(live)} live parking feeds answered")

    memory = state.load(out, "parking")
    kept = _changed_only(
        rows,
        "facility_id",
        ["open", "full", "capacity", "vacant", "last_updated"],
        memory.setdefault("last", {}),
    )
    storage.append_rows(storage.day_path(out, "parking", fetched_at), parking.STATUS_COLUMNS, kept)

    catalogued = ""
    if _is_stale(memory.get("catalogue_at"), fetched_at, cfg.get("catalogue_max_age_days", 7)):
        ids = {r["facility_id"] for r in rows}
        urls = [f["staticDataUrl"] for f in live if f.get("identifier") in ids]
        with ThreadPoolExecutor(cfg.get("workers", 16)) as pool:
            statics = list(pool.map(fetch, urls))
        catalogue = [c for p in statics if p for c in [parking.parse_static(p)] if c]
        catalogue.sort(key=lambda c: str(c["facility_id"]))
        storage.write_rows(out / "parking_catalogue.csv", parking.CATALOGUE_COLUMNS, catalogue)
        memory["catalogue_at"] = fetched_at
        catalogued = f", catalogue of {len(catalogue)} refreshed"
    state.save(out, "parking", memory)
    full = sum(1 for r in rows if r["full"] is True)
    return (
        f"parking: {len(rows)}/{len(live)} live facilities answered, {full} full, "
        f"{len(kept)} changed rows stored{catalogued}"
    )


def collect_charts(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    # Apple answers each chart slowly (5-10 s), so they are fetched in parallel.
    jobs = [
        (c, ch) for c in cfg.get("countries", ["nl"]) for ch in cfg.get("charts", ["apps-free"])
    ]

    def fetch(job: tuple[str, str]) -> list[dict] | str:
        country, chart = job
        url = charts.url(country, chart, cfg.get("size", 100), cfg.get("base", charts.BASE))
        try:
            payload = json.loads(download(url, retries=cfg.get("retries", 3)))
        except Exception as exc:
            return f"{country}/{chart}: {exc!r}"
        return charts.parse(payload, country, chart, fetched_at)

    with ThreadPoolExecutor(cfg.get("workers", 8)) as pool:
        results = list(pool.map(fetch, jobs))
    rows = [row for r in results if isinstance(r, list) for row in r]
    failed = [r for r in results if isinstance(r, str)]
    storage.append_rows(storage.day_path(out, "apple_charts", fetched_at), charts.COLUMNS, rows)
    if failed:
        raise RuntimeError(f"{len(rows)} rows saved, but these failed: {failed}")
    return f"apple charts: {len(rows)} rows"


def collect_trends(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    rows, failed = [], []
    for geo in cfg.get("geos", ["NL"]):
        try:
            raw = download(cfg["url"].format(geo=geo), retries=cfg.get("retries", 3))
            if sample_dir:
                (sample_dir / f"trends_{geo}.xml").write_bytes(raw)
            rows += trends.parse(io.BytesIO(raw), geo, fetched_at)
        except Exception as exc:
            failed.append(f"{geo}: {exc!r}")
    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_day[(row["started"] or fetched_at)[:10]].append(row)
    for day, day_rows in sorted(by_day.items()):
        path = storage.day_path(out, "google_trending", day)
        storage.write_rows(path, trends.COLUMNS, trends.merge(storage.read_rows(path), day_rows))
    if failed:
        raise RuntimeError(f"{len(rows)} trends saved, but these failed: {failed}")
    return f"google trending: {len(rows)} trends across {len(cfg.get('geos', ['NL']))} countries"


def collect_ovfiets(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    raw = download(cfg["url"], retries=cfg.get("retries", 3))
    rows, catalogue = ovfiets.parse(json.loads(raw), fetched_at)
    if not rows:
        raise RuntimeError("OV-fiets feed listed no locations")
    memory = state.load(out, "ovfiets")
    kept = _changed_only(rows, "location", ["bikes", "open"], memory.setdefault("last", {}))
    storage.append_rows(storage.day_path(out, "ovfiets", fetched_at), ovfiets.STATUS_COLUMNS, kept)
    storage.write_rows(out / "ovfiets_catalogue.csv", ovfiets.CATALOGUE_COLUMNS, catalogue)
    state.save(out, "ovfiets", memory)
    bikes = sum(r["bikes"] or 0 for r in rows)
    newest = max((r["feed_time"] for r in rows if r["feed_time"]), default="?")
    return (
        f"ovfiets: {len(rows)} locations, {bikes} bikes available, {len(kept)} changed rows "
        f"stored (feed time {newest})"
    )


def collect_netflix(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    notes, failed = [], []
    for kind, url in cfg.get("files", {}).items():
        try:
            raw = download(url, retries=cfg.get("retries", 3), allow_partial=True)
            week, columns, rows = netflix.latest_week(raw)
        except Exception as exc:
            failed.append(f"{kind}: {exc!r}")
            continue
        if week:
            storage.write_rows(out / "netflix_top10" / kind / f"{week}.csv", columns, rows)
        notes.append(f"{kind} week {week or '?'} ({len(rows)} rows)")
    if failed:
        raise RuntimeError(f"saved {notes}, but these failed: {failed}")
    return "netflix top 10: " + ", ".join(notes)


COLLECTORS = {
    "bridges": collect_bridges,
    "traffic": collect_traffic,
    "parking": collect_parking,
    "apple_charts": collect_charts,
    "google_trending": collect_trends,
    "ovfiets": collect_ovfiets,
    "netflix_top10": collect_netflix,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="unexpected-signals")
    sub = parser.add_subparsers(dest="command", required=True)
    col = sub.add_parser("collect", help="take one snapshot of each enabled feed")
    col.add_argument("--config", type=Path, default=Path("config.toml"))
    col.add_argument("--out", type=Path, default=Path("data"))
    col.add_argument("--only", choices=sorted(COLLECTORS), action="append")
    col.add_argument("--sample-dir", type=Path, help="also save raw responses here, for debugging")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    fetched_at = now_iso()
    if args.sample_dir:
        args.sample_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    schedule = state.load(args.out, "schedule")
    for name, collector in COLLECTORS.items():
        feed = config.get(name, {})
        if args.only and name not in args.only:
            continue
        if not feed.get("enabled", False):
            continue
        # Feeds that change slowly set `every_minutes`; skip them until due.
        if not args.only and not state.is_due(
            schedule.get(name), fetched_at, feed.get("every_minutes", 0)
        ):
            continue
        try:
            print(collector(feed, args.out, fetched_at, args.sample_dir))
            schedule[name] = fetched_at
        except Exception as exc:  # one broken feed should not stop the others
            failures += 1
            print(f"{name}: FAILED: {exc!r}", file=sys.stderr)
    if args.out.exists():
        state.save(args.out, "schedule", schedule)
    return 1 if failures else 0
