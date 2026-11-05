"""Find corporate PACs with a foreign parent and total their giving by country.

The FEC does not flag foreign-connected PACs, so this matches PAC and
connected-organisation names against a hand-made list of foreign parents
(foreign_parents.csv). Every match is written out so it can be checked.

Usage: python analysis/money/foreign_pacs.py RAW_DIR CYCLE OUT_DIR
  RAW_DIR holds fec/cmYY.zip and fec/webkYY.zip from fetch_raw.py.
"""

import csv
import io
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

# Column positions in the FEC bulk files.
CM_ID, CM_NAME, CM_ORG_TYPE, CM_CONNECTED = 0, 1, 12, 13
WK_ID, WK_RECEIPTS, WK_TO_COMMITTEES = 0, 5, 22


def read_bar_file(path: Path):
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        text = io.TextIOWrapper(z.open(name), encoding="latin-1")
        for line in text:
            yield line.rstrip("\n").split("|")


def load_parents():
    rows = list(csv.DictReader((HERE / "foreign_parents.csv").open()))
    for r in rows:
        r["regex"] = re.compile(r["pattern"], re.I)
    return rows


def main(raw: Path, cycle: int, out: Path) -> int:
    yy = f"{cycle % 100:02d}"
    committees = {f[CM_ID]: f for f in read_bar_file(raw / f"fec/cm{yy}.zip")}
    parents = load_parents()
    matches = []
    for f in read_bar_file(raw / f"fec/webk{yy}.zip"):
        cm = committees.get(f[WK_ID])
        if not cm or cm[CM_ORG_TYPE] != "C":  # corporate PACs only
            continue
        text = f"{cm[CM_NAME]} | {cm[CM_CONNECTED]}"
        hits = [p for p in parents if p["regex"].search(text)]
        if not hits:
            continue
        p = hits[0]
        matches.append(
            {
                "cycle": cycle,
                "committee_id": f[WK_ID],
                "committee_name": cm[CM_NAME],
                "connected_org": cm[CM_CONNECTED],
                "parent": p["parent"],
                "country": p["country"],
                "domicile_only": p["note"].startswith("domicile-only"),
                "receipts": float(f[WK_RECEIPTS] or 0),
                "to_committees": float(f[WK_TO_COMMITTEES] or 0),
                "other_matches": "; ".join(h["parent"] for h in hits[1:]),
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    with (out / f"foreign_pacs_{cycle}.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(matches[0]))
        w.writeheader()
        w.writerows(sorted(matches, key=lambda m: -m["to_committees"]))

    by_country = defaultdict(lambda: [0, 0.0])
    for m in matches:
        if m["domicile_only"]:
            continue
        by_country[m["country"]][0] += 1
        by_country[m["country"]][1] += m["to_committees"]
    with (out / f"foreign_pacs_by_country_{cycle}.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cycle", "country", "pacs", "to_committees"])
        for c, (n, amt) in sorted(by_country.items(), key=lambda kv: -kv[1][1]):
            w.writerow([cycle, c, n, round(amt)])
    print(f"{cycle}: {len(matches)} matched PACs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])))
