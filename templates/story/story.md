Start with the question in plain words, and why anyone would care. One short paragraph. The first letter becomes a drop cap, like the opening of a newspaper story.

This template shows every component a story can use. Copy it with `python newsroom/build.py new my-slug`, then replace the text and keep the structure: the question, what the data shows, the unexpected part, what the data can't tell you, and how it was done.

{{ signal value="+38%" label="Put the one number to remember here, in a sentence that still makes sense on its own." }}

## What the data shows

Each chart is one line in this file. A D3 chart is a small JavaScript module in `charts/` that gets the data, the width and the theme colours, and returns an SVG. Everything stays grey except the signal.

{{ chart src="charts/line.js" data="data/example-weekly.csv" title="The headline of the chart says what it shows" subtitle="Weekly index, 2025. The subtitle gives units and the time span." source="Example data, made up for this template" }}

## The unexpected part

Observable Plot is the quick way: a whole chart in a dozen lines, with tooltips built in. It is made by the D3 team, so the two mix well.

{{ chart src="charts/dots.js" data="data/example-places.csv" title="Bigger places have higher rates, and the South more so" subtitle="Each dot is one place. The line is a linear fit." source="Example data" note="Hover a dot for its name." }}

A Datawrapper chart goes in the same way: write `datawrapper id="aBc12" title="..." source="..."` between double curly braces on its own line, using the short id from the chart's share link (datawrapper.dwcdn.net/**aBc12**/). It follows the reader's light or dark setting.

> A pull quote, for the sentence you'd want someone to screenshot.

## What the data can't tell you

Be explicit about the limits. This is where trust comes from. A table works for small comparisons:

| Check | Why it matters |
| --- | --- |
| Who collected it | Coverage gaps hide in the method |
| What changed over time | A new system can look like a trend |
| What a row really is | Counts of records are not counts of events |

## How I did it

Name the source, the steps and the choices you made, and link the code. The Data and Code boxes at the bottom are filled in from `story.toml`.
