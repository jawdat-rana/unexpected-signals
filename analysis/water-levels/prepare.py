"""Turn the raw Rijkswaterstaat water levels into the replay's data.

Reads the output of fetch_raw.py (the raw-water branch) and writes:

    replays/water-nl/data/levels.csv   t, then one column per station: water
                                       height in cm relative to NAP, every
                                       10 minutes (UTC), empty when missing
    replays/water-nl/charts/meta.js    stations (name, group, position, their
                                       normal level and range) and the moments
                                       the replay can jump to

    git fetch origin raw-water && git worktree add /tmp/raw-water FETCH_HEAD
    python analysis/water-levels/prepare.py /tmp/raw-water
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "replays" / "water-nl"
STEP = dt.timedelta(minutes=10)
# Gaps up to this long are filled by straight lines; longer ones stay empty.
MAX_GAP = dt.timedelta(minutes=40)

GROUPS = {
    "coast": [
        "vlissingen", "westkapelle", "roompot-buiten", "haringvliet-buiten", "hoek-van-holland",
        "scheveningen", "ijmuiden", "petten", "den-helder", "oudeschild", "den-oever",
        "kornwerderzand", "harlingen", "vlieland", "terschelling", "nes", "schiermonnikoog",
        "lauwersoog", "eemshaven", "delfzijl", "nieuwe-statenzijl",
    ],
    "behind-barrier": ["roompot-binnen"],
    "scheldt": ["terneuzen", "hansweert", "bath"],
    "rotterdam": [
        "maeslant-sea", "maeslant-river", "brienenoord", "maassluis", "vlaardingen", "rotterdam",
        "spijkenisse", "krimpen", "dordrecht",
        "moerdijk", "goidschalxoord",
    ],
    "rhine": ["lobith", "pannerdense-kop", "nijmegen", "tiel", "zaltbommel", "gorinchem"],
    "lek": ["arnhem", "driel", "amerongen", "hagestein", "schoonhoven"],
    "ijssel": ["westervoort", "zutphen", "deventer", "olst", "kampen"],
    "meuse": [
        "eijsden", "maastricht", "roermond", "venlo", "grave", "lith", "heesbeen", "keizersveer",
    ],
}  # fmt: skip
GROUP_OF = {key: group for group, keys in GROUPS.items() for key in keys}
# Short names for labels.
LABELS = {
    "hoek-van-holland": "Hoek van Holland", "roompot-buiten": "Roompot (sea)",
    "roompot-binnen": "Roompot (Oosterschelde)", "haringvliet-buiten": "Haringvliet (sea)",
    "den-helder": "Den Helder", "den-oever": "Den Oever", "nieuwe-statenzijl": "Nieuwe Statenzijl",
    "pannerdense-kop": "Pannerdense Kop", "ijmuiden": "IJmuiden", "krimpen": "Krimpen a/d IJssel",
    "maeslant-sea": "Maeslantkering (sea side)", "maeslant-river": "Maeslantkering (river side)",
    "brienenoord": "Brienenoordbrug", "rotterdam": "Rotterdam", "nes": "Ameland",
    "oudeschild": "Texel", "goidschalxoord": "Heinenoord", "bath": "Bath",
}  # fmt: skip


def parse(stamp: str) -> dt.datetime:
    return dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.UTC)


def read_levels(path: Path) -> dict[dt.datetime, float]:
    with path.open(encoding="utf-8") as f:
        return {parse(r["time"]): float(r["cm"]) for r in csv.DictReader(f)}


def on_grid(values: dict[dt.datetime, float], times: list[dt.datetime]) -> list[float | None]:
    """Values at each grid time; short gaps filled by straight lines."""
    known = sorted((t, v) for t, v in values.items() if t.minute % 10 == 0)
    lookup = dict(known)
    out: list[float | None] = []
    j = 0
    for t in times:
        if t in lookup:
            out.append(lookup[t])
            continue
        while j < len(known) and known[j][0] < t:
            j += 1
        if 0 < j < len(known):
            (t0, v0), (t1, v1) = known[j - 1], known[j]
            if t1 - t0 <= MAX_GAP:
                out.append(v0 + (v1 - v0) * (t - t0) / (t1 - t0))
                continue
        out.append(None)
    return out


def closed_spells(sea: list, inside: list, times: list, threshold: float) -> list[tuple]:
    """Spells where the water inside a barrier stayed far below the sea: the
    barrier was shut. Needs the gap for two hours or more."""
    spells, start = [], None
    for i in range(len(times)):
        gap = None if sea[i] is None or inside[i] is None else sea[i] - inside[i]
        shut = gap is not None and gap > threshold
        if shut and start is None:
            start = i
        if not shut and start is not None:
            if i - start >= 12:
                spells.append((times[start], times[i - 1]))
            start = None
    if start is not None and len(times) - start >= 12:
        spells.append((times[start], times[-1]))
    return spells


def main(argv: list[str]) -> int:
    raw = Path(argv[1] if len(argv) > 1 else "raw")
    with (raw / "stations.csv").open(encoding="utf-8") as f:
        stations = [r for r in csv.DictReader(f) if r["lat"] and r["lon"]]
    series = {s["key"]: read_levels(raw / "levels" / f"{s['key']}.csv") for s in stations}
    first = min(min(v) for v in series.values() if v)
    last = max(max(v) for v in series.values() if v)
    times = []
    t = first.replace(minute=first.minute - first.minute % 10)
    while t <= last:
        times.append(t)
        t += STEP
    grid = {key: on_grid(values, times) for key, values in series.items()}
    # Keep stations with data for most of the window.
    keep = [s for s in stations if sum(v is not None for v in grid[s["key"]]) > 0.8 * len(times)]
    dropped = sorted({s["key"] for s in stations} - {s["key"] for s in keep})
    if dropped:
        print(f"Dropped (too many gaps): {', '.join(dropped)}")

    OUT.joinpath("data").mkdir(parents=True, exist_ok=True)
    with (OUT / "data" / "levels.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["t", *[s["key"] for s in keep]])
        for i, t in enumerate(times):
            cells = [grid[s["key"]][i] for s in keep]
            writer.writerow([t.strftime("%Y-%m-%dT%H:%MZ"),
                             *["" if v is None else round(v) for v in cells]])  # fmt: skip

    # "Normal" is each gauge's median over the first two days, 18 and 19
    # December: before the storm and before the river flood waves arrived.
    calm = [i for i, t in enumerate(times) if t < times[0] + dt.timedelta(days=2)]
    meta = []
    for s in keep:
        values = [v for v in grid[s["key"]] if v is not None]
        calm_values = [grid[s["key"]][i] for i in calm if grid[s["key"]][i] is not None]
        meta.append({
            "key": s["key"],
            "name": LABELS.get(s["key"], s["name"].split(",")[0].strip()),
            "group": GROUP_OF.get(s["key"], "other"),
            "lat": round(float(s["lat"]), 4),
            "lon": round(float(s["lon"]), 4),
            "normal": round(statistics.median(calm_values or values)),
            "low": round(min(values)),
            "high": round(max(values)),
        })  # fmt: skip

    moments = []

    def peak(key: str) -> tuple[dt.datetime, float] | None:
        if key not in grid:
            return None
        pairs = [(v, times[i]) for i, v in enumerate(grid[key]) if v is not None]
        value = max(v for v, _ in pairs)
        # The first time it reached its highest level.
        return next(t for v, t in pairs if v == value), value

    for key, label in (("hoek-van-holland", "Storm surge at Hoek van Holland"),
                       ("lobith", "The Rhine peaks at Lobith"),
                       ("eijsden", "The Maas flood wave enters at Eijsden")):  # fmt: skip
        found = peak(key)
        if found:
            when, value = found
            moments.append({"t": when.strftime("%Y-%m-%dT%H:%MZ"), "label": label,
                            "station": key, "cm": round(value)})  # fmt: skip
            print(f"{label}: {value:.0f} cm NAP at {when:%Y-%m-%d %H:%M} UTC")

    barriers = []
    # Gauges on either side of each barrier, best pair first. The gauges at the
    # Maeslantkering itself had no data for this window, so Hoek van Holland
    # (sea) and Maassluis (behind it) stand in.
    pairs = (
        ("Maeslantkering", "maeslant-sea", "maeslant-river", 50),
        ("Maeslantkering", "hoek-van-holland", "maassluis", 50),
        ("Oosterscheldekering", "roompot-buiten", "roompot-binnen", 120),
    )
    done = set()
    for name, sea, inside, threshold in pairs:
        if name not in done and sea in grid and inside in grid:
            done.add(name)
            for start, end in closed_spells(grid[sea], grid[inside], times, threshold):
                barriers.append({"name": name, "from": start.strftime("%Y-%m-%dT%H:%MZ"),
                                 "to": end.strftime("%Y-%m-%dT%H:%MZ")})  # fmt: skip
                print(f"{name} shut (inferred): {start:%Y-%m-%d %H:%M} to {end:%Y-%m-%d %H:%M} UTC")

    (OUT / "charts" / "meta.js").write_text(
        "// Stations, moments and barrier closures for the water replay.\n"
        "// Made by analysis/water-levels/prepare.py from Rijkswaterstaat data.\n"
        f"export const stations = {json.dumps(meta, indent=1)};\n"
        f"export const moments = {json.dumps(moments, indent=1)};\n"
        "// Spells when the water behind a storm barrier stayed far below the sea,\n"
        "// so the barrier was shut. Inferred from the levels, not from RWS logs.\n"
        f"export const barriers = {json.dumps(barriers, indent=1)};\n",
        encoding="utf-8",
    )
    print(f"{len(keep)} stations, {len(times)} steps of 10 minutes, {times[0]} to {times[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
