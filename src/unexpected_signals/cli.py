"""Command line entry point: `python -m unexpected_signals collect`."""

from __future__ import annotations

import argparse
import io
import sys
import tomllib
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import bridges, sites, storage, traffic
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
            traffic.select(rows, watchlist),
        )
    return (
        f"traffic: {len(rows)} sites reporting, {roads} motorways summarised, "
        f"{kept} configured sites kept"
    )


COLLECTORS = {"bridges": collect_bridges, "traffic": collect_traffic}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="unexpected-signals")
    sub = parser.add_subparsers(dest="command", required=True)
    col = sub.add_parser("collect", help="take one snapshot of each enabled feed")
    col.add_argument("--config", type=Path, default=Path("config.toml"))
    col.add_argument("--out", type=Path, default=Path("data"))
    col.add_argument("--only", choices=sorted(COLLECTORS), action="append")
    col.add_argument("--sample-dir", type=Path, help="also save the raw XML here, for debugging")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    fetched_at = now_iso()
    if args.sample_dir:
        args.sample_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for name, collector in COLLECTORS.items():
        feed = config.get(name, {})
        if args.only and name not in args.only:
            continue
        if not feed.get("enabled", False):
            continue
        try:
            print(collector(feed, args.out, fetched_at, args.sample_dir))
        except Exception as exc:  # one broken feed should not stop the others
            failures += 1
            print(f"{name}: FAILED: {exc!r}", file=sys.stderr)
    return 1 if failures else 0
