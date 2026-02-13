import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# =========================
# CONSTANTS
# =========================

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

LANGS = ["DE","EN","TR","FR","IT","NL"]
ROLES = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# =========================
# SIDEBAR
# =========================

st.sidebar.header("Global Inputs")

worked_hours_default = st.sidebar.number_input("Worked Hours (Default)", 0.0, 500.0, 180.0)
shrinkage_default = st.sidebar.number_input("Shrinkage (Default)", 0.0, 1.0, 0.15)

salary_multiplier = st.sidebar.number_input("Salary Multiplier", 0.0, 10.0, 1.7)
bonus_pct = st.sidebar.number_input("Bonus %", 0.0, 1.0, 0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier", 0.0, 10.0, 1.0)
meal_card = st.sidebar.number_input("Meal Card (TRY)", 0.0, 50000.0, 5850.0)

currency = st.sidebar.selectbox("Unit Price Currency",["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default", 0.0, 1000.0, 38.0)

st.sidebar.divider()

absenteeism = st.sidebar.number_input("Absenteeism %", 0.0, 1.0, 0.10)
attrition = st.sidebar.number_input("Attrition %", 0.0, 1.0, 0.07)
overtime_hours = st.sidebar.number_input("Overtime Hours per HC", 0.0, 200.0, 0.0)

billing_model = st.sidebar.selectbox(
    "Invoicing Model",
    ["Full Productive Hours","50% Billing","Fixed HC"]
)

selected_month = st.sidebar.selectbox("Select Month", MONTHS)

# =========================
# SESSION STORAGE INIT
# =========================

if "data" not in st.session_state:
    st.session_state["data"] = {
        m:{
            "fx":fx_default,
            "wh":worked_hours_default,
            "sh":shrinkage_default,
            "prod":[{"hc":0.0,"salary":0.0,"up":0.0} for _ in range(6)],
            "oh":[{"hc":0.0,"salary":0.0} for _ in range(5)]
        } for m in MONTHS
    }

md = st.session_state["data"][selected_month]

# =========================
# MONTH OVERRIDES
# =========================

st.subheader(f"{selected_month} Inputs")

c1,c2,c3 = st.columns(3)

md["fx"] = c1.number_input("FX (Month)", 0.0, 1000.0, float(md["fx"]))
md["wh"] = c2.number_input("Worked Hours (Month)", 0.0, 500.0, float(md["wh"]))
md["sh"] = c3.number_input("Shrinkage (Month)", 0.0, 1.0, float(md["sh"]))

# =========================
# PRODUCTION
# =========================

st.subheader("Production")

for i in range(6):
    with st.expander(LANGS[i], expanded=(i==0)):
        c1,c2,c3 = st.columns(3)
        md["prod"][i]["hc"] = c1.number_input(
            f"HC_{i}",0.0,10000.0,float(md["prod"][i]["hc"]),key=f"hc_{selected_month}_{i}"
        )
        md["prod"][i]["salary"] = c2.number_input(
            f"Salary_{i}",0.0,200000.0,float(md["prod"][i]["salary"]),key=f"sal_{selected_month}_{i}"
        )
        md["prod"][i]["up"] = c3.number_input(
            f"UnitPrice_{i}",0.0,10000.0,float(md["prod"][i]["up"]),key=f"up_{selected_month}_{i}"
        )

# =========================
# OVERHEAD
# =========================

st.subheader("Overhead")

for i in range(5):
    with st.expander(ROLES[i], expanded=(i==0)):
        c1,c2 = st.columns(2)
        md["oh"][i]["hc"] = c1.number_input(
            f"OH_HC_{i}",0.0,10000.0,float(md["oh"][i]["hc"]),key=f"ohhc_{selected_month}_{i}"
        )
        md["oh"][i]["salary"] = c2.number_input(
            f"OH_SAL_{i}",0.0,200000.0,float(md["oh"][i]["salary"]),key=f"ohsal_{selected_month}_{i}"
        )

# =========================
# CALCULATION ENGINE
# =========================

def compute_month(m):

    md = st.session_state["data"][m]

    fx = md["fx"]
    wh = md["wh"]
    sh = md["sh"]

    hours = wh*(1-sh)*(1-absenteeism)

    if billing_model=="50% Billing":
        hours *= 0.5

    revenue = 0
    cost = 0

    for row in md["prod"]:
        hc=row["hc"]
        salary=row["salary"]
        up=row["up"]

        bonus=salary*bonus_pct*bonus_multiplier
        gross=salary+bonus
        loaded=gross*salary_multiplier
        cost_per=loaded+meal_card

        rev=hc*hours*up*fx

        if overtime_hours>0:
            rev += hc*overtime_hours*up*fx
            cost_per *= 1.5

        revenue+=rev
        cost+=hc*cost_per

    for row in md["oh"]:
        salary=row["salary"]
        hc=row["hc"]
        bonus=salary*bonus_pct*bonus_multiplier
        gross=salary+bonus
        loaded=gross*salary_multiplier
        cost+=hc*(loaded+meal_card)

    margin=revenue-cost
    gm=margin/revenue if revenue>0 else 0

    return revenue,cost,margin,gm

total_revenue,total_cost,margin,gm = compute_month(selected_month)

# =========================
# SUMMARY
# =========================

st.divider()
st.subheader("Final Summary")

s1,s2,s3,s4 = st.columns(4)
s1.metric("Revenue",f"{total_revenue:,.0f}")
s2.metric("Total Cost",f"{total_cost:,.0f}")
s3.metric("Margin",f"{margin:,.0f}")
s4.metric("GM %",f"{gm*100:.1f}%")

# =========================
# CHARTS
# =========================

st.divider()
st.subheader("Charts")

summary_df = pd.DataFrame(
    {"Value":[total_revenue,total_cost,margin]},
    index=["Revenue","Cost","Margin"]
)

st.bar_chart(summary_df)

gm_df = pd.DataFrame({"GM%":[gm*100]},index=["GM"])
st.bar_chart(gm_df)

trend = []

for m in MONTHS:
    r,c,mar,g = compute_month(m)
    trend.append({"Month":m,"Revenue":r,"Cost":c,"Margin":mar,"GM%":g*100})

trend_df = pd.DataFrame(trend).set_index("Month")

st.line_chart(trend_df[["Revenue","Cost","Margin"]])
st.line_chart(trend_df[["GM%"]])

# =========================
# MOM
# =========================

st.divider()
st.subheader("Month-over-Month")

compare_month = st.selectbox("Compare With",MONTHS)

cur_rev,cur_cost,cur_margin,cur_gm = compute_month(selected_month)
prev_rev,prev_cost,prev_margin,prev_gm = compute_month(compare_month)

d1,d2,d3,d4 = st.columns(4)
d1.metric("Revenue Δ",f"{cur_rev-prev_rev:,.0f}")
d2.metric("Cost Δ",f"{cur_cost-prev_cost:,.0f}")
d3.metric("Margin Δ",f"{cur_margin-prev_margin:,.0f}")
d4.metric("GM Δ (pp)",f"{(cur_gm-prev_gm)*100:.2f}")
