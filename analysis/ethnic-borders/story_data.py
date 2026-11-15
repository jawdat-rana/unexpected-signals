"""Chart data for "Borders drawn through people".

Reads the overlay tables that `overlay.py` writes to the `raw-borders` branch,
decides which groups today's borders split, and writes the story's chart data:
regions, split groups, the borders that cut them, and a light world map.

A group counts as split when at least two countries each hold 10% or more of
its homeland and two of those countries share a land border. The border test
keeps out diaspora pockets that the 1964 atlas also mapped, like Italians in
Argentina, which are not homelands cut by a line.

Needs geopandas. Natural Earth (public domain) is downloaded once into raw/.

Usage: python analysis/ethnic-borders/story_data.py RAW_BORDERS_DIR
"""

from __future__ import annotations

import json
import sys
import urllib.request
import warnings
from itertools import combinations
from pathlib import Path

import geopandas as gpd
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "raw"
OUT = HERE.parent.parent / "stories" / "borders-drawn-through-people" / "data"
NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_10m_admin_0_countries.geojson"
)

# Breakaway areas Natural Earth draws separately, folded into the state most
# maps show, so a line that most maps don't draw doesn't count as a split.
FOLD = {"SOL": "SOM", "CYN": "CYP", "KAB": "KAZ"}

SOUTH_ASIA = {"IND", "PAK", "BGD", "AFG", "NPL", "BTN", "LKA", "MDV"}
FORMER_USSR = {
    "RUS", "UKR", "BLR", "MDA", "EST", "LVA", "LTU", "ARM", "AZE", "GEO",
    "KAZ", "KGZ", "TJK", "TKM", "UZB",
}  # fmt: skip
MENA_EXTRA = {"IRN", "TUR", "SDN"}


def region(a3: str, continent: str, subregion: str) -> str:
    """Story regions, by the country that holds most of a group's homeland."""
    if a3 in SOUTH_ASIA:
        return "South Asia"
    if a3 in FORMER_USSR:
        return "Former Soviet Union"
    if a3 in MENA_EXTRA or subregion in ("Western Asia", "Northern Africa"):
        return "Middle East and North Africa"
    if continent == "Africa":
        return "Sub-Saharan Africa"
    if subregion == "South America":
        return "South America"
    if subregion in ("Central America", "Caribbean"):
        return "Central America and Caribbean"
    if subregion == "Northern America":
        return "North America"
    if continent == "Europe":
        return "Europe"
    if continent == "Oceania":
        return "Oceania"
    return "East and Southeast Asia"


