// Two indexed lines: flaws published (signal) and flaws exploited (second
// colour), each relative to its own 2025 monthly average = 100.

const SERIES = [
  { key: "Flaws published", label: "Flaws published (CVE List)", token: "signal" },
  { key: "Flaws exploited", label: "Flaws exploited (CISA KEV)", token: "categorical1" },
];

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 380;
  const m = { top: 24, right: narrow ? 64 : 140, bottom: 28, left: 40 };
  const color = (k) => (k === "Flaws published" ? theme.signal : theme.categorical[1]);
  const groups = d3.group(data, (d) => d.series);

  const x = d3.scaleUtc(d3.extent(data, (d) => d.month), [m.left, width - m.right]);
  const y = d3.scaleLinear([0, d3.max(data, (d) => d.index)], [height - m.bottom, m.top]).nice();

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 4 : 6).tickSizeOuter(0).tickFormat(d3.utcFormat("%b %Y")));

  // The 2025 average, the line both series are measured against.
  svg.append("path").attr("class", "annotation-line")
    .attr("d", `M${m.left},${y(100)}H${width - m.right}`);

  const line = d3.line((d) => x(d.month), (d) => y(d.index)).curve(d3.curveMonotoneX);
  for (const s of SERIES) {
    const rows = groups.get(s.key);
    svg.append("path").datum(rows).attr("fill", "none").attr("stroke", color(s.key))
      .attr("stroke-width", 2.5).attr("d", line);
    const last = rows[rows.length - 1];
    svg.append("circle").attr("cx", x(last.month)).attr("cy", y(last.index)).attr("r", 4)
      .attr("fill", color(s.key)).attr("stroke", theme.paper).attr("stroke-width", 2);
    svg.append("text").attr("class", "label-strong").attr("x", x(last.month) + 8)
      .attr("y", y(last.index) + 4).attr("fill", color(s.key))
      .text(narrow ? d3.format(".0f")(last.index) : `${s.key.replace("Flaws ", "")}: ${d3.format(".0f")(last.index)}`);
  }

  const months = [...groups.get("Flaws published")].map((d) => d.month);
  const fmt = d3.utcFormat("%B %Y");
  const focus = svg.append("line").attr("stroke", theme.muted).attr("y1", m.top).attr("y2", height - m.bottom)
    .style("display", "none");
  svg.append("rect").attr("x", m.left).attr("y", m.top).attr("width", width - m.left - m.right)
    .attr("height", height - m.top - m.bottom).attr("fill", "transparent")
    .on("pointerleave", () => { focus.style("display", "none"); tooltip.hide(); })
    .on("pointermove", (event) => {
      const i = d3.bisectCenter(months, x.invert(d3.pointer(event)[0]));
      const p = groups.get("Flaws published")[i];
      const e = groups.get("Flaws exploited")[i];
      focus.style("display", null).attr("x1", x(p.month)).attr("x2", x(p.month));
      tooltip.show(event, `<strong>${fmt(p.month)}</strong>`
        + `Published: ${d3.format(",")(p.count)} (index ${d3.format(".0f")(p.index)})<br>`
        + `Exploited: ${e.count} (index ${d3.format(".0f")(e.index)})`);
    });

  const legend = document.createElement("div");
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:13px;color:var(--ink-2)";
  legend.innerHTML = SERIES.map((s) => `<span style="display:inline-flex;align-items:center;gap:6px">`
    + `<svg width="14" height="4" aria-hidden="true"><rect width="14" height="3" fill="${color(s.key)}"/></svg>${s.label}</span>`).join("");

  const rows = months.map((mo, i) => ({
    month: mo, published: groups.get("Flaws published")[i].count, exploited: groups.get("Flaws exploited")[i].count,
  }));
  return [legend, svg.node(), table(rows, [
    { key: "month", label: "Month", format: fmt },
    { key: "published", label: "Flaws published", format: d3.format(",") },
    { key: "exploited", label: "Added to CISA KEV" },
  ])];
}
