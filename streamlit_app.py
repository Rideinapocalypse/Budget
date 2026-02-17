import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# =====================================================
# CONSTANTS
# =====================================================

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

LANGS = ["DE","EN","TR","FR","IT","NL"]
ROLES = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# =====================================================
# SIDEBAR – GLOBAL INPUTS
# =====================================================

st.sidebar.header("Global Inputs")

worked_hours_default = st.sidebar.number_input("Worked Hours (Default)", value=180.0)
shrinkage_default = st.sidebar.number_input("Shrinkage (Default)", value=0.15)

salary_multiplier = st.sidebar.number_input("Salary Multiplier", value=1.7)
bonus_pct = st.sidebar.number_input("Bonus %", value=0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier", value=1.0)
meal_card = st.sidebar.number_input("Meal Card (TRY)", value=5850.0)

currency = st.sidebar.selectbox("Unit Price Currency",["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default", value=38.0)

# =====================================================
# ADVANCED DRIVERS
# =====================================================

st.sidebar.divider()
st.sidebar.subheader("Advanced Drivers")

absenteeism = st.sidebar.number_input("Absenteeism %", value=0.10)
attrition = st.sidebar.number_input("Attrition %", value=0.07)
overtime_hours = st.sidebar.number_input("Overtime Hours (per HC)", value=0.0)

billing_model = st.sidebar.selectbox(
    "Invoicing Model",
    ["Full Productive Hours","50% Billing","Fixed HC"]
)

# =====================================================
# SESSION STORAGE
# =====================================================

if "data" not in st.session_state:
    st.session_state["data"] = {
        m:{
            "fx":None,
            "wh":None,
            "sh":None,
            "prod":[{"hc":0.0,"salary":0.0,"up":0.0} for _ in range(6)],
            "oh":[{"hc":0.0,"salary":0.0} for _ in range(5)]
        } for m in MONTHS
    }

selected_month = st.sidebar.selectbox("Select Month", MONTHS)
md = st.session_state["data"][selected_month]

# =====================================================
# MONTH OVERRIDES
# =====================================================

col1,col2,col3 = st.columns(3)

md["fx"] = col1.number_input("FX (Month)",
    value=md["fx"] if md["fx"] else fx_default,
    key=f"fx_{selected_month}")

md["wh"] = col2.number_input("Worked Hours (Month)",
    value=md["wh"] if md["wh"] else worked_hours_default,
    key=f"wh_{selected_month}")

md["sh"] = col3.number_input("Shrinkage (Month)",
    value=md["sh"] if md["sh"] else shrinkage_default,
    key=f"sh_{selected_month}")

# =====================================================
# EXCEL TEMPLATE + IMPORT
# =====================================================

st.divider()
st.subheader("📁 Excel Template & Import")

def build_template():
    inputs_df = pd.DataFrame({
        "Month": MONTHS,
        "FX": [fx_default]*12,
        "WorkedHours": [worked_hours_default]*12,
        "Shrinkage": [shrinkage_default]*12
    })

    prod_rows = []
    for m in MONTHS:
        for lang in LANGS:
            prod_rows.append({
                "Month": m,
                "Language": lang,
                "HC": 0,
                "Salary": 0,
                "UnitPrice": 0
            })
    prod_df = pd.DataFrame(prod_rows)

    oh_rows = []
    for m in MONTHS:
        for role in ROLES:
            oh_rows.append({
                "Month": m,
                "Role": role,
                "HC": 0,
                "Salary": 0
            })
    oh_df = pd.DataFrame(oh_rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        prod_df.to_excel(writer, sheet_name="Production", index=False)
        oh_df.to_excel(writer, sheet_name="Overhead", index=False)

    return output.getvalue()

st.download_button(
    "⬇ Download Excel Template",
    data=build_template(),
    file_name="budget_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded = st.file_uploader("Upload Filled Template (.xlsx)", type=["xlsx"])

if uploaded and st.button("Apply Import"):
    xls = pd.ExcelFile(uploaded)

    inputs_df = pd.read_excel(xls,"Inputs")
    prod_df = pd.read_excel(xls,"Production")
    oh_df = pd.read_excel(xls,"Overhead")

    for _,row in inputs_df.iterrows():
        if row["Month"] in MONTHS:
            st.session_state["data"][row["Month"]]["fx"] = row["FX"]
            st.session_state["data"][row["Month"]]["wh"] = row["WorkedHours"]
            st.session_state["data"][row["Month"]]["sh"] = row["Shrinkage"]

    for _,row in prod_df.iterrows():
        if row["Month"] in MONTHS and row["Language"] in LANGS:
            idx = LANGS.index(row["Language"])
            st.session_state["data"][row["Month"]]["prod"][idx] = {
                "hc":row["HC"],
                "salary":row["Salary"],
                "up":row["UnitPrice"]
            }

    for _,row in oh_df.iterrows():
        if row["Month"] in MONTHS and row["Role"] in ROLES:
            idx = ROLES.index(row["Role"])
            st.session_state["data"][row["Month"]]["oh"][idx] = {
                "hc":row["HC"],
                "salary":row["Salary"]
            }

    st.success("Import Applied")
    st.rerun()

# =====================================================
# PRODUCTION
# =====================================================

st.subheader("Production")

for i in range(6):
    with st.expander(LANGS[i], expanded=(i==0)):
        c1,c2,c3 = st.columns(3)
        md["prod"][i]["hc"] = c1.number_input("HC", md["prod"][i]["hc"], key=f"hc_{selected_month}_{i}")
        md["prod"][i]["salary"] = c2.number_input("Salary", md["prod"][i]["salary"], key=f"sal_{selected_month}_{i}")
        md["prod"][i]["up"] = c3.number_input("Unit Price", md["prod"][i]["up"], key=f"up_{selected_month}_{i}")

# =====================================================
# OVERHEAD
# =====================================================

st.subheader("Overhead")

for i in range(5):
    with st.expander(ROLES[i], expanded=(i==0)):
        c1,c2 = st.columns(2)
        md["oh"][i]["hc"] = c1.number_input("OH HC", md["oh"][i]["hc"], key=f"ohhc_{selected_month}_{i}")
        md["oh"][i]["salary"] = c2.number_input("Salary", md["oh"][i]["salary"], key=f"ohsal_{selected_month}_{i}")

# =====================================================
# CALCULATIONS
# =====================================================

fx = md["fx"] or fx_default
wh = md["wh"] or worked_hours_default
sh = md["sh"] or shrinkage_default

effective_hours = wh*(1-sh)*(1-absenteeism)

if billing_model=="50% Billing":
    effective_hours *= 0.5

total_revenue = 0
total_cost = 0

for row in md["prod"]:
    hc=row["hc"]
    salary=row["salary"]
    up=row["up"]

    bonus=salary*bonus_pct*bonus_multiplier
    gross=salary+bonus
    loaded=gross*salary_multiplier
    cost_per=loaded+meal_card

    revenue=hc*effective_hours*up*fx
    revenue+=hc*overtime_hours*up*fx

    total_revenue+=revenue
    total_cost+=hc*cost_per

for row in md["oh"]:
    hc=row["hc"]
    salary=row["salary"]
    bonus=salary*bonus_pct*bonus_multiplier
    gross=salary+bonus
    loaded=gross*salary_multiplier
    total_cost+=hc*(loaded+meal_card)

margin = total_revenue-total_cost
gm = margin/total_revenue if total_revenue>0 else 0

# =====================================================
# SUMMARY
# =====================================================

st.divider()
st.subheader("Final Summary")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Revenue",f"{total_revenue:,.0f}")
c2.metric("Total Cost",f"{total_cost:,.0f}")
c3.metric("Margin",f"{margin:,.0f}")
c4.metric("GM %",f"{gm*100:.1f}%")

# =====================================================
# GRAPHS
# =====================================================

st.divider()
st.subheader("Summary Graphics")

chart_df = pd.DataFrame({
    "Value":[total_revenue,total_cost,margin]
},index=["Revenue","Cost","Margin"])

st.bar_chart(chart_df)

# =====================================================
# MOM ANALYSIS
# =====================================================

st.divider()
st.subheader("Month-over-Month")

compare_month = st.selectbox("Compare With", MONTHS)

def compute_month(m):
    md=st.session_state["data"][m]
    fx=md["fx"] or fx_default
    wh=md["wh"] or worked_hours_default
    sh=md["sh"] or shrinkage_default
    hours=wh*(1-sh)*(1-absenteeism)

    rev=0
    cost=0

    for row in md["prod"]:
        rev+=row["hc"]*hours*row["up"]*fx
        bonus=row["salary"]*bonus_pct*bonus_multiplier
        gross=row["salary"]+bonus
        loaded=gross*salary_multiplier
        cost+=row["hc"]*(loaded+meal_card)

    for row in md["oh"]:
        bonus=row["salary"]*bonus_pct*bonus_multiplier
        gross=row["salary"]+bonus
        loaded=gross*salary_multiplier
        cost+=row["hc"]*(loaded+meal_card)

    margin=rev-cost
    gm=margin/rev if rev>0 else 0
    return rev,cost,margin,gm

cur_rev,cur_cost,cur_margin,cur_gm=compute_month(selected_month)
prev_rev,prev_cost,prev_margin,prev_gm=compute_month(compare_month)

d1,d2,d3,d4 = st.columns(4)
d1.metric("Revenue Δ",f"{cur_rev-prev_rev:,.0f}")
d2.metric("Cost Δ",f"{cur_cost-prev_cost:,.0f}")
d3.metric("Margin Δ",f"{cur_margin-prev_margin:,.0f}")
d4.metric("GM Δ (pp)",f"{(cur_gm-prev_gm)*100:.2f}")

# =====================================================
# EXPORT
# =====================================================

st.divider()
st.subheader("Export Current Month")

def export_excel():
    df = pd.DataFrame([{
        "Month":selected_month,
        "Revenue":total_revenue,
        "Cost":total_cost,
        "Margin":margin,
        "GM%":gm
    }])
    output=BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer,index=False)
    return output.getvalue()

st.download_button(
    "⬇ Download Summary Excel",
    data=export_excel(),
    file_name=f"budget_summary_{selected_month}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
