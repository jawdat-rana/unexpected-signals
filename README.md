# unexpected-signals

Collecting open data that nobody thought of as a signal, until it turned out to be one.

This repo takes regular snapshots of Dutch open data feeds and stores them as
small, tidy CSV files, so there is history to analyse later. It starts with two
feeds from [NDW](https://opendata.ndw.nu/), the Dutch national road traffic data portal:

| Dataset | What is stored | Where |
| --- | --- | --- |
| Bridge openings | One row per opening record, with first and last time it was seen | `data/bridges/YYYY/YYYY-MM.csv` |
| Traffic summary | National totals per snapshot: sites reporting, mean speed, total flow | `data/traffic_summary/YYYY/MM/YYYY-MM-DD.csv` |
| Traffic sites | Speed and flow for the measurement sites you choose in `config.toml` | `data/traffic_sites/YYYY/MM/YYYY-MM-DD.csv` |

The data lives on the [`data` branch](../../tree/data), and the code lives on `main`.

## How it works

```
GitHub Actions (every 15 min)
  -> download feed (.xml.gz)
  -> stream-parse DATEX II, matching on element names, not namespaces
  -> collapse to one row per record or site
  -> merge or append into date-partitioned CSVs
  -> commit to the data branch
```

- **No dependencies.** It uses only the Python standard library (3.11+), so it runs anywhere.
- **Version tolerant.** The parser matches local element names, so it reads both DATEX II v2.3 and v3.
- **Small storage.** Raw national traffic files would be about 100 MB a day. Parsed and summarised, they are a few hundred KB.
- **One feed failing doesn't stop the others.** The run is marked failed, but whatever was collected is still saved.

## Run it yourself

```bash
pip install -e ".[dev]"
python -m unexpected_signals collect                       # writes to ./data
python -m unexpected_signals collect --only bridges        # one feed
python -m unexpected_signals collect --sample-dir samples  # keep the raw XML too
pytest
```

## Fork it

1. Fork the repo.
2. Edit `config.toml`: turn feeds on or off, change the URLs, and list the traffic sites you care about.
3. Under the Actions tab, enable workflows. The `collect` workflow runs on a schedule, and you can also start it by hand.

To add a new feed, write a parser module next to `bridges.py`, add a collector
function in `cli.py`, add a section to `config.toml`, and add a fixture and test.

### Things to know about GitHub Actions

- Public repos get unlimited free minutes on standard runners.
- Scheduled runs can be delayed or skipped when GitHub is busy, so expect small gaps.
- GitHub turns off scheduled workflows after 60 days of no repository activity.

## Data licence and caveats

NDW open data is published under [CC0 1.0](https://docs.ndw.nu/algemeen/data-gebruiksvoorwaarden/),
and attribution is appreciated. The code is MIT licensed.

- The bridge feed holds current and planned openings. Repeated snapshots are
  what turn it into a history, so `first_seen` and `last_seen` are only as accurate as the
  snapshot interval.
- NDW reports -1 for "no data". Those values are dropped before averaging.
- The DATEX II v2.3 traffic files stop on 9 February 2027. This repo uses v3.
