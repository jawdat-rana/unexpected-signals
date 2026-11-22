from pathlib import Path

import pytest

from unexpected_signals import sites

FIXTURE = Path(__file__).parent / "fixtures" / "sites_v3.xml"


def test_parses_one_row_per_site():
    with FIXTURE.open("rb") as fh:
        rows = sites.parse(fh)
    assert [r.site_id for r in rows] == ["RWS01_MONIBAS_0021hrl0403ra", "PZH01_MST_0047_01"]
    a2, n208 = rows
    assert (a2.road, a2.lanes, a2.latitude, a2.longitude) == ("A2", 2, 52.2, 4.9)
    assert a2.carriageway == "mainCarriageway"
    assert (n208.name, n208.road) == ("N208 km 5.645 Li", "N208")


@pytest.mark.parametrize(
    ("site_id", "name", "road"),
    [
        ("RWS01_MONIBAS_0121hrl0358ra", None, "A12"),
        ("RWS01_MONIBAS_0020vwn0606ra", None, "A2"),
        ("RWS01_MONIBAS_2071hrl0100ra", None, "N207"),
        ("PFR07_101607_N354_Z", None, "N354"),
        ("PGL10_N787-02_hmp_12.5_Li_HTN2768", None, "N787"),
        ("PNH02_X", "A325 Arnhem", "N325"),
        ("GAD02_Amstd_31_0", "Michiel de Ruijtertunnel Richting West", None),
        ("RWS01_MONICA_00D0020A1014D0050009", None, None),
    ],
)
def test_road_of(site_id, name, road):
    assert sites.road_of(site_id, name) == road


def test_motorway_main_lanes_skips_slip_roads_and_n_roads():
    catalogue = [
        {"site_id": "a", "road": "A2", "carriageway": "mainCarriageway"},
        {"site_id": "b", "road": "A2", "carriageway": "exitSlipRoad"},
        {"site_id": "c", "road": "N208", "carriageway": "mainCarriageway"},
        {"site_id": "d", "road": "", "carriageway": "mainCarriageway"},
    ]
    assert sites.motorway_main_lanes(catalogue) == {"a": "A2"}
