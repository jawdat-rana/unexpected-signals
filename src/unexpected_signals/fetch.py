"""Download a gzipped feed with retries, returning decompressed bytes."""

from __future__ import annotations

import gzip
import time
import urllib.request

USER_AGENT = "unexpected-signals/0.1 (+https://github.com/jawdat-rana/unexpected-signals)"


def download(url: str, retries: int = 3, timeout: int = 60) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read()
            return gzip.decompress(payload) if payload[:2] == b"\x1f\x8b" else payload
        except Exception as exc:  # network errors vary a lot; retry them all
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Failed to download {url}") from last_error
