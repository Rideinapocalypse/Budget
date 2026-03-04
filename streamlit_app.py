<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>CC Budget App</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0e1117;
  --surface:#161b27;
  --surface2:#1e2535;
  --surface3:#252d3f;
  --border:#2a3347;
  --border2:#344060;
  --text:#e8edf5;
  --text2:#8b96b0;
  --text3:#5a6480;
  --accent:#3b82f6;
  --accent2:#60a5fa;
  --green:#10b981;
  --red:#ef4444;
  --yellow:#f59e0b;
  --purple:#8b5cf6;
}
html{scroll-behavior:smooth}
body{font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:14px}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--surface)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

.app{display:grid;grid-template-columns:280px 1fr;min-height:100vh}

.sidebar{background:var(--surface);border-right:1px solid var(--border);padding:0;display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto}
.sidebar-header{padding:20px 20px 16px;border-bottom:1px solid var(--border)}
.logo{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.logo-icon{width:32px;height:32px;background:var(--accent);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:16px}
.logo-text{font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:15px;letter-spacing:-0.03em}
.logo-text span{color:var(--accent)}
.logo-sub{font-size:11px;color:var(--text3);letter-spacing:0.04em;text-transform:uppercase;margin-top:2px}
.sidebar-section{padding:16px 20px;border-bottom:1px solid var(--border)}
.sidebar-section-title{font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--text3);margin-bottom:12px}
.field{margin-bottom:12px}
.field:last-child{margin-bottom:0}
.field label{display:block;font-size:11px;color:var(--text2);margin-bottom:5px;font-weight:500}
.field-row{display:flex;align-items:center;gap:0}
.field-row input{flex:1;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;font-family:'IBM Plex Mono',monospace;font-size:13px;border-radius:4px 0 0 4px;outline:none;transition:border-color .15s}
.field-row input:focus{border-color:var(--accent)}
.field-row .spin{width:28px;height:32px;background:var(--surface3);border:1px solid var(--border);color:var(--text2);cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;transition:all .15s;border-left:none}
.field-row .spin:last-of-type{border-radius:0 4px 4px 0}
.field-row .spin:hover{background:var(--accent);color:white;border-color:var(--accent)}
.field input[type=range]{width:100%;accent-color:var(--accent);cursor:pointer}
.range-val{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--accent);text-align:right;margin-top:3px}
select.field-select{width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;font-family:'IBM Plex Sans',sans-serif;font-size:13px;border-radius:4px;outline:none;cursor:pointer}
select.field-select:focus{border-color:var(--accent)}

.month-tabs{display:flex;flex-wrap:wrap;gap:4px;padding:12px 20px;border-bottom:1px solid var(--border);background:var(--surface)}
.month-tab{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:500;padding:5px 10px;border-radius:3px;border:1px solid var(--border);background:transparent;color:var(--text3);cursor:pointer;transition:all .15s}
.month-tab:hover{border-color:var(--border2);color:var(--text2)}
.month-tab.active{background:var(--accent);border-color:var(--accent);color:white}

.main{padding:0;display:flex;flex-direction:column}
.topbar{padding:16px 28px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--surface);position:sticky;top:0;z-index:10}
.topbar-title{font-size:18px;font-weight:600;letter-spacing:-0.02em}
.topbar-title span{color:var(--accent);font-family:'IBM Plex Mono',monospace}
.topbar-actions{display:flex;gap:8px}
.btn{font-family:'IBM Plex Sans',sans-serif;font-size:12px;font-weight:600;padding:7px 14px;border-radius:4px;border:none;cursor:pointer;display:flex;align-items:center;gap:6px;letter-spacing:0.02em;transition:all .15s}
.btn-ghost{background:transparent;border:1px solid var(--border2);color:var(--text2)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent)}
.btn-primary{background:var(--accent);color:white}
.btn-primary:hover{background:var(--accent2)}
.btn-green{background:var(--green);color:white}
.btn-green:hover{opacity:.85}
.btn-yellow{background:var(--yellow);color:#000}
.btn-yellow:hover{opacity:.85}

.content{padding:24px 28px;flex:1}

.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;position:relative;overflow:hidden}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--kpi-color,var(--accent))}
.kpi-label{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;font-weight:600}
.kpi-val{font-family:'IBM Plex Mono',monospace;font-size:18px;font-weight:600;color:var(--text)}
.kpi-sub{font-size:10px;color:var(--text3);margin-top:3px}

