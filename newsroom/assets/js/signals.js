// Chart runtime for Unexpected Signals.
//
// A story places a chart with the `chart` shortcode, which becomes
//   <div class="chart" data-chart="charts/bars.js" data-data="data/x.csv">
// This file finds those divs, loads the chart module and its CSV, and calls the
// module's default export with everything it needs:
//
//   export default function draw({ data, width, d3, Plot, theme, tooltip, table }) {
//     return svgNode; // or any DOM node, e.g. what Plot.plot() returns
//   }
//
// Charts redraw when their width changes or the reader switches light/dark,
// so a chart never has to handle resizing or theme changes itself.

const d3 = window.d3;
const Plot = window.Plot;

// --- Theme ------------------------------------------------------------------

const TOKENS = ["paper", "paper-2", "ink", "ink-2", "muted", "rule", "grid", "signal", "context",
  "cat-1", "cat-2", "cat-3"];

export function theme() {
  const style = getComputedStyle(document.documentElement);
  const t = Object.fromEntries(TOKENS.map((k) => [k.replace(/-(\w)/g, (_, c) => c.toUpperCase()),
    style.getPropertyValue(`--${k}`).trim()]));
  t.categorical = [t.cat1, t.cat2, t.cat3];
  t.font = getComputedStyle(document.body).getPropertyValue("--sans").trim() || "sans-serif";
  // Defaults for Observable Plot, so Plot charts match the D3 ones.
  t.plot = {
    style: { background: "transparent", color: t.muted, fontFamily: t.font, fontSize: "12px",
      overflow: "visible" },
    marginTop: 24,
  };
  return t;
}

function currentTheme() {
  const explicit = document.documentElement.dataset.theme;
  if (explicit) return explicit;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function setupToggle() {
  const button = document.querySelector(".theme-toggle");
  if (!button) return;
  const label = () => {
    button.textContent = currentTheme() === "dark" ? "Day edition" : "Night edition";
  };
  label();
  button.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("us-theme", next);
    } catch {
      // Storage can be blocked; the toggle still works for this page.
    }
    label();
    redrawAll();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    label();
    redrawAll();
  });
}

// --- Tooltip and table helpers -----------------------------------------------

function makeTooltip(el) {
  let tip = el.querySelector(":scope > .tooltip");
  if (!tip) {
    tip = document.createElement("div");
    tip.className = "tooltip";
    tip.setAttribute("role", "status");
    el.append(tip);
  }
  return {
    node: tip,
    // html is trusted markup built by the chart; escape data with tooltip.esc().
    show(event, html) {
      tip.innerHTML = html;
      tip.classList.add("on");
      const box = el.getBoundingClientRect();
      const x = event.clientX - box.left;
      const y = event.clientY - box.top;
      const w = tip.offsetWidth;
      const left = x + 14 + w > box.width ? x - 14 - w : x + 14;
      tip.style.left = `${Math.max(0, left)}px`;
      tip.style.top = `${Math.max(0, y - tip.offsetHeight - 8)}px`;
    },
    hide() {
      tip.classList.remove("on");
    },
    esc,
  };
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

// A collapsed table of the chart's numbers, so a chart is never colour-only
// or mouse-only. columns: [{ key, label, format? }]
function makeTable(rows, columns) {
  const details = document.createElement("details");
  details.className = "chart-table";
  const head = columns.map((c) => `<th>${esc(c.label)}</th>`).join("");
  const body = rows.map((r) => `<tr>${columns.map((c) =>
    `<td>${esc(c.format ? c.format(r[c.key]) : r[c.key])}</td>`).join("")}</tr>`).join("");
  details.innerHTML = `<summary>Show the numbers</summary>
    <table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  return details;
}

// --- Loading and drawing -------------------------------------------------------

const charts = new Map();

async function setup(el) {
  const src = new URL(el.dataset.chart, location.href).href;
  try {
    const [module, data] = await Promise.all([
      import(src),
      el.dataset.data ? d3.csv(new URL(el.dataset.data, location.href).href, d3.autoType) : null,
    ]);
    charts.set(el, { draw: module.default, data, width: 0 });
    draw(el, true);
    new ResizeObserver(() => draw(el)).observe(el);
  } catch (error) {
    el.innerHTML = `<p class="chart-error">Chart failed to load: ${esc(error.message)}</p>`;
    console.error(error);
  }
}

function draw(el, force = false) {
  const chart = charts.get(el);
  if (!chart) return;
  const width = Math.round(el.clientWidth);
  if (!force && width === chart.width) return;
  chart.width = width;
  const tooltip = makeTooltip(el);
  const node = chart.draw({ data: chart.data, width, d3, Plot, theme: theme(), tooltip,
    table: makeTable, el });
  el.replaceChildren(...[node].flat().filter(Boolean), tooltip.node);
}

function redrawAll() {
  for (const el of charts.keys()) draw(el, true);
  setDatawrapperTheme();
}

// --- Datawrapper ---------------------------------------------------------------

// Datawrapper's own embed snippet: charts post their height so the iframe fits.
window.addEventListener("message", (event) => {
  const heights = event.data && event.data["datawrapper-height"];
  if (!heights) return;
  for (const id of Object.keys(heights)) {
    const frame = document.getElementById(`datawrapper-chart-${id}`);
    if (frame && frame.contentWindow === event.source) frame.style.height = `${heights[id]}px`;
  }
});

function setDatawrapperTheme() {
  const dark = document.documentElement.dataset.theme;
  for (const frame of document.querySelectorAll("iframe.datawrapper")) {
    const url = new URL(frame.src);
    const wanted = dark ? String(dark === "dark") : "auto";
    if (url.searchParams.get("dark") !== wanted) {
      url.searchParams.set("dark", wanted);
      frame.src = url.href;
    }
  }
}

setupToggle();
setDatawrapperTheme();
document.querySelectorAll(".chart[data-chart]").forEach(setup);
