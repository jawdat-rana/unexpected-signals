// Grouped columns per election cycle: money through pro-Israel PACs (signal)
// against all other foreign-policy, diaspora and faith-based groups combined.

const SERIES = [
  { key: "Pro-Israel", label: "Pro-Israel PACs", token: "signal" },
  { key: "All other groups", label: "All other groups combined", token: "context" },
];

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 360;
  const m = { top: 24, right: 8, bottom: 28, left: 48 };
  const cycles = [...new Set(data.map((d) => d.cycle))].sort();
  const color = new Map(SERIES.map((s) => [s.key, theme[s.token]]));
  const money = (v) => (v === 0 ? "$0" : v >= 1e6 ? `$${d3.format(".0f")(v / 1e6)}M` : `$${d3.format(".0f")(v / 1e3)}K`);
  const money1 = (v) => `$${d3.format(".1f")(v / 1e6)}M`;

  const x = d3.scaleBand(cycles, [m.left, width - m.right]).paddingInner(narrow ? 0.25 : 0.35).paddingOuter(0.1);
  const xs = d3.scaleBand(SERIES.map((s) => s.key), [0, x.bandwidth()]).paddingInner(0.08);
  const y = d3.scaleLinear([0, d3.max(data, (d) => d.total)], [height - m.bottom, m.top]).nice();

  const legend = document.createElement("div");
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:13px;color:var(--ink-2)";
  legend.innerHTML = SERIES.map((s) => `<span style="display:inline-flex;align-items:center;gap:6px">`
    + `<svg width="10" height="10" aria-hidden="true"><rect width="10" height="10" rx="2" fill="${color.get(s.key)}"/></svg>`
    + `${s.label}</span>`).join("");

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat(money));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8).tickFormat((c) => (c === 2026 ? "2026*" : c)));

  // Columns with a rounded top only; the baseline end stays square.
  const r = 4;
  const path = (d) => {
    const x0 = x(d.cycle) + xs(d.series);
    const w = xs.bandwidth();
    const yb = y(0);
    const yt = Math.min(yb - r, y(d.total));
    return `M${x0},${yb}V${yt + r}a${r},${r} 0 0 1 ${r},${-r}H${x0 + w - r}`
      + `a${r},${r} 0 0 1 ${r},${r}V${yb}Z`;
  };
  svg.append("g").selectAll("path").data(data).join("path")
    .attr("d", path).attr("fill", (d) => color.get(d.series));

  // Label the pro-Israel totals from 2022 on, where the jump is.
  svg.append("g").attr("class", "label-strong").selectAll("text")
    .data(data.filter((d) => d.series === "Pro-Israel" && d.cycle >= 2022)).join("text")
    .attr("x", (d) => x(d.cycle) + xs(d.series) + xs.bandwidth() / 2)
    .attr("y", (d) => y(d.total) - 6).attr("text-anchor", "middle")
    .style("font-size", narrow ? "11px" : null)
    .text((d) => money(d.total));

  // Hit target: the whole cycle column, so both bars show in one tooltip.
  svg.append("g").selectAll("rect").data(cycles).join("rect")
    .attr("x", (c) => x(c) - (x.step() - x.bandwidth()) / 2).attr("width", x.step())
    .attr("y", m.top).attr("height", height - m.top - m.bottom).attr("fill", "transparent")
    .on("pointermove", (event, c) => tooltip.show(event, `<strong>${c} cycle${c === 2026 ? " (to mid-October)" : ""}</strong>`
      + SERIES.map((s) => {
        const d = data.find((r) => r.cycle === c && r.series === s.key);
        return `${s.label}: ${money1(d ? d.total : 0)}`;
      }).join("<br>")))
    .on("pointerleave", () => tooltip.hide());

  const wrap = document.createElement("div");
  wrap.append(legend, svg.node());
  return [wrap, table(data, [
    { key: "cycle", label: "Cycle" },
    { key: "series", label: "Groups" },
    { key: "total", label: "Total", format: (v) => `$${d3.format(",")(v)}` },
    { key: "primary", label: "Of which primaries", format: (v) => `$${d3.format(",")(v)}` },
  ])];
}
