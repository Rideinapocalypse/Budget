"""
CCBudget — Staffing Calculator
Monthly schedule per work type. Shares st.session_state with main budget app.
"""

import math
import streamlit as st
import pandas as pd

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Staffing Calculator — CCBudget",
    page_icon="🧮",
    layout="wide",
)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

def get_clients():
    return st.session_state.get("clients", [])

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card { background:#1e2535;border:1px solid #2a3347;border-radius:8px;padding:16px;text-align:center; }
.metric-val  { color:#e8edf5;font-size:22px;font-weight:700; }
.metric-lbl  { color:#8b96b0;font-size:11px;margin-top:4px; }
.metric-sub  { color:#8b96b0;font-size:11px;margin-top:2px; }
.warn-box    { background:#2d1f1f;border:1px solid #ef444455;border-radius:6px;padding:10px 14px;color:#ef4444;font-size:13px;margin-top:8px; }
.ok-box      { background:#1a2d1f;border:1px solid #10b98155;border-radius:6px;padding:10px 14px;color:#10b981;font-size:13px;margin-top:8px; }
.info-box    { background:#1e2535;border:1px solid #3b82f655;border-radius:6px;padding:10px 14px;color:#8b96b0;font-size:13px;margin-top:8px; }
.sched-hdr   { background:#1e2535;border-radius:6px;padding:8px 12px;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#5a6480;margin-bottom:6px; }
</style>
""", unsafe_allow_html=True)

def rostered_hc(productive_hc, shrinkage_pct):
    shrink = max(0.0, min(0.99, shrinkage_pct / 100))
    return productive_hc / (1 - shrink) if shrink < 1 else productive_hc

def occ_status(occ_pct):
    if occ_pct > 90:   return "warn", f"Occupancy {occ_pct:.1f}% — agents overloaded."
    elif occ_pct > 85: return "warn", f"Occupancy {occ_pct:.1f}% — at the edge."
    elif occ_pct < 60: return "info", f"Occupancy {occ_pct:.1f}% — significant idle time."
    else:              return "ok",   f"Occupancy {occ_pct:.1f}% — healthy (60-85%)."

def metric_card(label, value, sub=""):
    return (f"<div class='metric-card'><div class='metric-val'>{value}</div>"
            f"<div class='metric-lbl'>{label}</div>"
            f"{'<div class=metric-sub>' + sub + '</div>' if sub else ''}</div>")

def results_row(cols_data):
    cols = st.columns(len(cols_data))
    for col, (label, value, sub) in zip(cols, cols_data):
        col.markdown(metric_card(label, value, sub), unsafe_allow_html=True)

def _erlang_solve(A, aht, sl_target, sl_seconds, max_agents=100):
    if A <= 0: return 0, 0, 0
    def erlang_c(N, A):
        if N <= A: return 1.0
        try:
            log_AN = N * math.log(A) - sum(math.log(k) for k in range(1, N+1))
            sum_t  = sum(math.exp(k * math.log(A) - sum(math.log(j) for j in range(1, k+1))) for k in range(N))
            num = math.exp(log_AN); den = num + (1 - A/N) * sum_t
            return num / den if den else 1.0
        except: return 1.0
    def service_level(N, A, aht, t):
        if N <= A: return 0.0
        return 1 - erlang_c(N, A) * math.exp(-(N-A) * (t/aht))
    def asa(N, A, aht):
        if N <= A: return float('inf')
        return (erlang_c(N, A) * aht) / (N - A)
    min_N = math.ceil(A) + 1; req_N = min_N
    for n in range(min_N, max_agents + 1):
        if service_level(n, A, aht, sl_seconds) >= sl_target:
            req_N = n; break
    occ = (A / req_N * 100) if req_N > 0 else 0
    return req_N, asa(req_N, A, aht), occ

def full_year_summary(schedule):
    active = [r for r in schedule if r["volume"] > 0]
    if not active:
        st.info("Enter volume for at least one month to see the summary.")
        return
    total_vol = sum(r["volume"] for r in active)
    avg_ros   = sum(r["rostered_hc"] for r in active) / len(active)
    peak_row  = max(active, key=lambda r: r["rostered_hc"])
    min_row   = min(active, key=lambda r: r["rostered_hc"])
    st.markdown("#### Full-Year Summary")
    results_row([
        ("Total Annual Volume", f"{total_vol:,}", f"Across {len(active)} active months"),
        ("Avg Rostered HC",     f"{avg_ros:.1f}", "Monthly average"),
        ("Peak Month",          f"{peak_row['month']} — {peak_row['rostered_hc']}", "Highest HC"),
        ("Lowest Month",        f"{min_row['month']} — {min_row['rostered_hc']}",   "Lowest HC"),
        ("HC Swing",            f"{peak_row['rostered_hc'] - min_row['rostered_hc']}", "Peak minus lowest"),
    ])
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Rostered HC", x=[r["month"] for r in schedule],
            y=[r["rostered_hc"] for r in schedule], marker_color="#3b82f6",
            hovertemplate="%{x}: %{y} rostered<extra></extra>"))
        fig.add_trace(go.Scatter(name="Productive HC", x=[r["month"] for r in schedule],
            y=[r["productive_hc"] for r in schedule], mode="lines+markers",
            line=dict(color="#10b981", width=2, dash="dot"), marker=dict(size=5),
            hovertemplate="%{x}: %{y:.1f} productive<extra></extra>"))
        fig.update_layout(plot_bgcolor="#0e1420", paper_bgcolor="#0e1420",
            font=dict(color="#8b96b0"), legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=10,r=10,t=40,b=10), height=280,
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1e2535", title="HC"),
            hoverlabel=dict(bgcolor="#1e2535", font=dict(color="#e8edf5")))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError: pass
    with st.expander("Full monthly detail table", expanded=False):
        rows = []
        for r in schedule:
            row = {"Month": r["month"], "Volume": f"{r['volume']:,}" if r["volume"] else "—",
                   "Shrink %": f"{r['shrink_pct']}%" if r["volume"] else "—",
                   "Prod. HC": f"{r['productive_hc']:.1f}" if r["volume"] else "—",
                   "Rostered HC": r["rostered_hc"] if r["volume"] else "—"}
            if "prod_hr" in r and r["volume"]: row["Prod/hr"] = r["prod_hr"]
            if "asa" in r and r["volume"]:     row["ASA (s)"] = f"{r['asa']:.0f}"
            rows.append(row)
        st.dataframe(pd.DataFrame(rows).set_index("Month"), use_container_width=True)

def push_all_months_ui(schedule, key_prefix):
    st.divider()
    st.markdown("### Push Schedule to Budget Block")
    st.caption("Writes the rostered HC for each month into the selected block.")
    clients = get_clients()
    if not clients:
        st.info("No clients found. Set up a client on the main Budget page first, then navigate here in the same session.")
        return
    pb1, pb2, pb3 = st.columns([2, 2, 1])
    client_idx = pb1.selectbox("Client", range(len(clients)),
        format_func=lambda i: clients[i]["name"], key=f"{key_prefix}_push_client")
    cl = clients[client_idx]
    all_blocks_flat = []
    seen = set()
    for m in MONTHS:
        for bi, b in enumerate(cl["blocks"].get(m, [])):
            lbl = b.get("lang") or f"Block #{bi+1}"
            if lbl not in seen:
                seen.add(lbl); all_blocks_flat.append((lbl, bi))
    if not all_blocks_flat:
        pb2.warning("No blocks found. Add production blocks on the main page first.")
        return
    block_choice = pb2.selectbox("Block", all_blocks_flat,
        format_func=lambda x: x[0], key=f"{key_prefix}_push_block")
    active_months = [(r["month"], r["rostered_hc"]) for r in schedule if r["volume"] > 0]
    skipped = [r["month"] for r in schedule if r["volume"] == 0]
    preview = "  |  ".join([f"{m}: <b>{hc}</b>" for m, hc in active_months])
    st.markdown(
        f"<div class='info-box'><b>Block:</b> {block_choice[0]}<br>"
        f"<b>Months to push:</b> {preview if preview else 'None'}<br>"
        f"{'<b>Skipped (vol=0):</b> ' + ', '.join(skipped) if skipped else ''}</div>",
        unsafe_allow_html=True)
    if pb3.button("Push All", key=f"{key_prefix}_push_btn", use_container_width=True, type="primary"):
        if not active_months:
            st.warning("No months with volume > 0.")
            return
        pushed = 0
        for row in schedule:
            if row["volume"] == 0: continue
            blks = cl["blocks"].get(row["month"], [])
            for b in blks:
                lbl = b.get("lang") or f"Block #{blks.index(b)+1}"
                if lbl == block_choice[0]:
                    b["hc"] = row["rostered_hc"]; pushed += 1
        if pushed:
            st.success(f"HC schedule pushed to '{block_choice[0]}' across {pushed} month(s). Go to Budget page to confirm.")
        else:
            st.warning("No matching blocks updated. Make sure blocks exist for these months.")

# ═══════════════════════════════════════════════════════════════
# HEADER & GLOBALS
# ═══════════════════════════════════════════════════════════════
st.markdown("## Staffing Calculator")
st.caption("Enter a 12-month forecast schedule. Results calculate instantly. Push to budget when ready.")

global_hours  = st.session_state.get("g_hours",  180)
global_shrink = int(st.session_state.get("g_shrink", 0.15) * 100)

st.divider()
work_type = st.radio("Work type",
    ["Claims / Back-office", "Inbound Voice (Erlang-C)", "Email / Async", "Blended"],
    horizontal=True, key="sc_work_type")
st.divider()

# ═══════════════════════════════════════════════════════════════
# 1. CLAIMS
# ═══════════════════════════════════════════════════════════════
if work_type == "Claims / Back-office":
    st.markdown("### Claims / Back-office — Monthly Schedule")
    st.caption(f"Model: Rostered HC = (Volume / (prod/hr x {global_hours}h)) / (1 - shrinkage). "
               f"AHT (mins) auto-calculates prod/hr — override per month if needed.")
    rc1, rc2 = st.columns(2)
    ramp_eff = rc1.slider("New hire ramp efficiency %", 10, 100, 70, 5, format="%d%%", key="claims_ramp_eff")
    ramp_mo  = rc2.number_input("Ramp-up months", value=2, step=1, min_value=0, max_value=6, key="claims_ramp_mo")
    st.divider()
    st.markdown("<div class='sched-hdr'>Monthly Forecast Schedule</div>", unsafe_allow_html=True)
    st.caption("AHT drives prod/hr automatically (60 / AHT mins). Override prod/hr per month if you have a better estimate.")
    d1,d2,d3,d4 = st.columns(4)
    def_vol  = d1.number_input("Default volume",    value=5000, step=100, min_value=0,   key="claims_def_vol")
    def_aht  = d2.number_input("Default AHT (mins)",value=12,   step=1,   min_value=1,   key="claims_def_aht",
                                 help="Average Handle Time in minutes. Sets prod/hr = 60 / AHT automatically.")
    def_prod = d3.number_input("Default prod/hr override (0 = auto from AHT)", value=0, step=1, min_value=0,
                                key="claims_def_prod",
                                help="Leave at 0 to use AHT-derived rate. Enter a value to override.")
    def_shr  = d4.slider("Default shrinkage %", 0, 40, global_shrink, 1, format="%d%%", key="claims_def_shr")
    # Show derived default prod/hr
    auto_prod_default = round(60 / def_aht, 2) if def_aht > 0 else 5
    eff_prod_default  = def_prod if def_prod > 0 else auto_prod_default
    st.caption(f"ℹ️ Default prod/hr: **{eff_prod_default:.1f}** "
               f"({'manual override' if def_prod > 0 else f'auto from {def_aht} min AHT'})")
    if st.button("⬇ Apply defaults to all months", key="claims_apply_defaults", type="secondary"):
        for m in MONTHS:
            st.session_state[f"claims_{m}_vol"]  = int(def_vol)
            st.session_state[f"claims_{m}_aht"]  = int(def_aht)
            st.session_state[f"claims_{m}_prod"] = int(def_prod)
            st.session_state[f"claims_{m}_shr"]  = int(def_shr)
        st.rerun()
    st.divider()
    hcols = st.columns([1.0, 1.4, 1.2, 1.2, 1.0, 1.2, 1.0, 1.0])
    for col, lbl in zip(hcols, ["Month","Volume","AHT(min)","Prod/hr","Override","Shrink%","Prod.HC","Rostered"]):
        col.markdown(f"**{lbl}**")
    schedule = []
    for m in MONTHS:
        c_m,c_v,c_a,c_ap,c_ov,c_sh,c_ph,c_rh = st.columns([1.0,1.4,1.2,1.2,1.0,1.2,1.0,1.0])
        c_m.markdown(f"**{m}**")
        vol  = c_v.number_input("",  value=int(def_vol),  step=100, min_value=0,  key=f"claims_{m}_vol",  label_visibility="collapsed")
        aht  = c_a.number_input("",  value=int(def_aht),  step=1,   min_value=1,  key=f"claims_{m}_aht",  label_visibility="collapsed")
        auto_prod = round(60 / aht, 2) if aht > 0 else 5
        c_ap.markdown(f"<span style='color:#10b981;font-size:13px'>{auto_prod:.1f}</span>", unsafe_allow_html=True)
        override = c_ov.number_input("", value=int(def_prod), step=1, min_value=0, key=f"claims_{m}_prod", label_visibility="collapsed")
        shr  = c_sh.number_input("", value=int(def_shr),  step=1,   min_value=0, max_value=40, key=f"claims_{m}_shr",  label_visibility="collapsed")
        eff_prod    = override if override > 0 else auto_prod
        monthly_cap = eff_prod * global_hours
        prod_hc = vol / monthly_cap if monthly_cap > 0 and vol > 0 else 0
        ros = math.ceil(rostered_hc(prod_hc, shr)) if vol > 0 else 0
        c_ph.markdown(f"{'—' if vol==0 else f'{prod_hc:.1f}'}")
        c_rh.markdown(f"**{'—' if vol==0 else ros}**")
        schedule.append({"month":m,"volume":vol,"aht_mins":aht,"prod_hr":eff_prod,"shrink_pct":shr,"productive_hc":prod_hc,"rostered_hc":ros})
    st.divider()
    full_year_summary(schedule)
    active = [r for r in schedule if r["volume"] > 0]
    if active and ramp_mo > 0:
        ramp_rows = active[:int(ramp_mo)]
        ramp_hcs  = [math.ceil(r["rostered_hc"] / (ramp_eff / 100)) for r in ramp_rows]
        st.markdown(f"<div class='warn-box'>Ramp-up: First {ramp_mo} active month(s) need <b>{', '.join(str(h) for h in ramp_hcs)}</b> rostered agents at {ramp_eff}% efficiency.</div>", unsafe_allow_html=True)
    push_all_months_ui(schedule, "claims")

# ═══════════════════════════════════════════════════════════════
# 2. VOICE
# ═══════════════════════════════════════════════════════════════
elif work_type == "Inbound Voice (Erlang-C)":
    st.markdown("### Inbound Voice (Erlang-C) — Monthly Schedule")
    st.info("Erlang-C works best at 15-30 min intervals. Monthly inputs are a planning approximation — treat as a floor.", icon="i")
    vc1,vc2 = st.columns(2)
    v_shrink = vc1.slider("Default shrinkage %", 0, 40, global_shrink, 1, format="%d%%", key="voice_def_shrink")
    v_max    = vc2.number_input("Max agents (solver ceiling)", value=100, step=10, min_value=10, key="voice_def_max")
    st.divider()
    st.markdown("<div class='sched-hdr'>Monthly Forecast Schedule</div>", unsafe_allow_html=True)
    st.caption("Volume = peak calls per hour. Set defaults then override per month.")
    d1,d2,d3,d4 = st.columns(4)
    def_vol_v = d1.number_input("Default calls/hr", value=120, step=5, min_value=0, key="voice_def_vol")
    def_aht_v = d2.number_input("Default AHT (s)",  value=240, step=10, min_value=10, key="voice_def_aht")
    def_sl_v  = d3.number_input("Default SL %", value=80, step=1, min_value=1, max_value=99, key="voice_def_sl")
    def_sls_v = d4.number_input("Answer within (s)", value=20, step=5, min_value=1, key="voice_def_sls")
    if st.button("⬇ Apply defaults to all months", key="voice_apply_defaults", type="secondary"):
        for m in MONTHS:
            st.session_state[f"voice_{m}_vol"] = int(def_vol_v)
            st.session_state[f"voice_{m}_aht"] = int(def_aht_v)
            st.session_state[f"voice_{m}_sl"]  = int(def_sl_v)
            st.session_state[f"voice_{m}_shr"] = int(v_shrink)
        st.rerun()
    st.divider()
    hcols = st.columns([1.2,1.4,1.4,1.2,1.2,1.2,1.2,1.2])
    for col, lbl in zip(hcols, ["Month","Calls/hr","AHT(s)","SL%","Shrink%","Prod.HC","Rostered","ASA"]):
        col.markdown(f"**{lbl}**")
    v_schedule = []
    for m in MONTHS:
        c_m,c_v,c_a,c_sl,c_sh,c_ph,c_rh,c_asa = st.columns([1.2,1.4,1.4,1.2,1.2,1.2,1.2,1.2])
        c_m.markdown(f"**{m}**")
        vol = c_v.number_input("",  value=int(def_vol_v), step=5,  min_value=0, key=f"voice_{m}_vol", label_visibility="collapsed")
        aht = c_a.number_input("",  value=int(def_aht_v), step=10, min_value=10, key=f"voice_{m}_aht", label_visibility="collapsed")
        sl  = c_sl.number_input("", value=int(def_sl_v),  step=1,  min_value=1, max_value=99, key=f"voice_{m}_sl", label_visibility="collapsed")
        shr = c_sh.number_input("", value=int(v_shrink),  step=1,  min_value=0, max_value=40, key=f"voice_{m}_shr", label_visibility="collapsed")
        if vol > 0:
            A = (vol / 3600) * aht
            req_n, asa_v, occ_v = _erlang_solve(A, aht, sl/100, def_sls_v, v_max)
            ros = math.ceil(rostered_hc(req_n, shr))
            c_ph.markdown(f"{req_n}"); c_rh.markdown(f"**{ros}**"); c_asa.markdown(f"{asa_v:.0f}s")
        else:
            req_n=ros=occ_v=asa_v=0
            c_ph.markdown("—"); c_rh.markdown("—"); c_asa.markdown("—")
        v_schedule.append({"month":m,"volume":vol,"aht":aht,"sl_target":sl,"shrink_pct":shr,"productive_hc":req_n,"rostered_hc":ros,"asa":asa_v,"occ":occ_v})
    st.divider()
    full_year_summary(v_schedule)
    push_all_months_ui(v_schedule, "voice")

# ═══════════════════════════════════════════════════════════════
# 3. EMAIL
# ═══════════════════════════════════════════════════════════════
elif work_type == "Email / Async":
    st.markdown("### Email / Async — Monthly Schedule")
    st.caption("Model: Rostered HC = (Monthly volume / (emails/day x working days)) / (1 - shrinkage). "
               "AHT (mins) auto-derives emails/day — override per month if needed.")
    work_days = st.number_input("Working days / month", value=22, step=1, min_value=1, key="email_work_days")
    d1,d2,d3,d4 = st.columns(4)
    def_vol_e  = d1.number_input("Default monthly volume",   value=3000, step=100, min_value=0, key="email_def_vol")
    def_aht_e  = d2.number_input("Default AHT (mins)",       value=8,    step=1,   min_value=1, key="email_def_aht",
                                   help="Average time per email including reading and writing. Sets emails/day = work_hours_per_day x 60 / AHT.")
    def_epd_e  = d3.number_input("Default emails/day override (0 = auto)", value=0, step=1, min_value=0,
                                   key="email_def_epd", help="Leave 0 to use AHT-derived rate.")
    def_shrk_e = d4.slider("Default shrinkage %", 0, 40, global_shrink, 1, format="%d%%", key="email_def_shrink")
    work_hrs_day = 8  # standard working hours per day
    auto_epd_default = round(work_hrs_day * 60 / def_aht_e) if def_aht_e > 0 else 30
    eff_epd_default  = def_epd_e if def_epd_e > 0 else auto_epd_default
    st.caption(f"ℹ️ Default emails/day: **{eff_epd_default}** "
               f"({'manual override' if def_epd_e > 0 else f'auto from {def_aht_e} min AHT x {work_hrs_day}h day'})")
    if st.button("⬇ Apply defaults to all months", key="email_apply_defaults", type="secondary"):
        for m in MONTHS:
            st.session_state[f"email_{m}_vol"] = int(def_vol_e)
            st.session_state[f"email_{m}_aht"] = int(def_aht_e)
            st.session_state[f"email_{m}_epd"] = int(def_epd_e)
            st.session_state[f"email_{m}_shr"] = int(def_shrk_e)
        st.rerun()
    st.divider()
    st.markdown("<div class='sched-hdr'>Monthly Forecast Schedule</div>", unsafe_allow_html=True)
    hcols = st.columns([1.0,1.4,1.2,1.2,1.0,1.2,1.0,1.0])
    for col, lbl in zip(hcols, ["Month","Volume","AHT(min)","Emails/day","Override","Shrink%","Prod.HC","Rostered"]):
        col.markdown(f"**{lbl}**")
    e_schedule = []
    for m in MONTHS:
        c_m,c_v,c_a,c_ae,c_ov,c_sh,c_ph,c_rh = st.columns([1.0,1.4,1.2,1.2,1.0,1.2,1.0,1.0])
        c_m.markdown(f"**{m}**")
        vol = c_v.number_input("",  value=int(def_vol_e),  step=100, min_value=0,  key=f"email_{m}_vol", label_visibility="collapsed")
        aht = c_a.number_input("",  value=int(def_aht_e),  step=1,   min_value=1,  key=f"email_{m}_aht", label_visibility="collapsed")
        auto_epd = round(work_hrs_day * 60 / aht) if aht > 0 else 30
        c_ae.markdown(f"<span style='color:#10b981;font-size:13px'>{auto_epd}</span>", unsafe_allow_html=True)
        override = c_ov.number_input("", value=int(def_epd_e), step=1, min_value=0, key=f"email_{m}_epd", label_visibility="collapsed")
        shr = c_sh.number_input("",  value=int(def_shrk_e), step=1,   min_value=0, max_value=40, key=f"email_{m}_shr", label_visibility="collapsed")
        eff_epd = override if override > 0 else auto_epd
        monthly_cap = eff_epd * work_days
        prod_hc = vol / monthly_cap if monthly_cap > 0 and vol > 0 else 0
        ros = math.ceil(rostered_hc(prod_hc, shr)) if vol > 0 else 0
        c_ph.markdown(f"{'—' if vol==0 else f'{prod_hc:.1f}'}")
        c_rh.markdown(f"**{'—' if vol==0 else ros}**")
        e_schedule.append({"month":m,"volume":vol,"aht_mins":aht,"emails_per_day":eff_epd,"shrink_pct":shr,"productive_hc":prod_hc,"rostered_hc":ros})
    st.divider()
    full_year_summary(e_schedule)
    push_all_months_ui(e_schedule, "email")

# ═══════════════════════════════════════════════════════════════
# 4. BLENDED
# ═══════════════════════════════════════════════════════════════
elif work_type == "Blended":
    st.markdown("### Blended — Monthly Schedule")
    st.caption("Agents handle multiple work types. Required HC = binding constraint across all types.")
    bc1,bc2 = st.columns(2)
    n_types  = bc1.number_input("Number of work types", value=2, min_value=1, max_value=4, step=1, key="blend_n_types")
    b_shrink = bc2.slider("Default shrinkage %", 0, 40, global_shrink, 1, format="%d%%", key="blend_shrink")
    st.markdown("#### Work type mix")
    type_opts = ["Claims / Back-office", "Email / Async", "Outbound", "Other"]
    wt_defs = []; total_split = 0
    for t in range(int(n_types)):
        tc1,tc2,tc3,tc4 = st.columns(4)
        wname = tc1.selectbox(f"Type {t+1}", type_opts, key=f"blend_wname_{t}")
        waht  = tc2.number_input(f"AHT mins (type {t+1})", value=12, step=1, min_value=1, key=f"blend_waht_{t}",
                                  help="Auto-derives prod/hr = 60 / AHT. Override below if needed.")
        auto_wprod = round(60 / waht, 2) if waht > 0 else 5
        wprod_ov = tc3.number_input(f"Prod/hr override (0=auto) type {t+1}", value=0, step=1, min_value=0, key=f"blend_wprod_{t}")
        wprod = wprod_ov if wprod_ov > 0 else auto_wprod
        tc3.caption(f"Using: {wprod:.1f}/hr")
        wspl  = tc4.number_input(f"Time split % (type {t+1})", value=int(100//n_types), step=5, min_value=1, max_value=100, key=f"blend_wspl_{t}")
        wt_defs.append({"name":wname,"aht_mins":waht,"prod_hr":wprod,"split":wspl}); total_split += wspl
    if abs(total_split - 100) > 1:
        st.warning(f"Time splits sum to {total_split}% — should equal 100%.")
    st.divider()
    st.markdown("<div class='sched-hdr'>Monthly Forecast Schedule</div>", unsafe_allow_html=True)
    def_vol_b = st.number_input("Default monthly volume (total)", value=5000, step=100, min_value=0, key="blend_def_vol")
    if st.button("⬇ Apply defaults to all months", key="blend_apply_defaults", type="secondary"):
        for m in MONTHS:
            st.session_state[f"blend_{m}_vol"] = int(def_vol_b)
            st.session_state[f"blend_{m}_shr"] = int(b_shrink)
        st.rerun()
    st.divider()
    hcols = st.columns([1.2,1.8,1.2,1.2,1.2])
    for col, lbl in zip(hcols, ["Month","Total Volume","Shrink%","Prod.HC","Rostered"]):
        col.markdown(f"**{lbl}**")
    b_schedule = []
    for m in MONTHS:
        c_m,c_v,c_sh,c_ph,c_rh = st.columns([1.2,1.8,1.2,1.2,1.2])
        c_m.markdown(f"**{m}**")
        vol = c_v.number_input("",  value=int(def_vol_b), step=100, min_value=0, key=f"blend_{m}_vol", label_visibility="collapsed")
        shr = c_sh.number_input("", value=int(b_shrink),  step=1,   min_value=0, max_value=40, key=f"blend_{m}_shr", label_visibility="collapsed")
        max_hc = 0
        if vol > 0 and total_split > 0:
            for wd in wt_defs:
                eff_prod = wd["prod_hr"] * (wd["split"]/100) * global_hours
                hc_for_type = vol * (wd["split"]/100) / eff_prod if eff_prod > 0 else 0
                max_hc = max(max_hc, hc_for_type)
        ros = math.ceil(rostered_hc(max_hc, shr)) if vol > 0 else 0
        c_ph.markdown(f"{'—' if vol==0 else f'{max_hc:.1f}'}")
        c_rh.markdown(f"**{'—' if vol==0 else ros}**")
        b_schedule.append({"month":m,"volume":vol,"shrink_pct":shr,"productive_hc":max_hc,"rostered_hc":ros})
    st.divider()
    full_year_summary(b_schedule)
    push_all_months_ui(b_schedule, "blended")

st.divider()
st.caption(f"Models: Productivity (Claims, Email, Blended) = volume / adjusted capacity. Erlang-C (Voice) = queueing theory. Worked hours: {global_hours}h/month from budget settings.")
