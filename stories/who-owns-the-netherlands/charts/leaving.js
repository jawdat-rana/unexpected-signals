// Line: share of each year's knowledge migrants who had left the Netherlands
// within five years.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const rows = data.filter((d) => d.year >= 2005 && d.knowledge_left_within_5y_pct !== null && d.knowledge_left_within_5y_pct !== "");
  const height = width < 560 ? 260 : 300;
  const m = { top: 24, right: 56, bottom: 28, left: 44 };
  const x = d3.scaleLinear(d3.extent(rows, (d) => d.year), [m.left, width - m.right]);
  const y = d3.scaleLinear([0, 100], [height - m.bottom, m.top]);
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat((v) => `${v}%`));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(width < 560 ? 4 : 8).tickFormat(d3.format("d")).tickSize(0).tickPadding(8));
  svg.append("path").datum(rows).attr("fill", "none").attr("stroke", theme.signal).attr("stroke-width", 2.5)
    .attr("d", d3.line((d) => x(d.year), (d) => y(d.knowledge_left_within_5y_pct)));
  svg.append("g").selectAll("circle").data(rows).join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.knowledge_left_within_5y_pct)).attr("r", 3.5)
    .attr("fill", theme.signal).attr("stroke", theme.paper).attr("stroke-width", 1.5)
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>Arrived in ${d.year}</strong><br>${d.knowledge_left_within_5y_pct}% had left within 5 years<br>${d3.format(",")(d.knowledge_migrants)} arrived`))
    .on("pointerleave", () => tooltip.hide());
  for (const d of [rows[0], rows[rows.length - 1]]) {
    svg.append("text").attr("class", "label-strong").attr("x", x(d.year)).attr("y", y(d.knowledge_left_within_5y_pct) - 10)
      .attr("text-anchor", d === rows[0] ? "start" : "end").text(`${Math.round(d.knowledge_left_within_5y_pct)}%`);
  }
  return [svg.node(), table(rows, [
    { key: "year", label: "Year of arrival" },
    { key: "knowledge_migrants", label: "Arrived", format: d3.format(",") },
    { key: "knowledge_left_within_5y_pct", label: "Left within 5 years (%)" },
  ])];
}
