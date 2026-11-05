"""Command line entry point: `python -m unexpected_signals collect`."""

from __future__ import annotations

import argparse
import io
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from . import bridges, storage, traffic
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
    path = storage.month_path(out, "bridges", fetched_at)
    merged = bridges.merge(storage.read_rows(path), records)
    storage.write_rows(path, bridges.COLUMNS, merged)
    return f"bridges: {len(records)} records in snapshot, {len(merged)} rows in {path.name}"


def collect_traffic(cfg: dict, out: Path, fetched_at: str, sample_dir: Path | None) -> str:
    raw = download(cfg["url"], retries=cfg.get("retries", 3))
    if sample_dir:
        (sample_dir / "traffic.xml").write_bytes(raw)
    rows = traffic.parse(io.BytesIO(raw))
    summary = traffic.summarise(rows, fetched_at)
    storage.append_rows(
        storage.day_path(out, "traffic_summary", fetched_at), traffic.SUMMARY_COLUMNS, [summary]
    )
    sites = set(cfg.get("sites", []))
    kept = 0
    if sites:
        kept = storage.append_rows(
            storage.day_path(out, "traffic_sites", fetched_at),
            traffic.SITE_COLUMNS,
            traffic.select(rows, sites),
        )
    return f"traffic: {len(rows)} sites reporting, {kept} configured sites kept"


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
