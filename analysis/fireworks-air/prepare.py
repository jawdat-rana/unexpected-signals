"""Turn the raw New Year's Eve weeks into the story's tables.

    python analysis/fireworks-air/prepare.py RAW_DIR [STORY_DATA_DIR]

RAW_DIR is a checkout of the `raw-fireworks` branch (see fetch_raw.py).

Definitions, per station and per turn of the year (all times UTC; the
Netherlands and Germany are UTC+1 in winter):

- night:     the mean of the hours starting 22:00 to 02:00, i.e. 23:00 to
             04:00 local time, from 31 December to 1 January.
- baseline:  the median of the same five-hour mean on the quiet nights of the
             same week (nights starting 28, 29 December, 1 and 2 January;
             the night of 30 December is left out, people start early).
- excess:    night minus baseline: the fine dust the turn of the year added.
- peak:      the highest single hour from 31 December 18:00 to 1 January 06:00.

A station counts for a year when it has at least 4 of the 5 night hours and
2 quiet nights. Country figures are medians over stations, so one station next
to a big display can't move them.

Wind: the mean hourly wind speed (FF) over all KNMI stations in the same
five night hours. Wind is the main thing besides the amount of fireworks that
decides how high the dust gets.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_OUT = ROOT / "stories" / "first-quiet-new-year" / "data"

NIGHT_HOURS = [22, 23, 0, 1, 2]
QUIET_STARTS = [(12, 28), (12, 29), (1, 1), (1, 2)]
MIN_NIGHT_HOURS = 4
MIN_QUIET_NIGHTS = 2

# Seasons without consumer fireworks on sale in the Netherlands / Germany.
NL_STATUS = {2020: "covid ban", 2021: "covid ban", 2026: "consumer ban"}
DE_STATUS = {2020: "covid ban", 2021: "covid ban"}


def season(year: int) -> str:
    return f"{year}/{str(year + 1)[-2:]}"


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def night_mean(series: dict[dt.datetime, float], start: dt.date) -> float | None:
    """Mean of the five night hours of the night that starts on `start`."""
    values = []
    for hour in NIGHT_HOURS:
        day = start if hour >= 12 else start + dt.timedelta(days=1)
        value = series.get(dt.datetime.combine(day, dt.time(hour)))
        if value is not None:
            values.append(value)
    return statistics.fmean(values) if len(values) >= MIN_NIGHT_HOURS else None


def station_year(series: dict[dt.datetime, float], year: int) -> dict | None:
    nye = dt.date(year, 12, 31)
    night = night_mean(series, nye)
    quiet = []
    for month, day in QUIET_STARTS:
        start = dt.date(year if month == 12 else year + 1, month, day)
        value = night_mean(series, start)
        if value is not None:
            quiet.append(value)
    if night is None or len(quiet) < MIN_QUIET_NIGHTS:
        return None
    lo = dt.datetime(year, 12, 31, 18)
    hi = dt.datetime(year + 1, 1, 1, 6)
    window = [(v, t) for t, v in series.items() if lo <= t <= hi]
    peak, peak_time = max(window)
    baseline = statistics.median(quiet)
    return {
        "night": night,
        "baseline": baseline,
        "excess": night - baseline,
        "ratio": night / baseline if baseline > 0 else None,
        "peak": peak,
        "peak_time": peak_time,
    }


def load_series(path: Path) -> dict[tuple[str, str], dict[dt.datetime, float]]:
    out: dict[tuple[str, str], dict[dt.datetime, float]] = defaultdict(dict)
    for row in read(path):
        try:
            value = float(row["value"])
        except (TypeError, ValueError):
            continue
        if value < 0 or value > 5000:  # negative or impossible readings
            continue
        when = dt.datetime.strptime(row["time_utc"][:19], "%Y-%m-%d %H:%M:%S")
        out[(row["station"], row["formula"])][when] = value
    return out


def wind(raw: Path, year: int) -> float | None:
    by_time = defaultdict(list)
    for row in read(raw / "knmi" / f"{year}.csv"):
        if row["ff"] != "":
            by_time[row["time_utc"][:19]].append(float(row["ff"]))
    nye = dt.date(year, 12, 31)
    means = []
    for hour in NIGHT_HOURS:
        day = nye if hour >= 12 else nye + dt.timedelta(days=1)
        key = dt.datetime.combine(day, dt.time(hour)).strftime("%Y-%m-%d %H:%M:%S")
        if by_time.get(key):
            means.append(statistics.fmean(by_time[key]))
    return round(statistics.fmean(means), 1) if len(means) >= MIN_NIGHT_HOURS else None


def r(value, digits=0):
    return "" if value is None else round(value, digits) if digits else round(value)


def main(raw: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    names = {}
    path = raw / "nl_locations.csv"
    if path.exists():
        lines = [
            line
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if not line.startswith("#")
        ]
        for row in csv.DictReader(lines, delimiter=";"):
            names[row["meetlocatie_id"]] = {
                "name": row["meetlocatie_naam"],
                "municipality": row["meetlocatie_plaatsnaam"],
            }
    names.update(
        {
            s["id"]: {"name": s["name"], "municipality": s["city"]}
            for s in read(raw / "de_stations.csv")
        }
    )

    years = sorted(int(p.stem) for p in (raw / "nl").glob("*.csv"))
    nights, stations, profile = [], [], []
    for year in years:
        w = wind(raw, year)
        for country, folder, status in (("NL", "nl", NL_STATUS), ("DE", "de", DE_STATUS)):
            series = load_series(raw / folder / f"{year}.csv")
            for formula in ("PM25", "PM10"):
                results = []
                for (station, f), values in series.items():
                    if f != formula:
                        continue
                    result = station_year(values, year)
                    if result:
                        results.append((station, result))
                        if country == "NL":
                            meta = names.get(station, {})
                            stations.append(
                                {
                                    "season": season(year),
                                    "formula": formula,
                                    "station": station,
                                    "name": meta.get("name", ""),
                                    "municipality": meta.get("municipality", ""),
                                    "night": r(result["night"]),
                                    "baseline": r(result["baseline"]),
                                    "excess": r(result["excess"]),
                                    "peak": r(result["peak"]),
                                    "peak_time_utc": result["peak_time"].strftime("%Y-%m-%d %H:%M"),
                                }
                            )
                if not results:
                    continue
                top_station, top = max(results, key=lambda s: s[1]["peak"])
                nights.append(
                    {
                        "season": season(year),
                        "year": year,
                        "country": country,
                        "formula": formula,
                        "status": status.get(year, "sold"),
                        "stations": len(results),
                        "median_night": r(statistics.median(s["night"] for _, s in results)),
                        "median_baseline": r(statistics.median(s["baseline"] for _, s in results)),
                        "median_excess": r(statistics.median(s["excess"] for _, s in results)),
                        "median_ratio": r(
                            statistics.median(s["ratio"] for _, s in results if s["ratio"]), 1
                        ),
                        "max_peak": r(top["peak"]),
                        "max_peak_station": names.get(top_station, {}).get("name", top_station),
                        "wind_ms": w if country == "NL" else "",
                    }
                )
                # Hour-by-hour median over stations, 31 Dec 12:00 to 1 Jan 12:00 UTC.
                if country == "NL":
                    for offset in range(-11, 12):
                        t = dt.datetime(year + 1, 1, 1) + dt.timedelta(hours=offset)
                        values = [v[t] for (st, f), v in series.items() if f == formula and t in v]
                        if len(values) >= 5:
                            profile.append(
                                {
                                    "season": season(year),
                                    "formula": formula,
                                    "hour_local": offset + 1,  # hours after midnight, local time
                                    "median": r(statistics.median(values)),
                                    "stations": len(values),
                                }
                            )

    add_wind_model(nights)
    sales = {row["season"]: row for row in read(HERE / "sales.csv")}
    for n in nights:
        n["sales_eur_m"] = sales.get(n["season"], {}).get("sales_eur_m", "")
    write(out / "nights.csv", nights)
    write(out / "profile.csv", profile)
    write(HERE / "stations_by_year.csv", stations)
    print(
        f"{len(nights)} country-years, {len(stations)} station-years, {len(profile)} profile rows"
    )
    for row in nights:
        print(
            f"{row['season']} {row['country']} {row['formula']:5} {row['status']:12} "
            f"n={row['stations']:3} excess={row['median_excess']:>5} x{row['median_ratio']:<4} "
            f"peak={row['max_peak']:>5} ({row['max_peak_station']}) wind={row['wind_ms']}"
        )


def add_wind_model(nights: list[dict]) -> None:
    """Expected excess for the night's wind, fitted on the Dutch years with sales.

    log(excess) = a + b * wind, least squares, per pollutant. `vs_expected` is
    the actual excess divided by the expected one: 1.0 is a normal night for
    that wind, 0.5 half the dust you'd expect.
    """
    for formula in ("PM25", "PM10"):
        rows = [n for n in nights if n["country"] == "NL" and n["formula"] == formula]
        fit = [
            n
            for n in rows
            if n["status"] == "sold" and n["wind_ms"] != "" and n["median_excess"] > 0
        ]
        xs = [n["wind_ms"] for n in fit]
        ys = [math.log(n["median_excess"]) for n in fit]
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
        b = sxy / sum((x - mx) ** 2 for x in xs)
        a = my - b * mx
        residuals = [y - (a + b * x) for x, y in zip(xs, ys, strict=True)]
        r2 = 1 - sum(e * e for e in residuals) / sum((y - my) ** 2 for y in ys)
        print(
            f"wind model {formula}: excess x{math.exp(b):.2f} per extra m/s, R2 {r2:.2f}, "
            f"residual sd {statistics.stdev(residuals):.2f} (log), fitted on {len(fit)} years"
        )
        for n in rows:
            if n["wind_ms"] == "":
                continue
            expected = math.exp(a + b * n["wind_ms"])
            n["expected_excess"] = round(expected)
            n["vs_expected"] = round(n["median_excess"] / expected, 2)
    for n in nights:
        n.setdefault("expected_excess", "")
        n.setdefault("vs_expected", "")


def write(path: Path, rows: list[dict]) -> None:
    if not rows:
        print(f"nothing to write for {path}", file=sys.stderr)
        return
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT)
