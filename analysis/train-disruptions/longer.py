"""Are Dutch train disruptions getting longer, or just more frequent?

Uses the same data as profile.py, from 2017 onwards (comparable after the NS
system change). Prints per-year counts, durations and long-tail shares, hours
by cause group, and the longest disruptions in the peak years.

    python analysis/train-disruptions/longer.py
"""

from __future__ import annotations

import importlib.util
import statistics
from collections import defaultdict
from pathlib import Path

# Load profile.py by path: a plain "import profile" would find the stdlib module.
_spec = importlib.util.spec_from_file_location(
    "trains_profile", Path(__file__).parent / "profile.py"
)
_profile = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_profile)
load, minutes, section, table = _profile.load, _profile.minutes, _profile.section, _profile.table

YEARS = range(2017, 2026)
LONG = 4 * 60  # a "long" disruption: four hours or more


def main() -> None:
    data = {year: load(year) for year in YEARS}

    section("Per year: frequency vs duration")
    out = []
    for year, rows in data.items():
        mins = sorted(m for r in rows if (m := minutes(r)) is not None)
        total = sum(mins)
        long_mins = [m for m in mins if m >= LONG]
        q = statistics.quantiles(mins, n=10)
        out.append(
            (
                year,
                len(rows),
                round(total / 60),
                round(statistics.median(mins)),
                round(q[8]),
                len(long_mins),
                f"{sum(long_mins) / total:.0%}",
            )
        )
    table(
        out, ("year", "count", "hours", "median_min", "p90_min", "n_4h_plus", "hours_share_4h_plus")
    )

    section("Hours by cause group per year")
    groups = sorted({r["cause_group"] or "(empty)" for rows in data.values() for r in rows})
    by = {y: defaultdict(float) for y in data}
    for year, rows in data.items():
        for r in rows:
            by[year][r["cause_group"] or "(empty)"] += (minutes(r) or 0) / 60
    table(
        [(g, *(round(by[y][g]) for y in data)) for g in groups],
        ("cause_group", *(str(y) for y in data)),
    )

    section("Median minutes by cause group, 2019 vs 2023 vs 2025")
    out = []
    for g in groups:
        row = [g]
        for y in (2019, 2023, 2025):
            mins = [
                m
                for r in data[y]
                if (r["cause_group"] or "(empty)") == g and (m := minutes(r)) is not None
            ]
            row.append(round(statistics.median(mins)) if mins else "-")
        out.append(tuple(row))
    table(out, ("cause_group", "2019", "2023", "2025"))

    for year in (2022, 2023, 2025):
        section(f"Ten longest disruptions, {year}")
        rows = sorted(data[year], key=lambda r: minutes(r) or 0, reverse=True)[:10]
        table(
            [
                (
                    r["start_time"][:10],
                    round((minutes(r) or 0) / 60),
                    r["cause_en"][:30],
                    (r.get("rdt_lines") or "")[:45],
                )
                for r in rows
            ],
            ("start", "hours", "cause", "line"),
        )


if __name__ == "__main__":
    main()
