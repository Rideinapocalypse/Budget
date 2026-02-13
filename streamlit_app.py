if uploaded:
    if st.button("Apply Import"):

        try:
            xls = pd.ExcelFile(uploaded)

            required = {"Inputs", "Production", "Overhead"}
            if not required.issubset(set(xls.sheet_names)):
                missing = required - set(xls.sheet_names)
                st.error(f"Missing sheet(s): {', '.join(missing)}")
                st.stop()

            inputs_df = pd.read_excel(xls, "Inputs")
            prod_df = pd.read_excel(xls, "Production")
            oh_df = pd.read_excel(xls, "Overhead")

            # -------------------------
            # INPUTS
            # -------------------------
            for _, row in inputs_df.iterrows():
                m = str(row.get("Month")).strip()
                if m in MONTHS:
                    st.session_state["data"][m]["fx"] = float(row.get("FX", fx_default))
                    st.session_state["data"][m]["wh"] = float(row.get("WorkedHours", worked_hours_default))

                    sh = float(row.get("Shrinkage", shrinkage_default))
                    if sh > 1:
                        sh = sh / 100
                    st.session_state["data"][m]["sh"] = sh

            # -------------------------
            # PRODUCTION
            # -------------------------
            for _, row in prod_df.iterrows():

                m = str(row.get("Month")).strip()
                lang = str(row.get("Language")).strip()

                if m in MONTHS and lang in LANGS:

                    idx = LANGS.index(lang)

                    st.session_state["data"][m]["prod"][idx]["hc"] = float(row.get("HC", 0))

                    # Safe column handling
                    salary = row.get("Salary")
                    if salary is None:
                        salary = row.get("BaseSalaryTRY", 0)

                    unitprice = row.get("UnitPrice")
                    if unitprice is None:
                        unitprice = row.get("UnitPriceCurrency", 0)

                    st.session_state["data"][m]["prod"][idx]["salary"] = float(salary)
                    st.session_state["data"][m]["prod"][idx]["up"] = float(unitprice)

            # -------------------------
            # OVERHEAD
            # -------------------------
            for _, row in oh_df.iterrows():

                m = str(row.get("Month")).strip()
                role = str(row.get("Role")).strip()

                if m in MONTHS and role in ROLES:

                    idx = ROLES.index(role)

                    st.session_state["data"][m]["oh"][idx]["hc"] = float(row.get("HC", 0))

                    salary = row.get("Salary")
                    if salary is None:
                        salary = row.get("BaseSalaryTRY", 0)

                    st.session_state["data"][m]["oh"][idx]["salary"] = float(salary)

            st.success("Import Applied Successfully")
            st.rerun()

        except Exception as e:
            st.error(f"Import Failed: {e}")
