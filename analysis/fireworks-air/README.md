# Fireworks and air

Data for [The first quiet New Year?](../../stories/first-quiet-new-year/).

1. `fetch_raw.py` keeps the week around every New Year's Eve since 2012/13:
   hourly PM10 and PM2.5 for every Dutch station from RIVM's bulk files
   (the Luchtmeetnet API only for the newest week, which isn't in a bulk file
   yet), hourly PM for German stations from the Umweltbundesamt, and hourly wind
   from KNMI. The `fetch` workflow (`name=fireworks`) runs it and commits to the
   `raw-fireworks` branch. Run it by hand after New Year to add the latest night.
2. `prepare.py RAW_DIR` computes, per station and year, the extra dust of New
   Year's night over the quiet nights of the same week, takes the median over
   stations, and fits the wind curve. Writes the story CSVs and
   `stations_by_year.csv` (every Dutch station, every year).
3. `sales.csv`: consumer fireworks sales per season as reported by the trade
   association BPN in the news, with the source of each figure.

```bash
git clone -b raw-fireworks --depth 1 https://github.com/jawdat-rana/unexpected-signals.git /tmp/raw-fireworks
python analysis/fireworks-air/prepare.py /tmp/raw-fireworks
```

Cite RIVM Luchtmeetnet, KNMI (CC0) and the Umweltbundesamt.
