Every Dutch winter starts with the same question: will we skate this year? This year the question came early. On 23 November 2026 De Bilt had its first day with a mean temperature below zero, and KNMI's cold counter for this winter moved off zero, to 0.4. The first 23 days of November averaged 5.5 °C, two degrees below normal and the coldest start to November since 1998.

Does that mean a cold winter is coming? The 125 winters of KNMI data behind this story say it helps a little, and they show why the question has kept getting the same answer for almost 30 years.

{{ signal value="29 winters" label="since De Bilt last had a cold winter, in 1997. Before that, the longest wait since 1902 was 10 winters." }}

## This November: the coldest start since 1998

{{ chart src="charts/november.js" data="data/debilt_november.csv" title="The coldest start to November since 1998" subtitle="Mean daily temperature in De Bilt from 1 to 23 November, every year since 1901. Red: 2026. Below the dashed line: colder than this year." source="KNMI daily data, De Bilt (CC0)" note="KNMI publishes daily data a few days late; 23 November is the latest day available. Hover or tap a dot for the winter that followed." size="wide" }}

Since 1990, only 1993 and 1998 started November colder. Over the whole record it's less special: 39 years since 1901 had a colder first three weeks, most of them before 1990. The five long-running stations from Den Helder to Maastricht tell the same story, with 1998 the last colder start.

A cold November is a weak signal for the winter. Of the 20 coldest starts to November since 1901, 9 were followed by a cold winter, against about 1 in 5 for all years. The two most recent ones didn't deliver: after November 1993 the winter scored 63, after November 1998 it scored 48. Both mild.

## How to measure a winter

KNMI has a simple yardstick, the Hellmann cold sum. Take every day from 1 November to 31 March, keep the days with a mean temperature below zero, and add up how far below zero they were. A winter with 20 days at an average of -5 °C scores 100. KNMI calls a winter above 100 cold, above 160 very cold, and above 300 severe. Below 40 it's mild.

The record holders are 1947 (342.5) and 1963 (337.2), the winter of the famously brutal Elfstedentocht. I rebuilt the sum from KNMI's daily data, and it matches KNMI's own list to the decimal.

{{ chart src="charts/hellmann.js" data="data/debilt_winters.csv" title="Cold winters used to come every few years. The last one was 1997" subtitle="Hellmann cold sum in De Bilt, every winter from 1902 to 2026. Red: a winter with an Elfstedentocht." source="KNMI daily data, De Bilt (CC0)" note="A winter is named after the year it ends in: 1963 runs from November 1962 to March 1963. Hover or tap a bar." size="wide" }}

## The unexpected part: it's the run, not the average

Mild winters aren't new. Before 1989, more than a third of the winters in De Bilt were mild. What's new is that they don't stop. Every winter since 2014 has scored below 40, 13 in a row. Before that, the longest run of mild winters since 1902 was five.

The same goes for cold ones. Between 1902 and 1997, De Bilt had 27 cold winters, and the longest gap between two of them was 10 years (1929 to 1939). Since 1997 there hasn't been a single one.

| Winters | Average Hellmann | Cold winters | Elfstedentochten |
| --- | --- | --- | --- |
| 1902–1926 | 69 | 8 | 3 |
| 1927–1951 | 98 | 6 | 6 |
| 1952–1976 | 80 | 6 | 3 |
| 1977–2001 | 67 | 7 | 3 |
| 2002–2026 | 32 | 0 | 0 |

## Friesland now freezes like Zeeland used to

De Bilt is one station in the middle of the country. KNMI has 14 stations with long enough records to compare the 38 winters from 1951 to 1988 with the 38 from 1989 to 2026. Every one of them lost about half its ice days, the days the temperature stays below zero all day.

{{ chart src="charts/ice-map.js" data="data/stations.csv" title="Everywhere lost about half its ice days" subtitle="Average number of days a winter with a maximum below 0 °C, 1951–1988 (ring) against 1989–2026 (red dot), at the 14 KNMI stations with long records." source="KNMI daily data (CC0); Natural Earth" note="Hover or tap a station for the share of cold winters too." size="wide" }}

Leeuwarden, the home of the Elfstedentocht, had a cold winter in 35% of the winters before 1989. Since then it's 8%, the same share Vlissingen, on the Zeeland coast, had before 1989. The north still gets more ice than the south and the coast, but the whole map has shifted.

## What about the Elfstedentocht?

KNMI uses a rule of thumb for a "potential" Elfstedentocht: the coldest 15 days of the winter in De Bilt average below -4.2 °C. That's cold enough for ice of at least 15 cm along the whole 200 km route. By that rule, 20 winters since 1902 were cold enough, and 13 of them had a tour. The rule misses two early tours (1909 and 1912) that were run on thinner ice, and it flags winters like 1979 and 2012 that were cold enough but had no tour, because of snow on the ice, a thaw at the wrong moment or weak spots on the route.

The last winter cold enough by this rule was 2012, 14 winters ago. In 2019 KNMI put the chance of a potential Elfstedentocht at about 8% a year, down from about 20% a century ago.

## What the data can't tell you

| Limit | What it means here |
| --- | --- |
| Temperature, not ice | Ice also depends on wind, snow, sunshine and how deep the water is. KNMI's own ice model uses all of those. I only use temperature, as the Hellmann sum and the Elfstedentocht rule do. |
| Short cold snaps still count | In February 2021 people skated across the country, in a winter that scored only 36. A few cold days are enough for shallow ditches and flooded fields, even when the winter as a whole is mild. |
| Stations move and change | Most long records are at airports, and the area around them changed in 70 years. KNMI corrects some long series for this; these are the raw daily values. |
| Two periods, not a trend line | Comparing 1951–1988 with 1989–2026 shows how much changed, not exactly when. |

## How I did it

KNMI publishes daily weather for every station through its [daggegevens service](https://www.daggegevens.knmi.nl/) (CC0, bron: KNMI). A GitHub Actions workflow downloads the daily mean, minimum and maximum temperature for 50 stations. De Bilt goes back to 1901. For each winter (1 November to 31 March) I computed the [Hellmann cold sum](https://www.knmi.nl/nederland-nu/klimatologie/lijsten/hellmann), the number of ice days and the coldest 15-day mean, and kept winters with at least 145 days of data. For November I averaged the daily mean in De Bilt over the same days of every year, up to the latest day KNMI has published. The Elfstedentocht rule comes from KNMI's [2019 analysis](https://www.knmi.nl/kennis-en-datacentrum/achtergrond/kans-op-elfstedentocht-in-een-veranderend-klimaat) by Van Oldenborgh, Visser, Brandsma and De Vries. The station map uses the 14 stations with at least 25 complete winters in both periods.

KNMI is not involved in this analysis and doesn't necessarily endorse it. The code is in [`analysis/natural-ice`](https://github.com/jawdat-rana/unexpected-signals/tree/main/analysis/natural-ice).
