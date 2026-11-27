"""Download UN voting records for the UN votes stories.

Three sources, each optional (a failure is logged in manifest.csv and the rest
still run):

1. UN Digital Library, "Voting Data" collection: every recorded vote in the
   General Assembly and Security Council, including vetoed Security Council
   drafts, as MARC XML. We page through the whole collection and keep one row
   per resolution/draft (votes.csv-like tables are built later by prepare.py).
       records/<page>.xml.gz
2. Erik Voeten's UNGA voting dataset (Harvard Dataverse, doi:10.7910/DVN/LEJUQZ):
   the file list, and every file under 90 MB.
       voeten/files.json, voeten/<file>
3. Dag Hammarskjöld Library list of Security Council vetoes (HTML page).
       vetoes.html

Standard library only. Runs in GitHub Actions (these hosts are not reachable
from every environment):

    python analysis/un-votes/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}
DL_SEARCH = "https://digitallibrary.un.org/search"
DATAVERSE = "https://dataverse.harvard.edu"
VOETEN_DOI = "doi:10.7910/DVN/LEJUQZ"
VETO_URL = "https://research.un.org/en/docs/sc/quick/veto"
PAGE = 200
MAX_FILE = 90_000_000

manifest: list[dict] = []


def get(url: str, timeout: int = 120, tries: int = 4) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def log(source: str, item: str, status: str, detail: str = "") -> None:
    manifest.append({"source": source, "item": item, "status": status, "detail": detail})
    print(f"{source:10} {item:40} {status} {detail}", flush=True)


def digital_library(out: Path) -> None:
    folder = out / "records"
    folder.mkdir(parents=True, exist_ok=True)
    total = None
    start = 1
    while True:
        query = urllib.parse.urlencode(
            {"cc": "Voting Data", "ln": "en", "of": "xm", "rg": PAGE, "jrec": start,
             "sf": "latest first", "so": "d"}
        )
        try:
            body = get(f"{DL_SEARCH}?{query}")
        except Exception as e:  # noqa: BLE001
            log("dl", f"page from {start}", "failed", str(e)[:200])
            return
        text = body.decode("utf-8", "replace")
        if total is None:
            m = re.search(r"Search-Engine-Total-Number-Of-Results:\s*(\d+)", text)
            total = int(m.group(1)) if m else None
            log("dl", "total", "info", str(total))
        n = text.count("<record")
        if n == 0:
            log("dl", f"page from {start}", "empty", text[:200].replace("\n", " "))
            break
        (folder / f"{start:06d}.xml.gz").write_bytes(gzip.compress(body))
        log("dl", f"page from {start}", "ok", f"{n} records")
        start += PAGE
        if n < PAGE or (total and start > total):
            break
        time.sleep(2)


def voeten(out: Path) -> None:
    folder = out / "voeten"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        meta = json.loads(get(f"{DATAVERSE}/api/datasets/:persistentId?persistentId={VOETEN_DOI}"))
    except Exception as e:  # noqa: BLE001
        log("voeten", "metadata", "failed", str(e)[:200])
        return
    (folder / "files.json").write_text(json.dumps(meta, indent=1))
    latest = meta["data"]["latestVersion"]
    log("voeten", "version", "info",
        f"{latest.get('versionNumber')}.{latest.get('versionMinorNumber')} {latest.get('releaseTime')}")
    lic = latest.get("license") or latest.get("termsOfUse")
    log("voeten", "licence", "info", json.dumps(lic)[:200])
    for f in latest["files"]:
        df = f["dataFile"]
        name, size, fid = df.get("filename"), df.get("filesize", 0), df["id"]
        if size > MAX_FILE:
            log("voeten", name, "skipped", f"{size} bytes")
            continue
        try:
            data = get(f"{DATAVERSE}/api/access/datafile/{fid}?format=original", timeout=600)
            (folder / name).write_bytes(data)
            log("voeten", name, "ok", f"{len(data)} bytes")
        except Exception as e:  # noqa: BLE001
            log("voeten", name, "failed", str(e)[:200])


def vetoes(out: Path) -> None:
    try:
        data = get(VETO_URL)
        (out / "vetoes.html").write_bytes(data)
        log("vetoes", "page", "ok", f"{len(data)} bytes")
    except Exception as e:  # noqa: BLE001
        log("vetoes", "page", "failed", str(e)[:200])


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    vetoes(out)
    voeten(out)
    digital_library(out)
    with open(out / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "item", "status", "detail"])
        w.writeheader()
        w.writerows(manifest)


if __name__ == "__main__":
    main()
