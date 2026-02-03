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
# Constants
# ============================
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

default_langs = ["DE", "EN", "TR", "FR", "IT", "NL"]
default_roles = ["Team Manager", "QA", "Ops", "Trainer", "RTA/WFM"]

# ============================
# Helpers
# ============================
def fmt0(x: float) -> str:
    return f"{x:,.0f}"

def normalize_month(m):
    """Accept Jan/January/1..12/Excel dates/timestamps."""
    if m is None:
        return None
    try:
        if pd.isna(m):
            return None
    except Exception:
        pass

    # datetime-like (Timestamp)
    try:
        if hasattr(m, "month"):
            mn = int(m.month)
            if 1 <= mn <= 12:
                return MONTHS[mn - 1]
    except Exception:
        pass

    # numeric month
    try:
        if isinstance(m, (int, float)) and 1 <= int(m) <= 12:
            return MONTHS[int(m) - 1]
    except Exception:
        pass

    s = str(m).strip()
    full_to_short = {
        "january": "Jan", "february": "Feb", "march": "Mar", "april": "Apr",
        "may": "May", "june": "Jun", "july": "Jul", "august": "Aug",
        "september": "Sep", "october": "Oct", "november": "Nov", "december": "Dec"
    }
    s_lower = s.lower()
    if s_lower in full_to_short:
        return full_to_short[s_lower]

    mapping = {x.lower(): x for x in MONTHS}
    return mapping.get(s_lower, None)

def ensure_storage():
    """
    Central truth:
      st.session_state["data"]["months"][month] = {
        "inputs": {...},
        "prod": list of 6 dicts,
        "oh": list of 5 dicts
      }
    """
    if "data" in st.session_state:
        return

    st.session_state["data"] = {"months": {}}
    for m in MONTHS:
        st.session_state["data"]["months"][m] = {
            "inputs": {
                "fx": None,
                "worked_hours": None,
                "shrinkage": None,
            },
            "prod": [
                {"lang": default_langs[i], "hc": 0.0, "salary": 0.0, "up": 0.0}
                for i in range(6)
            ],
            "oh": [
                {"role": default_roles[i], "hc": 0.0, "salary": 0.0}
                for i in range(5)
            ],
        }

def get_month_data(month: str) -> dict:
    ensure_storage()
    return st.session_state["data"]["months"][month]

def save_widgets_to_month(month: str):
    """Save current widget values into central storage for that month."""
    md = get_month_data(month)

    # month-specific overrides
    md["inputs"]["fx"] = st.session_state.get("w_fx_month", md["inputs"]["fx"])
    md["inputs"]["worked_hours"] = st.session_state.get("w_wh_month", md["inputs"]["worked_hours"])
    md["inputs"]["shrinkage"] = st.session_state.get("w_sh_month", md["inputs"]["shrinkage"])

    # production
    for i in range(6):
        md["prod"][i]["lang"] = st.session_state.get(f"w_lang_{i}", md["prod"][i]["lang"])
        md["prod"][i]["hc"] = float(st.session_state.get(f"w_hc_{i}", md["prod"][i]["hc"]))
        md["prod"][i]["salary"] = float(st.session_state.get(f"w_sal_{i}", md["prod"][i]["salary"]))
        md["prod"][i]["up"] = float(st.session_state.get(f"w_up_{i}", md["prod"][i]["up"]))

    # overhead
    for i in range(5):
        md["oh"][i]["role"] = st.session_state.get(f"w_role_{i}", md["oh"][i]["role"])
        md["oh"][i]["hc"] = float(st.session_state.get(f"w_oh_hc_{i}", md["oh"][i]["hc"]))
        md["oh"][i]["salary"] = float(st.session_state.get(f"w_oh_sal_{i}", md["oh"][i]["salary"]))

