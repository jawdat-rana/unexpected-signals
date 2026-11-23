# Natural ice

Data for [The ice we lost](../../stories/the-ice-we-lost/).

1. `fetch_raw.py` downloads KNMI daily temperatures (TG, TN, TX) for every
   station. The `fetch` workflow (`name=ice`) runs it and commits the result to the
   `raw-ice` branch; run the workflow by hand to add the latest days.
2. `prepare.py RAW_DIR` reads a checkout of `raw-ice` and writes the story CSVs:
   Hellmann cold sum, ice days and coldest 15-day mean per winter, using KNMI's
   own definitions. It prints a check against KNMI's published Hellmann list.

```bash
git clone -b raw-ice --depth 1 https://github.com/jawdat-rana/unexpected-signals.git /tmp/raw-ice
python analysis/natural-ice/prepare.py /tmp/raw-ice
```

KNMI data is CC0; cite as "bron: KNMI".
