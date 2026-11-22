# NDW bridge openings

Planned bridge openings from NDW's open data feed (CC0), collected by
`src/unexpected_signals` onto the `data` branch.

```bash
git fetch origin data
git worktree add data-branch origin/data
python analysis/ndw-bridges/prepare.py data-branch/data   # writes stories/canal-bridges/data/*.csv
```

The planned openings repeat almost exactly from one weekday to the next, so
they work as a timetable of slots, not confirmed openings.
