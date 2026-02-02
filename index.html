import streamlit as st

# =========================
# Page config
# =========================
st.set_page_config(page_title="Budget App", layout="wide")
st.title("📊 Budget App")

# =========================
# GLOBAL INPUTS (SIDEBAR)
# =========================
st.sidebar.header("Global Inputs")

worked_hours = st.sidebar.number_input(
    "Worked Hours per Agent (Monthly)",
    value=180.0,
    step=1.0
)

shrinkage = st.sidebar.slider(
    "Shrinkage (%)",
    0.0, 0.5, 0.15
)

productive_hours = worked_hours * (1 - shrinkage)

st.sidebar.divider()
st.sidebar.subheader("Global Cost Drivers")

salary_multiplier = st.sidebar.number_input(
    "Salary Multiplier",
    value=1.7,
    step=0.05
)

bonus_pct = st.sidebar.number_input(
    "Bonus % (of Net Salary)",
    value=0.10,
    step=0.01
)

meal_card = st.sidebar.number_input(
    "Meal Card per Agent (Monthly TRY)",
    value=5850.0,
    step=100.0
)

st.sidebar.divider()
currency = st.sidebar.selectbox("Unit Price Currency", ["EUR", "USD"])

fx_rate = st.sidebar.number_input(
    f"{currency} / TRY FX Rate",
    value=38.0 if currency == "EUR" else 35.0,
    step=0.1
)

# =========================
# HELPER FUNCTIONS
# =========================
def calculate_agent_cost(net_salary):
    gross = net_salary * salary_multiplier
    bonus = net_salary * bonus_pct
    return gross + bonus + meal_card

# =========================
# CALCULATED VALUES
# =========================
st.subheader("Calculated Values")
st.metric("Productive Hours per Agent", f"{productive_hours:.2f}")

# =========================
# PRODUCTION BLOCKS
# =========================
st.divider()
st.subheader("Production Blocks")

total_salary_all = 0.0
total_revenue_all = 0.0

for i in range(1, 7):
    st.markdown(f"### Language Block {i}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        lang = st.text_input(f"Language {i}", key=f"lang_{i}")

    with col2:
        hc = st.number_input(
            f"HC {i}",
            min_value=0,
            step=1,
            key=f"hc_{i}"
        )

    with col3:
        salary = st.number_input(
            f"Salary {i} (TRY)",
            min_value=0.0,
            step=500.0,
            key=f"salary_{i}"
        )

    with col4:
        unit_price = st.number_input(
            f"Unit Price {i} ({currency})",
            min_value=0.0,
            step=1.0,
            key=f"price_{i}"
        )

    if lang and hc > 0:
        effective_salary = calculate_agent_cost(salary)
        cost = hc * effective_salary

        unit_price_try = unit_price * fx_rate
        revenue = hc * productive_hours * unit_price_try

        margin = revenue - cost

        total_salary_all += cost
        total_revenue_all += revenue

        st.write(
            f"**{lang}** | "
            f"Cost: {cost:,.0f} TRY | "
            f"Revenue: {revenue:,.0f} TRY | "
            f"Margin: {margin:,.0f} TRY"
        )

# =========================
# OVERHEAD SECTION
# =========================
st.divider()
st.subheader("Overhead")

total_overhead = 0.0

for i in range(1, 5):
    st.markdown(f"### Overhead Block {i}")
    oh1, oh2, oh3 = st.columns(3)

    with oh1:
        role = st.text_input(
            f"Role {i}",
            key=f"oh_role_{i}",
            placeholder="Team Manager / QA / Ops / Trainer"
        )

    with oh2:
        oh_hc = st.number_input(
            f"HC {i}",
            min_value=0,
            step=1,
            key=f"oh_hc_{i}"
        )

    with oh3:
        oh_salary = st.number_input(
            f"Salary {i} (TRY)",
            min_value=0.0,
            step=500.0,
            key=f"oh_salary_{i}"
        )

    if role and oh_hc > 0:
        oh_cost = oh_hc * calculate_agent_cost(oh_salary)
        total_overhead += oh_cost
        st.write(f"**{role}** | Cost: {oh_cost:,.0f} TRY")

# =========================
# FINAL SUMMARY
# =========================
st.divider()
st.subheader("Final Summary")

grand_cost = total_salary_all + total_overhead
grand_margin = total_revenue_all - grand_cost
gm_pct = (grand_margin / total_revenue_all) if total_revenue_all > 0 else 0

st.metric("Total Cost (TRY)", f"{grand_cost:,.0f}")
st.metric("Total Revenue (TRY)", f"{total_revenue_all:,.0f}")
st.metric("Total Margin (TRY)", f"{grand_margin:,.0f}")
st.metric("GM %", f"{gm_pct * 100:.1f}%")
