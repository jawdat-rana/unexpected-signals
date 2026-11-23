"""Check the Luchtmeetnet API path before New Year: fetch a few stations for the
2025/26 night through the API so the values and hour stamps can be compared with
RIVM's bulk files. Prints the rows; writes nothing."""
import datetime as dt, sys
sys.path.insert(0, "analysis/fireworks-air")
import fetch_raw as f
start, end = dt.datetime(2025, 12, 31, 20), dt.datetime(2026, 1, 1, 4)
for station in ["NL10639", "NL10247", "NL10449", "NL10446", "NL10821"]:
    for formula in f.FORMULAS:
        rows = f.lml_series(station, formula, start, end)
        print(station, formula, len(rows), rows[:12])
