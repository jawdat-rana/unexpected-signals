// Live bridge openings in each hour of the day, all bridges together. The
// weekday rush hours are drawn in the signal colour.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 260 : 300;
  const m = { top: 12, right: 8, bottom: 28, left: 36 };
  const x = d3.scaleBand(d3.range(24), [m.left, width - m.right]).padding(0.18);
  const y = d3.scaleLinear([0, d3.max(data, (d) => d.openings_per_day)], [height - m.bottom, m.top]).nice();
  const rush = new Set([7, 8, 16, 17]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img").attr("aria-label", "Bar chart of bridge openings by hour of the day. Openings continue through the rush hours and into the night.");
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(6));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(narrow ? [0, 6, 12, 18] : d3.range(0, 24, 3)).tickSize(0).tickPadding(8)
      .tickFormat((h) => `${String(h).padStart(2, "0")}:00`));

  svg.append("g").selectAll("rect").data(data).join("rect")
    .attr("x", (d) => x(d.hour)).attr("width", x.bandwidth())
    .attr("y", (d) => y(d.openings_per_day)).attr("height", (d) => y(0) - y(d.openings_per_day))
    .attr("rx", 2).attr("fill", (d) => (rush.has(d.hour) ? theme.signal : theme.context))
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${String(d.hour).padStart(2, "0")}:00–${String(d.hour).padStart(2, "0")}:59</strong>${d.openings_per_day} openings a day`))
    .on("pointerleave", () => tooltip.hide());

  const key = document.createElement("div");
  key.style.cssText = "display:flex;gap:14px;margin:0 0 6px;font-size:13px;color:var(--ink-2)";
  const sw = (c) => `<svg width="12" height="12" aria-hidden="true"><rect width="12" height="12" rx="2" fill="${c}"/></svg>`;
  key.innerHTML = `<span style="display:inline-flex;gap:6px;align-items:center">${sw(theme.signal)}Rush hours (07–09, 16–18)</span>`
    + `<span style="display:inline-flex;gap:6px;align-items:center">${sw(theme.context)}Other hours</span>`;

  return [key, svg.node(), table(data.map((d) => ({ ...d, label: `${String(d.hour).padStart(2, "0")}:00` })), [
    { key: "label", label: "Hour" },
    { key: "openings_per_day", label: "Openings a day" },
  ])];
}
