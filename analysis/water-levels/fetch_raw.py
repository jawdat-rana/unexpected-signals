"""Download Rijkswaterstaat water levels for the national water replay.

Rijkswaterstaat publishes measured water heights (WATHTE, cm relative to NAP,
every 10 minutes) for a few hundred stations through its waterwebservices.
The data is open (CC0, "bron: Rijkswaterstaat"). In 2025 the service moved to
a new host ("DD-API 2.0"); this script tries the new host first and falls back
to the old one, so it keeps working either way.

Steps:
1. Fetch the catalogue and keep every station that measures water height in
   surface water (catalogue.csv), so stations can be picked by name.
2. For each station in STATIONS (matched on name), fetch the measured water
   height over the replay window and write one CSV per station.

Standard library only. Runs in GitHub Actions (the RWS hosts are not reachable
from every environment) and writes into OUT_DIR:

    catalogue.csv         code,name,x,y,crs,lat,lon   every WATHTE station
    stations.csv          key,code,name,lat,lon,rows   the stations fetched
    levels/<key>.csv      time,cm                      UTC, cm relative to NAP
    log.md                what happened, for the run summary

    python analysis/water-levels/fetch_raw.py OUT_DIR
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOSTS = [
    # (name, metadata base, observations base)
    (
        "ddapi20",
        "https://ddapi20-waterwebservices.rijkswaterstaat.nl/METADATASERVICES/",
        "https://ddapi20-waterwebservices.rijkswaterstaat.nl/ONLINEWAARNEMINGENSERVICES/",
    ),
    (
        "classic",
        "https://waterwebservices.rijkswaterstaat.nl/METADATASERVICES_DBO/",
        "https://waterwebservices.rijkswaterstaat.nl/ONLINEWAARNEMINGENSERVICES_DBO/",
    ),
]
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "unexpected-signals (github.com/jawdat-rana/unexpected-signals)",
}

# Storm Pia (21-22 Dec 2023, storm barriers closed) and the Christmas 2023 /
# New Year 2024 high water on the Rhine and Meuse.
START = dt.datetime(2023, 12, 18, tzinfo=dt.UTC)
END = dt.datetime(2024, 1, 9, tzinfo=dt.UTC)
# Requests are split into chunks so none hits the service's size limit.
CHUNK = dt.timedelta(days=4)

# key: name patterns tried in order against catalogue names (case-insensitive,
# whole-name match first, then substring). Keys are what the page uses.
STATIONS = {
    # Coast, south to north and east
    "vlissingen": ["Vlissingen"],
    "westkapelle": ["Westkapelle"],
    "roompot-buiten": ["Roompot buiten"],
    "roompot-binnen": ["Roompot binnen"],
    "haringvliet-buiten": ["Haringvlietsluizen buiten", "Haringvliet 10", "Haringvliet"],
    "hoek-van-holland": ["Hoek van Holland"],
    "scheveningen": ["Scheveningen"],
    "ijmuiden": ["IJmuiden buitenhaven", "IJmuiden"],
    "petten": ["Petten zuid", "Petten"],
    "den-helder": ["Den Helder"],
    "oudeschild": ["Oudeschild"],
    "den-oever": ["Den Oever buiten", "Den Oever"],
    "kornwerderzand": ["Kornwerderzand buiten", "Kornwerderzand"],
    "harlingen": ["Harlingen"],
    "vlieland": ["Vlieland haven", "Vlieland"],
    "terschelling": ["West-Terschelling", "Terschelling"],
    "nes": ["Nes"],
    "schiermonnikoog": ["Schiermonnikoog"],
    "lauwersoog": ["Lauwersoog"],
    "eemshaven": ["Eemshaven"],
    "delfzijl": ["Delfzijl"],
    "nieuwe-statenzijl": ["Nieuwe Statenzijl"],
    # Western Scheldt
    "terneuzen": ["Terneuzen"],
    "hansweert": ["Hansweert"],
    "bath": ["Bath"],
    # Rotterdam and the rivers' mouths
    "maassluis": ["Maassluis"],
    "vlaardingen": ["Vlaardingen"],
    "rotterdam": ["Rotterdam"],
    "spijkenisse": ["Spijkenisse"],
    "krimpen": ["Krimpen a/d IJssel", "Krimpen aan de IJssel", "Krimpen"],
    "dordrecht": ["Dordrecht"],
    "moerdijk": ["Moerdijk"],
    "goidschalxoord": ["Goidschalxoord"],
    # Rhine and Waal
    "lobith": ["Lobith"],
    "pannerdense-kop": ["Pannerdense Kop", "Pannerden"],
    "nijmegen": ["Nijmegen haven", "Nijmegen"],
    "tiel": ["Tiel Waal", "Tiel"],
    "zaltbommel": ["Zaltbommel"],
    "vuren": ["Vuren"],
    # Nederrijn and Lek
    "arnhem": ["Arnhem"],
    "driel": ["Driel boven", "Driel"],
    "amerongen": ["Amerongen boven", "Amerongen"],
    "hagestein": ["Hagestein boven", "Hagestein"],
    "schoonhoven": ["Schoonhoven"],
    # IJssel
    "westervoort": ["Westervoort"],
    "zutphen": ["Zutphen"],
    "deventer": ["Deventer"],
    "olst": ["Olst"],
    "kampen": ["Kampen"],
    # Meuse
    "eijsden": ["Eijsden grens", "Eijsden"],
    "maastricht": ["Sint Pieter", "Maastricht"],
    "roermond": ["Roermond boven", "Roermond"],
    "venlo": ["Venlo"],
    "grave": ["Grave beneden", "Grave"],
    "lith": ["Lith boven", "Lith"],
    "heesbeen": ["Heesbeen"],
    "keizersveer": ["Keizersveer"],
}


log_lines: list[str] = []


def log(message: str) -> None:
    print(message, flush=True)
    log_lines.append(message)


def post(url: str, body: dict, tries: int = 4) -> dict:
    data = json.dumps(body).encode()
    for attempt in range(tries):
        request = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")[:500]
            # 204 / 4xx with a message usually means "no data", not a hiccup.
            if exc.code < 500:
                raise RuntimeError(f"HTTP {exc.code}: {text}") from exc
            error: Exception = RuntimeError(f"HTTP {exc.code}: {text}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            error = exc
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url}: {error}")


def iso(moment: dt.datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")


# --- Coordinates ----------------------------------------------------------------


def utm31_to_latlon(x: float, y: float) -> tuple[float, float]:
    """ETRS89 / UTM zone 31N (EPSG:25831) to latitude and longitude."""
    a, f, k0 = 6378137.0, 1 / 298.257222101, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x -= 500000.0
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
    )
    n1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    t1 = math.tan(phi1) ** 2
    c1 = ep2 * math.cos(phi1) ** 2
    r1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lon = (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / math.cos(phi1)
    return math.degrees(lat), 3 + math.degrees(lon)


def latlon(loc: dict) -> tuple[float | None, float | None]:
    for la, lo in (("Lat", "Lon"), ("Latitude", "Longitude")):
        if loc.get(la) is not None and loc.get(lo) is not None:
            return float(loc[la]), float(loc[lo])
    x, y = loc.get("X"), loc.get("Y")
    if x is None or y is None:
        return None, None
    crs = str(loc.get("Coordinatenstelsel", ""))
    x, y = float(x), float(y)
    if "25831" in crs or (x > 100000 and y > 5000000):
        return utm31_to_latlon(x, y)
    if "4258" in crs or "4326" in crs or abs(y) <= 90:
        # Some services give lon in X and lat in Y.
        return (y, x) if abs(y) > abs(x) else (x, y)
    return None, None


# --- Catalogue -------------------------------------------------------------------


def catalogue() -> tuple[str, str, list[dict]]:
    """The first host that answers, its observations base, and the stations
    that measure water height in surface water."""
    body = {
        "CatalogusFilter": {
            "Grootheden": True,
            "Compartimenten": True,
            "Hoedanigheden": True,
            "Eenheden": True,
            "Parameters": True,
            "ProcesTypes": True,
        }
    }
    for name, meta, obs in HOSTS:
        try:
            result = post(meta + "OphalenCatalogus", body)
        except Exception as exc:  # noqa: BLE001
            log(f"- catalogue on {name}: failed ({exc})")
            continue
        keys = ", ".join(sorted(result))
        log(f"- catalogue on {name}: ok, keys {keys}")
        aquo = {a.get("AquoMetadata_MessageID"): a for a in result.get("AquoMetadataLijst", [])}
        locs = {loc.get("Locatie_MessageID"): loc for loc in result.get("LocatieLijst", [])}
        links = result.get("AquoMetadataLocatieLijst", [])
        if locs:
            sample = next(iter(locs.values()))
            log(f"- sample location: {json.dumps(sample)[:400]}")
        wanted = set()
        for link in links:
            meta_item = aquo.get(link.get("AquoMetaData_MessageID", link.get("AquoMetadata_MessageID")))
            if not meta_item:
                continue
            grootheid = (meta_item.get("Grootheid") or {}).get("Code")
            compartiment = (meta_item.get("Compartiment") or {}).get("Code")
            if grootheid == "WATHTE" and compartiment == "OW":
                wanted.add(link.get("Locatie_MessageID"))
        stations = [locs[i] for i in wanted if i in locs]
        if not links:
            log("- no AquoMetadataLocatieLijst: keeping every location")
            stations = list(locs.values())
        log(f"- {len(stations)} locations measure WATHTE in OW (of {len(locs)})")
        return name, obs, stations
    raise SystemExit("No Rijkswaterstaat host answered the catalogue request.")


def match(stations: list[dict], patterns: list[str]) -> dict | None:
    def norm(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip().lower()

    for pattern in patterns:
        p = norm(pattern)
        exact = [s for s in stations if norm(s.get("Naam")) == p]
        if exact:
            return exact[0]
    for pattern in patterns:
        p = norm(pattern)
        partial = sorted(
            (s for s in stations if p in norm(s.get("Naam"))), key=lambda s: len(s.get("Naam", ""))
        )
        if partial:
            return partial[0]
    return None


# --- Observations ------------------------------------------------------------------


def location_filter(loc: dict) -> dict:
    keep = {k: loc[k] for k in ("Code", "X", "Y") if loc.get(k) is not None}
    return keep or {"Code": loc.get("Code")}


def measurements(obs: str, loc: dict) -> dict[str, float]:
    values: dict[str, float] = {}
    start = START
    first_error = ""
    while start < END:
        stop = min(start + CHUNK, END)
        body = {
            "Locatie": location_filter(loc),
            "AquoPlusWaarnemingMetadata": {
                "AquoMetadata": {"Compartiment": {"Code": "OW"}, "Grootheid": {"Code": "WATHTE"}}
            },
            "Periode": {"Begindatumtijd": iso(start), "Einddatumtijd": iso(stop)},
        }
        try:
            result = post(obs + "OphalenWaarnemingen", body)
        except Exception as exc:  # noqa: BLE001
            first_error = first_error or str(exc)[:300]
            start = stop
            continue
        for series in result.get("WaarnemingenLijst", []):
            aquo = series.get("AquoMetadata", {})
            # Keep measurements only: not forecasts or astronomical tide.
            proces = str(aquo.get("ProcesType", "")).lower()
            if proces and proces != "meting":
                continue
            hoedanigheid = (aquo.get("Hoedanigheid") or {}).get("Code", "NAP")
            if hoedanigheid not in ("NAP", ""):
                continue
            for item in series.get("MetingenLijst", []):
                value = (item.get("Meetwaarde") or {}).get("Waarde_Numeriek")
                stamp = item.get("Tijdstip")
                # 999999999 marks a missing value.
                if value is None or stamp is None or abs(float(value)) > 10000:
                    continue
                moment = dt.datetime.fromisoformat(stamp).astimezone(dt.UTC)
                values[moment.strftime("%Y-%m-%dT%H:%MZ")] = float(value)
        start = stop
        time.sleep(0.3)
    if not values and first_error:
        log(f"  first error: {first_error}")
    return values


def main(argv: list[str]) -> int:
    out = Path(argv[1] if len(argv) > 1 else "raw")
    (out / "levels").mkdir(parents=True, exist_ok=True)
    log(f"# Water levels {START:%Y-%m-%d} to {END:%Y-%m-%d}\n")
    host, obs, stations = catalogue()

    with (out / "catalogue.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name", "x", "y", "crs", "lat", "lon"])
        for loc in sorted(stations, key=lambda s: str(s.get("Naam"))):
            lat, lon = latlon(loc)
            writer.writerow([
                loc.get("Code"), loc.get("Naam"), loc.get("X"), loc.get("Y"),
                loc.get("Coordinatenstelsel"),
                f"{lat:.5f}" if lat is not None else "", f"{lon:.5f}" if lon is not None else "",
            ])  # fmt: skip

    rows = []
    for key, patterns in STATIONS.items():
        loc = match(stations, patterns)
        if not loc:
            log(f"- {key}: no station named like {patterns}")
            continue
        values = measurements(obs, loc)
        lat, lon = latlon(loc)
        log(f"- {key}: {loc.get('Naam')} ({loc.get('Code')}), {len(values)} values")
        if not values:
            continue
        with (out / "levels" / f"{key}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "cm"])
            for stamp in sorted(values):
                writer.writerow([stamp, f"{values[stamp]:g}"])
        rows.append([key, loc.get("Code"), loc.get("Naam"),
                     f"{lat:.5f}" if lat is not None else "",
                     f"{lon:.5f}" if lon is not None else "", len(values)])  # fmt: skip

    with (out / "stations.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "code", "name", "lat", "lon", "rows"])
        writer.writerows(rows)
    log(f"\nHost: {host}. Fetched {len(rows)} of {len(STATIONS)} stations.")
    (out / "log.md").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
