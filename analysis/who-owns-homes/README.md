# Who owns the homes

CBS StatLine tables on housing tenure, household wealth and migration, used by
the story `stories/who-owns-the-netherlands`.

- `tables.txt` lists the tables and how each is filtered.
- `fetch_raw.py` downloads them (the `housing-fetch` workflow runs it and
  commits the result to the `raw-housing` branch).
- `prepare.py RAW_DIR` writes the story's chart CSVs.

```bash
git fetch origin raw-housing && git worktree add /tmp/raw-housing origin/raw-housing
python analysis/who-owns-homes/prepare.py /tmp/raw-housing
```

All tables are CBS open data, CC BY 4.0.
