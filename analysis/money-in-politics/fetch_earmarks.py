"""Total the donations that home-front PACs pass on to candidates (earmarks).

PACs like AIPAC PAC, JStreetPAC and NORPAC mostly act as conduits: a donor
writes a check earmarked for a candidate, and the PAC forwards it. Those
forwarded donations are not in the committee files. They sit in the FEC
individual contributions file (itcont), on the receiving campaign's report,
with the conduit PAC in the OTHER_ID column.

The file is several GB per cycle and full of donor names, so this streams it
and writes only totals, never names. Two outputs per cycle:

- earmarks_YYYY.csv: by conduit PAC, receiving committee, election (PGI),
  transaction type and memo code, as reported by the receiving committee
- conduit_receipts_YYYY.csv: what the PACs themselves report receiving from
  individuals, by PAC, transaction type, memo code and whether it was
  earmarked (OTHER_ID filled in)

Usage: python analysis/money-in-politics/fetch_earmarks.py INDIV_ZIP CYCLE OUT_DIR
"""

import csv
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

CMTE, PGI, TP, AMT, OTHER, MEMO = 0, 3, 5, 14, 15, 18


def main(zpath: Path, cycle: int, out: Path) -> int:
    ids = {r["committee_id"] for r in csv.DictReader((HERE / "home_front_committees.csv").open())}
    earmarks = defaultdict(lambda: [0, 0.0])
    receipts = defaultdict(lambda: [0, 0.0])
    with zipfile.ZipFile(zpath) as z:
        name = max(z.namelist(), key=lambda n: z.getinfo(n).file_size)
        for line in io.TextIOWrapper(z.open(name), encoding="latin-1"):
            f = line.split("|")
            if len(f) < 20:
                continue
            if f[OTHER] in ids and f[CMTE] not in ids:
                key = (f[OTHER], f[CMTE], f[PGI][:1], f[TP], f[MEMO])
                acc = earmarks[key]
            elif f[CMTE] in ids:
                key = (f[CMTE], f[TP], f[MEMO], bool(f[OTHER]))
                acc = receipts[key]
            else:
                continue
            acc[0] += 1
            acc[1] += float(f[AMT] or 0)

    out.mkdir(parents=True, exist_ok=True)
    with (out / f"earmarks_{cycle}.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cycle", "conduit_id", "recipient_id", "pgi", "type", "memo", "n", "amount"])
        for k, (n, a) in sorted(earmarks.items()):
            w.writerow([cycle, *k, n, round(a, 2)])
    with (out / f"conduit_receipts_{cycle}.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cycle", "committee_id", "type", "memo", "has_other_id", "n", "amount"])
        for k, (n, a) in sorted(receipts.items()):
            w.writerow([cycle, *k, n, round(a, 2)])
    print(f"{cycle}: {len(earmarks)} earmark rows, {len(receipts)} receipt rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])))
