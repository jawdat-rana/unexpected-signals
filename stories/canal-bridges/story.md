Every Dutch driver knows the moment: the lights turn red, the barriers come down and a slab of road tips up into the sky so a barge can pass. It feels like bad luck. On one route in North Holland it's the timetable.

Since early November I've been collecting NDW's open data feed of planned bridge openings. NDW is the national road traffic data portal. The feed covers 57 movable bridges, all in North Holland, and 25 of them sit on a single shipping route: from Den Helder down the Noordhollandsch Kanaal through Alkmaar and on to the Zaan. I wanted to know how much of the day those bridges are set aside for boats.

{{ signal value="3 hours" label="Each bridge on the route from Den Helder to Zaanstad has about 31 planned openings of 6 minutes a day: some 3 hours in which the road can close for ships." }}

## What the data shows

The first surprise was the shape of the data itself. The planned openings repeat almost exactly from one weekday to the next: 78% of the opening times on a weekday come back on every other weekday, to the minute. Saturdays and Sundays have their own pattern. So this isn't a forecast of ships. It works as a timetable: the slots in which each bridge is planned to open.

On the 25 bridges between Den Helder and Zaanstad there are about 31 slots a day, almost all of 6 minutes. Add them up and the road over each bridge is planned to close for cars for about 3 hours and 5 minutes a day. The bridges on the route have nearly the same number of slots, bridge after bridge.

{{ chart src="charts/bridge-map.js" data="data/bridges.csv" title="Most of the bridges in the feed sit on one route through North Holland" subtitle="Movable bridges with planned openings in NDW's feed, 6 to 21 November 2026. Circle size: planned openings a day." source="NDW open data, planned bridge openings (CC0); Natural Earth" note="Hover or tap a bridge for its numbers. NDW gives coordinates, not bridge names, so bridges are labelled by the nearest town." size="wide" }}

The other 32 bridges sit on two routes further south. One runs from Spaarndam through Haarlem to Sassenheim, the other from Amsterdam past Schiphol to Leimuiden. They have fewer slots: about 18 and 23 a day. Together, the 57 bridges are planned to be open about 142 hours a day.

{{ chart src="charts/week.js" data="data/week.csv" title="A week at one bridge near Den Helder: the same timetable every weekday" subtitle="Every planned opening at the busiest bridge on the route, Monday 9 to Sunday 15 November 2026. Shaded: the weekday rush hours." source="NDW open data, planned bridge openings (CC0)" note="Each red mark is one planned opening, drawn at least 2 pixels wide so the short ones stay visible." }}

Weekends are quieter but not quiet. A bridge on the northern route still has about 27 slots on a Saturday or Sunday, against 33 on a weekday. Around Haarlem the number nearly halves at the weekend.

## The unexpected part

I expected the timetable to keep the rush hours free. Plenty of Dutch bridges keep their decks down for cars at peak times. Not on this route. On an average weekday, each bridge between Den Helder and Zaanstad has 4 to 11 planned openings in the four rush hours, from 7 to 9 in the morning and 4 to 6 in the afternoon. In Amsterdam, most bridges have none or one.

{{ chart src="charts/rush.js" data="data/bridges.csv" title="Bridges on the northern route keep opening in the rush hours" subtitle="Planned openings between 07:00–09:00 and 16:00–18:00 on an average weekday, per bridge, 6 to 21 November 2026." source="NDW open data, planned bridge openings (CC0)" note="Hover or tap a dot for the bridge." }}

The night tells the same story. The Haarlem bridges are almost silent between 11 at night and 6 in the morning. The northern route isn't: each bridge has about 4 planned openings a night, most of them between 1 and 5 in the morning, when there are few cars to stop.

{{ chart src="charts/hours.js" data="data/hours.csv" title="The northern route is planned to open around the clock" subtitle="Planned openings per bridge in each hour of the day, average of 6 to 21 November 2026. Shaded: the weekday rush hours." source="NDW open data, planned bridge openings (CC0)" note="Hover for the numbers in each hour." }}

## What the data can't tell you

| Limit | What it means here |
| --- | --- |
| Planned, not confirmed | A slot in the timetable doesn't mean the bridge opens: no ship, no opening. I'm now also collecting the live openings, so a follow-up can check how many slots are really used. |
| Only bridges in the feed | NDW's planning feed covers 57 bridges, all in North Holland. Most Dutch movable bridges aren't in it, so this is not a national ranking. |
| Closed for cars isn't the same as delay | An opening only costs drivers time if there's traffic waiting. A 6-minute opening at 3 in the morning hurts nobody. Measuring the real cost needs traffic sensors next to the bridges, which I've started collecting too. |
| Sixteen days in November | The numbers describe late autumn. Timetables often change with the season, and summer brings recreational boats. |
| Rush hours are a fixed window | I count 07:00–09:00 and 16:00–18:00, local time. The local rules for each bridge can differ. |

## How I did it

NDW publishes a [feed of planned bridge openings](https://opendata.ndw.nu/) in DATEX II format (CC0). A small collector in this repository takes a snapshot of it every 5 to 15 minutes and stores each planned opening once, with the first and last time it was seen. When a plan changes, I keep only its latest version, and a handful of openings listed twice under different ids count once.

I used whole days from 6 to 21 November 2026 and counted openings per bridge, per hour and per day of the week, in Dutch local time. The three routes are groups of bridges that lie along the same waterway and have near-identical numbers of openings.

The collector is in [`src/unexpected_signals`](https://github.com/jawdat-rana/unexpected-signals/tree/main/src/unexpected_signals) and the analysis in [`analysis/ndw-bridges/prepare.py`](https://github.com/jawdat-rana/unexpected-signals/blob/main/analysis/ndw-bridges/prepare.py). The data behind each chart is linked below it.
