import json
from datetime import UTC, datetime

from unexpected_signals import health


def _data(tmp_path, schedule):
    data = tmp_path / "data"
    (data / "_state").mkdir(parents=True)
    (data / "_state" / "schedule.json").write_text(json.dumps(schedule))
    day = data / "bridges" / "2026" / "11"
    day.mkdir(parents=True)
    (day / "2026-11-22.csv").write_text("a\n1\n2\n3\n")
    return data


CONFIG = {
    "bridges": {"enabled": True},
    "shazam": {"enabled": True, "every_minutes": 360},
    "parking": {"enabled": False},
}


def test_quiet_feeds_are_flagged(tmp_path):
    now = datetime(2026, 11, 23, 12, tzinfo=UTC)
    data = _data(
        tmp_path,
        # bridges: 7 h ago, past the 6 h floor. shazam: 10 h ago, under 3 x 6 h.
        {"bridges": "2026-11-23T05:00:00Z", "shazam": "2026-11-23T02:00:00Z"},
    )
    text, quiet = health.report(CONFIG, data, now)
    assert quiet == ["bridges"]
    assert "**Quiet feeds:** bridges" in text
    assert "| bridges | 0 | 0 | 0 | 0 | 0 | 0 | 3 |" in text
    assert "parking" not in text


def test_run_gaps(tmp_path):
    now = datetime(2026, 11, 23, 12, tzinfo=UTC)
    runs = [
        {"created_at": "2026-11-23T10:00:00Z", "conclusion": "success"},
        {"created_at": "2026-11-23T10:05:00Z", "conclusion": "failure"},
        {"created_at": "2026-11-23T11:35:00Z", "conclusion": "success"},
        {"created_at": "2026-11-01T00:00:00Z", "conclusion": "failure"},  # too old
    ]
    path = tmp_path / "runs.json"
    path.write_text(json.dumps([{"workflow_runs": runs[:2]}, {"workflow_runs": runs[2:]}]))
    data = _data(tmp_path, {"bridges": "2026-11-23T11:55:00Z", "shazam": "2026-11-23T11:00:00Z"})
    text, quiet = health.report(CONFIG, data, now, health.load_runs(path))
    assert quiet == []
    assert "3 runs, 1 failed, longest gap between runs 1.5 h" in text
