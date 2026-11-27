"""Write the river lines for the water replay's map.

Takes the big rivers (Rhine and its branches, Maas, IJssel, Scheldt) from
Natural Earth 1:10m river centerlines (public domain), clips them to the
Netherlands and a little around it, rounds to ~100 m, and writes them as a JS
module next to the country outline.

    python analysis/water-levels/make_rivers.py [path/to/ne_10m_rivers_lake_centerlines.geojson]
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "replays" / "water-nl" / "charts" / "rivers.js"
URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_10m_rivers_lake_centerlines.geojson"
)
RIVERS = {"Rhine", "Maas", "IJssel", "Schelde", "Lek", "Nederrijn", "Waal"}
BOX = (3.3, 50.7, 7.25, 53.5)  # lon/lat box around the Netherlands


def inside(point: list[float]) -> bool:
    return BOX[0] <= point[0] <= BOX[2] and BOX[1] <= point[1] <= BOX[3]


def clip(line: list[list[float]]) -> list[list[list[float]]]:
    """Split a line into the runs of points inside the box."""
    runs, run = [], []
    for point in line:
        if inside(point):
            run.append([round(point[0], 3), round(point[1], 3)])
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) > 1]


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        source = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    else:
        with urllib.request.urlopen(URL, timeout=120) as response:
            source = json.load(response)
    features = []
    for feature in source["features"]:
        name = feature["properties"].get("name")
        geometry = feature.get("geometry")
        if name not in RIVERS or not geometry:
            continue
        lines = geometry["coordinates"]
        if geometry["type"] == "LineString":
            lines = [lines]
        runs = [run for line in lines for run in clip(line)]
        if runs:
            features.append({
                "type": "Feature",
                "properties": {"name": name},
                "geometry": {"type": "MultiLineString", "coordinates": runs},
            })  # fmt: skip
    body = json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
    OUT.write_text(
        "// The big rivers of the Netherlands (Rhine, Waal, Nederrijn, Lek, IJssel,\n"
        "// Maas, Scheldt), from Natural Earth 1:10m river centerlines (public domain,\n"
        "// naturalearthdata.com). Made by analysis/water-levels/make_rivers.py.\n"
        f"export default {body};\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(features)} river features")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
