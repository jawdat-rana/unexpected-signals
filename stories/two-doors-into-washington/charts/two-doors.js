// Scatter: each country's FARA clients (x) against its companies' PAC giving (y),
// coloured by which door it mostly uses.

const DOORS = [
  { key: "Mostly companies", token: "cat2" },
  { key: "Mostly hired agents", token: "cat1" },
  { key: "Both doors", token: "cat3" },
  { key: "Neither stands out", token: "context" },
];
const SHORT = { "United Kingdom": "UK", "United Arab Emirates": "UAE", "Saudi Arabia": "Saudi Arabia" };
// Labels that fit at every width, then extra ones for wide screens. [dx, dy, anchor]
const LABELS = {
  Switzerland: [8, 4, "start"],
  Japan: [0, -10, "middle"],
  "Saudi Arabia": [2, -10, "start"],
};
const WIDE_LABELS = {
  Germany: [8, 4, "start"],
  "United Kingdom": [8, 4, "start"],
  Canada: [8, 4, "start"],
  France: [0, -11, "middle"],
  Ukraine: [-2, -10, "end"],
  "United Arab Emirates": [0, -10, "middle"],
  Qatar: [0, -10, "middle"],
  Israel: [0, -10, "middle"],
};

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = Math.max(300, Math.min(460, width * 0.62));
  const m = { top: 20, right: 16, bottom: 40, left: 48 };
  const color = new Map(DOORS.map((d) => [d.key, theme[d.token]]));
  const money = (v) => (v === 0 ? "$0" : v >= 1e6 ? `$${d3.format(".1f")(v / 1e6)}M` : `$${d3.format(".0f")(v / 1e3)}K`);

  const x = d3.scaleLinear([0, d3.max(data, (d) => d.fara_clients) * 1.05], [m.left, width - m.right]).nice();
  const y = d3.scaleLinear([0, d3.max(data, (d) => d.pac_dollars) * 1.08], [height - m.bottom, m.top]).nice();

  const legend = document.createElement("div");
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:13px;color:var(--ink-2)";
  legend.innerHTML = DOORS.map((d) => `<span style="display:inline-flex;align-items:center;gap:6px">`
    + `<svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="5" fill="${color.get(d.key)}"/></svg>`
    + `${d.key}</span>`).join("");

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);

  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "grid").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 4 : 7).tickSize(-(height - m.top - m.bottom)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat(money));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 4 : 7).tickSize(0).tickPadding(8));
  svg.append("text").attr("x", width - m.right).attr("y", height - 4).attr("text-anchor", "end")
    .text("Foreign clients with registered U.S. agents (FARA), 2023–24 →");
  svg.append("text").attr("x", m.left - 44).attr("y", m.top - 8).text("↑ PAC giving, 2024");

  // Draw the grey dots first so coloured ones sit on top.
  const order = [...data].sort((a, b) => (a.door === "Neither stands out" ? -1 : 0) - (b.door === "Neither stands out" ? -1 : 0));
  svg.append("g").selectAll("circle").data(order).join("circle")
    .attr("cx", (d) => x(d.fara_clients)).attr("cy", (d) => y(d.pac_dollars))
    .attr("r", (d) => (d.country === "Netherlands" ? 7 : 5.5))
    .attr("fill", (d) => color.get(d.door))
    .attr("stroke", (d) => (d.country === "Netherlands" ? theme.ink : theme.paper))
    .attr("stroke-width", 2);

  const labels = narrow ? LABELS : { ...LABELS, ...WIDE_LABELS };
  svg.append("g").selectAll("text").data(data.filter((d) => labels[d.country])).join("text")
    .attr("x", (d) => x(d.fara_clients) + labels[d.country][0])
    .attr("y", (d) => y(d.pac_dollars) + labels[d.country][1])
    .attr("text-anchor", (d) => labels[d.country][2])
    .attr("class", (d) => (d.country === "Netherlands" ? "label-strong" : "annotation"))
    .text((d) => SHORT[d.country] || d.country);

  // The Netherlands sits in a crowded corner, so its label goes in the open
  // space with a leader line.
  const nl = data.find((d) => d.country === "Netherlands");
  if (nl) {
    const nx = x(nl.fara_clients);
    const ny = y(nl.pac_dollars);
    const lx = nx + (narrow ? 34 : 56);
    const ly = ny - (narrow ? 30 : 40);
    svg.append("path").attr("class", "annotation-line").attr("d", `M${nx + 6},${ny - 5}L${lx - 4},${ly + 4}`);
    svg.append("text").attr("class", "label-strong").attr("x", lx).attr("y", ly).text("Netherlands");
    svg.append("text").attr("class", "annotation").attr("x", lx).attr("y", ly + 15)
      .text(`${money(nl.pac_dollars)}, ${nl.fara_clients} FARA clients`);
  }

  // Hover: nearest country to the pointer, so small dots are easy to hit.
  const delaunay = d3.Delaunay.from(data, (d) => x(d.fara_clients), (d) => y(d.pac_dollars));
  const ring = svg.append("circle").attr("r", 9).attr("fill", "none").attr("stroke", theme.ink)
    .attr("stroke-width", 1.5).style("display", "none");
  svg.append("rect").attr("width", width).attr("height", height).attr("fill", "transparent")
    .on("pointermove", (event) => {
      const [px, py] = d3.pointer(event);
      const d = data[delaunay.find(px, py)];
      if (Math.hypot(x(d.fara_clients) - px, y(d.pac_dollars) - py) > 40) {
        ring.style("display", "none");
        tooltip.hide();
        return;
      }
      ring.style("display", null).attr("cx", x(d.fara_clients)).attr("cy", y(d.pac_dollars));
      tooltip.show(event, `<strong>${tooltip.esc(d.country)}</strong>`
        + `${money(d.pac_dollars)} from company PACs<br>${d.fara_clients} FARA clients`
        + (d.top_parents ? `<br><span class="muted">${tooltip.esc(d.top_parents)}</span>` : ""));
    })
    .on("pointerleave", () => { ring.style("display", "none"); tooltip.hide(); });

  return [legend, svg.node(), table(data, [
    { key: "country", label: "Country" },
    { key: "pac_dollars", label: "PAC giving", format: (v) => `$${d3.format(",")(v)}` },
    { key: "fara_clients", label: "FARA clients" },
    { key: "door", label: "Door" },
  ])];
}
