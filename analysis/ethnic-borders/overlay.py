"""Overlay the GREG ethnic-group map on today's country borders.

Downloads GREG (Weidmann, Rød and Cederman 2010, a digitised version of the
1964 Soviet "Atlas Narodov Mira") and Natural Earth's 1:10m countries, and
measures how much of each group's homeland lies in each country.

Only derived tables are written: area in km² per group and country, and a
summary per group. The GREG polygons themselves are not redistributed, since
GREG states no licence beyond a citation request.

GitHub Actions runs this (`borders-overlay` workflow) because the GREG host is
not reachable from every network. Needs geopandas.

Usage: python analysis/ethnic-borders/overlay.py OUT_DIR
"""

from __future__ import annotations

import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid

GREG_URL = "https://icr.ethz.ch/data/greg/GREG.zip"
NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_10m_admin_0_countries.geojson"
)
HEADERS = {"User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)"}

# World Cylindrical Equal Area, so areas are comparable everywhere.
EQUAL_AREA = "EPSG:6933"
# A country counts as holding part of a group's homeland from this share up.
# Michalopoulos and Papaioannou (2016) use 10%; slivers below that are mostly
# mismatches between a 1964 map and modern borders.
SPLIT_SHARE = 0.10
COUNTRY_FIELDS = ["ADM0_A3", "NAME", "CONTINENT", "SUBREGION"]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def load_greg(raw: Path) -> gpd.GeoDataFrame:
    zip_path = raw / "GREG.zip"
    if not zip_path.exists():
        zip_path.write_bytes(fetch(GREG_URL))
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(raw / "greg")
    shp = next((raw / "greg").rglob("*.shp"))
    greg = gpd.read_file(shp)
    if greg.crs is None:
        greg = greg.set_crs("EPSG:4326")
    print(f"GREG: {len(greg)} polygons, columns {list(greg.columns)}")
    return greg


def load_countries(raw: Path) -> gpd.GeoDataFrame:
    path = raw / "ne_10m_admin_0_countries.geojson"
    if not path.exists():
        path.write_bytes(fetch(NE_URL))
    countries = gpd.read_file(path)[COUNTRY_FIELDS + ["geometry"]]
    print(f"Natural Earth: {len(countries)} countries")
    return countries


def group_rows(greg: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """One row per (polygon, group). A polygon can hold up to three groups,
    and each of them counts as living there, as in the GREG paper."""
    parts = []
    for i in (1, 2, 3):
        part = greg[[f"G{i}ID", f"G{i}SHORTNAM", "geometry"]].copy()
        part.columns = ["group_id", "group", "geometry"]
        part = part[part["group_id"].fillna(0).astype(int) > 0]
        parts.append(part)
    rows = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=greg.crs)
    rows["group_id"] = rows["group_id"].astype(int)
    rows["group"] = rows["group"].astype(str).str.strip()
    return rows


def clean(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.to_crs(EQUAL_AREA)
    gdf["geometry"] = gdf.geometry.apply(make_valid)
    gdf = gdf.explode(index_parts=False)
    return gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])]


def overlay(groups: gpd.GeoDataFrame, countries: gpd.GeoDataFrame) -> pd.DataFrame:
    pieces = gpd.overlay(groups, countries, how="intersection", keep_geom_type=True)
    pieces["area_km2"] = pieces.geometry.area / 1e6
    table = (
        pieces.groupby(["group_id", "group", *COUNTRY_FIELDS], as_index=False)["area_km2"]
        .sum()
        .sort_values(["group_id", "area_km2"], ascending=[True, False])
    )
    total = table.groupby("group_id")["area_km2"].transform("sum")
    table["share"] = table["area_km2"] / total
    return table


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (gid, name), g in table.groupby(["group_id", "group"], sort=False):
        g = g.sort_values("area_km2", ascending=False)
        big = g[g["share"] >= SPLIT_SHARE]
        first = g.iloc[0]
        second = g.iloc[1] if len(g) > 1 else None
        out.append(
            {
                "group_id": gid,
                "group": name,
                "area_km2": round(g["area_km2"].sum()),
                "countries_10pct": len(big),
                "split": int(len(big) >= 2),
                "main_country": first["ADM0_A3"],
                "main_country_name": first["NAME"],
                "main_share": round(first["share"], 4),
                "continent": first["CONTINENT"],
                "subregion": first["SUBREGION"],
                "second_country": "" if second is None else second["ADM0_A3"],
                "second_share": 0 if second is None else round(second["share"], 4),
                "countries_10pct_list": " ".join(big["ADM0_A3"]),
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    out = Path(sys.argv[1])
    raw = out / "_tmp"
    raw.mkdir(parents=True, exist_ok=True)

    greg = load_greg(raw)
    countries = clean(load_countries(raw))
    groups = clean(group_rows(greg))
    table = overlay(groups, countries)
    summary = summarise(table)

    table["area_km2"] = table["area_km2"].round(1)
    table["share"] = table["share"].round(4)
    table.to_csv(out / "group_country_area.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    summary.to_csv(out / "groups.csv", index=False)

    buf = io.StringIO()
    by_sub = summary.groupby("subregion").agg(groups=("split", "size"), split=("split", "sum"))
    by_sub["share_split"] = (by_sub["split"] / by_sub["groups"]).round(3)
    by_sub.sort_values("share_split", ascending=False).to_csv(buf)
    (out / "summary_by_subregion.csv").write_text(buf.getvalue())
    print(buf.getvalue())
    print(f"{summary['split'].sum()} of {len(summary)} groups split at {SPLIT_SHARE:.0%}")


if __name__ == "__main__":
    main()
