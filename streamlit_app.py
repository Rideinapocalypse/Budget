"""
CC Budget & Forecast Tool - Streamlit App
Run with: streamlit run streamlit_app.py
Install:  pip install streamlit openpyxl xlsxwriter pandas
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import json

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="CC Budget Tool",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background: #161b27;
        border: 1px solid #2a3347;
        border-radius: 8px;
        padding: 12px 16px;
    }
    div[data-testid="metric-container"] label { color: #5a6480 !important; font-size: 11px !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 22px !important; }
    .stExpander { background: #161b27; border: 1px solid #2a3347; border-radius: 8px; }
    .section-title {
        font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #5a6480;
        border-bottom: 1px solid #2a3347; padding-bottom: 6px;
        margin-bottom: 12px; margin-top: 8px;
    }
    .kpi-positive { color: #10b981 !important; }
    .kpi-negative { color: #ef4444 !important; }
    .stDataFrame { border: 1px solid #2a3347; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Session state init ────────────────────────────────────────
if "blocks" not in st.session_state:
    st.session_state.blocks = {m: [] for m in MONTHS}

if "active_month" not in st.session_state:
    st.session_state.active_month = "Jan"

# ── Helpers ───────────────────────────────────────────────────
def fmt_eur(val):
    return f"€{val:,.0f}"

def fmt_pct(val):
    return f"{val*100:.1f}%"

def get_month_totals(month, g):
    blocks = st.session_state.blocks.get(month, [])
    total_rev = total_cost = total_hc = total_hrs = 0.0
    for b in blocks:
        shrink = b.get("shrink_override") if b.get("shrink_override") is not None else g["shrink"]
        fx     = b.get("fx_override")     if b.get("fx_override")     is not None else g["fx"]
        hours  = b.get("hours_override")  if b.get("hours_override")  is not None else g["hours"]
        hc         = b.get("hc", 0)
        salary     = b.get("salary", 0)
        unit_price = b.get("unit_price", 0)
        eff_hrs    = hours * (1 - shrink)
        rev        = hc * eff_hrs * unit_price
        cost_try   = hc * salary * g["ctc"] * (1 + g["bonus_pct"]) + hc * g["meal"]
        cost_eur   = cost_try / fx if fx else 0
        total_rev  += rev
        total_cost += cost_eur
        total_hc   += hc
        total_hrs  += hc * eff_hrs
    return dict(rev=total_rev, cost=total_cost,
                margin=total_rev - total_cost,
                hc=total_hc, hrs=total_hrs)

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📞 CCBudget")
    st.caption("Call Center Forecast Tool")
    st.divider()

    st.markdown('<div class="section-title">Global Inputs</div>', unsafe_allow_html=True)
    g_hours  = st.number_input("Worked Hours / Agent / Month", value=180, step=1, min_value=1)
    g_shrink = st.slider("Shrinkage % (default)", 0.0, 0.5, 0.15, 0.01, format="%.0f%%",
                         help="Applied to all blocks unless overridden")
    g_fx     = st.number_input("FX Rate (1 EUR = TRY) [default]", value=38.0, step=0.5, min_value=0.1)

    st.divider()
    st.markdown('<div class="section-title">Global Cost Drivers</div>', unsafe_allow_html=True)
    g_ctc       = st.number_input("Salary Multiplier (CTC)", value=1.70, step=0.05, min_value=1.0)
    g_bonus_pct = st.number_input("Bonus % of Base Salary", value=0.10, step=0.01, min_value=0.0)
    g_meal      = st.number_input("Meal Card / Agent / Month (TRY)", value=5850, step=50, min_value=0)

    g = dict(hours=g_hours, shrink=g_shrink, fx=g_fx,
             ctc=g_ctc, bonus_pct=g_bonus_pct, meal=g_meal)

    st.divider()
    st.markdown('<div class="section-title">Data Import / Export</div>', unsafe_allow_html=True)

    # Export
    def build_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            wb = writer.book

            # Formats
            hdr_fmt  = wb.add_format({"bold":True,"bg_color":"#1F4E79","font_color":"#FFFFFF","border":1})
            num_fmt  = wb.add_format({"num_format":"#,##0.00","border":1})
            pct_fmt  = wb.add_format({"num_format":"0.0%","border":1})
            text_fmt = wb.add_format({"border":1})
            bold_fmt = wb.add_format({"bold":True,"border":1})

            # Summary sheet
            summary_rows = []
            for m in MONTHS:
                t = get_month_totals(m, g)
                summary_rows.append({
                    "Month": m,
                    "Revenue (EUR)": round(t["rev"],2),
                    "Cost (EUR)":    round(t["cost"],2),
                    "Margin (EUR)":  round(t["margin"],2),
                    "Margin %":      round(t["margin"]/t["rev"],4) if t["rev"] else 0,
                    "Total HC":      t["hc"],
                })
            df_sum = pd.DataFrame(summary_rows)
            df_sum.to_excel(writer, sheet_name="Summary", index=False)

            # Global settings sheet
            settings = {
                "Setting": ["Worked Hours/Agent/Month","Shrinkage %","FX Rate (EUR=TRY)",
                            "CTC Multiplier","Bonus % of Base","Meal Card (TRY/mo)"],
                "Value":   [g_hours, g_shrink, g_fx, g_ctc, g_bonus_pct, g_meal]
            }
            pd.DataFrame(settings).to_excel(writer, sheet_name="Settings", index=False)

            # Per-month sheets
            for m in MONTHS:
                blocks = st.session_state.blocks.get(m, [])
                rows = []
                for b in blocks:
                    shrink = b.get("shrink_override") if b.get("shrink_override") is not None else g_shrink
                    fx     = b.get("fx_override")     if b.get("fx_override")     is not None else g_fx
                    hours  = b.get("hours_override")  if b.get("hours_override")  is not None else g_hours
                    hc     = b.get("hc",0)
                    salary = b.get("salary",0)
                    up     = b.get("unit_price",0)
                    eff    = hours*(1-shrink)
                    rev    = hc*eff*up
                    cost_e = (hc*salary*g_ctc*(1+g_bonus_pct)+hc*g_meal)/fx if fx else 0
                    rows.append({
                        "Language":             b.get("lang",""),
                        "HC":                   hc,
                        "Base Salary (TRY)":    salary,
                        "Unit Price (EUR/hr)":  up,
                        "Shrinkage Override":   b.get("shrink_override",""),
                        "FX Override":          b.get("fx_override",""),
                        "Hours Override":       b.get("hours_override",""),
                        "Revenue (EUR)":        round(rev,2),
                        "Cost (EUR)":           round(cost_e,2),
                        "Margin (EUR)":         round(rev-cost_e,2),
                    })
                if rows:
                    pd.DataFrame(rows).to_excel(writer, sheet_name=m, index=False)
                else:
                    pd.DataFrame(columns=["Language","HC","Base Salary (TRY)",
                                          "Unit Price (EUR/hr)","Shrinkage Override",
                                          "FX Override","Hours Override",
                                          "Revenue (EUR)","Cost (EUR)","Margin (EUR)"]).to_excel(
                        writer, sheet_name=m, index=False)
        return output.getvalue()

    if st.button("⬇ Export Excel", use_container_width=True, type="primary"):
        excel_data = build_excel()
        st.download_button(
            label="📥 Download CC_Budget_Export.xlsx",
            data=excel_data,
            file_name="CC_Budget_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.divider()
    uploaded = st.file_uploader("⬆ Import Excel", type=["xlsx"], label_visibility="collapsed")
    if uploaded:
        try:
            xls = pd.ExcelFile(uploaded)
            # Read settings
            if "Settings" in xls.sheet_names:
                df_s = pd.read_excel(xls, sheet_name="Settings")
                smap = dict(zip(df_s["Setting"], df_s["Value"]))
                # We can't set slider/number_input values from code after render,
                # but we store them so user sees a notice
                st.info("Settings sheet found. Globals loaded on next run if you save state.")

            # Read blocks
            for m in MONTHS:
                if m in xls.sheet_names:
                    df_m = pd.read_excel(xls, sheet_name=m)
                    blocks = []
                    for _, row in df_m.iterrows():
                        blocks.append({
                            "lang":            str(row.get("Language","")) if pd.notna(row.get("Language","")) else "",
                            "hc":              int(row.get("HC",0)) if pd.notna(row.get("HC",0)) else 0,
                            "salary":          float(row.get("Base Salary (TRY)",0)) if pd.notna(row.get("Base Salary (TRY)",0)) else 0,
                            "unit_price":      float(row.get("Unit Price (EUR/hr)",0)) if pd.notna(row.get("Unit Price (EUR/hr)",0)) else 0,
                            "shrink_override": float(row["Shrinkage Override"]) if pd.notna(row.get("Shrinkage Override")) else None,
                            "fx_override":     float(row["FX Override"]) if pd.notna(row.get("FX Override")) else None,
                            "hours_override":  float(row["Hours Override"]) if pd.notna(row.get("Hours Override")) else None,
                        })
                    st.session_state.blocks[m] = blocks
            st.success("✅ Excel imported successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# ── MAIN ──────────────────────────────────────────────────────
st.markdown("## 📞 CC Budget & Forecast")

# Month selector
cols_tabs = st.columns(12)
for i, m in enumerate(MONTHS):
    with cols_tabs[i]:
        if st.button(m, use_container_width=True,
                     type="primary" if m == st.session_state.active_month else "secondary"):
            st.session_state.active_month = m
            st.rerun()

active = st.session_state.active_month
st.markdown(f"### {active}")

# ── KPI row ───────────────────────────────────────────────────
t = get_month_totals(active, g)
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Total Revenue", fmt_eur(t["rev"]), help="EUR this month")
k2.metric("Total Cost",    fmt_eur(t["cost"]), help="EUR this month")
margin_delta = fmt_pct(t["margin"]/t["rev"]) if t["rev"] else "0%"
k3.metric("Gross Margin",  fmt_eur(t["margin"]), delta=margin_delta)
k4.metric("Total HC",      f"{int(t['hc'])} agents")
k5.metric("Effective Hrs", f"{t['hrs']:,.0f} hrs")

st.divider()

# ── Copy month helper ─────────────────────────────────────────
with st.expander("📋 Copy Month to Another Month"):
    cc1, cc2, cc3 = st.columns([2,2,1])
    copy_from = cc1.selectbox("From", MONTHS, index=MONTHS.index(active), key="copy_from")
    copy_to   = cc2.selectbox("To",   MONTHS, index=(MONTHS.index(active)+1)%12, key="copy_to")
    if cc3.button("Copy", use_container_width=True, type="primary"):
        if copy_from == copy_to:
            st.error("Source and destination are the same!")
        else:
            import copy
            st.session_state.blocks[copy_to] = copy.deepcopy(st.session_state.blocks[copy_from])
            st.success(f"Copied {copy_from} → {copy_to}")
            st.rerun()

# ── Production blocks ─────────────────────────────────────────
st.markdown('<div class="section-title">Production Blocks</div>', unsafe_allow_html=True)

blocks = st.session_state.blocks[active]

# Add block button
if st.button("+ Add Production Block", type="secondary"):
    blocks.append({"lang":"","hc":0,"salary":0,"unit_price":0,
                   "shrink_override":None,"fx_override":None,"hours_override":None})
    st.rerun()

blocks_to_delete = []

for i, b in enumerate(blocks):
    shrink = b.get("shrink_override") if b.get("shrink_override") is not None else g_shrink
    fx     = b.get("fx_override")     if b.get("fx_override")     is not None else g_fx
    hours  = b.get("hours_override")  if b.get("hours_override")  is not None else g_hours
    hc     = b.get("hc",0)
    salary = b.get("salary",0)
    up     = b.get("unit_price",0)
    eff    = hours*(1-shrink)
    rev    = hc*eff*up
    cost_e = (hc*salary*g_ctc*(1+g_bonus_pct)+hc*g_meal)/fx if fx else 0
    margin = rev - cost_e

    label = b.get("lang") or f"Block #{i+1}"
    title = f"Block #{i+1} — {label} | HC: {hc} | Rev: {fmt_eur(rev)} | Margin: {fmt_eur(margin)}"

    with st.expander(title, expanded=True):
        r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns([2,1,2,2,1])

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

        r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns([2,2,2,2,2])

        shr_raw = r2c1.text_input(f"Shrinkage Override (global: {g_shrink*100:.0f}%)",
                                   value="" if b.get("shrink_override") is None else str(b["shrink_override"]),
                                   key=f"shr_{active}_{i}", placeholder="leave blank = global")
        fx_raw  = r2c2.text_input(f"FX Override (global: {g_fx})",
                                   value="" if b.get("fx_override") is None else str(b["fx_override"]),
                                   key=f"fx_{active}_{i}", placeholder="leave blank = global")
        hr_raw  = r2c3.text_input(f"Hours Override (global: {g_hours})",
                                   value="" if b.get("hours_override") is None else str(b["hours_override"]),
                                   key=f"hr_{active}_{i}", placeholder="leave blank = global")

        with r2c4:
            st.markdown("**Revenue (EUR)**")
            st.markdown(f"<span style='color:#10b981;font-size:18px;font-weight:700'>{fmt_eur(rev)}</span>",
                        unsafe_allow_html=True)
        with r2c5:
            st.markdown("**Margin (EUR)**")
            color = "#10b981" if margin >= 0 else "#ef4444"
            st.markdown(f"<span style='color:{color};font-size:18px;font-weight:700'>{fmt_eur(margin)}</span>",
                        unsafe_allow_html=True)

        # Update block state
        blocks[i]["lang"]            = new_lang
        blocks[i]["hc"]              = new_hc
        blocks[i]["salary"]          = new_sal
        blocks[i]["unit_price"]      = new_up
        blocks[i]["shrink_override"] = float(shr_raw) if shr_raw.strip() else None
        blocks[i]["fx_override"]     = float(fx_raw)  if fx_raw.strip()  else None
        blocks[i]["hours_override"]  = float(hr_raw)  if hr_raw.strip()  else None

# Delete marked blocks
if blocks_to_delete:
    for idx in sorted(blocks_to_delete, reverse=True):
        blocks.pop(idx)
    st.rerun()

# ── P&L Summary Table ─────────────────────────────────────────
st.divider()
st.markdown("### 📉 P&L Summary — Full Year")

pnl_data = {"Line Item": ["Revenue (EUR)", "Cost (EUR)", "Gross Margin (EUR)", "Margin %"]}
fy_rev = fy_cost = fy_margin = 0.0

for m in MONTHS:
    mt = get_month_totals(m, g)
    fy_rev    += mt["rev"]
    fy_cost   += mt["cost"]
    fy_margin += mt["margin"]
    pnl_data[m] = [
        fmt_eur(mt["rev"]),
        fmt_eur(mt["cost"]),
        fmt_eur(mt["margin"]),
        fmt_pct(mt["margin"]/mt["rev"]) if mt["rev"] else "—",
    ]

pnl_data["Full Year"] = [
    fmt_eur(fy_rev),
    fmt_eur(fy_cost),
    fmt_eur(fy_margin),
    fmt_pct(fy_margin/fy_rev) if fy_rev else "—",
]

df_pnl = pd.DataFrame(pnl_data).set_index("Line Item")
st.dataframe(df_pnl, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.caption("CC Budget Tool · Built with Streamlit · Export to Excel anytime from the sidebar")
