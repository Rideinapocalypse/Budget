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
MAX_SOLUTIONS = 5

# =====================================================
# GLOBAL SIDEBAR INPUTS
# =====================================================
st.sidebar.header("Global Drivers")

worked_hours_default = st.sidebar.number_input("Worked Hours (default)", 0.0, 300.0, 180.0)
shrinkage_default = st.sidebar.slider("Shrinkage % (default)", 0.0, 0.5, 0.15)

salary_multiplier = st.sidebar.number_input("Salary Multiplier", 0.0, 5.0, 1.7)
bonus_pct = st.sidebar.number_input("Bonus %", 0.0, 2.0, 0.10)
bonus_multiplier = st.sidebar.number_input("Bonus Multiplier", 0.0, 5.0, 1.0)
meal_card = st.sidebar.number_input("Meal Card (TRY)", 0.0, 20000.0, 5850.0)

currency = st.sidebar.selectbox("Unit Price Currency", ["EUR","USD"])
fx_default = st.sidebar.number_input("FX Default", 0.0, 200.0, 38.0)

# =====================================================
# INIT STORAGE
# =====================================================
if "data" not in st.session_state:
    st.session_state.data = {}
    for m in MONTHS:
        st.session_state.data[m] = {
            "inputs": {"fx": fx_default, "wh": worked_hours_default, "sh": shrinkage_default},
            "prod": {lang: [] for lang in LANGS},
            "oh": [{"role": r, "hc":0.0,"salary":0.0} for r in ROLES]
        }

selected_month = st.sidebar.selectbox("Select Month", MONTHS)
md = st.session_state.data[selected_month]

# =====================================================
# SOLUTIONS PER LANGUAGE
# =====================================================
st.sidebar.divider()
st.sidebar.subheader("Solutions per Language")

solution_counts = {}
for lang in LANGS:
    solution_counts[lang] = st.sidebar.number_input(
        f"{lang} solutions",
        min_value=0,
        max_value=MAX_SOLUTIONS,
        value=len(md["prod"][lang])
    )

# ensure structure matches solution count
for lang in LANGS:
    current = len(md["prod"][lang])
    target = solution_counts[lang]

    if target > current:
        for i in range(target-current):
            md["prod"][lang].append(
                {"hc":0.0,"salary":0.0,"up":0.0}
            )
    elif target < current:
        md["prod"][lang] = md["prod"][lang][:target]

# =====================================================
# MONTH OVERRIDES
# =====================================================
st.subheader("Month Overrides")

c1,c2,c3 = st.columns(3)
md["inputs"]["fx"] = c1.number_input("FX", 0.0, 200.0, md["inputs"]["fx"])
md["inputs"]["wh"] = c2.number_input("Worked Hours", 0.0, 300.0, md["inputs"]["wh"])
md["inputs"]["sh"] = c3.slider("Shrinkage", 0.0, 0.5, md["inputs"]["sh"])

# =====================================================
# PRODUCTION UI
# =====================================================
st.divider()
st.subheader("Production")

for lang in LANGS:
    if solution_counts[lang] == 0:
        continue

    with st.expander(lang, expanded=False):
        for i in range(solution_counts[lang]):
            st.markdown(f"**{lang} – Solution {i+1}**")
            col1,col2,col3 = st.columns(3)

            md["prod"][lang][i]["hc"] = col1.number_input(
                "HC", 0.0, 1000.0,
                md["prod"][lang][i]["hc"],
                key=f"{selected_month}_{lang}_hc_{i}"
            )

            md["prod"][lang][i]["salary"] = col2.number_input(
                "Base Salary (TRY)", 0.0, 200000.0,
                md["prod"][lang][i]["salary"],
                key=f"{selected_month}_{lang}_sal_{i}"
            )

            md["prod"][lang][i]["up"] = col3.number_input(
                f"Unit Price ({currency})", 0.0, 1000.0,
                md["prod"][lang][i]["up"],
                key=f"{selected_month}_{lang}_up_{i}"
            )

# =====================================================
# OVERHEAD
# =====================================================
st.divider()
st.subheader("Overhead")

for i,row in enumerate(md["oh"]):
    with st.expander(row["role"], expanded=False):
        col1,col2 = st.columns(2)
        row["hc"] = col1.number_input("HC", 0.0, 200.0, row["hc"], key=f"{selected_month}_oh_hc_{i}")
        row["salary"] = col2.number_input("Base Salary", 0.0, 200000.0, row["salary"], key=f"{selected_month}_oh_sal_{i}")

# =====================================================
# CALCULATION
# =====================================================
fx = md["inputs"]["fx"]
wh = md["inputs"]["wh"]
sh = md["inputs"]["sh"]

productive_hours = wh * (1 - sh)

def loaded_cost(base):
    bonus = base * bonus_pct * bonus_multiplier
    gross = base + bonus
    loaded = gross * salary_multiplier
    return loaded + meal_card

total_revenue = 0
total_prod_cost = 0

for lang in LANGS:
    for sol in md["prod"][lang]:
        hc = sol["hc"]
        salary = sol["salary"]
        up = sol["up"]

        revenue = hc * productive_hours * up * fx
        cost = hc * loaded_cost(salary)

        total_revenue += revenue
        total_prod_cost += cost

total_oh = 0
for row in md["oh"]:
    total_oh += row["hc"] * loaded_cost(row["salary"])

grand_cost = total_prod_cost + total_oh
margin = total_revenue - grand_cost
gm = margin / total_revenue if total_revenue > 0 else 0

# =====================================================
# SUMMARY
# =====================================================
st.divider()
st.subheader("Final Summary")

s1,s2,s3,s4 = st.columns(4)
s1.metric("Revenue (TRY)", f"{total_revenue:,.0f}")
s2.metric("Production Cost", f"{total_prod_cost:,.0f}")
s3.metric("Overhead Cost", f"{total_oh:,.0f}")
s4.metric("GM %", f"{gm*100:.1f}%")

t1,t2 = st.columns(2)
t1.metric("Grand Cost", f"{grand_cost:,.0f}")
t2.metric("Margin", f"{margin:,.0f}")

# =====================================================
# MONTH OVER MONTH
# =====================================================
st.divider()
st.subheader("Month-over-Month")

compare_month = st.selectbox("Compare With", MONTHS)

def compute_month(m):
    md2 = st.session_state.data[m]
    fx2 = md2["inputs"]["fx"]
    wh2 = md2["inputs"]["wh"]
    sh2 = md2["inputs"]["sh"]
    ph = wh2*(1-sh2)

    rev=0
    cost=0

    for lang in LANGS:
        for sol in md2["prod"][lang]:
            rev += sol["hc"]*ph*sol["up"]*fx2
            cost += sol["hc"]*loaded_cost(sol["salary"])

    for row in md2["oh"]:
        cost += row["hc"]*loaded_cost(row["salary"])

    margin = rev-cost
    gm = margin/rev if rev>0 else 0
    return rev,cost,margin,gm

cur = compute_month(selected_month)
prev = compute_month(compare_month)

c1,c2,c3,c4 = st.columns(4)
c1.metric("Revenue Δ", f"{cur[0]-prev[0]:,.0f}")
c2.metric("Cost Δ", f"{cur[1]-prev[1]:,.0f}")
c3.metric("Margin Δ", f"{cur[2]-prev[2]:,.0f}")
c4.metric("GM Δ (pp)", f"{(cur[3]-prev[3])*100:.2f}")