def load_countries() -> gpd.GeoDataFrame:
    RAW.mkdir(exist_ok=True)
    path = RAW / "ne_10m_admin_0_countries.geojson"
    if not path.exists():
        req = urllib.request.Request(NE_URL, headers={"User-Agent": "unexpected-signals"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            path.write_bytes(resp.read())
    ne = gpd.read_file(path)[["ADM0_A3", "NAME", "CONTINENT", "SUBREGION", "geometry"]]
    ne = ne[ne["CONTINENT"] != "Antarctica"]
    ne["ADM0_A3"] = ne["ADM0_A3"].replace(FOLD)
    return ne.dissolve("ADM0_A3", aggfunc="first").reset_index()


def neighbours(ne: gpd.GeoDataFrame) -> dict[frozenset, object]:
    """Land borders between countries, as simplified lines."""
    geo = ne.set_index("ADM0_A3").geometry
    pairs = {}
    for a, b in gpd.sjoin(ne, ne, predicate="intersects")[["ADM0_A3_left", "ADM0_A3_right"]].values:
        if a < b:
            line = geo[a].boundary.intersection(geo[b].buffer(0.01))
            if line.length > 0.05:
                pairs[frozenset((a, b))] = line.simplify(0.05)
    return pairs


def rnd(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 2), round(coords[1], 2)]
    return [rnd(c) for c in coords]


def feature(geom, props: dict) -> dict:
    g = geom.__geo_interface__
    geometry = {**g, "coordinates": rnd(g["coordinates"])}
    return {"type": "Feature", "properties": props, "geometry": geometry}


def main() -> None:
    src = Path(sys.argv[1])
    table = pd.read_csv(src / "group_country_area.csv", keep_default_na=False)
    ne = load_countries()
    names = dict(zip(ne["ADM0_A3"], ne["NAME"], strict=True))
    meta = ne.set_index("ADM0_A3")[["CONTINENT", "SUBREGION"]]
    borders = neighbours(ne)

    table["ADM0_A3"] = table["ADM0_A3"].replace(FOLD)
    table = table.groupby(["group_id", "group", "ADM0_A3"], as_index=False)["area_km2"].sum()
    table["share"] = table["area_km2"] / table.groupby("group_id")["area_km2"].transform("sum")

    groups, cut_pairs = [], {}
    for (_gid, name), g in table.groupby(["group_id", "group"]):
        g = g.sort_values("area_km2", ascending=False)
        main_a3 = g.iloc[0]["ADM0_A3"]
        big = list(g[g["share"] >= 0.10]["ADM0_A3"])
        cut = [frozenset(p) for p in combinations(big, 2) if frozenset(p) in borders]
        for p in cut:
            cut_pairs.setdefault(p, []).append((name, g["area_km2"].sum()))
        groups.append(
            {
                "group": name,
                "region": region(main_a3, *meta.loc[main_a3]),
                "split": int(bool(cut)),
                "countries": " · ".join(names[a] for a in big),
                "main_share": round(g.iloc[0]["share"] * 100),
                "area_km2": round(g["area_km2"].sum()),
            }
        )
    groups = pd.DataFrame(groups)

    OUT.mkdir(parents=True, exist_ok=True)
    by_region = (
        groups.groupby("region")
        .agg(groups=("split", "size"), split=("split", "sum"))
        .assign(share=lambda d: (d["split"] / d["groups"] * 100).round(1))
        .sort_values("share", ascending=False)
        .reset_index()
    )
    by_region.to_csv(OUT / "split_by_region.csv", index=False)
    split = groups[groups["split"] == 1].drop(columns="split")
    split.sort_values(["region", "area_km2"], ascending=[True, False]).to_csv(
        OUT / "split_groups.csv", index=False
    )

    pair_rows = []
    for p, cut in cut_pairs.items():
        a, b = sorted(p)
        biggest = [n for n, _ in sorted(cut, key=lambda x: -x[1])]
        pair_rows.append(
            {
                "border": f"{a}-{b}",
                "countries": f"{names[a]} – {names[b]}",
                "groups_cut": len(cut),
                "groups": ", ".join(biggest),
            }
        )
    pairs = pd.DataFrame(pair_rows).sort_values("groups_cut", ascending=False)
    pairs.to_csv(OUT / "border_cuts.csv", index=False)

    # A light base map: small islands dropped, outlines simplified. Areas in
    # square degrees are fine for a size cut-off.
    warnings.filterwarnings("ignore", "Geometry is in a geographic CRS")
    land = ne.explode(index_parts=False)
    land = land[land.geometry.area > 0.3].dissolve("ADM0_A3", aggfunc="first").reset_index()
    land["geometry"] = land.geometry.simplify(0.15)
    world = {
        "type": "FeatureCollection",
        "features": [
            feature(r.geometry, {"id": r.ADM0_A3, "name": r.NAME})
            for r in land.itertuples()
            if not r.geometry.is_empty
        ]
        + [
            feature(borders[frozenset(row.border.split("-"))], {"border": row.border})
            for row in pairs.itertuples()
        ],
    }
    (OUT / "world.json").write_text(json.dumps(world, separators=(",", ":")))

    print(by_region.to_string(index=False))
    print(f"\n{groups['split'].sum()} of {len(groups)} groups split")
    print(pairs.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
