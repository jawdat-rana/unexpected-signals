// Observable Plot template: a scatter with a few groups.
//
// Plot (built on D3 by the same people) is the quick option: a full chart in a
// dozen lines. Reach for it first; switch to raw D3 when you need full control.
// Docs: https://observablehq.com/plot/

export default function draw({ data, width, Plot, theme }) {
  return Plot.plot({
    ...theme.plot,
    width,
    height: Math.max(260, Math.min(420, width * 0.6)),
    grid: true,
    x: { label: "Size →" },
    y: { label: "↑ Rate (%)" },
    color: {
      // Fixed order, so a group keeps its colour in every chart of the story.
      domain: ["North", "Middle", "South"],
      range: theme.categorical,
      legend: true,
      style: { background: "transparent" },
    },
    marks: [
      Plot.linearRegressionY(data, { x: "size", y: "rate", stroke: theme.muted, strokeWidth: 1 }),
      Plot.dot(data, {
        x: "size",
        y: "rate",
        fill: "region",
        r: 4.5,
        stroke: theme.paper,
        strokeWidth: 1.5,
        tip: true,
        channels: { Place: "place" },
      }),
      Plot.text(
        data.filter((d) => d.rate === Math.max(...data.map((r) => r.rate))),
        { x: "size", y: "rate", text: "place", dy: -12, fill: theme.ink, fontWeight: 600 },
      ),
    ],
  });
}
