// Every New Year's night after taking the wind out: actual extra PM2.5 divided
// by what the wind would lead you to expect. 1 is an ordinary year.

const BANS = new Set(["2020/21", "2021/22"]);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 260 : 300;
  const m = { top: 24, right: 8, bottom: 26, left: 32 };
  const rows = data.filter((d) => d.country === "NL" && d.formula === "PM25" && d.vs_expected != null);
  const newest = rows.at(-1).season;
  const x = d3.scaleBand(rows.map((d) => d.season), [m.left, width - m.right]).paddingInner(0.2);
  const y = d3.scaleLinear([0, Math.max(2, d3.max(rows, (d) => d.vs_expected))], [height - m.bottom, m.top]).nice();

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Bar chart of each New Year's fine dust compared with what the wind predicts. Most years sit near 1. The covid-ban years are lower; the last New Year before the ban is the highest.");
  svg.append("g").selectAll("line").data(y.ticks(4)).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y).attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickFormat((v) => `${v}×`).tickSize(0)).call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickFormat((s) => narrow ? `'${s.slice(2, 4)}` : s.replace("20", "'").replace("/", "/")).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", (d) => x(d.season)).attr("width", x.bandwidth())
    .attr("y", (d) => y(d.vs_expected)).attr("height", (d) => y(0) - y(d.vs_expected))
    .attr("fill", (d) => d.season === newest ? theme.signal : BANS.has(d.season) ? theme.paper : theme.context)
    .attr("stroke", (d) => BANS.has(d.season) ? theme.ink : "none").attr("stroke-width", 1.5)
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>${d.season}</strong>`
      + `${d.vs_expected}× the dust expected for ${d.wind_ms} m/s wind`
      + (BANS.has(d.season) ? "<br>Covid ban: no legal sales" : d.sales_eur_m ? `<br>Sales: €${d.sales_eur_m} million` : "")))
    .on("pointerleave", () => tooltip.hide());

  svg.append("line").attr("x1", m.left).attr("x2", width - m.right).attr("y1", y(1)).attr("y2", y(1))
    .attr("stroke", theme.ink2).attr("stroke-dasharray", "3 3");
  svg.append("text").attr("class", "annotation").attr("x", m.left + 4).attr("y", y(1) - 5).attr("fill", theme.ink2)
    .attr("paint-order", "stroke").attr("stroke", theme.paper).attr("stroke-width", 3).text("As expected for the wind");

  return [svg.node(), table(rows, [
    { key: "season", label: "New Year" },
    { key: "status", label: "Fireworks" },
    { key: "sales_eur_m", label: "Sales (€ million)" },
    { key: "wind_ms", label: "Wind (m/s)" },
    { key: "vs_expected", label: "Actual ÷ expected" },
  ])];
}
