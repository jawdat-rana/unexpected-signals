// The Dutch rail network, one line per section of track between two stations.
// Line width: NS passengers per working day. Colour: hours disrupted, or the
// journeys that ran into those hours. A toggle switches the colour.

import outline from "./netherlands.js";

const MODES = {
  trips: {
    label: "Journeys caught",
    key: "trips_hit",
    // Bin edges, so the legend reads as clear steps.
    bins: [100e3, 500e3, 1.5e6, 3e6],
    names: ["< 100k", "100k–500k", "0.5–1.5M", "1.5–3M", "3M+"],
    legend: "Journeys that passed while the section was disrupted, 2025",
  },
  hours: {
    label: "Hours disrupted",
    key: "hours",
    bins: [100, 250, 400, 600],
    names: ["< 100", "100–250", "250–400", "400–600", "600+"],
    legend: "Hours the section had a disruption, 2025",
  },
};

// Kept outside draw(), so a resize or theme switch keeps the reader's choice.
let mode = "trips";

// Orientation labels: [station code, label, dx, dy, anchor, shown when narrow]
const PLACES = [
  ["ASD", "Amsterdam", 6, -6, "start", true],
  ["RTD", "Rotterdam", -8, 4, "end", true],
  ["GVC", "Den Haag", -8, -2, "end", true],
  ["UT", "Utrecht", 8, 4, "start", true],
  ["EHV", "Eindhoven", 0, 16, "middle", true],
  ["GN", "Groningen", 0, -9, "middle", true],
  ["ZL", "Zwolle", 8, 4, "start", false],
  ["AH", "Arnhem", 8, 12, "start", false],
  ["NM", "Nijmegen", 8, 4, "start", false],
  ["MT", "Maastricht", 8, 4, "start", false],
  ["LW", "Leeuwarden", 0, -9, "middle", false],
  ["ES", "Enschede", 0, 16, "middle", false],
  ["BD", "Breda", 0, 16, "middle", false],
  ["HT", "Den Bosch", 8, 12, "start", false],
];

