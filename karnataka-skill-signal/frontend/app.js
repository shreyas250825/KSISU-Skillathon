/**
 * app.js — Karnataka Skill Signal
 *
 * DATA STRATEGY:
 *   1. If window.KSS_DATA is defined (data_bundle.js loaded), use it — works fully offline.
 *   2. Otherwise, try to fetch from the FastAPI backend at window.KSS_API_BASE.
 *
 * This means the site works as a plain static file (just open index.html) AND
 * also works with a live backend when one is running.
 */

// ── Config ──────────────────────────────────────────────────────────────────
const API_BASE = window.KSS_API_BASE || "http://localhost:8000";

// ── Data access (embedded or API) ────────────────────────────────────────────
const EMBEDDED = window.KSS_DATA || null;

async function getData(key, endpoint, params = "") {
  // Prefer embedded bundle
  if (EMBEDDED && EMBEDDED[key]) return EMBEDDED[key];
  // Fallback to live API
  return apiFetch(endpoint + params);
}

async function apiFetch(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Palette ──────────────────────────────────────────────────────────────────
const PALETTE = {
  greenDeep:  "#2d4a2d",
  greenMid:   "#4a6b3a",
  greenSage:  "#7a9b6a",
  greenLight: "#c8dab8",
  greenPale:  "#e8f0e0",
  terra:      "#9b4a2a",
  terraLight: "#f0d8cc",
  olive:      "#7a7a3a",
  gold:       "#c8a84a",
  stone:      "#a09080",
  blue:       "#5a7a9a",
};

const CHART_COLORS = [
  PALETTE.greenMid, PALETTE.terra, PALETTE.greenSage,
  PALETTE.gold, PALETTE.blue, PALETTE.olive, PALETTE.stone,
];

Chart.defaults.font.family = "'Inter', 'DM Sans', system-ui, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = "#5a5550";

// ── Utility helpers ──────────────────────────────────────────────────────────
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

function fmt(n, decimals = 0) {
  if (n == null) return "—";
  if (typeof n === "string") return n;
  return Number(n).toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtPct(n) {
  if (n == null) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${Number(n).toFixed(1)}%`;
}

function arrow(n) {
  if (n == null) return "";
  return n > 0 ? "▲" : n < 0 ? "▼" : "=";
}

function showError(el, msg) {
  el.innerHTML = `
    <div class="error-state">
      <div class="error-state__title">Data unavailable</div>
      <div class="error-state__desc">${msg}</div>
    </div>`;
}

function showLoading(el) {
  el.innerHTML = `
    <div style="display:flex;gap:8px;flex-direction:column;padding:16px;">
      <div class="skeleton" style="height:20px;width:60%;"></div>
      <div class="skeleton" style="height:200px;"></div>
    </div>`;
}

// ── Chart registry ────────────────────────────────────────────────────────────
const charts = {};
function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

// ── Sortable tables ───────────────────────────────────────────────────────────
function makeSortable(table) {
  if (!table) return;
  const headers = $$("th", table);
  headers.forEach((th, i) => {
    let dir = 1;
    th.style.cursor = "pointer";
    th.addEventListener("click", () => {
      headers.forEach(h => h.classList.remove("sorted-asc", "sorted-desc"));
      th.classList.add(dir > 0 ? "sorted-asc" : "sorted-desc");
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));
      rows.sort((a, b) => {
        const av = a.cells[i]?.textContent.replace(/[,₹%↑↓▲▼+\s]/g, "").trim();
        const bv = b.cells[i]?.textContent.replace(/[,₹%↑↓▲▼+\s]/g, "").trim();
        const an = parseFloat(av), bn = parseFloat(bv);
        if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir;
        return (av || "").localeCompare(bv || "") * dir;
      });
      rows.forEach(r => tbody.appendChild(r));
      dir *= -1;
    });
  });
}

// ── CSV export (API or data-URI fallback) ────────────────────────────────────
function downloadCSV(apiPath, filename, fallbackRows) {
  if (!EMBEDDED) {
    // Try live API
    const a = document.createElement("a");
    a.href = `${API_BASE}${apiPath}`;
    a.download = filename;
    a.click();
    return;
  }
  // Build CSV from embedded data
  if (!fallbackRows || !fallbackRows.length) return;
  const keys = Object.keys(fallbackRows[0]);
  const lines = [keys.join(",")];
  fallbackRows.forEach(row => {
    lines.push(keys.map(k => JSON.stringify(row[k] ?? "")).join(","));
  });
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Nav active state ──────────────────────────────────────────────────────────
function initNavScroll() {
  const sections = $$("section[id]");
  const links    = $$(".nav__links a");
  const obs = new IntersectionObserver(
    entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          links.forEach(l => l.classList.remove("active"));
          const link = links.find(l => l.getAttribute("href") === `#${e.target.id}`);
          if (link) link.classList.add("active");
        }
      });
    },
    { rootMargin: "-40% 0px -55% 0px" }
  );
  sections.forEach(s => obs.observe(s));
}

