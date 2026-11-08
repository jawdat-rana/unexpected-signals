"""Find where the NS annual-report dashboard loads its station data from.

Opens the public dashboard page in a headless browser, records every network
request it makes, and prints the data-looking ones (XHR/fetch, JSON, .ashx,
/api/) with a short preview of each response. Read-only, one page load.

    pip install playwright && playwright install chromium
    python analysis/ns-stations/probe.py [station-slug]
"""

from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

BASE = "https://dashboards.nsjaarverslag.nl/reizigersgedrag/"


def main(slug: str) -> None:
    seen: list[tuple[str, str, str, int, str]] = []

    def on_response(response) -> None:
        req = response.request
        ctype = response.headers.get("content-type", "")
        preview = ""
        if req.resource_type in ("xhr", "fetch") or "json" in ctype:
            try:
                preview = response.text()[:800]
            except Exception as exc:  # body may be unavailable for redirects
                preview = f"<no body: {exc!r}>"
        seen.append((req.method, req.resource_type, response.url, response.status, ctype))
        if preview:
            print(f"\n=== {req.method} {response.status} {response.url}\n{ctype}\n{preview}")
            if req.post_data:
                print(f"--- request body: {req.post_data[:500]}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("response", on_response)
        page.goto(BASE + slug, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()

    print("\n\n## All requests")
    for method, rtype, url, status, ctype in seen:
        print(f"{method:5} {status} {rtype:10} {ctype[:30]:30} {url[:160]}")

    print("\n\n## Rendered page text (first 3000 chars)")
    import re

    text = re.sub(r"<[^>]+>", " ", html)
    print(re.sub(r"\s+", " ", text)[:3000])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "rotterdam-centraal")
