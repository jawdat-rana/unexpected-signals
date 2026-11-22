"""Download a gzipped feed with retries, returning decompressed bytes."""

from __future__ import annotations

import gzip
import http.client
import time
import urllib.request

USER_AGENT = "unexpected-signals/0.1 (+https://github.com/jawdat-rana/unexpected-signals)"


def download(url: str, retries: int = 3, timeout: int = 60, allow_partial: bool = False) -> bytes:
    """Download `url`. With `allow_partial`, a body cut off early is returned as is,
    after the last retry, instead of raising (the caller must cope)."""
    last_error: Exception | None = None
    partial = b""
    for attempt in range(retries):
        try:
            headers = {"User-Agent": USER_AGENT}
            if not allow_partial:  # a cut-off gzip body can't be decompressed
                headers["Accept-Encoding"] = "gzip"
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                try:
                    payload = response.read()
                except http.client.IncompleteRead as exc:
                    if not allow_partial:
                        raise
                    partial = max(partial, exc.partial, key=len)
                    raise
            return gzip.decompress(payload) if payload[:2] == b"\x1f\x8b" else payload
        except Exception as exc:  # network errors vary a lot; retry them all
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
    if allow_partial and partial:
        return partial
    raise RuntimeError(f"Failed to download {url}") from last_error
