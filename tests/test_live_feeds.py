"""Tests for the live feeds added in November 2026, using local file:// fixtures."""

import json
from pathlib import Path

from unexpected_signals import charts, cli, state, trends

TRENDS_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0"><channel>
<item><title>correia</title><ht:approx_traffic>200+</ht:approx_traffic>
<pubDate>Sun, 22 Nov 2026 12:40:00 -0800</pubDate>
<ht:news_item><ht:news_item_title>Kraay on Correia</ht:news_item_title>
<ht:news_item_url>https://example.org/a</ht:news_item_url>
<ht:news_item_source>LiveScore</ht:news_item_source></ht:news_item></item>
<item><title>sinterklaas</title><ht:approx_traffic>10K+</ht:approx_traffic>
<pubDate>Mon, 23 Nov 2026 01:00:00 +0000</pubDate></item>
</channel></rss>"""


def write(path: Path, data) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())
    return path.as_uri()


def lines(path: Path) -> list[str]:
    return path.read_text().splitlines()


def test_traffic_floor():
    assert trends.traffic_floor("200+") == 200
    assert trends.traffic_floor("10K+") == 10_000
    assert trends.traffic_floor("2M+") == 2_000_000
    assert trends.traffic_floor(None) == 0


def test_trends_merge_keeps_first_seen_and_top_band(tmp_path: Path):
    src = tmp_path / "t.xml"
    src.write_bytes(TRENDS_RSS)
    first = trends.parse(src.open("rb"), "NL", "2026-11-22T21:00:00Z")
    assert first[0]["started"] == "2026-11-22T20:40:00Z"
    later = [dict(r, approx_traffic="100+", traffic_min=100) for r in first]
    later = [dict(r, last_seen="2026-11-22T22:00:00Z") for r in later]
    merged = trends.merge(first, later)
    assert len(merged) == 2
    row = next(r for r in merged if r["title"] == "correia")
    assert row["first_seen"] == "2026-11-22T21:00:00Z"
    assert row["last_seen"] == "2026-11-22T22:00:00Z"
    assert row["approx_traffic"] == "200+"


def test_charts_parse_ranks_in_order():
    payload = {
        "feed": {
            "results": [
                {
                    "id": "1",
                    "name": "ChatGPT",
                    "artistName": "OpenAI",
                    "genres": [{"name": "Productivity"}],
                },
                {"id": "2", "name": "Woolsocks", "artistName": "Woolsocks AG"},
            ]
        }
    }
    rows = charts.parse(payload, "nl", "apps-free", "T")
    assert [(r["rank"], r["name"], r["genre"]) for r in rows] == [
        (1, "ChatGPT", "Productivity"),
        (2, "Woolsocks", None),
    ]
    assert charts.url("nl", "songs", 100).endswith("/nl/music/most-played/100/songs.json")


def test_is_due_with_slack():
    assert state.is_due(None, "2026-11-22T10:00:00Z", 60)
    assert not state.is_due("2026-11-22T10:00:00Z", "2026-11-22T10:30:00Z", 60)
    assert state.is_due("2026-11-22T10:00:00Z", "2026-11-22T10:58:30Z", 60)


def test_collect_new_feeds_end_to_end(tmp_path: Path, monkeypatch):
    src = tmp_path / "src"
    dyn_ok = write(
        src / "dyn1.json",
        {
            "parkingFacilityDynamicInformation": {
                "identifier": "p1",
                "name": "Forum",
                "facilityActualStatus": {
                    "open": True,
                    "full": True,
                    "parkingCapacity": 340,
                    "vacantSpaces": 1,
                    "lastUpdated": 1795107992,
                },
            }
        },
    )
    static = write(
        src / "static1.json",
        {
            "parkingFacilityInformation": {
                "identifier": "p1",
                "name": "Forum",
                "limitedAccess": False,
                "specifications": [
                    {"validityStartOfPeriod": 1, "capacity": 300, "usage": "garage"},
                    {"validityStartOfPeriod": 2, "capacity": 340, "usage": "garage"},
                ],
                "operator": {"name": "Groningen"},
                "accessPoints": [
                    {
                        "accessPointAddress": {"city": "Groningen", "province": "Groningen"},
                        "accessPointLocation": [{"latitude": 53.2, "longitude": 6.5}],
                    }
                ],
            }
        },
    )
    index = write(
        src / "index.json",
        {
            "ParkingFacilities": [
                {
                    "identifier": "p1",
                    "name": "Forum",
                    "staticDataUrl": static,
                    "dynamicDataUrl": dyn_ok,
                    "limitedAccess": False,
                },
                {
                    "identifier": "p2",
                    "name": "Private",
                    "staticDataUrl": static,
                    "dynamicDataUrl": "file:///nope.json",
                    "limitedAccess": True,
                },
                {"identifier": "p3", "name": "Static only", "staticDataUrl": static},
            ]
        },
    )
    apple = write(
        src / "nl/apps/top-free/2/apps.json",
        {"feed": {"results": [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]}},
    )
    apple_base = apple.split("nl/apps/")[0]
    write(src / "trends_NL.xml", TRENDS_RSS)
    ov = write(
        src / "ov.json",
        {
            "locaties": {
                "utt001": {
                    "description": "Utrecht Terwijde",
                    "city": "Vleuten",
                    "stationCode": "UTT",
                    "lat": 52.1,
                    "lng": 5.04,
                    "open": "Yes",
                    "extra": {
                        "rentalBikes": "7",
                        "locationCode": "utt001",
                        "fetchTime": 1795381095,
                    },
                }
            }
        },
    )
    config = tmp_path / "config.toml"
    config.write_text(f"""
