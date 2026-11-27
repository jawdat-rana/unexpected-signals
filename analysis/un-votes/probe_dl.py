"""One-off probe of UN Digital Library search options for bulk voting data.

Writes each reply into OUT_DIR so it can be read from the raw-un-probe branch.
"""
import sys, time, urllib.parse, urllib.request
from pathlib import Path

H = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}
S = "https://digitallibrary.un.org/search"
TRIES = {
    "datasets_voting": {"ln": "en", "p": "voting data", "c": "Datasets", "of": "xm", "rg": 50},
    "any_voting_dataset": {"ln": "en", "p": "\"General Assembly voting data\"", "of": "xm", "rg": 50},
    "year_1990": {"ln": "en", "cc": "Voting Data", "p": "269__a:1990*", "of": "xm", "rg": 200},
    "year_1990_count": {"ln": "en", "cc": "Voting Data", "p": "269__a:1990*", "of": "id", "rg": 1000},
    "all_ids": {"ln": "en", "cc": "Voting Data", "of": "id", "rg": 100000},
    "kashmir": {"ln": "en", "cc": "Voting Data", "p": "kashmir OR jammu OR \"india-pakistan\"", "of": "hb", "rg": 100},
    "vetoed_drafts": {"ln": "en", "cc": "Voting Data", "p": "791__a:S/* -791__a:S/RES*", "of": "id", "rg": 1000},
}
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for name, q in TRIES.items():
    url = f"{S}?{urllib.parse.urlencode(q)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=300) as r:
            b = r.read()
        (out / f"{name}.txt").write_bytes(b)
        print(name, len(b), b[:300])
    except Exception as e:
        print(name, "FAILED", e)
    time.sleep(3)
for path in ["https://digitallibrary.un.org/collection/Voting%20Data?ln=en", "https://digitallibrary.un.org/collection/Datasets?ln=en"]:
    try:
        with urllib.request.urlopen(urllib.request.Request(path, headers=H), timeout=120) as r:
            b = r.read()
        (out / (path.split("/")[-1].split("?")[0].replace("%20", "_") + ".html")).write_bytes(b)
        print(path, len(b))
    except Exception as e:
        print(path, "FAILED", e)
