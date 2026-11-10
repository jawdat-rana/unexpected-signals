"""Write the chart data for "The home front" story.

Reads the output of home_front.py and writes small CSVs into
stories/the-home-front/data/, which the page's charts read.

Usage: python analysis/money-in-politics/home_front_story.py HOME_FRONT_OUT
  HOME_FRONT_OUT is the OUT_DIR given to home_front.py.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "stories" / "the-home-front" / "data"
FOCUS = "Pro-Israel"
OTHERS = "All other groups"
TABLE_CYCLES = (2024, 2026)


def write(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {name}", file=sys.stderr)


def main(src: Path) -> int:
    groups = list(csv.DictReader((src / "home_front_by_group.csv").open()))
    series = defaultdict(lambda: {"total": 0, "primary": 0})
    for r in groups:
        key = (int(r["cycle"]), FOCUS if r["group"] == FOCUS else OTHERS)
        series[key]["total"] += int(r["total"])
        series[key]["primary"] += int(r["primary"])
    write(
        "home_front_by_cycle.csv",
        [
            {"cycle": c, "series": s, "total": v["total"], "primary": v["primary"]}
            for (c, s), v in sorted(series.items())
        ],
    )

    # One row per group, with the two latest cycles side by side.
    table = defaultdict(dict)
    for r in groups:
        c = int(r["cycle"])
        if c in TABLE_CYCLES:
            table[r["group"]][f"total_{c}"] = int(r["total"])
            table[r["group"]][f"primary_{c}"] = int(r["primary"])
            table[r["group"]][f"committees_{c}"] = int(r["committees"])
    cols = [f"{k}_{c}" for c in TABLE_CYCLES for k in ("total", "primary", "committees")]
    rows = [{"group": g, **{k: v.get(k, 0) for k in cols}} for g, v in table.items()]
    rows.sort(key=lambda r: -r["total_2024"])
    write("home_front_groups.csv", rows)

    committees = list(csv.DictReader((src / "home_front_committees_by_cycle.csv").open()))
    write("home_front_committees.csv", committees)
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
