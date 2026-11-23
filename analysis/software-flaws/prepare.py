"""Turn the raw flaw data into the small CSVs the "Black October" story reads.

Reads analysis/software-flaws/raw/ (cves.csv, kev.csv, msrc.csv, ncsc_nl.csv,
from the `raw-flaws` branch) and writes chart-ready CSVs to
stories/black-october/data/.

    git fetch origin raw-flaws
    mkdir -p analysis/software-flaws/raw
    for f in cves kev msrc ncsc_nl manifest; do
      git show FETCH_HEAD:$f.csv > analysis/software-flaws/raw/$f.csv
    done
    python analysis/software-flaws/prepare.py

Definitions
- "Found": a CVE record published in the CVE List that month (state PUBLISHED).
- "Exploited": added to CISA's Known Exploited Vulnerabilities (KEV) catalogue
  that month. KEV is a floor: it lists flaws with reliable evidence of attacks
  and a fix or mitigation, not every attack.
- "Credited to AI": the CVE record's credits name an AI system or an AI
  security research team (see AI_CREDIT below). A floor too: most records
  don't say how a flaw was found.
- Microsoft: CVEs assigned by Microsoft as a CVE Numbering Authority. Its
  monthly update guides also list Chromium and open-source flaws it ships,
  which the press figure of "1,400" leaves out, and so do we.
"""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw"
OUT = HERE.parent.parent / "stories" / "black-october" / "data"

START = "2019-01"  # monthly charts start here
LAST_FULL = "2026-10"  # last complete month in the data (fetched 23 Nov 2026)

# Terms from fetch_raw.AI_TERMS that, in credits, reliably mean an AI system or
# AI security team. "artificial intelligence" matched a company name; dropped.
AI_CREDIT = {
    "claude",
    "anthropic",
    "openai",
    "aisle",
    "big sleep",
    "naptime",
    "xbow",
    "depthfirst",
    "zeropath",
    "codemender",
    "aardvark",
    "ai agent",
    "llm",
    "large language model",
    "ai-assisted",
    "ai assisted",
    "atlantis",
    "buttercup",
    "cyber reasoning system",
    "gpt-5",
    "gpt-6",
}


def read(name: str) -> list[dict]:
    with (RAW / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {(OUT / name).relative_to(HERE.parent.parent)}")


def months(start: str, end: str) -> list[str]:
    y, m = map(int, start.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= end:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main() -> None:
    cves = read("cves.csv")
    kev = read("kev.csv")
    ncsc = read("ncsc_nl.csv")
    span = months(START, LAST_FULL)

    published = Counter(r["published"][:7] for r in cves)
    critical = Counter(r["published"][:7] for r in cves if r["score"] and float(r["score"]) >= 9)
    microsoft = Counter(r["published"][:7] for r in cves if r["assigner"] == "microsoft")
    ai = Counter(
        r["published"][:7] for r in cves if r["ai_in"] == "credits" and r["ai_term"] in AI_CREDIT
    )
    exploited = Counter(r["dateAdded"][:7] for r in kev)
    advisories = Counter(r["released"][:7] for r in ncsc)
    # Microsoft's own flag for "exploited when the fix came out", Microsoft-assigned CVEs only.
    ms_assigned = {r["cve"] for r in cves if r["assigner"] == "microsoft"}
    ms_exploited = Counter()
    seen = set()
    for r in read("msrc.csv"):
        if r["exploited"] == "Yes" and r["cve"] in ms_assigned and r["cve"] not in seen:
            seen.add(r["cve"])
            ms_exploited[r["release"][:7]] += 1

    rows = [
        {
            "month": m,
            "cves": published[m],
            "critical": critical[m],
            "microsoft": microsoft[m],
            "microsoft_exploited": ms_exploited[m],
            "ai_credited": ai[m],
            "kev_added": exploited[m],
            "ncsc_nl": advisories[m] if m >= "2024-06" else "",
        }
        for m in span
    ]
    write_csv("monthly.csv", rows)

    # Found vs exploited, indexed to the 2025 monthly average = 100.
    base = [m for m in span if m.startswith("2025")]
    avg_c = statistics.mean(published[m] for m in base)
    avg_k = statistics.mean(exploited[m] for m in base)
    idx = []
    for m in months("2024-01", LAST_FULL):
        idx.append(
            {
                "month": m,
                "series": "Flaws published",
                "index": round(published[m] / avg_c * 100, 1),
                "count": published[m],
            }
        )
        idx.append(
            {
                "month": m,
                "series": "Flaws exploited",
                "index": round(exploited[m] / avg_k * 100, 1),
                "count": exploited[m],
            }
        )
    write_csv("found_vs_exploited.csv", idx)

    # How fast a flaw lands in KEV after its CVE is published, per year added.
    pub = {r["cve"]: r["published"] for r in cves}
    lag_rows = []
    by_year: dict[str, list[int]] = defaultdict(list)
    for k in kev:
        p = pub.get(k["cveID"])
        if not p:
            continue
        by_year[k["dateAdded"][:4]].append(
            (date.fromisoformat(k["dateAdded"]) - date.fromisoformat(p)).days
        )
    for year in sorted(by_year):
        if year < "2023":
            continue  # 2021-22: CISA was loading years of older, known flaws
        lags = by_year[year]
        lag_rows.append(
            {
                "year": year,
                "added": len(lags),
                "median_days": statistics.median(lags),
                "within_7_days": sum(x <= 7 for x in lags),
                "within_30_days": sum(x <= 30 for x in lags),
                "share_within_30_days": round(sum(x <= 30 for x in lags) / len(lags) * 100),
            }
        )
    write_csv("exploit_speed.csv", lag_rows)

    # Who published the extra flaws: top assigners, October 2025 vs October 2026.
    a25 = Counter(r["assigner"] for r in cves if r["published"].startswith("2025-10"))
    a26 = Counter(r["assigner"] for r in cves if r["published"].startswith("2026-10"))
    top = [a for a, _ in a26.most_common(12)]
    write_csv(
        "assigners_october.csv",
        [{"assigner": a, "oct_2025": a25[a], "oct_2026": a26[a]} for a in top],
    )

    o25, o26 = published["2025-10"], published["2026-10"]
    print(f"Oct 2025 {o25} -> Oct 2026 {o26} CVEs ({o26 / o25:.1f}x)")
    print(f"KEV Oct 2025 {exploited['2025-10']} -> Oct 2026 {exploited['2026-10']}")
    print(f"Microsoft Oct 2025 {microsoft['2025-10']} -> Oct 2026 {microsoft['2026-10']}")
    print(
        "Microsoft exploited-at-release Jan-Oct 2025 "
        f"{sum(ms_exploited[m] for m in months('2025-01', '2025-10'))} -> 2026 "
        f"{sum(ms_exploited[m] for m in months('2026-01', '2026-10'))}"
    )
    print(f"AI-credited Oct 2025 {ai['2025-10']} -> Oct 2026 {ai['2026-10']}")
    ytd25 = sum(published[m] for m in months("2025-01", "2025-10"))
    ytd26 = sum(published[m] for m in months("2026-01", "2026-10"))
    k25 = sum(exploited[m] for m in months("2025-01", "2025-10"))
    k26 = sum(exploited[m] for m in months("2026-01", "2026-10"))
    print(f"Jan-Oct CVEs {ytd25} -> {ytd26}; KEV {k25} -> {k26}")
    print(f"KEV per 1,000 new CVEs: {k25 / ytd25 * 1000:.1f} -> {k26 / ytd26 * 1000:.1f}")


if __name__ == "__main__":
    main()
