# Story folder

Not published. One folder per story:

| File | What it is |
| --- | --- |
| `story.toml` | Title, dek, date, section, status, sources |
| `story.md` | The text, with `chart`, `datawrapper` and `signal` shortcodes |
| `charts/*.js` | D3 or Observable Plot chart modules |
| `data/*.csv` | Small, chart-ready data, written by `analysis/<slug>/prepare.py` |

See `docs/PUBLISHING.md` for the full workflow.
