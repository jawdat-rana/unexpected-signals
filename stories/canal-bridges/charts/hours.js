// Planned openings per bridge in each hour of the day, by route. The weekday
// rush hours are shaded, so you can see which routes still open in them.

const ROUTE = {
  north: "Den Helder – Zaanstad",
  amsterdam: "Amsterdam – Leimuiden",
  haarlem: "Haarlem – Sassenheim",
};

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 340;
  const m = { top: 16, right: narrow ? 12 : 150, bottom: 30, left: 36 };
  const x = d3.scaleLinear([0, 24], [m.left, width - m.right]);
  const y = d3.scaleLinear([0, d3.max(data, (d) => d.openings)], [height - m.bottom, m.top]).nice();
  const routes = ["haarlem", "amsterdam", "north"]; // signal drawn last, on top
  const series = routes.map((route) => {
    const rows = data.filter((d) => d.route === route).sort((a, b) => a.hour - b.hour);
    // A step line: each hour holds its value from :00 to :59.
    return { route, rows, points: rows.flatMap((d) => [[d.hour, d.openings], [d.hour + 1, d.openings]]) };
  });

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Line chart of planned bridge openings by hour. The Den Helder to Zaanstad route opens through the night and in the rush hours; the Haarlem route is almost silent from 23:00 to 05:00.");

  for (const [a, b] of [[7, 9], [16, 18]]) {
    svg.append("rect").attr("x", x(a)).attr("width", x(b) - x(a)).attr("y", m.top)
      .attr("height", height - m.bottom - m.top).attr("fill", theme.grid).attr("opacity", 0.6);
  }
  svg.append("text").attr("class", "annotation").attr("x", x(8)).attr("y", m.top + 10)
    .attr("text-anchor", "middle").text("rush");
  svg.append("text").attr("class", "annotation").attr("x", x(17)).attr("y", m.top + 10)
    .attr("text-anchor", "middle").text("rush");

  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(narrow ? [0, 6, 12, 18, 24] : d3.range(0, 25, 3))
      .tickSize(0).tickPadding(8).tickFormat((h) => `${String(h % 24).padStart(2, "0")}:00`));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(6).tickFormat(d3.format(".1f")));

  const line = d3.line().x((p) => x(p[0])).y((p) => y(p[1]));
  svg.append("g").attr("fill", "none").attr("stroke-linejoin", "round").selectAll("path").data(series).join("path")
    .attr("d", (s) => line(s.points))
    .attr("stroke", (s) => (s.route === "north" ? theme.signal : theme.context))
    .attr("stroke-width", (s) => (s.route === "north" ? 2.5 : 2))
    .attr("stroke-dasharray", (s) => (s.route === "haarlem" ? "4 3" : null));

  // Direct labels at the right end on wide screens; a key above on narrow ones.
  const nodes = [];
  if (narrow) {
    const key = document.createElement("div");
    key.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 14px;margin:0 0 6px;font-size:13px;color:var(--ink-2)";
    const sw = (s) => `<svg width="20" height="8" aria-hidden="true"><line x1="1" y1="4" x2="19" y2="4" stroke="${s.route === "north" ? theme.signal : theme.context}" stroke-width="2.5" ${s.route === "haarlem" ? 'stroke-dasharray="4 3"' : ""}/></svg>`;
    key.innerHTML = [...series].reverse().map((s) => `<span style="display:inline-flex;gap:6px;align-items:center">${sw(s)}${ROUTE[s.route]}</span>`).join("");
    nodes.push(key);
  } else {
    const ends = series.map((s) => ({ ...s, ly: y(d3.mean(s.rows.filter((d) => d.hour >= 20), (d) => d.openings)) }));
    // Nudge labels apart.
    ends.sort((a, b) => a.ly - b.ly);
    for (let i = 1; i < ends.length; i++) ends[i].ly = Math.max(ends[i].ly, ends[i - 1].ly + 16);
    svg.append("g").selectAll("text").data(ends).join("text")
      .attr("class", (s) => (s.route === "north" ? "label-strong" : "annotation"))
      .attr("x", x(24) + 8).attr("y", (s) => s.ly).attr("dy", "0.35em").text((s) => ROUTE[s.route]);
  }

  // Hover: one hour, all three routes.
  const rule = svg.append("line").attr("y1", m.top).attr("y2", height - m.bottom)
    .attr("stroke", theme.ink).attr("stroke-width", 1).style("display", "none");
  svg.append("rect").attr("x", m.left).attr("width", x(24) - m.left).attr("y", m.top)
    .attr("height", height - m.bottom - m.top).attr("fill", "transparent")
    .on("pointermove", (event) => {
      const hour = Math.max(0, Math.min(23, Math.floor(x.invert(d3.pointer(event)[0]))));
      rule.style("display", null).attr("x1", x(hour + 0.5)).attr("x2", x(hour + 0.5));
      const lines = [...series].reverse().map((s) => {
        const v = s.rows.find((d) => d.hour === hour)?.openings ?? 0;
        return `${ROUTE[s.route]}: ${v.toFixed(2)}`;
      });
      tooltip.show(event, `<strong>${String(hour).padStart(2, "0")}:00–${String(hour).padStart(2, "0")}:59</strong>${lines.join("<br>")}`);
    })
    .on("pointerleave", () => {
      rule.style("display", "none");
      tooltip.hide();
    });

  nodes.push(svg.node());
  const wide = d3.range(24).map((hour) => Object.fromEntries([["hour", `${String(hour).padStart(2, "0")}:00`],
    ...routes.map((r) => [r, data.find((d) => d.route === r && d.hour === hour)?.openings ?? 0])]));
  nodes.push(table(wide, [
    { key: "hour", label: "Hour" },
    { key: "north", label: ROUTE.north },
    { key: "amsterdam", label: ROUTE.amsterdam },
    { key: "haarlem", label: ROUTE.haarlem },
  ]));
  return nodes;
}
