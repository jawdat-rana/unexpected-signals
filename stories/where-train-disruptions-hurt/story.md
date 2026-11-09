Counting train disruptions tells you where the railway breaks. It doesn't tell you where it hurts. A signal failure on a quiet branch line and the same failure on the busiest stretch in the country count as one disruption each, but one strands a few hundred people and the other strands tens of thousands.

So I weighted every disruption of 2025 by the number of passengers who use that piece of track. The question: which sections of the Dutch rail network cost passengers the most?

{{ signal value="817 hours" label="The track between Schiphol Airport and Amsterdam had a disruption for 817 hours in 2025, about 34 days, while some 125,000 NS passengers use it on a working day." }}

## What the data shows

Each line on the map is one section of track between two neighbouring stations. The thicker the line, the more NS passengers use it on an average working day. The colour shows how many journeys ran into a disruption there. Switch to "Hours disrupted" to see where the railway breaks, regardless of who is on it.

{{ chart src="charts/rail-map.js" data="data/sections.csv" title="Disruptions hurt most in the Randstad, and most of all under Schiphol" subtitle="Sections of track between neighbouring stations, 2025. Width: NS passengers per working day. Colour: journeys that passed while the section was disrupted." source="Rijden de Treinen (CC BY 4.0); NS annual report dashboard; Natural Earth" note="Hover or tap a section for its numbers and main causes. Dashed lines are run by other operators, so NS has no passenger count for them." size="wide" }}

The busy core of the network, the Randstad between Amsterdam, Rotterdam, Den Haag and Utrecht, carries about 79% of the journeys caught by disruptions, on under a third of the track that NS counts passengers on. That is not because the track there breaks more often per kilometre. It's because every hour of trouble there lands on far more people.

{{ chart src="charts/top-sections.js" data="data/sections.csv" title="Two Schiphol sections top the list" subtitle="The ten sections of track with the most journeys caught by a disruption, 2025. Label: hours disrupted × NS passengers per working day." source="Rijden de Treinen (CC BY 4.0); NS annual report dashboard" }}

## The unexpected part

I expected the ranking to move around from year to year, with a big storm or a long repair job taking the top spot. It barely moves. The section between Schiphol Airport and Amsterdam Riekerpolder, about six kilometres, much of it in the tunnel under the airport, comes out on top in six of the seven years from 2019 to 2025. The exception is 2020, when the pandemic emptied the trains.

It is not one kind of failure either. In 2025 the hours there were spread across broken-down trains, an NS strike, signal failures and points failures. Trains to Amsterdam, Utrecht, Almere, Leiden and Rotterdam all funnel through this stretch, so a problem anywhere on those routes tends to show up here too.

## What the data can't tell you

| Limit | What it means here |
| --- | --- |
| "Journeys caught" is an estimate | It assumes passengers are spread evenly over 18 service hours. A disruption in the rush hour hits more people, one at 23:00 fewer. Read it as an index, not a headcount. |
| A disruption isn't always a full stop | Rijden de Treinen records a disruption whether all trains stop or only some do. I count the hours the same either way. |
| Station lists, not exact locations | Each disruption lists the stations around the problem. I place it on the track that connects them, which can include a section or two more than were really blocked. |
| Only NS passengers | Lines run by Arriva, Keolis and others have no passenger count in the NS data, so they can't score on impact. |
| Years aren't comparable in level | NS changed how it counts passengers, so I only compare rankings between years, never the numbers. |

## How I did it

Two sources, joined on station codes. [Rijden de Treinen](https://www.rijdendetreinen.nl/en/open-data/disruptions) publishes every disruption since 2011, with its cause, its duration and the codes of the stations involved (CC BY 4.0). NS publishes passenger numbers per station and per section of track in its [annual report dashboard](https://dashboards.nsjaarverslag.nl/reizigersgedrag). The page loads them from a small JSON API, one file per year, which is what I used.

For each disruption I found the shortest stretch of network that connects its stations, then added its time to every section on that stretch. Overlapping disruptions on one section count once, so the hours are hours with at least one disruption. I left out problems abroad, which stop international trains but not Dutch ones. Journeys caught is hours disrupted × passengers per day ÷ 18.

The code is in [`analysis/train-disruptions/impact.py`](https://github.com/jawdat-rana/unexpected-signals/blob/main/analysis/train-disruptions/impact.py), and the map's data is linked below each chart.
