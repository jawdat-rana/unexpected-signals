// Ice days per winter at the 14 KNMI stations with long records: the open ring
// is 1951-1988, the red dot 1989-2026. The ring is always bigger.

import outline from "./netherlands.js";

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = Math.round(Math.min(720, Math.max(420, width * 1.12)));
  const land = outline.features[0];
  const projection = d3.geoMercator().fitExtent([[8, 8], [width - 8, height - 8]], land);
  const path = d3.geoPath(projection);
  const xy = (d) => projection([d.lon, d.lat]);
  const r = d3.scaleSqrt([0, 16], [0, narrow ? 20 : 32]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Map of the Netherlands with 14 weather stations. At every station the red dot for ice days since 1989 is about half the size of the ring for 1951 to 1988.");
  svg.append("path").attr("d", path(land)).attr("fill", theme.paper2).attr("stroke", theme.rule).attr("stroke-width", 0.75);
  svg.append("path").attr("d", path(outline.features[1])).attr("fill", theme.paper).attr("stroke", theme.rule).attr("stroke-width", 0.5);

  const stations = svg.append("g").selectAll("g").data(data).join("g")
    .attr("transform", (d) => `translate(${xy(d)})`).style("cursor", "pointer")
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.name)}</strong>`
      + `Ice days a winter: ${d.ice_days_early} → ${d.ice_days_late}<br>`
      + `Cold winters: ${d.cold_early}% → ${d.cold_late}%<br>`
      + `<span class="muted">1951–1988 → 1989–2026</span>`))
    .on("pointerleave", () => tooltip.hide());
  stations.append("circle").attr("r", (d) => r(d.ice_days_early))
    .attr("fill", theme.context).attr("fill-opacity", 0.45).attr("stroke", theme.ink2).attr("stroke-width", 1);
  stations.append("circle").attr("r", (d) => r(d.ice_days_late))
    .attr("fill", theme.signal).attr("fill-opacity", 0.85);

  const named = new Set(narrow ? ["Leeuwarden Airport", "Vlissingen", "Maastricht Airport"]
    : ["Leeuwarden Airport", "Groningen Airport Eelde", "De Bilt", "Twenthe Airport", "Vlissingen", "Maastricht Airport"]);
  const place = (d) => ({ "Leeuwarden Airport": "left", "De Bilt": "below" })[d.name] ?? "right";
  svg.append("g").attr("class", "annotation").style("pointer-events", "none")
    .selectAll("text").data(data.filter((d) => named.has(d.name))).join("text")
    .attr("x", (d) => xy(d)[0] + (place(d) === "left" ? -1 : place(d) === "below" ? 0 : 1) * (r(d.ice_days_early) + 4))
    .attr("y", (d) => xy(d)[1] + (place(d) === "below" ? r(d.ice_days_early) + 12 : 0)).attr("dy", "0.35em")
    .attr("text-anchor", (d) => ({ left: "end", below: "middle" })[place(d)] ?? "start")
    .attr("paint-order", "stroke").attr("stroke", theme.paper2).attr("stroke-width", 3).attr("stroke-linejoin", "round")
    .attr("fill", theme.ink2).text((d) => `${d.name.replace(/ Airport| Eelde/g, "")} ${d.ice_days_early} → ${d.ice_days_late}`);

  // Legend
  const legend = svg.append("g").attr("class", "annotation").attr("transform", `translate(14, ${height - 58})`).attr("fill", theme.ink2);
  legend.append("circle").attr("cx", 10).attr("r", 9).attr("fill", theme.context).attr("fill-opacity", 0.45).attr("stroke", theme.ink2).attr("stroke-width", 1.25);
  legend.append("text").attr("x", 26).attr("dy", "0.35em").text("1951–1988");
  legend.append("circle").attr("cx", 10).attr("cy", 26).attr("r", 6).attr("fill", theme.signal);
  legend.append("text").attr("x", 26).attr("y", 26).attr("dy", "0.35em").text("1989–2026");

  return [svg.node(), table(data, [
    { key: "name", label: "Station" },
    { key: "ice_days_early", label: "Ice days 1951–88" },
    { key: "ice_days_late", label: "Ice days 1989–2026" },
    { key: "cold_early", label: "Cold winters 1951–88 (%)" },
    { key: "cold_late", label: "Cold winters 1989–2026 (%)" },
    { key: "potential_early", label: "Tour-cold 1951–88 (%)" },
    { key: "potential_late", label: "Tour-cold 1989–2026 (%)" },
  ])];
}
