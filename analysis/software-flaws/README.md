# Software flaws: found vs exploited

Data and code behind [Black October](../../stories/black-october/).

| Step | Where | What |
| --- | --- | --- |
| Fetch | `fetch_raw.py`, run by `.github/workflows/flaws-fetch.yml` | Downloads the CVE List (cvelistV5 release), CISA's KEV catalogue, Microsoft's monthly CVRF update guides and NCSC-NL CSAF advisories, and commits compact CSVs to the `raw-flaws` branch |
| Prepare | `prepare.py` | Turns those CSVs into the chart data in `stories/black-october/data/` |

Raw files on `raw-flaws`:

| File | One row per |
| --- | --- |
| `cves.csv` | Published CVE: publish date, assigner, vendor, highest CVSS score, first CWE, and any AI system named in its credits or description |
| `kev.csv` | Flaw in CISA's Known Exploited Vulnerabilities catalogue |
| `msrc.csv` | CVE in a Microsoft monthly update guide, with Microsoft's "exploited" flag (includes Chromium and open-source flaws Microsoft ships) |
| `ncsc_nl.csv` | NCSC-NL advisory with its CVEs |

Run `prepare.py` with the commands in its docstring. Re-run the fetch from the Actions tab (`flaws-fetch`, "Run workflow") to refresh.
