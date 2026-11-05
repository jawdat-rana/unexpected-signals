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
    sites = out / "traffic_sites/2026/11/2026-11-05.csv"
    assert len(sites.read_text().splitlines()) == 3


def test_a_broken_feed_returns_non_zero(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text(
        '[bridges]\nenabled = true\nretries = 1\nurl = "file:///does/not/exist.xml"\n'
    )
    assert cli.main(["collect", "--config", str(config), "--out", str(tmp_path)]) == 1
