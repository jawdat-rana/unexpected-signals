// Every bridge that reported a live opening to NDW in the period, sized by
// openings. The busiest few are labelled with their place name.

import outline from "./netherlands.js";

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = Math.round(Math.min(760, Math.max(420, width * 1.12)));
  const land = outline.features[0];
  const projection = d3.geoMercator().fitExtent([[8, 8], [width - 8, height - 8]], land);
  const path = d3.geoPath(projection);
  const xy = (d) => projection([d.longitude, d.latitude]);
  const r = d3.scaleSqrt([0, d3.max(data, (d) => d.openings_per_day)], [1.5, narrow ? 10 : 14]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Map of the Netherlands with the bridges that reported live openings. Clusters stand out in Groningen and Friesland, Zeeland near Terneuzen, and around Rotterdam.");
  svg.append("path").attr("d", path(land)).attr("fill", theme.paper2).attr("stroke", theme.rule).attr("stroke-width", 0.75);
  svg.append("path").attr("d", path(outline.features[1])).attr("fill", theme.paper).attr("stroke", theme.rule).attr("stroke-width", 0.5);

  const sorted = [...data].sort((a, b) => b.openings - a.openings);
  svg.append("g").selectAll("circle").data([...sorted].reverse()).join("circle")
    .attr("cx", (d) => xy(d)[0]).attr("cy", (d) => xy(d)[1]).attr("r", (d) => r(d.openings_per_day))
    .attr("fill", theme.signal).attr("fill-opacity", 0.85).attr("stroke", theme.paper2).attr("stroke-width", 1)
    .style("cursor", "pointer")
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>Bridge at ${tooltip.esc(d.place)}</strong>`
      + `${d.openings} openings (${d.openings_per_day} a day)<br>`
      + `<span class="muted">${d.night_openings} between 23:00 and 06:00</span>`))
    .on("pointerleave", () => tooltip.hide());

  // Label the busiest bridge per place, at most five places.
  const seen = new Set();
  const top = sorted.filter((d) => (seen.has(d.place) ? false : seen.add(d.place))).slice(0, narrow ? 3 : 5);
  svg.append("g").attr("class", "annotation").style("pointer-events", "none")
    .selectAll("text").data(top).join("text")
    .attr("x", (d) => xy(d)[0] + r(d.openings_per_day) + 4).attr("y", (d) => xy(d)[1]).attr("dy", "0.35em")
    .attr("paint-order", "stroke").attr("stroke", theme.paper2).attr("stroke-width", 3).attr("stroke-linejoin", "round")
    .attr("fill", theme.ink2).text((d) => d.place);

  return [svg.node(), table(sorted, [
    { key: "place", label: "Place" },
    { key: "openings", label: "Openings" },
    { key: "openings_per_day", label: "A day" },
    { key: "night_openings", label: "Night (23–06)" },
    { key: "rush_hour_openings", label: "Weekday rush hours" },
  ])];
}
