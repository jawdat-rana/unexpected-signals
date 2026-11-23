<!-- DRAFT. Numbers marked ⟨…⟩ wait for a full week of live data (Mon 23 to Sun 29 November 2026). Re-run analysis/ndw-bridges/live.py and fill them in. -->

When the Spijkenisserbrug lifts, Spijkenisse loses its main road link to the north. Traffic piles up on the Groene Kruisweg, and the only other way out is a detour over the Botlekbrug, which opens for ships too. Drivers ask the same question every time: why does a barge get to hold up thousands of cars? Why not make the ship wait?

The short answer is that a ship can't wait the way a car can. Here's why Dutch bridges still let the boats go first, and what a week of live bridge data shows about how often that happens.

{{ signal value="800 m" label="When a ship is 800 metres from the Spijkenisserbrug, the bridge has to be fully up. From that point the ship can't be stopped in time." }}

## Reason 1: a ship can't brake

"You can easily stop a car. That doesn't apply to a ship," Rijkswaterstaat wrote in October 2025 about the Spijkenisserbrug. A loaded ship carries so much momentum that it needs hundreds of metres to stop, and it can't steer well at low speed. So the bridge has to be fully open well before the ship arrives. At Spijkenisse that point of no return is 800 metres, a safety margin set after a seagoing ship only just missed the bridge in 2017, when a fault kept it from opening. An opening there now takes 9 to 12 minutes on average.

## Reason 2: the water doesn't wait either

On tidal rivers like the Oude Maas, the current keeps pushing a ship whether or not the bridge is open. Rijkswaterstaat told AutoRAI in 2017 that shipping at the Botlekbrug has priority over road traffic because of the tide. A ship waiting there would have to hold its position against the current, and there are only so many places where ships can safely wait. That's why, Rijkswaterstaat said, a ban on bridge openings in the rush hour is impossible. Instead, the quietest times are agreed per bridge or waterway with the people who manage it and use it.

## Reason 3: the freight is huge

Inland ships carried about 332 million tonnes of goods on Dutch waterways in 2024, according to CBS, the national statistics office. That's coal, ore, sand, chemicals and some 41 million tonnes in containers. Most of it would otherwise go by truck, on the same roads that wait at the bridge.

## What a week of live data shows

NDW, the national road traffic data portal, publishes bridge openings live as they happen. Over ⟨one week⟩, ⟨N⟩ bridges reported ⟨N⟩ openings, about ⟨N⟩ a day. The busiest was ⟨place⟩, with ⟨N⟩ openings a day.

{{ chart src="charts/live-map.js" data="data/live_bridges.csv" title="Bridges open all over the country, but most of all in the north and in Zeeland" subtitle="Live bridge openings reported to NDW, ⟨23 to 29 November 2026⟩. Circle size: openings a day." source="NDW open data, bridge openings (CC0); UN/LOCODE; Natural Earth" note="Hover or tap a bridge. Place names come from the location code in NDW's records." size="wide" }}

The boats really do go first in the rush hour. ⟨N⟩ of the openings fell in the weekday rush hours, from 7 to 9 and from 4 to 6, and ⟨N⟩ were at night, between 11 pm and 6 am.

{{ chart src="charts/live-hours.js" data="data/live_hours.csv" title="Bridges keep opening in the rush hours" subtitle="Live bridge openings per hour of the day, all bridges, average of ⟨23 to 29 November 2026⟩." source="NDW open data, bridge openings (CC0)" }}

## What the data can't tell you

| Limit | What it means here |
| --- | --- |
| Only bridges that report live | NDW's live feed covers ⟨N⟩ bridges. Many smaller bridges don't report, so the national total is higher. |
| Openings, not delay | The feed says a bridge opened, not how many cars waited. A follow-up will use traffic sensors next to the Botlekbrug and the Spijkenisserbrug to measure that. |
| Snapshots every 5 minutes | Openings are seen in snapshots taken every 5 minutes, so a very short opening between two snapshots can be missed. |
| One week in late November | Summer brings recreational boats and many more openings on some waterways. |

## How I did it

NDW publishes bridge openings in a [DATEX II feed](https://opendata.ndw.nu/) (CC0). A collector in this repository takes a snapshot every 5 minutes and keeps every opening it sees, with the time it started and the last time it was seen. I counted openings per bridge and per hour over whole days in Dutch local time. Place names come from the UN/LOCODE in each record.

The background comes from Rijkswaterstaat's [article on the Spijkenisserbrug](https://www.rijkswaterstaat.nl/nieuws/archief/2025/10/een-schip-kan-je-niet-zomaar-even-stilzetten) (October 2025), [AutoRAI's interview with Rijkswaterstaat](https://autorai.nl/daarom-gaan-bruggen-open-tijdens-spits/) (November 2017), and [CBS figures on inland shipping](https://www.cbs.nl/nl-nl/nieuws/2025/20/binnenvaart-vervoert-meer-goederen-in-2024) for 2024.

The analysis is in [`analysis/ndw-bridges/live.py`](https://github.com/jawdat-rana/unexpected-signals/blob/main/analysis/ndw-bridges/live.py).
