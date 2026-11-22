// Planned openings in the weekday rush hours (07-09 and 16-18), one dot per
// bridge, grouped by route. Amsterdam's city bridges sit near zero.

const ROUTE = {
  north: "Den Helder – Zaanstad",
  amsterdam: "Amsterdam – Leimuiden",
  haarlem: "Haarlem – Sassenheim",
};

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const routes = ["north", "amsterdam", "haarlem"];
  const m = { top: 8, right: 16, bottom: 34, left: narrow ? 12 : 170 };
  const band = narrow ? 74 : 56;
  const height = m.top + m.bottom + band * routes.length;
  const x = d3.scaleLinear([0, Math.ceil(d3.max(data, (d) => d.rush_hour_openings) + 1)], [m.left, width - m.right]);
  const y = d3.scaleBand(routes, [m.top, height - m.bottom]).padding(0.2);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Dot chart of rush-hour openings per bridge. Bridges on the Den Helder to Zaanstad route open 4 to 11 times in the weekday rush hours; most bridges in Amsterdam open less than twice.");

  svg.append("g").attr("class", "grid").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(6).tickSize(-(height - m.top - m.bottom)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(6).tickSize(0).tickPadding(8));

  svg.append("g").selectAll("text").data(routes).join("text")
    .attr("class", (r) => (r === "north" ? "label-strong" : null)).attr("fill", theme.ink)
    .attr("x", narrow ? m.left : m.left - 12)
    .attr("y", (r) => (narrow ? y(r) + 10 : y(r) + y.bandwidth() / 2)).attr("dy", "0.35em")
    .attr("text-anchor", narrow ? "start" : "end").text((r) => ROUTE[r]);

  // Dots jittered vertically by a fixed pattern, so reloads look the same.
  const jitter = (i) => ((i * 7) % 11) / 10 - 0.5;
  const rows = routes.flatMap((r) => data.filter((d) => d.route === r)
    .map((d, i) => ({ ...d, cy: y(r) + y.bandwidth() * (narrow ? 0.65 : 0.5) + jitter(i) * y.bandwidth() * (narrow ? 0.4 : 0.6) })));
  svg.append("g").selectAll("circle").data(rows).join("circle")
    .attr("cx", (d) => x(d.rush_hour_openings)).attr("cy", (d) => d.cy).attr("r", 5)
    .attr("fill", (d) => (d.route === "north" ? theme.signal : theme.context))
    .attr("stroke", theme.paper).attr("stroke-width", 1.5)
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>Bridge near ${tooltip.esc(d.near)}</strong>`
      + `${d.rush_hour_openings} planned openings in the rush hours of an average weekday`))
    .on("pointerleave", () => tooltip.hide());

  svg.append("text").attr("class", "annotation").attr("x", width - m.right).attr("y", height - 4)
    .attr("text-anchor", "end").text("Openings per weekday, 07–09 and 16–18 →");

  return [svg.node(), table([...data].sort((a, b) => b.rush_hour_openings - a.rush_hour_openings), [
    { key: "near", label: "Near" },
    { key: "route", label: "Route", format: (v) => ROUTE[v] },
    { key: "rush_hour_openings", label: "Rush-hour openings (weekday)" },
    { key: "weekday_openings", label: "All openings (weekday)" },
  ])];
}
