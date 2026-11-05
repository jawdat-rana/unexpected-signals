from pathlib import Path

from unexpected_signals import storage


def test_paths_are_partitioned_by_date(tmp_path: Path):
    stamp = "2026-11-05T15:52:00Z"
    assert storage.day_path(tmp_path, "x", stamp) == tmp_path / "x/2026/11/2026-11-05.csv"


def test_append_writes_header_once(tmp_path: Path):
    path = tmp_path / "a.csv"
    storage.append_rows(path, ["a", "b"], [{"a": 1, "b": None}])
    storage.append_rows(path, ["a", "b"], [{"a": 2, "b": 3}])
    assert path.read_text().splitlines() == ["a,b", "1,", "2,3"]
    assert storage.read_rows(path) == [{"a": "1", "b": ""}, {"a": "2", "b": "3"}]
