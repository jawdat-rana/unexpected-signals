"""Download the UN's bulk voting datasets for the UN votes stories.

1. UN Digital Library "Datasets" collection: the Dag Hammarskjöld Library
   publishes every recorded vote as CSV, refreshed a few times a year:
   General Assembly votes (record 4060887), General Assembly outcomes
   (4060945, including resolutions adopted without a vote) and Security
   Council votes (4055387). We look the records up by search, so a new
   release with new file names is picked up, and keep every CSV and its
   Markdown notes, gzipped.
       dl/<file>.gz, dl/records.xml
2. Erik Voeten's UNGA ideal points (Harvard Dataverse, doi:10.7910/DVN/LEJUQZ,
   CC0): the file list and the files under 5 MB.
       voeten/files.json, voeten/<file>

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
DL_QUERY = {"ln": "en", "p": "voting data", "c": "Datasets", "of": "xm", "rg": 50}
DATAVERSE = "https://dataverse.harvard.edu"
VOETEN_DOI = "doi:10.7910/DVN/LEJUQZ"
MAX_FILE = 5_000_000

manifest: list[dict] = []


def get(url: str, timeout: int = 600, tries: int = 4) -> bytes:
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
    print(f"{source:8} {item:45} {status} {detail}", flush=True)


def digital_library(out: Path) -> None:
    folder = out / "dl"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        xml = get(f"{DL_SEARCH}?{urllib.parse.urlencode(DL_QUERY)}")
    except Exception as e:  # noqa: BLE001
        log("dl", "search", "failed", str(e)[:200])
        return
    (folder / "records.xml").write_bytes(xml)
    urls = sorted(set(re.findall(r'<subfield code="u">(https://digitallibrary\.un\.org/record/\d+/files/[^<]+\.(?:csv|md))</subfield>',
                                 xml.decode("utf-8", "replace"))))
    log("dl", "search", "ok", f"{len(urls)} files")
    for url in urls:
        name = url.rsplit("/", 1)[-1]
        try:
            data = get(url)
            (folder / f"{name}.gz").write_bytes(gzip.compress(data, 6))
            rows = data.count(b"\n") if name.endswith(".csv") else ""
            log("dl", name, "ok", f"{len(data)} bytes {rows} lines")
        except Exception as e:  # noqa: BLE001
            log("dl", name, "failed", str(e)[:200])


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
    for f in latest["files"]:
        df = f["dataFile"]
        name, size, fid = df.get("filename"), df.get("filesize", 0), df["id"]
        if size > MAX_FILE:
            log("voeten", name, "skipped", f"{size} bytes")
            continue
        try:
            data = get(f"{DATAVERSE}/api/access/datafile/{fid}?format=original")
            (folder / name).write_bytes(data)
            log("voeten", name, "ok", f"{len(data)} bytes")
        except Exception as e:  # noqa: BLE001
            log("voeten", name, "failed", str(e)[:200])


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    digital_library(out)
    voeten(out)
    with open(out / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "item", "status", "detail"])
        w.writeheader()
        w.writerows(manifest)


if __name__ == "__main__":
    main()
