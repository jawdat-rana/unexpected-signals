// Every winter's Hellmann cold sum in De Bilt since 1902. Grey bars, the
// winters with an Elfstedentocht in red, KNMI's "cold winter" line at 100.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 380;
  const m = { top: 28, right: 8, bottom: 26, left: 36 };
  const x = d3.scaleBand(data.map((d) => d.winter), [m.left, width - m.right]).paddingInner(0.15);
  const y = d3.scaleLinear([0, 360], [height - m.bottom, m.top]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Bar chart of the Hellmann cold sum in De Bilt for every winter from 1902 to 2026. Tall bars, many with an Elfstedentocht, are spread through the century until 1997. Since 2014 every bar is short.");

  svg.append("g").attr("class", "grid").selectAll("line").data([100, 200, 300]).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y)
    .attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).tickValues([0, 100, 200, 300]).tickSize(0))
    .call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(data.map((d) => d.winter).filter((w) => w % (narrow ? 25 : 10) === 0)).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  // The last 13 winters, all "zacht" or milder.
  const since = data.filter((d) => d.winter >= 2014);
  svg.append("rect").attr("x", x(2014) - 1).attr("width", x(2026) + x.bandwidth() - x(2014) + 2)
    .attr("y", m.top).attr("height", height - m.bottom - m.top).attr("fill", theme.context).attr("fill-opacity", 0.18);

  svg.append("g").selectAll("rect").data(data).join("rect")
    .attr("x", (d) => x(d.winter)).attr("width", x.bandwidth())
    .attr("y", (d) => y(Math.max(d.hellmann, 1.5))).attr("height", (d) => y(0) - y(Math.max(d.hellmann, 1.5)))
    .attr("fill", (d) => (d.held ? theme.signal : theme.context))
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>Winter ${d.winter}</strong>`
      + `Hellmann ${d.hellmann}<br>${d.ice_days} ice days`
      + (d.held ? "<br>Elfstedentocht held" : "")
      + (d.potential && !d.held ? "<br><span class=\"muted\">Cold enough, no tour</span>" : "")))
    .on("pointerleave", () => tooltip.hide());

  svg.append("line").attr("x1", m.left).attr("x2", width - m.right).attr("y1", y(100)).attr("y2", y(100))
    .attr("stroke", theme.ink2).attr("stroke-dasharray", "3 3");
  const note = svg.append("g").attr("class", "annotation").attr("fill", theme.ink2).style("pointer-events", "none");
  note.append("text").attr("x", x(2014) - 6).attr("y", y(100) - 5).attr("text-anchor", "end")
    .attr("paint-order", "stroke").attr("stroke", theme.paper).attr("stroke-width", 3)
    .text(narrow ? "Cold winter" : "Above 100: a cold winter (KNMI)");
  const label = (winter, text, dx = 0, anchor = "middle", top = null) => {
    const d = data.find((r) => r.winter === winter);
    note.append("text").attr("x", x(winter) + x.bandwidth() / 2 + dx).attr("y", y(top ?? d.hellmann) - 6)
      .attr("text-anchor", anchor).text(text);
  };
  label(1947, "1947", -2, "end");
  label(1963, "1963");
  label(1997, narrow ? "1997" : "1997, last tour", 0, "middle", 160);
  note.append("text").attr("x", x(2026) + x.bandwidth()).attr("y", m.top - 8).attr("text-anchor", "end")
    .text(narrow ? "Since 2014: all mild" : "Since 2014: 13 mild winters in a row");

  return [svg.node(), table([...data].reverse(), [
    { key: "winter", label: "Winter" },
    { key: "hellmann", label: "Hellmann" },
    { key: "ice_days", label: "Ice days" },
    { key: "tg15n", label: "Coldest 15 days (°C)" },
    { key: "held", label: "Elfstedentocht", format: (v) => (v ? "Yes" : "") },
  ])];
}