def load_month_to_widgets(month: str, defaults: dict):
    """
    Load month data into session_state widget keys BEFORE widgets are created.
    Do NOT call this after widgets exist in the same run.
    """
    md = get_month_data(month)

    fx = md["inputs"]["fx"] if md["inputs"]["fx"] is not None else defaults["fx_default"]
    wh = md["inputs"]["worked_hours"] if md["inputs"]["worked_hours"] is not None else defaults["wh_default"]
    sh = md["inputs"]["shrinkage"] if md["inputs"]["shrinkage"] is not None else defaults["sh_default"]

    st.session_state["w_fx_month"] = float(fx)
    st.session_state["w_wh_month"] = float(wh)
    st.session_state["w_sh_month"] = float(sh)

    for i in range(6):
        st.session_state[f"w_lang_{i}"] = md["prod"][i]["lang"]
        st.session_state[f"w_hc_{i}"] = float(md["prod"][i]["hc"])
        st.session_state[f"w_sal_{i}"] = float(md["prod"][i]["salary"])
        st.session_state[f"w_up_{i}"] = float(md["prod"][i]["up"])

    for i in range(5):
        st.session_state[f"w_role_{i}"] = md["oh"][i]["role"]
        st.session_state[f"w_oh_hc_{i}"] = float(md["oh"][i]["hc"])
        st.session_state[f"w_oh_sal_{i}"] = float(md["oh"][i]["salary"])

# ============================
# Sidebar defaults (global)
# ============================
st.sidebar.header("Global Inputs")

wh_default = st.sidebar.number_input(
    "Worked Hours per Agent (Monthly) [default]",
    value=180.0, step=1.0, min_value=0.0
)
sh_default = st.sidebar.slider(
    "Shrinkage (%) [default]",
    min_value=0.0, max_value=0.5, value=0.15, step=0.01
)

st.sidebar.divider()
st.sidebar.subheader("Global Cost Drivers")

salary_multiplier = st.sidebar.number_input("Salary Multiplier", value=1.70, step=0.05, min_value=0.0)

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
fx_default = st.sidebar.number_input(
    f"FX Rate (1 {currency} = TRY) [default]",
    value=38.0 if currency == "EUR" else 35.0,
    step=0.1,
    min_value=0.0
)

defaults_pack = {"wh_default": wh_default, "sh_default": sh_default, "fx_default": fx_default}

# ============================
# Month selection + controlled save/load
# ============================
st.sidebar.divider()
st.sidebar.subheader("Month Filter")

ensure_storage()

if "selected_month" not in st.session_state:
    st.session_state["selected_month"] = MONTHS[0]
if "prev_month" not in st.session_state:
    st.session_state["prev_month"] = st.session_state["selected_month"]

def on_month_change():
    prev = st.session_state.get("prev_month", MONTHS[0])
    new = st.session_state.get("selected_month", MONTHS[0])
    save_widgets_to_month(prev)

    # Safe: mark pending reload; do NOT set widget keys here (widgets may already exist)
    st.session_state["pending_reload_month"] = new
    st.session_state["prev_month"] = new
    st.rerun()

st.sidebar.selectbox(
    "Select Month",
    MONTHS,
    key="selected_month",
    on_change=on_month_change
)

view_mode = st.sidebar.radio(
    "View",
    ["Selected Month", "All Months (Trend)"],
    index=0
)

selected_month = st.session_state["selected_month"]

# ============================
# Handle pending reload BEFORE widgets exist
# ============================
if st.session_state.get("pending_reload_month"):
    m = st.session_state.pop("pending_reload_month")
    load_month_to_widgets(m, defaults_pack)
    st.session_state["_widgets_loaded"] = m
    st.session_state["prev_month"] = m

# first-time load
if st.session_state.get("_widgets_loaded") != selected_month:
    load_month_to_widgets(selected_month, defaults_pack)
    st.session_state["_widgets_loaded"] = selected_month
    st.session_state["prev_month"] = selected_month

# ============================
# Core calcs
# ============================
def calculate_agent_cost(base_salary_try: float) -> float:
    bonus = base_salary_try * bonus_pct * bonus_multiplier
    gross = base_salary_try + bonus
    loaded = gross * salary_multiplier
    return loaded + meal_card

