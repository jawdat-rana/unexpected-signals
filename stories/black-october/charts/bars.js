// Shared monthly column chart. Each chart module below calls it with a column
// name; months from HIGHLIGHT on are drawn in the signal colour.

export function monthlyBars({ data, width, d3, theme, tooltip, table }, opts) {
  const { key, label, from, highlight, extra } = opts;
  const rows = data.filter((d) => d.month >= new Date(from));
  const narrow = width < 560;
  const height = narrow ? 260 : 320;
  const m = { top: 20, right: 8, bottom: 28, left: 48 };
  const x = d3.scaleBand(rows.map((d) => d.month), [m.left, width - m.right]).padding(0.2);
  const y = d3.scaleLinear([0, d3.max(rows, (d) => d[key])], [height - m.bottom, m.top]).nice();
  const fmt = d3.utcFormat("%B %Y");
  const hi = new Date(highlight);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat(d3.format(",")));
  const jan = rows.filter((d) => d.month.getUTCMonth() === 0 || d.month.getUTCMonth() === 6).map((d) => d.month);
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(jan).tickSize(0).tickPadding(8).tickFormat(d3.utcFormat("%b %Y")));

  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", (d) => x(d.month)).attr("width", x.bandwidth())
    .attr("y", (d) => y(d[key])).attr("height", (d) => y(0) - y(d[key])).attr("rx", 1.5)
    .attr("fill", (d) => (d.month >= hi ? theme.signal : theme.context))
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${fmt(d.month)}</strong>`
      + `${label}: ${d3.format(",")(d[key])}` + (extra ? `<br>${extra.label}: ${d3.format(",")(d[extra.key])}` : "")))
    .on("pointerleave", () => tooltip.hide());

  const last = rows[rows.length - 1];
  svg.append("text").attr("class", "label-strong").attr("text-anchor", "end")
    .attr("x", x(last.month) + x.bandwidth()).attr("y", y(last[key]) - 6).text(d3.format(",")(last[key]));

  const cols = [{ key: "month", label: "Month", format: fmt }, { key, label, format: d3.format(",") }];
  if (extra) cols.push({ key: extra.key, label: extra.label, format: d3.format(",") });
  return [svg.node(), table(rows, cols)];
}