function initMobileNav() {
  const toggle = $(".nav__toggle");
  const links  = $(".nav__links");
  if (!toggle) return;
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open);
  });
  $$(".nav__links a").forEach(a =>
    a.addEventListener("click", () => links.classList.remove("open"))
  );
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function initTabs(containerSel) {
  const container = $(containerSel);
  if (!container) return;
  const tabs   = $$(".tab",   container);
  const panels = $$(".tab-panel", container);
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => { t.classList.remove("active"); t.setAttribute("aria-selected","false"); });
      panels.forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      tab.setAttribute("aria-selected","true");
      const target = $(`#${tab.dataset.panel}`, container);
      if (target) target.classList.add("active");
    });
  });
}

// ── Hero mini chart ───────────────────────────────────────────────────────────
function renderHeroChart(data) {
  const canvas = $("#hero-mini-canvas");
  if (!canvas || !data.available) return;
  const yrs  = data.years || ["2018-19","2019-20","2020-21","2021-22"];
  const tots = yrs.map(y => data.annual_totals?.[y] ?? 0);
  const lfl  = yrs.map(y => data.lfl_annual?.[y] ?? null);
  destroyChart("hero");
  charts["hero"] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: yrs,
      datasets: [
        { label: "All centres", data: tots, backgroundColor: PALETTE.greenMid+"cc",
          borderColor: PALETTE.greenMid, borderWidth:1, borderRadius:4 },
        { label: "Like-for-like", data: lfl, type: "line", tension: 0.3,
          borderColor: PALETTE.terra, backgroundColor: "transparent",
          pointBackgroundColor: PALETTE.terra, pointRadius: 4,
          borderWidth: 2, fill: false },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { mode:"index", intersect:false } },
      scales: {
        x: { grid: { display:false }, ticks: { font:{ size:10 } } },
        y: { grid: { color:"#ebe8e1" }, ticks: { font:{ size:10 } } },
      },
    },
  });
}

// ── Hero stats ────────────────────────────────────────────────────────────────
function renderHeroStats(ov) {
  const el = $("#hero-facts");
  if (!el) return;
  el.innerHTML = `
    <div>
      <span class="hero__fact-value">${ov.datasets_loaded}/${ov.datasets_total}</span>
      <span class="hero__fact-label">Datasets loaded</span>
    </div>
    <div>
      <span class="hero__fact-value">${ov.indicators_computed}</span>
      <span class="hero__fact-label">Indicators computed</span>
    </div>
    <div>
      <span class="hero__fact-value">2011–22</span>
      <span class="hero__fact-label">Reporting periods</span>
    </div>`;
}

// ── Overview cards ────────────────────────────────────────────────────────────
function renderOverviewCards(ov) {
  const el = $("#overview-cards");
  if (!el) return;
  const cards = [
    {
      tag:"Training Activity",
      num: ov.gttc_grand_total ? fmt(ov.gttc_grand_total) : "—",
      title:"GTTC CoE Short-term Reported Counts",
      desc:"Cumulative reported counts across 10 CoE centres and 3 CoE partners, FY 2018–19 to 2021–22.",
      period:ov.gttc_years,
      tells:"Shows what the training system reports.",
      cannot:"Not employer demand, completion or placement.",
    },
    {
      tag:"Historical Workforce",
      num: ov.census_total_persons ? fmt(ov.census_total_persons) : "—",
      title:"Marginal Workers in Karnataka",
      desc:"Census 2011 profile by industry, age, gender, and rural/urban classification across 30 districts.",
      period:ov.census_year,
      tells:"Shows who worked marginally in 2011.",
      cannot:"Not today's labour demand.",
    },
    {
      tag:"Economic Signal",
      num: ov.slswcc_employment ? fmt(ov.slswcc_employment) : "—",
      title:"Listed Employment from Approved Projects",
      desc:`${ov.slswcc_units||"307"} units approved through the Single Window Committee, FY 2020–21.`,
      period:ov.slswcc_year,
      tells:"Shows approved investment plans.",
      cannot:"Not vacancies or realised jobs.",
    },
  ];
  el.innerHTML = cards.map(c => `
    <div class="card">
      <div class="card__tag">${c.tag}</div>
      <div class="card__number card__number--green">${c.num}</div>
      <div class="card__title">${c.title}</div>
      <div class="card__desc">${c.desc}</div>
      <div class="card__meta">${c.period}</div>
      <div class="card__tells mt-md">
        <strong>Tells us:</strong> ${c.tells}<br>
        <span class="card__tells--cannot"><strong>Cannot tell us:</strong> ${c.cannot}</span>
      </div>
      <div class="mt-md"><a href="#dashboard" class="btn btn--secondary btn--sm">View analysis →</a></div>
    </div>`).join("");
}

