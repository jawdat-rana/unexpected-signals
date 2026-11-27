"""Download a gzipped feed with retries, returning decompressed bytes."""

from __future__ import annotations

import gzip
import json
import time
import urllib.request

USER_AGENT = "unexpected-signals/0.1 (+https://github.com/jawdat-rana/unexpected-signals)"


def download(url: str, retries: int = 3, timeout: int = 60, check=None) -> bytes:
    """Fetch `url`, retrying on errors.

    `check` is called on the body; if it raises, the body counts as a failed
    download and is fetched again. Servers sometimes close the connection
    early without an error, so a truncated body would otherwise get through.
    """
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read()
            body = gzip.decompress(payload) if payload[:2] == b"\x1f\x8b" else payload
            if check:
                check(body)
            return body
        except Exception as exc:  # network errors vary a lot; retry them all
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Failed to download {url}: {last_error!r}") from last_error


def download_json(url: str, retries: int = 3, timeout: int = 60):
    """Download and parse JSON, re-fetching a body that was cut off."""
    return json.loads(download(url, retries=retries, timeout=timeout, check=json.loads))
