"""One-off: list RIVM's bulk Luchtmeetnet folders and show the start of a file."""
import re, sys, urllib.request
H = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}
def get(u, n=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60) as r:
            return r.read(n) if n else r.read()
    except Exception as e:
        return f"ERR {e}".encode()
def links(u):
    t = get(u).decode("utf-8", "replace")
    return [l for l in re.findall(r'href="([^"?]+)"', t) if not l.startswith(("/", "http", ".."))], t[:300]
base = "https://data.rivm.nl/data/luchtmeetnet/"
top, raw = links(base)
print("TOP", top, raw if not top else "")
for d in top:
    sub, raw = links(base + d)
    print("\nDIR", d, sub[:40], raw if not sub else "")
    for s in sub[:3]:
        if s.endswith("/"):
            sub2, _ = links(base + d + s)
            print("  SUB", d + s, sub2[:30])