def compute_from_month_store(month: str):
    md = get_month_data(month)

    fx = md["inputs"]["fx"] if md["inputs"]["fx"] is not None else fx_default
    wh = md["inputs"]["worked_hours"] if md["inputs"]["worked_hours"] is not None else wh_default
    sh = md["inputs"]["shrinkage"] if md["inputs"]["shrinkage"] is not None else sh_default
    prod_hours = wh * (1 - sh)

    def try_from_currency_month(x: float) -> float:
        return x * float(fx)

    prod_rows = []
    total_prod_cost = 0.0
    total_revenue = 0.0

    for i in range(6):
        row = md["prod"][i]
        lang = row["lang"]
        hc = float(row["hc"])
        salary = float(row["salary"])
        up_cur = float(row["up"])

        up_try = try_from_currency_month(up_cur)
        cost_per = calculate_agent_cost(salary)
        total_cost = hc * cost_per
        revenue = hc * prod_hours * up_try
        margin = revenue - total_cost

        total_prod_cost += total_cost
        total_revenue += revenue

        prod_rows.append({
            "Month": month,
            "Language": lang,
            "HC": hc,
            "Base Salary (TRY)": salary,
            f"Unit Price ({currency})": up_cur,
            "FX Rate": float(fx),
            "Worked Hours": float(wh),
            "Shrinkage": float(sh),
            "Productive Hours": float(prod_hours),
            "Unit Price (TRY)": up_try,
            "Cost/Agent (TRY)": cost_per,
            "Total Cost (TRY)": total_cost,
            "Revenue (TRY)": revenue,
            "Margin (TRY)": margin,
            "Bonus %": bonus_pct,
            "Bonus Multiplier": bonus_multiplier,
            "Salary Multiplier": salary_multiplier,
            "Meal Card (TRY)": meal_card,
        })

    oh_rows = []
    total_oh = 0.0
    for i in range(5):
        row = md["oh"][i]
        role = row["role"]
        hc = float(row["hc"])
        salary = float(row["salary"])

        cost_per = calculate_agent_cost(salary) if hc > 0 else 0.0
        total_cost = hc * cost_per
        total_oh += total_cost

        oh_rows.append({
            "Month": month,
            "Role": role,
            "HC": hc,
            "Base Salary (TRY)": salary,
            "Cost/Head (TRY)": cost_per,
            "Total Cost (TRY)": total_cost,
            "Bonus %": bonus_pct,
            "Bonus Multiplier": bonus_multiplier,
            "Salary Multiplier": salary_multiplier,
            "Meal Card (TRY)": meal_card,
        })

    grand_cost = total_prod_cost + total_oh
    grand_margin = total_revenue - grand_cost
    gm = (grand_margin / total_revenue) if total_revenue > 0 else 0.0

    summary_df = pd.DataFrame([{
        "Month": month,
        "Total Production Cost (TRY)": total_prod_cost,
        "Total Overhead Cost (TRY)": total_oh,
        "Total Revenue (TRY)": total_revenue,
        "Grand Total Cost (TRY)": grand_cost,
        "Grand Margin (TRY)": grand_margin,
        "GM %": gm
    }])

    return pd.DataFrame(prod_rows), pd.DataFrame(oh_rows), summary_df

# ============================
# Month-level overrides UI
# ============================
st.subheader("Calculated Values")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Month", selected_month)
c2.number_input(f"FX for {selected_month} (TRY/{currency})", min_value=0.0, step=0.1, key="w_fx_month")
c3.number_input(f"Worked Hours for {selected_month}", min_value=0.0, step=1.0, key="w_wh_month")
c4.slider(f"Shrinkage for {selected_month}", min_value=0.0, max_value=0.5, step=0.01, key="w_sh_month")
c5.metric("Bonus Mult.", f"{bonus_multiplier:,.2f}")

# Save widgets to store each run
save_widgets_to_month(selected_month)

# Compute
prod_df_m, oh_df_m, summary_df_m = compute_from_month_store(selected_month)
s = summary_df_m.iloc[0]

# ============================
# Copy month helper
# ============================
st.divider()
with st.expander("📌 Helper: Copy this month to next month", expanded=False):
    idx = MONTHS.index(selected_month)
    next_month = MONTHS[idx + 1] if idx < 11 else None
    if next_month:
        if st.button(f"Copy {selected_month} → {next_month}"):
            st.session_state["data"]["months"][next_month] = {
                "inputs": dict(get_month_data(selected_month)["inputs"]),
                "prod": [dict(x) for x in get_month_data(selected_month)["prod"]],
                "oh": [dict(x) for x in get_month_data(selected_month)["oh"]],
            }
            st.session_state["pending_reload_month"] = next_month
            st.rerun()
    else:
        st.info("You're on Dec. No next month to copy into.")

