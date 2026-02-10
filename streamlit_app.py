# ============================
# BUDGET APP (LOCKED CORE + MoM ANALYSIS)
# ============================

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
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
default_langs = ["DE","EN","TR","FR","IT","NL"]
default_roles = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# ============================
# Helpers
# ============================
def fmt0(x): return f"{x:,.0f}"

def ensure_storage():
    if "data" in st.session_state:
        return
    st.session_state["data"] = {"months": {}}
    for m in MONTHS:
        st.session_state["data"]["months"][m] = {
            "inputs": {"fx": None, "worked_hours": None, "shrinkage": None},
            "prod": [{"lang":l,"hc":0,"salary":0,"up":0} for l in default_langs],
            "oh": [{"role":r,"hc":0,"salary":0} for r in default_roles],
        }

def get_month_data(m):
    ensure_storage()
    return st.session_state["data"]["months"][m]

# ============================
# Sidebar defaults (global)
# ============================
st.sidebar.header("Global Inputs")

wh_default = st.sidebar.number_input("Worked Hours per Agent (Monthly)",180.0)
sh_default = st.sidebar.slider("Shrinkage",0.0,0.5,0.15)

st.sidebar.divider()
salary_multiplier = st.sidebar.number_input("Salary Multiplier",1.70)
bonus_pct = st.sidebar.number_input("Bonus %",0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier",1.00)
meal_card = st.sidebar.number_input("Meal Card (TRY)",5850.0)

st.sidebar.divider()
currency = st.sidebar.selectbox("Unit Price Currency",["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default",38.0)

# ============================
# Month selection
# ============================
ensure_storage()
if "selected_month" not in st.session_state:
    st.session_state["selected_month"] = MONTHS[0]

selected_month = st.sidebar.selectbox("Select Month", MONTHS, key="selected_month")

# ============================
# Core calculations
# ============================
def calculate_agent_cost(base_salary):
    bonus = base_salary * bonus_pct * bonus_multiplier
    return ((base_salary + bonus) * salary_multiplier) + meal_card

def compute_from_month_store(month):
    md = get_month_data(month)
    fx = md["inputs"]["fx"] or fx_default
    wh = md["inputs"]["worked_hours"] or wh_default
    sh = md["inputs"]["shrinkage"] or sh_default
    prod_hours = wh * (1 - sh)

    total_prod_cost = total_revenue = total_oh = 0

    for r in md["prod"]:
        hc = r["hc"]
        up_try = r["up"] * fx
        cost = hc * calculate_agent_cost(r["salary"])
        revenue = hc * prod_hours * up_try
        total_prod_cost += cost
        total_revenue += revenue

    for r in md["oh"]:
        total_oh += r["hc"] * calculate_agent_cost(r["salary"])

    total_cost = total_prod_cost + total_oh
    margin = total_revenue - total_cost
    gm = margin / total_revenue if total_revenue > 0 else 0

    return {
        "Revenue": total_revenue,
        "Total Cost": total_cost,
        "Margin": margin,
        "GM": gm
    }

# ============================
# FINAL SUMMARY
# ============================
st.divider()
st.subheader("Final Summary")

cur = compute_from_month_store(selected_month)

s1,s2,s3,s4 = st.columns(4)
s1.metric("Revenue (TRY)", fmt0(cur["Revenue"]))
s2.metric("Total Cost (TRY)", fmt0(cur["Total Cost"]))
s3.metric("Margin (TRY)", fmt0(cur["Margin"]))
s4.metric("GM %", f"{cur['GM']*100:.1f}%")

# =====================================================
# 🔵 MONTH-OVER-MONTH ANALYSIS (NEW)
# =====================================================
st.divider()
st.subheader("📊 Month-over-Month Analysis")

idx = MONTHS.index(selected_month)
default_prev = MONTHS[idx-1] if idx > 0 else MONTHS[0]

compare_month = st.selectbox(
    "Compare with month",
    MONTHS,
    index=MONTHS.index(default_prev)
)

prev = compute_from_month_store(compare_month)

rev_delta = cur["Revenue"] - prev["Revenue"]
cost_delta = cur["Total Cost"] - prev["Total Cost"]
margin_delta = cur["Margin"] - prev["Margin"]
gm_delta = (cur["GM"] - prev["GM"]) * 100

d1,d2,d3,d4 = st.columns(4)
d1.metric("Revenue Δ (TRY)", fmt0(rev_delta),
          f"{(rev_delta/prev['Revenue']*100 if prev['Revenue'] else 0):.1f}%")
d2.metric("Cost Δ (TRY)", fmt0(cost_delta))
d3.metric("Margin Δ (TRY)", fmt0(margin_delta))
d4.metric("GM Δ (pp)", f"{gm_delta:+.2f}")

bridge_df = pd.DataFrame([
    {"Driver":"Revenue change","Impact (TRY)":rev_delta},
    {"Driver":"Cost change","Impact (TRY)":-cost_delta},
    {"Driver":"Net Margin impact","Impact (TRY)":margin_delta},
])

st.markdown("### Margin Bridge")
st.dataframe(bridge_df, use_container_width=True)

# ============================
# Charts
# ============================
st.divider()
st.subheader("Summary Graphics")

chart_df = pd.DataFrame(
    {"TRY":[cur["Revenue"],cur["Total Cost"],cur["Margin"]]},
    index=["Revenue","Cost","Margin"]
)
st.bar_chart(chart_df)

# ============================
# END
# ============================
