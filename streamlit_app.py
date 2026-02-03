import streamlit as st
import pandas as pd
from io import BytesIO

# ============================
# Page config
# ============================
st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# ============================
# UI: tighter spacing (smaller blocks)
# ============================
st.markdown(
    """
<style>
div.block-container {padding-top: 1.0rem; padding-bottom: 1.0rem; max-width: 1400px;}
div[data-testid="stVerticalBlock"] > div {gap: 0.35rem;}
[data-testid="stMetric"] {padding: 6px 10px;}
[data-testid="stMetricLabel"] {font-size: 0.80rem;}
[data-testid="stMetricValue"] {font-size: 1.05rem;}
h3 {margin-top: 0.4rem;}
</style>
""",
    unsafe_allow_html=True,
)

# ============================
# Month constants
# ============================
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

default_langs = ["DE", "EN", "TR", "FR", "IT", "NL"]
default_roles = ["Team Manager", "QA", "Ops", "Trainer", "RTA/WFM"]

# ============================
# Helper functions
# ============================
def fmt0(x: float) -> str:
    return f"{x:,.0f}"

def get_val(key: str, default=0.0):
    return st.session_state.get(key, default)

def normalize_month(m):
    m = str(m).strip()
    mapping = {x.lower(): x for x in MONTHS}
    return mapping.get(m.lower(), None)

# ============================
# GLOBAL INPUTS (SIDEBAR)
# ============================
st.sidebar.header("Global Inputs")

worked_hours_default = st.sidebar.number_input(
    "Worked Hours per Agent (Monthly) [default]",
    value=180.0, step=1.0, min_value=0.0
)

shrinkage_default = st.sidebar.slider(
    "Shrinkage (%) [default]",
    min_value=0.0, max_value=0.5, value=0.15, step=0.01
)

st.sidebar.divider()
st.sidebar.subheader("Global Cost Drivers")

salary_multiplier = st.sidebar.number_input(
    "Salary Multiplier", value=1.70, step=0.05, min_value=0.0
)

bonus_pct = st.sidebar.number_input(
    "Bonus % (of Base Salary)", value=0.10, step=0.01, min_value=0.0, max_value=5.0
)

bonus_multiplier = st.sidebar.number_input(
    "Bonus Multiplier", value=1.00, step=0.05, min_value=0.0
)

meal_card = st.sidebar.number_input(
    "Meal Card per Agent (Monthly TRY)", value=5850.0, step=100.0, min_value=0.0
)

st.sidebar.divider()
currency = st.sidebar.selectbox("Unit Price Currency", ["EUR", "USD"])

fx_rate_default = st.sidebar.number_input(
    f"FX Rate (1 {currency} = TRY) [default]",
    value=38.0 if currency == "EUR" else 35.0,
    step=0.1,
    min_value=0.0
)

st.sidebar.divider()
st.sidebar.subheader("Month Filter")

selected_month = st.sidebar.selectbox("Select Month", MONTHS, index=0)

view_mode = st.sidebar.radio(
    "View",
    ["Selected Month", "All Months (Trend)"],
    index=0
)

# Effective month inputs (optional per-month overrides from Excel import)
worked_hours_effective = float(st.session_state.get(f"{selected_month}_worked_hours", worked_hours_default))
shrinkage_effective = float(st.session_state.get(f"{selected_month}_shrinkage", shrinkage_default))
productive_hours_effective = worked_hours_effective * (1 - shrinkage_effective)
fx_rate_effective = float(st.session_state.get(f"{selected_month}_fx", fx_rate_default))

st.sidebar.caption(f"Effective FX for {selected_month}: {fx_rate_effective:,.2f} TRY/{currency}")

def try_from_currency(amount_in_currency: float) -> float:
    return amount_in_currency * fx_rate_effective

