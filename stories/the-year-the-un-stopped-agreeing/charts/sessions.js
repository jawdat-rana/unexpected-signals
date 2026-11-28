// Share of General Assembly resolutions that went to a recorded vote, per
// session since 1990. Grey bars, the 2025–26 session in red.

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 280 : 340;
  const m = { top: 30, right: 8, bottom: 26, left: 34 };
  const x = d3.scaleBand(data.map((d) => d.start_year), [m.left, width - m.right]).paddingInner(0.18);
  const y = d3.scaleLinear([0, 70], [height - m.bottom, m.top]);
  const last = data[data.length - 1];

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", `Bar chart of the share of General Assembly resolutions adopted by recorded vote, per session from 1990 to 2025. The bars stay between 18 and 34 percent until the 2025–26 session, which reaches ${Math.round(last.recorded_share)} percent.`);

  svg.append("g").selectAll("line").data([20, 40, 60]).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y).attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).tickValues([0, 20, 40, 60]).tickFormat((d) => `${d}%`).tickSize(0))
    .call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(data.map((d) => d.start_year).filter((v) => v % (narrow ? 10 : 5) === 0)).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  svg.append("g").selectAll("rect").data(data).join("rect")
    .attr("x", (d) => x(d.start_year)).attr("width", x.bandwidth())
    .attr("y", (d) => y(d.recorded_share)).attr("height", (d) => y(0) - y(d.recorded_share))
    .attr("fill", (d) => (d === last ? theme.signal : theme.context))
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>Session ${d.session} (${d.label})</strong>`
      + `${d.recorded} of ${d.resolutions} resolutions by recorded vote (${d.recorded_share}%)<br>`
      + `The US voted no ${d.us_no} times`))
    .on("pointerleave", () => tooltip.hide());

  const note = svg.append("g").attr("class", "annotation").style("pointer-events", "none");
  note.append("text").attr("class", "label-strong").attr("x", x(last.start_year) - 6).attr("y", y(last.recorded_share) + 12)
    .attr("text-anchor", "end").attr("fill", theme.signal)
    .text(narrow ? `2025–26: ${Math.round(last.recorded_share)}%` : `2025–26: ${last.recorded} of ${last.resolutions} (${Math.round(last.recorded_share)}%)`);
  note.append("text").attr("x", x(1990)).attr("y", y(34) - 6).attr("fill", theme.ink2)
    .text(narrow ? "35 years: about 1 in 4" : "For 35 years: about 1 in 4 went to a vote");

  return [svg.node(), table([...data].reverse(), [
    { key: "label", label: "Session" },
    { key: "resolutions", label: "Resolutions" },
    { key: "recorded", label: "Recorded vote" },
    { key: "without_vote", label: "Without a vote" },
    { key: "recorded_share", label: "Recorded (%)" },
    { key: "us_no", label: "US voted no" },
  ])];
}
