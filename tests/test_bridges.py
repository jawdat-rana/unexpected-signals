from pathlib import Path

from unexpected_signals import bridges

FIXTURE = Path(__file__).parent / "fixtures" / "bridges_v3.xml"


def parse(fetched_at="2026-11-05T10:07:00Z"):
    with FIXTURE.open("rb") as fh:
        return bridges.parse(fh, fetched_at)


def test_parses_each_situation_record():
    records = parse()
    assert [r.record_id for r in records] == ["REC_1", "REC_2"]
    first = records[0]
    assert first.situation_id == "NLRWS_BRUG_1"
    assert first.record_type == "GeneralNetworkManagement"
    assert first.management_type == "bridgeSwingInOperation"
    assert first.validity_status == "active"
    assert first.start_time == "2026-11-05T10:00:00Z"
    assert first.end_time == "2026-11-05T10:12:00Z"
    assert (first.latitude, first.longitude) == (52.0901, 5.1214)


def test_missing_fields_are_none():
    planned = parse()[1]
    assert planned.end_time is None
    assert planned.latitude is None
    assert planned.validity_status == "planned"


def test_merge_keeps_first_seen_and_updates_the_rest():
    earlier = [r.as_row() for r in parse("2026-11-05T10:07:00Z")]
    earlier = [{k: "" if v is None else str(v) for k, v in row.items()} for row in earlier]
    later = parse("2026-11-05T10:22:00Z")
    later[0].validity_status = "suspended"

    merged = bridges.merge(earlier, later)

    assert len(merged) == 2
    rec = next(r for r in merged if r["record_id"] == "REC_1")
    assert rec["first_seen"] == "2026-11-05T10:07:00Z"
    assert rec["last_seen"] == "2026-11-05T10:22:00Z"
    assert rec["validity_status"] == "suspended"
