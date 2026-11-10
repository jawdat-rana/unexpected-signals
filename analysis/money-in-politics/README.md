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

# Money in politics, Part 2: The home front

American donors who give through PACs about a foreign country, a diaspora
community or a faith community. This is domestic money: every dollar comes
from U.S. citizens or residents.

1. `fetch_home_front.py` downloads the FEC committee, PAC summary and
   candidate files for 2016–2026, and keeps the contributions and independent
   expenditures of every committee whose name matches a wide keyword list
   (`money-home-fetch` workflow, `raw-money-home` branch).
2. `home_front_committees.csv` is the hand-checked list of committees that
   count, with their group. Rule: the committee's name or stated purpose is
   about a foreign country, a diaspora community, or a faith community
   (faith-based PACs are their own group). Keyword hits that don't fit
   (Zions Bancorporation, Indian gaming, "Progress Incubator") are left out.
3. `fetch_earmarks.py` streams the multi-GB individual contributions files
   and keeps only totals (never donor names) of donations earmarked for a
   candidate and passed on by a listed PAC (`money-home-earmarks` workflow).
4. `home_front.py` totals each committee per cycle and per group.
5. `home_front_story.py` writes the chart data for the story in
   `stories/the-home-front/data/`.

```
git worktree add raw-money-home origin/raw-money-home
python analysis/money-in-politics/home_front.py raw-money-home out
python analysis/money-in-politics/home_front_story.py out
```

Method notes:
- Totals come from the reported summary figures, so small unitemized
  donations are included. "Given" is contributions to candidates and other
  committees; for AIPAC PAC, JStreetPAC and NORPAC most of it is donations
  earmarked by individual donors and passed on. "Independent" is independent
  expenditures for or against candidates (super PACs such as United
  Democracy Project, DMFI PAC, RJC Victory Fund).
- The primary line uses the share of itemized records marked as primary
  (FEC election code P), applied to the reported total. Runoffs don't count
  as primaries. Money a super PAC gives to other super PACs has no election
  attached and never counts toward the primary line.
- Contributions from one listed committee to another are subtracted once.
- The 2026 cycle has data through the pre-general reports (mid-October 2026).
