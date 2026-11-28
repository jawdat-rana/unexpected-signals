// Countries that most often cast the only no in a General Assembly vote, since
// 1946. The three stories in this piece in red; the rest grey.

const SIGNAL = new Set(["Türkiye", "India", "France"]);
const TOP = 12;

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const rows = [...data].sort((a, b) => b.lone_no - a.lone_no).slice(0, TOP);
  const bar = 26;
  const m = { top: 8, right: narrow ? 40 : 56, bottom: 24, left: narrow ? 96 : 118 };
  const height = m.top + m.bottom + rows.length * bar;
  const x = d3.scaleLog([1, 400], [m.left, width - m.right]);
  const y = d3.scaleBand(rows.map((d) => d.country), [m.top, height - m.bottom]).padding(0.25);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Bar chart, on a log scale, of how often each country was the only no vote in the General Assembly. The United States leads with 353, then Israel with 152, North Korea 37, India 35, Türkiye 34 and France 27.");
  svg.append("g").selectAll("line").data([1, 10, 100]).join("line")
    .attr("x1", x).attr("x2", x).attr("y1", m.top).attr("y2", height - m.bottom).attr("stroke", theme.grid);

  svg.append("g").attr("transform", `translate(0,${height - m.bottom + 4})`)
    .call(d3.axisBottom(x).tickValues([1, 10, 100]).tickFormat(d3.format("d")).tickSize(0))
    .call((g) => g.select(".domain").remove()).attr("color", theme.muted);

  const fill = (d) => (SIGNAL.has(d.country) ? theme.signal : theme.context);
  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", x(1)).attr("y", (d) => y(d.country)).attr("height", y.bandwidth())
    .attr("width", (d) => Math.max(1, x(d.lone_no) - x(1))).attr("rx", 2).attr("fill", fill);
  svg.append("g").selectAll("text").data(rows).join("text")
    .attr("x", m.left - 8).attr("y", (d) => y(d.country) + y.bandwidth() / 2).attr("dy", "0.32em")
    .attr("text-anchor", "end").attr("class", (d) => (SIGNAL.has(d.country) ? "label-strong" : null))
    .text((d) => d.country);
  svg.append("g").selectAll("text").data(rows).join("text")
    .attr("x", (d) => x(d.lone_no) + 6).attr("y", (d) => y(d.country) + y.bandwidth() / 2).attr("dy", "0.32em")
    .attr("class", (d) => (SIGNAL.has(d.country) ? "label-strong" : null)).text((d) => d.lone_no);

  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", 0).attr("width", width).attr("y", (d) => y(d.country) - (y.step() - y.bandwidth()) / 2)
    .attr("height", y.step()).attr("fill", "transparent")
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.country)}</strong>`
      + `The only no ${d.lone_no} times (${d.first}–${d.last})<br>Most often: ${tooltip.esc(d.top_title)} `
      + `(${d.top_count} times, ${d.top_first}–${d.top_last})`))
    .on("pointerleave", () => tooltip.hide());

  return [svg.node(), table(rows, [
    { key: "country", label: "Country" },
    { key: "lone_no", label: "Only no" },
    { key: "top_title", label: "Resolution it most often stood alone against" },
    { key: "top_count", label: "Times" },
  ])];
}
