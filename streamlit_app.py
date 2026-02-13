# =====================================================
# Excel Template Download + Import
# =====================================================

st.divider()
st.subheader("Excel Template & Import")

def build_template():
    inputs_rows = []
    for m in MONTHS:
        inputs_rows.append({
            "Month": m,
            "FX": fx_default,
            "WorkedHours": worked_hours_default,
            "Shrinkage": shrinkage_default
        })
    inputs_df = pd.DataFrame(inputs_rows)

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

def apply_import(file):
    xls = pd.ExcelFile(file)

    inputs_df = pd.read_excel(xls, "Inputs")
    prod_df = pd.read_excel(xls, "Production")
    oh_df = pd.read_excel(xls, "Overhead")

    # Inputs
    for _, row in inputs_df.iterrows():
        m = row["Month"]
        if m in MONTHS:
            st.session_state["data"][m]["fx"] = row["FX"]
            st.session_state["data"][m]["wh"] = row["WorkedHours"]
            st.session_state["data"][m]["sh"] = row["Shrinkage"]

    # Production
    for _, row in prod_df.iterrows():
        m = row["Month"]
        if m in MONTHS:
            lang_index = LANGS.index(row["Language"])
            st.session_state["data"][m]["prod"][lang_index]["hc"] = row["HC"]
            st.session_state["data"][m]["prod"][lang_index]["salary"] = row["Salary"]
            st.session_state["data"][m]["prod"][lang_index]["up"] = row["UnitPrice"]

    # Overhead
    for _, row in oh_df.iterrows():
        m = row["Month"]
        if m in MONTHS:
            role_index = ROLES.index(row["Role"])
            st.session_state["data"][m]["oh"][role_index]["hc"] = row["HC"]
            st.session_state["data"][m]["oh"][role_index]["salary"] = row["Salary"]

if uploaded:
    if st.button("Apply Import"):
        apply_import(uploaded)
        st.success("Import applied successfully.")
        st.rerun()
