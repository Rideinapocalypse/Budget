<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CC Budget Tool — Call Center Budget & Forecast</title>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --ink:    #0d0f14;
      --paper:  #f5f2eb;
      --accent: #1a6fff;
      --green:  #00c471;
      --yellow: #ffd84d;
      --muted:  #6b7280;
      --card:   #ffffff;
      --border: #e2ddd4;
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'DM Mono', monospace;
      background: var(--paper);
      color: var(--ink);
      overflow-x: hidden;
    }

    body::before {
      content: '';
      position: fixed; inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 0;
    }

    nav {
      position: sticky; top: 0;
      display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 2.5rem;
      background: rgba(245,242,235,0.88);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      z-index: 100;
    }

    .nav-logo {
      font-family: 'Syne', sans-serif;
      font-weight: 800;
      font-size: 1rem;
      letter-spacing: -0.02em;
      display: flex; align-items: center; gap: 0.5rem;
    }
    .nav-logo span { color: var(--accent); }

    .nav-links { display: flex; gap: 2rem; list-style: none; }
    .nav-links a {
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--muted);
      text-decoration: none;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      transition: color .2s;
    }
    .nav-links a:hover { color: var(--ink); }

    .nav-cta {
      background: var(--ink);
      color: var(--paper) !important;
      padding: 0.45rem 1.1rem;
      border-radius: 4px;
      transition: background .2s !important;
    }
    .nav-cta:hover { background: var(--accent) !important; color: white !important; }

    .hero {
      position: relative;
      min-height: 90vh;
      display: grid;
      place-items: center;
      padding: 6rem 2rem 4rem;
      overflow: hidden;
    }

    .hero-bg {
      position: absolute; inset: 0;
      background:
        radial-gradient(ellipse 70% 60% at 80% 20%, rgba(26,111,255,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 10% 80%, rgba(0,196,113,0.06) 0%, transparent 50%);
    }

    .hero-grid {
      position: absolute; inset: 0;
      background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
      background-size: 48px 48px;
      opacity: 0.5;
      mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
    }

    .hero-inner {
      position: relative;
      max-width: 860px;
      text-align: center;
    }

    .hero-badge {
      display: inline-flex; align-items: center; gap: 0.4rem;
      font-size: 0.72rem;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: var(--yellow);
      color: var(--ink);
      padding: 0.35rem 0.9rem;
      border-radius: 2px;
      margin-bottom: 1.8rem;
      opacity: 0;
      animation: fadeUp 0.6s ease 0.1s forwards;
    }

    h1 {
      font-family: 'Syne', sans-serif;
      font-weight: 800;
      font-size: clamp(2.8rem, 7vw, 5.2rem);
      line-height: 1.0;
      letter-spacing: -0.04em;
      margin-bottom: 1.4rem;
      opacity: 0;
      animation: fadeUp 0.7s ease 0.25s forwards;
    }

    h1 .accent { color: var(--accent); }
    h1 .line2 { display: block; }

    .hero-sub {
      font-size: 1.05rem;
      font-weight: 300;
      color: var(--muted);
      line-height: 1.7;
      max-width: 560px;
      margin: 0 auto 2.5rem;
      opacity: 0;
      animation: fadeUp 0.7s ease 0.4s forwards;
    }

    .hero-actions {
      display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;
      opacity: 0;
      animation: fadeUp 0.7s ease 0.55s forwards;
    }

    .btn {
      font-family: 'DM Mono', monospace;
      font-size: 0.82rem;
      font-weight: 500;
      letter-spacing: 0.03em;
      padding: 0.75rem 1.8rem;
      border-radius: 4px;
      text-decoration: none;
      transition: transform .15s, box-shadow .15s;
      cursor: pointer;
      border: none;
    }

    .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }

    .btn-primary { background: var(--ink); color: var(--paper); }
    .btn-primary:hover { background: var(--accent); }

    .btn-outline {
      background: transparent;
      color: var(--ink);
      border: 1.5px solid var(--ink);
    }
    .btn-outline:hover { background: var(--ink); color: var(--paper); }

    .stats-bar {
      background: var(--ink);
      color: var(--paper);
      padding: 1.2rem 2.5rem;
      display: flex;
      justify-content: center;
      gap: 0;
      overflow: hidden;
    }

    .stat-item {
      display: flex; flex-direction: column; align-items: center;
      padding: 0 3rem;
      border-right: 1px solid rgba(255,255,255,0.1);
    }
    .stat-item:last-child { border-right: none; }

    .stat-num {
      font-family: 'Syne', sans-serif;
      font-size: 1.6rem;
      font-weight: 800;
      color: var(--yellow);
    }
    .stat-label { font-size: 0.7rem; color: rgba(255,255,255,0.5); letter-spacing: 0.06em; text-transform: uppercase; margin-top: 0.15rem; }

    section { padding: 5rem 2rem; position: relative; }
    .section-inner { max-width: 1100px; margin: 0 auto; }

    .section-tag {
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 0.8rem;
    }

    h2 {
      font-family: 'Syne', sans-serif;
      font-weight: 800;
      font-size: clamp(1.8rem, 4vw, 2.8rem);
      letter-spacing: -0.03em;
      line-height: 1.1;
      margin-bottom: 1rem;
    }

    .section-desc {
      font-size: 0.92rem;
      color: var(--muted);
      line-height: 1.8;
      max-width: 520px;
    }

    .sheets-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.5rem;
      margin-top: 3rem;
    }

    .sheet-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1.6rem;
      position: relative;
      overflow: hidden;
      transition: transform .2s, box-shadow .2s;
    }
    .sheet-card:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
    .sheet-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: var(--card-accent, var(--accent));
    }

    .sheet-card:nth-child(1) { --card-accent: #1a6fff; }
    .sheet-card:nth-child(2) { --card-accent: #ffd84d; }
    .sheet-card:nth-child(3) { --card-accent: #00c471; }
    .sheet-card:nth-child(4) { --card-accent: #ff6b35; }
    .sheet-card:nth-child(5) { --card-accent: #9b59b6; }
    .sheet-card:nth-child(6) { --card-accent: #e74c3c; }

    .sheet-emoji { font-size: 1.6rem; margin-bottom: 0.8rem; }
    .sheet-name { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem; margin-bottom: 0.5rem; }
    .sheet-desc { font-size: 0.8rem; color: var(--muted); line-height: 1.65; }

    .colors-section { background: var(--ink); }
    .colors-section h2, .colors-section .section-tag { color: var(--paper); }
    .colors-section .section-desc { color: rgba(255,255,255,0.5); }

    .color-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1rem;
      margin-top: 3rem;
    }

    .color-card {
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 6px;
      padding: 1.4rem;
      display: flex; align-items: flex-start; gap: 1rem;
    }

    .color-dot { width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0; margin-top: 2px; }
    .color-info { flex: 1; }
    .color-name { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.9rem; color: white; margin-bottom: 0.3rem; }
    .color-meaning { font-size: 0.75rem; color: rgba(255,255,255,0.45); line-height: 1.5; }

    .steps-list {
      display: flex;
      flex-direction: column;
      gap: 0;
      margin-top: 3rem;
      max-width: 680px;
    }

    .step {
      display: flex; gap: 1.5rem;
      padding: 1.5rem 0;
      border-bottom: 1px solid var(--border);
      opacity: 0;
      transform: translateX(-20px);
      transition: opacity .5s, transform .5s;
    }
    .step.visible { opacity: 1; transform: none; }

    .step-num {
      font-family: 'Syne', sans-serif;
      font-weight: 800;
      font-size: 2rem;
      color: var(--border);
      line-height: 1;
      flex-shrink: 0;
      width: 48px;
      text-align: right;
    }

    .step-body { flex: 1; }
    .step-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem; margin-bottom: 0.35rem; }
    .step-text { font-size: 0.82rem; color: var(--muted); line-height: 1.7; }

    code {
      background: rgba(26,111,255,0.08);
      color: var(--accent);
      padding: 0.15rem 0.45rem;
      border-radius: 3px;
      font-size: 0.85em;
    }

    .tips-section { background: #f0f4ff; }

    .tips-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1rem;
      margin-top: 3rem;
    }

    .tip-card {
      background: white;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1.4rem;
    }

    .tip-icon { font-size: 1.4rem; margin-bottom: 0.6rem; }
    .tip-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.4rem; }
    .tip-text { font-size: 0.78rem; color: var(--muted); line-height: 1.6; }

    .download-section { background: var(--accent); color: white; text-align: center; }
    .download-section h2 { color: white; }
    .download-section .section-desc { color: rgba(255,255,255,0.7); margin: 0 auto 2.5rem; }

    .download-btns { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }

    .btn-white { background: white; color: var(--accent); }
    .btn-white:hover { background: var(--paper); }

    .btn-ghost {
      background: transparent;
      color: white;
      border: 1.5px solid rgba(255,255,255,0.5);
    }
    .btn-ghost:hover { background: rgba(255,255,255,0.15); }

    footer {
      background: var(--ink);
      color: rgba(255,255,255,0.35);
      text-align: center;
      padding: 2rem;
      font-size: 0.75rem;
      letter-spacing: 0.04em;
    }
    footer a { color: rgba(255,255,255,0.5); text-decoration: none; }
    footer a:hover { color: white; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(20px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 640px) {
      nav { padding: 1rem 1.2rem; }
      .nav-links { display: none; }
      .stat-item { padding: 0 1.2rem; }
      .stat-num { font-size: 1.2rem; }
      section { padding: 3.5rem 1.2rem; }
    }
  </style>
</head>
<body>

<nav>
  <div class="nav-logo">📞 <span>CC</span>Budget</div>
  <ul class="nav-links">
    <li><a href="#sheets">Sheets</a></li>
    <li><a href="#quickstart">Quick Start</a></li>
    <li><a href="#tips">Tips</a></li>
    <li><a href="#download" class="nav-cta">Download</a></li>
  </ul>
</nav>

<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
  <div class="hero-inner">
    <div class="hero-badge">🔥 Free Template — No Sign-up Required</div>
    <h1>
      Call Center
      <span class="line2 accent">Budget &amp; Forecast</span>
    </h1>
    <p class="hero-sub">
      A professional Excel template for call centers — with a Python script to regenerate or customize it. Fill in blue cells, everything else calculates automatically.
    </p>
    <div class="hero-actions">
      <a href="CC_Budget_Template.xlsx" class="btn btn-primary" download>⬇ Download Excel Template</a>
      <a href="generate_budget.py" class="btn btn-outline" download>⬇ Download Python Script</a>
    </div>
  </div>
</section>

<div class="stats-bar">
  <div class="stat-item"><span class="stat-num">6</span><span class="stat-label">Sheets</span></div>
  <div class="stat-item"><span class="stat-num">100%</span><span class="stat-label">Auto-calc</span></div>
  <div class="stat-item"><span class="stat-num">12</span><span class="stat-label">Months</span></div>
  <div class="stat-item"><span class="stat-num">Free</span><span class="stat-label">No Cost</span></div>
</div>

<section id="sheets">
  <div class="section-inner">
    <p class="section-tag">What's inside</p>
    <h2>Six sheets.<br/>One complete picture.</h2>
    <p class="section-desc">Every sheet is linked — change a headcount number and revenue, costs, and margins update instantly across the whole workbook.</p>
    <div class="sheets-grid">
      <div class="sheet-card">
        <div class="sheet-emoji">📋</div>
        <div class="sheet-name">Instructions</div>
        <div class="sheet-desc">Read first. Color coding guide, usage tips, and how each sheet connects to the others.</div>
      </div>
      <div class="sheet-card">
        <div class="sheet-emoji">📊</div>
        <div class="sheet-name">Assumptions</div>
        <div class="sheet-desc">Enter unit rates, shrinkage %, salaries, meal cards, and CTC multipliers. These drive everything else.</div>
      </div>
      <div class="sheet-card">
        <div class="sheet-emoji">👥</div>
        <div class="sheet-name">Headcount Plan</div>
        <div class="sheet-desc">Enter FTE count per role per month. Overhead roles auto-calculate as a ratio of billable agents.</div>
      </div>
      <div class="sheet-card">
        <div class="sheet-emoji">💰</div>
        <div class="sheet-name">Salary &amp; Cost</div>
        <div class="sheet-desc">Auto-calculated salary + CTC cost. Includes gross wages, employer social costs, and meal card totals.</div>
      </div>
      <div class="sheet-card">
        <div class="sheet-emoji">📈</div>
        <div class="sheet-name">Revenue Forecast</div>
        <div class="sheet-desc">Auto-calculated billable revenue based on headcount, unit rates, and adjusted productive hours.</div>
      </div>
      <div class="sheet-card">
        <div class="sheet-emoji">📉</div>
        <div class="sheet-name">P&amp;L Summary</div>
        <div class="sheet-desc">Full P&amp;L with margin — adds overhead costs here. Shows gross margin $ and % by month and full year.</div>
      </div>
    </div>
  </div>
</section>

<section class="colors-section">
  <div class="section-inner">
    <p class="section-tag" style="color: rgba(255,255,255,0.4)">Color system</p>
    <h2>Know what<br/>to touch.</h2>
    <p class="section-desc">Every cell is color-coded so you always know exactly what to edit and what to leave alone.</p>
    <div class="color-grid">
      <div class="color-card">
        <div class="color-dot" style="background:#1a6fff;"></div>
        <div class="color-info">
          <div class="color-name">Blue Text</div>
          <div class="color-meaning">Input cells — fill these in. These are the only cells you should edit.</div>
        </div>
      </div>
      <div class="color-card">
        <div class="color-dot" style="background:#333;border:1px solid rgba(255,255,255,0.2);"></div>
        <div class="color-info">
          <div class="color-name">Black Text</div>
          <div class="color-meaning">Auto-calculated formulas — do not edit. These update automatically.</div>
        </div>
      </div>
      <div class="color-card">
        <div class="color-dot" style="background:#00c471;"></div>
        <div class="color-info">
          <div class="color-name">Green Text</div>
          <div class="color-meaning">Linked from another sheet — do not edit. Values pulled automatically.</div>
        </div>
      </div>
      <div class="color-card">
        <div class="color-dot" style="background:#ffd84d;"></div>
        <div class="color-info">
          <div class="color-name">Yellow Background</div>
          <div class="color-meaning">Key assumption needing regular review — check these when business conditions change.</div>
        </div>
      </div>
    </div>
  </div>
</section>

<section id="quickstart">
  <div class="section-inner">
    <p class="section-tag">No coding needed</p>
    <h2>Up and running<br/>in minutes.</h2>
    <div class="steps-list">
      <div class="step">
        <div class="step-num">01</div>
        <div class="step-body">
          <div class="step-title">Download the Excel template</div>
          <div class="step-text">Click the download button above to get <code>CC_Budget_Template.xlsx</code>. Open it in Excel or Google Sheets.</div>
        </div>
      </div>
      <div class="step">
        <div class="step-num">02</div>
        <div class="step-body">
          <div class="step-title">Read the Instructions tab</div>
          <div class="step-text">Start on the <code>📋 Instructions</code> tab to understand the color coding and sheet structure.</div>
        </div>
      </div>
      <div class="step">
        <div class="step-num">03</div>
        <div class="step-body">
          <div class="step-title">Fill in the Assumptions sheet</div>
          <div class="step-text">Enter unit rates, shrinkage %, salaries, meal cards, and CTC multipliers in the <strong>blue cells only</strong>.</div>
        </div>
      </div>
      <div class="step">
        <div class="step-num">04</div>
        <div class="step-body">
          <div class="step-title">Enter headcount by month</div>
          <div class="step-text">In the <code>👥 Headcount Plan</code> tab, enter your FTE count per role for each month. Overhead auto-fills.</div>
        </div>
      </div>
      <div class="step">
        <div class="step-num">05</div>
        <div class="step-body">
          <div class="step-title">Review results automatically</div>
          <div class="step-text">Check <code>💰 Salary &amp; Cost</code>, <code>📈 Revenue Forecast</code>, and <code>📉 P&amp;L Summary</code> — all calculated instantly.</div>
        </div>
      </div>
    </div>
  </div>
</section>

<section id="tips" class="tips-section">
  <div class="section-inner">
    <p class="section-tag">Pro tips</p>
    <h2>Get the most<br/>out of it.</h2>
    <div class="tips-grid">
      <div class="tip-card">
        <div class="tip-icon">📐</div>
        <div class="tip-title">Shrinkage is fully adjustable</div>
        <div class="tip-text">Edit each shrinkage component separately in the Assumptions sheet. Vacation, sick leave, training — each has its own line.</div>
      </div>
      <div class="tip-card">
        <div class="tip-icon">🏗️</div>
        <div class="tip-title">Overhead auto-calculates</div>
        <div class="tip-text">Team Leaders, QA, WFM, and Compliance are tracked separately from billable agents and update as headcount changes.</div>
      </div>
      <div class="tip-card">
        <div class="tip-icon">💼</div>
        <div class="tip-title">CTC multiplier</div>
        <div class="tip-text">Automatically adds employer social costs on top of gross salary. Just set the multiplier once and it applies everywhere.</div>
      </div>
      <div class="tip-card">
        <div class="tip-icon">🍽️</div>
        <div class="tip-title">Meal card calculation</div>
        <div class="tip-text">Calculated as daily rate × working days per month. Update the daily rate in Assumptions and it flows through automatically.</div>
      </div>
      <div class="tip-card">
        <div class="tip-icon">🔮</div>
        <div class="tip-title">Instant forecasting</div>
        <div class="tip-text">Change headcount numbers in future months — revenue and costs update instantly. Great for scenario planning.</div>
      </div>
      <div class="tip-card">
        <div class="tip-icon">🐍</div>
        <div class="tip-title">Customize with Python</div>
        <div class="tip-text">Download <code>generate_budget.py</code>, edit the config at the top, and run it to regenerate the entire workbook with your LOBs and roles.</div>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="section-inner">
    <p class="section-tag">Advanced</p>
    <h2>Customize with<br/>Python.</h2>
    <p class="section-desc">Want different languages, agent types, or overhead roles? Edit a few lines in the script and regenerate the whole workbook.</p>
    <div style="margin-top:2.5rem; background: var(--ink); border-radius: 8px; padding: 2rem; font-size: 0.8rem; line-height: 1.9; overflow-x: auto;">
      <div style="color: rgba(255,255,255,0.3); margin-bottom: 1rem; font-size: 0.7rem; letter-spacing: 0.08em;">INSTALL &amp; RUN</div>
      <div><span style="color:#ffd84d;">$</span> <span style="color:#00c471;">pip</span> <span style="color:white;">install openpyxl</span></div>
      <div><span style="color:#ffd84d;">$</span> <span style="color:#00c471;">python</span> <span style="color:white;">generate_budget.py</span></div>
      <div style="margin-top:1.2rem; color: rgba(255,255,255,0.3); font-size: 0.7rem; letter-spacing: 0.08em;">ADD A NEW LANGUAGE / LOB</div>
      <div style="margin-top:0.4rem; color: rgba(255,255,255,0.6);">UNIT_RATE_ROWS = [</div>
      <div style="color: rgba(255,255,255,0.6);">&nbsp;&nbsp;("Spanish – Voice Inbound", "Per Hour", 7.5),</div>
      <div style="color: #1a6fff;">&nbsp;&nbsp;("French – Chat Inbound",&nbsp;&nbsp; "Per Hour", 6.0),&nbsp;&nbsp;<span style="color:rgba(255,255,255,0.3)"># ← add here</span></div>
      <div style="color: rgba(255,255,255,0.6);">]</div>
    </div>
  </div>
</section>

<section id="download" class="download-section">
  <div class="section-inner">
    <p class="section-tag" style="color:rgba(255,255,255,0.6)">Free download</p>
    <h2>Ready to build<br/>your budget?</h2>
    <p class="section-desc">No sign-up. No paywall. Just download and start filling in blue cells.</p>
    <div class="download-btns">
      <a href="CC_Budget_Template.xlsx" class="btn btn-white" download>⬇ Excel Template (.xlsx)</a>
      <a href="generate_budget.py" class="btn btn-ghost" download>⬇ Python Script (.py)</a>
    </div>
  </div>
</section>

<footer>
  <p>CC Budget Tool &mdash; Free call center budget template &mdash; <a href="generate_budget.py">View source</a></p>
</footer>

<script>
  const steps = document.querySelectorAll('.step');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        setTimeout(() => e.target.classList.add('visible'), i * 100);
      }
    });
  }, { threshold: 0.2 });
  steps.forEach(s => observer.observe(s));
</script>

</body>
</html>
