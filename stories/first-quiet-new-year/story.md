At 00:00 on 1 January 2026, a measuring station on a busy street in Utrecht recorded 1,848 micrograms of fine dust (PM10) per cubic metre of air. That's 37 times the European limit for a daily average. Two hours later the air was clean again. That was the last New Year with legal consumer fireworks in the Netherlands. A national ban took effect on 1 August 2026, so ⟨the night of 31 December 2026 was the first one without them. Result: one sentence on how the 2026/27 night compares, filled in from the 3 January data run.⟩

{{ signal value="⟨x×⟩" label="⟨the fine dust the first New Year under the ban added, compared with what the wind would lead you to expect. 1× is an ordinary year with fireworks.⟩" }}

## Midnight, every year

The Netherlands has about 80 stations that measure fine dust every hour. The chart shows the median of all of them, hour by hour, from 18:00 on New Year's Eve to 08:00 on New Year's Day. In every year with fireworks on sale, the jump comes in the first hour after midnight, and it's gone by breakfast.

{{ chart src="charts/profile.js" data="data/profile.csv" title="Every year, the air fills up in the first hour of the new year" subtitle="Median fine dust (PM2.5, µg/m³) over all Dutch stations, local time, 31 December to 1 January. Grey: years with fireworks on sale. Dashed: the two covid bans. Red: the newest year." source="RIVM Luchtmeetnet" note="Hover or tap a line for the year." size="wide" }}

⟨One paragraph on the 2026/27 curve: did the midnight jump disappear, shrink, or stay?⟩

## The ban isn't the first one

This isn't the first New Year without legal fireworks. During covid, the Netherlands had no legal sales on 31 December 2020 or 31 December 2021. Those two nights are the best guide to what a ban does to the air, and they don't agree with each other.

- **2020/21:** the midnight hour was much lower than usual (a median of 110 µg/m³ of PM2.5, against 289 in 2025/26). But the smoke didn't clear. It stayed high for hours after midnight, so the night as a whole was still one of the dirtiest in the data.
- **2021/22:** the night added 23 µg/m³ of PM2.5, a quarter of the 2025/26 figure. Only the stormiest years with fireworks came that low, and this one had a moderate wind.

The difference between the two years is mostly the weather.

## Wind decides as much as fireworks

Smoke doesn't stay where it's made. On a windy night it's blown away within the hour. On a still, cold night it hangs over the streets until morning. Of all the New Year's nights since 2013, 2020/21 had the least wind, an average of 2.4 metres per second across KNMI's stations. The year after had 5.5.

So comparing years without the weather is misleading. I fitted a simple curve on the years with fireworks on sale: how much dust a night adds for a given wind speed. Wind alone explains about three-quarters of the difference between years. Every extra metre per second of wind cuts the dust by about 18%.

{{ chart src="charts/wind.js" data="data/nights.csv" title="Still nights fill up with smoke, windy nights stay clean" subtitle="Each dot is one New Year's night in the Netherlands: the average wind against the extra fine dust (PM2.5) in the five hours after 23:00. The dotted curve is what the years with fireworks on sale predict." source="RIVM Luchtmeetnet, KNMI" note="Open circles: covid bans, no legal sales. Hover or tap a dot." size="wide" }}

Measured against that curve, the first covid ban added about 37% less dust than the wind predicted, and the second about 71% less. The data can't say why the first ban did less. Fireworks bought earlier or abroad, and illegal ones, are the obvious suspects. ⟨2026/27: how far below the curve it lands, and where it sits next to the covid years.⟩

## Was it getting worse?

Fireworks sales went from about €77 million in 2019 to a record €129 million in 2025, according to the trade association BPN. The air shows some of that. After taking out the wind, 2025/26 was the worst New Year in the data, with almost twice the dust the wind would predict. But the three years before it were close to normal, so the record is one year, not a clear trend.

{{ chart src="charts/index.js" data="data/nights.csv" title="The last New Year before the ban was the smokiest for its wind" subtitle="Extra fine dust (PM2.5) on each New Year's night, divided by what the wind would lead you to expect. 1× is an ordinary year." source="RIVM Luchtmeetnet, KNMI; sales: BPN via news reports" note="Open bars: covid bans. Hover or tap a bar for the sales figure." }}

