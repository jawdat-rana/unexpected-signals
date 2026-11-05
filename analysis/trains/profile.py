"""First-pass profile of the Rijden de Treinen disruptions dataset.

Downloads the yearly CSVs (CC BY 4.0, https://www.rijdendetreinen.nl/en/open-data/disruptions)
and prints a plain-text profile: volume per year, field completeness, causes,
timing, lines and durations. Standard library only.

    python analysis/trains/profile.py            # all years
    python analysis/trains/profile.py 2023 2024  # selected years
"""

from __future__ import annotations

import csv
import io
import statistics
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

URL = "https://opendata.rijdendetreinen.nl/public/disruptions/disruptions-{year}.csv"
CACHE = Path(__file__).parent / "raw"
YEARS = range(2011, 2026)
# NS changed its disruption system in 2017, so timing comparisons use 2017 onwards.
COMPARABLE_FROM = 2017


def load(year: int) -> list[dict[str, str]]:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"disruptions-{year}.csv"
    if not path.exists():
        request = urllib.request.Request(
            URL.format(year=year), headers={"User-Agent": "unexpected-signals"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def minutes(row: dict[str, str]) -> float | None:
    try:
        return float(row.get("duration_minutes") or "")
    except ValueError:
        return None


def section(title: str) -> None:
    print(f"\n## {title}\n")


def table(rows: list[tuple], headers: tuple[str, ...]) -> None:
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows, strict=True)]
    line = lambda r: "  ".join(str(v).ljust(w) for v, w in zip(r, widths, strict=True))  # noqa: E731
    print(line(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(line(r))


def main(argv: list[str]) -> None:
    years = [int(y) for y in argv] or list(YEARS)
    data: dict[int, list[dict[str, str]]] = {}
    for year in years:
        try:
            data[year] = load(year)
        except Exception as exc:
            print(f"! {year}: could not load ({exc!r})")
    rows = [r for y in data for r in data[y]]
    if not rows:
        raise SystemExit("No data loaded")

    section("Columns and completeness")
    columns = list(rows[0].keys())
    table(
        [
            (c, f"{sum(1 for r in rows if (r.get(c) or '').strip()) / len(rows):.0%}")
            for c in columns
        ],
        ("column", "filled"),
    )

    section("Volume per year")
    out = []
    for year, yr in data.items():
        mins = [m for r in yr if (m := minutes(r)) is not None]
        out.append(
            (year, len(yr), round(sum(mins) / 60), round(statistics.median(mins)) if mins else "-")
        )
    table(out, ("year", "disruptions", "total_hours", "median_min"))

    for field in ("cause_group", "statistical_cause_en", "cause_en"):
        if field not in columns:
            continue
        section(f"Top causes by `{field}` (all years)")
        counts = Counter(r[field] or "(empty)" for r in rows)
        total_min: dict[str, float] = defaultdict(float)
        for r in rows:
            total_min[r[field] or "(empty)"] += minutes(r) or 0
        table(
            [
                (k[:45], n, f"{n / len(rows):.1%}", round(total_min[k] / 60))
                for k, n in counts.most_common(15)
            ],
            ("cause", "count", "share", "hours"),
        )

    recent = [r for y in data if y >= COMPARABLE_FROM for r in data[y]]
    starts = [(r, t) for r in recent if (t := parse_time(r.get("start_time", "")))]
    if starts:
        section(f"By month, {COMPARABLE_FROM} onwards")
        by_month: dict[int, list[float]] = defaultdict(list)
        for r, t in starts:
            by_month[t.month].append(minutes(r) or 0)
        table(
            [(m, len(v), round(sum(v) / 60)) for m, v in sorted(by_month.items())],
            ("month", "disruptions", "hours"),
        )

        section(f"By start hour, {COMPARABLE_FROM} onwards")
        by_hour = Counter(t.hour for _, t in starts)
        table([(h, by_hour[h]) for h in range(24)], ("hour", "disruptions"))

        section(f"By weekday, {COMPARABLE_FROM} onwards")
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        by_day = Counter(t.weekday() for _, t in starts)
        table([(names[d], by_day[d]) for d in range(7)], ("weekday", "disruptions"))

    line_field = "rdt_lines" if "rdt_lines" in columns else None
    if line_field:
        section(f"Top 15 lines, {COMPARABLE_FROM} onwards")
        counts = Counter(r[line_field] for r in recent if r.get(line_field))
        table([(k[:60], n) for k, n in counts.most_common(15)], ("line", "disruptions"))

    mins = sorted(m for r in rows if (m := minutes(r)) is not None)
    if mins:
        section("Duration distribution (minutes, all years)")
        q = statistics.quantiles(mins, n=20)
        table(
            [
                ("p10", round(q[1])),
                ("p25", round(q[4])),
                ("median", round(q[9])),
                ("p75", round(q[14])),
                ("p90", round(q[17])),
                ("p95", round(q[18])),
                ("max", round(mins[-1])),
            ],
            ("percentile", "minutes"),
        )

    section("Sample rows")
    for r in rows[:2] + rows[-2:]:
        print({k: (v[:60] if v else v) for k, v in r.items()})


if __name__ == "__main__":
    main(sys.argv[1:])
