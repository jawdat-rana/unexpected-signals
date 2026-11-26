"""Turn KNMI daily temperatures into the tables for "The ice we lost".

Uses two KNMI definitions, nothing home-made:

- Hellmann cold sum (koudegetal): from 1 November to 31 March, add up the daily
  mean temperatures below zero, without the minus sign. The winter is named
  after the year it ends in (1963 = Nov 1962 to Mar 1963). Above 100 KNMI calls
  a winter cold, above 160 very cold, above 300 severe.
- Potential Elfstedentocht: the coldest 15-day stretch of the winter has a mean
  daily temperature below -4.2 C (van Oldenborgh, Visser, Brandsma and de Vries,
  KNMI 2019). Cold enough for ice thick enough for the whole route.

Plus ice days (daily maximum below zero), the standard KNMI count.

And how cold November has been so far: the mean daily temperature in De Bilt
from 1 November to the last day KNMI has published for the latest November,
for every year, next to the Hellmann sum of the winter that followed.

    python analysis/natural-ice/prepare.py RAW_DIR

RAW_DIR is a checkout of the `raw-ice` branch (see fetch_raw.py).
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

STORY = Path(__file__).resolve().parents[2] / "stories" / "the-ice-we-lost" / "data"
DE_BILT = 260
EARLY = range(1951, 1989)  # winters 1951 to 1988
LATE = range(1989, 2027)  # winters 1989 to 2026, the same 38 winters
COLD = 100  # KNMI: Hellmann above 100 is a cold winter
POTENTIAL = -4.2  # KNMI 2019: coldest 15-day mean below this
MIN_DAYS = 145  # of 151 (152 in leap years) Nov-Mar days
MIN_WINTERS = 25  # per period, for a station to be on the map
# Elfstedentochten held, by winter (KNMI, Koninklijke Vereniging De Friesche Elf Steden)
HELD = {1909, 1912, 1917, 1929, 1933, 1940, 1941, 1942, 1947, 1954, 1956, 1963, 1985, 1986, 1997}


def winter_of(day: date) -> int | None:
    if day.month >= 11:
        return day.year + 1
    if day.month <= 3:
        return day.year
    return None


def load(path: Path) -> dict[int, list[tuple[date, float, float | None]]]:
    winters = defaultdict(list)
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            if not row["tg"]:
                continue
            day = date.fromisoformat(row["date"])
            winter = winter_of(day)
            if winter is not None:
                winters[winter].append(
                    (day, float(row["tg"]), float(row["tx"]) if row["tx"] else None)
                )
    return winters


def measure(days: list[tuple[date, float, float | None]]) -> dict | None:
    if len(days) < MIN_DAYS:
        return None
    days.sort()
    by_day = {d: tg for d, tg, _ in days}
    coldest = None
    for d, _, _ in days:
        window = [by_day.get(d + timedelta(i)) for i in range(15)]
        if None in window:
            continue
        mean = sum(window) / 15
        coldest = mean if coldest is None else min(coldest, mean)
    return {
        "hellmann": round(sum(-tg for _, tg, _ in days if tg < 0), 1),
        "tg15n": None if coldest is None else round(coldest, 2),
        "ice_days": sum(1 for _, _, tx in days if tx is not None and tx < 0),
    }


def share(values: list[bool]) -> float:
    return round(100 * sum(values) / len(values), 1)


def main(raw: Path) -> None:
    STORY.mkdir(parents=True, exist_ok=True)
    stations = {int(r["stn"]): r for r in csv.DictReader(open(raw / "stations.csv"))}
    results = {}
    for stn in stations:
        path = raw / "daily" / f"{stn}.csv"
        if path.exists():
            results[stn] = {w: m for w, d in load(path).items() if (m := measure(d))}

    # De Bilt, every winter since 1902
    bilt = results[DE_BILT]
    rows = []
    for winter in sorted(bilt):
        m = bilt[winter]
        rows.append(
            {
                "winter": winter,
                "hellmann": m["hellmann"],
                "tg15n": m["tg15n"],
                "ice_days": m["ice_days"],
                "potential": int(m["tg15n"] is not None and m["tg15n"] < POTENTIAL),
                "held": int(winter in HELD),
            }
        )
    write(STORY / "debilt_winters.csv", rows)

    # De Bilt per 25-year block
    blocks = []
    for start in range(1902, 2027, 25):
        block = [r for r in rows if start <= r["winter"] < start + 25]
        if not block:
            continue
        blocks.append(
            {
                "period": f"{start}-{block[-1]['winter']}",
                "winters": len(block),
                "avg_hellmann": round(sum(r["hellmann"] for r in block) / len(block), 1),
                "cold_winters": sum(r["hellmann"] > COLD for r in block),
                "potential": sum(r["potential"] for r in block),
                "held": sum(r["held"] for r in block),
            }
        )
    write(STORY / "debilt_periods.csv", blocks)

    # November so far in De Bilt, every year, with the winter that followed
    novembers = november_to_date(raw / "daily" / f"{DE_BILT}.csv")
    last = max(novembers)
    days = novembers[last][1]
    write(
        STORY / "debilt_november.csv",
        [
            {
                "year": year,
                "days": days,
                "mean": round(mean, 2),
                "winter_hellmann": bilt[year + 1]["hellmann"] if year + 1 in bilt else "",
            }
            for year, (mean, n) in sorted(novembers.items())
            if n == days
        ],
    )

    # Every station with enough winters in both periods
    table = []
    for stn, winters in results.items():
        early = [winters[w] for w in EARLY if w in winters]
        late = [winters[w] for w in LATE if w in winters]
        if len(early) < MIN_WINTERS or len(late) < MIN_WINTERS:
            continue
        s = stations[stn]
        table.append(
            {
                "stn": stn,
                "name": s["name"].title(),
                "lon": s["lon"],
                "lat": s["lat"],
                "winters_early": len(early),
                "winters_late": len(late),
                "cold_early": share([m["hellmann"] > COLD for m in early]),
                "cold_late": share([m["hellmann"] > COLD for m in late]),
                "potential_early": share(
                    [m["tg15n"] is not None and m["tg15n"] < POTENTIAL for m in early]
                ),
                "potential_late": share(
                    [m["tg15n"] is not None and m["tg15n"] < POTENTIAL for m in late]
                ),
                "ice_days_early": round(sum(m["ice_days"] for m in early) / len(early), 1),
                "ice_days_late": round(sum(m["ice_days"] for m in late) / len(late), 1),
            }
        )
    table.sort(key=lambda r: -float(r["lat"]))
    write(STORY / "stations.csv", table)

    # Check against KNMI's published list for De Bilt
    for winter, knmi in [(1947, 342.5), (1963, 337.2)]:
        print(f"De Bilt {winter}: ours {bilt[winter]['hellmann']}, KNMI {knmi}")
    print(f"{len(rows)} De Bilt winters, {len(table)} stations on the map")
    colder = sorted(y for y, (m, n) in novembers.items() if n == days and m < novembers[last][0])
    print(
        f"November {last}, 1-{days}: {novembers[last][0]:.2f} C, "
        f"{len(colder)} colder years, the latest {colder[-3:]}"
    )


def november_to_date(path: Path) -> dict[int, tuple[float, int]]:
    """Mean daily temperature from 1 November up to the day the latest November
    has reached, per year, with the number of days used."""
    temps = defaultdict(dict)
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            if row["tg"] and row["date"][5:7] == "11":
                temps[int(row["date"][:4])][int(row["date"][8:])] = float(row["tg"])
    reached = max(temps[max(temps)])
    result = {}
    for year, days in temps.items():
        values = [days[d] for d in range(1, reached + 1) if d in days]
        result[year] = (sum(values) / len(values), len(values))
    return result


def write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.name}: {len(rows)} rows")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "raw"))
