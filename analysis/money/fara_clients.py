"""Count each country's foreign clients ("foreign principals") under FARA.

The FARA bulk files have no dollar amounts, so this counts clients that were
active at any point in a window, and the registered agents working for them.

Usage: python analysis/money/fara_clients.py RAW_DIR START END OUT_CSV
  START and END are dates like 2025-01-01.
"""

import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


def parse(s: str) -> date | None:
    try:
        return datetime.strptime(s.strip(), "%m/%d/%Y").date()
    except ValueError:
        return None


def main(raw: Path, start: date, end: date, out: Path) -> int:
    with zipfile.ZipFile(raw / "fara/FARA_All_ForeignPrincipals.csv.zip") as z:
        text = io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1")
        rows = list(csv.DictReader(text))
    clients = defaultdict(set)
    agents = defaultdict(set)
    for r in rows:
        began = parse(r["Foreign Principal Registration Date"])
        ended = parse(r["Foreign Principal Termination Date"])
        if began is None or began > end or (ended is not None and ended < start):
            continue
        country = r["Country/Location Represented"].strip().title()
        clients[country].add((r["Registration Number"], r["Foreign Principal"].strip().upper()))
        agents[country].add(r["Registration Number"])
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["country", "fara_clients", "fara_agents", "window_start", "window_end"])
        for c in sorted(clients, key=lambda c: -len(clients[c])):
            w.writerow([c, len(clients[c]), len(agents[c]), start, end])
    return 0


if __name__ == "__main__":
    a = sys.argv
    sys.exit(main(Path(a[1]), date.fromisoformat(a[2]), date.fromisoformat(a[3]), Path(a[4])))
