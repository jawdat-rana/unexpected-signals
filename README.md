# unexpected-signals

Collecting open data that nobody thought of as a signal, until it turned out to be one.

**Read the stories: <https://jawdat-rana.github.io/unexpected-signals/>**

This repo is two things:

1. **A publishing home.** Each analysis is a story in `stories/<slug>/`, with its
   chart data and the Python that made it in `analysis/<slug>/`. GitHub Pages
   builds and publishes the site on every merge. See [docs/PUBLISHING.md](docs/PUBLISHING.md).
2. **A data collector**, described below.

```bash
python newsroom/build.py new my-story --title "A question worth asking" --section Trains
python newsroom/build.py serve     # preview at http://localhost:8000
```

## The NDW collector

This repo takes regular snapshots of Dutch open data feeds and stores them as
small, tidy CSV files, so there is history to analyse later. It started with two
feeds from [NDW](https://opendata.ndw.nu/), the Dutch national road traffic data portal:

| Dataset | What is stored | Where |
| --- | --- | --- |
| Bridge openings | One row per opening record, with first and last time it was seen, filed by the opening's date | `data/bridges/YYYY/MM/YYYY-MM-DD.csv` |
| Traffic summary | National totals per snapshot: sites reporting, mean speed, and total flow (an activity index, since vehicles pass many sites) | `data/traffic_summary/YYYY/MM/YYYY-MM-DD.csv` |
| Traffic per motorway | The same totals per motorway (A1, A2, ...) per snapshot, main carriageway only | `data/traffic_roads/YYYY/MM/YYYY-MM-DD.csv` |
| Traffic sites | Speed and flow for the measurement sites you choose in `config.toml` | `data/traffic_sites/YYYY/MM/YYYY-MM-DD.csv` |
| Site catalogue | Every measurement site with its road, lanes and location, refreshed weekly | `data/traffic_sites_catalogue.csv` |

Since November 2026 it also saves five other live feeds that only ever show "now":

| Dataset | What is stored | How often | Where |
| --- | --- | --- | --- |
| Parking garages ([RDW](https://npropendata.rdw.nl/parkingdata/v2/)) | Free spaces, capacity, open and full, for the ~320 public garages and P+R sites with live data. A row is stored only when a garage's status changed. | 10 min | `data/parking/YYYY/MM/YYYY-MM-DD.csv`, `data/parking_catalogue.csv` |
| Apple charts | App Store top 100 free apps and Apple Music top 100 songs, for NL, BE, DE, GB and US | 3 hours | `data/apple_charts/YYYY/MM/YYYY-MM-DD.csv` |
| Google Trends "Trending now" | One row per trending search (country, title, start time, traffic band, top news link), with first and last time seen | 1 hour | `data/google_trending/YYYY/MM/YYYY-MM-DD.csv` |
| OV-fiets | Bikes available per pick-up point (~300). A row is stored only when the count changed. | 10 min | `data/ovfiets/YYYY/MM/YYYY-MM-DD.csv`, `data/ovfiets_catalogue.csv` |
| Shazam top 200 | The most-Shazamed songs of the past 7 days for NL, BE, DE, GB, US and the world. Replaced daily on Shazam, one file per chart day here. | 6 hours | `data/shazam/YYYY/MM/YYYY-MM-DD.csv` |

For the "changed only" feeds, carry the last row forward to get the value at any moment.
`data/_state/` holds when each feed last ran and the last values seen.

The data lives on the [`data` branch](../../tree/data), and the code lives on `main`.

## How it works

```
GitHub Actions (every 5 min, started by cron-job.org)
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

- The bridge feed holds current and planned openings. Planned openings carry
  `probability = riskOf`. Repeated snapshots are what turn it into a history, so
  `first_seen` and `last_seen` are only as accurate as the snapshot interval.
- NDW reports -1 for "no data". Those values are dropped before averaging.
- The DATEX II v2.3 traffic files stop on 9 February 2027. This repo uses v3.
- RDW parking data is RDW open data. About a quarter of the live garages have not
  updated in days or longer, so filter on `last_updated` before using a garage.
  Garages marked limited access need an RDW account and are skipped.
- OV-fiets counts come from [openOV](http://fiets.openov.nl/)'s mirror of the NS
  places API. The data is NS's; credit NS. Some pop-up locations have stale counts (see `feed_time`).
- Apple chart feeds and Google Trends have no open licence. Quote ranks and
  titles as facts with a credit, and don't republish app icons or artwork.
- Netflix Top 10 is not collected: Netflix publishes its full weekly history at netflix.com/tudum/top10.
- Spotify is not collected: charts.spotify.com keeps the full daily and weekly
  history itself (CSV downloads with a free login), and the API no longer serves
  Spotify's own playlists. Apple Music is saved as a second view of "the hits".
- TikTok's song chart (Creative Center) needs a login and blocks automated
  readers, so it is not collected. Shazam stands in: people Shazam songs they
  hear elsewhere, often in TikTok videos. Shazam's chart has no open licence;
  quote ranks with a credit.

### How big does the data get?

Parsed CSVs, all feeds together, are roughly 3 to 4 MB a day before git
compresses them, and git packs repetitive CSVs well. Expect the repository to
grow by about 20 to 30 MB a month. GitHub is comfortable with repositories up to
about 1 GB, so this is fine for a few years. If the `data` branch gets past that,
move finished months to compressed files elsewhere (a GitHub release or Zenodo)
and start the branch fresh. To get only the code: `git clone --single-branch https://github.com/jawdat-rana/unexpected-signals`.
