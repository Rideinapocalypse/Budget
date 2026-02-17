# =====================================================
# EXCEL TEMPLATE + IMPORT
# =====================================================

st.divider()
st.subheader("Excel Template & Import")

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
                "OpeningHC": 0,
                "Hires": 0,
                "AttritionPct": 0.07,
                "TrainingHC": 0,
                "BaseSalary": 0,
                "UnitPrice": 0,
                "TrainingUnitPrice": 0
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
    file_name="workforce_budget_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded = st.file_uploader("Upload Filled Template (.xlsx)", type=["xlsx"])

if uploaded:
    if st.button("Apply Import"):
        xls = pd.ExcelFile(uploaded)

        inputs_df = pd.read_excel(xls,"Inputs")
        prod_df = pd.read_excel(xls,"Production")
        oh_df = pd.read_excel(xls,"Overhead")

        # INPUTS
        for _,row in inputs_df.iterrows():
            m = row["Month"]
            if m in MONTHS:
                st.session_state["data"][m]["fx"] = row["FX"]
                st.session_state["data"][m]["wh"] = row["WorkedHours"]
                st.session_state["data"][m]["sh"] = row["Shrinkage"]

        # PRODUCTION
        for _,row in prod_df.iterrows():
            m = row["Month"]
            if m in MONTHS and row["Language"] in LANGS:
                idx = LANGS.index(row["Language"])
                st.session_state["data"][m]["prod"][idx]["opening_hc"] = row["OpeningHC"]
                st.session_state["data"][m]["prod"][idx]["hires"] = row["Hires"]
                st.session_state["data"][m]["prod"][idx]["attrition_pct"] = row["AttritionPct"]
                st.session_state["data"][m]["prod"][idx]["training_hc"] = row["TrainingHC"]
                st.session_state["data"][m]["prod"][idx]["salary"] = row["BaseSalary"]
                st.session_state["data"][m]["prod"][idx]["up"] = row["UnitPrice"]
                st.session_state["data"][m]["prod"][idx]["up_training"] = row["TrainingUnitPrice"]

        # OVERHEAD
        for _,row in oh_df.iterrows():
            m = row["Month"]
            if m in MONTHS and row["Role"] in ROLES:
                idx = ROLES.index(row["Role"])
                st.session_state["data"][m]["oh"][idx]["hc"] = row["HC"]
                st.session_state["data"][m]["oh"][idx]["salary"] = row["Salary"]

        st.success("Import Applied")
        st.rerun()

