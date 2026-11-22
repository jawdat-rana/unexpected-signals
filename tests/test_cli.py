from pathlib import Path

from unexpected_signals import cli

FIXTURES = Path(__file__).parent / "fixtures"


def test_collect_end_to_end(tmp_path: Path, monkeypatch):
    config = tmp_path / "config.toml"
    config.write_text(
        f"""
[bridges]
enabled = true
url = "{(FIXTURES / "bridges_v3.xml").as_uri()}"

[traffic]
enabled = true
url = "{(FIXTURES / "traffic_v3.xml").as_uri()}"
catalogue_url = "{(FIXTURES / "sites_v3.xml").as_uri()}"
sites = ["RWS01_MONIBAS_0021hrl0403ra"]
"""
    )
    monkeypatch.setattr(cli, "now_iso", lambda: "2026-11-05T15:52:00Z")
    out = tmp_path / "data"

    assert cli.main(["collect", "--config", str(config), "--out", str(out)]) == 0
    assert cli.main(["collect", "--config", str(config), "--out", str(out)]) == 0

    bridges_csv = out / "bridges/2026/11/2026-11-05.csv"
    assert len(bridges_csv.read_text().splitlines()) == 3  # header + 2 records, deduplicated
    summary = out / "traffic_summary/2026/11/2026-11-05.csv"
    assert len(summary.read_text().splitlines()) == 3  # header + 2 snapshots
    sites = (out / "traffic_sites/2026/11/2026-11-05.csv").read_text().splitlines()
    assert len(sites) == 3
    assert sites[1].startswith("2026-11-05T15:52:00Z,RWS01_MONIBAS_0021hrl0403ra,")
    catalogue = out / "traffic_sites_catalogue.csv"
    assert len(catalogue.read_text().splitlines()) == 3  # header + 2 sites
    roads = (out / "traffic_roads/2026/11/2026-11-05.csv").read_text().splitlines()
    assert roads[0].startswith("fetched_at,road,")
    assert [line.split(",")[1] for line in roads[1:]] == ["A2", "A2"]  # one per snapshot


def test_catalogue_is_reused_until_it_is_a_week_old(tmp_path: Path, monkeypatch):
    calls = []
    real = cli.download
    monkeypatch.setattr(cli, "download", lambda url, retries=3: calls.append(url) or real(url))
    cfg = {"catalogue_url": (FIXTURES / "sites_v3.xml").as_uri()}
    cli.site_catalogue(cfg, tmp_path, "2026-11-05T00:00:00Z")
    cli.site_catalogue(cfg, tmp_path, "2026-11-11T23:00:00Z")
    assert len(calls) == 1
    cli.site_catalogue(cfg, tmp_path, "2026-11-12T00:00:00Z")
    assert len(calls) == 2


def test_a_broken_feed_returns_non_zero(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text(
        '[bridges]\nenabled = true\nretries = 1\nurl = "file:///does/not/exist.xml"\n'
    )
    assert cli.main(["collect", "--config", str(config), "--out", str(tmp_path)]) == 1
