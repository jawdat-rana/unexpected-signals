# Publishing a story

The site lives at <https://jawdat-rana.github.io/unexpected-signals/>. It is
built from this repo by GitHub Actions and served by GitHub Pages, so a story is
public, versioned and reproducible from the moment it is merged.

## The weekly loop

```bash
pip install -e ".[dev]"                      # once

python newsroom/build.py new autumn-trains --title "Is autumn the worst month for trains?" --section Trains
# -> stories/autumn-trains/      the page: story.toml, story.md, charts/, data/, post.md
# -> analysis/autumn-trains/     the Python: prepare.py writes stories/autumn-trains/data/*.csv

python analysis/autumn-trains/prepare.py     # raw data -> small chart CSVs
python newsroom/build.py serve               # preview with drafts at http://localhost:8000
```

1. **Branch.** One branch and one pull request per story.
   Name analysis folders after the dataset or series (`analysis/train-disruptions`),
   so one folder can feed several stories; `new` creates `analysis/<slug>` as a
   starting point, which you can rename and point `analysis =` in `story.toml` at.
2. **Analyse in Python.** `analysis/<slug>/prepare.py` downloads raw data into
   `analysis/<slug>/raw/` (ignored by git) and writes aggregated, chart-ready
   CSVs into `stories/<slug>/data/`. Only the small CSVs are published.
3. **Write.** Edit `story.md`. Keep the structure: the question, what the data
   shows, the unexpected part, what it can't tell you, how it was done.
4. **Chart.** Pick one per figure:
   - **Observable Plot** (`charts/dots.js` in the template): quickest, a chart in a dozen lines.
   - **D3** (`charts/line.js`): full control, for the one chart that carries the story.
   - **Datawrapper**: when a point-and-click chart or map is faster. Embed by id.
5. **Preview.** `python newsroom/build.py serve`. Check the page on a phone width
   and in the night edition (the toggle in the masthead).
6. **Publish.** Set `status = "published"` in `story.toml`, open the PR, merge.
   The `pages` workflow deploys in about a minute.
7. **Post.** Use `post.md` for LinkedIn. Link the story page, not the repo.

Drafts are never on the live site. Their titles do show under "In the
newsroom" on the front page; set `show_upcoming = false` in
`newsroom/site.toml` to hide them.

## Shortcodes

Each goes on its own line in `story.md`. All attributes are optional except
the first one shown.

| Shortcode | Attributes |
| --- | --- |
| `{{ chart src="charts/x.js" }}` | `data`, `title`, `subtitle`, `source`, `note`, `alt`, `size` (`wide` or `text`) |
| `{{ datawrapper id="aBc12" }}` | `height` (starting height, it then fits itself), `title`, `subtitle`, `source`, `alt` |
| `{{ signal value="$24M" label="..." }}` | the big-number callout, one per story |

`title`, `subtitle`, `source`, `note` and `label` accept inline Markdown such as links.

## Writing a chart module

A chart module exports one function. The runtime (`newsroom/assets/js/signals.js`)
calls it with everything it needs and redraws it when the width or theme changes:

```js
export default function draw({ data, width, d3, Plot, theme, tooltip, table }) {
  // data:    rows from the CSV in `data=`, numbers and dates already parsed
  // theme:   colours as hex: theme.signal, theme.context, theme.ink, theme.muted,
  //          theme.categorical (3 colours, fixed order), theme.plot (Plot defaults)
  // tooltip: tooltip.show(event, html), tooltip.hide(), tooltip.esc(text)
  // table:   table(rows, [{ key, label, format }]) -> a "Show the numbers" table
  return svgNode; // or [svgNode, table(...)]
}
```

## The look

A broadsheet for open data: newsprint, ink, and one signal colour.

- **Grey everything, colour the signal.** Context is `--context` grey; the
  thing the story is about is `--signal` red. Use the three categorical colours
  only when groups really need telling apart, always in the same order.
- **Type.** Newsreader for text and headlines, IBM Plex Sans in charts, IBM
  Plex Mono for labels and metadata. All self-hosted, so no tracking by font CDNs.
- **Every chart:** a title that states the finding, a subtitle with units and
  time span, a source line, a link to its data, and a table of its numbers.
- **Night edition.** Separate dark colours, checked for colour-blind separation
  on the dark paper, not an automatic inversion.

Colours for Datawrapper (paste into the custom colour field):

| Role | Light | Dark |
| --- | --- | --- |
| Signal | `#d6452b` | `#e5532f` |
| Context | `#bdb4a4` | `#57524a` |
| Second group | `#1f6fa8` | `#3f8fd0` |
| Third group | `#a07c10` | `#b88a1c` |
| Text | `#1b1915` | `#eee7d8` |
| Background | `#f5f0e6` | `#14130f` |

The full component set is on the [style guide page](https://jawdat-rana.github.io/unexpected-signals/style/),
which is built from `templates/story/`, so the template and the guide can't drift apart.

## Hosting: why GitHub Pages

- **Codespaces** is a cloud dev machine for editing and running this repo in a
  browser. It is handy for writing on a laptop without setup, but it doesn't
  host anything publicly, and it stops when idle.
- **GitHub Pages** serves the built site for free from this repo, on
  `jawdat-rana.github.io/unexpected-signals`, with HTTPS. A custom domain can
  be added later in Settings > Pages.

One-time setup: **Settings > Pages > Build and deployment > Source: GitHub Actions**.

## Repo layout

```
stories/<slug>/          one folder per published piece (text, charts, chart data)
analysis/<dataset>/      Python per dataset or series, e.g. money-in-politics, train-disruptions
templates/story/         the scaffold for new stories, also rendered as the style guide
templates/analysis/      the scaffold for prepare.py
newsroom/                site build script, theme (CSS, fonts), chart runtime, vendored D3 and Plot
src/unexpected_signals/  the NDW data collector (runs every 15 minutes)
```

D3 7.9.0 and Observable Plot 0.6.16 are vendored in `newsroom/assets/vendor/`
so pages never depend on a CDN. To upgrade, replace the files and the script
tags in `newsroom/templates/base.html`.
