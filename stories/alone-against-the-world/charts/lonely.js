// Every recorded vote on three resolutions, one row each, one dot per vote.
// Red: the country was the only no. Grey ring: it voted no with others.
// Hollow: it abstained or was absent.

const ROWS = [
  { case: "Law of the Sea", label: "Türkiye on the Law of the Sea" },
  { case: "Regional arms control", label: "India on regional arms control" },
  { case: "Mayotte", label: "France on Mayotte" },
];

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const rowH = narrow ? 64 : 58;
  const m = { top: 8, right: 10, bottom: 26, left: 10 };
  const height = m.top + m.bottom + ROWS.length * rowH;
  const x = d3.scaleLinear([1974, 2026], [m.left + 6, width - m.right - 6]);
  const y = d3.scaleBand(ROWS.map((r) => r.case), [m.top, height - m.bottom]);
  const r = narrow ? 3.2 : 4.2;

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Three rows of dots, one dot per yearly vote. Türkiye voted no on every Law of the Sea resolution from 1984 to 2025, alone 32 times. India was the only no on the regional conventional arms control resolution every year from 1996 to 2025. France was the only no on Mayotte from 1976 to 1992, after which the vote stopped.");
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(narrow ? [1980, 2000, 2020] : [1975, 1985, 1995, 2005, 2015, 2025]).tickFormat(d3.format("d")).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  for (const row of ROWS) {
    const top = y(row.case);
    svg.append("text").attr("x", m.left).attr("y", top + 14).attr("class", "label-strong").text(row.label);
    svg.append("line").attr("x1", x(1974)).attr("x2", x(2026)).attr("y1", top + rowH * 0.62).attr("y2", top + rowH * 0.62)
      .attr("stroke", theme.grid);
  }
  svg.append("g").selectAll("circle").data(data).join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.case) + rowH * 0.62).attr("r", r)
    .attr("fill", (d) => (d.alone ? theme.signal : d.vote === "no" ? theme.context : theme.paper))
    .attr("stroke", (d) => (d.alone ? theme.paper : d.vote === "no" ? theme.context : theme.muted))
    .attr("stroke-width", (d) => (d.alone ? 1 : 1.2))
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>${d.year}: ${tooltip.esc(d.resolution)}</strong>`
      + `${tooltip.esc(d.country)} voted ${d.vote}${d.alone ? ", the only no" : ""}<br>`
      + `${d.yes} yes, ${d.no} no, ${d.abstain} abstain`))
    .on("pointerleave", () => tooltip.hide());

  return [svg.node(), table(data, [
    { key: "case", label: "Resolution" },
    { key: "year", label: "Year" },
    { key: "country", label: "Country" },
    { key: "vote", label: "Its vote" },
    { key: "yes", label: "Yes" },
    { key: "no", label: "No" },
    { key: "abstain", label: "Abstain" },
  ])];
}
