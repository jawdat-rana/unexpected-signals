// Lines per cycle: money spent on primary races, pro-Israel PACs (signal)
// against all other groups combined (context).

const SERIES = [
  { key: "Pro-Israel", label: "Pro-Israel PACs", token: "signal" },
  { key: "All other groups", label: "All other groups", token: "context" },
];

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 280 : 320;
  const m = { top: 20, right: narrow ? 70 : 140, bottom: 28, left: 48 };
  const cycles = [...new Set(data.map((d) => d.cycle))].sort();
  const color = new Map(SERIES.map((s) => [s.key, theme[s.token]]));
  const money = (v) => (v === 0 ? "$0" : `$${d3.format(".0f")(v / 1e6)}M`);
  const money1 = (v) => `$${d3.format(".1f")(v / 1e6)}M`;

  const x = d3.scalePoint(cycles, [m.left + 12, width - m.right]);
  const y = d3.scaleLinear([0, d3.max(data, (d) => d.primary)], [height - m.bottom, m.top]).nice();

  const legend = document.createElement("div");
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:13px;color:var(--ink-2)";
  legend.innerHTML = SERIES.map((s) => `<span style="display:inline-flex;align-items:center;gap:6px">`
    + `<svg width="16" height="10" aria-hidden="true"><line x1="0" x2="16" y1="5" y2="5" stroke="${color.get(s.key)}" stroke-width="2"/></svg>`
    + `${s.label}</span>`).join("");

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat(money));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8).tickFormat((c) => (c === 2026 ? "2026*" : c)));

  const line = d3.line().x((d) => x(d.cycle)).y((d) => y(d.primary));
  for (const s of SERIES) {
    const rows = data.filter((d) => d.series === s.key).sort((a, b) => a.cycle - b.cycle);
    svg.append("path").datum(rows).attr("d", line).attr("fill", "none")
      .attr("stroke", color.get(s.key)).attr("stroke-width", 2);
    svg.append("g").selectAll("circle").data(rows).join("circle")
      .attr("cx", (d) => x(d.cycle)).attr("cy", (d) => y(d.primary)).attr("r", 4)
      .attr("fill", color.get(s.key)).attr("stroke", theme.paper).attr("stroke-width", 2);
    // Direct label at the line's end.
    const last = rows[rows.length - 1];
    svg.append("text").attr("x", x(last.cycle) + 10).attr("y", y(last.primary)).attr("dy", "0.35em")
      .attr("class", s.key === "Pro-Israel" ? "label-strong" : "annotation")
      .text(narrow ? money(last.primary) : `${money1(last.primary)} ${s.key === "Pro-Israel" ? "pro-Israel" : "all others"}`);
  }

  // Crosshair tooltip per cycle.
  const rule = svg.append("line").attr("y1", m.top).attr("y2", height - m.bottom)
    .attr("stroke", theme.muted).attr("stroke-width", 1).style("display", "none");
  svg.append("rect").attr("x", m.left).attr("width", width - m.left - m.right)
    .attr("y", m.top).attr("height", height - m.top - m.bottom).attr("fill", "transparent")
    .on("pointermove", (event) => {
      const [px] = d3.pointer(event);
      const c = cycles.reduce((a, b) => (Math.abs(x(b) - px) < Math.abs(x(a) - px) ? b : a));
      rule.attr("x1", x(c)).attr("x2", x(c)).style("display", null);
      tooltip.show(event, `<strong>Primaries, ${c} cycle${c === 2026 ? " (to mid-October)" : ""}</strong>`
        + SERIES.map((s) => {
          const d = data.find((r) => r.cycle === c && r.series === s.key);
          const share = d && d.total ? ` (${Math.round((100 * d.primary) / d.total)}% of its total)` : "";
          return `${s.label}: ${money1(d ? d.primary : 0)}${share}`;
        }).join("<br>"));
    })
    .on("pointerleave", () => { rule.style("display", "none"); tooltip.hide(); });

  const wrap = document.createElement("div");
  wrap.append(legend, svg.node());
  return [wrap, table(data, [
    { key: "cycle", label: "Cycle" },
    { key: "series", label: "Groups" },
    { key: "primary", label: "Primaries", format: (v) => `$${d3.format(",")(v)}` },
    { key: "total", label: "Total", format: (v) => `$${d3.format(",")(v)}` },
  ])];
}
