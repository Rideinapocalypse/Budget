import streamlit as st
import pandas as pd
from io import BytesIO

# ============================
# Page config
# ============================
st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# ============================
# GLOBAL INPUTS (SIDEBAR)
# ============================
st.sidebar.header("Global Inputs")

worked_hours = st.sidebar.number_input(
    "Worked Hours per Agent (Monthly)", value=180.0, step=1.0, min_value=0.0
)

shrinkage = st.sidebar.slider(
    "Shrinkage (%)", min_value=0.0, max_value=0.5, value=0.15, step=0.01
)

productive_hours = worked_hours * (1 - shrinkage)

st.sidebar.divider()
st.sidebar.subheader("Global Cost Drivers")

salary_multiplier = st.sidebar.number_input(
    "Salary Multiplier", value=1.70, step=0.05, min_value=0.0
)

bonus_pct = st.sidebar.number_input(
    "Bonus % (of Base Salary)", value=0.10, step=0.01, min_value=0.0, max_value=5.0
)

# ✅ ADDED: Bonus Multiplier (adjustable like other costs)
bonus_multiplier = st.sidebar.number_input(
    "Bonus Multiplier", value=1.00, step=0.05, min_value=0.0
)

meal_card = st.sidebar.number_input(
    "Meal Card per Agent (Monthly TRY)", value=5850.0, step=100.0, min_value=0.0
)

st.sidebar.divider()
currency = st.sidebar.selectbox("Unit Price Currency", ["EUR", "USD"])

fx_rate = st.sidebar.number_input(
    f"FX Rate (1 {currency} = TRY)",
    value=38.0 if currency == "EUR" else 35.0,
    step=0.1,
    min_value=0.0
)

# ============================
# Helper functions
# ============================
def calculate_agent_cost(base_salary_try: float) -> float:
    """
    Fully loaded monthly cost per head in TRY:
    (base_salary + base_salary*bonus_pct*bonus_multiplier) * salary_multiplier + meal_card
    """
    bonus = base_salary_try * bonus_pct * bonus_multiplier  # ✅ bonus multiplier applied here
    gross = base_salary_try + bonus
    loaded = gross * salary_multiplier
    return loaded + meal_card

def try_from_currency(amount_in_currency: float) -> float:
    return amount_in_currency * fx_rate

def fmt0(x: float) -> str:
    return f"{x:,.0f}"

# ============================
# CALCULATED VALUES
# ============================
st.subheader("Calculated Values")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Worked Hours / Agent", f"{worked_hours:,.2f}")
c2.metric("Productive Hours / Agent", f"{productive_hours:,.2f}")
c3.metric("Shrinkage", f"{shrinkage*100:.1f}%")
c4.metric("Bonus Multiplier", f"{bonus_multiplier:,.2f}")  # ✅ visible confirmation

# ============================
# PRODUCTION BLOCKS
# ============================
st.divider()
st.subheader("Production Blocks")

total_prod_cost = 0.0
total_revenue = 0.0

default_langs = ["DE", "EN", "TR", "FR", "IT", "NL"]
prod_rows = []

