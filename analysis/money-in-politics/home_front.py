"""Total the money spent through home-front PACs, per group and cycle.

"Home front" PACs are U.S. committees, funded by American donors, whose name
or stated purpose is about a foreign country, a diaspora community or (as
their own group) a faith community. The hand-checked list is
home_front_committees.csv; every committee in it is treated the same way.

Totals come from what each committee reports on its summary pages (the FEC
PAC summary file, webk), so small unitemized amounts are included:

- given: contributions to candidates and other committees (webk column
  CONTRIB_TO_OTHER_CMTE). For conduit PACs like AIPAC PAC, JStreetPAC and
  NORPAC most of this is donations earmarked by individual donors for a
  named candidate and passed on by the PAC.
- independent: independent expenditures for or against candidates (webk
  IND_EXP). Groups that file Form 5 instead (ids starting C9) are not in
  webk; their expenditures come from the independent expenditure file, with
  amended filings dropped.

Contributions from one listed committee to another are subtracted from the
giver, so no dollar is counted twice. Money a super PAC gives to other super
PACs (United Democracy Project does this) is counted as given, but its
election is unknown, so it never counts toward the primary line.

The primary line needs the election each dollar was for, which only the
itemized records have:
- independent: itemized Schedule E (itpas2 24E/24A, or Form 5 rows)
- given: itemized direct contributions (itpas2 24K/24Z) plus earmarked
  donations as reported by the receiving campaigns (itcont 15E with the PAC
  as conduit, totals from fetch_earmarks.py). The primary share of these
  itemized records is applied to the reported total.
"Primary" means the FEC election code starts with P. Runoffs are not counted.

Usage: python analysis/money-in-politics/home_front.py RAW_DIR OUT_DIR
  RAW_DIR is a checkout of the raw-money-home branch.
"""

import csv
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
CYCLES = [2016, 2018, 2020, 2022, 2024, 2026]

# itpas2 columns
P_CMTE, P_PGI, P_TP, P_AMT, P_OTHER, P_MEMO = 0, 3, 5, 14, 15, 18
DIRECT = {"24K", "24Z"}
INDEPENDENT = {"24E", "24A"}
# webk columns
W_ID, W_GIVEN, W_IE = 0, 22, 23


def committees():
    return {
        r["committee_id"]: r for r in csv.DictReader((HERE / "home_front_committees.csv").open())
    }


def webk(path: Path, ids: set[str]):
    with zipfile.ZipFile(path) as z:
        for line in io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1"):
            f = line.rstrip("\r\n").split("|")
            if f[W_ID] in ids:
                yield f[W_ID], float(f[W_GIVEN] or 0), float(f[W_IE] or 0)


def form5_rows(path: Path, ids: set[str]):
    """Independent expenditures by Form 5 filers, without superseded filings."""
    rows = [
        r
        for r in csv.DictReader(path.open(encoding="latin-1"))
        if r["spe_id"] in ids and r["spe_id"].startswith("C9")
    ]
    replaced = {r["prev_file_num"] for r in rows if r["prev_file_num"]}
    return [r for r in rows if r["file_num"] not in replaced]


def share(itemized: dict) -> float | None:
    total = itemized[True] + itemized[False]
    if total <= 0:
        return None
    return min(1.0, max(0.0, itemized[True] / total))


def main(raw: Path, out: Path) -> int:
    cms = committees()
    ids = set(cms)
    rows = []
    for cycle in CYCLES:
        yy = f"{cycle % 100:02d}"
        given = defaultdict(float)
        indep = defaultdict(float)
        for cid, g, ie in webk(raw / f"fec/webk{yy}.zip", ids):
            given[cid] += g
            indep[cid] += ie

        # Itemized amounts by primary (True) or not (False).
        item_given = defaultdict(lambda: {True: 0.0, False: 0.0})
        item_ie = defaultdict(lambda: {True: 0.0, False: 0.0})
        earmarked = defaultdict(float)
        for f in csv.reader((raw / f"pas2_{cycle}.csv").open(encoding="latin-1")):
            if f[P_CMTE] not in ids or f[P_MEMO] == "X":
                continue
            target = (
                item_given if f[P_TP] in DIRECT else item_ie if f[P_TP] in INDEPENDENT else None
            )
            if target is not None:
                target[f[P_CMTE]][f[P_PGI][:1] == "P"] += float(f[P_AMT] or 0)
        for r in form5_rows(raw / f"ie_{cycle}.csv", ids):
            amt = float(r["exp_amo"] or 0)
            item_ie[r["spe_id"]][r["ele_type"][:1] == "P"] += amt
            indep[r["spe_id"]] += amt
        # Contributions between listed committees would be counted twice.
        internal = defaultdict(float)
        for name in (f"pas2_{cycle}.csv", f"oth_{cycle}.csv"):
            for f in csv.reader((raw / name).open(encoding="latin-1")):
                if (
                    f[P_CMTE] in ids
                    and f[P_OTHER] in ids
                    and f[P_TP] in DIRECT
                    and f[P_MEMO] != "X"
                ):
                    internal[f[P_CMTE]] += float(f[P_AMT] or 0)
        for cid, amt in internal.items():
            given[cid] -= amt

        em = raw / f"earmarks_{cycle}.csv"
        if not em.exists():
            print(f"{cycle}: no earmark totals", file=sys.stderr)
        else:
            for r in csv.DictReader(em.open()):
                if r["type"] == "15E" and r["memo"] != "X" and r["conduit_id"] in ids:
                    amt = float(r["amount"])
                    item_given[r["conduit_id"]][r["pgi"] == "P"] += amt
                    earmarked[r["conduit_id"]] += amt

        for cid in ids:
            g, ie = given[cid], indep[cid]
            if not (g or ie):
                continue
            sg, si = share(item_given[cid]), share(item_ie[cid])
            primary = g * (sg or 0) + ie * (si or 0)
            rows.append(
                {
                    "cycle": cycle,
                    "committee_id": cid,
                    "group": cms[cid]["group"],
                    "name": cms[cid]["name"],
                    "given": round(g),
                    "independent": round(ie),
                    "total": round(g + ie),
                    "primary": round(primary),
                    "earmarked_itemized": round(earmarked[cid]),
                    "primary_share_given": "" if sg is None else round(sg, 3),
                    "primary_share_independent": "" if si is None else round(si, 3),
                }
            )

    out.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: (r["cycle"], r["group"], -r["total"]))
    with (out / "home_front_committees_by_cycle.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    groups = defaultdict(lambda: defaultdict(float))
    for r in rows:
        g = groups[(r["cycle"], r["group"])]
        for k in ("given", "independent", "total", "primary"):
            g[k] += r[k]
        g["committees"] += 1
    with (out / "home_front_by_group.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cycle", "group", "committees", "given", "independent", "total", "primary"])
        for (cycle, group), g in sorted(groups.items(), key=lambda kv: (kv[0][0], -kv[1]["total"])):
            w.writerow(
                [cycle, group, int(g["committees"])]
                + [round(g[k]) for k in ("given", "independent", "total", "primary")]
            )
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