// ── GTTC Trends ───────────────────────────────────────────────────────────────
function renderGTTCTrends(panel, data) {
  const canvasEl = $("#gttc-trend-chart", panel);
  const tableEl  = $("#gttc-trend-table", panel);
  if (!canvasEl || !data.available) {
    if (canvasEl) showError(canvasEl.parentElement, "GTTC courses file not available.");
    return;
  }
  const yrs  = ["2018-19","2019-20","2020-21","2021-22"];
  const tots = data.trend_series.filter(s => s.series==="All Centres").map(s=>s.count);
  const lfl  = data.trend_series.filter(s => s.series.includes("Like")).map(s=>s.count);

  destroyChart("gttc-trend");
  charts["gttc-trend"] = new Chart(canvasEl, {
    type:"bar",
    data:{
      labels:yrs,
      datasets:[
        { label:"All reporting centres", data:tots, backgroundColor:PALETTE.greenMid+"cc",
          borderColor:PALETTE.greenMid, borderWidth:1, borderRadius:5 },
        { label:"Like-for-like (3 centres — Mysuru / Dandeli / Kalaburgi)", data:lfl,
          type:"line", tension:0.35, borderColor:PALETTE.terra, backgroundColor:"transparent",
          pointBackgroundColor:PALETTE.terra, pointRadius:5, borderWidth:2 },
      ],
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{position:"bottom",labels:{boxWidth:12,padding:14}}, tooltip:{mode:"index",intersect:false} },
      scales:{
        x:{ grid:{display:false} },
        y:{ grid:{color:"#ebe8e1"}, beginAtZero:true,
            title:{display:true,text:"Reported count (unit not defined)"} },
      },
    },
  });

  if (tableEl) {
    const rows = data.yoy_table.map(r => `
      <tr>
        <td>${r.year}</td>
        <td class="num">${fmt(r.count)}</td>
        <td class="num">${r.yoy_pct!=null
          ? `<span class="stat-badge ${r.yoy_pct>=0?"stat-badge--up":"stat-badge--down"}">${arrow(r.yoy_pct)} ${Math.abs(r.yoy_pct).toFixed(1)}%</span>`
          : "—"}</td>
        <td class="num">${r.n_reporting}</td>
        <td class="num">${r.lfl_count!=null ? fmt(r.lfl_count) : "—"}</td>
        <td class="num">${r.lfl_yoy_pct!=null
          ? `<span class="stat-badge ${r.lfl_yoy_pct>=0?"stat-badge--up":"stat-badge--down"}">${arrow(r.lfl_yoy_pct)} ${Math.abs(r.lfl_yoy_pct).toFixed(1)}%</span>`
          : "—"}</td>
      </tr>`).join("");
    tableEl.innerHTML = `
      <div class="data-table-wrap">
        <table class="data-table" id="t-gttc-trend">
          <thead><tr><th>Year</th><th>All Centres Count</th><th>YoY Change</th>
            <th>Centres Reporting</th><th>LFL Count</th><th>LFL YoY Change</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="callout callout--warning mt-md">
        <strong>Note:</strong> The count unit in this file is not defined in a data dictionary.
        Values labelled as "reported counts." The like-for-like series tracks only the 3 centres
        (${(data.lfl_centres||[]).join(", ")}) that reported in every year.
      </div>`;
    makeSortable($("#t-gttc-trend"));
  }
}

