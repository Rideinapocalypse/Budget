import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# ============================
# Constants
# ============================

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

LANGS = ["DE","EN","TR","FR","IT","NL"]
ROLES = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# ============================
# Sidebar – Global Inputs
# ============================

st.sidebar.header("Global Inputs")

worked_hours_default = st.sidebar.number_input(
    "Worked Hours (Monthly)", value=180.0
)

shrinkage_default = st.sidebar.slider(
    "Shrinkage", 0.0, 0.5, 0.15
)

salary_multiplier = st.sidebar.number_input(
    "Salary Multiplier", value=1.7
)

bonus_pct = st.sidebar.number_input(
    "Bonus %", value=0.10
)

bonus_multiplier = st.sidebar.number_input(
    "Bonus Multiplier", value=1.0
)

meal_card = st.sidebar.number_input(
    "Meal Card (TRY)", value=5850.0
)

currency = st.sidebar.selectbox("Unit Price Currency",["EUR","USD"])

fx_default = st.sidebar.number_input(
    f"FX Default ({currency}/TRY)", value=38.0
)

# ============================
# Advanced Drivers
# ============================

st.sidebar.divider()
st.sidebar.subheader("Advanced Drivers")

absenteeism = st.sidebar.number_input(
    "Absenteeism %", value=0.10
)

attrition = st.sidebar.number_input(
    "Attrition %", value=0.07
)

overtime_hours = st.sidebar.number_input(
    "Overtime Hours (per HC)", value=0.0
)

billing_model = st.sidebar.selectbox(
    "Invoicing Model",
    ["Full Productive Hours","50% Billing","Fixed HC"]
)

# ============================
# Session Storage
# ============================

if "data" not in st.session_state:
    st.session_state["data"] = {
        m:{
            "fx":None,
            "wh":None,
            "sh":None,
            "prod":[{"hc":0,"salary":0,"up":0} for _ in range(6)],
            "oh":[{"hc":0,"salary":0} for _ in range(5)]
        } for m in MONTHS
    }

selected_month = st.sidebar.selectbox("Select Month",MONTHS)

md = st.session_state["data"][selected_month]

# ============================
# Month Overrides
# ============================

col1,col2,col3 = st.columns(3)

md["fx"] = col1.number_input(
    "FX (Month)",
    value=md["fx"] if md["fx"] else fx_default,
    key=f"fx_{selected_month}"
)

md["wh"] = col2.number_input(
    "Worked Hours (Month)",
    value=md["wh"] if md["wh"] else worked_hours_default,
    key=f"wh_{selected_month}"
)

md["sh"] = col3.number_input(
    "Shrinkage (Month)",
    value=md["sh"] if md["sh"] else shrinkage_default,
    key=f"sh_{selected_month}"
)

# ============================
# Production Blocks
# ============================

st.subheader("Production")

for i in range(6):
    with st.expander(LANGS[i],expanded=(i==0)):
        c1,c2,c3 = st.columns(3)

        md["prod"][i]["hc"] = c1.number_input(
            "HC",
            value=md["prod"][i]["hc"],
            key=f"hc_{selected_month}_{i}"
        )

        md["prod"][i]["salary"] = c2.number_input(
            "Salary",
            value=md["prod"][i]["salary"],
            key=f"salary_{selected_month}_{i}"
        )

        md["prod"][i]["up"] = c3.number_input(
            "Unit Price",
            value=md["prod"][i]["up"],
            key=f"up_{selected_month}_{i}"
        )

# ============================
# Overhead
# ============================

st.subheader("Overhead")

for i in range(5):
    with st.expander(ROLES[i],expanded=(i==0)):
        c1,c2 = st.columns(2)

        md["oh"][i]["hc"] = c1.number_input(
            "OH HC",
            value=md["oh"][i]["hc"],
            key=f"ohhc_{selected_month}_{i}"
        )

        md["oh"][i]["salary"] = c2.number_input(
            "Base Salary",
            value=md["oh"][i]["salary"],
            key=f"ohsalary_{selected_month}_{i}"
        )

# ============================
# Calculations
# ============================

fx = md["fx"]
wh = md["wh"]
sh = md["sh"]

effective_hours = wh * (1 - sh) * (1 - absenteeism)

if billing_model == "50% Billing":
    effective_hours *= 0.5

total_revenue = 0
total_prod_cost = 0

for row in md["prod"]:
    hc = row["hc"]
    salary = row["salary"]
    up = row["up"]

    bonus = salary * bonus_pct * bonus_multiplier
    gross = salary + bonus
    loaded = gross * salary_multiplier
    cost_per = loaded + meal_card

    revenue = hc * effective_hours * up * fx

    if overtime_hours > 0:
        revenue += hc * overtime_hours * up * fx
        cost_per += (salary/hour if False else 0)

    total_revenue += revenue
    total_prod_cost += hc * cost_per

total_oh = 0
for row in md["oh"]:
    hc = row["hc"]
    salary = row["salary"]
    bonus = salary * bonus_pct * bonus_multiplier
    gross = salary + bonus
    loaded = gross * salary_multiplier
    cost_per = loaded + meal_card
    total_oh += hc * cost_per

grand_cost = total_prod_cost + total_oh
grand_margin = total_revenue - grand_cost
gm = grand_margin/total_revenue if total_revenue>0 else 0

# ============================
# Summary
# ============================

st.subheader("Final Summary")

s1,s2,s3,s4 = st.columns(4)
s1.metric("Revenue",f"{total_revenue:,.0f}")
s2.metric("Total Cost",f"{grand_cost:,.0f}")
s3.metric("Margin",f"{grand_margin:,.0f}")
s4.metric("GM %",f"{gm*100:.1f}%")

# ============================
# MoM Analysis
# ============================

st.divider()
st.subheader("Month-over-Month")

compare_month = st.selectbox("Compare with",MONTHS,index=0)

prev_md = st.session_state["data"][compare_month]

def compute_month(md):
    fx = md["fx"] or fx_default
    wh = md["wh"] or worked_hours_default
    sh = md["sh"] or shrinkage_default
    hours = wh*(1-sh)*(1-absenteeism)

    rev=0
    cost=0

    for row in md["prod"]:
        rev += row["hc"]*hours*row["up"]*fx
        bonus = row["salary"]*bonus_pct*bonus_multiplier
        gross = row["salary"]+bonus
        loaded = gross*salary_multiplier
        cost += row["hc"]*(loaded+meal_card)

    for row in md["oh"]:
        bonus = row["salary"]*bonus_pct*bonus_multiplier
        gross = row["salary"]+bonus
        loaded = gross*salary_multiplier
        cost += row["hc"]*(loaded+meal_card)

    margin=rev-cost
    gm=margin/rev if rev>0 else 0
    return rev,cost,margin,gm

cur_rev,cur_cost,cur_margin,cur_gm = compute_month(md)
prev_rev,prev_cost,prev_margin,prev_gm = compute_month(prev_md)

c1,c2,c3,c4 = st.columns(4)
c1.metric("Revenue Δ",f"{cur_rev-prev_rev:,.0f}")
c2.metric("Cost Δ",f"{cur_cost-prev_cost:,.0f}")
c3.metric("Margin Δ",f"{cur_margin-prev_margin:,.0f}")
c4.metric("GM Δ (pp)",f"{(cur_gm-prev_gm)*100:.2f}")
