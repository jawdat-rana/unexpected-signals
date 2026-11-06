// D3 template: one line over time, with the unexpected moment coloured and annotated.
//
// Copy this file, point the `chart` shortcode at it, and change the four
// settings below. Everything else (theme, resizing, dark mode) is handled by
// newsroom/assets/js/signals.js.

const X = "week"; // date column
const Y = "value"; // number column
const Y_LABEL = "Index";
const HIGHLIGHT = { from: "2025-10-06", to: "2025-10-13", note: "The spike nobody expected" };

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const height = Math.max(240, Math.min(400, width * 0.55));
  const m = { top: 28, right: 16, bottom: 28, left: 40 };

  const x = d3.scaleUtc(d3.extent(data, (d) => d[X]), [m.left, width - m.right]);
  const y = d3.scaleLinear([0, d3.max(data, (d) => d[Y]) * 1.1], [height - m.bottom, m.top]).nice();

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width);

  // Recessive grid and axes: the data is the loudest thing on the page.
  svg.append("g").attr("class", "grid")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
  svg.append("g").attr("class", "axis")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8));
  svg.append("g").attr("class", "axis")
    .attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(width < 500 ? 4 : 8).tickSizeOuter(0));
  svg.append("text").attr("x", m.left - 36).attr("y", m.top - 14).text(Y_LABEL);

  const line = d3.line((d) => x(d[X]), (d) => y(d[Y])).curve(d3.curveMonotoneX);

  // Context in grey, the signal in colour.
  svg.append("path").datum(data)
    .attr("fill", "none").attr("stroke", theme.context).attr("stroke-width", 2).attr("d", line);

  const from = new Date(HIGHLIGHT.from);
  const to = new Date(HIGHLIGHT.to);
  const i0 = Math.max(0, data.findIndex((d) => d[X] >= from) - 1);
  const i1 = data.findIndex((d) => d[X] > to);
  const signal = data.slice(i0, i1 === -1 ? undefined : i1 + 1);
  svg.append("path").datum(signal)
    .attr("fill", "none").attr("stroke", theme.signal).attr("stroke-width", 2.5).attr("d", line);

  // Annotation: say what the reader should see, right next to it.
  const peak = d3.greatest(signal, (d) => d[Y]);
  const px = x(peak[X]);
  const py = y(peak[Y]);
  const left = px > width * 0.6;
  svg.append("path").attr("class", "annotation-line")
    .attr("d", `M${px},${py - 6} L${px},${m.top + 4}`);
  svg.append("text").attr("class", "annotation label-strong")
    .attr("x", px + (left ? -6 : 6)).attr("y", m.top + 8)
    .attr("text-anchor", left ? "end" : "start").text(HIGHLIGHT.note);
  svg.append("circle").attr("cx", px).attr("cy", py).attr("r", 4.5)
    .attr("fill", theme.signal).attr("stroke", theme.paper).attr("stroke-width", 2);

  // Crosshair and tooltip: hover anywhere, not just on the thin line.
  const focus = svg.append("g").style("display", "none");
  focus.append("line").attr("stroke", theme.muted).attr("y1", m.top).attr("y2", height - m.bottom);
  focus.append("circle").attr("r", 4).attr("fill", theme.ink);
  const format = d3.utcFormat("%-d %b %Y");
  svg.append("rect")
    .attr("x", m.left).attr("y", m.top).attr("width", width - m.left - m.right)
    .attr("height", height - m.top - m.bottom).attr("fill", "transparent")
    .on("pointerleave", () => { focus.style("display", "none"); tooltip.hide(); })
    .on("pointermove", (event) => {
      const i = d3.bisectCenter(data.map((d) => d[X]), x.invert(d3.pointer(event)[0]));
      const d = data[i];
      focus.style("display", null);
      focus.select("line").attr("x1", x(d[X])).attr("x2", x(d[X]));
      focus.select("circle").attr("cx", x(d[X])).attr("cy", y(d[Y]));
      tooltip.show(event, `<strong>${format(d[X])}</strong>${d3.format(",.1f")(d[Y])}`);
    });

  return [svg.node(), table(data, [
    { key: X, label: "Week", format },
    { key: Y, label: Y_LABEL },
  ])];
}
