<!-- DRAFT: numbers below come from analysis/water-levels/prepare.py. -->

Press play and watch three weeks of water, from 18 December 2023 to 8 January 2024. Twice a day the tide runs up the coast, from Vlissingen to Delfzijl. On 21 December storm Pia pushes the sea up, and the storm barriers shut. Then, over Christmas, the flood wave on the Rhine and the Maas rolls down towards the sea.

{{ chart src="charts/replay.js" data="data/levels.csv" title="Three weeks of water in the Netherlands" subtitle="Water level at each Rijkswaterstaat gauge against its own normal (the median over these three weeks), every 10 minutes. Times are Amsterdam time." source="Rijkswaterstaat waterwebservices (CC0); Natural Earth" note="Press Rotterdam to zoom in on the river mouth and the Maeslantkering. Drag the timeline to scrub, or use the arrow keys on it." size="stage" alt="Animated map of the Netherlands with a dot per water gauge, coloured by how far the water stands above or below normal" }}

## What to look for

- **The tide goes round.** High water reaches Vlissingen first, Hoek van Holland about ⟨N⟩ hours later, and Delfzijl ⟨N⟩ hours after Vlissingen.
- **Storm Pia.** ⟨The sea at Hoek van Holland peaked at N m NAP on 21 or 22 December⟩. Behind the Maeslantkering, Rotterdam stayed ⟨N⟩ metres lower.
- **The flood wave.** The Rhine at Lobith peaked at ⟨N m NAP on date⟩. ⟨It reached … days later⟩.

## How it was made

Rijkswaterstaat publishes the measured water height of its gauges every 10 minutes, as open data. We took ⟨N⟩ gauges along the coast and the big rivers, put them on one 10-minute clock and coloured each by how far it stood above or below its own median over the three weeks. A gauge is grey when it has no reading.

When the sea side of a storm barrier stands far above the water behind it for an hour or more, we mark the barrier as shut. That is read from the water levels, not from Rijkswaterstaat's operating log.