const fmt = (v) => (v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${Math.round(v / 1e3)}k` : `${v}`);

export default function draw({ data, width, d3, theme, tooltip, table }) {
  const narrow = width < 560;
  const height = Math.round(Math.min(760, Math.max(420, width * 1.12)));
  const m = MODES[mode];

  const land = outline.features[0];
  const projection = d3.geoMercator().fitExtent([[8, 8], [width - 8, height - 8]], land);
  const path = d3.geoPath(projection);
  const xy = (lat, lng) => projection([lng, lat]);

  // Grey to signal red in four steps; the top step steps further away from the
  // paper (darker on light paper, brighter on dark), so it stands out in both.
  const dark = d3.hsl(theme.paper).l < 0.5;
  const ramp = [0, 0.4, 0.7, 1].map((t) => d3.interpolateLab(theme.context, theme.signal)(t));
  ramp.push((dark ? d3.color(theme.signal).brighter(0.7) : d3.color(theme.signal).darker(0.9)).formatHex());
  const color = d3.scaleThreshold(m.bins, ramp);
  const maxPassengers = d3.max(data, (d) => d.passengers);
  const stroke = d3.scaleSqrt([0, maxPassengers], [0.8, narrow ? 6 : 9]);

  const rows = data.map((d) => ({ ...d, a: xy(d.from_lat, d.from_lng), b: xy(d.to_lat, d.to_lng) }));
  const counted = rows.filter((d) => d.passengers > 0).sort((p, q) => p[m.key] - q[m.key]);
  const uncounted = rows.filter((d) => d.passengers === 0);

  // --- Controls and legend (HTML, so they wrap and stay readable) ---
  const head = document.createElement("div");
  head.style.cssText = "display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;margin:0 0 6px;font-size:13px;color:var(--ink-2)";
  const toggle = document.createElement("div");
  toggle.setAttribute("role", "group");
  toggle.setAttribute("aria-label", "Colour the map by");
  toggle.style.cssText = "display:inline-flex;border:1px solid var(--rule-strong);border-radius:3px;overflow:hidden";
  for (const [key, def] of Object.entries(MODES)) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = def.label;
    button.setAttribute("aria-pressed", String(key === mode));
    const on = key === mode;
    button.style.cssText = `font:inherit;font-size:13px;padding:5px 10px;border:0;cursor:pointer;`
      + `background:${on ? "var(--ink)" : "transparent"};color:${on ? "var(--paper)" : "var(--ink)"}`;
    button.addEventListener("click", () => {
      if (mode === key) return;
      mode = key;
      const el = head.parentElement;
      // Redraw in place with the same width.
      const nodes = draw({ data, width, d3, theme, tooltip, table });
      el.replaceChildren(...nodes, tooltip.node);
    });
    toggle.append(button);
  }
  const key = document.createElement("div");
  key.style.cssText = "display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px";
  key.innerHTML = ramp.map((c, i) => `<span style="display:inline-flex;align-items:center;gap:5px">`
    + `<svg width="18" height="8" aria-hidden="true"><line x1="1" y1="4" x2="17" y2="4" stroke="${c}" stroke-width="5" stroke-linecap="round"/></svg>`
    + `${m.names[i]}</span>`).join("");
  const caption = document.createElement("div");
  caption.style.cssText = "width:100%;font-size:12px;color:var(--muted)";
  caption.textContent = `${m.legend}. Line width: NS passengers per working day.`;
  head.append(toggle, key, caption);

  // --- Map ---
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .attr("role", "img")
    .attr("aria-label", "Map of the Dutch rail network. The sections around Schiphol, Amsterdam and Utrecht stand out as both busy and often disrupted.");

  svg.append("path").attr("d", path(land)).attr("fill", theme.paper2).attr("stroke", theme.rule).attr("stroke-width", 0.75);
  svg.append("path").attr("d", path(outline.features[1])).attr("fill", theme.paper).attr("stroke", theme.rule).attr("stroke-width", 0.5);

  const line = (d) => `M${d.a[0]},${d.a[1]}L${d.b[0]},${d.b[1]}`;
  svg.append("g").attr("fill", "none").attr("stroke", theme.muted).attr("stroke-width", 0.8)
    .attr("stroke-dasharray", "2 2").attr("opacity", 0.7)
    .selectAll("path").data(uncounted).join("path").attr("d", line);
  svg.append("g").attr("fill", "none").attr("stroke-linecap", "round")
    .selectAll("path").data(counted).join("path").attr("d", line)
    .attr("stroke", (d) => color(d[m.key])).attr("stroke-width", (d) => stroke(d.passengers));

  // Place labels, from the section ends.
  const where = new Map();
  for (const d of rows) {
    where.set(d.from_code, d.a);
    where.set(d.to_code, d.b);
  }
  const places = PLACES.filter((p) => where.has(p[0]) && (!narrow || p[5]));
  const labels = svg.append("g").attr("class", "annotation");
  labels.selectAll("circle").data(places).join("circle")
    .attr("cx", (p) => where.get(p[0])[0]).attr("cy", (p) => where.get(p[0])[1]).attr("r", 2)
    .attr("fill", theme.ink);
  labels.selectAll("text").data(places).join("text")
    .attr("x", (p) => where.get(p[0])[0] + p[2]).attr("y", (p) => where.get(p[0])[1] + p[3])
    .attr("text-anchor", (p) => p[4]).attr("paint-order", "stroke").attr("stroke", theme.paper2)
    .attr("stroke-width", 3).attr("stroke-linejoin", "round").attr("fill", theme.ink2).text((p) => p[1]);

  // The Schiphol callout sits in the North Sea, with a leader line.
  const shl = where.get("SHL");
  if (shl) {
    const lx = Math.max(10, shl[0] - (narrow ? 70 : 120));
    const ly = shl[1] - (narrow ? 40 : 60);
    svg.append("path").attr("class", "annotation-line").attr("d", `M${shl[0] - 4},${shl[1] - 3}L${lx + 4},${ly + 6}`);
    svg.append("text").attr("class", "label-strong").attr("x", lx).attr("y", ly - 14).text("The line under Schiphol");
    svg.append("text").attr("class", "annotation").attr("x", lx).attr("y", ly).text("817 hours disrupted in 2025");
  }

  // --- Hover: wide invisible strokes make thin lines easy to hit ---
  const highlight = svg.append("path").attr("fill", "none").attr("stroke", theme.ink)
    .attr("stroke-linecap", "round").style("pointer-events", "none").style("display", "none");
  svg.append("g").attr("fill", "none").attr("stroke", "transparent").attr("stroke-width", 12)
    .selectAll("path").data(rows).join("path").attr("d", line).style("cursor", "pointer")
    .on("pointerenter pointermove", (event, d) => {
      highlight.style("display", null).attr("d", line(d))
        .attr("stroke-width", Math.max(2, (d.passengers ? stroke(d.passengers) : 1) + 2)).attr("opacity", 0.35);
      const causes = d.top_causes ? `<br><span class="muted">Main causes: ${tooltip.esc(d.top_causes)}</span>` : "";
      tooltip.show(event, `<strong>${tooltip.esc(d.from_name)} – ${tooltip.esc(d.to_name)}</strong>`
        + (d.passengers
          ? `${d3.format(",")(d.passengers)} NS passengers a working day<br>`
            + `${d3.format(",")(Math.round(d.hours))} hours disrupted in 2025<br>`
            + `about ${fmt(d.trips_hit)} journeys caught`
          : `No NS passenger count (other operator)<br>${d3.format(",")(Math.round(d.hours))} hours disrupted in 2025`)
        + causes);
    })
    .on("pointerleave", () => {
      highlight.style("display", "none");
      tooltip.hide();
    });

  const top = [...data].filter((d) => d.passengers > 0).sort((p, q) => q.trips_hit - p.trips_hit).slice(0, 25);
  return [head, svg.node(), table(top, [
    { key: "from_name", label: "From" },
    { key: "to_name", label: "To" },
    { key: "passengers", label: "Passengers a day", format: d3.format(",") },
    { key: "hours", label: "Hours disrupted", format: (v) => d3.format(",")(Math.round(v)) },
    { key: "trips_hit", label: "Journeys caught", format: d3.format(",") },
  ])];
}
