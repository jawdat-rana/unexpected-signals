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


def test_failing_workflows_and_stale_pulls_need_a_look(tmp_path):
    now = datetime(2026, 11, 30, 6, tzinfo=UTC)
    data = _data(tmp_path, {"bridges": "2026-11-30T05:55:00Z", "shazam": "2026-11-30T05:00:00Z"})
    runs = [
        # collect failed once, then recovered: listed, no alarm.
        {
            "name": "collect",
            "created_at": "2026-11-27T09:20:00Z",
            "conclusion": "failure",
            "head_branch": "main",
            "html_url": "https://example.test/1",
        },
        {
            "name": "collect",
            "created_at": "2026-11-27T09:25:00Z",
            "conclusion": "success",
            "head_branch": "main",
        },
        # pages still failing on main: alarm.
        {
            "name": "pages",
            "created_at": "2026-11-29T05:17:00Z",
            "conclusion": "failure",
            "head_branch": "main",
        },
        # ci failed on a PR branch only: listed, no alarm.
        {
            "name": "ci",
            "created_at": "2026-11-28T10:00:00Z",
            "conclusion": "failure",
            "head_branch": "some-branch",
        },
        {
            "name": "ci",
            "created_at": "2026-11-28T11:00:00Z",
            "conclusion": "success",
            "head_branch": "main",
        },
    ]
    pulls = [
        {
            "number": 30,
            "title": "Old draft",
            "draft": True,
            "created_at": "2026-11-10T00:00:00Z",
            "updated_at": "2026-11-12T00:00:00Z",
        },
        {
            "number": 33,
            "title": "Busy",
            "created_at": "2026-11-20T00:00:00Z",
            "updated_at": "2026-11-29T00:00:00Z",
        },
        {
            "number": 34,
            "title": "New",
            "created_at": "2026-11-27T00:00:00Z",
            "updated_at": "2026-11-27T00:00:00Z",
        },
    ]
    text, alerts = health.report(CONFIG, data, now, None, 7, runs, pulls)
    assert alerts == ["workflow pages is failing on main", "PR #30 untouched for 2+ weeks"]
    assert "| collect | 1 | [Fri 27 Nov 09:20](https://example.test/1) | ok |" in text
    assert "| pages | 1 | Sun 29 Nov 05:17 | failed ⚠️ |" in text
    assert "| ci | 1 |" in text
    assert "#30 Old draft" in text and "(draft), open 20 days ⚠️" in text
    assert "#33 Busy" in text and "#34" not in text


def test_all_clear(tmp_path):
    now = datetime(2026, 11, 30, 6, tzinfo=UTC)
    data = _data(tmp_path, {"bridges": "2026-11-30T05:55:00Z", "shazam": "2026-11-30T05:00:00Z"})
    text, alerts = health.report(CONFIG, data, now, None, 7, [], [])
    assert alerts == []
    assert "Nothing needs a look this week." in text
    assert "No failed runs." in text
