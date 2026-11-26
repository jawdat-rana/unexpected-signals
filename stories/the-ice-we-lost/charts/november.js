// The first weeks of November in De Bilt, every year since 1901. One dot a
// year, this year in red, with a dashed line at this year's level so the
// colder years (below it) stand out.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 260 : 320;
  const m = { top: 28, right: 12, bottom: 26, left: 36 };
  const last = data[data.length - 1];
  const days = last.days;
  const x = d3.scaleLinear([data[0].year - 1, last.year + 1], [m.left, width - m.right]);
  const y = d3.scaleLinear([0, 11], [height - m.bottom, m.top]);
  const colder = data.filter((d) => d.mean < last.mean && d.year !== last.year);
  const since = colder[colder.length - 1];

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", `Dot chart of the mean temperature in De Bilt from 1 to ${days} November, every year since ${data[0].year}. This year, ${last.mean} °C, is among the colder dots and the coldest since ${since.year}, though colder Novembers were common before 1990.`);

  svg.append("g").attr("class", "grid").selectAll("line").data([2, 4, 6, 8, 10]).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y)
    .attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).tickValues([0, 2, 4, 6, 8, 10]).tickFormat((v) => `${v}°`).tickSize(0))
    .call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(d3.range(1925, last.year, narrow ? 25 : 25)).tickFormat(d3.format("d")).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  svg.append("line").attr("x1", m.left).attr("x2", width - m.right)
    .attr("y1", y(last.mean)).attr("y2", y(last.mean))
    .attr("stroke", theme.ink2).attr("stroke-dasharray", "3 3");

  svg.append("g").selectAll("circle").data(data).join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.mean))
    .attr("r", (d) => (d.year === last.year ? 5 : narrow ? 2.5 : 3))
    .attr("fill", (d) => (d.year === last.year ? theme.signal : theme.context))
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>November ${d.year}</strong>`
      + `1–${days} November: ${d.mean} °C`
      + (d.winter_hellmann !== "" && d.winter_hellmann != null
        ? `<br>Winter after: Hellmann ${d.winter_hellmann}${d.winter_hellmann > 100 ? " (cold)" : ""}` : "")))
    .on("pointerleave", () => tooltip.hide());

  const note = svg.append("g").attr("class", "annotation").attr("fill", theme.ink2).style("pointer-events", "none");
  const label = (d, text, dy, anchor = "middle") => note.append("text")
    .attr("x", x(d.year)).attr("y", y(d.mean) + dy).attr("text-anchor", anchor)
    .attr("paint-order", "stroke").attr("stroke", theme.paper).attr("stroke-width", 3).text(text);
  label(last, `${last.year}: ${last.mean.toFixed(1)}°`, -10, "end");
  for (const [year, anchor] of [[1993, "end"], [1998, "start"]]) {
    const d = data.find((r) => r.year === year);
    if (d) label(d, String(year), 16, anchor);
  }

  return [svg.node(), table([...data].reverse(), [
    { key: "year", label: "Year" },
    { key: "mean", label: `1–${days} Nov (°C)` },
    { key: "winter_hellmann", label: "Hellmann, winter after" },
  ])];
}