// ── GTTC Centres ──────────────────────────────────────────────────────────────
function renderGTTCCentres(panel, data) {
  const canvasEl  = $("#gttc-centres-chart", panel);
  const partnerEl = $("#gttc-partner-chart", panel);
  const tableEl   = $("#gttc-centres-table", panel);
  if (!canvasEl || !data.available) {
    if (canvasEl) showError(canvasEl.parentElement, "GTTC centres file not available.");
    return;
  }

  const sorted = [...data.centres].sort((a,b)=>(a.total||0)-(b.total||0));
  const colours = sorted.map(c =>
    c.coe?.includes("Siemens") ? PALETTE.greenMid :
    c.coe?.includes("Dassault") ? PALETTE.greenSage : PALETTE.stone
  );

  destroyChart("gttc-centres");
  charts["gttc-centres"] = new Chart(canvasEl, {
    type:"bar",
    data:{
      labels:sorted.map(c=>c.centre),
      datasets:[{ label:"Cumulative 2018–22", data:sorted.map(c=>c.total||0),
        backgroundColor:colours.map(c=>c+"bb"), borderColor:colours, borderWidth:1, borderRadius:3 }],
    },
    options:{
      indexAxis:"y", responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{
        label:ctx=>{ const c=data.centres.find(x=>x.centre===ctx.label); return ` ${fmt(ctx.raw)} (${c?.coe||"—"})`; }
      }}},
      scales:{
        x:{ grid:{color:"#ebe8e1"}, beginAtZero:true, title:{display:true,text:"Cumulative reported count"} },
        y:{ grid:{display:false} },
      },
    },
  });

  if (partnerEl) {
    const partners = data.partner_breakdown;
    destroyChart("gttc-partner");
    charts["gttc-partner"] = new Chart(partnerEl, {
      type:"doughnut",
      data:{
        labels:partners.map(p=>p.partner),
        datasets:[{ data:partners.map(p=>p.total),
          backgroundColor:[PALETTE.greenMid,PALETTE.greenSage,PALETTE.stone],
          borderColor:"white", borderWidth:3 }],
      },
      options:{
        responsive:true, maintainAspectRatio:false, cutout:"60%",
        plugins:{
          legend:{position:"bottom",labels:{boxWidth:10,padding:14}},
          tooltip:{callbacks:{label:ctx=>{
            const tot = ctx.dataset.data.reduce((a,b)=>a+b,0);
            return ` ${ctx.label}: ${fmt(ctx.raw)} (${tot>0?((ctx.raw/tot)*100).toFixed(1):0}%)`;
          }}},
        },
      },
    });
  }

  if (tableEl) {
    const yrs = data.years;
    const hdr = yrs.map(y=>`<th>${y}</th>`).join("");
    const rows = data.concentration.map(c => {
      const cent = data.centres.find(x=>x.centre===c.centre)||{};
      const yrCells = yrs.map(y=>`<td class="num">${cent[y]!=null?fmt(cent[y]):"—"}</td>`).join("");
      return `<tr>
        <td>${c.centre}</td><td>${cent.coe||"—"}</td>
        <td class="num">${fmt(c.total)}</td>
        <td class="num">${c.share_pct.toFixed(1)}%</td>
        <td class="num">${c.cumulative_pct.toFixed(1)}%</td>
        ${yrCells}
      </tr>`;
    }).join("");
    tableEl.innerHTML = `
      <div class="data-table-wrap">
        <table class="data-table" id="t-gttc-centres">
          <thead><tr><th>Centre</th><th>CoE Partner</th><th>Total</th><th>Share %</th><th>Cumul. %</th>${hdr}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
    makeSortable($("#t-gttc-centres"));
  }
}

// ── GTTC Coverage ─────────────────────────────────────────────────────────────
function renderGTTCCoverage(panel, data) {
  const el = $("#gttc-coverage-content", panel);
  if (!el) return;

  const cov  = data.coverage || {};
  const rbyY = data.reporting_by_year || [];
  const heatmap = rbyY.map(r=>`
    <div style="text-align:center;">
      <div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:4px;">${r.year}</div>
      <div style="font-size:1.3rem;font-weight:800;color:var(--green-deep);">${r.reporting_centres}</div>
      <div style="font-size:0.68rem;color:var(--text-muted);">of ${r.total_centres}</div>
    </div>`).join("");

  const progs = (data.all_programmes||[]).filter(p=>
    !["MANUFACTRING","NO OF GTTC"].some(k=>p.programme.includes(k))
  );
  const years = ["2019","2020","2021"];
  const progRows = progs.map(p=>{
    const cells = years.map(y=>{
      const v = p[`passed_${y}`];
      if (v==null||v==="NA"||v==="") return `<td class="num">—</td>`;
      if (typeof v==="string"&&isNaN(Number(v))) return `<td class="num" style="color:var(--terra);">${v}</td>`;
      return `<td class="num">${fmt(v)}</td>`;
    }).join("");
    return `<tr><td>${p.programme}</td>${cells}</tr>`;
  }).join("");

  const orderRows = (data.all_programmes||[])
    .filter(p=>p.programme.includes("MANUFACTRING"))
    .map(p=>`<tr><td>Manufacturing Service Order Value</td>${years.map(y=>{
      const v=p[`order_value_${y}`];
      return `<td class="num">${v!=null?`₹${v} lakh`:"—"}</td>`;
    }).join("")}</tr>`)
    .join("");

  el.innerHTML = `
    <div class="chart-wrap">
      <div class="chart-wrap__header">
        <div class="chart-wrap__title">Reporting Centre Count by Year (I6: Completeness)</div>
      </div>
      <div style="display:flex;gap:24px;margin-bottom:16px;">${heatmap}</div>
      <div>
        <div style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:8px;">Cell coverage (centre × year):</div>
        <div class="coverage-bar"><div class="coverage-bar__fill" style="width:${cov.pct||0}%"></div></div>
        <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">
          ${cov.filled||0} of ${cov.cells||0} cells filled (${cov.pct||0}%)
        </div>
      </div>
      <div class="callout callout--warning mt-md">
        <strong>Blank ≠ zero.</strong> A blank cell means no data was reported for that centre-year.
        Totals-row reconciliation: <strong>${data.totals_match ? "✓ PASS" : "✗ MISMATCH"}</strong>
      </div>
    </div>
    <div class="chart-wrap mt-md">
      <div class="chart-wrap__title mb-md">GTTC Passed-Out Counts by Programme (Calendar Years)</div>
      <div class="data-table-wrap">
        <table class="data-table" id="t-gttc-prog">
          <thead><tr><th>Programme / Information Type</th><th>2019</th><th>2020</th><th>2021</th></tr></thead>
          <tbody>${progRows}${orderRows}</tbody>
        </table>
      </div>
      <div class="chart-wrap__source">
        Source: GTTC_Number_of_Students_Passed_2019-2021_0.csv · Calendar years 2019–2021 ·
        CoE counts match GTTC short-term file yearly totals — files appear to be one source.
      </div>
    </div>`;
  makeSortable($("#t-gttc-prog"));
}

// ── Census Industry ───────────────────────────────────────────────────────────
function renderCensusIndustry(panel, data) {
  const canvasEl = $("#census-industry-chart", panel);
  const tableEl  = $("#census-industry-table", panel);
  if (!canvasEl || !data.available) {
    if (canvasEl) showError(canvasEl.parentElement, "Census file not available.");
    return;
  }
  const cats = data.categories;
  destroyChart("census-industry");
  charts["census-industry"] = new Chart(canvasEl, {
    type:"bar",
    data:{
      labels:cats.map(c=>c.label),
      datasets:[
        { label:"Persons", data:cats.map(c=>c.persons),
          backgroundColor:cats.map((_,i)=>CHART_COLORS[i%CHART_COLORS.length]+"bb"),
          borderColor:cats.map((_,i)=>CHART_COLORS[i%CHART_COLORS.length]), borderWidth:1, borderRadius:3 },
        { label:"Males", data:cats.map(c=>c.males), backgroundColor:PALETTE.blue+"88",
          borderColor:PALETTE.blue, borderWidth:1, borderRadius:3 },
        { label:"Females", data:cats.map(c=>c.females), backgroundColor:PALETTE.gold+"88",
          borderColor:PALETTE.gold, borderWidth:1, borderRadius:3 },
      ],
    },
    options:{
      indexAxis:"y", responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{position:"bottom",labels:{boxWidth:12,padding:14}}, tooltip:{mode:"index",intersect:false} },
      scales:{
        x:{ grid:{color:"#ebe8e1"}, title:{display:true,text:"Marginal workers (count)"} },
        y:{ grid:{display:false} },
      },
    },
  });
  if (tableEl) {
    const rows = cats.map(c=>`
      <tr><td>${c.code}</td><td>${c.label}</td>
        <td class="num">${fmt(c.persons)}</td><td class="num">${fmt(c.males)}</td>
        <td class="num">${fmt(c.females)}</td><td class="num">${c.share_pct.toFixed(1)}%</td>
      </tr>`).join("");
    tableEl.innerHTML = `
      <div class="data-table-wrap">
        <table class="data-table" id="t-census-ind">
          <thead><tr><th>Code</th><th>Category</th><th>Persons</th><th>Males</th><th>Females</th><th>Share %</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="callout callout--info mt-md">
        <strong>Historical data only.</strong> Census 2011 marginal worker counts.
        Not current employment demand, vacancies or skill requirements.
      </div>`;
    makeSortable($("#t-census-ind"));
  }
}

// ── Census Demographics ───────────────────────────────────────────────────────
function renderCensusDemographics(panel, data) {
  const genderEl = $("#census-gender-chart", panel);
  const distEl   = $("#census-district-chart", panel);
  const ageEl    = $("#census-age-chart", panel);
  if (!genderEl || !data.available) return;

  destroyChart("census-gender");
  charts["census-gender"] = new Chart(genderEl, {
    type:"doughnut",
    data:{
      labels:["Males","Females"],
      datasets:[{ data:[data.total_males,data.total_females],
        backgroundColor:[PALETTE.blue+"cc",PALETTE.gold+"cc"], borderColor:"white", borderWidth:3 }],
    },
    options:{
      responsive:true, maintainAspectRatio:false, cutout:"55%",
      plugins:{
        legend:{position:"bottom"},
        tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.raw)} (${((ctx.raw/data.total_persons)*100).toFixed(1)}%)`}},
      },
    },
  });

  if (distEl) {
    const top10 = (data.districts||[]).slice(0,10);
    destroyChart("census-district");
    charts["census-district"] = new Chart(distEl, {
      type:"bar",
      data:{
        labels:top10.map(d=>d.district),
        datasets:[{ label:"Marginal workers", data:top10.map(d=>d.persons),
          backgroundColor:PALETTE.greenSage+"bb", borderColor:PALETTE.greenSage, borderWidth:1, borderRadius:3 }],
      },
      options:{
        indexAxis:"y", responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{display:false} },
        scales:{
          x:{ grid:{color:"#ebe8e1"}, title:{display:true,text:"Marginal workers (2011)"} },
          y:{ grid:{display:false} },
        },
      },
    });
  }

  if (ageEl) {
    const va = (data.age_breakdown||[]).filter(a=>a.age_group!=="Age not stated");
    destroyChart("census-age");
    charts["census-age"] = new Chart(ageEl, {
      type:"bar",
      data:{
        labels:va.map(a=>a.age_group),
        datasets:[
          { label:"Males", data:va.map(a=>a.males), backgroundColor:PALETTE.blue+"88", borderColor:PALETTE.blue, borderWidth:1 },
          { label:"Females", data:va.map(a=>a.females), backgroundColor:PALETTE.gold+"88", borderColor:PALETTE.gold, borderWidth:1 },
        ],
      },
      options:{
        responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{position:"bottom"}, tooltip:{mode:"index",intersect:false} },
        scales:{
          x:{ grid:{display:false} },
          y:{ grid:{color:"#ebe8e1"}, title:{display:true,text:"Count"} },
        },
      },
    });
  }
}

