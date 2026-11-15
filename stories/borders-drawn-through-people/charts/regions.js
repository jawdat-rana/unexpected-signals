// Horizontal bars: share of each region's peoples whose homeland today's
// borders split. South America, the surprise, is the signal.

const SIGNAL = "South America";
const SHORT = {
  "Middle East and North Africa": "Middle East, N. Africa",
  "Central America and Caribbean": "Central Am., Caribbean",
  "East and Southeast Asia": "East, SE Asia",
  "Former Soviet Union": "Former USSR",
};

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const rows = [...data].sort((a, b) => b.share - a.share);
  const bar = 26;
  const m = { top: 8, right: narrow ? 64 : 96, bottom: 8, left: narrow ? 150 : 210 };
  const height = m.top + m.bottom + rows.length * bar;

  const x = d3.scaleLinear([0, 60], [m.left, width - m.right]);
  const y = d3.scaleBand(rows.map((d) => d.region), [m.top, height - m.bottom]).padding(0.25);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(0,${m.top})`)
    .call(d3.axisTop(x).tickValues([0, 20, 40, 60]).tickSize(-(height - m.top - m.bottom))
      .tickFormat(""));

  const fill = (d) => (d.region === SIGNAL ? theme.signal : theme.context);
  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", x(0)).attr("y", (d) => y(d.region)).attr("height", y.bandwidth())
    .attr("width", (d) => Math.max(1, x(d.share) - x(0))).attr("rx", 2).attr("fill", fill);

  svg.append("g").selectAll("text").data(rows).join("text")
    .attr("x", m.left - 8).attr("y", (d) => y(d.region) + y.bandwidth() / 2)
    .attr("dy", "0.32em").attr("text-anchor", "end")
    .attr("class", (d) => (d.region === SIGNAL ? "label-strong" : null))
    .text((d) => (narrow ? SHORT[d.region] ?? d.region : d.region));

  svg.append("g").selectAll("text").data(rows).join("text")
    .attr("x", (d) => x(d.share) + 6).attr("y", (d) => y(d.region) + y.bandwidth() / 2)
    .attr("dy", "0.32em")
    .attr("class", (d) => (d.region === SIGNAL ? "label-strong" : null))
    .text((d) => (narrow ? `${Math.round(d.share)}%` : `${Math.round(d.share)}% (${d.split} of ${d.groups})`));

  svg.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", 0).attr("width", width).attr("y", (d) => y(d.region) - (y.step() - y.bandwidth()) / 2)
    .attr("height", y.step()).attr("fill", "transparent")
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.region)}</strong>`
      + `${d.split} of ${d.groups} peoples split by a border (${d.share}%)`))
    .on("pointerleave", () => tooltip.hide());

  return [svg.node(), table(rows, [
    { key: "region", label: "Region" },
    { key: "groups", label: "Peoples mapped" },
    { key: "split", label: "Split by a border" },
    { key: "share", label: "Share (%)" },
  ])];
}
