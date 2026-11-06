// Ranked bars: PAC money by parent company's country, with one country highlighted.

const HIGHLIGHT = "Netherlands";
const LABELLED = new Set(["Switzerland", HIGHLIGHT]);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const rows = [...data].sort((a, b) => b.pac_dollars - a.pac_dollars);
  const bar = 18;
  const gap = 6;
  const m = { top: 24, right: 56, bottom: 8, left: width < 480 ? 104 : 120 };
  const height = m.top + m.bottom + rows.length * (bar + gap);

  const x = d3.scaleLinear([0, d3.max(rows, (d) => d.pac_dollars)], [m.left, width - m.right]).nice();
  const y = d3.scaleBand(rows.map((d) => d.country), [m.top, height - m.bottom]).paddingInner(gap / (bar + gap));
  const money = (v) => (v >= 1e6 ? `$${d3.format(".1f")(v / 1e6)}M` : `$${d3.format(".0f")(v / 1e3)}K`);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);

  svg.append("g").attr("class", "grid")
    .attr("transform", `translate(0,${m.top})`)
    .call(d3.axisTop(x).ticks(width < 480 ? 3 : 5).tickSize(-(height - m.top - m.bottom)).tickFormat(""));
  svg.append("g").attr("class", "axis")
    .attr("transform", `translate(0,${m.top})`)
    .call(d3.axisTop(x).ticks(width < 480 ? 3 : 5).tickSize(0).tickPadding(6).tickFormat(money));

  // Bars with a rounded end on the data side only; the baseline end stays square.
  const r = 4;
  const path = (d) => {
    const x0 = x(0);
    const x1 = Math.max(x0 + r, x(d.pac_dollars));
    const y0 = y(d.country);
    const h = y.bandwidth();
    return `M${x0},${y0}H${x1 - r}a${r},${r} 0 0 1 ${r},${r}V${y0 + h - r}`
      + `a${r},${r} 0 0 1 ${-r},${r}H${x0}Z`;
  };

  const rowsG = svg.append("g").selectAll("g").data(rows).join("g");
  rowsG.append("path")
    .attr("d", path)
    .attr("fill", (d) => (d.country === HIGHLIGHT ? theme.signal : theme.context));
  rowsG.append("text")
    .attr("x", m.left - 8)
    .attr("y", (d) => y(d.country) + y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "end")
    .attr("class", (d) => (d.country === HIGHLIGHT ? "label-strong" : null))
    .text((d) => d.country);
  rowsG.filter((d) => LABELLED.has(d.country)).append("text")
    .attr("x", (d) => x(d.pac_dollars) + 6)
    .attr("y", (d) => y(d.country) + y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .attr("class", "label-strong")
    .text((d) => money(d.pac_dollars));

  // Hit target is the whole row, wider than the bar.
  rowsG.append("rect")
    .attr("x", 0).attr("width", width)
    .attr("y", (d) => y(d.country) - gap / 2).attr("height", bar + gap)
    .attr("fill", "transparent")
    .on("pointermove", (event, d) => tooltip.show(event,
      `<strong>${tooltip.esc(d.country)}</strong>${money(d.pac_dollars)} from ${d.pacs} PAC${d.pacs === 1 ? "" : "s"}`
      + `<br><span class="muted">Biggest: ${tooltip.esc(d.top_parents)}</span>`))
    .on("pointerleave", () => tooltip.hide());

  return [svg.node(), table(rows, [
    { key: "country", label: "Country" },
    { key: "pac_dollars", label: "PAC giving", format: (v) => `$${d3.format(",")(v)}` },
    { key: "pacs", label: "PACs" },
    { key: "top_parents", label: "Biggest parents" },
  ])];
}
