// The Netherlands on water, replayed. Every dot is a Rijkswaterstaat gauge;
// its colour and size show how far the water stands above or below that
// gauge's normal level, every 10 minutes. Press play to watch the tide run up
// the coast twice a day, storm Pia push the sea in, the barriers shut, and the
// Rhine and Maas flood wave roll down to the sea. "Rotterdam" zooms in on the
// river mouth and the Maeslantkering.
//
// The runtime redraws on resize and theme change, so playback state lives on
// the chart element and survives a redraw.

import land from "./netherlands.js";
import rivers from "./rivers.js";
import { stations, moments, barriers } from "./meta.js";

const SPEEDS = [
  { label: "1 day = 8 s", ms: 55 },
  { label: "1 day = 3 s", ms: 20 },
];
const ROTTERDAM = [[3.95, 51.78], [4.72, 52.02]]; // lon/lat box for the zoom
const BARRIERS = {
  Maeslantkering: [4.163, 51.956],
  Oosterscheldekering: [3.69, 51.645],
};
// Labelled in the national view; the Rotterdam view labels every station there.
const NATIONAL_LABELS = new Set(["vlissingen", "hoek-van-holland", "den-helder", "harlingen",
  "delfzijl", "lobith", "venlo", "kampen", "rotterdam"]);

const when = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Amsterdam", weekday: "short",
  day: "numeric", month: "short", year: "numeric" });
const clockFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Amsterdam", hour: "2-digit",
  minute: "2-digit" });
const metres = (cm) => (cm === null || cm === undefined ? "–"
  : `${cm >= 0 ? "+" : "−"}${Math.abs(cm / 100).toFixed(2)} m`);

