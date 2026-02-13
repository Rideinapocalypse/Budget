import streamlit as st
import pandas as pd
from io import BytesIO

# ============================
# Page config
# ============================
st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# ============================
# UI Styling (compact blocks)
# ============================
st.markdown("""
<style>
div.block-container {padding-top: 1.0rem; padding-bottom: 1.0rem; max-width: 1400px;}
div[data-testid="stVerticalBlock"] > div {gap: 0.35rem;}
[data-testid="stMetric"] {padding: 6px 10px;}
[data-testid="stMetricLabel"] {font-size: 0.80rem;}
[data-testid="stMetricValue"] {font-size: 1.05rem;}
</style>
""", unsafe_allow_html=True)

# ============================
# Constants
# ============================
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
default_langs = ["DE","EN","TR","FR","IT","NL"]
default_roles = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# ============================
# Storage
# ============================
def ensure_storage():
    if "data" in st.session_state:
        return

    st.session_state["data"] = {"months": {}}
    for m in MONTHS:
        st.session_state["data"]["months"][m] = {
            "inputs": {
                "fx": None,
                "worked_hours": None,
                "shrinkage": None,
                "absenteeism": 0.10,
                "attrition": 0.07,
                "ot_pct": 0.0,
                "ot_multiplier": 1.5,
                "invoicing_model": "Productive Hours"
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

def get_month_data(m):
    ensure_storage()
    return st.session_state["data"]["months"][m]

# ============================
# Cost Logic
# ============================
def calculate_agent_cost(base_salary):
    bonus = base_salary * bonus_pct * bonus_multiplier
    gross = base_salary + bonus
    loaded = gross * salary_multiplier
    return loaded + meal_card

# ============================
# Sidebar Global Inputs
# ============================
st.sidebar.header("Global Inputs")

wh_default = st.sidebar.number_input("Worked Hours (default)", value=180.0)
sh_default = st.sidebar.slider("Shrinkage (default)", 0.0, 0.5, 0.15)

st.sidebar.divider()
st.sidebar.subheader("Global Cost Drivers")

salary_multiplier = st.sidebar.number_input("Salary Multiplier", value=1.70)
bonus_pct = st.sidebar.number_input("Bonus %", value=0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier", value=1.00)
meal_card = st.sidebar.number_input("Meal Card (TRY)", value=5850.0)

st.sidebar.divider()
currency = st.sidebar.selectbox("Currency", ["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default", value=38.0)

# ============================
# Month Selection
# ============================
ensure_storage()

selected_month = st.sidebar.selectbox("Month", MONTHS)
view_mode = st.sidebar.radio("View", ["Selected Month","All Months"])

md = get_month_data(selected_month)

# ============================
# Advanced Drivers (Grouped UI)
# ============================
st.subheader("📌 Advanced Drivers")

c1,c2,c3,c4 = st.columns(4)
md["inputs"]["absenteeism"] = c1.slider("Absenteeism",0.0,0.5,md["inputs"]["absenteeism"])
md["inputs"]["attrition"] = c2.slider("Attrition",0.0,0.5,md["inputs"]["attrition"])
md["inputs"]["ot_pct"] = c3.number_input("Overtime %", value=md["inputs"]["ot_pct"])
md["inputs"]["ot_multiplier"] = c4.number_input("OT Multiplier", value=md["inputs"]["ot_multiplier"])

md["inputs"]["invoicing_model"] = st.selectbox(
    "Invoicing Model",
    ["Productive Hours","Worked Hours","FTE Flat"],
    index=["Productive Hours","Worked Hours","FTE Flat"].index(md["inputs"]["invoicing_model"])
)

# ============================
# Production UI
# ============================
st.subheader("Production Blocks")

for i in range(6):
    with st.expander(default_langs[i], expanded=(i==0)):
        col1,col2,col3,col4 = st.columns(4)
        md["prod"][i]["hc"] = col1.number_input("HC", value=md["prod"][i]["hc"])
        md["prod"][i]["salary"] = col2.number_input("Salary", value=md["prod"][i]["salary"])
        md["prod"][i]["up"] = col3.number_input("Unit Price", value=md["prod"][i]["up"])

# ============================
# Core Compute Engine
# ============================
def compute_month(m):
    md = get_month_data(m)

    fx = md["inputs"]["fx"] or fx_default
    wh = md["inputs"]["worked_hours"] or wh_default
    sh = md["inputs"]["shrinkage"] or sh_default

    abs_r = md["inputs"]["absenteeism"]
    attr = md["inputs"]["attrition"]
    ot = md["inputs"]["ot_pct"]
    ot_mult = md["inputs"]["ot_multiplier"]
    model = md["inputs"]["invoicing_model"]

    ramp = 0.50
    productive_hours = wh * (1 - sh - abs_r)

    total_cost = 0
    total_rev = 0

    for row in md["prod"]:
        hc = row["hc"]
        salary = row["salary"]
        up_try = row["up"] * fx

        lost = hc * attr
        billable = hc - lost * (1-ramp)

        cost = hc * calculate_agent_cost(salary)

        if model=="Productive Hours":
            revenue = billable * productive_hours * up_try
        elif model=="Worked Hours":
            revenue = billable * wh * up_try
        else:
            revenue = billable * up_try

        if ot>0:
            ot_hours = wh * ot
            revenue += hc * ot_hours * up_try
            base_hour_cost = calculate_agent_cost(salary)/wh if wh>0 else 0
            cost += hc * ot_hours * base_hour_cost * (ot_mult-1)

        total_cost += cost
        total_rev += revenue

    margin = total_rev-total_cost
    gm = margin/total_rev if total_rev>0 else 0

    return total_rev,total_cost,margin,gm

rev,cost,margin,gm = compute_month(selected_month)

# ============================
# Summary
# ============================
st.subheader("Summary")
s1,s2,s3,s4 = st.columns(4)
s1.metric("Revenue", f"{rev:,.0f}")
s2.metric("Cost", f"{cost:,.0f}")
s3.metric("Margin", f"{margin:,.0f}")
s4.metric("GM %", f"{gm*100:.1f}%")

# ============================
# Trend
# ============================
if view_mode=="All Months":
    trend=[]
    for m in MONTHS:
        r,c,mg,g=compute_month(m)
        trend.append({"Month":m,"Revenue":r,"Cost":c,"Margin":mg})
    trend_df=pd.DataFrame(trend).set_index("Month")
    st.line_chart(trend_df)
