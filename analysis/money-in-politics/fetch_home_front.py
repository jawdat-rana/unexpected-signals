"""Download and pre-filter FEC data for Part 2, "The home front".

Part 2 counts money from American donors that goes through foreign-policy and
diaspora PACs. The FEC has no flag for that, so this script casts a wide net:
every committee whose name or connected organisation matches one of the
keywords below is kept as a *candidate*. Choosing which candidates count, and
for which group, is done by hand afterwards in `home_front_committees.csv`.

The full contribution files are too big to keep, so for each cycle this keeps:
- fec/cmYY.zip, fec/webkYY.zip, fec/cnYY.zip (committee master, PAC
  summaries, candidate master; small, kept whole)
- candidates_YYYY.csv: committee master rows that matched a keyword
- pas2_YYYY.csv: contributions to candidates and independent expenditures
  (itpas2) made by those committees
- oth_YYYY.csv: other committee transactions (itoth) filed by them, which
  is where earmarked contributions passed through a PAC show up
- ie_YYYY.csv: rows of the independent expenditure file filed by them

Usage: python analysis/money-in-politics/fetch_home_front.py OUT_DIR
"""

import csv
import io
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

FEC = "https://www.fec.gov/files/bulk-downloads"
CYCLES = [2016, 2018, 2020, 2022, 2024, 2026]

# Wide on purpose. False hits (INDIAN tribes, CHINESE restaurant owners, ...)
# are dropped by hand when building home_front_committees.csv.
KEYWORDS = re.compile(
    r"ISRAEL|ZION|JEWISH|\bJ ?STREET|NORPAC|AIPAC|UNITED DEMOCRACY PROJECT"
    r"|ARMENIA|\bINDIAN?\b|INDO[- ]|HINDU|SIKH|CUBA|TAIWAN|FORMOSA|PAKIST"
    r"|UKRAIN|IRAN|PERSIAN|GREEK|HELLEN|CYPR|KOREA|PALESTIN|\bARAB|MUSLIM"
    r"|ISLAM|LEBAN|POLISH|POLONIA|IRISH|BANGLADESH|NEPAL|ETHIOP|ERITRE"
    r"|SOMALI|NIGERIA|HAITI|VIETNAM|FILIPINO|PHILIPPIN|CHINESE|TIBET|KURD"
    r"|ASSYRIA|COPTIC|EGYPT|TURKISH|AZERBAIJ|SERBIA|ALBANIA|BALTIC|LITHUANIA"
    r"|LATVIA|ESTONIA|VENEZUEL|NICARAGU|COLOMBIA|EMGAGE|IMPACT FUND"
    r"|FOREIGN POLICY|DIASPORA|DMFI|\bANCA\b|INDIASPORA",
    re.I,
)

LISTED = Path(__file__).parent / "home_front_committees.csv"

# FEC bulk column positions.
CM_ID, CM_NAME, CM_CONNECTED = 0, 1, 13
PAS2_CMTE = 0
IE_SPENDER = 2  # spe_id
CANDIDATE_COLS = [
    "cycle",
    "committee_id",
    "name",
    "type",
    "designation",
    "party",
    "connected_org",
    "keyword",
]

HEADERS = {
    "User-Agent": "unexpected-signals research script (github.com/jawdat-rana/unexpected-signals)"
}


def fetch(url: str, path: Path) -> tuple[int, int]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as fh:
                n = 0
                while chunk := resp.read(1 << 20):
                    fh.write(chunk)
                    n += len(chunk)
            return resp.status, n
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:  # noqa: BLE001 - record any failure and move on
        print(f"  error: {e}", file=sys.stderr)
        return 0, 0


def bar_rows(zpath: Path):
    with zipfile.ZipFile(zpath) as z:
        name = z.namelist()[0]
        for line in io.TextIOWrapper(z.open(name), encoding="latin-1"):
            yield line.rstrip("\r\n").split("|")


def main(out: Path) -> int:
    manifest = []
    tmp = out / "_tmp"
    for cycle in CYCLES:
        yy = f"{cycle % 100:02d}"
        files = {
            "cm": (f"{FEC}/{cycle}/cm{yy}.zip", out / f"fec/cm{yy}.zip"),
            "webk": (f"{FEC}/{cycle}/webk{yy}.zip", out / f"fec/webk{yy}.zip"),
            "cn": (f"{FEC}/{cycle}/cn{yy}.zip", out / f"fec/cn{yy}.zip"),
            "pas2": (f"{FEC}/{cycle}/pas2{yy}.zip", tmp / f"pas2{yy}.zip"),
            "oth": (f"{FEC}/{cycle}/oth{yy}.zip", tmp / f"oth{yy}.zip"),
            "ie": (
                f"{FEC}/{cycle}/independent_expenditure_{cycle}.csv",
                tmp / f"ie{cycle}.csv",
            ),
        }
        ok = {}
        for key, (url, path) in files.items():
            print(f"GET {url}", file=sys.stderr)
            status, n = fetch(url, path)
            ok[key] = status == 200 and n > 0
            manifest.append({"cycle": cycle, "file": key, "url": url, "status": status, "bytes": n})
            time.sleep(1)
        if not ok["cm"]:
            continue

        # Listed committees are always kept, even if a later name change
        # means they no longer match a keyword (RJC Victory Fund, for one).
        ids = {r["committee_id"] for r in csv.DictReader(LISTED.open())}
        with (out / f"candidates_{cycle}.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(CANDIDATE_COLS)
            for f in bar_rows(files["cm"][1]):
                m = KEYWORDS.search(f"{f[CM_NAME]} | {f[CM_CONNECTED]}")
                if m:
                    ids.add(f[CM_ID])
                    w.writerow(
                        [cycle, f[CM_ID], f[CM_NAME], f[9], f[8], f[10], f[CM_CONNECTED]]
                        + [m.group(0).upper()]
                    )

        for key in ("pas2", "oth"):
            if not ok[key]:
                continue
            with (out / f"{key}_{cycle}.csv").open("w", newline="") as fh:
                w = csv.writer(fh)
                for f in bar_rows(files[key][1]):
                    if f[PAS2_CMTE] in ids:
                        w.writerow(f)
            files[key][1].unlink()

        if ok["ie"]:
            with (
                files["ie"][1].open(newline="", encoding="latin-1") as src,
                (out / f"ie_{cycle}.csv").open("w", newline="") as fh,
            ):
                r = csv.reader(src)
                w = csv.writer(fh)
                w.writerow(next(r))
                for f in r:
                    if len(f) > IE_SPENDER and f[IE_SPENDER] in ids:
                        w.writerow(f)
            files["ie"][1].unlink()
        print(f"{cycle}: {len(ids)} candidate committees", file=sys.stderr)

    with (out / "manifest.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["cycle", "file", "url", "status", "bytes"])
        w.writeheader()
        w.writerows(manifest)
    return 0


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    sys.exit(main(out))
