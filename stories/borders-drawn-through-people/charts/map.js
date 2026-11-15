// World map: every land border that cuts through at least one people's
// homeland, in the signal colour, thicker where it cuts more groups.
// The base map and border lines come from data/world.json (Natural Earth,
// public domain); the CSV gives each border's count and the groups it cuts.

const world = await fetch(new URL("../data/world.json", import.meta.url)).then((r) => r.json());
const countries = world.features.filter((f) => f.properties.id);
const borders = world.features.filter((f) => f.properties.border);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const byBorder = new Map(data.map((d) => [d.border, d]));
  const height = Math.round(width * 0.5);
  const projection = d3.geoEqualEarth().fitExtent([[4, 4], [width - 4, height - 4]], {
    type: "FeatureCollection",
    features: countries,
  });
  const path = d3.geoPath(projection);
  const stroke = d3.scaleSqrt([1, d3.max(data, (d) => d.groups_cut)], [1.2, width < 560 ? 3.5 : 5]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").selectAll("path").data(countries).join("path")
    .attr("d", path).attr("fill", theme.context).attr("fill-opacity", 0.35)
    .attr("stroke", theme.paper).attr("stroke-width", 0.5);

  const show = (event, f) => {
    const d = byBorder.get(f.properties.border);
    tooltip.show(event, `<strong>${tooltip.esc(d.countries)}</strong>`
      + `${d.groups_cut} ${d.groups_cut === 1 ? "group" : "groups"}: ${tooltip.esc(d.groups)}`);
  };
  svg.append("g").attr("fill", "none").attr("stroke-linecap", "round")
    .selectAll("path").data(borders.sort((a, b) =>
      byBorder.get(a.properties.border).groups_cut - byBorder.get(b.properties.border).groups_cut))
    .join("path")
    .attr("d", path).attr("stroke", theme.signal)
    .attr("stroke-width", (f) => stroke(byBorder.get(f.properties.border).groups_cut));
  // Wide invisible copies make thin lines easy to hover and tap.
  svg.append("g").attr("fill", "none").selectAll("path").data(borders).join("path")
    .attr("d", path).attr("stroke", "transparent").attr("stroke-width", 12)
    .style("cursor", "default")
    .on("pointermove", show).on("pointerleave", () => tooltip.hide());

  // Legend above the map, so it never sits on top of land on a phone.
  const legend = document.createElement("div");
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:13px;color:var(--ink-2)";
  legend.innerHTML = [1, 3, 6].map((n) => `<span style="display:inline-flex;align-items:center;gap:6px">`
    + `<svg width="22" height="10" aria-hidden="true"><line x1="2" x2="20" y1="5" y2="5" stroke="${theme.signal}"`
    + ` stroke-width="${stroke(n)}" stroke-linecap="round"/></svg>${n} ${n === 1 ? "group" : "groups"} cut</span>`).join("");

  const wrap = document.createElement("div");
  wrap.append(legend, svg.node());
  return [wrap, table(data, [
    { key: "countries", label: "Border" },
    { key: "groups_cut", label: "Groups cut" },
    { key: "groups", label: "Groups" },
  ])];
}
