# Train disruptions

An investigation of what goes wrong on the Dutch rail network, when it happens and where,
using [Rijden de Treinen's open disruption data](https://www.rijdendetreinen.nl/en/open-data/disruptions)
(CC BY 4.0, 2011 to 2025).

Step 1 is a profile of the raw data:

```bash
python analysis/train-disruptions/profile.py
```

Caveats from the source: only disruptions NS communicated are included, and
NS changed systems in 2017, so timing comparisons start in 2017.

## Passenger impact (`impact.py`)

Where do disruptions hurt the most passengers? `fetch_raw.py` downloads the
Rijden de Treinen disruptions and the NS annual report dashboard JSON
(passengers per section of track, `https://dashboards.nsjaarverslag.nl/api/dashboard/<year>`).
The `trains-fetch` workflow runs it and commits the files to the `raw-trains`
branch, for machines that can't reach those hosts.

```bash
git fetch origin raw-trains && git --work-tree=analysis/train-disruptions/raw checkout origin/raw-trains -- . && git reset
python analysis/train-disruptions/impact.py 2025   # writes stories/where-train-disruptions-hurt/data/sections.csv
```

Each disruption is placed on the shortest stretch of network joining its
stations; per section the script sums hours with a disruption (overlaps merged)
and estimates journeys caught as hours x passengers per day / 18.
