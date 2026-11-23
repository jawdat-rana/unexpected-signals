# Publishing a story

The site lives at <https://jawdat-rana.github.io/unexpected-signals/>. It is
built from this repo by GitHub Actions and served by GitHub Pages, so a story is
public, versioned and reproducible from the moment it is merged.

## The weekly loop

```bash
pip install -e ".[dev]"                      # once

python newsroom/build.py new autumn-trains --title "Is autumn the worst month for trains?" --section Trains
# -> stories/autumn-trains/      the page: story.toml, story.md, charts/, data/
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
6. **Publish.** Either publish now: set `status = "published"`, open the PR,
   merge, and the `pages` workflow deploys in about a minute. Or schedule it:
   set `status = "ready"` and `date` to the day it should go live, and merge.
   See [Scheduling](#scheduling) below.
7. **Share.** Link the story page, not the repo. Keep social posts and other
   personal drafts out of this repo: everything here is for readers to reuse.

Drafts are never on the live site. Their titles do show under "In the
newsroom" on the front page; set `show_upcoming = false` in
`newsroom/site.toml` to hide them.

## Scheduling

Merge drafts early and let the date do the publishing. A story moves through
three statuses in `story.toml`:

| Status | Meaning |
| --- | --- |
| `draft` | Being written. Listed under "In the newsroom", never on the live site. |
| `ready` | Signed off. Goes live by itself on `date`, if nothing blocks it. |
| `published` | Live. |

A `ready` story stays off the site, even after its date, while any of these is true:

- `open = [...]` in `story.toml` lists an open question or action. Empty it when settled.
- `story.md` still has `⟨…⟩` placeholders, `TODO`/`TBD`, or a `<!-- DRAFT` comment.
- `after = "other-slug"` names a story that isn't live yet, so a series keeps its order.

The `pages` workflow runs every morning (about 06:15 Amsterdam time) and
rebuilds the site, so ready stories appear on their date without a commit.
Their `story.toml` keeps saying `ready`; switch it to `published` whenever
convenient. Each run also writes the newsroom list to the run's summary page.
To see it locally:

```bash
python newsroom/build.py schedule                    # what goes live when, and what blocks it
python newsroom/build.py build --today 2026-12-01    # the site as it will look on that day
```

## Updating a published story

Keep `date` as the day it first went live. Add `updated` with the day of the
change and, if readers should know what changed, `update_note`:

```toml
updated = 2026-12-14
update_note = "Final 2026 numbers from the post-general FEC reports."
```

The byline then reads "Updated 14 December 2026", and the note sits in a box
above the text.

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

## Page views

GitHub Pages has no visitor statistics. The site can count page views with
[GoatCounter](https://www.goatcounter.com/): free for personal sites, open
source, no cookies and no personal data, so no consent banner is needed.
Sign up, then set `goatcounter = "<your code>"` in `newsroom/site.toml`.
It is off when empty, so forks don't count into your dashboard.

## Hosting: why GitHub Pages

- **Codespaces** is a cloud dev machine for editing and running this repo in a
  browser. It is handy for writing on a laptop without setup, but it doesn't
  host anything publicly, and it stops when idle.
- **GitHub Pages** serves the built site for free from this repo, on
  `jawdat-rana.github.io/unexpected-signals`, with HTTPS. A custom domain can
  be added later in Settings > Pages.

One-time setup: **Settings > Pages > Build and deployment > Source: GitHub Actions**.

## Raw data and helper workflows

Many sources can only be reached from GitHub's runners, so raw downloads run
in Actions and land on a `raw-<name>` branch, never on `main`.

- **fetch.** Describe a download in `analysis/<dataset>/fetch.toml` (name, the
  command, which files trigger a re-run). Pushing a change to those files runs
  it; `gh workflow run fetch -f name=<name>` runs it by hand. The format is at
  the top of `.github/scripts/fetch_plan.py`.
- **probe.** Before writing a collector, check what a URL returns from GitHub:
  `gh workflow run probe -f url=https://...` (method, body and headers are
  optional). The status, headers and first lines go to the run summary; the
  full reply is kept for 7 days. No temporary workflows on `main`.
- **health.** Every Monday morning, a report on each collector: last success,
  rows per day and gaps between runs. If a feed has gone quiet, it opens an
  issue labelled `collector-health`, or comments on the open one.

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
