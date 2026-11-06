"use strict";

const $ = (id) => document.getElementById(id);
const select = $("index");
const runBtn = $("load");
const exportBtn = $("export");
const scanExport = $("scan-export");
const scanStatus = $("scan-status");
const progressWrap = $("progress-wrap");
const progressBar = $("progress-bar");
const scanTable = $("scan-results");
const scanBody = scanTable.querySelector("tbody");
const constTable = $("results");
const constBody = constTable.querySelector("tbody");
const filterEl = $("filter");

// Relative URLs so this also works behind the Colab proxy.
const COLS = [
  { key: "Date", label: "Scan date", type: "text" },
  { key: "Ticker", label: "Ticker", type: "text", cls: "ticker" },
  { key: "Stock", label: "Stock", type: "text", cls: "muted-cell" },
  { key: "CMP", label: "CMP", type: "num", cls: "strong" },
  { key: "52W High", label: "52W High", type: "num" },
  { key: "52W High Date", label: "52W High Date", type: "date" },
  { key: "30 DMA", label: "30 DMA", type: "num" },
  { key: "50 DMA", label: "50 DMA", type: "num" },
  { key: "200 DMA", label: "200 DMA", type: "num" },
  { key: "200 DMA Dist %", label: "200 DMA Dist %", type: "pct" },
  { key: "CAR Status", label: "CAR", type: "badge" },
  { key: "Action", label: "Action", type: "badge" },
];

let rows = [];
let sortKey = "200 DMA Dist %";
let sortDesc = false;
let scanToken = 0;
let scanJobId = null;
let constLoaded = false;

/* ---------- helpers ---------- */
function setStatus(text, isError) {
  scanStatus.textContent = text;
  scanStatus.className = "status" + (isError ? " error" : "");
}

function setProgress(done, total) {
  progressWrap.hidden = false;
  const pct = total ? Math.round((done / total) * 100) : 0;
  progressBar.style.width = pct + "%";
}

// dd-mm-yyyy -> sortable number
function dateVal(s) {
  const [d, m, y] = String(s).split("-").map(Number);
  return y * 10000 + m * 100 + d;
}

function sortVal(row, col) {
  const v = row[col.key];
  if (col.type === "date") return dateVal(v);
  if (col.type === "num" || col.type === "pct") return Number(v);
  return String(v).toLowerCase();
}

const fmt = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function cell(row, col) {
  const td = document.createElement("td");
  const v = row[col.key];
  if (col.type === "num") {
    td.textContent = fmt.format(v);
    td.className = "num";
  } else if (col.type === "pct") {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = fmt.format(v) + "%";
    td.className = "num";
    td.appendChild(pill);
  } else if (col.type === "badge") {
    const b = document.createElement("span");
    b.className = "badge";
    b.textContent = String(v);
    td.appendChild(b);
  } else {
    td.textContent = String(v);
  }
  if (col.cls) td.classList.add(col.cls);
  return td;
}

/* ---------- breakout table ---------- */
const headRow = scanTable.querySelector("thead tr");
for (const col of COLS) {
  const th = document.createElement("th");
  th.textContent = col.label;
  th.className = "sortable" + (col.type === "num" || col.type === "pct" ? " num" : "");
  th.dataset.key = col.key;
  th.addEventListener("click", () => {
    if (sortKey === col.key) sortDesc = !sortDesc;
    else { sortKey = col.key; sortDesc = col.type !== "text"; }
    renderRows();
  });
  headRow.appendChild(th);
}

function renderRows() {
  const q = filterEl.value.trim().toLowerCase();
  const col = COLS.find((c) => c.key === sortKey);
  const shown = rows
    .filter((r) => !q || r.Ticker.toLowerCase().includes(q) || r.Stock.toLowerCase().includes(q))
    .sort((a, b) => {
      const x = sortVal(a, col), y = sortVal(b, col);
      const c = x < y ? -1 : x > y ? 1 : 0;
      return sortDesc ? -c : c;
    });

  headRow.querySelectorAll("th").forEach((th) => {
    const on = th.dataset.key === sortKey;
    th.classList.toggle("sorted", on);
    th.classList.toggle("desc", on && sortDesc);
  });

  scanBody.replaceChildren(...shown.map((r) => {
    const tr = document.createElement("tr");
    COLS.forEach((c) => tr.appendChild(cell(r, c)));
    return tr;
  }));
  scanTable.hidden = shown.length === 0;
  $("empty").hidden = rows.length !== 0 || scanJobId === null;
  $("row-count").textContent = rows.length ? shown.length + " of " + rows.length + " shown" : "";
}