def calculate_agent_cost(base_salary_try: float) -> float:
    """
    Fully loaded monthly cost per head in TRY:
    (base_salary + base_salary*bonus_pct*bonus_multiplier) * salary_multiplier + meal_card
    """
    bonus = base_salary_try * bonus_pct * bonus_multiplier
    gross = base_salary_try + bonus
    loaded = gross * salary_multiplier
    return loaded + meal_card

# ============================
# TEMPLATE + IMPORT (SIDEBAR)
# ============================
st.sidebar.divider()
st.sidebar.subheader("Excel Import / Template")

def build_template_xlsx() -> bytes:
    months = MONTHS
    langs = default_langs
    roles = default_roles

    inputs_df = pd.DataFrame({
        "Month": months,
        "FX": [fx_rate_default] * 12,
        "WorkedHours": [worked_hours_default] * 12,
        "Shrinkage": [shrinkage_default] * 12,
    })

    prod_rows = []
    for m in months:
        for l in langs:
            prod_rows.append({
                "Month": m,
                "Language": l,
                "HC": 0,
                "BaseSalaryTRY": 0,
                "UnitPriceCurrency": 0,
            })
    prod_df = pd.DataFrame(prod_rows)

    oh_rows = []
    for m in months:
        for r in roles:
            oh_rows.append({
                "Month": m,
                "Role": r,
                "HC": 0,
                "BaseSalaryTRY": 0,
            })
    oh_df = pd.DataFrame(oh_rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as w:
        inputs_df.to_excel(w, sheet_name="Inputs", index=False)
        prod_df.to_excel(w, sheet_name="Production", index=False)
        oh_df.to_excel(w, sheet_name="Overhead", index=False)

    return output.getvalue()

st.sidebar.download_button(
    "⬇️ Download Excel Template",
    data=build_template_xlsx(),
    file_name="budget_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ============================
# CALCULATED VALUES (compact)
# ============================
st.subheader("Calculated Values")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Month", selected_month)
c2.metric("Worked Hours", f"{worked_hours_effective:,.2f}")
c3.metric("Productive Hours", f"{productive_hours_effective:,.2f}")
c4.metric("Shrinkage", f"{shrinkage_effective*100:.1f}%")
c5.metric("Bonus Mult.", f"{bonus_multiplier:,.2f}")
c6.metric("FX (effective)", f"{fx_rate_effective:,.2f}")

# ============================
# IMPORT UI (main page)
# ============================
st.divider()
st.subheader("Import from Excel")

uploaded = st.file_uploader("Upload filled template (.xlsx)", type=["xlsx"])

def apply_import_xlsx(file):
    xls = pd.ExcelFile(file)
    required = {"Inputs", "Production", "Overhead"}
    if not required.issubset(set(xls.sheet_names)):
        missing = required - set(xls.sheet_names)
        raise ValueError(f"Missing sheet(s): {', '.join(missing)}")

    inputs_df = pd.read_excel(xls, "Inputs")
    prod_df = pd.read_excel(xls, "Production")
    oh_df = pd.read_excel(xls, "Overhead")

    # Inputs: store per-month FX / worked hours / shrinkage overrides
    for _, row in inputs_df.iterrows():
        m = normalize_month(row.get("Month"))
        if not m:
            continue

        fx = row.get("FX")
        if pd.notna(fx):
            st.session_state[f"{m}_fx"] = float(fx)

        wh = row.get("WorkedHours")
        if pd.notna(wh):
            st.session_state[f"{m}_worked_hours"] = float(wh)

        sh = row.get("Shrinkage")
        if pd.notna(sh):
            st.session_state[f"{m}_shrinkage"] = float(sh)

    # Production: map by language -> index
    lang_to_idx = {default_langs[i].strip(): i for i in range(6)}

    for _, row in prod_df.iterrows():
        m = normalize_month(row.get("Month"))
        if not m:
            continue

        lang = str(row.get("Language", "")).strip()
        if lang not in lang_to_idx:
            continue
        i = lang_to_idx[lang]

        hc = row.get("HC")
        sal = row.get("BaseSalaryTRY")
        up = row.get("UnitPriceCurrency")

        if pd.notna(hc):
            st.session_state[f"{m}_hc_{i}"] = float(hc)
        if pd.notna(sal):
            st.session_state[f"{m}_salary_{i}"] = float(sal)
        if pd.notna(up):
            st.session_state[f"{m}_price_{i}"] = float(up)

        st.session_state[f"{m}_lang_{i}"] = lang

    # Overhead: map by role -> index
    role_to_idx = {default_roles[i].strip(): i for i in range(5)}

    for _, row in oh_df.iterrows():
        m = normalize_month(row.get("Month"))
        if not m:
            continue

        role = str(row.get("Role", "")).strip()
        if role not in role_to_idx:
            continue
        i = role_to_idx[role]

        hc = row.get("HC")
        sal = row.get("BaseSalaryTRY")

        if pd.notna(hc):
            st.session_state[f"{m}_oh_hc_{i}"] = float(hc)
        if pd.notna(sal):
            st.session_state[f"{m}_oh_salary_{i}"] = float(sal)

        st.session_state[f"{m}_oh_role_{i}"] = role

if uploaded is not None:
    a, b = st.columns([1, 2])
    with a:
        if st.button("✅ Apply import to app inputs"):
            try:
                apply_import_xlsx(uploaded)
                st.success("Imported! Switch months in the sidebar to confirm values loaded.")
            except Exception as e:
                st.error(f"Import failed: {e}")
    with b:
        st.info("Tip: If a month isn't filled in Excel, it will remain as-is (often zero) in the app.")

# ============================
# CORE COMPUTE (per month)
# ============================
def compute_for_month(month: str):
    # Use month-specific overrides if present, otherwise fall back to defaults
    wh = float(st.session_state.get(f"{month}_worked_hours", worked_hours_default))
    sh = float(st.session_state.get(f"{month}_shrinkage", shrinkage_default))
    prod_hours = wh * (1 - sh)
    fx = float(st.session_state.get(f"{month}_fx", fx_rate_default))

    def try_from_currency_month(amount_in_currency: float) -> float:
        return amount_in_currency * fx

    total_prod_cost = 0.0
    total_revenue = 0.0
    prod_rows = []

    # Production
    for i in range(6):
        lang_key = f"{month}_lang_{i}"
        hc_key = f"{month}_hc_{i}"
        salary_key = f"{month}_salary_{i}"
        price_key = f"{month}_price_{i}"

        lang = get_val(lang_key, default_langs[i])
        hc = float(get_val(hc_key, 0.0))
        salary = float(get_val(salary_key, 0.0))
        unit_price_cur = float(get_val(price_key, 0.0))

        unit_price_try = try_from_currency_month(unit_price_cur)
        cost_per_agent = calculate_agent_cost(salary)
        cost_total = hc * cost_per_agent
        revenue = hc * prod_hours * unit_price_try
        margin = revenue - cost_total

        total_prod_cost += cost_total
        total_revenue += revenue

        prod_rows.append({
            "Month": month,
            "Language": lang,
            "HC": hc,
            "Base Salary (TRY)": salary,
            f"Unit Price ({currency})": unit_price_cur,
            "FX Rate": fx,
            "Worked Hours": wh,
            "Shrinkage": sh,
            "Productive Hours": prod_hours,
            "Unit Price (TRY)": unit_price_try,
            "Cost/Agent (TRY)": cost_per_agent,
            "Total Cost (TRY)": cost_total,
            "Revenue (TRY)": revenue,
            "Margin (TRY)": margin,
            "Bonus %": bonus_pct,
            "Bonus Multiplier": bonus_multiplier,
            "Salary Multiplier": salary_multiplier,
            "Meal Card (TRY)": meal_card,
        })

    # Overhead
    total_overhead = 0.0
    oh_rows = []

    for i in range(5):
        role_key = f"{month}_oh_role_{i}"
        oh_hc_key = f"{month}_oh_hc_{i}"
        oh_salary_key = f"{month}_oh_salary_{i}"

        role = get_val(role_key, default_roles[i])
        oh_hc = float(get_val(oh_hc_key, 0.0))
        oh_salary = float(get_val(oh_salary_key, 0.0))

        oh_cost_per = calculate_agent_cost(oh_salary) if oh_hc > 0 else 0.0
        oh_cost_total = oh_hc * oh_cost_per
        total_overhead += oh_cost_total

        oh_rows.append({
            "Month": month,
            "Role": role,
            "HC": oh_hc,
            "Base Salary (TRY)": oh_salary,
            "Cost/Head (TRY)": oh_cost_per,
            "Total Cost (TRY)": oh_cost_total,
            "Bonus %": bonus_pct,
            "Bonus Multiplier": bonus_multiplier,
            "Salary Multiplier": salary_multiplier,
            "Meal Card (TRY)": meal_card,
        })

    grand_cost = total_prod_cost + total_overhead
    grand_margin = total_revenue - grand_cost
    gm_pct = (grand_margin / total_revenue) if total_revenue > 0 else 0.0

    summary = {
        "Month": month,
        "Total Production Cost (TRY)": total_prod_cost,
        "Total Overhead Cost (TRY)": total_overhead,
        "Total Revenue (TRY)": total_revenue,
        "Grand Total Cost (TRY)": grand_cost,
        "Grand Margin (TRY)": grand_margin,
        "GM %": gm_pct,
    }

    return pd.DataFrame(prod_rows), pd.DataFrame(oh_rows), pd.DataFrame([summary])

# ============================
# INPUT UI (Selected Month)
# ============================
st.divider()
st.subheader("Production Blocks")

for i in range(6):
    with st.expander(f"#{i+1} Production — {default_langs[i]}  ({selected_month})", expanded=(i == 0)):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.text_input(
                f"Language Label #{i+1}",
                value=get_val(f"{selected_month}_lang_{i}", default_langs[i]),
                key=f"{selected_month}_lang_{i}",
            )
        with col2:
            st.number_input(
                f"HC ({default_langs[i]})",
                min_value=0.0,
                step=1.0,
                key=f"{selected_month}_hc_{i}",
            )
        with col3:
            st.number_input(
                f"Base Salary ({default_langs[i]}) TRY",
                min_value=0.0,
                step=500.0,
                key=f"{selected_month}_salary_{i}",
            )
        with col4:
            st.number_input(
                f"Unit Price ({default_langs[i]}) in {currency}",
                min_value=0.0,
                step=0.1,
                key=f"{selected_month}_price_{i}",
            )

st.divider()
st.subheader("Overhead")

for i in range(5):
    with st.expander(f"Overhead #{i+1}  ({selected_month})", expanded=(i == 0)):
        oh1, oh2, oh3 = st.columns(3)
        with oh1:
            st.text_input(
                f"Role #{i+1}",
                value=get_val(f"{selected_month}_oh_role_{i}", default_roles[i]),
                key=f"{selected_month}_oh_role_{i}",
            )
        with oh2:
            st.number_input(
                "OH HC",
                min_value=0.0,
                step=1.0,
                key=f"{selected_month}_oh_hc_{i}",
            )
        with oh3:
            st.number_input(
                "Base Salary (TRY)",
                min_value=0.0,
                step=500.0,
                key=f"{selected_month}_oh_salary_{i}",
            )

# ============================
# COMPUTE Selected Month
# ============================
prod_df_m, oh_df_m, summary_df_m = compute_for_month(selected_month)

st.divider()
st.subheader("Final Summary")

s = summary_df_m.iloc[0]
s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Production Cost (TRY)", fmt0(s["Total Production Cost (TRY)"]))
s2.metric("Total Overhead Cost (TRY)", fmt0(s["Total Overhead Cost (TRY)"]))
s3.metric("Total Revenue (TRY)", fmt0(s["Total Revenue (TRY)"]))
s4.metric("GM %", f"{s['GM %']*100:.1f}%")

t1, t2, t3 = st.columns(3)
t1.metric("Grand Total Cost (TRY)", fmt0(s["Grand Total Cost (TRY)"]))
t2.metric("Grand Margin (TRY)", fmt0(s["Grand Margin (TRY)"]))
t3.metric("Currency + FX", f"{currency} @ {fx_rate_effective:,.2f} TRY")

# ============================
# SUMMARY GRAPHICS
# ============================
st.divider()
st.subheader("Summary Graphics")

summary_bar = pd.DataFrame(
    {"TRY": [s["Total Revenue (TRY)"], s["Grand Total Cost (TRY)"], s["Grand Margin (TRY)"]]},
    index=["Revenue", "Total Cost", "Margin"]
)
st.bar_chart(summary_bar)

gm_df = pd.DataFrame({"GM%": [s["GM %"] * 100.0]}, index=["GM %"])
st.bar_chart(gm_df)

# Trend view across months
if view_mode == "All Months (Trend)":
    all_sum = []
    for m in MONTHS:
        _, _, sm = compute_for_month(m)
        all_sum.append(sm)
    all_sum_df = pd.concat(all_sum, ignore_index=True)

    st.markdown("#### All Months Trend")
    trend_df = all_sum_df.set_index("Month")[["Total Revenue (TRY)", "Grand Total Cost (TRY)", "Grand Margin (TRY)"]]
    st.line_chart(trend_df)

    gm_trend = (all_sum_df.set_index("Month")[["GM %"]] * 100.0).rename(columns={"GM %": "GM%"})
    st.line_chart(gm_trend)

# ============================
# TABLES
# ============================
with st.expander("Show detailed tables (Selected Month)"):
    st.markdown("#### Production")
    st.dataframe(prod_df_m, use_container_width=True)
    st.markdown("#### Overhead")
    st.dataframe(oh_df_m, use_container_width=True)

# ============================
# EXCEL EXPORT
# ============================
st.divider()
st.subheader("Export")

def build_excel_export() -> bytes:
    inputs_df = pd.DataFrame([{
        "Selected Month": selected_month,
        "Worked Hours (effective)": worked_hours_effective,
        "Shrinkage (effective)": shrinkage_effective,
        "Productive Hours (effective)": productive_hours_effective,
        "Salary Multiplier": salary_multiplier,
        "Bonus %": bonus_pct,
        "Bonus Multiplier": bonus_multiplier,
        "Meal Card (TRY)": meal_card,
        "Currency": currency,
        "FX Rate (effective)": fx_rate_effective,
    }])

    # Selected month sheets
    sel_summary = summary_df_m.copy()

    # All months summary
    all_sum = []
    for m in MONTHS:
        _, _, sm = compute_for_month(m)
        all_sum.append(sm)
    all_months_summary_df = pd.concat(all_sum, ignore_index=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        prod_df_m.to_excel(writer, sheet_name=f"Prod_{selected_month}", index=False)
        oh_df_m.to_excel(writer, sheet_name=f"OH_{selected_month}", index=False)
        sel_summary.to_excel(writer, sheet_name=f"Summary_{selected_month}", index=False)
        all_months_summary_df.to_excel(writer, sheet_name="Summary_AllMonths", index=False)

    return output.getvalue()

excel_bytes = build_excel_export()

st.download_button(
    label="⬇️ Download Excel (.xlsx)",
    data=excel_bytes,
    file_name=f"budget_app_export_{selected_month}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("Show formula details"):
    st.write(
        """
**Cost per head (TRY)** =
(base_salary + base_salary×bonus_pct×bonus_multiplier) × salary_multiplier + meal_card

**Revenue (TRY)** =
HC × productive_hours × (unit_price_in_currency × FX)

**GM%** =
(Revenue − Total Cost) / Revenue
        """
    )
