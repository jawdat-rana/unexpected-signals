// Agreement with the US per session since 2015 for a few countries. The three
// Pacific states tied to the US by treaty in blue, Argentina and Israel in red.

const COLOUR = { Micronesia: "blue", "Marshall Islands": "blue", Palau: "blue", Argentina: "signal", Israel: "signal" };

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 300 : 360;
  const m = { top: 16, right: narrow ? 116 : 136, bottom: 26, left: 36 };
  const years = [...new Set(data.map((d) => d.start_year))].sort();
  const x = d3.scaleLinear(d3.extent(years), [m.left, width - m.right]);
  const y = d3.scaleLinear([0, 100], [height - m.bottom, m.top]);
  const groups = d3.groups(data, (d) => d.country);
  const stroke = (c) => ({ signal: theme.signal, blue: theme.categorical[1] }[COLOUR[c]] ?? theme.context);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Line chart of agreement with the United States from 2015 to 2025. Micronesia stays between 62 and 82 percent until 2024, then drops to 23 percent. Argentina rises from about 20 percent to 71 percent in 2024. Israel stays near 80 to 90 percent.");

  svg.append("g").selectAll("line").data([25, 50, 75, 100]).join("line")
    .attr("x1", m.left).attr("x2", width - m.right).attr("y1", y).attr("y2", y).attr("stroke", theme.grid);
  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).tickValues([0, 25, 50, 75, 100]).tickFormat((d) => `${d}%`).tickSize(0))
    .call((g) => g.select(".domain").remove()).attr("color", theme.muted);
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues((narrow ? [2015, 2020, 2025] : years.filter((v, i) => i % 2 === 0)))
      .tickFormat((v) => `${v}–${String(v + 1).slice(2)}`).tickSize(0))
    .call((g) => g.select(".domain").attr("stroke", theme.rule)).attr("color", theme.muted);

  const line = d3.line((d) => x(d.start_year), (d) => y(d.agree));
  const ordered = [...groups].sort(([a], [b]) => (COLOUR[a] ? 1 : 0) - (COLOUR[b] ? 1 : 0));
  svg.append("g").selectAll("path").data(ordered).join("path")
    .attr("d", ([, rows]) => line(rows)).attr("fill", "none").attr("stroke", ([c]) => stroke(c))
    .attr("stroke-width", ([c]) => (COLOUR[c] ? 2.5 : 1.5));

  // End labels, nudged apart.
  const ends = groups.map(([c, rows]) => ({ c, v: rows[rows.length - 1].agree, yy: y(rows[rows.length - 1].agree) }))
    .sort((a, b) => a.yy - b.yy);
  for (let i = 1; i < ends.length; i++) ends[i].yy = Math.max(ends[i].yy, ends[i - 1].yy + 12);
  svg.append("g").selectAll("text").data(ends).join("text")
    .attr("x", width - m.right + 6).attr("y", (d) => d.yy).attr("dy", "0.32em")
    .attr("fill", (d) => (COLOUR[d.c] ? stroke(d.c) : theme.muted))
    .attr("class", (d) => (COLOUR[d.c] ? "label-strong" : null))
    .text((d) => `${narrow && d.c === "Marshall Islands" ? "Marshall Is." : narrow && d.c === "United Kingdom" ? "UK" : narrow && d.c === "Netherlands" ? "Neth." : d.c} ${Math.round(d.v)}%`);

  svg.append("g").selectAll("circle").data(data).join("circle")
    .attr("cx", (d) => x(d.start_year)).attr("cy", (d) => y(d.agree)).attr("r", 6).attr("fill", "transparent")
    .on("pointerenter pointermove", (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.country)}, ${d.start_year}–${String(d.start_year + 1).slice(2)}</strong>`
      + `Voted like the US on ${d.agree}% of ${d.votes} recorded votes`))
    .on("pointerleave", () => tooltip.hide());

  return [svg.node(), table(data.filter((d) => d.start_year >= 2023), [
    { key: "country", label: "Country" },
    { key: "start_year", label: "Session", format: (v) => `${v}–${String(v + 1).slice(2)}` },
    { key: "agree", label: "Agreement (%)" },
    { key: "votes", label: "Votes" },
  ])];
}
