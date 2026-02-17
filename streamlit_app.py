import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Budget Workforce Engine", layout="wide")
st.title("📊 Budget Workforce Engine")

# =====================================================
# CONSTANTS
# =====================================================

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

LANGS = ["DE","EN","TR","FR","IT","NL"]
ROLES = ["Team Manager","QA","Ops","Trainer","RTA/WFM"]

# =====================================================
# SIDEBAR GLOBAL DRIVERS
# =====================================================

st.sidebar.header("Global Drivers")

worked_hours_default = st.sidebar.number_input("Worked Hours (Default)", value=180.0)
shrinkage_default = st.sidebar.number_input("Shrinkage % (Default)", value=0.15)

salary_multiplier = st.sidebar.number_input("Salary Multiplier", value=1.7)
bonus_pct = st.sidebar.number_input("Bonus %", value=0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier", value=1.0)
meal_card = st.sidebar.number_input("Meal Card (TRY)", value=5850.0)

training_productivity = st.sidebar.slider("Training Productivity %",
                                          min_value=0.0,
                                          max_value=1.0,
                                          value=0.50,
                                          step=0.05)

currency = st.sidebar.selectbox("Unit Price Currency",["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default", value=38.0)

# =====================================================
# SESSION STORAGE
# =====================================================

if "data" not in st.session_state:
    st.session_state["data"] = {
        m:{
            "fx":None,
            "wh":None,
            "sh":None,
            "prod":[
                {
                    "opening_hc":0.0,
                    "hires":0.0,
                    "attrition_pct":0.07,
                    "training_hc":0.0,
                    "salary":0.0,
                    "up":0.0,
                    "up_training":0.0
                } for _ in range(6)
            ],
            "oh":[{"hc":0.0,"salary":0.0} for _ in range(5)]
        } for m in MONTHS
    }

selected_month = st.sidebar.selectbox("Select Month", MONTHS)
md = st.session_state["data"][selected_month]

# =====================================================
# MONTH OVERRIDES
# =====================================================

c1,c2,c3 = st.columns(3)

md["fx"] = c1.number_input("FX (Month)",
                           value=md["fx"] or fx_default)

md["wh"] = c2.number_input("Worked Hours (Month)",
                           value=md["wh"] or worked_hours_default)

md["sh"] = c3.number_input("Shrinkage (Month)",
                           value=md["sh"] or shrinkage_default)

# =====================================================
# WORKFORCE CALC FUNCTION
# =====================================================

def calculate_cost_per_head(salary):
    bonus = salary * bonus_pct * bonus_multiplier
    gross = salary + bonus
    loaded = gross * salary_multiplier
    return loaded + meal_card

def compute_month(m):
    md = st.session_state["data"][m]

    fx = md["fx"] or fx_default
    wh = md["wh"] or worked_hours_default
    sh = md["sh"] or shrinkage_default

    effective_hours = wh * (1 - sh)

    total_revenue = 0
    total_cost = 0

    detailed = []

    for i, lang in enumerate(LANGS):
        row = md["prod"][i]

        opening = row["opening_hc"]
        hires = row["hires"]
        attr = row["attrition_pct"]
        training = row["training_hc"]

        attr_volume = opening * attr
        closing = opening + hires - attr_volume
        productive = max(closing - training, 0)

        salary = row["salary"]
        up = row["up"]
        up_tr = row["up_training"]

        cost_per = calculate_cost_per_head(salary)

        revenue_full = productive * effective_hours * up * fx
        revenue_training = training * effective_hours * training_productivity * up_tr * fx
        revenue = revenue_full + revenue_training

        cost = closing * cost_per

        total_revenue += revenue
        total_cost += cost

        detailed.append({
            "Language":lang,
            "Opening HC":opening,
            "Hires":hires,
            "Attrition %":attr,
            "Closing HC":closing,
            "Productive HC":productive,
            "Training HC":training,
            "Revenue":revenue,
            "Cost":cost,
            "Margin":revenue - cost
        })

    # overhead
    for row in md["oh"]:
        salary=row["salary"]
        hc=row["hc"]
        cost_per = calculate_cost_per_head(salary)
        total_cost += hc * cost_per

    margin = total_revenue - total_cost
    gm = margin / total_revenue if total_revenue>0 else 0

    return total_revenue,total_cost,margin,gm,pd.DataFrame(detailed)

# =====================================================
# PRODUCTION UI
# =====================================================

st.subheader("Workforce & Revenue Drivers")

for i,lang in enumerate(LANGS):
    with st.expander(lang, expanded=(i==0)):
        r = md["prod"][i]

        c1,c2,c3 = st.columns(3)
        r["opening_hc"] = c1.number_input("Opening HC", value=r["opening_hc"], key=f"op_{selected_month}_{i}")
        r["hires"] = c2.number_input("Hires", value=r["hires"], key=f"hire_{selected_month}_{i}")
        r["attrition_pct"] = c3.number_input("Attrition %", value=r["attrition_pct"], key=f"att_{selected_month}_{i}")

        c4,c5 = st.columns(2)
        r["training_hc"] = c4.number_input("Training HC", value=r["training_hc"], key=f"train_{selected_month}_{i}")
        r["salary"] = c5.number_input("Base Salary", value=r["salary"], key=f"sal_{selected_month}_{i}")

        c6,c7 = st.columns(2)
        r["up"] = c6.number_input("Unit Price", value=r["up"], key=f"up_{selected_month}_{i}")
        r["up_training"] = c7.number_input("Training Unit Price", value=r["up_training"], key=f"uptr_{selected_month}_{i}")

# =====================================================
# OVERHEAD
# =====================================================

st.subheader("Overhead")

for i,role in enumerate(ROLES):
    with st.expander(role, expanded=(i==0)):
        md["oh"][i]["hc"] = st.number_input("HC", value=md["oh"][i]["hc"], key=f"ohhc_{selected_month}_{i}")
        md["oh"][i]["salary"] = st.number_input("Salary", value=md["oh"][i]["salary"], key=f"ohsal_{selected_month}_{i}")

# =====================================================
# SUMMARY
# =====================================================

rev,cost,margin,gm,detail_df = compute_month(selected_month)

st.divider()
st.subheader("Final Summary")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Revenue", f"{rev:,.0f}")
c2.metric("Cost", f"{cost:,.0f}")
c3.metric("Margin", f"{margin:,.0f}")
c4.metric("GM %", f"{gm*100:.2f}")

st.bar_chart(pd.DataFrame(
    {"TRY":[rev,cost,margin]},
    index=["Revenue","Cost","Margin"]
))

with st.expander("Detailed Workforce Breakdown"):
    st.dataframe(detail_df, use_container_width=True)

# =====================================================
# MONTH OVER MONTH
# =====================================================

st.divider()
st.subheader("Month-over-Month Analysis")

compare_month = st.selectbox("Compare With", MONTHS)

rev2,cost2,margin2,gm2,_ = compute_month(compare_month)

d1,d2,d3,d4 = st.columns(4)
d1.metric("Revenue Δ", f"{rev-rev2:,.0f}")
d2.metric("Cost Δ", f"{cost-cost2:,.0f}")
d3.metric("Margin Δ", f"{margin-margin2:,.0f}")
d4.metric("GM Δ (pp)", f"{(gm-gm2)*100:.2f}")
