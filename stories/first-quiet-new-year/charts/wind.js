// Each New Year's night as a dot: average wind speed against how much fine dust
// (PM2.5) the night added. The curve is fitted on the years with fireworks on
// sale: the dust you'd expect for that much wind.

const BANS = new Set(["2020/21", "2021/22"]);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 360;
  const m = { top: 20, right: 16, bottom: 36, left: 40 };
  const rows = data.filter((d) => d.country === "NL" && d.formula === "PM25" && d.wind_ms != null);
  const newest = rows.at(-1).season;
  const sold = rows.filter((d) => d.status === "sold" && d.median_excess > 0);
  // log(excess) = a + b * wind, the same fit as prepare.py
  const mx = d3.mean(sold, (d) => d.wind_ms), my = d3.mean(sold, (d) => Math.log(d.median_excess));
  const b = d3.sum(sold, (d) => (d.wind_ms - mx) * (Math.log(d.median_excess) - my)) / d3.sum(sold, (d) => (d.wind_ms - mx) ** 2);
  const a = my - b * mx;

  const x = d3.scaleLinear([0, 14], [m.left, width - m.right]);
  const y = d3.scaleLinear([0, Math.max(160, d3.max(rows, (d) => d.median_excess))], [height - m.bottom, m.top]).nice();
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Scatter plot of New Year's nights in the Netherlands: wind speed against the extra fine dust. Windy nights stay clean, still nights fill up with smoke. A curve shows what to expect for each wind speed.");

  svg.append("g").selectAll("line").data(y.ticks(4)).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y).attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(0)).call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(7).tickSize(0)).call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted)
    .call((g) => g.append("text").attr("x", width - m.right).attr("y", 30).attr("text-anchor", "end")
      .attr("fill", theme.muted).text("Wind, metres per second →"));

  const curve = d3.range(1.5, 13.1, 0.25).map((w) => [w, Math.exp(a + b * w)]).filter((d) => d[1] <= y.domain()[1]);
  svg.append("path").attr("d", d3.line().x((d) => x(d[0])).y((d) => y(d[1]))(curve))
    .attr("fill", "none").attr("stroke", theme.ink2).attr("stroke-width", 1.2).attr("stroke-dasharray", "2 3");

  const color = (d) => d.season === newest ? theme.signal : BANS.has(d.season) ? theme.ink : theme.context;
  svg.append("g").selectAll("circle").data(rows).join("circle")
    .attr("cx", (d) => x(d.wind_ms)).attr("cy", (d) => y(d.median_excess)).attr("r", narrow ? 5 : 6)
    .attr("fill", (d) => BANS.has(d.season) ? theme.paper : color(d))
    .attr("stroke", color).attr("stroke-width", 2)
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>${d.season}${BANS.has(d.season) ? " (covid ban)" : ""}</strong>`
      + `Wind ${d.wind_ms} m/s<br>Extra PM2.5: ${d.median_excess} µg/m³<br>Expected for that wind: ${d.expected_excess}`))
    .on("pointerleave", () => tooltip.hide());

  const note = svg.append("g").attr("class", "annotation").style("pointer-events", "none")
    .attr("paint-order", "stroke").attr("stroke", theme.paper).attr("stroke-width", 3);
  for (const d of rows) {
    // Label the years the text talks about; the rest are in the tooltip and table.
    const named = BANS.has(d.season) || d.season === newest || (!narrow && ["2019/20", "2024/25"].includes(d.season));
    if (!named) continue;
    note.append("text").attr("x", x(d.wind_ms) + 9).attr("y", y(d.median_excess)).attr("dy", "0.32em")
      .attr("fill", BANS.has(d.season) || d.season === newest ? theme.ink : theme.muted)
      .text(BANS.has(d.season) ? `${d.season} ban` : d.season);
  }

  return [svg.node(), table(rows, [
    { key: "season", label: "New Year" },
    { key: "status", label: "Fireworks" },
    { key: "wind_ms", label: "Wind (m/s)" },
    { key: "median_excess", label: "Extra PM2.5 (µg/m³)" },
    { key: "expected_excess", label: "Expected for the wind" },
    { key: "vs_expected", label: "Actual ÷ expected" },
  ])];
}
