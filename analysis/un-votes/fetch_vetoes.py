"""Download the UN list of Security Council vetoes since 1946.

The Dag Hammarskjöld Library veto guide renders its table from the UN Peace
and Security Data Hub dataset DPPA-SCVETOES. We keep the dataset page and every
data file it links to (CSV, XLSX, JSON), plus the guide's rendered veto list.

Standard library only; runs in GitHub Actions:

    python analysis/un-votes/fetch_vetoes.py OUT_DIR
"""

from __future__ import annotations

import csv
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}
PAGES = {
    "dataset.html": "https://psdata.un.org/dataset/DPPA-SCVETOES",
    "veto_list.html": "https://ydsftksff8.execute-api.us-east-1.amazonaws.com/dev/render_meeting_veto/sc_veto_list/EN",
}
manifest: list[dict] = []


def get(url: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def log(item: str, status: str, detail: str = "") -> None:
    manifest.append({"item": item, "status": status, "detail": detail})
    print(f"{item:50} {status} {detail}", flush=True)


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, url in PAGES.items():
        try:
            data = get(url)
            (out / name).write_bytes(data)
            log(name, "ok", f"{len(data)} bytes")
        except Exception as e:  # noqa: BLE001
            log(name, "failed", str(e)[:200])
            continue
        if name != "dataset.html":
            continue
        links = set(re.findall(r'href="([^"]+\.(?:csv|xlsx|json)(?:\?[^"]*)?)"', data.decode("utf-8", "replace"), re.I))
        for link in sorted(links):
            full = urllib.parse.urljoin(url, link)
            fname = re.sub(r"[^A-Za-z0-9._-]", "_", urllib.parse.urlparse(full).path.rsplit("/", 1)[-1])
            try:
                blob = get(full)
                (out / fname).write_bytes(blob)
                log(fname, "ok", f"{len(blob)} bytes from {full}")
            except Exception as e:  # noqa: BLE001
                log(fname, "failed", str(e)[:200])
    with open(out / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "status", "detail"])
        w.writeheader()
        w.writerows(manifest)


if __name__ == "__main__":
    main()