export default function draw({ data, width, d3, theme, table, el }) {
  const S = theme.stage;
  const narrow = width < 600;
  const times = data.map((d) => d.t);
  const n = data.length;
  const state = (el._water ??= { i: 0, playing: false, view: "nl", speed: 0, timer: null });
  clearInterval(state.timer);
  state.timer = null;
  if (state.i >= n) state.i = 0;

  const anomaly = (key, i) => {
    const v = data[i][key];
    return v === null || v === undefined || v === "" ? null : v - byKey.get(key).normal;
  };
  const byKey = new Map(stations.map((s) => [s.key, s]));
  const colour = d3.scaleLinear()
    .domain([-150, 0, 100, 200, 300])
    .range([S.low, S.mid, S.high, S.peak, S.alert])
    .interpolate(d3.interpolateRgb)
    .clamp(true);
  const radius = (a) => (a === null ? 2.5 : 3 + Math.min(Math.abs(a), 300) / 300 * (narrow ? 7 : 10));

  const root = document.createElement("div");
  root.style.cssText = `display:grid;gap:10px;font-family:var(--sans);color:${S.ink}`;

  // --- Controls -------------------------------------------------------------
  const controls = document.createElement("div");
  controls.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;align-items:center";
  const button = (label, title = "") => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    if (title) b.title = title;
    b.style.cssText = `font:inherit;font-size:13px;padding:6px 10px;border-radius:4px;cursor:pointer;
      border:1px solid ${S.grid};background:${S.panel};color:${S.ink}`;
    return b;
  };
  const play = button("▶ Play");
  play.style.cssText += ";font-weight:600;min-width:84px";
  const speed = button(SPEEDS[state.speed].label, "Playback speed");
  const viewNl = button("Netherlands");
  const viewRdam = button("Rotterdam");
  controls.append(play, speed, viewNl, viewRdam);
  const jumps = document.createElement("div");
  jumps.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:12px";
  jumps.innerHTML = `<span style="color:${S.muted}">Jump to</span>`;
  for (const m of moments) {
    const b = button(m.label);
    b.style.fontSize = "12px";
    b.addEventListener("click", () => {
      // Start a few hours early so the build-up is visible.
      const target = times.findIndex((t) => +t >= +new Date(m.t));
      state.i = Math.max(0, target - 36);
      if (m.station !== "hoek-van-holland" && state.view === "rdam") setView("nl");
      if (m.station === "hoek-van-holland" && state.view !== "rdam") setView("rdam");
      update();
      start();
    });
    jumps.append(b);
  }

  // --- Clock and readout --------------------------------------------------------
  const head = document.createElement("div");
  head.style.cssText = `display:flex;flex-wrap:wrap;gap:6px 24px;align-items:baseline`;
  const clock = document.createElement("div");
  clock.style.cssText = `font-size:${narrow ? 26 : 34}px;font-weight:600;font-variant-numeric:tabular-nums`;
  const day = document.createElement("div");
  day.style.cssText = `font-size:14px;color:${S.muted}`;
  const readout = document.createElement("div");
  readout.style.cssText = `font-size:13px;color:${S.muted};font-variant-numeric:tabular-nums;
    flex-basis:100%`;
  head.append(clock, day, readout);

  // --- Map ----------------------------------------------------------------------
  const mapWidth = width - 24;
  const mapHeight = Math.round(narrow ? mapWidth * 1.15 : Math.min(640, mapWidth * 0.72));
  const projection = d3.geoMercator().fitExtent([[10, 10], [mapWidth - 10, mapHeight - 10]], land);
  const path = d3.geoPath(projection);
  const svg = d3.create("svg").attr("viewBox", `0 0 ${mapWidth} ${mapHeight}`)
    .attr("width", mapWidth).attr("height", mapHeight)
    .style("background", S.bg).style("border-radius", "4px").style("touch-action", "manipulation");
  const defs = svg.append("defs");
  const glow = defs.append("filter").attr("id", "water-glow").attr("x", "-100%").attr("y", "-100%")
    .attr("width", "300%").attr("height", "300%");
  glow.append("feGaussianBlur").attr("stdDeviation", 3).attr("result", "b");
  const merge = glow.append("feMerge");
  merge.append("feMergeNode").attr("in", "b");
  merge.append("feMergeNode").attr("in", "SourceGraphic");
  svg.append("clipPath").attr("id", "water-clip").append("rect")
    .attr("width", mapWidth).attr("height", mapHeight);

  const world = svg.append("g").attr("clip-path", "url(#water-clip)").append("g");
  world.append("g").selectAll("path").data(land.features).join("path")
    .attr("d", path)
    .attr("fill", (d) => (d.properties.kind === "land" ? S.land : S.bg))
    .attr("stroke", S.coast).attr("stroke-width", 0.8).attr("vector-effect", "non-scaling-stroke");
  world.append("g").selectAll("path").data(rivers.features).join("path")
    .attr("d", path).attr("fill", "none").attr("stroke", S.coast).attr("stroke-width", 1.2)
    .attr("vector-effect", "non-scaling-stroke");

  const barrierG = world.append("g");
  const barrierMarks = Object.entries(BARRIERS).map(([name, lonlat]) => {
    const [x, y] = projection(lonlat);
    const g = barrierG.append("g").attr("transform", `translate(${x},${y})`);
    const bar = g.append("rect").attr("x", -1.5).attr("y", -7).attr("width", 3).attr("height", 14)
      .attr("rx", 1);
    const text = g.append("text").attr("x", 6).attr("y", -8).attr("font-size", 11)
      .attr("font-weight", 600);
    return { name, g, bar, text };
  });

  const dots = world.append("g").selectAll("circle").data(stations).join("circle")
    .attr("transform", (d) => `translate(${projection([d.lon, d.lat])})`)
    .attr("filter", "url(#water-glow)");
  const labels = world.append("g").selectAll("text").data(stations).join("text")
    .attr("transform", (d) => `translate(${projection([d.lon, d.lat])})`)
    .attr("font-size", 11).attr("paint-order", "stroke").attr("stroke", S.bg)
    .attr("stroke-width", 3).attr("stroke-linejoin", "round");

  // Zoom: scale the map group; dots, labels and barriers are scaled back so
  // they keep their size on screen.
  let k = 1;
  const fitBox = (box) => {
    const [[x0, y1], [x1, y0]] = box.map((p) => projection(p));
    const scale = Math.min(mapWidth / (x1 - x0), mapHeight / (y1 - y0));
    return { k: scale, x: (mapWidth - scale * (x0 + x1)) / 2, y: (mapHeight - scale * (y0 + y1)) / 2 };
  };
  function placeLabels() {
    const zoomed = state.view === "rdam";
    dots.attr("transform", (d) => `translate(${projection([d.lon, d.lat])}) scale(${1 / k})`);
    labels.attr("transform", (d) => `translate(${projection([d.lon, d.lat])}) scale(${1 / k})`)
      .attr("display", (d) => (zoomed ? (d.group === "rotterdam" || d.key === "hoek-van-holland")
        : NATIONAL_LABELS.has(d.key)) ? null : "none");
    barrierMarks.forEach((b) => {
      const [x, y] = projection(BARRIERS[b.name]);
      b.g.attr("transform", `translate(${x},${y}) scale(${1 / k})`);
    });
  }
  function setView(view, animate = true) {
    state.view = view;
    const t = view === "rdam" ? fitBox(ROTTERDAM) : { k: 1, x: 0, y: 0 };
    const from = { k, x: (world.attr("data-x") ?? 0) * 1, y: (world.attr("data-y") ?? 0) * 1 };
    const apply = (p) => {
      k = p.k;
      world.attr("transform", `translate(${p.x},${p.y}) scale(${p.k})`)
        .attr("data-x", p.x).attr("data-y", p.y);
      placeLabels();
    };
    if (!animate || matchMedia("(prefers-reduced-motion: reduce)").matches) apply(t);
    else {
      const ik = d3.interpolate(from, t);
      d3.select(world.node()).transition().duration(1200).ease(d3.easeCubicInOut)
        .tween("zoom", () => (u) => apply(ik(u)));
    }
    viewNl.style.borderColor = view === "nl" ? S.high : S.grid;
    viewRdam.style.borderColor = view === "rdam" ? S.high : S.grid;
  }

  // --- Legend -------------------------------------------------------------------
  const legend = document.createElement("div");
  legend.style.cssText = `display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;font-size:12px;
    color:${S.muted}`;
  const stops = [-150, 0, 100, 200, 300];
  const gradient = `linear-gradient(90deg, ${stops.map((v, i) =>
    `${colour(v)} ${(i / (stops.length - 1)) * 100}%`).join(",")})`;
  legend.innerHTML = `<span>Water level against each gauge's normal</span>
    <span style="display:inline-flex;align-items:center;gap:6px">−1.5 m
      <span style="display:inline-block;width:${narrow ? 120 : 180}px;height:8px;border-radius:4px;
        background:${gradient}"></span>+3 m</span>
    <span><span style="display:inline-block;width:3px;height:12px;background:${S.alert};
      vertical-align:middle"></span> storm barrier shut</span>`;

  // --- Timeline: the sea and the Rhine, with a playhead you can drag ---------------
  const tlHeight = 96;
  const margin = { top: 12, right: 8, bottom: 20, left: 8 };
  const x = d3.scaleTime().domain([times[0], times[n - 1]]).range([margin.left, mapWidth - margin.right]);
  const lines = [
    { key: "hoek-van-holland", label: "Sea at Hoek van Holland", colour: S.high },
    { key: "lobith", label: "Rhine at Lobith", colour: S.peak },
  ].filter((l) => byKey.has(l.key));
  const y = d3.scaleLinear()
    .domain(d3.extent(lines.flatMap((l) => data.map((_, i) => anomaly(l.key, i))).filter((v) => v !== null)))
    .nice().range([tlHeight - margin.bottom, margin.top]);
  const tl = d3.create("svg").attr("viewBox", `0 0 ${mapWidth} ${tlHeight}`).attr("width", mapWidth)
    .attr("height", tlHeight).style("cursor", "pointer").style("touch-action", "none")
    .attr("role", "slider").attr("aria-label", "Replay time").attr("tabindex", 0);
  for (const b of barriers) {
    tl.append("rect").attr("x", x(new Date(b.from))).attr("y", margin.top)
      .attr("width", Math.max(2, x(new Date(b.to)) - x(new Date(b.from))))
      .attr("height", tlHeight - margin.top - margin.bottom).attr("fill", S.alert).attr("opacity", 0.25);
  }
  tl.append("g").attr("transform", `translate(0,${tlHeight - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(narrow ? 4 : 8).tickSizeOuter(0))
    .call((g) => g.select(".domain").attr("stroke", S.grid))
    .call((g) => g.selectAll("line").attr("stroke", S.grid))
    .call((g) => g.selectAll("text").attr("fill", S.muted));
  for (const l of lines) {
    tl.append("path").attr("fill", "none").attr("stroke", l.colour).attr("stroke-width", 1.2)
      .attr("d", d3.line().defined((_, i) => anomaly(l.key, i) !== null)
        .x((_, i) => x(times[i])).y((_, i) => y(anomaly(l.key, i)))(data));
  }
  tl.append("g").attr("font-size", 11).selectAll("text").data(lines).join("text")
    .attr("x", (_, j) => margin.left + 4 + j * 170).attr("y", margin.top - 1).attr("fill", (l) => l.colour)
    .text((l) => l.label);
  const playhead = tl.append("line").attr("y1", margin.top - 4).attr("y2", tlHeight - margin.bottom)
    .attr("stroke", S.ink).attr("stroke-width", 1.5);
  const scrub = (event) => {
    const [px] = d3.pointer(event, tl.node());
    const t = x.invert(px);
    state.i = Math.max(0, Math.min(n - 1, d3.bisector((d) => d).center(times, t)));
    update();
  };
  tl.on("pointerdown", (event) => {
    stop();
    scrub(event);
    tl.node().setPointerCapture(event.pointerId);
    tl.on("pointermove", scrub);
  }).on("pointerup pointercancel", () => tl.on("pointermove", null));
  tl.on("keydown", (event) => {
    const step = event.shiftKey ? 36 : 6;
    if (event.key === "ArrowRight") state.i = Math.min(n - 1, state.i + step);
    else if (event.key === "ArrowLeft") state.i = Math.max(0, state.i - step);
    else if (event.key === " ") return (event.preventDefault(), state.playing ? stop() : start());
    else return;
    event.preventDefault();
    update();
  });

  // --- Playback -------------------------------------------------------------------
  function update() {
    const i = state.i;
    const t = times[i];
    clock.textContent = clockFmt.format(t);
    day.textContent = when.format(t);
    dots.attr("r", (d) => radius(anomaly(d.key, i)))
      .attr("fill", (d) => (anomaly(d.key, i) === null ? S.grid : colour(anomaly(d.key, i))));
    labels.attr("fill", S.ink)
      .text((d) => `${d.name} ${metres(anomaly(d.key, i))}`)
      .attr("x", 9).attr("y", 4);
    for (const b of barrierMarks) {
      const shut = barriers.some((s) => s.name === b.name && +t >= +new Date(s.from) && +t <= +new Date(s.to));
      b.bar.attr("fill", shut ? S.alert : S.muted);
      b.text.attr("fill", shut ? S.alert : S.muted)
        .text(shut ? `${b.name}: shut` : (state.view === "rdam" || !narrow ? b.name : ""));
    }
    const sea = data[i]["hoek-van-holland"];
    const city = data[i].rotterdam;
    const lobith = data[i].lobith;
    const nap = (cm) => (cm === null || cm === undefined || cm === "" ? "–" : metres(cm).replace(" m", " m NAP"));
    readout.innerHTML = `Sea at Hoek van Holland <b style="color:${S.ink}">${nap(sea)}</b> ·
      Rotterdam <b style="color:${S.ink}">${nap(city)}</b> ·
      Rhine at Lobith <b style="color:${S.ink}">${nap(lobith)}</b>`;
    playhead.attr("x1", x(t)).attr("x2", x(t));
    tl.attr("aria-valuetext", `${day.textContent} ${clock.textContent}`);
  }
  function start() {
    if (state.i >= n - 1) state.i = 0;
    state.playing = true;
    play.textContent = "❚❚ Pause";
    clearInterval(state.timer);
    state.timer = setInterval(() => {
      if (!el.isConnected) return stop();
      state.i += 1;
      if (state.i >= n - 1) {
        state.i = n - 1;
        stop();
      }
      update();
    }, SPEEDS[state.speed].ms);
  }
  function stop() {
    state.playing = false;
    play.textContent = "▶ Play";
    clearInterval(state.timer);
    state.timer = null;
  }
  play.addEventListener("click", () => (state.playing ? stop() : start()));
  speed.addEventListener("click", () => {
    state.speed = (state.speed + 1) % SPEEDS.length;
    speed.textContent = SPEEDS[state.speed].label;
    if (state.playing) start();
  });
  viewNl.addEventListener("click", () => setView("nl"));
  viewRdam.addEventListener("click", () => setView("rdam"));

  root.append(controls, jumps, head, svg.node(), legend, tl.node());
  setView(state.view, false);
  update();
  if (state.playing) start();

  // The numbers behind the dots: each gauge's normal level and its extremes.
  const rows = stations.map((s) => ({ ...s, rise: s.high - s.normal }))
    .sort((a, b) => b.rise - a.rise);
  return [root, table(rows, [
    { key: "name", label: "Gauge" },
    { key: "normal", label: "Normal (cm NAP)" },
    { key: "low", label: "Lowest (cm NAP)" },
    { key: "high", label: "Highest (cm NAP)" },
    { key: "rise", label: "Highest above normal (cm)" },
  ])];
}
