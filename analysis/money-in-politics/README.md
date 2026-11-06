# Money in politics, Part 1: Two doors in

How countries reach U.S. politics: through their companies' U.S. PACs, or through
registered foreign agents under FARA.

1. `fetch_raw.py` downloads FEC and FARA bulk files. GitHub Actions runs it
   (`money-fetch` workflow) and commits the files to the `raw-money` branch.
2. `foreign_pacs.py` finds corporate PACs whose parent is foreign, using the
   hand-made list in `foreign_parents.csv`, and totals their contributions to
   other committees by country. Every matched PAC is written out for checking.
3. `fara_clients.py` counts each country's FARA foreign clients (principals)
   active in a date window. FARA bulk files have no dollar amounts.
4. `story_data.py` joins both into the chart data for the story in
   `stories/two-doors-into-washington/data/`. The charts themselves are D3, in that story's `charts/`.

```
git worktree add raw-money origin/raw-money
python analysis/money-in-politics/foreign_pacs.py raw-money 2024 out
python analysis/money-in-politics/fara_clients.py raw-money 2023-01-01 2024-12-31 out/fara_2024.csv
python analysis/money-in-politics/story_data.py out/foreign_pacs_2024.csv out/fara_2024.csv
```

Method notes:
- PAC money comes from U.S. employees of the U.S. subsidiary, not from the
  foreign parent. That's the law, and the post says so up front.
- Companies that are only legally domiciled abroad for tax reasons but run
  from the U.S. (Medtronic, Accenture, Invesco and others) are marked
  `domicile-only` and left out of the country totals.
- FARA "clients" include governments, state companies, political parties and
  some private firms. It counts relationships, not spending.
