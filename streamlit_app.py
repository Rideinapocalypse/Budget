"""
CC Budget & Forecast Tool - Streamlit App
Run with: streamlit run streamlit_app.py
Install:  pip install streamlit openpyxl pandas
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import copy
import urllib.request
import json
import math

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="CC Budget Tool", page_icon="📞", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background: #161b27; border: 1px solid #2a3347;
        border-radius: 8px; padding: 12px 16px;
    }
    div[data-testid="metric-container"] label { color: #5a6480 !important; font-size: 11px !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 22px !important; }
    .section-title {
        font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #5a6480;
        border-bottom: 1px solid #2a3347; padding-bottom: 6px;
        margin-bottom: 12px; margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

if "blocks" not in st.session_state:
    st.session_state.blocks = {m: [] for m in MONTHS}
if "active_month" not in st.session_state:
    st.session_state.active_month = "Jan"
if "attrition_rate" not in st.session_state:
    st.session_state.attrition_rate = 0.05
if "backfill_efficiency" not in st.session_state:
    st.session_state.backfill_efficiency = 0.50
# Overhead roles: TM, QM, OM — stored per month
if "overhead" not in st.session_state:
    st.session_state.overhead = {
        m: {
            "TM": {"ratio": 10, "hc_override": None, "salary": 55000},
            "QM": {"ratio": 20, "hc_override": None, "salary": 60000},
            "OM": {"ratio": 50, "hc_override": None, "salary": 80000},
        }
        for m in MONTHS
    }

@st.cache_data(ttl=300)
def fetch_live_fx():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        return round(data["rates"]["TRY"], 2), True
    except Exception:
        return 38.0, False

def fmt_eur(v): return f"€{v:,.0f}"
def fmt_try(v): return f"₺{v:,.0f}"
def fmt_pct(v): return f"{v*100:.1f}%"

def get_totals(month, g):
    total_rev_eur = total_cost_eur = total_cost_try = total_rev_try = total_hc = total_hrs = 0.0
    weighted_sal = weighted_fx = weighted_hrs = 0.0
    for b in st.session_state.blocks.get(month, []):
        raw_shrink = b["shrink_override"] if b.get("shrink_override") is not None else g["shrink"]
        shrink = max(0.0, min(0.99, raw_shrink if raw_shrink <= 1 else raw_shrink / 100))
        fx     = b["fx_override"]     if b.get("fx_override")     is not None else g["fx"]
        hours  = b["hours_override"]  if b.get("hours_override")  is not None else g["hours"]
        hc, sal, up = b.get("hc",0), b.get("salary",0), b.get("unit_price",0)
        eff          = hours * (1 - shrink)
        rev_eur      = hc * eff * up
        rev_try      = rev_eur * fx
        cost_try     = hc * sal * g["ctc"] * (1 + g["bonus_pct"]) + hc * g["meal"]
        cost_eur     = cost_try / fx if fx else 0
        total_rev_eur  += rev_eur;  total_rev_try  += rev_try
        total_cost_eur += cost_eur; total_cost_try += cost_try
        total_hc += hc; total_hrs += hc * eff
        weighted_sal += hc * sal
        weighted_fx  += hc * fx
        weighted_hrs += hc * eff

    # Per-block or global attrition rate
    att_rate   = st.session_state.attrition_rate
    bf_eff     = st.session_state.backfill_efficiency  # e.g. 0.50 = 50% productive

    # Exact fractional attrition & backfill
    attrition_hc = total_hc * att_rate          # e.g. 8 × 5% = 0.4
    backfill_hc  = attrition_hc                  # 1-for-1 replacement
    net_hc       = total_hc - attrition_hc

    # Weighted averages for backfill costing
    avg_sal = (weighted_sal / total_hc) if total_hc else 0
    avg_fx  = (weighted_fx  / total_hc) if total_hc else g["fx"]
    avg_eff = (weighted_hrs / total_hc) if total_hc else g["hours"] * (1 - g["shrink"])

    # Backfill cost: full salary (they're employed), partial hours due to training efficiency
    backfill_cost_try  = backfill_hc * avg_sal * g["ctc"] * (1 + g["bonus_pct"]) + backfill_hc * g["meal"]
    backfill_cost_eur  = backfill_cost_try / avg_fx if avg_fx else 0
    # Hours: backfill agents work but at reduced efficiency — counted in produced, not billed
    backfill_hrs       = backfill_hc * avg_eff * bf_eff

    total_cost_try_incl = total_cost_try + backfill_cost_try
    total_cost_eur_incl = total_cost_eur + backfill_cost_eur
    total_hrs_incl      = total_hrs + backfill_hrs

    # Overhead roles (TM/QM/OM) — pure cost, no hours, no revenue
    oh = calc_overhead(month, total_hc, g)
    oh_cost_eur = oh["total_cost_eur"]
    oh_cost_try = oh["total_cost_try"]

    grand_cost_eur = total_cost_eur_incl + oh_cost_eur
    grand_cost_try = total_cost_try_incl + oh_cost_try

    # Break-even: must cover all costs (prod + backfill + overhead) per billable hr
    breakeven_up = (grand_cost_eur / total_hrs) if total_hrs > 0 else 0

    return dict(
        rev=total_rev_eur,              rev_try=total_rev_try,
        cost=grand_cost_eur,            cost_try=grand_cost_try,
        cost_excl_backfill=total_cost_eur,
        backfill_cost_eur=backfill_cost_eur,
        backfill_cost_try=backfill_cost_try,
        oh_cost_eur=oh_cost_eur,        oh_cost_try=oh_cost_try,
        oh=oh,
        margin=total_rev_eur - grand_cost_eur,
        margin_try=total_rev_try - grand_cost_try,
        hc=total_hc,
        hrs=total_hrs_incl,
        hrs_billable=total_hrs,
        backfill_hrs=backfill_hrs,
        attrition_hc=attrition_hc,
        backfill_hc=backfill_hc,
        net_hc=net_hc,
        breakeven_up=breakeven_up,
    )

def calc_overhead(month, prod_hc, g):
    """Calculate overhead cost for TM/QM/OM roles for a given month."""
    oh     = st.session_state.overhead.get(month, {})
    result = {}
    total_cost_try = total_cost_eur = 0.0
    for role, defaults in [("TM",{"ratio":10,"salary":55000}),
                            ("QM",{"ratio":20,"salary":60000}),
                            ("OM",{"ratio":50,"salary":80000})]:
        cfg      = oh.get(role, defaults)
        ratio    = cfg.get("ratio", defaults["ratio"])
        sal      = cfg.get("salary", defaults["salary"])
        override = cfg.get("hc_override")
        # HC: manual override wins, else ratio-based (at least 1 if prod_hc > 0)
        if override is not None:
            hc = override
        else:
            hc = prod_hc / ratio if ratio > 0 else 0  # exact fractional
        cost_try = hc * sal * g["ctc"] * (1 + g["bonus_pct"]) + hc * g["meal"]
        cost_eur = cost_try / g["fx"] if g["fx"] else 0
        result[role] = dict(hc=hc, salary=sal, ratio=ratio,
                            cost_try=cost_try, cost_eur=cost_eur,
                            manual=override is not None)
        total_cost_try += cost_try
        total_cost_eur += cost_eur
    result["total_cost_try"] = total_cost_try
    result["total_cost_eur"] = total_cost_eur
    return result

# openpyxl helpers
def bdr():
    s = Side(style="thin", color="AAAAAA")
    return Border(left=s, right=s, top=s, bottom=s)

def wcell(ws, r, c, v, bold=False, bg=None, fg="000000", fmt=None, italic=False):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = Font(name="Calibri", bold=bold, italic=italic, color=fg, size=11)
    cell.border = bdr()
    cell.alignment = Alignment(horizontal="left", vertical="center")
    if bg: cell.fill = PatternFill("solid", start_color=bg)
    if fmt: cell.number_format = fmt
    return cell

def hdr(ws, r, c, v):  return wcell(ws, r, c, v, bold=True,   bg="1F4E79", fg="FFFFFF")
def inp(ws, r, c, v, fmt=None): return wcell(ws, r, c, v, bg="DDEEFF", fg="00008B", fmt=fmt)
def note(ws, r, c, v): return wcell(ws, r, c, v, italic=True,  fg="888888")

def set_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

# ── Template builder (single sheet) ─────────────────────────
def build_template(gh, gs, gfx, gctc, gbp, gm):
    wb = Workbook(); wb.remove(wb.active)

    # ── Settings sheet ────────────────────────────────────────
    ws_s = wb.create_sheet("Settings"); set_widths(ws_s, [35, 22])
    hdr(ws_s,1,1,"Setting"); hdr(ws_s,1,2,"Value")
    for ri,(lbl,val) in enumerate([
        ("Worked Hours/Agent/Month", gh), ("Shrinkage %", gs),
        ("FX Rate (EUR=TRY)", gfx), ("CTC Multiplier", gctc),
        ("Bonus % of Base", gbp), ("Meal Card (TRY/mo)", gm),
    ], start=2):
        wcell(ws_s,ri,1,lbl); inp(ws_s,ri,2,val,fmt="#,##0.00")

    # ── Single data sheet with all months ────────────────────
    ws = wb.create_sheet("Budget Data")
    set_widths(ws, [10, 18, 10, 22, 22, 22, 16, 18, 18, 14, 22])

    col_hdrs  = ["Month","Language","HC","Base Salary (TRY)","Unit Price (EUR/hr)",
                 "Shrinkage Override","FX Override","Hours Override",
                 "Attrition Target %","Backfill HC","Backfill Salary (TRY)"]
    col_hints = ["Jan/Feb/etc","e.g. DE, EN, TR","agents","monthly gross TRY","billable EUR/hr",
                 "blank=global","blank=global","blank=global",
                 "e.g. 0.05=5%","auto=HC×attrition%","blank=same as prod salary"]

    # Title
    ws["A1"].value = "CC Budget Tool - Data Template"
    ws["A1"].font  = Font(name="Calibri", bold=True, size=13, color="1F4E79")
    ws["A2"].value = "Fill in BLUE cells below. Month column must match exactly: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec"
    ws["A2"].font  = Font(name="Calibri", italic=True, color="444444", size=10)

    # Header row
    for ci, h in enumerate(col_hdrs, 1): hdr(ws, 3, ci, h)
    # Hint row
    for ci, ht in enumerate(col_hints, 1): note(ws, 4, ci, ht)

    # Pre-fill existing blocks grouped by month, else 3 blank rows per month
    ri = 5
    for m in MONTHS:
        existing = st.session_state.blocks.get(m, [])
        rows = existing or [{"lang":"","hc":0,"salary":0,"unit_price":0,
                             "shrink_override":None,"fx_override":None,"hours_override":None}]
        for b in rows:
            hc_val   = b.get("hc", 0)
            att_rate = st.session_state.attrition_rate
            bf_hc    = hc_val * att_rate  # exact fraction
            vals = [m, b.get("lang",""), hc_val, b.get("salary",0), b.get("unit_price",0),
                    b["shrink_override"] if b.get("shrink_override") is not None else "",
                    b["fx_override"]     if b.get("fx_override")     is not None else "",
                    b["hours_override"]  if b.get("hours_override")  is not None else "",
                    att_rate, bf_hc, b.get("salary",0)]
            for ci, v in enumerate(vals, 1): inp(ws, ri, ci, v)
            ri += 1
        # blank separator row between months
        ri += 1

    buf = BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

# ── Data export builder ───────────────────────────────────────
def build_export(g):
    wb = Workbook(); wb.remove(wb.active)

    # Summary
    ws = wb.create_sheet("Summary"); set_widths(ws, [12,18,18,18,12,10])
    for ci, h in enumerate(["Month","Revenue (EUR)","Cost (EUR)","Margin (EUR)","Margin %","HC"],1):
        hdr(ws,1,ci,h)
    fy = {"rev":0,"cost":0,"margin":0}
    for ri, m in enumerate(MONTHS, start=2):
        t = get_totals(m, g)
        fy["rev"]+=t["rev"]; fy["cost"]+=t["cost"]; fy["margin"]+=t["margin"]
        row = [m, round(t["rev"],2), round(t["cost"],2), round(t["margin"],2),
               round(t["margin"]/t["rev"],4) if t["rev"] else 0, int(t["hc"])]
        for ci, v in enumerate(row, 1):
            c = ws.cell(row=ri, column=ci, value=v); c.border = bdr()
            if ci in (2,3,4): c.number_format = "#,##0.00"
            if ci == 5:       c.number_format = "0.0%"
    for ci, v in enumerate([
        "Full Year", round(fy["rev"],2), round(fy["cost"],2), round(fy["margin"],2),
        round(fy["margin"]/fy["rev"],4) if fy["rev"] else 0, ""
    ], 1):
        c = wcell(ws, len(MONTHS)+2, ci, v, bold=True, bg="E8F0FE")
        if ci in (2,3,4): c.number_format = "#,##0.00"
        if ci == 5:       c.number_format = "0.0%"

    # Settings
    ws2 = wb.create_sheet("Settings"); set_widths(ws2, [35,22])
    hdr(ws2,1,1,"Setting"); hdr(ws2,1,2,"Value")
    for ri,(lbl,val) in enumerate([
        ("Worked Hours/Agent/Month",g["hours"]),("Shrinkage %",g["shrink"]),
        ("FX Rate (EUR=TRY)",g["fx"]),("CTC Multiplier",g["ctc"]),
        ("Bonus % of Base",g["bonus_pct"]),("Meal Card (TRY/mo)",g["meal"]),
    ], start=2):
        wcell(ws2,ri,1,lbl); inp(ws2,ri,2,val,fmt="#,##0.00")

    # Per month
    dh = ["Language","HC","Base Salary (TRY)","Unit Price (EUR/hr)",
          "Shrinkage Override","FX Override","Hours Override",
          "Revenue (EUR)","Cost (EUR)","Margin (EUR)"]
    for m in MONTHS:
        ws3 = wb.create_sheet(m); set_widths(ws3, [18,8,20,20,20,14,18,16,16,16])
        for ci, h in enumerate(dh, 1): hdr(ws3,1,ci,h)
        for ri, b in enumerate(st.session_state.blocks.get(m,[]), start=2):
            shrink = b["shrink_override"] if b.get("shrink_override") is not None else g["shrink"]
            fx     = b["fx_override"]     if b.get("fx_override")     is not None else g["fx"]
            hours  = b["hours_override"]  if b.get("hours_override")  is not None else g["hours"]
            hc,sal,up = b.get("hc",0),b.get("salary",0),b.get("unit_price",0)
            eff = hours*(1-shrink); rev = hc*eff*up
            cost = (hc*sal*g["ctc"]*(1+g["bonus_pct"])+hc*g["meal"])/fx if fx else 0
            row = [b.get("lang",""),hc,sal,up,
                   b["shrink_override"] if b.get("shrink_override") is not None else "",
                   b["fx_override"]     if b.get("fx_override")     is not None else "",
                   b["hours_override"]  if b.get("hours_override")  is not None else "",
                   round(rev,2),round(cost,2),round(rev-cost,2)]
            for ci, v in enumerate(row, 1):
                c = ws3.cell(row=ri,column=ci,value=v); c.border=bdr()
                if ci in (8,9,10): c.number_format="#,##0.00"

    buf = BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📞 CCBudget")
    st.caption("Call Center Forecast Tool")
    st.divider()

    st.markdown('<div class="section-title">Global Inputs</div>', unsafe_allow_html=True)
    g_hours  = st.number_input("Worked Hours / Agent / Month", value=180, step=1, min_value=1)
    g_shrink = st.slider("Shrinkage % (default)", 0.0, 0.5, 0.15, 0.01, format="%.0f%%")

    live_fx, fx_ok = fetch_live_fx()
    if fx_ok:
        st.caption(f"🟢 Live EUR/TRY: **{live_fx}** (auto-fetched, editable below)")
    else:
        st.caption("🔴 Could not fetch live rate — using fallback")
    g_fx = st.number_input("FX Rate (1 EUR = TRY)", value=live_fx, step=0.5, min_value=0.1)

    st.divider()
    st.markdown('<div class="section-title">Global Cost Drivers</div>', unsafe_allow_html=True)
    g_ctc       = st.number_input("Salary Multiplier (CTC)", value=1.70, step=0.05, min_value=1.0)
    g_bonus_pct = st.number_input("Bonus % of Base Salary",  value=0.10, step=0.01, min_value=0.0)
    g_meal      = st.number_input("Meal Card / Agent / Month (TRY)", value=5850, step=50, min_value=0)

    st.divider()
    st.markdown('<div class="section-title">Attrition & Backfill</div>', unsafe_allow_html=True)
    attrition_pct = st.slider("Monthly Attrition %", 0.0, 0.30, 0.05, 0.005, format="%.1f%%",
                               help="Fraction of HC lost per month. Backfill hired 1-for-1.")
    bf_efficiency = st.slider("Backfill Training Efficiency %", 0.0, 1.0, 0.50, 0.05, format="%.0f%%",
                               help="How productive backfill agents are while in training. 50% = half speed. Hours are counted but generate no revenue.")
    st.session_state.attrition_rate       = attrition_pct
    st.session_state.backfill_efficiency  = bf_efficiency

    g = dict(hours=g_hours, shrink=g_shrink, fx=g_fx,
             ctc=g_ctc, bonus_pct=g_bonus_pct, meal=g_meal)

    st.divider()
    st.markdown('<div class="section-title">Data Import / Export</div>', unsafe_allow_html=True)

    st.download_button(
        label="📋 Download Blank Template",
        data=build_template(g_hours, g_shrink, g_fx, g_ctc, g_bonus_pct, g_meal),
        file_name="CC_Budget_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        help="Fillable Excel template — fill blue cells, then import.",
    )
    st.download_button(
        label="⬇ Export Data to Excel",
        data=build_export(g),
        file_name="CC_Budget_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary",
    )

    st.divider()
    uploaded = st.file_uploader("⬆ Import Excel", type=["xlsx"])
    if uploaded:
        try:
            xls = pd.ExcelFile(uploaded)
            def sf(v):
                try: return float(v) if str(v).strip() not in ("","nan") else None
                except: return None

            loaded = 0
            # Support both old multi-sheet format and new single-sheet format
            if "Budget Data" in xls.sheet_names:
                # New single-sheet format
                df_all = pd.read_excel(xls, sheet_name="Budget Data", header=2)
                df_all.columns = [str(c).strip() for c in df_all.columns]
                df_all = df_all[pd.to_numeric(df_all.get("HC", pd.Series()), errors="coerce").notna()]
                new_blocks = {m: [] for m in MONTHS}
                for _, row in df_all.iterrows():
                    m = str(row.get("Month","")).strip()
                    if m not in MONTHS: continue
                    new_blocks[m].append({
                        "lang":            str(row.get("Language","")).strip() if pd.notna(row.get("Language","")) else "",
                        "hc":              int(float(row["HC"])) if pd.notna(row.get("HC")) else 0,
                        "salary":          float(row.get("Base Salary (TRY)",0)) if pd.notna(row.get("Base Salary (TRY)")) else 0,
                        "unit_price":      float(row.get("Unit Price (EUR/hr)",0)) if pd.notna(row.get("Unit Price (EUR/hr)")) else 0,
                        "shrink_override": sf(row.get("Shrinkage Override","")),
                        "fx_override":     sf(row.get("FX Override","")),
                        "hours_override":  sf(row.get("Hours Override","")),
                    })
                    loaded += 1
                st.session_state.blocks = new_blocks
            else:
                # Legacy per-month sheet format
                for m in MONTHS:
                    if m not in xls.sheet_names: continue
                    df_m = pd.read_excel(xls, sheet_name=m)
                    if "HC" in df_m.columns:
                        df_m = df_m[pd.to_numeric(df_m["HC"], errors="coerce").notna()]
                    blocks = []
                    for _, row in df_m.iterrows():
                        blocks.append({
                            "lang":            str(row.get("Language","")).strip() if pd.notna(row.get("Language","")) else "",
                            "hc":              int(float(row["HC"])) if pd.notna(row.get("HC")) else 0,
                            "salary":          float(row.get("Base Salary (TRY)",0)) if pd.notna(row.get("Base Salary (TRY)")) else 0,
                            "unit_price":      float(row.get("Unit Price (EUR/hr)",0)) if pd.notna(row.get("Unit Price (EUR/hr)")) else 0,
                            "shrink_override": sf(row.get("Shrinkage Override","")),
                            "fx_override":     sf(row.get("FX Override","")),
                            "hours_override":  sf(row.get("Hours Override","")),
                        })
                    st.session_state.blocks[m] = blocks
                    loaded += len(blocks)
            st.success(f"✅ Imported {loaded} blocks across all months!")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# ── MAIN ──────────────────────────────────────────────────────
st.markdown("## 📞 CC Budget & Forecast")

cols_tabs = st.columns(12)
for i, m in enumerate(MONTHS):
    with cols_tabs[i]:
        if st.button(m, use_container_width=True,
                     type="primary" if m == st.session_state.active_month else "secondary"):
            st.session_state.active_month = m
            st.rerun()

active = st.session_state.active_month
st.markdown(f"### {active}")

t = get_totals(active, g)
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Revenue (EUR)", fmt_eur(t["rev"]),
          delta=fmt_try(t["rev_try"]) + " TRY", delta_color="off")
k2.metric("Cost (EUR)", fmt_eur(t["cost"]),
          delta=f'{fmt_try(t["cost_try"])} TRY  |  OH: €{t["oh_cost_eur"]:,.0f}',
          delta_color="off", help="Includes production, backfill & overhead (TM/QM/OM)")
gm_pct = fmt_pct(t["margin"]/t["rev"]) if t["rev"] else "0%"
k3.metric(f"Gross Margin (EUR)  {gm_pct}", fmt_eur(t["margin"]),
          delta=f'{fmt_try(t["margin_try"])} TRY  |  {gm_pct}',
          delta_color="normal")
attr_hc   = t["attrition_hc"]
net_hc    = t["net_hc"]
attr_pct  = fmt_pct(attrition_pct)
k4.metric("Total HC",
          f"{int(t['hc'])} agents",
          delta=f"-{attr_hc} attrition ({attr_pct})",
          delta_color="inverse",
          help=f"Net HC after {attr_pct} attrition: {net_hc} agents")
k5.metric("Produced Hrs",
          f"{t['hrs']:,.0f} hrs",
          delta=f"Billable: {t['hrs_billable']:,.0f}  |  Backfill: {t['backfill_hrs']:,.0f}",
          delta_color="off",
          help="Total hours worked incl. backfill trainees. Only billable hours generate revenue.")

# Break-even banner
if t["hc"] > 0:
    be   = t["breakeven_up"]
    avg_up = t["rev"] / t["hrs_billable"] if t["hrs_billable"] else 0
    be_gap = avg_up - be
    be_color = "#10b981" if be_gap >= 0 else "#ef4444"
    be_icon  = "✅" if be_gap >= 0 else "⚠️"
    st.markdown(
        f"<div style='background:#12192a;border:1px solid #2a3347;border-radius:6px;"
        f"padding:8px 18px;margin-top:-8px;margin-bottom:4px;"
        f"display:flex;justify-content:space-between;align-items:center;font-size:13px'>"
        f"<span style='color:#5a6480'>Break-even Unit Price</span>"
        f"<span style='color:{be_color};font-weight:700'>{be_icon} €{be:.2f}/hr break-even"
        f"&nbsp;·&nbsp;avg selling €{avg_up:.2f}/hr"
        f"&nbsp;·&nbsp;gap <b>€{be_gap:+.2f}/hr</b></span>"
        f"</div>", unsafe_allow_html=True
    )

# ── Attrition warning banner ─────────────────────────────────
if t["hc"] > 0:
    attr_hc  = t["attrition_hc"]
    net_hc   = t["net_hc"]
    color    = "#f59e0b" if attr_hc > 0 else "#10b981"
    icon     = "⚠️" if attr_hc > 0 else "✅"
    st.markdown(
        f"<div style='background:#1e2535;border:1px solid {color};border-radius:6px;"
        f"padding:10px 18px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center'>"
        f"<span style='color:{color};font-weight:600'>{icon} Attrition Forecast — {active}</span>"
        f"<span style='color:#e8edf5'>"
        f"Starting HC: <b>{int(t['hc'])}</b> &nbsp;|&nbsp; "
        f"Attrition ({fmt_pct(attrition_pct)}): <b style='color:#ef4444'>-{attr_hc}</b> &nbsp;|&nbsp; "
        f"Net HC End of Month: <b style='color:#10b981'>{net_hc}</b>"
        f"</span></div>",
        unsafe_allow_html=True
    )

st.divider()

with st.expander("📋 Copy Month to Multiple Months"):
    cc1, cc2 = st.columns([2, 4])
    copy_from = cc1.selectbox("Copy FROM", MONTHS, index=MONTHS.index(active), key="copy_from")

    with cc2:
        st.markdown("**Copy TO** (select one or more)")
        dest_cols = st.columns(6)
        selected_targets = []
        for mi, m in enumerate(MONTHS):
            col = dest_cols[mi % 6]
            disabled = (m == copy_from)
            checked = col.checkbox(
                m,
                key=f"copy_target_{m}",
                value=False,
                disabled=disabled,
                help="Same as source" if disabled else f"Copy to {m}",
            )
            if checked and not disabled:
                selected_targets.append(m)

    st.markdown("")
    btn_col, info_col = st.columns([1, 4])
    if btn_col.button("▶ Copy", use_container_width=True, type="primary"):
        if not selected_targets:
            st.error("Please select at least one destination month.")
        else:
            for m in selected_targets:
                st.session_state.blocks[m] = copy.deepcopy(st.session_state.blocks[copy_from])
            targets_str = ", ".join(selected_targets)
            st.success(f"✅ Copied **{copy_from}** → {targets_str}")
            st.rerun()
    with info_col:
        if selected_targets:
            st.info(f"Will copy **{copy_from}** → {', '.join(selected_targets)}")
        else:
            st.caption("No destination months selected yet.")

st.markdown('<div class="section-title">Production Blocks</div>', unsafe_allow_html=True)
blocks = st.session_state.blocks[active]

if st.button("+ Add Production Block", type="secondary"):
    blocks.append({"lang":"","hc":0,"salary":0,"unit_price":0,
                   "shrink_override":None,"fx_override":None,"hours_override":None})
    st.rerun()

blocks_to_delete = []
for i, b in enumerate(blocks):
    raw_shrink = b["shrink_override"] if b.get("shrink_override") is not None else g_shrink
    shrink = max(0.0, min(0.99, raw_shrink if raw_shrink <= 1 else raw_shrink / 100))
    fx     = b["fx_override"]     if b.get("fx_override")     is not None else g_fx
    hours  = b["hours_override"]  if b.get("hours_override")  is not None else g_hours
    hc, salary, up = b.get("hc",0), b.get("salary",0), b.get("unit_price",0)
    eff            = hours * (1 - shrink)
    rev_eur        = hc * eff * up
    rev_try        = rev_eur * fx
    cost_try_total = hc * salary * g_ctc * (1 + g_bonus_pct) + hc * g_meal
    cost_e         = cost_try_total / fx if fx else 0
    margin         = rev_eur - cost_e
    margin_try     = rev_try - cost_try_total
    label  = b.get("lang") or f"Block #{i+1}"
    title  = f"Block #{i+1} — {label} | HC: {hc} | Rev: {fmt_eur(rev_eur)} ({fmt_try(rev_try)}) | Margin: {fmt_eur(margin)}"

    with st.expander(title, expanded=True):
        r1c1,r1c2,r1c3,r1c4,r1c5 = st.columns([2,1,2,2,1])
        new_lang = r1c1.text_input("Language / Label", value=b.get("lang",""),
                                    key=f"lang_{active}_{i}", placeholder="e.g. DE, EN, TR")
        new_hc   = r1c2.number_input("HC", value=int(b.get("hc",0)), min_value=0, step=1,
                                      key=f"hc_{active}_{i}")
        new_sal  = r1c3.number_input("Base Salary (TRY/mo)", value=float(b.get("salary",0)),
                                      min_value=0.0, step=100.0, key=f"sal_{active}_{i}")
        new_up   = r1c4.number_input("Unit Price (EUR/hr)", value=float(b.get("unit_price",0)),
                                      min_value=0.0, step=0.1, key=f"up_{active}_{i}")
        if r1c5.button("🗑 Remove", key=f"del_{active}_{i}", use_container_width=True):
            blocks_to_delete.append(i)

        r2c1,r2c2,r2c3,r2c4,r2c5,r2c6 = st.columns([2,2,2,2,2,2])
        shr_raw = r2c1.text_input(f"Shrinkage Override (global: {g_shrink*100:.0f}%)",
                                   value="" if b.get("shrink_override") is None else str(b["shrink_override"]),
                                   key=f"shr_{active}_{i}", placeholder="blank = global")
        fx_raw  = r2c2.text_input(f"FX Override (global: {g_fx})",
                                   value="" if b.get("fx_override") is None else str(b["fx_override"]),
                                   key=f"fx_{active}_{i}", placeholder="blank = global")
        hr_raw  = r2c3.text_input(f"Hours Override (global: {g_hours})",
                                   value="" if b.get("hours_override") is None else str(b["hours_override"]),
                                   key=f"hr_{active}_{i}", placeholder="blank = global")
        att_raw = r2c4.text_input(f"Attrition Override (global: {attrition_pct*100:.1f}%)",
                                   value="" if b.get("attrition_override") is None else str(b["attrition_override"]),
                                   key=f"att_{active}_{i}", placeholder="blank = global",
                                   help="Override attrition rate for this block only e.g. 0.08 for 8%")
        # ── Cost breakdown ────────────────────────────────────
        ctc_cost_try     = hc * salary * g_ctc * (1 + g_bonus_pct)
        meal_cost_try    = hc * g_meal
        # per-block backfill
        # Per-block attrition override or global
        raw_att          = b.get("attrition_override")
        blk_att          = raw_att if raw_att is not None else st.session_state.attrition_rate
        blk_att          = max(0.0, min(1.0, blk_att if blk_att <= 1 else blk_att / 100))
        b_hc             = hc * blk_att
        b_cost_try       = b_hc * salary * g_ctc * (1 + g_bonus_pct) + b_hc * g_meal
        b_cost_eur       = b_cost_try / fx if fx else 0
        b_hrs            = b_hc * eff * st.session_state.backfill_efficiency
        total_cost_incl  = cost_try_total + b_cost_try
        margin_incl_eur  = rev_eur - (cost_e + b_cost_eur)
        margin_incl_try  = rev_try - total_cost_incl
        # Break-even unit price for this block
        total_billable_hrs = hc * eff
        blk_breakeven    = (cost_e + b_cost_eur) / total_billable_hrs if total_billable_hrs else 0

        st.markdown("---")
        bd1, bd2, bd3, bd4, bd5, bd6 = st.columns(6)
        with bd1:
            st.markdown("**🕐 Eff. Hrs / Agent**")
            st.markdown(f"<span style='color:#8b96b0;font-size:15px;font-weight:600'>{eff:.1f} hrs</span>", unsafe_allow_html=True)
            st.caption(f"{hours}h × (1 - {shrink*100:.0f}%)")
        with bd2:
            st.markdown("**💸 Salary CTC**")
            st.markdown(f"<span style='color:#f59e0b;font-size:15px;font-weight:600'>₺{ctc_cost_try:,.0f}</span>", unsafe_allow_html=True)
            st.caption(f"₺{salary:,.0f} × {g_ctc} × (1+{g_bonus_pct*100:.0f}%)")
        with bd3:
            st.markdown("**🍽️ Meal Cards**")
            st.markdown(f"<span style='color:#f59e0b;font-size:15px;font-weight:600'>₺{meal_cost_try:,.0f}</span>", unsafe_allow_html=True)
            st.caption(f"{hc} HC × ₺{g_meal:,.0f}")
        with bd4:
            st.markdown("**🔄 Backfill Cost**")
            st.markdown(f"<span style='color:#8b5cf6;font-size:15px;font-weight:600'>₺{b_cost_try:,.0f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#8b5cf6;font-size:13px'>{fmt_eur(b_cost_eur)}</span>", unsafe_allow_html=True)
            st.caption(f"{b_hc:.2f} HC · {b_hrs:.0f} hrs @ {st.session_state.backfill_efficiency*100:.0f}% efficiency · no revenue")
        with bd5:
            st.markdown("**💰 Total Cost**")
            st.markdown(f"<span style='color:#ef4444;font-size:15px;font-weight:600'>₺{total_cost_incl:,.0f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#ef4444;font-size:13px'>{fmt_eur(cost_e + b_cost_eur)}</span>", unsafe_allow_html=True)
            st.caption("incl. backfill")
        with bd6:
            st.markdown("**📈 Revenue**")
            st.markdown(f"<span style='color:#10b981;font-size:15px;font-weight:600'>₺{rev_try:,.0f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#10b981;font-size:13px'>{fmt_eur(rev_eur)}</span>", unsafe_allow_html=True)
            st.caption(f"{hc} HC × {eff:.1f}h × €{up}/hr")
        # Break-even insight
        be_color = "#10b981" if up >= blk_breakeven else "#ef4444"
        be_label = "✅ Above break-even" if up >= blk_breakeven else "⚠️ Below break-even"
        st.markdown(
            f"<div style='background:#12192a;border:1px solid #2a3347;border-radius:5px;"
            f"padding:6px 14px;margin-top:6px;font-size:12px;color:#8b96b0'>"
            f"Break-even price: <b style='color:{be_color}'>€{blk_breakeven:.2f}/hr</b>"
            f"&nbsp;&nbsp;·&nbsp;&nbsp;Current: <b style='color:{be_color}'>€{up:.2f}/hr</b>"
            f"&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{be_color}'>{be_label}</span>"
            f"</div>", unsafe_allow_html=True
        )

        margin_color = "#10b981" if margin_incl_eur >= 0 else "#ef4444"
        st.markdown(
            f"<div style='background:#1e2535;border:1px solid #2a3347;border-radius:6px;"
            f"padding:10px 16px;margin-top:8px;display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='color:#8b96b0;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em'>"
            f"Gross Margin <span style='color:#8b5cf6;font-weight:400'>(incl. backfill)</span></span>"
            f"<span style='color:{margin_color};font-size:20px;font-weight:700'>{fmt_eur(margin_incl_eur)}"
            f"&nbsp;&nbsp;<span style='font-size:14px'>₺{margin_incl_try:,.0f}</span>"
            f"&nbsp;&nbsp;<span style='font-size:13px'>({fmt_pct(margin_incl_eur/rev_eur) if rev_eur else '—'})</span></span>"
            f"</div>",
            unsafe_allow_html=True
        )

        blocks[i].update({
            "lang": new_lang, "hc": new_hc, "salary": new_sal, "unit_price": new_up,
            "shrink_override":    float(shr_raw) if shr_raw.strip() else None,
            "fx_override":        float(fx_raw)  if fx_raw.strip()  else None,
            "hours_override":     float(hr_raw)  if hr_raw.strip()  else None,
            "attrition_override": float(att_raw) if att_raw.strip() else None,
        })

if blocks_to_delete:
    for idx in sorted(blocks_to_delete, reverse=True):
        blocks.pop(idx)
    st.rerun()

# ── Overhead Roles ───────────────────────────────────────────
st.divider()
st.markdown("### 🏢 Overhead Roles")
st.caption("TM / QM / OM — cost only, not billable. HC auto-calculated from production HC via span-of-control ratio, or set manually.")

oh_data   = st.session_state.overhead[active]
prod_hc_now = t["hc"]  # current month production HC for ratio display

oh_cols = st.columns(3)
ROLE_META = {
    "TM": {"icon":"👥", "label":"Team Manager",       "default_ratio":10, "default_sal":55000},
    "QM": {"icon":"🎯", "label":"Quality Manager",    "default_ratio":20, "default_sal":60000},
    "OM": {"icon":"⚙️", "label":"Operations Manager", "default_ratio":50, "default_sal":80000},
}

for col, (role, meta) in zip(oh_cols, ROLE_META.items()):
    cfg = oh_data.setdefault(role, {
        "ratio": meta["default_ratio"],
        "hc_override": None,
        "salary": meta["default_sal"],
    })
    with col:
        st.markdown(f"**{meta['icon']} {role} — {meta['label']}**")
        new_sal   = st.number_input(f"Base Salary TRY/mo ({role})",
                                     value=float(cfg.get("salary", meta["default_sal"])),
                                     step=1000.0, min_value=0.0, key=f"oh_sal_{active}_{role}")
        new_ratio = st.number_input(f"Span of Control (1 {role} per N agents)",
                                     value=int(cfg.get("ratio", meta["default_ratio"])),
                                     step=1, min_value=1, key=f"oh_ratio_{active}_{role}",
                                     help=f"Auto HC = {prod_hc_now} ÷ {cfg.get('ratio', meta['default_ratio'])} = {prod_hc_now / cfg.get('ratio', meta['default_ratio']):.2f}")
        override_raw = st.text_input(f"HC Override (blank = auto)",
                                      value="" if cfg.get("hc_override") is None else str(cfg["hc_override"]),
                                      key=f"oh_hc_{active}_{role}",
                                      placeholder=f"auto: {prod_hc_now / new_ratio:.2f}")
        # Calc display
        hc_val    = float(override_raw) if override_raw.strip() else prod_hc_now / new_ratio
        cost_try  = hc_val * new_sal * g_ctc * (1 + g_bonus_pct) + hc_val * g_meal
        cost_eur  = cost_try / g_fx if g_fx else 0
        st.markdown(
            f"<div style='background:#1e2535;border:1px solid #2a3347;border-radius:5px;"
            f"padding:8px 12px;margin-top:4px;font-size:12px'>"
            f"<span style='color:#8b96b0'>HC: </span><b style='color:#e8edf5'>{hc_val:.2f}</b>"
            f"&nbsp;·&nbsp;<span style='color:#8b96b0'>Cost: </span>"
            f"<b style='color:#ef4444'>₺{cost_try:,.0f}</b>"
            f"&nbsp;/&nbsp;<b style='color:#ef4444'>€{cost_eur:,.0f}</b>"
            f"</div>", unsafe_allow_html=True
        )
        # Save state
        oh_data[role]["salary"]      = new_sal
        oh_data[role]["ratio"]       = new_ratio
        oh_data[role]["hc_override"] = float(override_raw) if override_raw.strip() else None

# Overhead summary bar
oh_now = calc_overhead(active, prod_hc_now, g)
oh_total_try = oh_now["total_cost_try"]
oh_total_eur = oh_now["total_cost_eur"]
oh_hc_total  = sum(oh_now[r]["hc"] for r in ROLE_META)
st.markdown(
    f"<div style='background:#1e2535;border:1px solid #8b5cf6;border-radius:6px;"
    f"padding:10px 18px;margin-top:8px;display:flex;justify-content:space-between;align-items:center'>"
    f"<span style='color:#8b5cf6;font-weight:600'>🏢 Total Overhead Cost — {active}</span>"
    f"<span style='color:#e8edf5'>"
    f"TM: <b>{oh_now['TM']['hc']:.2f} HC</b> &nbsp;|&nbsp; "
    f"QM: <b>{oh_now['QM']['hc']:.2f} HC</b> &nbsp;|&nbsp; "
    f"OM: <b>{oh_now['OM']['hc']:.2f} HC</b> &nbsp;|&nbsp; "
    f"Total: <b style='color:#ef4444'>₺{oh_total_try:,.0f}</b> / "
    f"<b style='color:#ef4444'>€{oh_total_eur:,.0f}</b>"
    f"</span></div>", unsafe_allow_html=True
)

st.divider()
st.markdown("### 📉 P&L Summary — Full Year")

fy = {"rev":0,"rev_try":0,"cost":0,"cost_try":0,"margin":0,"margin_try":0}
month_data = {}
for m in MONTHS:
    mt = get_totals(m, g)
    month_data[m] = mt
    for k in fy: fy[k] += mt[k]

pnl_eur = {"Line Item": ["Revenue (EUR)","  Prod. Cost (EUR)","  Backfill Cost (EUR)","Total Cost (EUR)","Gross Margin (EUR)","Margin %","HC","Attrition (-)","Backfill HC","Net HC"]}
pnl_try = {"Line Item": ["Revenue (TRY)","  Prod. Cost (TRY)","  Backfill Cost (TRY)","Total Cost (TRY)","Gross Margin (TRY)","Margin %","HC","Attrition (-)","Backfill HC","Net HC"]}
for m in MONTHS:
    mt = month_data[m]
    prod_cost_try = mt["cost_try"] - mt["backfill_cost_try"]
    pnl_eur[m] = [
        fmt_eur(mt["rev"]),
        fmt_eur(mt["cost_excl_backfill"]),
        fmt_eur(mt["backfill_cost_eur"]),
        fmt_eur(mt["cost"]),
        fmt_eur(mt["margin"]),
        fmt_pct(mt["margin"]/mt["rev"]) if mt["rev"] else "—",
        int(mt["hc"]), f'-{mt["attrition_hc"]:.2f}', f'{mt["backfill_hc"]:.2f}', f'{mt["net_hc"]:.2f}',
    ]
    pnl_try[m] = [
        fmt_try(mt["rev_try"]),
        fmt_try(prod_cost_try),
        fmt_try(mt["backfill_cost_try"]),
        fmt_try(mt["cost_try"]),
        fmt_try(mt["margin_try"]),
        fmt_pct(mt["margin_try"]/mt["rev_try"]) if mt["rev_try"] else "—",
        int(mt["hc"]), f'-{mt["attrition_hc"]:.2f}', f'{mt["backfill_hc"]:.2f}', f'{mt["net_hc"]:.2f}',
    ]
fy_prod_cost_try = fy["cost_try"] - sum(month_data[m]["backfill_cost_try"] for m in MONTHS)
fy_backfill_eur  = sum(month_data[m]["backfill_cost_eur"] for m in MONTHS)
fy_backfill_try  = sum(month_data[m]["backfill_cost_try"] for m in MONTHS)
fy_excl          = sum(month_data[m]["cost_excl_backfill"] for m in MONTHS)
fy_hrs_bill  = sum(month_data[m]["hrs_billable"] for m in MONTHS)
fy_hrs_bf    = sum(month_data[m]["backfill_hrs"] for m in MONTHS)
fy_hrs_tot   = sum(month_data[m]["hrs"] for m in MONTHS)
fy_be        = fy["cost"] / fy_hrs_bill if fy_hrs_bill else 0
fy_avg_up    = fy["rev"]  / fy_hrs_bill if fy_hrs_bill else 0
pnl_eur["Full Year"] = [fmt_eur(fy["rev"]), fmt_eur(fy_excl), fmt_eur(fy_backfill_eur),
                         fmt_eur(fy["cost"]), fmt_eur(fy["margin"]),
                         fmt_pct(fy["margin"]/fy["rev"]) if fy["rev"] else "—",
                         f'€{fy_be:.2f}', f'€{fy_avg_up:.2f}',
                         "","","","",
                         f'{fy_hrs_bill:,.0f}', f'{fy_hrs_bf:,.0f}', f'{fy_hrs_tot:,.0f}']
pnl_try["Full Year"] = [fmt_try(fy["rev_try"]), fmt_try(fy_prod_cost_try), fmt_try(fy_backfill_try),
                         fmt_try(fy["cost_try"]), fmt_try(fy["margin_try"]),
                         fmt_pct(fy["margin_try"]/fy["rev_try"]) if fy["rev_try"] else "—",
                         f'€{fy_be:.2f}', f'€{fy_avg_up:.2f}',
                         "","","","",
                         f'{fy_hrs_bill:,.0f}', f'{fy_hrs_bf:,.0f}', f'{fy_hrs_tot:,.0f}']

tab_eur, tab_try = st.tabs(["💶 EUR View", "₺ TRY View"])
with tab_eur:
    st.dataframe(pd.DataFrame(pnl_eur).set_index("Line Item"), use_container_width=True)
with tab_try:
    st.dataframe(pd.DataFrame(pnl_try).set_index("Line Item"), use_container_width=True)

st.divider()
st.caption("CC Budget Tool · Streamlit · openpyxl · No xlsxwriter needed")
