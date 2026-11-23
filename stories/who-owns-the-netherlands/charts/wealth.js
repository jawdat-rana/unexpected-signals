// Scatter: share of households owning their home (y) against share of
// millionaire households (x). Municipalities in grey, sized by number of homes;
// the twelve provinces in the signal colour, to show the pattern flipping.

const LABELS = new Set(["Amsterdam", "Utrecht", "Rotterdam", "Bloemendaal", "Laren (NH.)"]);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = narrow ? 340 : 420;
  const m = { top: 20, right: 16, bottom: 40, left: 44 };
  const munis = data.filter((d) => d.level === "municipality");
  const provs = data.filter((d) => d.level === "province");

  const x = d3.scaleLinear([0, d3.max(munis, (d) => d.millionaire_pct) + 2], [m.left, width - m.right]);
  const y = d3.scaleLinear([20, 90], [height - m.bottom, m.top]);
  const r = d3.scaleSqrt([0, d3.max(munis, (d) => d.dwellings)], [1.5, narrow ? 12 : 18]);

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);
  svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat((v) => `${v}%`));
  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 4 : 8).tickSize(0).tickPadding(8).tickFormat((v) => `${v}%`));
  svg.append("text").attr("class", "annotation").attr("x", width - m.right).attr("y", height - 6)
    .attr("text-anchor", "end").text("Households worth €1M or more →");
  svg.append("text").attr("class", "annotation").attr("x", m.left + 4).attr("y", m.top + 4)
    .text("↑ Households that own their home");

  const show = (event, d) => tooltip.show(event, `<strong>${tooltip.esc(d.name)}</strong>${d.level === "province" ? " (province)" : ""}<br>`
    + `Own their home: ${d.own_pct}%<br>Millionaire households: ${d.millionaire_pct}%`
    + (d.level === "municipality" ? `<br>${d3.format(",")(d.dwellings)} homes` : ""));

  svg.append("g").selectAll("circle").data(munis.sort((a, b) => b.dwellings - a.dwellings)).join("circle")
    .attr("cx", (d) => x(d.millionaire_pct)).attr("cy", (d) => y(d.own_pct)).attr("r", (d) => r(d.dwellings))
    .attr("fill", theme.context).attr("fill-opacity", 0.55).attr("stroke", theme.paper).attr("stroke-width", 0.75)
    .on("pointermove", show).on("pointerleave", () => tooltip.hide());

  // Province trend: a straight line through the provinces, to show it slopes down.
  const fit = (rows) => {
    const mx = d3.mean(rows, (d) => d.millionaire_pct), my = d3.mean(rows, (d) => d.own_pct);
    const b = d3.sum(rows, (d) => (d.millionaire_pct - mx) * (d.own_pct - my)) / d3.sum(rows, (d) => (d.millionaire_pct - mx) ** 2);
    return (v) => my + b * (v - mx);
  };
  const mf = fit(munis);
  const [m0, m1] = d3.extent(munis, (d) => d.millionaire_pct);
  svg.append("line").attr("x1", x(m0)).attr("x2", x(m1)).attr("y1", y(mf(m0))).attr("y2", y(mf(m1)))
    .attr("stroke", theme.ink).attr("stroke-width", 1.25).attr("stroke-opacity", 0.6);
  const lx = narrow ? 22 : 24;
  svg.append("text").attr("class", "annotation").attr("x", x(lx)).attr("y", y(mf(lx)) - 8)
    .attr("text-anchor", "middle").attr("transform", `rotate(${(Math.atan2(y(mf(m1)) - y(mf(m0)), x(m1) - x(m0)) * 180) / Math.PI},${x(lx)},${y(mf(lx)) - 8})`).text(narrow ? "Municipalities" : "Municipalities: the richer, the more owners");
  const pf = fit(provs);
  const [p0, p1] = d3.extent(provs, (d) => d.millionaire_pct);
  svg.append("line").attr("x1", x(p0)).attr("x2", x(p1)).attr("y1", y(pf(p0))).attr("y2", y(pf(p1)))
    .attr("stroke", theme.signal).attr("stroke-width", 2).attr("stroke-dasharray", "4 3");

  svg.append("g").selectAll("circle").data(provs).join("circle")
    .attr("cx", (d) => x(d.millionaire_pct)).attr("cy", (d) => y(d.own_pct)).attr("r", 5)
    .attr("fill", theme.signal).attr("stroke", theme.paper).attr("stroke-width", 1.5)
    .on("pointermove", show).on("pointerleave", () => tooltip.hide());

  svg.append("g").selectAll("text").data(munis.filter((d) => LABELS.has(d.name))).join("text")
    .attr("class", "annotation")
    .attr("x", (d) => x(d.millionaire_pct) + (x(d.millionaire_pct) > width * 0.8 ? -1 : 1) * (r(d.dwellings) + 3))
    .attr("text-anchor", (d) => (x(d.millionaire_pct) > width * 0.8 ? "end" : "start"))
    .attr("y", (d) => y(d.own_pct) + (d.name.startsWith("Laren") ? 9 : d.name === "Bloemendaal" ? -9 : 0)).attr("dy", "0.35em").text((d) => d.name.replace(" (NH.)", ""));
  const label = narrow ? "Provinces" : "Provinces: the richer, the fewer owners";
  const nh = provs.find((d) => d.name === "Noord-Holland") || provs[0];
  svg.append("text").attr("class", "label-strong").attr("fill", theme.signal)
    .attr("x", x(nh.millionaire_pct) + 8).attr("y", y(nh.own_pct) + 16).text(label);

  return [svg.node(), table([...provs, ...munis.sort((a, b) => b.millionaire_pct - a.millionaire_pct)], [
    { key: "name", label: "Place" },
    { key: "level", label: "Level" },
    { key: "own_pct", label: "Own their home (%)" },
    { key: "millionaire_pct", label: "Millionaire households (%)" },
    { key: "dwellings", label: "Homes", format: d3.format(",") },
  ])];
}
