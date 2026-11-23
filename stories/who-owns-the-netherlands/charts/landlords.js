// Line: homes owned by private landlords (companies, individuals, investors),
// on 1 January each year. The last step is the first fall in the series.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const height = width < 560 ? 260 : 300;
  const m = { top: 24, right: 20, bottom: 28, left: 52 };
  const x = d3.scaleLinear(d3.extent(data, (d) => d.year), [m.left, width - m.right]);
  const y = d3.scaleLinear([800000, 1250000], [height - m.bottom, m.top]);
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat((v) => `${d3.format(".2~f")(v / 1e6)}M`));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(width < 560 ? 4 : 8).tickFormat(d3.format("d")).tickSize(0).tickPadding(8));
  const line = d3.line((d) => x(d.year), (d) => y(d.landlord));
  svg.append("path").datum(data).attr("fill", "none").attr("stroke", theme.context).attr("stroke-width", 2).attr("d", line);
  svg.append("path").datum(data.slice(-2)).attr("fill", "none").attr("stroke", theme.signal).attr("stroke-width", 2.5).attr("d", line);
  svg.append("g").selectAll("circle").data(data).join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.landlord)).attr("r", 3.5)
    .attr("fill", (d, i) => (i === data.length - 1 ? theme.signal : theme.context)).attr("stroke", theme.paper).attr("stroke-width", 1.5)
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>1 January ${d.year}</strong><br>${d3.format(",")(d.landlord)} homes owned by private landlords<br>${(100 * d.landlord / d.total).toFixed(1)}% of all homes`))
    .on("pointerleave", () => tooltip.hide());
  const last = data[data.length - 1];
  svg.append("text").attr("class", "label-strong").attr("x", x(last.year)).attr("y", y(last.landlord) + 20)
    .attr("text-anchor", "end").text("First fall since 2019");
  return [svg.node(), table(data, [
    { key: "year", label: "1 January" },
    { key: "landlord", label: "Private landlords", format: d3.format(",") },
    { key: "corporation", label: "Housing associations", format: d3.format(",") },
    { key: "owner", label: "Owner-occupied", format: d3.format(",") },
    { key: "total", label: "All homes", format: d3.format(",") },
  ])];
}