[parking]
enabled = true
every_minutes = 10
url = "{index}"
[apple_charts]
enabled = true
every_minutes = 180
base = "{apple_base}"
countries = ["nl"]
charts = ["apps-free"]
size = 2
[google_trending]
enabled = true
url = "{src.as_uri()}/trends_{{geo}}.xml"
geos = ["NL"]
[ovfiets]
enabled = true
url = "{ov}"
""")
    out = tmp_path / "data"
    stamps = iter(["2026-11-22T21:00:00Z", "2026-11-22T21:05:00Z", "2026-11-22T21:15:00Z"])
    monkeypatch.setattr(cli, "now_iso", lambda: next(stamps))
    for _ in range(3):
        assert cli.main(["collect", "--config", str(config), "--out", str(out)]) == 0

    parking_rows = lines(out / "parking/2026/11/2026-11-22.csv")
    assert len(parking_rows) == 2  # header + one row: the status never changed
    assert parking_rows[1].startswith("2026-11-22T21:00:00Z,p1,True,True,340,1,")
    catalogue = lines(out / "parking_catalogue.csv")
    assert catalogue[1] == "p1,Forum,Groningen,Groningen,53.2,6.5,340,garage,Groningen,False"

    # Apple charts every 180 min: only the first run is due.
    assert len(lines(out / "apple_charts/2026/11/2026-11-22.csv")) == 3
    # Trends run every time but merge into one row per trend, filed by start day.
    assert len(lines(out / "google_trending/2026/11/2026-11-22.csv")) == 2
    assert len(lines(out / "google_trending/2026/11/2026-11-23.csv")) == 2
    assert len(lines(out / "ovfiets/2026/11/2026-11-22.csv")) == 2  # unchanged count
    ov_catalogue = lines(out / "ovfiets_catalogue.csv")
    assert ov_catalogue[1] == "utt001,UTT,Utrecht Terwijde,Vleuten,52.1,5.04"
    schedule = state.load(out, "schedule")
    assert schedule["apple_charts"] == "2026-11-22T21:00:00Z"
    assert schedule["parking"] == "2026-11-22T21:15:00Z"


SHAZAM_CSV = (
    '﻿\n"Monday, 23 November 2026 [performance over the past 7 days]"\n'
    'Rank,Artist,Title\n1,"Justice & Tame Impala","Flower In A Hurricane"\n'
    '2,"Isabèl Usher & Kraantje Pappie","Spijt Komt Later"\n'
).encode()


def test_shazam_parse_reads_chart_date():
    from unexpected_signals import shazam

    day, rows = shazam.parse(SHAZAM_CSV, "netherlands", "2026-11-24T01:00:00Z")
    assert day == "2026-11-23"
    assert [(r["rank"], r["title"]) for r in rows] == [
        ("1", "Flower In A Hurricane"),
        ("2", "Spijt Komt Later"),
    ]


def test_shazam_refetch_replaces_rows(tmp_path: Path):
    write(tmp_path / "src/netherlands", SHAZAM_CSV)
    config = tmp_path / "config.toml"
    config.write_text(
        f'[shazam]\nenabled = true\nbase = "{(tmp_path / "src").as_uri()}/"\n'
        'charts = ["netherlands"]\n'
    )
    out = tmp_path / "data"
    for _ in range(2):
        assert cli.main(["collect", "--config", str(config), "--out", str(out)]) == 0
    assert len(lines(out / "shazam/2026/11/2026-11-23.csv")) == 3


def test_partly_failed_feed_warns_and_waits_for_its_next_slot(tmp_path: Path, monkeypatch, capsys):
    src = tmp_path / "src"
    apple = write(
        src / "nl/apps/top-free/2/apps.json",
        {"feed": {"results": [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]}},
    )
    config = tmp_path / "config.toml"
    config.write_text(f"""
[apple_charts]
enabled = true
every_minutes = 180
retries = 1
base = "{apple.split("nl/apps/")[0]}"
countries = ["nl", "be"]
charts = ["apps-free"]
size = 2
""")
    out = tmp_path / "data"
    stamps = iter(["2026-11-24T10:40:00Z", "2026-11-24T10:45:00Z"])
    monkeypatch.setattr(cli, "now_iso", lambda: next(stamps))
    for _ in range(2):
        assert cli.main(["collect", "--config", str(config), "--out", str(out)]) == 0

    # "be" is missing: nl is saved once and the feed is not re-fetched 5 min later.
    assert len(lines(out / "apple_charts/2026/11/2026-11-24.csv")) == 3
    assert state.load(out, "schedule")["apple_charts"] == "2026-11-24T10:40:00Z"
    assert "::warning title=apple_charts partly failed::" in capsys.readouterr().err


def test_fully_failed_feed_still_fails_the_run(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text(
        '[apple_charts]\nenabled = true\nretries = 1\nbase = "file:///nope/"\ncountries = ["nl"]\n'
    )
    assert cli.main(["collect", "--config", str(config), "--out", str(tmp_path / "d")]) == 1
