import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App – Workforce + Multi-Solution Model")

# =========================================
# CONSTANTS
# =========================================

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

LANGS = ["DE","EN","TR","FR","IT","NL"]
ROLES = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# =========================================
# SIDEBAR – GLOBAL DRIVERS
# =========================================

st.sidebar.header("Global Drivers")

worked_hours_default = st.sidebar.number_input("Worked Hours", value=180.0)
shrinkage_default = st.sidebar.number_input("Shrinkage", value=0.15)
absenteeism = st.sidebar.number_input("Absenteeism", value=0.10)

salary_multiplier = st.sidebar.number_input("Salary Multiplier", value=1.7)
bonus_pct = st.sidebar.number_input("Bonus %", value=0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier", value=1.0)
meal_card = st.sidebar.number_input("Meal Card (TRY)", value=5850.0)

currency = st.sidebar.selectbox("Currency",["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default", value=38.0)

training_productivity = st.sidebar.number_input(
    "Training Productivity %",
    value=0.50
)

# =========================================
# SESSION STORAGE
# =========================================

if "data" not in st.session_state:
    st.session_state["data"] = {
        m:{
            "fx":fx_default,
            "wh":worked_hours_default,
            "sh":shrinkage_default,
            "prod":[{
                "opening":0.0,
                "hires":0.0,
                "attrition":0.07,
                "training_hc":0.0,
                "salary":0.0,
                "up_a":0.0,
                "up_b":0.0,
                "alloc_b":0.0
            } for _ in LANGS],
            "oh":[{"hc":0.0,"salary":0.0} for _ in ROLES]
        } for m in MONTHS
    }

selected_month = st.sidebar.selectbox("Select Month", MONTHS)
md = st.session_state["data"][selected_month]

# =========================================
# EXCEL TEMPLATE
# =========================================

st.divider()
st.subheader("Excel Template & Import")

def build_template():
    inputs_df = pd.DataFrame({
        "Month": MONTHS,
        "FX":[fx_default]*12,
        "WorkedHours":[worked_hours_default]*12,
        "Shrinkage":[shrinkage_default]*12
    })

    prod_rows=[]
    for m in MONTHS:
        for lang in LANGS:
            prod_rows.append({
                "Month":m,
                "Language":lang,
                "OpeningHC":0,
                "Hires":0,
                "Attrition%":0.07,
                "TrainingHC":0,
                "Salary":0,
                "UP_A":0,
                "UP_B":0,
                "Allocation_B%":0
            })
    prod_df=pd.DataFrame(prod_rows)

    oh_rows=[]
    for m in MONTHS:
        for role in ROLES:
            oh_rows.append({
                "Month":m,
                "Role":role,
                "HC":0,
                "Salary":0
            })
    oh_df=pd.DataFrame(oh_rows)

    output=BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        inputs_df.to_excel(writer,"Inputs",index=False)
        prod_df.to_excel(writer,"Production",index=False)
        oh_df.to_excel(writer,"Overhead",index=False)

    return output.getvalue()

st.download_button(
    "⬇ Download Excel Template",
    build_template(),
    file_name="budget_template.xlsx"
)

uploaded = st.file_uploader("Upload Filled Template", type=["xlsx"])

if uploaded and st.button("Apply Import"):
    xls = pd.ExcelFile(uploaded)
    inputs_df = pd.read_excel(xls,"Inputs")
    prod_df = pd.read_excel(xls,"Production")
    oh_df = pd.read_excel(xls,"Overhead")

    for _,row in inputs_df.iterrows():
        if row["Month"] in MONTHS:
            st.session_state["data"][row["Month"]]["fx"]=row["FX"]
            st.session_state["data"][row["Month"]]["wh"]=row["WorkedHours"]
            st.session_state["data"][row["Month"]]["sh"]=row["Shrinkage"]

    for _,row in prod_df.iterrows():
        if row["Month"] in MONTHS and row["Language"] in LANGS:
            idx=LANGS.index(row["Language"])
            st.session_state["data"][row["Month"]]["prod"][idx]={
                "opening":row["OpeningHC"],
                "hires":row["Hires"],
                "attrition":row["Attrition%"],
                "training_hc":row["TrainingHC"],
                "salary":row["Salary"],
                "up_a":row["UP_A"],
                "up_b":row["UP_B"],
                "alloc_b":row["Allocation_B%"]/100
            }

    for _,row in oh_df.iterrows():
        if row["Month"] in MONTHS and row["Role"] in ROLES:
            idx=ROLES.index(row["Role"])
            st.session_state["data"][row["Month"]]["oh"][idx]={
                "hc":row["HC"],
                "salary":row["Salary"]
            }

    st.success("Import Successful")
    st.rerun()

# =========================================
# PRODUCTION UI
# =========================================

st.divider()
st.subheader("Production")

for i,lang in enumerate(LANGS):
    with st.expander(lang,expanded=(i==0)):
        row=md["prod"][i]
        c1,c2,c3,c4,c5,c6,c7,c8=st.columns(8)

        row["opening"]=c1.number_input("Opening HC",value=row["opening"],key=f"op_{selected_month}_{i}")
        row["hires"]=c2.number_input("Hires",value=row["hires"],key=f"hi_{selected_month}_{i}")
        row["attrition"]=c3.number_input("Attrition %",value=row["attrition"],key=f"at_{selected_month}_{i}")
        row["training_hc"]=c4.number_input("Training HC",value=row["training_hc"],key=f"tr_{selected_month}_{i}")
        row["salary"]=c5.number_input("Salary",value=row["salary"],key=f"sal_{selected_month}_{i}")
        row["up_a"]=c6.number_input("UP A",value=row["up_a"],key=f"upa_{selected_month}_{i}")
        row["up_b"]=c7.number_input("UP B",value=row["up_b"],key=f"upb_{selected_month}_{i}")
        row["alloc_b"]=c8.number_input("Allocation B %",value=row["alloc_b"],key=f"alloc_{selected_month}_{i}")

# =========================================
# OVERHEAD
# =========================================

st.subheader("Overhead")

for i,role in enumerate(ROLES):
    with st.expander(role,expanded=(i==0)):
        row=md["oh"][i]
        c1,c2=st.columns(2)
        row["hc"]=c1.number_input("HC",value=row["hc"],key=f"ohhc_{selected_month}_{i}")
        row["salary"]=c2.number_input("Salary",value=row["salary"],key=f"ohsal_{selected_month}_{i}")

# =========================================
# CALCULATIONS
# =========================================

fx=md["fx"]
wh=md["wh"]
sh=md["sh"]

effective_hours = wh*(1-sh)*(1-absenteeism)

total_revenue=0
total_cost=0

for row in md["prod"]:
    attr_volume=row["opening"]*row["attrition"]
    closing=row["opening"]+row["hires"]-attr_volume
    productive=max(closing-row["training_hc"],0)

    bonus=row["salary"]*bonus_pct*bonus_multiplier
    gross=row["salary"]+bonus
    loaded=gross*salary_multiplier
    cost_per=loaded+meal_card

    alloc_b=row["alloc_b"]/100
    alloc_a=1-alloc_b

    revenue_a=productive*effective_hours*row["up_a"]*alloc_a*fx
    revenue_b=productive*effective_hours*row["up_b"]*alloc_b*fx
    revenue_training=row["training_hc"]*effective_hours*training_productivity*row["up_a"]*fx

    total_revenue+=revenue_a+revenue_b+revenue_training
    total_cost+=closing*cost_per

for row in md["oh"]:
    bonus=row["salary"]*bonus_pct*bonus_multiplier
    gross=row["salary"]+bonus
    loaded=gross*salary_multiplier
    total_cost+=row["hc"]*(loaded+meal_card)

margin=total_revenue-total_cost
gm=margin/total_revenue if total_revenue>0 else 0

# =========================================
# SUMMARY
# =========================================

st.divider()
st.subheader("Final Summary")

c1,c2,c3,c4=st.columns(4)
c1.metric("Revenue",f"{total_revenue:,.0f}")
c2.metric("Cost",f"{total_cost:,.0f}")
c3.metric("Margin",f"{margin:,.0f}")
c4.metric("GM %",f"{gm*100:.1f}%")

# =========================================
# CHART
# =========================================

st.divider()
st.subheader("Chart")

chart_df=pd.DataFrame({
    "Metric":["Revenue","Cost","Margin"],
    "Value":[total_revenue,total_cost,margin]
})

st.bar_chart(chart_df.set_index("Metric"))
