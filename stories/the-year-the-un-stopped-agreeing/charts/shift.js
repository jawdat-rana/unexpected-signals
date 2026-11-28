// Every member's agreement with the US in the 2024–25 session (x) against the
// 2025–26 session (y). Below the diagonal: agreed less. Named dots in colour.

const NAMED = {
  Israel: "signal", Argentina: "signal", Micronesia: "blue", "Marshall Islands": "blue",
  Palau: "blue", Hungary: "ink", "United Kingdom": "ink", Netherlands: "ink",
};

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const size = Math.min(width, 620);
  const height = size * (narrow ? 0.95 : 0.8);
  const m = { top: 16, right: 16, bottom: 40, left: 44 };
  const x = d3.scaleLinear([0, 100], [m.left, size - m.right]);
  const y = d3.scaleLinear([0, 100], [height - m.bottom, m.top]);
  const colour = (d) => ({ signal: theme.signal, blue: theme.categorical[1], ink: theme.ink }[NAMED[d.country]] ?? theme.context);

  const svg = d3.create("svg").attr("viewBox", [0, 0, size, height]).attr("width", size)
    .attr("role", "img")
    .attr("aria-label", "Scatter plot of each UN member's agreement with the United States in 2024–25 against 2025–26. Almost every dot falls far below the diagonal, most to under 10 percent. Israel and Argentina stay high. Micronesia, the Marshall Islands and Palau fall from 40 to 62 percent to between 10 and 23 percent.");

  svg.append("g").selectAll("line").data([25, 50, 75]).join("line")
    .attr("x1", m.left).attr("x2", size - m.right).attr("y1", y).attr("y2", y).attr("stroke", theme.grid);
  svg.append("g").selectAll("line").data([25, 50, 75]).join("line")
    .attr("y1", m.top).attr("y2", height - m.bottom).attr("x1", x).attr("x2", x).attr("stroke", theme.grid);
  svg.append("line").attr("x1", x(0)).attr("y1", y(0)).attr("x2", x(100)).attr("y2", y(100))
    .attr("stroke", theme.ink2).attr("stroke-dasharray", "3 3");
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues([0, 25, 50, 75, 100]).tickFormat((d) => `${d}%`).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).tickValues([0, 25, 50, 75, 100]).tickFormat((d) => `${d}%`).tickSize(0))
    .call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("text").attr("x", size - m.right).attr("y", height - 6).attr("text-anchor", "end").attr("fill", theme.muted)
    .text("Agreed with the US in 2024–25 →");
  svg.append("text").attr("x", m.left + 4).attr("y", m.top + 10).attr("fill", theme.muted).text("↑ in 2025–26");
  svg.append("text").attr("x", x(narrow ? 60 : 70)).attr("y", y(narrow ? 66 : 76)).attr("fill", theme.ink2)
    .attr("transform", `rotate(${-Math.atan2(y(0) - y(100), x(100) - x(0)) * 180 / Math.PI},${x(narrow ? 60 : 70)},${y(narrow ? 66 : 76)})`)
    .attr("text-anchor", "middle").text("no change");

  const rows = [...data].sort((a, b) => (NAMED[a.country] ? 1 : 0) - (NAMED[b.country] ? 1 : 0));
  svg.append("g").selectAll("circle").data(rows).join("circle")
    .attr("cx", (d) => x(d.agree_79)).attr("cy", (d) => y(d.agree_80)).attr("r", (d) => (NAMED[d.country] ? 5 : 3.2))
    .attr("fill", colour).attr("fill-opacity", (d) => (NAMED[d.country] ? 1 : 0.7))
    .attr("stroke", theme.paper).attr("stroke-width", (d) => (NAMED[d.country] ? 1.5 : 0.5))
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.country)}</strong>`
      + `Agreed with the US on ${d.agree_79}% of votes in 2024–25<br>and ${d.agree_80}% in 2025–26`))
    .on("pointerleave", () => tooltip.hide());

  const label = svg.append("g").attr("class", "annotation").style("pointer-events", "none");
  const place = { Israel: [8, 4, "start"], Argentina: [8, 4, "start"], Micronesia: [8, -8, "start"],
    "Marshall Islands": [8, 10, "start"], Palau: [-8, 4, "end"], Hungary: [-8, -8, "end"],
    "United Kingdom": [10, 14, "start"], Netherlands: [-8, 12, "end"] };
  for (const d of data.filter((r) => NAMED[r.country])) {
    if (narrow && ["Hungary", "United Kingdom", "Palau", "Netherlands"].includes(d.country)) continue;
    const [dx, dy, anchor] = place[d.country];
    label.append("text").attr("x", x(d.agree_79) + dx).attr("y", y(d.agree_80) + dy).attr("text-anchor", anchor)
      .attr("class", NAMED[d.country] === "ink" ? null : "label-strong").attr("fill", colour(d))
      .attr("paint-order", "stroke").attr("stroke", theme.paper).attr("stroke-width", 3)
      .text(d.country);
  }

  return [svg.node(), table(data, [
    { key: "country", label: "Country" },
    { key: "agree_79", label: "2024–25 (%)" },
    { key: "agree_80", label: "2025–26 (%)" },
    { key: "change", label: "Change (points)" },
  ])];
}