# ============================
# Excel Template + Import
# ============================
st.sidebar.divider()
st.sidebar.subheader("Excel Import / Template")

def build_template_xlsx() -> bytes:
    inputs_df = pd.DataFrame({
        "Month": MONTHS,
        "FX": [fx_default]*12,
        "WorkedHours": [wh_default]*12,
        "Shrinkage": [sh_default]*12,
    })

    prod_rows = []
    for m in MONTHS:
        for l in default_langs:
            prod_rows.append({"Month": m, "Language": l, "HC": 0, "BaseSalaryTRY": 0, "UnitPriceCurrency": 0})
    prod_df = pd.DataFrame(prod_rows)

    oh_rows = []
    for m in MONTHS:
        for r in default_roles:
            oh_rows.append({"Month": m, "Role": r, "HC": 0, "BaseSalaryTRY": 0})
    oh_df = pd.DataFrame(oh_rows)

    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        inputs_df.to_excel(w, sheet_name="Inputs", index=False)
        prod_df.to_excel(w, sheet_name="Production", index=False)
        oh_df.to_excel(w, sheet_name="Overhead", index=False)
    return out.getvalue()

st.sidebar.download_button(
    "⬇️ Download Excel Template",
    data=build_template_xlsx(),
    file_name="budget_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

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

    # month overrides
    for _, row in inputs_df.iterrows():
        m = normalize_month(row.get("Month"))
        if not m:
            continue
        md = get_month_data(m)

        fx = row.get("FX")
        if pd.notna(fx):
            md["inputs"]["fx"] = float(fx)

        wh = row.get("WorkedHours")
        if pd.notna(wh):
            md["inputs"]["worked_hours"] = float(wh)

        sh = row.get("Shrinkage")
        if pd.notna(sh):
            shv = float(sh)
            if shv > 1:
                shv = shv / 100.0  # fix 15 -> 0.15
            md["inputs"]["shrinkage"] = shv

    # production
    lang_to_idx = {x.upper(): i for i, x in enumerate(default_langs)}
    for _, row in prod_df.iterrows():
        m = normalize_month(row.get("Month"))
        if not m:
            continue
        lang = str(row.get("Language", "")).strip().upper()
        if lang not in lang_to_idx:
            continue
        i = lang_to_idx[lang]
        md = get_month_data(m)

        if pd.notna(row.get("HC")):
            md["prod"][i]["hc"] = float(row.get("HC"))
        if pd.notna(row.get("BaseSalaryTRY")):
            md["prod"][i]["salary"] = float(row.get("BaseSalaryTRY"))
        if pd.notna(row.get("UnitPriceCurrency")):
            md["prod"][i]["up"] = float(row.get("UnitPriceCurrency"))

        md["prod"][i]["lang"] = default_langs[i]  # keep canonical

    # overhead
    role_to_idx = {x.strip().lower(): i for i, x in enumerate(default_roles)}
    for _, row in oh_df.iterrows():
        m = normalize_month(row.get("Month"))
        if not m:
            continue
        role = str(row.get("Role", "")).strip().lower()
        if role not in role_to_idx:
            continue
        i = role_to_idx[role]
        md = get_month_data(m)

        if pd.notna(row.get("HC")):
            md["oh"][i]["hc"] = float(row.get("HC"))
        if pd.notna(row.get("BaseSalaryTRY")):
            md["oh"][i]["salary"] = float(row.get("BaseSalaryTRY"))
        md["oh"][i]["role"] = default_roles[i]  # keep canonical

    # Trigger safe reload (do NOT set widget keys directly here)
    st.session_state["pending_reload_month"] = selected_month

if uploaded is not None:
    colA, colB = st.columns([1, 2])
    with colA:
        if st.button("✅ Apply import"):
            try:
                apply_import_xlsx(uploaded)
                st.success("Import applied. Reloading…")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
    with colB:
        st.info("Tip: Month can be Jan/January/1..12 or an Excel date.")

# ============================
# Production Blocks UI
# ============================
st.divider()
st.subheader("Production Blocks")

for i in range(6):
    with st.expander(f"#{i+1} Production — {default_langs[i]}  ({selected_month})", expanded=(i == 0)):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.text_input(f"Language Label #{i+1}", key=f"w_lang_{i}")
        with col2:
            st.number_input("HC", min_value=0.0, step=1.0, key=f"w_hc_{i}")
        with col3:
            st.number_input("Base Salary (TRY)", min_value=0.0, step=500.0, key=f"w_sal_{i}")
        with col4:
            st.number_input(f"Unit Price ({currency})", min_value=0.0, step=0.1, key=f"w_up_{i}")

# ============================
# Overhead UI
# ============================
st.divider()
st.subheader("Overhead")

for i in range(5):
    with st.expander(f"Overhead #{i+1}  ({selected_month})", expanded=(i == 0)):
        oh1, oh2, oh3 = st.columns(3)
        with oh1:
            st.text_input("Role", key=f"w_role_{i}")
        with oh2:
            st.number_input("OH HC", min_value=0.0, step=1.0, key=f"w_oh_hc_{i}")
        with oh3:
            st.number_input("Base Salary (TRY)", min_value=0.0, step=500.0, key=f"w_oh_sal_{i}")

# Save edits and recompute
save_widgets_to_month(selected_month)
prod_df_m, oh_df_m, summary_df_m = compute_from_month_store(selected_month)
s = summary_df_m.iloc[0]

# ============================
# Final Summary
# ============================
st.divider()
st.subheader("Final Summary")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Production Cost (TRY)", fmt0(s["Total Production Cost (TRY)"]))
s2.metric("Total Overhead Cost (TRY)", fmt0(s["Total Overhead Cost (TRY)"]))
s3.metric("Total Revenue (TRY)", fmt0(s["Total Revenue (TRY)"]))
s4.metric("GM %", f"{s['GM %']*100:.1f}%")

t1, t2, t3 = st.columns(3)
t1.metric("Grand Total Cost (TRY)", fmt0(s["Grand Total Cost (TRY)"]))
t2.metric("Grand Margin (TRY)", fmt0(s["Grand Margin (TRY)"]))
fx_effective = get_month_data(selected_month)["inputs"]["fx"] if get_month_data(selected_month)["inputs"]["fx"] is not None else fx_default
t3.metric("Currency + FX", f"{currency} @ {fx_effective:,.2f} TRY")

# ============================
# Charts
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

if view_mode == "All Months (Trend)":
    all_sum = []
    for m in MONTHS:
        _, _, sm = compute_from_month_store(m)
        all_sum.append(sm)
    all_sum_df = pd.concat(all_sum, ignore_index=True)

    st.markdown("#### All Months Trend")
    trend_df = all_sum_df.set_index("Month")[["Total Revenue (TRY)", "Grand Total Cost (TRY)", "Grand Margin (TRY)"]]
    st.line_chart(trend_df)

    gm_trend = (all_sum_df.set_index("Month")[["GM %"]] * 100.0).rename(columns={"GM %": "GM%"})
    st.line_chart(gm_trend)

# ============================
# Tables
# ============================
with st.expander("Show detailed tables (Selected Month)"):
    st.markdown("#### Production")
    st.dataframe(prod_df_m, use_container_width=True)
    st.markdown("#### Overhead")
    st.dataframe(oh_df_m, use_container_width=True)

# ============================
# Export
# ============================
st.divider()
st.subheader("Export")

def build_excel_export() -> bytes:
    inputs_df = pd.DataFrame([{
        "Selected Month": selected_month,
        "Worked Hours (default)": wh_default,
        "Shrinkage (default)": sh_default,
        "Salary Multiplier": salary_multiplier,
        "Bonus %": bonus_pct,
        "Bonus Multiplier": bonus_multiplier,
        "Meal Card (TRY)": meal_card,
        "Currency": currency,
        "FX (default)": fx_default,
    }])

    all_sum = []
    for m in MONTHS:
        _, _, sm = compute_from_month_store(m)
        all_sum.append(sm)
    all_months_summary_df = pd.concat(all_sum, ignore_index=True)

    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        prod_df_m.to_excel(writer, sheet_name=f"Prod_{selected_month}", index=False)
        oh_df_m.to_excel(writer, sheet_name=f"OH_{selected_month}", index=False)
        summary_df_m.to_excel(writer, sheet_name=f"Summary_{selected_month}", index=False)
        all_months_summary_df.to_excel(writer, sheet_name="Summary_AllMonths", index=False)

    return out.getvalue()

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