// ── Industry (SLSWCC) ─────────────────────────────────────────────────────────
function renderIndustry(panel, data) {
  const canvasEl = $("#industry-sector-chart", panel);
  const tableEl  = $("#industry-table", panel);
  if (!canvasEl || !data.available) {
    if (canvasEl) showError(canvasEl.parentElement, data.file ? `Dataset not loaded: ${data.file}` : "SLSWCC file not available.");
    return;
  }
  const top = data.sectors.slice(0,12);
  destroyChart("industry-sector");
  charts["industry-sector"] = new Chart(canvasEl, {
    type:"bar",
    data:{
      labels:top.map(s=>s.SECTOR_CLEAN),
      datasets:[
        { label:"Listed Employment", data:top.map(s=>s.employment), backgroundColor:PALETTE.greenMid+"cc",
          borderColor:PALETTE.greenMid, borderWidth:1, borderRadius:3 },
        { label:"Number of Units", data:top.map(s=>s.units), backgroundColor:PALETTE.terra+"88",
          borderColor:PALETTE.terra, borderWidth:1, borderRadius:3, yAxisID:"y1" },
      ],
    },
    options:{
      indexAxis:"y", responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{position:"bottom",labels:{boxWidth:12,padding:14}}, tooltip:{mode:"index",intersect:false} },
      scales:{
        x:{ grid:{color:"#ebe8e1"}, title:{display:true,text:"Listed employment"} },
        y:{ grid:{display:false} },
        y1:{ position:"right", grid:{display:false}, title:{display:true,text:"Units"} },
      },
    },
  });
  if (tableEl) {
    const rows = data.sectors.map(s=>`
      <tr><td>${s.SECTOR_CLEAN}</td><td class="num">${fmt(s.units)}</td>
        <td class="num">${fmt(s.employment)}</td><td class="num">₹${fmt(s.investment,2)} Cr</td>
      </tr>`).join("");
    tableEl.innerHTML = `
      <div class="data-table-wrap">
        <table class="data-table" id="t-industry">
          <thead><tr><th>Sector</th><th>Units</th><th>Listed Employment</th><th>Investment</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="callout callout--warning mt-md">
        <strong>Important:</strong> ${data.limitation}
      </div>`;
    makeSortable($("#t-industry"));
  }
}

