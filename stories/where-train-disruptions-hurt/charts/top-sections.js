// The ten sections of track where disruptions caught the most journeys in 2025.
// Bars: journeys caught. Label: hours disrupted and passengers a day, the two
// things that multiply into the bar.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const top = data.filter((d) => d.passengers > 0)
    .sort((p, q) => q.trips_hit - p.trips_hit).slice(0, 10)
    .map((d) => ({ ...d, name: `${d.from_name} – ${d.to_name}`, schiphol: d.from_code === "SHL" || d.to_code === "SHL" }));

  const row = narrow ? 46 : 30;
  const m = { top: 4, right: narrow ? 40 : 150, bottom: 22, left: narrow ? 8 : 330 };
  const height = m.top + m.bottom + row * top.length;
  const x = d3.scaleLinear([0, d3.max(top, (d) => d.trips_hit)], [m.left, width - m.right]).nice();
  const y = d3.scaleBand(top.map((d) => d.name), [m.top, height - m.bottom]).padding(narrow ? 0.55 : 0.3);
  const millions = (v) => `${d3.format(".1f")(v / 1e6)}M`;

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 3 : 6).tickSize(-(height - m.top - m.bottom)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 3 : 6).tickSize(0).tickPadding(6).tickFormat((v) => (v ? millions(v) : "0")));

  svg.append("g").selectAll("rect").data(top).join("rect")
    .attr("x", m.left).attr("y", (d) => y(d.name)).attr("height", y.bandwidth())
    .attr("width", (d) => x(d.trips_hit) - m.left)
    .attr("fill", (d) => (d.schiphol ? theme.signal : theme.context))
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.name)}</strong>`
      + `${d3.format(",")(d.passengers)} passengers a working day<br>${Math.round(d.hours)} hours disrupted<br>`
      + `<span class="muted">${tooltip.esc(d.top_causes)}</span>`))
    .on("pointerleave", () => tooltip.hide());

  // Name: left of the bar on wide screens, above it on narrow ones.
  svg.append("g").selectAll("text").data(top).join("text")
    .attr("class", (d) => (d.schiphol ? "label-strong" : null))
    .attr("x", narrow ? m.left : m.left - 8)
    .attr("y", (d) => (narrow ? y(d.name) - 5 : y(d.name) + y.bandwidth() / 2))
    .attr("dy", narrow ? 0 : "0.35em").attr("text-anchor", narrow ? "start" : "end")
    .attr("fill", theme.ink).text((d) => d.name);

  // Value: journeys, then hours x passengers.
  svg.append("g").attr("class", "annotation").selectAll("text").data(top).join("text")
    .attr("x", (d) => x(d.trips_hit) + 5)
    .attr("y", (d) => y(d.name) + y.bandwidth() / 2).attr("dy", "0.35em")
    // Narrow screens get the total only; the table and tooltip have the rest.
    .text((d) => (narrow ? millions(d.trips_hit)
      : `${millions(d.trips_hit)} · ${Math.round(d.hours)}h × ${Math.round(d.passengers / 1000)}k/day`));

  return [svg.node(), table(top, [
    { key: "name", label: "Section" },
    { key: "trips_hit", label: "Journeys caught", format: d3.format(",") },
    { key: "hours", label: "Hours disrupted", format: (v) => d3.format(",")(Math.round(v)) },
    { key: "passengers", label: "Passengers a working day", format: d3.format(",") },
    { key: "top_causes", label: "Main causes (hours)" },
  ])];
}
