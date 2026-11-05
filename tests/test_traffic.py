from pathlib import Path

from unexpected_signals import traffic

FIXTURE = Path(__file__).parent / "fixtures" / "traffic_v3.xml"


def parse():
    with FIXTURE.open("rb") as fh:
        return traffic.parse(fh)


def test_collapses_lanes_to_one_row_per_site():
    rows = parse()
    assert len(rows) == 2
    site = rows[0]
    assert site.site_id == "RWS01_MONIBAS_0021hrl0403ra"
    assert site.measured_at == "2026-11-05T15:45:00Z"
    assert site.speed_kmh == 95.0
    assert site.flow_veh_h == 2000
    assert (site.lanes_with_speed, site.lanes_with_flow) == (2, 2)


def test_negative_values_mean_no_data():
    empty = parse()[1]
    assert empty.speed_kmh is None
    assert empty.flow_veh_h is None


def test_summary_and_selection():
    rows = parse()
    summary = traffic.summarise(rows, "2026-11-05T15:52:00Z")
    assert summary["sites_reporting"] == 2
    assert summary["sites_with_speed"] == 1
    assert summary["mean_speed_kmh"] == 95.0
    assert summary["total_flow_veh_h"] == 2000
    assert len(traffic.select(rows, {"RWS01_MONIBAS_0021hrl0403ra"})) == 1
