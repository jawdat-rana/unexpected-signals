// Share of flaws added to CISA KEV within 30 days of their CVE being
// published, per year. 2026 is the signal.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 240 : 280;
  const m = { top: 24, right: 8, bottom: 28, left: 40 };
  const x = d3.scaleBand(data.map((d) => d.year), [m.left, width - m.right]).padding(0.3);
  const y = d3.scaleLinear([0, 100], [height - m.bottom, m.top]);
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(8).tickFormat((v) => `${v}%`));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8).tickFormat((v) => (v === 2026 ? "2026*" : v)));
  svg.append("g").selectAll("rect").data(data).join("rect")
    .attr("x", (d) => x(d.year)).attr("width", x.bandwidth()).attr("rx", 2)
    .attr("y", (d) => y(d.share_within_30_days)).attr("height", (d) => y(0) - y(d.share_within_30_days))
    .attr("fill", (d) => (d.year === 2026 ? theme.signal : theme.context))
    .on("pointermove", (event, d) => tooltip.show(event, `<strong>${d.year}</strong>`
      + `${d.within_30_days} of ${d.added} within 30 days<br>Median: ${d.median_days} days`))
    .on("pointerleave", () => tooltip.hide());
  svg.append("g").attr("class", "label-strong").selectAll("text").data(data).join("text")
    .attr("x", (d) => x(d.year) + x.bandwidth() / 2).attr("y", (d) => y(d.share_within_30_days) - 6)
    .attr("text-anchor", "middle").text((d) => `${d.share_within_30_days}%`);
  return [svg.node(), table(data, [
    { key: "year", label: "Year added" },
    { key: "added", label: "Flaws added" },
    { key: "within_30_days", label: "Within 30 days" },
    { key: "within_7_days", label: "Within 7 days" },
    { key: "median_days", label: "Median days" },
  ])];
}