.panel{background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:16px;overflow:hidden}
.panel-header{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;cursor:pointer;user-select:none}
.panel-header:hover{background:var(--surface2)}
.panel-title{font-size:12px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:var(--text2);display:flex;align-items:center;gap:8px}
.panel-title .dot{width:8px;height:8px;border-radius:50%;background:var(--accent)}
.panel-chevron{color:var(--text3);font-size:12px;transition:transform .2s}
.panel-chevron.open{transform:rotate(180deg)}
.panel-body{padding:16px}

.prod-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:10px;align-items:end;margin-bottom:10px}
.prod-field label{font-size:10px;color:var(--text3);margin-bottom:4px;display:block;font-weight:500}
.prod-field input{width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;font-family:'IBM Plex Mono',monospace;font-size:13px;border-radius:4px;outline:none;transition:border-color .15s}
.prod-field input:focus{border-color:var(--accent)}
.prod-result{background:var(--surface3);border:1px solid var(--border);border-radius:4px;padding:7px 10px}
.prod-result-label{font-size:9px;color:var(--text3);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px}
.prod-result-val{font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--green);font-weight:500}
.remove-btn{width:30px;height:30px;background:transparent;border:1px solid var(--border);color:var(--text3);border-radius:4px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;transition:all .15s;align-self:end}
.remove-btn:hover{background:var(--red);border-color:var(--red);color:white}
.add-block-btn{width:100%;padding:10px;background:transparent;border:1px dashed var(--border2);color:var(--text3);border-radius:4px;cursor:pointer;font-family:'IBM Plex Sans',sans-serif;font-size:12px;font-weight:500;transition:all .15s;margin-top:12px}
.add-block-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(59,130,246,0.05)}

.pnl-table{width:100%;border-collapse:collapse;font-size:12px}
.pnl-table th{font-size:10px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:var(--text3);padding:8px 10px;text-align:right;border-bottom:1px solid var(--border)}
.pnl-table th:first-child{text-align:left}
.pnl-table td{padding:8px 10px;border-bottom:1px solid var(--border);font-family:'IBM Plex Mono',monospace;font-size:12px;text-align:right;color:var(--text2)}
.pnl-table td:first-child{text-align:left;font-family:'IBM Plex Sans',sans-serif;color:var(--text)}
.pnl-table tr:last-child td{border-bottom:none}
.pnl-table .total-row td{background:var(--surface2);font-weight:600;color:var(--text)}
.pnl-table .positive{color:var(--green)}
.pnl-table .negative{color:var(--red)}

.copy-helper{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:12px 16px;background:var(--surface2);border-radius:6px;margin-bottom:16px}
.copy-helper label{font-size:12px;color:var(--text2)}
.copy-helper select{background:var(--surface3);border:1px solid var(--border);color:var(--text);padding:5px 10px;border-radius:4px;font-size:12px;outline:none;cursor:pointer}

.toast{position:fixed;bottom:24px;right:24px;background:var(--surface2);border:1px solid var(--border2);color:var(--text);padding:12px 18px;border-radius:6px;font-size:13px;font-weight:500;z-index:1000;opacity:0;transform:translateY(10px);transition:all .3s;pointer-events:none}
.toast.show{opacity:1;transform:translateY(0)}
.toast.success{border-color:var(--green);color:var(--green)}
.toast.error{border-color:var(--red);color:var(--red)}

.section-label{font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--text3);margin-bottom:12px;margin-top:24px;display:flex;align-items:center;gap:8px}
.section-label::after{content:'';flex:1;height:1px;background:var(--border)}

