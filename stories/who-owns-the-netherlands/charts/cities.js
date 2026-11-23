// Horizontal bars: Indian nationals who moved to each municipality in
// 2023-2025, per 1,000 homes there. Top 12 municipalities by number of arrivals.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const rows = data.slice().sort((a, b) => b.indian_arrivals - a.indian_arrivals).slice(0, 12)
    .sort((a, b) => b.per_1000_homes - a.per_1000_homes);
  const avg = 3.5;
  const narrow = width < 560;
  const m = { top: 24, right: 60, bottom: 24, left: narrow ? 110 : 150 };
  const bar = 22;
  const height = m.top + m.bottom + rows.length * bar;
  const x = d3.scaleLinear([0, d3.max(rows, (d) => d.per_1000_homes)], [m.left, width - m.right]).nice();
  const y = d3.scaleBand(rows.map((d) => d.name), [m.top, height - m.bottom]).padding(0.25);
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).tickSize(0).tickPadding(8).tickFormat((v) => v.replace("'s-Gravenhage", "The Hague")));
  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", m.left).attr("y", (d) => y(d.name)).attr("height", y.bandwidth())
    .attr("width", (d) => x(d.per_1000_homes) - m.left)
    .attr("fill", (d) => (d.per_1000_homes >= 15 ? theme.signal : theme.context))
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.name)}</strong><br>`
      + `${d3.format(",")(d.indian_arrivals)} Indian nationals moved here in 2023–2025 (${d.share_of_national_pct}% of the national total)<br>`
      + `${d.per_1000_homes} per 1,000 homes<br>Homes: ${d.owner_pct}% owned, ${d.corporation_pct}% housing association, ${d.landlord_pct}% private landlord`))
    .on("pointerleave", () => tooltip.hide());
  svg.append("g").selectAll("text").data(rows).join("text").attr("class", "annotation")
    .attr("x", (d) => x(d.per_1000_homes) + 4).attr("y", (d) => y(d.name) + y.bandwidth() / 2).attr("dy", "0.35em")
    .text((d) => d.per_1000_homes);
  svg.append("line").attr("class", "annotation-line").attr("x1", x(avg)).attr("x2", x(avg))
    .attr("y1", m.top - 6).attr("y2", height - m.bottom);
  svg.append("text").attr("class", "annotation").attr("x", x(avg) + 4).attr("y", m.top - 10)
    .text(`Netherlands: ${avg}`);
  return [svg.node(), table(data.slice(0, 25), [
    { key: "name", label: "Municipality" },
    { key: "indian_arrivals", label: "Indian nationals arriving, 2023–2025", format: d3.format(",") },
    { key: "share_of_national_pct", label: "Share of national (%)" },
    { key: "per_1000_homes", label: "Per 1,000 homes" },
    { key: "landlord_pct", label: "Private landlord homes (%)" },
  ])];
}
