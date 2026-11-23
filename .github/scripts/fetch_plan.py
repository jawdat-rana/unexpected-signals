"""Decide which raw-data fetches the `fetch` workflow runs.

Each dataset that needs raw files fetched in GitHub Actions describes them in
``analysis/<dataset>/fetch.toml``, one ``[[fetch]]`` table per fetch:

    [[fetch]]
    name = "ice"                    # results go to the raw-ice branch
    run = "python -u analysis/natural-ice/fetch_raw.py raw"   # writes into raw/
    watch = ["analysis/natural-ice/fetch_raw.py"]  # a push touching these re-runs it
    keep = false                    # false: the branch holds only the latest fetch
    timeout = 20                    # minutes
    pip = []                        # extra packages
    summary = ""                    # a file in raw/ to add to the run summary

    python .github/scripts/fetch_plan.py --name ice            # one fetch, by name
    python .github/scripts/fetch_plan.py --changed files.txt   # fetches whose watch files changed

Prints a JSON list for the workflow's matrix.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS = {"watch": [], "keep": False, "timeout": 30, "pip": [], "summary": ""}


def load(root: Path = ROOT) -> list[dict]:
    fetches = []
    for path in sorted((root / "analysis").glob("*/fetch.toml")):
        for entry in tomllib.loads(path.read_text(encoding="utf-8")).get("fetch", []):
            missing = [key for key in ("name", "run") if key not in entry]
            if missing:
                raise ValueError(f"{path}: a [[fetch]] is missing {', '.join(missing)}")
            fetches.append({**DEFAULTS, **entry, "source": path.relative_to(root).as_posix()})
    names = [f["name"] for f in fetches]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"fetch names used twice: {', '.join(duplicates)}")
    return fetches


def matrix_row(fetch: dict) -> dict:
    return {
        "name": fetch["name"],
        "run": fetch["run"],
        "keep": bool(fetch["keep"]),
        "timeout": int(fetch["timeout"]),
        "pip": " ".join(fetch["pip"]),
        "summary": fetch["summary"],
    }


def plan(fetches: list[dict], name: str | None = None, changed: list[str] | None = None) -> list:
    if name:
        chosen = [f for f in fetches if f["name"] == name]
        if not chosen:
            known = ", ".join(f["name"] for f in fetches)
            raise ValueError(f"no fetch named {name!r}; known: {known}")
    else:
        chosen = [
            f
            for f in fetches
            if any(fnmatch.fnmatch(c, pattern) for c in changed or [] for pattern in f["watch"])
        ]
    return [matrix_row(f) for f in chosen]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name")
    group.add_argument("--changed", type=Path, help="file with one changed path per line")
    args = parser.parse_args(argv)
    changed = args.changed.read_text().split() if args.changed else None
    try:
        print(json.dumps(plan(load(), args.name, changed)))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
