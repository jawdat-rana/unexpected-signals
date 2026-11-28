# UN votes

Data for the "UN votes" series:
[The year the UN stopped agreeing](../../stories/the-year-the-un-stopped-agreeing/) and
[Alone against the world](../../stories/alone-against-the-world/).

1. `fetch_raw.py` downloads the UN Dag Hammarskjöld Library's bulk voting datasets
   (General Assembly votes, General Assembly outcomes, Security Council votes) and
   Erik Voeten's ideal points. The `fetch` workflow (`name=un-votes`) runs it and
   commits the result to the `raw-un-votes` branch. The Library refreshes the files a
   few times a year; re-run the workflow to pick up a new release.
2. `fetch_vetoes.py` keeps the Library's Security Council veto list (`raw-un-vetoes`).
   The bulk files leave out drafts that failed, so vetoed drafts are only here.
3. `prepare.py RAW_DIR` reads a checkout of `raw-un-votes` and writes the story CSVs.

```bash
git clone -b raw-un-votes --depth 1 https://github.com/jawdat-rana/unexpected-signals.git /tmp/raw-un-votes
python analysis/un-votes/prepare.py /tmp/raw-un-votes
```

The UN data is copyright the United Nations and may be reused for non-commercial
purposes with attribution. Voeten's ideal points are CC0.
