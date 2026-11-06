"""Write the chart data for the "Two doors into Washington" story.

Joins the PAC matches and the FARA client counts into two small CSVs in
stories/two-doors-into-washington/data/, which the page's charts read.

Usage: python analysis/money-in-politics/story_data.py PACS_CSV FARA_CSV
  PACS_CSV is foreign_pacs_YYYY.csv from foreign_pacs.py,
  FARA_CSV is the output of fara_clients.py.
"""

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "stories" / "two-doors-into-washington" / "data"

# FARA spells some countries differently from the parent-company list.
FARA_NAMES = {"South Korea": "Korea, South"}
# Countries with this many FARA clients are shown even without PAC money.
FARA_MIN = 20


def door(fara: int, pac_dollars: float) -> str:
    """Which door a country mostly uses. Thresholds are a judgment call, stated in the story."""
    if pac_dollars >= 1.5e6 and fara >= 14:
        return "Both doors"
    if pac_dollars >= 0.3e6 and fara <= 10:
        return "Mostly companies"
    if pac_dollars < 0.25e6 and fara >= FARA_MIN:
        return "Mostly hired agents"
    return "Neither stands out"


def write(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {name}", file=sys.stderr)


def main(pacs_csv: Path, fara_csv: Path) -> int:
    dollars: Counter[str] = Counter()
    pacs: Counter[str] = Counter()
    parents: dict[str, Counter[str]] = defaultdict(Counter)
    for r in csv.DictReader(pacs_csv.open(encoding="utf-8")):
        if r["domicile_only"] == "True":
            continue
        amount = float(r["to_committees"] or 0)
        dollars[r["country"]] += amount
        pacs[r["country"]] += 1
        parents[r["country"]][r["parent"]] += amount
    fara = {r["country"]: int(r["fara_clients"]) for r in csv.DictReader(fara_csv.open())}

    def top(country: str) -> str:
        return "; ".join(p for p, v in parents[country].most_common(3) if v > 0)

    by_country = [
        {"country": c, "pac_dollars": round(v), "pacs": pacs[c], "top_parents": top(c)}
        for c, v in dollars.most_common()
        if v > 0
    ]
    write("pac_money_by_country_2024.csv", by_country)

    skip = {"International", *FARA_NAMES.values()}
    names = set(dollars) | {c for c, n in fara.items() if n >= FARA_MIN and c not in skip}
    scatter = []
    for c in names:
        clients = fara.get(FARA_NAMES.get(c, c), 0)
        scatter.append(
            {
                "country": c,
                "pac_dollars": round(dollars[c]),
                "fara_clients": clients,
                "door": door(clients, dollars[c]),
                "top_parents": top(c),
            }
        )
    scatter.sort(key=lambda r: (-r["pac_dollars"], -r["fara_clients"]))
    write("two_doors_2024.csv", scatter)
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
