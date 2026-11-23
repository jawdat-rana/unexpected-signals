// Bars per year: homes added to the housing stock (context) next to knowledge
// migrants arriving (signal).

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const rows = data.filter((d) => d.year >= 2012 && d.homes_added);
  const narrow = width < 560;
  const height = narrow ? 280 : 320;
  const m = { top: 30, right: 12, bottom: 28, left: 48 };
  const keys = [
    { key: "homes_added", label: "Homes added", color: theme.context },
    { key: "knowledge_migrants", label: "Knowledge migrants arriving", color: theme.signal },
  ];
  const x0 = d3.scaleBand(rows.map((d) => d.year), [m.left, width - m.right]).padding(0.25);
  const x1 = d3.scaleBand(keys.map((k) => k.key), [0, x0.bandwidth()]).padding(0.08);
  const y = d3.scaleLinear([0, d3.max(rows, (d) => d.homes_added)], [height - m.bottom, m.top]).nice();

  const legend = document.createElement("div");
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:13px;color:var(--ink-2)";
  legend.innerHTML = keys.map((k) => `<span style="display:inline-flex;align-items:center;gap:6px">`
    + `<svg width="12" height="12" aria-hidden="true"><rect width="12" height="12" fill="${k.color}"/></svg>${k.label}</span>`).join("");

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat(d3.format("~s")));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x0).tickSize(0).tickPadding(8).tickFormat((v) => (narrow ? `'${String(v).slice(2)}` : v)));
  const g = svg.append("g").selectAll("g").data(rows).join("g").attr("transform", (d) => `translate(${x0(d.year)},0)`);
  g.selectAll("rect").data((d) => keys.map((k) => ({ ...k, year: d.year, value: d[k.key] }))).join("rect")
    .attr("x", (d) => x1(d.key)).attr("width", x1.bandwidth())
    .attr("y", (d) => y(d.value)).attr("height", (d) => y(0) - y(d.value)).attr("fill", (d) => d.color);
  svg.append("rect").attr("x", m.left).attr("y", m.top).attr("width", width - m.left - m.right)
    .attr("height", height - m.top - m.bottom).attr("fill", "transparent")
    .on("pointermove", (event) => {
      const [px] = d3.pointer(event);
      const d = rows.reduce((a, b) => (Math.abs(x0(b.year) + x0.bandwidth() / 2 - px) < Math.abs(x0(a.year) + x0.bandwidth() / 2 - px) ? b : a));
      tooltip.show(event, `<strong>${d.year}</strong><br>Homes added: ${d3.format(",")(d.homes_added)}<br>`
        + `Knowledge migrants arriving: ${d3.format(",")(d.knowledge_migrants)}<br>Family arriving with labour migrants: ${d3.format(",")(d.family_with_labour_migrants)}`);
    })
    .on("pointerleave", () => tooltip.hide());

  const wrap = document.createElement("div");
  wrap.append(legend, svg.node());
  return [wrap, table(rows, [
    { key: "year", label: "Year" },
    { key: "homes_added", label: "Homes added", format: d3.format(",") },
    { key: "knowledge_migrants", label: "Knowledge migrants arriving", format: d3.format(",") },
    { key: "family_with_labour_migrants", label: "Family arriving with labour migrants", format: d3.format(",") },
  ])];
}
