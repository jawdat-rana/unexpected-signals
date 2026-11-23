// The 57 movable bridges in NDW's planned-openings feed, all in North Holland.
// The route from Den Helder through Alkmaar to Zaanstad is the signal colour;
// the two routes around Haarlem and Amsterdam are context grey.

import outline from "./netherlands.js";

const ROUTE = {
  north: "Den Helder – Alkmaar – Zaanstad",
  amsterdam: "Amsterdam – Schiphol – Leimuiden",
  haarlem: "Spaarndam – Haarlem – Sassenheim",
};

// Orientation labels: [name, lat, lon, dx, dy, anchor, shown when narrow]
const TOWNS = [
  ["Den Helder", 52.957, 4.760, -8, 4, "end", true],
  ["Alkmaar", 52.632, 4.748, -10, 4, "end", true],
  ["Zaandam", 52.439, 4.826, 10, 4, "start", true],
  ["Amsterdam", 52.372, 4.895, 10, 4, "start", true],
  ["Haarlem", 52.381, 4.637, -10, 4, "end", true],
  ["Schagen", 52.787, 4.799, 10, 4, "start", false],
  ["Schiphol", 52.310, 4.768, -10, 4, "end", false],
];

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = Math.round(Math.min(720, Math.max(440, width * 1.15)));
  const land = outline.features[0];

  // Frame the bridges, not the country.
  const frame = {
    type: "MultiPoint",
    coordinates: [[4.45, 52.18], [5.0, 53.0]],
  };
  const projection = d3.geoMercator().fitExtent([[10, 10], [width - 10, height - 10]], frame);
  const path = d3.geoPath(projection);
  const xy = (d) => projection([d.longitude, d.latitude]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Map of North Holland with 57 movable bridges. 25 lie on one route from Den Helder through Alkmaar to Zaanstad; the others are around Haarlem and Amsterdam.");
  const clip = `clip-${Math.random().toString(36).slice(2)}`;
  svg.append("clipPath").attr("id", clip).append("rect").attr("width", width).attr("height", height);
  const base = svg.append("g").attr("clip-path", `url(#${clip})`);
  base.append("path").attr("d", path(land)).attr("fill", theme.paper2).attr("stroke", theme.rule).attr("stroke-width", 0.75);
  base.append("path").attr("d", path(outline.features[1])).attr("fill", theme.paper).attr("stroke", theme.rule).attr("stroke-width", 0.5);

  // The route as a thin line through its bridges, north to south.
  const north = data.filter((d) => d.route === "north").sort((a, b) => b.latitude - a.latitude);
  svg.append("path").attr("d", d3.line()(north.map(xy))).attr("fill", "none")
    .attr("stroke", theme.signal).attr("stroke-width", 1.5).attr("stroke-dasharray", "1 3")
    .attr("stroke-linecap", "round").attr("opacity", 0.8);

  const r = d3.scaleSqrt([0, d3.max(data, (d) => d.openings_per_day)], [0, narrow ? 6 : 8]);
  const ordered = [...data].sort((a, b) => (a.route === "north") - (b.route === "north"));
  svg.append("g").selectAll("circle").data(ordered).join("circle")
    .attr("cx", (d) => xy(d)[0]).attr("cy", (d) => xy(d)[1]).attr("r", (d) => r(d.openings_per_day))
    .attr("fill", (d) => (d.route === "north" ? theme.signal : theme.context))
    .attr("stroke", theme.paper2).attr("stroke-width", 1.5)
    .style("cursor", "pointer")
    .on("pointerenter pointermove", (event, d) => tooltip.show(event,
      `<strong>Bridge near ${tooltip.esc(d.near)}</strong>`
      + `<span class="muted">${ROUTE[d.route]}</span><br>`
      + `${d.openings_per_day} planned openings a day<br>`
      + `${d.minutes_open_per_day} minutes open a day<br>`
      + `${d.rush_hour_openings} in the weekday rush hours`))
    .on("pointerleave", () => tooltip.hide());

  const towns = TOWNS.filter((t) => !narrow || t[6]);
  const labels = svg.append("g").attr("class", "annotation").style("pointer-events", "none");
  labels.selectAll("text").data(towns).join("text")
    .attr("x", (t) => projection([t[2], t[1]])[0] + t[3]).attr("y", (t) => projection([t[2], t[1]])[1] + t[4])
    .attr("text-anchor", (t) => t[5]).attr("paint-order", "stroke").attr("stroke", theme.paper2)
    .attr("stroke-width", 3).attr("stroke-linejoin", "round").attr("fill", theme.ink2).text((t) => t[0]);

  // Callout for the route, east of it. Narrow screens have the legend instead.
  const mid = xy(north[Math.round(north.length * 0.3)]);
  if (!narrow) {
  const lx = Math.min(width - 10, mid[0] + (narrow ? 40 : 70));
  svg.append("text").attr("class", "label-strong").attr("x", lx).attr("y", mid[1] - 18)
    .attr("text-anchor", lx > width - 150 ? "end" : "start").text("25 bridges, one route");
  svg.append("text").attr("class", "annotation").attr("x", lx).attr("y", mid[1] - 2)
    .attr("text-anchor", lx > width - 150 ? "end" : "start").text("each planned open about 3 hours a day");
  }

  // Legend: what colour and size mean.
  const key = document.createElement("div");
  key.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 6px;font-size:13px;color:var(--ink-2)";
  const dot = (c) => `<svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="5" fill="${c}"/></svg>`;
  key.innerHTML = `<span style="display:inline-flex;gap:6px;align-items:center">${dot(theme.signal)}${ROUTE.north}</span>`
    + `<span style="display:inline-flex;gap:6px;align-items:center">${dot(theme.context)}Haarlem and Amsterdam routes</span>`;

  return [key, svg.node(), table(data, [
    { key: "near", label: "Near" },
    { key: "route", label: "Route", format: (v) => ROUTE[v] },
    { key: "openings_per_day", label: "Openings a day" },
    { key: "minutes_open_per_day", label: "Minutes open a day" },
    { key: "rush_hour_openings", label: "Rush-hour openings (weekday)" },
    { key: "night_openings", label: "Night openings (23–06)" },
  ])];
}