@media(max-width:900px){
  .app{grid-template-columns:1fr}
  .sidebar{position:relative;height:auto}
  .kpi-row{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>

<div class="app">
<aside class="sidebar">
  <div class="sidebar-header">
    <div class="logo">
      <div class="logo-icon">📞</div>
      <div>
        <div class="logo-text"><span>CC</span>Budget</div>
        <div class="logo-sub">Call Center Forecast</div>
      </div>
    </div>
  </div>

  <div class="sidebar-section">
    <div class="sidebar-section-title">Global Inputs</div>
    <div class="field">
      <label>Worked Hours / Agent / Month</label>
      <div class="field-row">
        <input type="number" id="g_hours" value="180" step="1" oninput="recalc()"/>
        <button class="spin" onclick="adj('g_hours',-1)">−</button>
        <button class="spin" onclick="adj('g_hours',1)">+</button>
      </div>
    </div>
    <div class="field">
      <label>Shrinkage % (default)</label>
      <input type="range" id="g_shrink" min="0" max="0.5" step="0.01" value="0.15" oninput="document.getElementById('g_shrink_val').textContent=(+this.value*100).toFixed(0)+'%';recalc()"/>
      <div class="range-val" id="g_shrink_val">15%</div>
    </div>
    <div class="field">
      <label>FX Rate (1 EUR = TRY) [default]</label>
      <div class="field-row">
        <input type="number" id="g_fx" value="38" step="0.5" oninput="recalc()"/>
        <button class="spin" onclick="adj('g_fx',-0.5)">−</button>
        <button class="spin" onclick="adj('g_fx',0.5)">+</button>
      </div>
    </div>
  </div>

  <div class="sidebar-section">
    <div class="sidebar-section-title">Global Cost Drivers</div>
    <div class="field">
      <label>Salary Multiplier (CTC)</label>
      <div class="field-row">
        <input type="number" id="g_ctc" value="1.70" step="0.05" oninput="recalc()"/>
        <button class="spin" onclick="adj('g_ctc',-0.05)">−</button>
        <button class="spin" onclick="adj('g_ctc',0.05)">+</button>
      </div>
    </div>
    <div class="field">
      <label>Bonus % of Base Salary</label>
      <div class="field-row">
        <input type="number" id="g_bonus_pct" value="0.10" step="0.01" oninput="recalc()"/>
        <button class="spin" onclick="adj('g_bonus_pct',-0.01)">−</button>
        <button class="spin" onclick="adj('g_bonus_pct',0.01)">+</button>
      </div>
    </div>
    <div class="field">
      <label>Meal Card / Agent / Month (TRY)</label>
      <div class="field-row">
        <input type="number" id="g_meal" value="5850" step="50" oninput="recalc()"/>
        <button class="spin" onclick="adj('g_meal',-50)">−</button>
        <button class="spin" onclick="adj('g_meal',50)">+</button>
      </div>
    </div>
    <div class="field">
      <label>Unit Price Currency</label>
      <select class="field-select" id="g_currency" onchange="recalc()">
        <option value="EUR">EUR</option>
        <option value="USD">USD</option>
        <option value="TRY">TRY</option>
      </select>
    </div>
  </div>

  <div class="sidebar-section">
    <div class="sidebar-section-title">Month Navigation</div>
    <div id="monthTabs" style="display:flex;flex-wrap:wrap;gap:4px"></div>
  </div>

  <div class="sidebar-section" style="margin-top:auto">
    <div class="sidebar-section-title">Data</div>
    <div style="display:flex;flex-direction:column;gap:8px">
      <button class="btn btn-green" onclick="exportExcel()" style="width:100%;justify-content:center">⬇ Export Excel</button>
      <button class="btn btn-ghost" onclick="document.getElementById('fileInput').click()" style="width:100%;justify-content:center">⬆ Import Excel</button>
      <input type="file" id="fileInput" accept=".xlsx" onchange="importExcel(event)" style="display:none"/>
    </div>
  </div>
</aside>

<main class="main">
  <div class="topbar">
    <div class="topbar-title">Budget — <span id="activeMonthLabel">Jan</span></div>
    <div class="topbar-actions">
      <button class="btn btn-ghost" onclick="addBlock()">+ Add Block</button>
      <button class="btn btn-yellow" onclick="showCopyHelper()">📋 Copy Month</button>
    </div>
  </div>

  <div class="content">
    <div class="kpi-row">
      <div class="kpi-card" style="--kpi-color:var(--accent)">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-val" id="kpi_rev">€0</div>
        <div class="kpi-sub">EUR this month</div>
      </div>
      <div class="kpi-card" style="--kpi-color:var(--red)">
        <div class="kpi-label">Total Cost</div>
        <div class="kpi-val" id="kpi_cost">€0</div>
        <div class="kpi-sub">EUR this month</div>
      </div>
      <div class="kpi-card" style="--kpi-color:var(--green)">
        <div class="kpi-label">Gross Margin</div>
        <div class="kpi-val" id="kpi_margin">€0</div>
        <div class="kpi-sub" id="kpi_margin_pct">0%</div>
      </div>
      <div class="kpi-card" style="--kpi-color:var(--yellow)">
        <div class="kpi-label">Total HC</div>
        <div class="kpi-val" id="kpi_hc">0</div>
        <div class="kpi-sub">agents this month</div>
      </div>
      <div class="kpi-card" style="--kpi-color:var(--purple)">
        <div class="kpi-label">Effective Hours</div>
        <div class="kpi-val" id="kpi_hrs">0</div>
        <div class="kpi-sub">billable hrs/month</div>
      </div>
    </div>

    <div class="copy-helper" id="copyHelper" style="display:none">
      <span>📋</span>
      <label>Copy</label>
      <select id="copyFrom"></select>
      <label>→ to →</label>
      <select id="copyTo"></select>
      <button class="btn btn-yellow" onclick="doCopy()">Copy</button>
      <button class="btn btn-ghost" onclick="document.getElementById('copyHelper').style.display='none'">✕</button>
    </div>

    <div class="section-label">Production Blocks</div>
    <div id="blocksContainer"></div>
    <button class="add-block-btn" onclick="addBlock()">+ Add Production Block</button>

    <div class="section-label" style="margin-top:32px">P&L Summary — Full Year</div>
    <div class="panel">
      <div class="panel-header" onclick="togglePanel(this)">
        <div class="panel-title"><span class="dot" style="background:var(--green)"></span>Annual P&L Overview</div>
        <span class="panel-chevron open">▼</span>
      </div>
      <div class="panel-body" style="overflow-x:auto">
        <table class="pnl-table" id="pnlTable">
          <thead>
            <tr>
              <th style="text-align:left">Line Item</th>
              <th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th><th>Jun</th>
              <th>Jul</th><th>Aug</th><th>Sep</th><th>Oct</th><th>Nov</th><th>Dec</th>
              <th>Full Year</th>
            </tr>
          </thead>
          <tbody id="pnlBody"></tbody>
        </table>
      </div>
    </div>
  </div>
</main>
</div>

<div class="toast" id="toast"></div>

<script>
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
let activeMonth = 0;
let state = {};
MONTHS.forEach((_,i) => { state[i] = []; });

function buildMonthTabs(){
  const el = document.getElementById('monthTabs');
  el.innerHTML = MONTHS.map((m,i)=>`<button class="month-tab ${i===activeMonth?'active':''}" onclick="setMonth(${i})">${m}</button>`).join('');
}

function setMonth(i){
  activeMonth = i;
  document.getElementById('activeMonthLabel').textContent = MONTHS[i];
  buildMonthTabs();
  renderBlocks();
  recalc();
}

function addBlock(data){
  state[activeMonth].push(data || {lang:'',hc:0,salary:0,unitPrice:0,shrink:null,fx:null,hours:null});
  renderBlocks();
  recalc();
}

function removeBlock(idx){
  state[activeMonth].splice(idx,1);
  renderBlocks();
  recalc();
}

function updateBlock(idx,field,val){
  state[activeMonth][idx][field] = val;
  recalc();
}

function renderBlocks(){
  const m = activeMonth;
  const blocks = state[m];
  const container = document.getElementById('blocksContainer');
  if(blocks.length===0){
    container.innerHTML=`<div style="text-align:center;padding:32px;color:var(--text3);font-size:13px">No production blocks for ${MONTHS[m]}. Click "+ Add Block" to start.</div>`;
    return;
  }
  container.innerHTML = blocks.map((b,i)=>{
    const shrinkVal = b.shrink!==null?b.shrink:+document.getElementById('g_shrink').value;
    const fxVal = b.fx!==null?b.fx:+document.getElementById('g_fx').value;
    const hoursVal = b.hours!==null?b.hours:+document.getElementById('g_hours').value;
    const effHrs = hoursVal*(1-shrinkVal);
    const rev = b.hc*effHrs*b.unitPrice;
    const ctc = +document.getElementById('g_ctc').value;
    const bonus = +document.getElementById('g_bonus_pct').value;
    const meal = +document.getElementById('g_meal').value;
    const totalCost_eur = (b.hc*b.salary*ctc*(1+bonus)+b.hc*meal)/fxVal;
    const margin = rev-totalCost_eur;
    const colors = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444'];
    return `
    <div class="panel" style="margin-bottom:10px">
      <div class="panel-header" onclick="togglePanel(this)" style="padding:10px 16px">
        <div class="panel-title">
          <span class="dot" style="background:${colors[i%5]}"></span>
          Block #${i+1}${b.lang?' — '+b.lang:''}
          <span style="font-size:10px;color:var(--text3);font-weight:400;margin-left:8px">${b.hc} HC · €${fmt(rev)} rev · €${fmt(margin)} margin</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <button class="remove-btn" onclick="event.stopPropagation();removeBlock(${i})">✕</button>
          <span class="panel-chevron open">▼</span>
        </div>
      </div>
      <div class="panel-body">
        <div class="prod-grid">
          <div class="prod-field"><label>Language / Label</label><input type="text" value="${b.lang}" placeholder="e.g. DE, EN, TR" oninput="updateBlock(${i},'lang',this.value)"/></div>
          <div class="prod-field"><label>Headcount (HC)</label><input type="number" value="${b.hc}" step="1" min="0" oninput="updateBlock(${i},'hc',+this.value)"/></div>
          <div class="prod-field"><label>Base Salary (TRY/mo)</label><input type="number" value="${b.salary}" step="100" min="0" oninput="updateBlock(${i},'salary',+this.value)"/></div>
          <div class="prod-field"><label>Unit Price (EUR/hr)</label><input type="number" value="${b.unitPrice}" step="0.1" min="0" oninput="updateBlock(${i},'unitPrice',+this.value)"/></div>
          <div></div>
        </div>
        <div class="prod-grid" style="grid-template-columns:1fr 1fr 1fr 1fr auto">
          <div class="prod-field"><label>Shrinkage % (override)</label><input type="number" value="${b.shrink!==null?b.shrink:''}" placeholder="Global: ${(+document.getElementById('g_shrink').value*100).toFixed(0)}%" step="0.01" oninput="updateBlock(${i},'shrink',this.value===''?null:+this.value)"/></div>
          <div class="prod-field"><label>FX Rate (override)</label><input type="number" value="${b.fx!==null?b.fx:''}" placeholder="Global: ${document.getElementById('g_fx').value}" step="0.5" oninput="updateBlock(${i},'fx',this.value===''?null:+this.value)"/></div>
          <div class="prod-field"><label>Hours/Agent (override)</label><input type="number" value="${b.hours!==null?b.hours:''}" placeholder="Global: ${document.getElementById('g_hours').value}" step="1" oninput="updateBlock(${i},'hours',this.value===''?null:+this.value)"/></div>
          <div><div class="prod-result"><div class="prod-result-label">Revenue (EUR)</div><div class="prod-result-val">€${fmt(rev)}</div></div></div>
          <div><div class="prod-result"><div class="prod-result-label">Margin (EUR)</div><div class="prod-result-val" style="color:${margin>=0?'var(--green)':'var(--red)'}">€${fmt(margin)}</div></div></div>
        </div>
      </div>
    </div>`;
  }).join('');
}

function fmt(n){return Number(n).toLocaleString('en',{minimumFractionDigits:0,maximumFractionDigits:0})}
function fmtPct(n){return (n*100).toFixed(1)+'%'}

function recalc(){
  renderBlocks();
  updateKPIs();
  updatePnL();
}

function getMonthTotals(m){
  const blocks = state[m];
  const gShrink=+document.getElementById('g_shrink').value;
  const gFx=+document.getElementById('g_fx').value;
  const gHours=+document.getElementById('g_hours').value;
  const ctc=+document.getElementById('g_ctc').value;
  const bonus=+document.getElementById('g_bonus_pct').value;
  const meal=+document.getElementById('g_meal').value;
  let totalRev=0,totalCostEur=0,totalHC=0,totalHrs=0;
  blocks.forEach(b=>{
    const shrink=b.shrink!==null?b.shrink:gShrink;
    const fx=b.fx!==null?b.fx:gFx;
    const hours=b.hours!==null?b.hours:gHours;
    const effHrs=hours*(1-shrink);
    totalRev+=b.hc*effHrs*b.unitPrice;
    totalCostEur+=(b.hc*b.salary*ctc*(1+bonus)+b.hc*meal)/fx;
    totalHC+=+b.hc;
    totalHrs+=b.hc*effHrs;
  });
  return{rev:totalRev,cost:totalCostEur,margin:totalRev-totalCostEur,hc:totalHC,hrs:totalHrs};
}

function updateKPIs(){
  const t=getMonthTotals(activeMonth);
  document.getElementById('kpi_rev').textContent='€'+fmt(t.rev);
  document.getElementById('kpi_cost').textContent='€'+fmt(t.cost);
  document.getElementById('kpi_margin').textContent='€'+fmt(t.margin);
  document.getElementById('kpi_margin').style.color=t.margin>=0?'var(--green)':'var(--red)';
  document.getElementById('kpi_margin_pct').textContent=t.rev>0?fmtPct(t.margin/t.rev):'0%';
  document.getElementById('kpi_hc').textContent=fmt(t.hc);
  document.getElementById('kpi_hrs').textContent=fmt(t.hrs);
}

function updatePnL(){
  const monthly=MONTHS.map((_,i)=>getMonthTotals(i));
  const totals=monthly.reduce((a,t)=>{a.rev+=t.rev;a.cost+=t.cost;a.margin+=t.margin;return a},{rev:0,cost:0,margin:0});
  const rows=[
    {label:'Revenue (EUR)',key:'rev',cls:'positive'},
    {label:'Total Cost (EUR)',key:'cost',cls:'negative'},
    {label:'Gross Margin (EUR)',key:'margin',cls:''},
    {label:'Margin %',key:'pct',cls:''},
  ];
  document.getElementById('pnlBody').innerHTML=rows.map(r=>{
    const vals=monthly.map(t=>r.key==='pct'?(t.rev>0?fmtPct(t.margin/t.rev):'—'):'€'+fmt(t[r.key]));
    const fyVal=r.key==='pct'?(totals.rev>0?fmtPct(totals.margin/totals.rev):'—'):'€'+fmt(totals[r.key]);
    const cls=r.key==='margin'?(totals.margin>=0?'positive':'negative'):r.cls;
    return`<tr class="${r.key==='margin'||r.key==='rev'?'total-row':''}">
      <td>${r.label}</td>
      ${vals.map(v=>`<td class="${r.key==='margin'?cls:r.cls}">${v}</td>`).join('')}
      <td class="${cls}" style="font-weight:600">${fyVal}</td>
    </tr>`;
  }).join('');
}

function togglePanel(header){
  const body=header.nextElementSibling;
  const chevron=header.querySelector('.panel-chevron');
  if(body.style.display==='none'){body.style.display='';chevron.classList.add('open')}
  else{body.style.display='none';chevron.classList.remove('open')}
}

function showCopyHelper(){
  const helper=document.getElementById('copyHelper');
  document.getElementById('copyFrom').innerHTML=MONTHS.map((m,i)=>`<option value="${i}" ${i===activeMonth?'selected':''}>${m}</option>`).join('');
  document.getElementById('copyTo').innerHTML=MONTHS.map((m,i)=>`<option value="${i}" ${i===(activeMonth+1)%12?'selected':''}>${m}</option>`).join('');
  helper.style.display='flex';
}

function doCopy(){
  const from=+document.getElementById('copyFrom').value;
  const to=+document.getElementById('copyTo').value;
  if(from===to){showToast('Source and destination are the same','error');return;}
  state[to]=JSON.parse(JSON.stringify(state[from]));
  showToast(`Copied ${MONTHS[from]} → ${MONTHS[to]}`,'success');
  if(activeMonth===to)recalc();
  document.getElementById('copyHelper').style.display='none';
}

function exportExcel(){
  const wb=XLSX.utils.book_new();
  const summaryData=[
    ['CC Budget Export'],[''],
    ['Global Settings',''],
    ['Worked Hours/Agent/Month',+document.getElementById('g_hours').value],
    ['Shrinkage %',+document.getElementById('g_shrink').value],
    ['FX Rate (EUR=TRY)',+document.getElementById('g_fx').value],
    ['CTC Multiplier',+document.getElementById('g_ctc').value],
    ['Bonus % of Base',+document.getElementById('g_bonus_pct').value],
    ['Meal Card (TRY/mo)',+document.getElementById('g_meal').value],
    [''],
    ['Month','Revenue (EUR)','Cost (EUR)','Margin (EUR)','Margin %','Total HC'],
  ];
  const totals={rev:0,cost:0,margin:0};
  MONTHS.forEach((_,i)=>{
    const t=getMonthTotals(i);
    summaryData.push([MONTHS[i],t.rev,t.cost,t.margin,t.rev>0?t.margin/t.rev:0,t.hc]);
    totals.rev+=t.rev;totals.cost+=t.cost;totals.margin+=t.margin;
  });
  summaryData.push(['Full Year',totals.rev,totals.cost,totals.margin,totals.rev>0?totals.margin/totals.rev:0,'']);
  XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(summaryData),'Summary');

  const gShrink=+document.getElementById('g_shrink').value;
  const gFx=+document.getElementById('g_fx').value;
  const gHours=+document.getElementById('g_hours').value;
  const ctc=+document.getElementById('g_ctc').value;
  const bonus=+document.getElementById('g_bonus_pct').value;
  const meal=+document.getElementById('g_meal').value;

  MONTHS.forEach((m,mi)=>{
    const rows=[['Language','HC','Base Salary (TRY)','Unit Price (EUR/hr)','Shrinkage Override','FX Override','Hours Override','Revenue (EUR)','Cost (EUR)','Margin (EUR)']];
    state[mi].forEach(b=>{
      const shrink=b.shrink!==null?b.shrink:gShrink;
      const fx=b.fx!==null?b.fx:gFx;
      const hours=b.hours!==null?b.hours:gHours;
      const effHrs=hours*(1-shrink);
      const rev=b.hc*effHrs*b.unitPrice;
      const cost_eur=(b.hc*b.salary*ctc*(1+bonus)+b.hc*meal)/fx;
      rows.push([b.lang,b.hc,b.salary,b.unitPrice,b.shrink!==null?b.shrink:'',b.fx!==null?b.fx:'',b.hours!==null?b.hours:'',rev,cost_eur,rev-cost_eur]);
    });
    XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(rows),m);
  });
  XLSX.writeFile(wb,'CC_Budget_Export.xlsx');
  showToast('Excel exported successfully!','success');
}

