"""
CC Budget & Forecast Tool - Streamlit App
Run with: streamlit run streamlit_app.py
Install:  pip install streamlit openpyxl pandas
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import copy

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

def fmt_eur(v): return f"€{v:,.0f}"
def fmt_pct(v): return f"{v*100:.1f}%"

def get_totals(month, g):
    total_rev = total_cost = total_hc = total_hrs = 0.0
    for b in st.session_state.blocks.get(month, []):
        shrink = b["shrink_override"] if b.get("shrink_override") is not None else g["shrink"]
        fx     = b["fx_override"]     if b.get("fx_override")     is not None else g["fx"]
        hours  = b["hours_override"]  if b.get("hours_override")  is not None else g["hours"]
        hc, sal, up = b.get("hc",0), b.get("salary",0), b.get("unit_price",0)
        eff = hours * (1 - shrink)
        rev = hc * eff * up
        cost = (hc * sal * g["ctc"] * (1 + g["bonus_pct"]) + hc * g["meal"]) / fx if fx else 0
        total_rev += rev; total_cost += cost; total_hc += hc; total_hrs += hc * eff
    return dict(rev=total_rev, cost=total_cost, margin=total_rev-total_cost,
                hc=total_hc, hrs=total_hrs)

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

# ── Template builder ──────────────────────────────────────────
def build_template(gh, gs, gfx, gctc, gbp, gm):
    wb = Workbook(); wb.remove(wb.active)

    # Instructions
    wi = wb.create_sheet("Instructions"); set_widths(wi, [40, 65])
    wi["A1"].value = "CC Budget Tool - Import Template"
    wi["A1"].font  = Font(name="Calibri", bold=True, size=14, color="1F4E79")
    wi["A2"].value = "Fill in the BLUE cells in each month sheet, then import this file."
    wi["A2"].font  = Font(name="Calibri", italic=True, color="444444", size=10)
    steps = [
        ("STEP 1", "Open the Settings sheet and update global values (FX, shrinkage, CTC, etc.)"),
        ("STEP 2", "Go to each month tab (Jan, Feb, ..., Dec)"),
        ("STEP 3", "Fill BLUE cells: Language, HC, Base Salary, Unit Price"),
        ("STEP 4", "Optionally override Shrinkage %, FX Rate, or Hours per block (leave blank = global)"),
        ("STEP 5", "Save the file and import it using the sidebar uploader in the app"),
    ]
    for ri, (s, d) in enumerate(steps, start=4):
        hdr(wi, ri, 1, s); note(wi, ri, 2, d)
    wcell(wi, 10, 1, "COLOR GUIDE", bold=True, bg="FFFACD", fg="7B4F00")
    inp( wi, 11, 1, "Blue cells"); note(wi, 11, 2, "Fill these in - your input data")
    note(wi, 12, 1, "Grey italic"); note(wi, 12, 2, "Leave blank to inherit the global default")

    # Settings
    ws = wb.create_sheet("Settings"); set_widths(ws, [35, 22])
    hdr(ws,1,1,"Setting"); hdr(ws,1,2,"Value")
    for ri,(lbl,val) in enumerate([
        ("Worked Hours/Agent/Month", gh), ("Shrinkage %", gs),
        ("FX Rate (EUR=TRY)", gfx), ("CTC Multiplier", gctc),
        ("Bonus % of Base", gbp), ("Meal Card (TRY/mo)", gm),
    ], start=2):
        wcell(ws,ri,1,lbl); inp(ws,ri,2,val,fmt="#,##0.00")

    # Month sheets
    col_hdrs  = ["Language","HC","Base Salary (TRY)","Unit Price (EUR/hr)",
                 "Shrinkage Override","FX Override","Hours Override"]
    col_hints = ["e.g. DE, EN, TR","agents","monthly gross TRY","billable EUR/hr",
                 "blank=global","blank=global","blank=global"]
    col_ws    = [18, 10, 22, 22, 24, 18, 22]
    for m in MONTHS:
        ws = wb.create_sheet(m); set_widths(ws, col_ws)
        for ci, h in enumerate(col_hdrs, 1): hdr(ws, 1, ci, h)
        for ci, ht in enumerate(col_hints, 1): note(ws, 2, ci, ht)
        rows = st.session_state.blocks.get(m,[]) or [
            {"lang":"","hc":0,"salary":0,"unit_price":0,
             "shrink_override":None,"fx_override":None,"hours_override":None}]*3
        for ri, b in enumerate(rows, start=3):
            vals = [b.get("lang",""), b.get("hc",0), b.get("salary",0), b.get("unit_price",0),
                    b["shrink_override"] if b.get("shrink_override") is not None else "",
                    b["fx_override"]     if b.get("fx_override")     is not None else "",
                    b["hours_override"]  if b.get("hours_override")  is not None else ""]
            for ci, v in enumerate(vals, 1): inp(ws, ri, ci, v)

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
    g_fx     = st.number_input("FX Rate (1 EUR = TRY)", value=38.0, step=0.5, min_value=0.1)

    st.divider()
    st.markdown('<div class="section-title">Global Cost Drivers</div>', unsafe_allow_html=True)
    g_ctc       = st.number_input("Salary Multiplier (CTC)", value=1.70, step=0.05, min_value=1.0)
    g_bonus_pct = st.number_input("Bonus % of Base Salary",  value=0.10, step=0.01, min_value=0.0)
    g_meal      = st.number_input("Meal Card / Agent / Month (TRY)", value=5850, step=50, min_value=0)

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
            loaded = 0
            for m in MONTHS:
                if m not in xls.sheet_names: continue
                df_m = pd.read_excel(xls, sheet_name=m)
                if "HC" in df_m.columns:
                    df_m = df_m[pd.to_numeric(df_m["HC"], errors="coerce").notna()]
                blocks = []
                for _, row in df_m.iterrows():
                    def sf(v):
                        try: return float(v) if str(v).strip() not in ("","nan") else None
                        except: return None
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
            st.success(f"Imported {loaded} blocks across all months!")
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
k1.metric("Total Revenue", fmt_eur(t["rev"]),  help="EUR this month")
k2.metric("Total Cost",    fmt_eur(t["cost"]), help="EUR this month")
k3.metric("Gross Margin",  fmt_eur(t["margin"]),
          delta=fmt_pct(t["margin"]/t["rev"]) if t["rev"] else "0%")
k4.metric("Total HC",      f"{int(t['hc'])} agents")
k5.metric("Effective Hrs", f"{t['hrs']:,.0f} hrs")

st.divider()

with st.expander("📋 Copy Month to Another Month"):
    cc1, cc2, cc3 = st.columns([2,2,1])
    copy_from = cc1.selectbox("From", MONTHS, index=MONTHS.index(active), key="copy_from")
    copy_to   = cc2.selectbox("To",   MONTHS, index=(MONTHS.index(active)+1)%12, key="copy_to")
    if cc3.button("Copy", use_container_width=True, type="primary"):
        if copy_from == copy_to:
            st.error("Source and destination are the same!")
        else:
            st.session_state.blocks[copy_to] = copy.deepcopy(st.session_state.blocks[copy_from])
            st.success(f"Copied {copy_from} to {copy_to}")
            st.rerun()

st.markdown('<div class="section-title">Production Blocks</div>', unsafe_allow_html=True)
blocks = st.session_state.blocks[active]

if st.button("+ Add Production Block", type="secondary"):
    blocks.append({"lang":"","hc":0,"salary":0,"unit_price":0,
                   "shrink_override":None,"fx_override":None,"hours_override":None})
    st.rerun()

blocks_to_delete = []
for i, b in enumerate(blocks):
    shrink = b["shrink_override"] if b.get("shrink_override") is not None else g_shrink
    fx     = b["fx_override"]     if b.get("fx_override")     is not None else g_fx
    hours  = b["hours_override"]  if b.get("hours_override")  is not None else g_hours
    hc, salary, up = b.get("hc",0), b.get("salary",0), b.get("unit_price",0)
    eff = hours * (1 - shrink)
    rev = hc * eff * up
    cost_e = (hc * salary * g_ctc * (1 + g_bonus_pct) + hc * g_meal) / fx if fx else 0
    margin = rev - cost_e
    label  = b.get("lang") or f"Block #{i+1}"
    title  = f"Block #{i+1} — {label} | HC: {hc} | Rev: {fmt_eur(rev)} | Margin: {fmt_eur(margin)}"

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

        r2c1,r2c2,r2c3,r2c4,r2c5 = st.columns([2,2,2,2,2])
        shr_raw = r2c1.text_input(f"Shrinkage Override (global: {g_shrink*100:.0f}%)",
                                   value="" if b.get("shrink_override") is None else str(b["shrink_override"]),
                                   key=f"shr_{active}_{i}", placeholder="blank = global")
        fx_raw  = r2c2.text_input(f"FX Override (global: {g_fx})",
                                   value="" if b.get("fx_override") is None else str(b["fx_override"]),
                                   key=f"fx_{active}_{i}", placeholder="blank = global")
        hr_raw  = r2c3.text_input(f"Hours Override (global: {g_hours})",
                                   value="" if b.get("hours_override") is None else str(b["hours_override"]),
                                   key=f"hr_{active}_{i}", placeholder="blank = global")
        with r2c4:
            st.markdown("**Revenue (EUR)**")
            st.markdown(f"<span style='color:#10b981;font-size:18px;font-weight:700'>{fmt_eur(rev)}</span>",
                        unsafe_allow_html=True)
        with r2c5:
            st.markdown("**Margin (EUR)**")
            color = "#10b981" if margin >= 0 else "#ef4444"
            st.markdown(f"<span style='color:{color};font-size:18px;font-weight:700'>{fmt_eur(margin)}</span>",
                        unsafe_allow_html=True)

        blocks[i].update({
            "lang": new_lang, "hc": new_hc, "salary": new_sal, "unit_price": new_up,
            "shrink_override": float(shr_raw) if shr_raw.strip() else None,
            "fx_override":     float(fx_raw)  if fx_raw.strip()  else None,
            "hours_override":  float(hr_raw)  if hr_raw.strip()  else None,
        })

if blocks_to_delete:
    for idx in sorted(blocks_to_delete, reverse=True):
        blocks.pop(idx)
    st.rerun()

st.divider()
st.markdown("### 📉 P&L Summary — Full Year")
pnl = {"Line Item": ["Revenue (EUR)","Cost (EUR)","Gross Margin (EUR)","Margin %"]}
fy_rev = fy_cost = fy_margin = 0.0
for m in MONTHS:
    mt = get_totals(m, g)
    fy_rev += mt["rev"]; fy_cost += mt["cost"]; fy_margin += mt["margin"]
    pnl[m] = [fmt_eur(mt["rev"]), fmt_eur(mt["cost"]), fmt_eur(mt["margin"]),
              fmt_pct(mt["margin"]/mt["rev"]) if mt["rev"] else "—"]
pnl["Full Year"] = [fmt_eur(fy_rev), fmt_eur(fy_cost), fmt_eur(fy_margin),
                    fmt_pct(fy_margin/fy_rev) if fy_rev else "—"]
st.dataframe(pd.DataFrame(pnl).set_index("Line Item"), use_container_width=True)

st.divider()
st.caption("CC Budget Tool · Streamlit · openpyxl · No xlsxwriter needed")