function updateKpis(data) {
  $("kpis").hidden = false;
  $("kpi-total").textContent = data.total;
  $("kpi-hits").textContent = data.count;
  $("kpi-rate").textContent = data.total ? ((data.count / data.total) * 100).toFixed(1) + "%" : "0%";
  const avg = data.rows.length
    ? data.rows.reduce((s, r) => s + Number(r["200 DMA Dist %"]), 0) / data.rows.length
    : null;
  $("kpi-dist").textContent = avg === null ? "\u2013" : avg.toFixed(2) + "%";
}

/* ---------- constituents ---------- */
async function loadConstituents() {
  exportBtn.disabled = true;
  constTable.hidden = true;
  $("const-status").textContent = "Loading...";
  try {
    const res = await fetch("api/constituents?index=" + encodeURIComponent(select.value));
    const data = await res.json();
    if (!res.ok) { $("const-status").textContent = data.error || "Request failed."; return; }
    constBody.replaceChildren(...data.tickers.map((t, i) => {
      const tr = document.createElement("tr");
      const n = document.createElement("td");
      n.textContent = String(i + 1);
      n.className = "muted-cell";
      const tk = document.createElement("td");
      tk.textContent = t;
      tk.className = "ticker";
      tr.append(n, tk);
      return tr;
    }));
    constTable.hidden = false;
    exportBtn.disabled = false;
    constLoaded = true;
    $("const-status").textContent = data.count + " constituents in " + data.index;
  } catch (e) {
    $("const-status").textContent = "Request failed.";
  }
}

/* ---------- background scan ---------- */
async function startScan() {
  const token = ++scanToken;
  scanJobId = null;
  rows = [];
  scanExport.disabled = true;
  runBtn.disabled = true;
  $("kpis").hidden = true;
  $("empty").hidden = true;
  scanTable.hidden = true;
  setProgress(0, 1);
  setStatus("Starting scan...");
  try {
    let res = await fetch("api/scan?index=" + encodeURIComponent(select.value), { method: "POST" });
    let data = await res.json();
    while (token === scanToken) {
      if (!res.ok) { progressWrap.hidden = true; setStatus(data.error || "Scan failed.", true); return; }
      if (data.state === "done") {
        progressWrap.hidden = true;
        scanJobId = data.job_id;
        rows = data.rows;
        updateKpis(data);
        renderRows();
        scanExport.disabled = rows.length === 0;
        setStatus("Scan complete: " + data.count + " positive breakouts in " + data.index + ".");
        return;
      }
      if (data.state === "error") { progressWrap.hidden = true; setStatus("Scan failed.", true); return; }
      setProgress(data.done, data.total);
      setStatus("Scanning " + data.done + " / " + (data.total || "?") + " stocks in " + data.index + "...");
      await new Promise((r) => setTimeout(r, 2000));
      if (token !== scanToken) return;
      res = await fetch("api/scan/" + encodeURIComponent(data.job_id));
      data = await res.json();
    }
  } catch (e) {
    if (token === scanToken) { progressWrap.hidden = true; setStatus("Scan failed.", true); }
  } finally {
    if (token === scanToken) runBtn.disabled = false;
  }
}

function runAll() {
  constLoaded = false;
  startScan();
  loadConstituents();
}

/* ---------- wiring ---------- */
async function loadIndices() {
  try {
    const res = await fetch("api/indices");
    const data = await res.json();
    select.replaceChildren(...data.indices.map((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      return opt;
    }));
  } catch (e) {
    setStatus("Could not load index list.", true);
  }
}

function showTab(which) {
  const scan = which === "scan";
  $("panel-scan").hidden = !scan;
  $("panel-const").hidden = scan;
  $("tab-scan").classList.toggle("active", scan);
  $("tab-const").classList.toggle("active", !scan);
  $("tab-scan").setAttribute("aria-selected", String(scan));
  $("tab-const").setAttribute("aria-selected", String(!scan));
  if (!scan && !constLoaded) loadConstituents();
}

$("tab-scan").addEventListener("click", () => showTab("scan"));
$("tab-const").addEventListener("click", () => showTab("const"));
runBtn.addEventListener("click", runAll);
select.addEventListener("change", runAll);
filterEl.addEventListener("input", renderRows);
exportBtn.addEventListener("click", () => {
  window.location.href = "api/export?index=" + encodeURIComponent(select.value);
});
scanExport.addEventListener("click", () => {
  if (scanJobId) window.location.href = "api/scan/" + encodeURIComponent(scanJobId) + "/export";
});

// Theme: saved choice, else OS preference.
const root = document.documentElement;
const saved = localStorage.getItem("theme");
root.dataset.theme = saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
$("theme").addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", root.dataset.theme);
});

loadIndices();
