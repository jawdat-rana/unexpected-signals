// A day at the Spijkenisserbrug, replayed. Press play and the day runs in
// 5-minute steps: the two bridges lift when NDW reports them open, and the
// lines show what the traffic sensors next to them measured.
//
// The chart redraws on resize and theme change, so the playback state lives on
// the chart's element and survives a redraw.

const STEP_MS = 90; // one 5-minute step of the day per 90 ms: a day in ~26 s

const fmt = (v) => (v === null || v === "" ? "–" : Math.round(v).toLocaleString("en-GB"));
const minutes = (t) => +t.slice(0, 2) * 60 + +t.slice(3, 5);

export default function draw({ data, width, d3, theme, table, el }) {
  const narrow = width < 560;
  const days = [...new Set(data.map((d) => d.day))];
  const state = (el._replay ??= { day: days[days.length - 1], i: 0, playing: false, timer: null });
  if (!days.includes(state.day)) state.day = days[days.length - 1];
  clearInterval(state.timer);

  const root = document.createElement("div");
  root.className = "replay";
  root.style.cssText = "display:grid;gap:12px;font-family:var(--sans);color:var(--ink)";

  // --- Controls -------------------------------------------------------------
  const controls = document.createElement("div");
  controls.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;align-items:center";
  const button = (label) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.style.cssText = `font:inherit;font-size:13px;padding:6px 10px;border-radius:4px;cursor:pointer;
      border:1px solid ${theme.rule};background:${theme.paper};color:${theme.ink}`;
    return b;
  };
  const play = button("▶ Play");
  play.style.fontWeight = "600";
  play.style.minWidth = "84px";
  controls.append(play);
  const dayButtons = days.map((day) => {
    const b = button(day);
    b.addEventListener("click", () => {
      state.day = day;
      state.i = 0;
      render(true);
    });
    controls.append(b);
    return [day, b];
  });

  // --- Status: two bridges and the clock ----------------------------------------
  const status = document.createElement("div");
  status.style.cssText = `display:grid;gap:10px;grid-template-columns:${width < 520 ? "1fr" : "auto 1fr 1fr"};
    align-items:stretch`;
  const clock = document.createElement("div");
  clock.style.cssText = `font-size:${width < 520 ? 28 : 36}px;font-weight:700;font-variant-numeric:tabular-nums;
    align-self:center;${width < 520 ? "grid-column:1 / -1" : "padding-right:8px"}`;
  clock.setAttribute("aria-live", "off");
  status.append(clock);

  const card = (name, road) => {
    const box = document.createElement("div");
    box.style.cssText = `border:1px solid ${theme.rule};border-radius:6px;padding:8px 10px;display:grid;
      grid-template-columns:56px 1fr;gap:4px 10px;align-items:center`;
    const svg = d3.create("svg").attr("viewBox", "0 0 56 40").attr("width", 56).attr("height", 40)
      .attr("aria-hidden", "true");
    svg.append("rect").attr("x", 0).attr("y", 34).attr("width", 56).attr("height", 6).attr("fill", theme.grid);
    svg.append("rect").attr("x", 4).attr("y", 2).attr("width", 6).attr("height", 34).attr("fill", theme.context);
    svg.append("rect").attr("x", 46).attr("y", 2).attr("width", 6).attr("height", 34).attr("fill", theme.context);
    const deck = svg.append("rect").attr("x", 10).attr("width", 36).attr("height", 5);
    const text = document.createElement("div");
    text.innerHTML = `<div style="font-weight:600;font-size:14px">${name}</div>
      <div class="state" style="font-size:13px"></div>
      <div class="flow" style="font-size:12px;color:${theme.muted}"></div>`;
    box.append(svg.node(), text);
    status.append(box);
    return (open, flow) => {
      deck.attr("y", open ? 4 : 26).attr("fill", open ? theme.signal : theme.ink);
      box.style.borderColor = open ? theme.signal : theme.rule;
      text.querySelector(".state").innerHTML = open
        ? `<strong style="color:${theme.signal}">Open for ships</strong>`
        : "Down for cars";
      text.querySelector(".flow").textContent = `${road}: ${fmt(flow)} vehicles an hour`;
    };
  };
  const spijkenisse = card("Spijkenisserbrug", "Groene Kruisweg");
  const botlek = card("Botlekbrug", "A15 main road");

  // --- Timeline -------------------------------------------------------------------
  const m = { top: 18, right: 20, bottom: 26, left: narrow ? 40 : 48 };
  const panel = narrow ? 92 : 110;
  const gap = 30;
  const height = m.top + panel * 2 + gap + m.bottom;
  const x = d3.scaleLinear([0, 24 * 60], [m.left, width - m.right]);
  const panels = [
    { key: "groene_kruisweg_flow", open: "spijkenisserbrug_open", y0: m.top,
      label: narrow ? "Groene Kruisweg, Spijkenisse" : "Groene Kruisweg, next to the Spijkenisserbrug", colour: theme.ink },
    { key: "a15_flow", open: "botlekbrug_open", y0: m.top + panel + gap,
      label: narrow ? "A15 main road at the Botlek" : "A15 main road at the Botlek crossing, both directions", colour: theme.context },
  ];

  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", width)
    .style("touch-action", "none").style("cursor", "pointer")
    .attr("role", "img")
    .attr("aria-label", "Timeline of one day: vehicles an hour on the Groene Kruisweg and the A15, with red bands when the Spijkenisserbrug and the Botlekbrug were open. Traffic on the Groene Kruisweg drops when the Spijkenisserbrug opens.");

  const layers = panels.map((p) => {
    const g = svg.append("g");
    const y = d3.scaleLinear([0, 1], [p.y0 + panel, p.y0]);
    g.append("text").attr("x", m.left).attr("y", p.y0 - 6).attr("font-size", 12)
      .attr("font-weight", 600).attr("fill", theme.ink).text(p.label);
    return { ...p, g, y, bands: g.append("g"), axis: g.append("g").attr("class", "axis"),
      faint: g.append("path").attr("fill", "none").attr("stroke", theme.grid).attr("stroke-width", 1.5),
      line: g.append("path").attr("fill", "none").attr("stroke", p.colour).attr("stroke-width", 1.75) };
  });

  svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(d3.range(0, 24 * 60 + 1, narrow ? 360 : 180)).tickSize(0)
      .tickPadding(8).tickFormat((v) => `${String(v / 60).padStart(2, "0")}:00`));
  const head = svg.append("line").attr("y1", m.top - 2).attr("y2", height - m.bottom)
    .attr("stroke", theme.signal).attr("stroke-width", 1.5);

  // --- Drawing a day and a moment ---------------------------------------------------
  let rows = [];
  function render(newDay = false) {
    rows = data.filter((d) => d.day === state.day);
    state.i = Math.min(state.i, rows.length - 1);
    for (const [day, b] of dayButtons) {
      const on = day === state.day;
      b.style.background = on ? theme.ink : theme.paper;
      b.style.color = on ? theme.paper : theme.ink;
      b.setAttribute("aria-pressed", String(on));
    }
    if (newDay || !layers[0].drawn) {
      for (const l of layers) {
        const max = d3.max(data, (d) => d[l.key]) || 1;
        l.y.domain([0, max]).nice();
        l.axis.attr("transform", `translate(${m.left},0)`)
          .call(d3.axisLeft(l.y).ticks(3).tickSize(-(width - m.left - m.right))
            .tickFormat((v) => (v >= 1000 ? `${v / 1000}k` : v)))
          .call((a) => a.select(".domain").remove())
          .call((a) => a.selectAll("line").attr("stroke", theme.grid));
        // Red bands where the bridge was open, one per run of open steps.
        const runs = [];
        rows.forEach((d, i) => {
          if (!d[l.open]) return;
          const last = runs[runs.length - 1];
          if (last && last.end === i - 1) last.end = i;
          else runs.push({ start: i, end: i });
        });
        l.bands.selectAll("rect").data(runs).join("rect")
          .attr("x", (r) => x(minutes(rows[r.start].time) - 2.5))
          .attr("width", (r) => Math.max(2, x(minutes(rows[r.end].time) + 2.5) - x(minutes(rows[r.start].time) - 2.5)))
          .attr("y", l.y0).attr("height", panel).attr("fill", theme.signal).attr("opacity", 0.18);
        l.drawn = true;
      }
    }
    const line = (l, upTo) => d3.line().defined((d) => d[l.key] !== null)
      .x((d) => x(minutes(d.time))).y((d) => l.y(d[l.key]))(rows.slice(0, upTo));
    for (const l of layers) {
      l.faint.attr("d", line(l, rows.length));
      l.line.attr("d", line(l, state.i + 1));
    }
    const now = rows[state.i];
    head.attr("x1", x(minutes(now.time))).attr("x2", x(minutes(now.time)));
    clock.textContent = now.time;
    spijkenisse(now.spijkenisserbrug_open, now.groene_kruisweg_flow);
    botlek(now.botlekbrug_open, now.a15_flow);
    play.textContent = state.playing ? "❚❚ Pause" : state.i >= rows.length - 1 ? "↺ Replay" : "▶ Play";
  }

  function tick() {
    if (state.i >= rows.length - 1) {
      stop();
      return;
    }
    state.i += 1;
    render();
  }
  function start() {
    if (state.i >= rows.length - 1) state.i = 0;
    state.playing = true;
    clearInterval(state.timer);
    state.timer = setInterval(() => {
      if (!el.isConnected) return stop();
      tick();
    }, STEP_MS);
    render();
  }
  function stop() {
    state.playing = false;
    clearInterval(state.timer);
    render();
  }
  play.addEventListener("click", () => (state.playing ? stop() : start()));

  // Scrub: click or drag on the timeline to jump to a moment.
  const seek = (event) => {
    const [px] = d3.pointer(event, svg.node());
    const t = x.invert(px);
    state.i = d3.leastIndex(rows, (d) => Math.abs(minutes(d.time) - t));
    render();
  };
  svg.on("pointerdown", (event) => {
    stop();
    seek(event);
    svg.node().setPointerCapture(event.pointerId);
  }).on("pointermove", (event) => {
    if (event.buttons) seek(event);
  });

  root.append(controls, status, svg.node());
  render(true);
  if (state.playing) start();

  // The table: per day, traffic on the Groene Kruisweg with the bridge up and down.
  const summary = days.map((day) => {
    const daytime = data.filter((d) => d.day === day && d.time >= "06:00" && d.time < "20:00"
      && d.groene_kruisweg_flow !== null);
    const up = daytime.filter((d) => d.spijkenisserbrug_open);
    const down = daytime.filter((d) => !d.spijkenisserbrug_open);
    return { day, up: up.length, flow_up: d3.mean(up, (d) => d.groene_kruisweg_flow),
      flow_down: d3.mean(down, (d) => d.groene_kruisweg_flow) };
  });
  return [root, table(summary, [
    { key: "day", label: "Day" },
    { key: "up", label: "5-minute steps with the Spijkenisserbrug open, 06:00–20:00" },
    { key: "flow_up", label: "Groene Kruisweg, vehicles an hour: bridge open", format: fmt },
    { key: "flow_down", label: "Bridge down", format: fmt },
  ])];
}
