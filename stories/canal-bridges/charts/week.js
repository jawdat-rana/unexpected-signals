// One week at the busiest bridge on the northern route, near Den Helder: every planned opening as a mark on a
// 24-hour line, one line per day. Rush hours are shaded.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const days = [...new Set(data.map((d) => d.day))];
  const row = narrow ? 30 : 34;
  const m = { top: 22, right: 12, bottom: 28, left: narrow ? 74 : 96 };
  const height = m.top + m.bottom + row * days.length;
  const x = d3.scaleLinear([0, 24], [m.left, width - m.right]);
  const y = d3.scaleBand(days, [m.top, height - m.bottom]).padding(0.28);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Each day from Monday 9 to Sunday 15 November shows about 30 planned openings at one bridge near Den Helder, spread from early morning to late evening, including the rush hours.");

  for (const [a, b] of [[7, 9], [16, 18]]) {
    svg.append("rect").attr("x", x(a)).attr("width", x(b) - x(a)).attr("y", m.top - 4)
      .attr("height", height - m.bottom - m.top + 4).attr("fill", theme.grid).attr("opacity", 0.6);
    svg.append("text").attr("class", "annotation").attr("x", x((a + b) / 2)).attr("y", m.top - 8)
      .attr("text-anchor", "middle").text("rush");
  }
  // The road is open: a thin grey line per day.
  svg.append("g").selectAll("line").data(days).join("line")
    .attr("x1", x(0)).attr("x2", x(24)).attr("y1", (d) => y(d) + y.bandwidth() / 2).attr("y2", (d) => y(d) + y.bandwidth() / 2)
    .attr("stroke", theme.context).attr("stroke-width", 1);

  const count = d3.rollup(data, (v) => v.length, (d) => d.day);
  svg.append("g").selectAll("text").data(days).join("text")
    .attr("x", m.left - 8).attr("y", (d) => y(d) + y.bandwidth() / 2).attr("dy", "0.35em")
    .attr("text-anchor", "end").attr("fill", theme.ink).style("font-size", "12px")
    .text((d) => (narrow ? d.split(" ").slice(0, 2).join(" ") : d));

  // Openings: at least 2px wide so a 6-minute opening stays visible.
  svg.append("g").selectAll("rect").data(data).join("rect")
    .attr("x", (d) => x(d.start_hour)).attr("width", (d) => Math.max(2, x(d.end_hour) - x(d.start_hour)))
    .attr("y", (d) => y(d.day)).attr("height", y.bandwidth()).attr("rx", 1)
    .attr("fill", theme.signal)
    .on("pointermove", (event, d) => {
      const t = (h) => `${String(Math.floor(h)).padStart(2, "0")}:${String(Math.round((h % 1) * 60)).padStart(2, "0")}`;
      tooltip.show(event, `<strong>${tooltip.esc(d.day)}</strong>Planned open ${t(d.start_hour)}–${t(d.end_hour)}<br>`
        + `<span class="muted">${count.get(d.day)} openings that day</span>`);
    })
    .on("pointerleave", () => tooltip.hide());

  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(narrow ? [0, 6, 12, 18, 24] : d3.range(0, 25, 3))
      .tickSize(0).tickPadding(8).tickFormat((h) => `${String(h % 24).padStart(2, "0")}:00`));

  const fmt = (h) => `${String(Math.floor(h)).padStart(2, "0")}:${String(Math.round((h % 1) * 60)).padStart(2, "0")}`;
  return [svg.node(), table(data, [
    { key: "day", label: "Day" },
    { key: "start_hour", label: "Opens", format: fmt },
    { key: "end_hour", label: "Closes", format: fmt },
  ])];
}