for i in range(6):
    st.markdown(f"### #{i+1} Production Block — {default_langs[i]}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        lang = st.text_input(f"Language Label #{i+1}", value=default_langs[i], key=f"lang_{i}")
    with col2:
        hc = st.number_input(f"HC ({lang})", min_value=0.0, step=1.0, key=f"hc_{i}")
    with col3:
        salary = st.number_input(f"Base Salary ({lang}) TRY", min_value=0.0, step=500.0, key=f"salary_{i}")
    with col4:
        unit_price_cur = st.number_input(
            f"Unit Price ({lang}) in {currency}", min_value=0.0, step=0.1, key=f"price_{i}"
        )

    unit_price_try = try_from_currency(unit_price_cur)
    cost_per_agent = calculate_agent_cost(salary)
    cost_total = hc * cost_per_agent
    revenue = hc * productive_hours * unit_price_try
    margin = revenue - cost_total

    total_prod_cost += cost_total
    total_revenue += revenue

    prod_rows.append({
        "Language": lang,
        "HC": hc,
        "Base Salary (TRY)": salary,
        "Unit Price (cur)": unit_price_cur,
        "Currency": currency,
        "FX Rate": fx_rate,
        "Unit Price (TRY)": unit_price_try,
        "Worked Hours": worked_hours,
        "Shrinkage": shrinkage,
        "Productive Hours": productive_hours,
        "Bonus %": bonus_pct,
        "Bonus Multiplier": bonus_multiplier,  # ✅ export it
        "Salary Multiplier": salary_multiplier,
        "Meal Card": meal_card,
        "Cost/Agent (TRY)": cost_per_agent,
        "Total Cost (TRY)": cost_total,
        "Revenue (TRY)": revenue,
        "Margin (TRY)": margin,
    })

    r1, r2, r3, r4 = st.columns(4)
    r1.metric(f"{lang} Cost/Agent (TRY)", fmt0(cost_per_agent))
    r2.metric(f"{lang} Total Cost (TRY)", fmt0(cost_total))
    r3.metric(f"{lang} Revenue (TRY)", fmt0(revenue))
    r4.metric(f"{lang} Margin (TRY)", fmt0(margin))

    st.caption(
        f"Unit Price TRY: {unit_price_try:,.2f} | "
        f"Revenue = HC × productive_hours × unit_price_try"
    )
    st.divider()

prod_df = pd.DataFrame(prod_rows)

# ============================
# OVERHEAD SECTION
# ============================
st.subheader("Overhead")
st.caption("Overhead uses the same fully loaded cost logic (salary + bonus + multiplier + meal card).")

oh_rows = []
total_overhead = 0.0

default_roles = ["Team Manager", "QA", "Ops", "Trainer", "RTA/WFM"]

for i in range(5):
    oh1, oh2, oh3 = st.columns(3)

    with oh1:
        role = st.text_input(
            f"Role #{i+1}",
            value=default_roles[i] if i < len(default_roles) else f"Role {i+1}",
            key=f"oh_role_{i}"
        )
    with oh2:
        oh_hc = st.number_input(f"OH HC ({role})", min_value=0.0, step=1.0, key=f"oh_hc_{i}")
    with oh3:
        oh_salary = st.number_input(f"Base Salary ({role}) TRY", min_value=0.0, step=500.0, key=f"oh_salary_{i}")

    oh_cost_per = calculate_agent_cost(oh_salary) if oh_hc > 0 else 0.0
    oh_cost_total = oh_hc * oh_cost_per

    total_overhead += oh_cost_total

    oh_rows.append({
        "Role": role,
        "HC": oh_hc,
        "Base Salary (TRY)": oh_salary,
        "Bonus %": bonus_pct,
        "Bonus Multiplier": bonus_multiplier,  # ✅ export it
        "Salary Multiplier": salary_multiplier,
        "Meal Card": meal_card,
        "Cost/Head (TRY)": oh_cost_per,
        "Total Cost (TRY)": oh_cost_total,
    })

    o1, o2, o3 = st.columns(3)
    o1.metric(f"{role} Cost/Head (TRY)", fmt0(oh_cost_per))
    o2.metric(f"{role} Total Cost (TRY)", fmt0(oh_cost_total))
    o3.metric(f"{role} HC", f"{oh_hc:,.0f}")

    st.divider()

oh_df = pd.DataFrame(oh_rows)

# ============================
# FINAL SUMMARY
# ============================
st.subheader("Final Summary")

grand_cost = total_prod_cost + total_overhead
grand_margin = total_revenue - grand_cost
gm_pct = (grand_margin / total_revenue) if total_revenue > 0 else 0.0

s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Production Cost (TRY)", fmt0(total_prod_cost))
s2.metric("Total Overhead Cost (TRY)", fmt0(total_overhead))
s3.metric("Total Revenue (TRY)", fmt0(total_revenue))
s4.metric("GM %", f"{gm_pct*100:.1f}%")

t1, t2, t3 = st.columns(3)
t1.metric("Grand Total Cost (TRY)", fmt0(grand_cost))
t2.metric("Grand Margin (TRY)", fmt0(grand_margin))
t3.metric("Currency + FX", f"{currency} @ {fx_rate:,.2f} TRY")

# ============================
# SUMMARY GRAPHICS
# ============================
st.divider()
st.subheader("Summary Graphics")

summary_bar = pd.DataFrame(
    {"TRY": [total_revenue, grand_cost, grand_margin]},
    index=["Revenue", "Total Cost", "Margin"]
)
st.bar_chart(summary_bar)

gm_df = pd.DataFrame({"GM%": [gm_pct * 100.0]}, index=["GM %"])
st.bar_chart(gm_df)

with st.expander("Show detailed tables (Production + Overhead)"):
    st.markdown("#### Production Table")
    st.dataframe(prod_df, use_container_width=True)
    st.markdown("#### Overhead Table")
    st.dataframe(oh_df, use_container_width=True)

# ============================
# EXCEL EXPORT
# ============================
st.divider()
st.subheader("Export")

def build_excel_file() -> bytes:
    inputs_df = pd.DataFrame([{
        "Worked Hours": worked_hours,
        "Shrinkage": shrinkage,
        "Productive Hours": productive_hours,
        "Salary Multiplier": salary_multiplier,
        "Bonus %": bonus_pct,
        "Bonus Multiplier": bonus_multiplier,  # ✅ export it
        "Meal Card (TRY)": meal_card,
        "Currency": currency,
        "FX Rate": fx_rate,
    }])

    summary_df = pd.DataFrame([{
        "Total Production Cost (TRY)": total_prod_cost,
        "Total Overhead Cost (TRY)": total_overhead,
        "Total Revenue (TRY)": total_revenue,
        "Grand Total Cost (TRY)": grand_cost,
        "Grand Margin (TRY)": grand_margin,
        "GM %": gm_pct,
    }])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        prod_df.to_excel(writer, sheet_name="Production", index=False)
        oh_df.to_excel(writer, sheet_name="Overhead", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    return output.getvalue()

excel_bytes = build_excel_file()

st.download_button(
    label="⬇️ Download Excel (.xlsx)",
    data=excel_bytes,
    file_name="budget_app_export.xlsx",
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
