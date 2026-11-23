import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("fetch_plan", ROOT / ".github/scripts/fetch_plan.py")
fetch_plan = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fetch_plan
spec.loader.exec_module(fetch_plan)


def test_repo_fetch_files_load():
    names = {f["name"] for f in fetch_plan.load()}
    assert {"trains", "ice", "housing", "money", "money-home", "borders"} <= names


def _write(root, dataset, text):
    folder = root / "analysis" / dataset
    folder.mkdir(parents=True)
    (folder / "fetch.toml").write_text(text)


def test_plan_by_name_and_by_changed_files(tmp_path):
    _write(
        tmp_path,
        "a",
        '[[fetch]]\nname = "a"\nrun = "python a.py raw"\nwatch = ["analysis/a/*.py"]\n'
        'keep = true\npip = ["shapely"]\n',
    )
    _write(tmp_path, "b", '[[fetch]]\nname = "b"\nrun = "python b.py raw"\n')
    fetches = fetch_plan.load(tmp_path)

    assert fetch_plan.plan(fetches, name="b") == [
        {
            "name": "b",
            "run": "python b.py raw",
            "keep": False,
            "timeout": 30,
            "pip": "",
            "summary": "",
        }
    ]
    rows = fetch_plan.plan(fetches, changed=["README.md", "analysis/a/fetch_raw.py"])
    assert [r["name"] for r in rows] == ["a"] and rows[0]["pip"] == "shapely" and rows[0]["keep"]
    assert fetch_plan.plan(fetches, changed=["analysis/a/fetch.toml"]) == []
    with pytest.raises(ValueError, match="known: a, b"):
        fetch_plan.plan(fetches, name="c")


def test_duplicate_names_are_an_error(tmp_path):
    _write(tmp_path, "a", '[[fetch]]\nname = "x"\nrun = "1"\n')
    _write(tmp_path, "b", '[[fetch]]\nname = "x"\nrun = "2"\n')
    with pytest.raises(ValueError, match="used twice: x"):
        fetch_plan.load(tmp_path)
