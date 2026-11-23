// Hour by hour around midnight: the median PM2.5 over all Dutch stations, one
// line per New Year since 2013/14. Years with fireworks on sale in grey, the
// two covid bans dashed, the newest year in red.

const BANS = new Set(["2020/21", "2021/22"]);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 360;
  const m = { top: 24, right: narrow ? 56 : 90, bottom: 30, left: 36 };
  const rows = data.filter((d) => d.formula === "PM25" && d.hour_local >= -6 && d.hour_local <= 8);
  const seasons = d3.groups(rows, (d) => d.season);
  const newest = seasons.at(-1)[0];
  const x = d3.scaleLinear([-6, 8], [m.left, width - m.right]);
  const y = d3.scaleLinear([0, Math.max(400, d3.max(rows, (d) => d.median))], [height - m.bottom, m.top]).nice();

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Line chart of the median fine dust (PM2.5) at Dutch stations from 18:00 on New Year's Eve to 08:00 on New Year's Day, one line per year. Every year with fireworks on sale jumps in the first hour after midnight. The two covid-ban years jump much less at midnight.");

  svg.append("g").selectAll("line").data(y.ticks(4)).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y).attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(0)).call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  const hour = (h) => `${String((h + 24) % 24).padStart(2, "0")}:00`;
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(narrow ? [-6, -2, 0, 2, 6] : [-6, -4, -2, 0, 2, 4, 6, 8]).tickFormat(hour).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  const line = d3.line().x((d) => x(d.hour_local)).y((d) => y(d.median)).curve(d3.curveMonotoneX);
  const style = (s) => s === newest ? { stroke: theme.signal, width: 2.5, dash: null }
    : BANS.has(s) ? { stroke: theme.ink2, width: 1.6, dash: "4 3" }
    : { stroke: theme.context, width: 1.2, dash: null };
  const order = [...seasons].sort((a, b) => (a[0] === newest) - (b[0] === newest) || BANS.has(a[0]) - BANS.has(b[0]));
  svg.append("g").attr("fill", "none").selectAll("path").data(order).join("path")
    .attr("d", ([, v]) => line(v))
    .attr("stroke", ([s]) => style(s).stroke).attr("stroke-width", ([s]) => style(s).width)
    .attr("stroke-dasharray", ([s]) => style(s).dash)
    .on("pointerenter pointermove", (event, [s, v]) => tooltip.show(event,
      `<strong>${s}${BANS.has(s) ? " (covid ban)" : ""}</strong>Midnight hour: ${v.find((d) => d.hour_local === 0)?.median ?? "–"} µg/m³`))
    .on("pointerleave", () => tooltip.hide());

  const note = svg.append("g").attr("class", "annotation").style("pointer-events", "none");
  const label = (s, text, color) => {
    const v = seasons.find(([k]) => k === s)?.[1];
    const d = v && v.find((r) => r.hour_local === 2);
    if (!d) return;
    note.append("text").attr("x", x(2) + 6).attr("y", y(d.median)).attr("dy", "0.32em")
      .attr("fill", color).attr("paint-order", "stroke").attr("stroke", theme.paper).attr("stroke-width", 3).text(text);
  };
  label(newest, newest, theme.signal);
  label("2020/21", narrow ? "2020/21 ban" : "2020/21, covid ban", theme.ink2);
  if (!narrow) label("2021/22", "2021/22, covid ban", theme.ink2);
  note.append("text").attr("x", x(0)).attr("y", m.top - 8).attr("text-anchor", "middle").attr("fill", theme.ink2)
    .text("Midnight");

  const wide = d3.rollups(rows, (v) => Object.fromEntries(v.map((d) => [d.season, d.median])), (d) => d.hour_local);
  const cols = seasons.map(([s]) => ({ key: s, label: s }));
  return [svg.node(), table(wide.map(([h, o]) => ({ hour: hour(h), ...o })), [{ key: "hour", label: "Hour (local)" }, ...cols])];
}
