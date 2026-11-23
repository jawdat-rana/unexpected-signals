"""Write the chart data for "Who owns the Netherlands' homes".

Reads the CBS tables that fetch_raw.py saved (the `raw-housing` branch) and
writes small CSVs into stories/who-owns-the-netherlands/data/.

    git worktree add raw-housing origin/raw-housing   # or any copy of that branch
    python analysis/who-owns-homes/prepare.py raw-housing

Standard library only. Every number in the story comes from this script.
"""

from __future__ import annotations

import csv
import gzip
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "stories" / "who-owns-the-netherlands" / "data"

TOTAL = "T001059"  # nationality: total
INDIAN = "NAT9348"
KNOWLEDGE = "A049128"  # migration motive: labour, knowledge migrant
WITH_LABOUR = "A052714"  # family who came with a labour migrant
ALL_MOTIVES = "T001056"
LEFT = "2017578"  # socio-economic category: no longer in the Netherlands
ALL_CATEGORIES = "T001083"


def rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle, delimiter=";")


def number(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def titles(path: Path) -> dict[str, str]:
    return {r["Identifier"]: r["Title"].strip() for r in rows(path)}


def year(period: str) -> int:
    return int(period[:4])


def write(name: str, data: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
    print(f"wrote {len(data)} rows to {name}", file=sys.stderr)


def tenure(raw: Path) -> dict[tuple[str, int], dict[str, float]]:
    """Dwellings on 1 January by owner type, per region and year (82900NED)."""
    names = {
        "T001258": "total",
        "A028868": "owner",
        "A047047": "corporation",
        "A047048": "landlord",
    }
    out: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    for r in rows(raw / "82900NED" / "Observations.csv.gz"):
        if r["StatusVanBewoning"] != "T001235" or r["Measure"] not in names:
            continue
        value = number(r["Value"])
        if value is not None:
            out[(r["RegioS"], year(r["Perioden"]))][names[r["Measure"]]] = value
    return out


def province_of(raw: Path) -> dict[str, str]:
    """Municipality code -> province name, from the 82900NED region hierarchy."""
    groups = {r["Id"]: r for r in rows(raw / "82900NED" / "RegioSGroups.csv")}
    names = titles(raw / "82900NED" / "RegioSCodes.csv")
    out = {}
    for r in rows(raw / "82900NED" / "RegioSCodes.csv"):
        group = groups.get(r.get("DimensionGroupId") or "")
        title = (group or {}).get("Title", "")
        if r["Identifier"].startswith("GM") and title:
            out[r["Identifier"]] = title.replace(" (PV)", "")
    return out or {k: "" for k in names}


def wealth_vs_owning(raw: Path, dwellings: dict) -> None:
    """Share of households that own their home, and share with EUR 1M+ wealth.

    Both from the same CBS wealth table (86379NED, regional classification
    2026), so numerator and denominator are the same households. CBS counts
    the home's value minus the mortgage as wealth.
    """
    table = raw / "86379NED"
    names = titles(table / "RegioSCodes.csv")
    want = {"1014800": "own_pct", "1021390": "millionaire_pct"}
    latest = max(year(r["Identifier"]) for r in rows(table / "PeriodenCodes.csv"))
    values: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows(table / "Observations.csv.gz"):
        if r["Measure"] != "M10662" or r["KenmerkenVanHuishoudens"] not in want:
            continue
        if year(r["Perioden"]) != latest:
            continue
        value = number(r["Value"])
        if value is not None:
            values[r["RegioS"]][want[r["KenmerkenVanHuishoudens"]]] = value
    provinces = province_of(raw)
    municipalities, regions = [], []
    for code, v in sorted(values.items()):
        if len(v) < 2:
            continue
        row = {
            "code": code,
            "name": names.get(code, code).replace(" (gemeente)", "").replace(" (PV)", ""),
            "own_pct": v["own_pct"],
            "millionaire_pct": v["millionaire_pct"],
            "dwellings": int(dwellings.get((code, latest), {}).get("total", 0)),
        }
        if code.startswith("GM"):
            row["province"] = provinces.get(code, "")
            municipalities.append(row)
        elif code.startswith(("PV", "NL")):
            regions.append(row)
    for row in municipalities + regions:
        row["year"] = latest
    for row in municipalities:
        row["level"] = "municipality"
    for row in regions:
        row["level"] = "country" if row["code"] == "NL01" else "province"
        row["province"] = row["name"]
    write("wealth_vs_owning.csv", municipalities + regions)
    print(
        f"  rank correlation, {len(municipalities)} municipalities: "
        f"{rank_correlation(municipalities):.2f}",
        file=sys.stderr,
    )
    print(
        f"  rank correlation, provinces: "
        f"{rank_correlation([r for r in regions if r['code'].startswith('PV')]):.2f}",
        file=sys.stderr,
    )


def rank_correlation(data: list[dict]) -> float:
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2
            i = j + 1
        return out

    a = ranks([d["own_pct"] for d in data])
    b = ranks([d["millionaire_pct"] for d in data])
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((y - mb) ** 2 for y in b) ** 0.5
    return cov / (va * vb)


def tenure_national(dwellings: dict) -> None:
    data = []
    for (code, y), v in sorted(dwellings.items()):
        if code == "NL01":
            data.append(
                {"year": y, **{k: int(v[k]) for k in ("total", "owner", "corporation", "landlord")}}
            )
    write("tenure_national.csv", data)


def knowledge_migrants(raw: Path, dwellings: dict) -> None:
    """Arrivals per year, and the share of each arrival year gone after N years (84809NED)."""
    table = raw / "84809NED"
    duration = {
        r["Identifier"]: int(r["Title"].split()[0]) for r in rows(table / "VerblijfsduurCodes.csv")
    }
    arrivals: dict[tuple[str, int], float] = {}
    gone: dict[tuple[str, int, int], float] = {}
    for r in rows(table / "Observations.csv.gz"):
        if r["Nationaliteit"] != TOTAL or r["Migratiemotief"] not in (
            KNOWLEDGE,
            WITH_LABOUR,
            ALL_MOTIVES,
        ):
            continue
        value = number(r["Value"])
        if value is None:
            continue
        key = (r["Migratiemotief"], year(r["JaarVanImmigratie"]))
        d = duration[r["Verblijfsduur"]]
        if r["SociaaleconomischeCategorie"] == ALL_CATEGORIES and d == 1:
            arrivals[key] = value
        elif r["SociaaleconomischeCategorie"] == LEFT:
            gone[(*key, d)] = value

    def still_here(motive: str, y: int) -> float:
        durations = [d for (m, yy, d) in gone if m == motive and yy == y]
        left = gone[(motive, y, max(durations))] if durations else 0
        return arrivals[(motive, y)] - left

    years = sorted({y for (m, y) in arrivals if m == KNOWLEDGE})
    data = []
    for y in years:
        added = dwellings.get(("NL01", y + 1), {}).get("total", 0) - dwellings.get(
            ("NL01", y), {}
        ).get("total", 0)
        row = {
            "year": y,
            "knowledge_migrants": int(arrivals[(KNOWLEDGE, y)]),
            "family_with_labour_migrants": int(arrivals.get((WITH_LABOUR, y), 0)),
            "all_non_eu_immigrants": int(arrivals.get((ALL_MOTIVES, y), 0)),
            "homes_added": int(added)
            if dwellings.get(("NL01", y + 1)) and dwellings.get(("NL01", y))
            else "",
            "knowledge_left_within_5y_pct": "",
            "knowledge_still_here": int(still_here(KNOWLEDGE, y)),
        }
        if (KNOWLEDGE, y, 5) in gone:
            row["knowledge_left_within_5y_pct"] = round(
                100 * gone[(KNOWLEDGE, y, 5)] / arrivals[(KNOWLEDGE, y)], 1
            )
        data.append(row)
    write("knowledge_migrants.csv", data)
    here = sum(r["knowledge_still_here"] for r in data)
    family = sum(still_here(WITH_LABOUR, y) for y in years if (WITH_LABOUR, y) in arrivals)
    print(
        f"  knowledge migrants still here: {here:,.0f}; "
        f"family who came with labour migrants: {family:,.0f}",
        file=sys.stderr,
    )


def where_indian_arrivals_settle(
    raw: Path, dwellings: dict, first: int = 2023, last: int = 2025
) -> None:
    """Immigration of Indian nationals per municipality (85451NED).

    A proxy for knowledge migrants.

    Indian nationals are the largest single group of knowledge migrants, but
    not all of them are knowledge migrants (students and family come too).
    """
    table = raw / "85451NED"
    names = titles(table / "RegioSCodes.csv")
    totals: dict[tuple[str, str], float] = defaultdict(float)
    for r in rows(table / "Observations.csv.gz"):
        if r["Measure"] != "M000167" or r["Nationaliteit"] not in (INDIAN, TOTAL):
            continue
        if not first <= year(r["Perioden"]) <= last:
            continue
        value = number(r["Value"])
        if value is not None:
            totals[(r["RegioS"], r["Nationaliteit"])] += value
    national = totals[("NL01", INDIAN)]
    data = []
    for (code, nat), value in totals.items():
        if nat != INDIAN or not code.startswith("GM"):
            continue
        stock = dwellings.get((code, last), {})
        if not stock.get("total"):
            continue
        data.append(
            {
                "code": code,
                "name": names.get(code, code).replace(" (gemeente)", ""),
                "indian_arrivals": int(value),
                "all_arrivals": int(totals[(code, TOTAL)]),
                "share_of_national_pct": round(100 * value / national, 1),
                "per_1000_homes": round(1000 * value / stock["total"], 1),
                "owner_pct": round(100 * stock["owner"] / stock["total"], 1),
                "corporation_pct": round(100 * stock["corporation"] / stock["total"], 1),
                "landlord_pct": round(100 * stock["landlord"] / stock["total"], 1),
                "period": f"{first}-{last}",
            }
        )
    data.sort(key=lambda r: -r["indian_arrivals"])
    write("indian_arrivals_by_municipality.csv", data)
    top5 = sum(r["indian_arrivals"] for r in data[:5]) / national
    print(
        f"  Indian arrivals {first}-{last}: {national:,.0f}; top 5 municipalities: {top5:.0%}",
        file=sys.stderr,
    )


def main(raw: Path) -> int:
    dwellings = tenure(raw)
    tenure_national(dwellings)
    wealth_vs_owning(raw, dwellings)
    knowledge_migrants(raw, dwellings)
    where_indian_arrivals_settle(raw, dwellings)
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "raw"))
    )
