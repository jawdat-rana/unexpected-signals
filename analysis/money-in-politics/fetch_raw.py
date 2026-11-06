"""Download the raw sources for the "Money in politics" series.

This only downloads. Parsing happens in separate scripts once we have seen what
each source actually returns. A failed URL is recorded in the manifest and
skipped, so one blocked site does not stop the rest.

Usage: python analysis/money-in-politics/fetch_raw.py OUT_DIR
"""

import csv
import sys
import time
import urllib.request
from pathlib import Path

OS = "https://www.opensecrets.org"
FEC = "https://www.fec.gov/files/bulk-downloads"
FARA = "https://efile.fara.gov/bulk/zip"
OS_PACS = f"{OS}/political-action-committees-pacs/foreign-connected-pacs"
FARA_FILES = (
    "FARA_All_Registrants",
    "FARA_All_ForeignPrincipals",
    "FARA_All_RegistrantDocs",
)

CYCLES = [2016, 2018, 2020, 2022, 2024, 2026]

SOURCES = (
    # OpenSecrets: foreign-connected PACs, with parent company and country.
    [(f"opensecrets/foreign-pacs-{c}.html", f"{OS_PACS}/{c}") for c in CYCLES]
    # OpenSecrets Foreign Lobby Watch: FARA spending by country. The exact
    # country page URL is a guess, so the landing page is saved too.
    + [
        ("opensecrets/fara-landing.html", f"{OS}/fara"),
        ("opensecrets/fara-countries.html", f"{OS}/fara/countries"),
    ]
    # FEC bulk files: committee master (connected organisation) and PAC
    # summaries (receipts, contributions to candidates) for recent cycles.
    + [(f"fec/cm{c % 100}.zip", f"{FEC}/{c}/cm{c % 100}.zip") for c in (2024, 2026)]
    + [(f"fec/webk{c % 100}.zip", f"{FEC}/{c}/webk{c % 100}.zip") for c in (2024, 2026)]
    # FARA eFile bulk files: registrants and foreign principals (no dollar
    # amounts; those are only in the filed documents).
    + [(f"fara/{name}.csv.zip", f"{FARA}/{name}.csv.zip") for name in FARA_FILES]
)

HEADERS = {
    "User-Agent": "unexpected-signals research script (github.com/jawdat-rana/unexpected-signals)"
}


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:  # noqa: BLE001 - record any failure and move on
        print(f"  error: {e}", file=sys.stderr)
        return 0, b""


def main(out: Path) -> int:
    rows = []
    for rel, url in SOURCES:
        print(f"GET {url}", file=sys.stderr)
        status, body = fetch(url)
        if status == 200 and body:
            path = out / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        rows.append({"path": rel, "url": url, "status": status, "bytes": len(body)})
        time.sleep(2)  # be polite to opensecrets.org
    with (out / "manifest.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "url", "status", "bytes"])
        w.writeheader()
        w.writerows(rows)
    ok = sum(r["status"] == 200 for r in rows)
    print(f"{ok}/{len(rows)} sources downloaded", file=sys.stderr)
    return 0


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    sys.exit(main(out))