## And the climate?

You might think a night like that shows up in the climate numbers too. It doesn't. RIVM puts the CO2 from fireworks at 43 grams per kilo. Dutch people set off about 16 million kilos a year around 2016, the latest count. That's about 700 tonnes of CO2, and perhaps 1,200 if the amount grew with sales.

The Netherlands emitted about 146 million tonnes of greenhouse gases in 2025, or about 277 tonnes a minute. So all the fireworks of a Dutch New Year emit about as much CO2 as the whole country does in **two and a half to four minutes**. Closing the gap to the 2030 target (102 million tonnes) would take the CO2 of more than 35,000 New Years. The ban doesn't change anything for the climate target.

Fine dust is a different story. In Germany, where the environment agency counted it, fireworks are about 1% of a year's PM10 emissions and 2% of PM2.5. Most of that comes out in one night, in the streets where people live. The ban doesn't matter for the climate, but it does for people's lungs.

## Germany as a check

Germany had no legal fireworks sales in those covid years either, and it has no ban now. Across a few hundred German stations, the New Year's night added a median of 11 and 6 µg/m³ of PM2.5 in the two covid years. In the other years since 2015 the median was 22, ranging from 16 to 77. That's a bigger drop than in the Netherlands. These German figures aren't adjusted for wind, though. ⟨2026/27: Germany's night, as a year with fireworks on sale next to the Dutch ban.⟩

## What the data can't tell you

| Limit | What it means here |
| --- | --- |
| A ban isn't zero fireworks | Professional shows, displays by local clubs that got an exemption, and illegal fireworks all still count. The data shows the air, not who lit what. |
| Wind isn't the only weather | Temperature inversions, rain and fog also matter. The wind curve leaves about a quarter of the year-to-year difference unexplained, so a single year 30% above or below it isn't unusual. |
| The newest data is unvalidated | ⟨2026/27⟩ and January 2026 come from RIVM's live feed, which can still change. For January 2026, only 39 PM10 and 25 PM2.5 stations are published so far. On those same stations, earlier years look the same or slightly dirtier, so the 2025/26 figure isn't low because of which stations reported. |
| Street stations, not homes | Many stations sit on busy roads. The median over all stations is a fair national figure. The single highest hour mostly says where a station happens to be. |
| Sales are trade-association estimates | BPN's figures are reported in the news each year. No official series exists. |

## How I did it

RIVM publishes every hourly measurement of the national air quality network as [bulk files](https://data.rivm.nl/data/luchtmeetnet/), validated per year back to the 1980s. For each New Year from 2012/13 I kept the week from 28 December to 3 January for PM10 and PM2.5 at every station. The newest week comes from the [Luchtmeetnet API](https://api-docs.luchtmeetnet.nl/), which gives the same values before validation.

For each station I took the mean of the five hours from 23:00 to 04:00 on New Year's night and subtracted the median of the same five hours on four quiet nights that week (28, 29 December and 1, 2 January). The national figure is the median over stations. Wind is the hourly mean wind speed over all [KNMI stations](https://www.daggegevens.knmi.nl/) in the same hours. The wind curve is a least-squares fit of log(extra dust) on wind speed over the years with legal sales. German data comes from the [Umweltbundesamt](https://www.umweltbundesamt.de/daten/luft/luftdaten), computed the same way.

The peaks match RIVM's own New Year reports: 1,848 µg/m³ PM10 in Utrecht and 530 µg/m³ PM2.5 in Veldhoven in 2025/26, and 908 µg/m³ in Den Haag in 2024/25. CO2 and PM10 per kilo come from RIVM's memo [Milieulast van vuurwerk](https://zoek.officielebekendmakingen.nl/blg-981345.pdf) (2020). The national total comes from [CBS](https://www.cbs.nl/en-gb/news/2026/11/increase-in-greenhouse-gas-emissions-in-2025), and the German shares from the [Umweltbundesamt](https://www.umweltbundesamt.de/en/node/84860).

RIVM, KNMI and the Umweltbundesamt aren't involved in this analysis and don't necessarily endorse it. The code is in [`analysis/fireworks-air`](https://github.com/jawdat-rana/unexpected-signals/tree/main/analysis/fireworks-air).