function importExcel(e){
  const file=e.target.files[0];
  if(!file)return;
  const reader=new FileReader();
  reader.onload=ev=>{
    try{
      const wb=XLSX.read(ev.target.result,{type:'binary'});
      const sum=wb.Sheets['Summary'];
      if(sum){
        const data=XLSX.utils.sheet_to_json(sum,{header:1});
        const findVal=label=>{const row=data.find(r=>r[0]===label);return row?row[1]:null};
        const setIf=(id,label)=>{const v=findVal(label);if(v!=null)document.getElementById(id).value=v};
        setIf('g_hours','Worked Hours/Agent/Month');
        setIf('g_shrink','Shrinkage %');
        document.getElementById('g_shrink_val').textContent=(+document.getElementById('g_shrink').value*100).toFixed(0)+'%';
        setIf('g_fx','FX Rate (EUR=TRY)');
        setIf('g_ctc','CTC Multiplier');
        setIf('g_bonus_pct','Bonus % of Base');
        setIf('g_meal','Meal Card (TRY/mo)');
      }
      MONTHS.forEach((m,mi)=>{
        const ws=wb.Sheets[m];
        if(!ws)return;
        state[mi]=[];
        XLSX.utils.sheet_to_json(ws,{header:1}).slice(1).forEach(r=>{
          if(r.length<4)return;
          state[mi].push({lang:r[0]||'',hc:+r[1]||0,salary:+r[2]||0,unitPrice:+r[3]||0,
            shrink:r[4]!==''&&r[4]!=null?+r[4]:null,
            fx:r[5]!==''&&r[5]!=null?+r[5]:null,
            hours:r[6]!==''&&r[6]!=null?+r[6]:null});
        });
      });
      recalc();
      showToast('Excel imported successfully!','success');
    }catch(err){showToast('Import failed: '+err.message,'error')}
    e.target.value='';
  };
  reader.readAsBinaryString(file);
}

function showToast(msg,type=''){
  const t=document.getElementById('toast');
  t.textContent=msg;t.className='toast show '+(type||'');
  setTimeout(()=>t.className='toast',3000);
}

function adj(id,delta){
  const el=document.getElementById(id);
  el.value=(parseFloat(el.value)||0)+delta;
  recalc();
}

buildMonthTabs();
recalc();
</script>
</body>
</html>