// ── Enrolment ─────────────────────────────────────────────────────────────────
function renderEnrolment(panel, data) {
  const el = $("#enrolment-content", panel);
  if (!el) return;
  const e21 = data.enrolment_2021;
  if (!e21?.available) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon">📂</div>
      <div class="empty-state__title">Dataset not loaded</div>
      <div class="empty-state__desc">TotalEnrollmentbyLevel_2020-21.csv not found.</div>
    </div>`;
    return;
  }
  const districts = (e21.districts||[]).filter(d=>d.class_9_10!=null).slice(0,15);
  el.innerHTML = `
    <div class="callout callout--info mb-md"><strong>Context only.</strong> ${data.note}</div>
    ${e21.corrupted_cells?.length ? `
      <div class="callout callout--warning mb-md">
        <strong>Data quality flag:</strong> ${e21.corrupted_cells.length} corrupted cell(s) found
        ("56972700%" — recoverable as 569,727 for Bengaluru U South).
      </div>` : ""}
    <div class="chart-wrap">
      <div class="chart-wrap__title mb-md">Class 9–10 Enrolment by District (All Management, 2020–21)</div>
      <div style="height:320px;"><canvas id="enrolment-canvas"></canvas></div>
      <div class="chart-wrap__source">Source: TotalEnrollmentbyLevel_2020-21.csv · AY 2020–21</div>
    </div>
    <div class="mt-md" style="font-size:0.85rem;color:var(--text-secondary);">
      <strong>${fmt(e21.n_districts)}</strong> education districts loaded.
      Management types: ${(e21.management_types||[]).join(", ")}.
    </div>`;

  if (districts.length) {
    const canvas = document.getElementById("enrolment-canvas");
    destroyChart("enrolment");
    charts["enrolment"] = new Chart(canvas, {
      type:"bar",
      data:{
        labels:districts.map(d=>d.district.replace(/ -\d+$/,"")),
        datasets:[{ label:"Class 9–10 total enrolment", data:districts.map(d=>d.class_9_10),
          backgroundColor:PALETTE.greenSage+"bb", borderColor:PALETTE.greenSage, borderWidth:1, borderRadius:3 }],
      },
      options:{
        indexAxis:"y", responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{display:false} },
        scales:{
          x:{ grid:{color:"#ebe8e1"}, title:{display:true,text:"Enrolment count"} },
          y:{ grid:{display:false}, ticks:{font:{size:10}} },
        },
      },
    });
  }
}

// ── Quality ───────────────────────────────────────────────────────────────────
function renderQualityReport(data) {
  const el = $("#quality-checks");
  const summaryEl = $("#quality-summary");
  if (!el) return;

  const iconMap = {
    PASS:        { char:"✓", cls:"pass" },
    WARNING:     { char:"!", cls:"warning" },
    FAIL:        { char:"✗", cls:"fail" },
    NOT_CHECKED: { char:"?", cls:"not_checked" },
  };
  const s = data.summary;

  if (summaryEl) {
    summaryEl.innerHTML = `
      <div style="display:flex;gap:16px;flex-wrap:wrap;">
        <div class="stat-badge stat-badge--up">✓ ${s.pass} PASS</div>
        <div class="stat-badge" style="background:var(--gold-pale);color:var(--olive);">⚠ ${s.warning} WARNING</div>
        <div class="stat-badge stat-badge--down">✗ ${s.fail} FAIL</div>
        <div class="stat-badge stat-badge--neutral">? ${s.not_checked} NOT CHECKED</div>
      </div>`;
  }

  el.innerHTML = `<div class="quality-grid">` +
    data.checks.map(c => {
      const ic = iconMap[c.status] || iconMap.NOT_CHECKED;
      return `
        <div class="quality-check">
          <div class="quality-check__icon quality-check__icon--${ic.cls}">${ic.char}</div>
          <div>
            <div class="quality-check__dataset">${c.dataset}</div>
            <div class="quality-check__name">${c.check}</div>
            <div class="quality-check__detail">${c.detail}</div>
          </div>
        </div>`;
    }).join("") + `</div>`;
}

// ── Methodology ───────────────────────────────────────────────────────────────
function renderMethodology(data) {
  const pipelineEl = $("#methodology-pipeline");
  const indEl      = $("#indicator-cards");
  if (!pipelineEl) return;

  const statusMap = { "Implemented":"implemented", "Implemented (partial)":"partial", "Proposed":"proposed" };
  const steps = data.pipeline_stages;
  pipelineEl.innerHTML = steps.map((s,i) => {
    const cls = statusMap[s.status] || "proposed";
    return `
      <div class="pipeline-step pipeline-step--${cls}">
        <div class="pipeline-step__num">${s.stage}</div>
        <div class="pipeline-step__label">${s.name}</div>
      </div>
      ${i < steps.length-1 ? '<div class="arch-arrow">→</div>' : ""}`;
  }).join("");

  if (indEl) {
    const sClsMap = { "Implemented":"implemented","Proposed":"proposed","Not Computable":"not-computable" };
    indEl.innerHTML = data.indicators.map(ind => `
      <div class="indicator-card">
        <div class="indicator-card__id">${ind.id}</div>
        <div class="indicator-card__name">${ind.name}
          <span class="indicator-status indicator-status--${sClsMap[ind.status]||"proposed"}"
                style="margin-left:6px;">${ind.status}</span>
        </div>
        <div class="indicator-card__formula">${ind.formula}</div>
        <div class="indicator-card__row">
          <span class="indicator-card__row-label">Level</span>
          <span class="indicator-card__row-value">${ind.level}</span>
        </div>
        <div class="indicator-card__row">
          <span class="indicator-card__row-label">Informs</span>
          <span class="indicator-card__row-value">${ind.informs}</span>
        </div>
        <div class="indicator-card__row">
          <span class="indicator-card__row-label">Cannot establish</span>
          <span class="indicator-card__row-value" style="color:var(--terra);">${ind.cannot_establish}</span>
        </div>
        <div class="indicator-card__row">
          <span class="indicator-card__row-label">Value</span>
          <span class="indicator-card__row-value" style="font-style:italic;">${ind.prototype_value}</span>
        </div>
      </div>`).join("");
  }
}

// ── District explorer ─────────────────────────────────────────────────────────
function renderDistrictExplorer(censusData, gttcData) {
  const el = $("#district-table");
  if (!el) return;
  const districts = censusData.available ? censusData.districts : [];
  const centres   = gttcData.available   ? gttcData.centres    : [];

  const byDist = {};
  centres.forEach(c => { byDist[c.centre.toLowerCase()] = c.total; });

  const rows = districts.map(d => {
    const dl = d.district.toLowerCase();
    const match = Object.entries(byDist).find(([k]) => dl.includes(k) || k.includes(dl));
    const gttcVal = match ? match[1] : null;
    return `
      <tr>
        <td>${d.district}</td>
        <td class="num">${fmt(d.persons)}</td>
        <td>Census 2011 (30-dist. boundary)</td>
        <td>${gttcVal!=null ? fmt(gttcVal)+" (cumul. 2018–22)" : "—"}</td>
        <td><span class="stat-badge stat-badge--neutral">2011</span></td>
      </tr>`;
  }).join("");

  el.innerHTML = `
    <div class="callout callout--warning mb-md">
      <strong>Linkage limitation:</strong> District names and boundaries changed between Census 2011 and later datasets.
      GTTC centres use city names, not district codes. Matches here are approximate and for illustration only.
      A versioned district-code crosswalk is required for reliable multi-source joins.
    </div>
    <div class="data-table-wrap">
      <table class="data-table" id="t-district">
        <thead><tr>
          <th>District / Area</th><th>Census 2011 Marginal Workers</th>
          <th>Source</th><th>GTTC CoE Activity (approx.)</th><th>Latest Period</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  makeSortable($("#t-district"));
}

