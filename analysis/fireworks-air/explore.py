"""One-off: show the format of RIVM's bulk Luchtmeetnet files."""
import re, sys, urllib.request
H = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}
B = "https://data.rivm.nl/data/luchtmeetnet/"
def head(path, lines=12, width=700):
    req = urllib.request.Request(B + path, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"\n=== {path} size={r.headers.get('Content-Length')} modified={r.headers.get('Last-Modified')}")
            data = r.read(60000).decode("latin-1")
    except Exception as e:
        print(f"\n=== {path} ERR {e}"); return
    for line in data.splitlines()[:lines]:
        print("   ", line[:width])
t = urllib.request.urlopen(urllib.request.Request(B + "Actueel-jaar/", headers=H)).read().decode()
print("ACTUEEL", re.findall(r'href="([^"?]+PM10[^"]*)"', t), re.findall(r'(\d{4}-\d\d-\d\d \d\d:\d\d)', t)[-12:])
head("Vastgesteld-jaar/2024/2024_PM10.csv", 14)
head("Vastgesteld-jaar/2012/2012_PM25.csv", 14)
head("Actueel-jaar/2026_11_PM10.csv", 14)
head("Metadata/luchtmeetnet_meetlocaties.csv", 5)
head("Metadata/luchtmeetnet_meetopstellingen.csv", 5)