// ── Main init ─────────────────────────────────────────────────────────────────
async function init() {
  initNavScroll();
  initMobileNav();
  initTabs("#dashboard-tabs");

  // ── Load all data (embedded or API) ────────────────────────────────────────
  let overview, gttcTrends, gttcCentres, gttcCoverage,
      censusInd, censusDem, enrolment, industry, quality, methodology;

  try {
    [overview, gttcTrends, gttcCentres, gttcCoverage,
     censusInd, censusDem, enrolment, industry, quality, methodology] = await Promise.all([
      getData("overview",            "/api/overview"),
      getData("gttc_trends",         "/api/gttc/trends"),
      getData("gttc_centres",        "/api/gttc/centres"),
      getData("gttc_coverage",       "/api/gttc/coverage"),
      getData("census_industry",     "/api/census/industry"),
      getData("census_demographics", "/api/census/demographics"),
      getData("enrolment",           "/api/enrolment/overview"),
      getData("industry",            "/api/industry/overview"),
      getData("quality",             "/api/quality/report"),
      getData("methodology",         "/api/methodology"),
    ]);
  } catch (e) {
    console.error("Failed to load data:", e);
    document.body.insertAdjacentHTML("afterbegin",
      `<div class="callout callout--error" style="position:fixed;top:70px;left:50%;transform:translateX(-50%);z-index:999;max-width:500px;padding:12px 20px;">
        <strong>Could not load data.</strong> Start the backend server or check that data_bundle.js is included.
      </div>`);
    return;
  }

  // ── Render immediately available sections ──────────────────────────────────
  renderHeroStats(overview);
  renderOverviewCards(overview);
  renderHeroChart(gttcTrends);

  // ── Lazy-render dashboard tabs on first activation ─────────────────────────
  const panelRenderers = {
    "tab-gttc-trends":   () => renderGTTCTrends(   $("#tab-gttc-trends"),   gttcTrends),
    "tab-gttc-centres":  () => renderGTTCCentres(  $("#tab-gttc-centres"),  gttcCentres),
    "tab-gttc-coverage": () => renderGTTCCoverage( $("#tab-gttc-coverage"), gttcCoverage),
    "tab-census-ind":    () => renderCensusIndustry($("#tab-census-ind"),   censusInd),
    "tab-census-demo":   () => renderCensusDemographics($("#tab-census-demo"), censusDem),
    "tab-industry":      () => renderIndustry(     $("#tab-industry"),      industry),
    "tab-enrolment":     () => renderEnrolment(    $("#tab-enrolment"),     enrolment),
  };

  const rendered = new Set();
  function activatePanel(id) {
    if (!rendered.has(id) && panelRenderers[id]) {
      rendered.add(id);
      panelRenderers[id]();
    }
  }
  activatePanel("tab-gttc-trends");  // first tab

  $$(".tab").forEach(tab =>
    tab.addEventListener("click", () => activatePanel(tab.dataset.panel))
  );

  // ── Always-visible sections ────────────────────────────────────────────────
  renderQualityReport(quality);
  renderMethodology(methodology);
  renderDistrictExplorer(censusDem, gttcCentres);

  // ── Export buttons ─────────────────────────────────────────────────────────
  document.addEventListener("click", e => {
    const btn = e.target.closest("[data-export]");
    if (!btn) return;
    const [apiPath, filename] = btn.dataset.export.split("|");
    // build fallback rows from embedded data
    let rows = null;
    if (apiPath.includes("gttc/trends/export"))  rows = gttcTrends?.yoy_table;
    if (apiPath.includes("gttc/centres/export")) rows = gttcCentres?.centres;
    if (apiPath.includes("census/industry/export")) rows = censusInd?.categories;
    if (apiPath.includes("industry/export"))     rows = industry?.sectors;
    downloadCSV(apiPath, filename, rows);
  });
}

document.addEventListener("DOMContentLoaded", init);
