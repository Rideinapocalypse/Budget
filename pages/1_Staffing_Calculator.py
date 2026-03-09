"""
CCBudget — Staffing Calculator
Separate page: productivity-based & Erlang-C HC sizing
Shares st.session_state with the main budget app.
"""

import math
import streamlit as st

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Staffing Calculator — CCBudget",
    page_icon="🧮",
    layout="wide",
)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Shared state helpers ──────────────────────────────────────
def get_clients():
    return st.session_state.get("clients", [])

def client_names():
    return [c["name"] for c in get_clients()]

# ── Styling (match main app) ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card {
    background: #1e2535; border: 1px solid #2a3347;
    border-radius: 8px; padding: 16px; text-align: center;
}
.metric-val  { color: #e8edf5; font-size: 22px; font-weight: 700; }
.metric-lbl  { color: #8b96b0; font-size: 11px; margin-top: 4px; }
.metric-sub  { color: #8b96b0; font-size: 11px; margin-top: 2px; }
.warn-box    { background:#2d1f1f; border:1px solid #ef444455;
               border-radius:6px; padding:10px 14px; color:#ef4444;
               font-size:13px; margin-top:8px; }
.ok-box      { background:#1a2d1f; border:1px solid #10b98155;
               border-radius:6px; padding:10px 14px; color:#10b981;
               font-size:13px; margin-top:8px; }
.info-box    { background:#1e2535; border:1px solid #3b82f655;
               border-radius:6px; padding:10px 14px; color:#8b96b0;
               font-size:13px; margin-top:8px; }
.section-title {
    font-size:11px; font-weight:700; letter-spacing:.08em;
    text-transform:uppercase; color:#5a6480;
    border-bottom:1px solid #2a3347; padding-bottom:4px;
    margin-bottom:12px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("## 🧮 Staffing Calculator")
st.caption(
    "Size your team from actual workload — not guesswork. "
    "Choose a work type, enter volume and productivity, get required HC. "
    "Then push directly to a block in your budget."
)

if not get_clients():
    st.info("No clients found. Go to the main Budget page and set up at least one client first.", icon="ℹ️")
    st.stop()

st.divider()

# ── Work type selector ────────────────────────────────────────
work_type = st.radio(
    "Work type",
    ["📋 Claims / Back-office", "📞 Inbound Voice (Erlang-C)",
     "✉️ Email / Async", "🔀 Blended"],
    horizontal=True, key="sc_work_type"
)

st.divider()

# ═══════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════
def rostered_hc(productive_hc, shrinkage_pct):
    """Productive HC → rostered HC after shrinkage."""
    shrink = max(0.0, min(0.99, shrinkage_pct / 100))
    return productive_hc / (1 - shrink) if shrink < 1 else productive_hc

def occupancy(productive_hc, traffic_erlangs):
    """Occupancy = traffic / productive agents."""
    return (traffic_erlangs / productive_hc * 100) if productive_hc else 0

def occ_status(occ_pct):
    if occ_pct > 90:
        return "warn", f"⚠️ Occupancy {occ_pct:.1f}% — agents are overloaded. Quality and attrition will suffer."
    elif occ_pct > 85:
        return "warn", f"⚠️ Occupancy {occ_pct:.1f}% — at the edge. Consider adding 1–2 agents."
    elif occ_pct < 60:
        return "info", f"ℹ️ Occupancy {occ_pct:.1f}% — agents have significant idle time. Review volume or reduce HC."
    else:
        return "ok", f"✅ Occupancy {occ_pct:.1f}% — healthy range (60–85%)."

def metric_card(label, value, sub=""):
    return (
        f"<div class='metric-card'>"
        f"<div class='metric-val'>{value}</div>"
        f"<div class='metric-lbl'>{label}</div>"
        f"{'<div class=metric-sub>' + sub + '</div>' if sub else ''}"
        f"</div>"
    )

def results_row(cols_data):
    cols = st.columns(len(cols_data))
    for col, (label, value, sub) in zip(cols, cols_data):
        col.markdown(metric_card(label, value, sub), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PUSH TO BLOCK
# ═══════════════════════════════════════════════════════════════
def push_to_block_ui(suggested_hc: float, key_prefix: str):
    """Shared UI for pushing calculated HC to a budget block."""
    st.divider()
    st.markdown("### 📤 Push to Budget Block")
    st.caption("Auto-fill the HC field in a block on the main budget page.")

    clients = get_clients()
    if not clients:
        st.info("No clients in budget. Add a client on the main page first.")
        return

    pb1, pb2, pb3, pb4 = st.columns([2, 2, 2, 1])

    client_idx = pb1.selectbox(
        "Client", range(len(clients)),
        format_func=lambda i: clients[i]["name"],
        key=f"{key_prefix}_push_client"
    )
    cl = clients[client_idx]

    # Get unique blocks by lang/label
    all_blocks_flat = []
    seen = set()
    for m in MONTHS:
        for bi, b in enumerate(cl["blocks"].get(m, [])):
            lbl = b.get("lang") or f"Block #{bi+1}"
            if lbl not in seen:
                seen.add(lbl)
                all_blocks_flat.append((lbl, bi))

    if not all_blocks_flat:
        pb2.warning("No blocks found in this client.")
        return

    block_choice = pb2.selectbox(
        "Block", all_blocks_flat,
        format_func=lambda x: x[0],
        key=f"{key_prefix}_push_block"
    )

    month_range = pb3.multiselect(
        "Apply to months", MONTHS,
        default=MONTHS,
        key=f"{key_prefix}_push_months"
    )

    hc_to_push = round(suggested_hc)
    st.markdown(
        f"<div class='info-box'>Will set HC = <b>{hc_to_push}</b> "
        f"(rostered, rounded) on block <b>{block_choice[0]}</b> "
        f"for months: <b>{', '.join(month_range) if month_range else 'none selected'}</b></div>",
        unsafe_allow_html=True
    )

    if pb4.button("⬆ Push", key=f"{key_prefix}_push_btn",
                  use_container_width=True, type="primary"):
        if not month_range:
            st.warning("Select at least one month.")
            return
        pushed = 0
        for m in month_range:
            blks = cl["blocks"].get(m, [])
            target_label = block_choice[0]
            for b in blks:
                lbl = b.get("lang") or f"Block #{blks.index(b)+1}"
                if lbl == target_label:
                    b["hc"] = hc_to_push
                    pushed += 1
        if pushed:
            st.success(
                f"✅ HC = {hc_to_push} pushed to '{block_choice[0]}' "
                f"across {pushed} month(s). Switch to the Budget page to see the update."
            )
        else:
            st.warning("No matching blocks found to update.")

# ═══════════════════════════════════════════════════════════════
# 1. CLAIMS / BACK-OFFICE
# ═══════════════════════════════════════════════════════════════
if work_type == "📋 Claims / Back-office":
    st.markdown("### 📋 Claims / Back-office Sizing")
    st.caption(
        "Best for: claims processing, back-office tasks, document handling, quality review. "
        "Model: Required HC = Monthly volume ÷ (productivity per hour × worked hours per month)."
    )

    # Pull worked hours from main budget session state, fallback to 180
    global_hours = st.session_state.get("g_hours", 180)

    c1, c2, c3 = st.columns(3)
    monthly_volume  = c1.number_input("Monthly work volume (units)", value=5000, step=100, min_value=1,
                                       help="Total claims, tickets, documents, etc. to process per month.")
    productivity_hr = c2.number_input("Productivity per agent / hour (units)", value=5, step=1, min_value=1,
                                       help="How many units one fully productive agent completes per hour.")
    shrink_pct      = c3.slider("Shrinkage %", 0, 40, 15, 1, format="%d%%",
                                 help="Breaks, sick leave, training, meetings. Productive HC ÷ (1 - shrinkage) = rostered HC.")

    c4, c5, c6 = st.columns(3)
    new_hire_ramp   = c4.slider("New hire ramp efficiency %", 10, 100, 70, 5, format="%d%%",
                                 help="If agents are new, they produce less than 100%. Adjusts effective productivity.")
    ramp_months     = c5.number_input("Ramp-up duration (months)", value=2, step=1, min_value=0, max_value=6,
                                       help="How many months the ramp efficiency applies. After this, full productivity.")
    worked_hours    = c6.number_input("Worked hours / agent / month", value=int(global_hours), step=5, min_value=1,
                                       help=f"Auto-filled from your budget global settings ({global_hours}h). Edit if needed.")

    # Calculation — per hour basis
    productivity_month = productivity_hr * worked_hours
    eff_productivity   = productivity_month * (new_hire_ramp / 100)
    productive_hc_raw  = monthly_volume / productivity_month
    productive_hc_ramp = monthly_volume / eff_productivity if ramp_months > 0 else productive_hc_raw
    rostered      = rostered_hc(productive_hc_raw, shrink_pct)
    rostered_ramp = rostered_hc(productive_hc_ramp, shrink_pct)
    util = monthly_volume / (max(1, math.ceil(rostered)) * productivity_month) * 100

    st.divider()
    st.markdown("#### Results")

    st.caption(
        f"ℹ️ Worked hours from budget: **{global_hours}h/month** · "
        f"Monthly capacity per agent: **{productivity_month:,.0f} units** "
        f"({productivity_hr} units/hr × {worked_hours}h)"
    )

    results_row([
        ("Productive HC needed", f"{productive_hc_raw:.1f}",
         f"{monthly_volume:,} ÷ {productivity_month:,.0f} units/agent/mo"),
        ("Rostered HC (after shrinkage)", f"{math.ceil(rostered)}",
         f"{productive_hc_raw:.1f} ÷ (1 − {shrink_pct}%)"),
        ("During ramp-up period", f"{math.ceil(rostered_ramp)}",
         f"At {new_hire_ramp}% efficiency × {ramp_months}mo"),
        ("Utilisation", f"{min(100, util):.1f}%", "Actual work ÷ capacity"),
    ])

    box_type, msg = occ_status(min(util * 0.85, 99))
    st.markdown(f"<div class='{box_type}-box'>{msg}</div>", unsafe_allow_html=True)

    with st.expander("📊 Sensitivity — rostered HC vs monthly volume", expanded=False):
        try:
            import plotly.graph_objects as go
            volumes = [int(monthly_volume * x / 100) for x in range(50, 201, 10)]
            hcs = [math.ceil(rostered_hc(v / productivity_month, shrink_pct)) for v in volumes]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=volumes, y=hcs, mode="lines+markers",
                line=dict(color="#3b82f6", width=2.5), marker=dict(size=5),
                hovertemplate="Volume: %{x:,}<br>HC needed: %{y}<extra></extra>"))
            fig.add_vline(x=monthly_volume, line_dash="dot", line_color="#f59e0b",
                          annotation_text=f"Current: {monthly_volume:,}",
                          annotation_font_color="#f59e0b")
            fig.update_layout(
                plot_bgcolor="#0e1420", paper_bgcolor="#0e1420",
                font=dict(color="#8b96b0"), height=260,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis=dict(showgrid=False, title="Monthly Volume"),
                yaxis=dict(showgrid=True, gridcolor="#1e2535", title="Rostered HC"),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

    push_to_block_ui(rostered, "claims")


# ═══════════════════════════════════════════════════════════════
# 2. INBOUND VOICE — ERLANG-C
# ═══════════════════════════════════════════════════════════════
elif work_type == "📞 Inbound Voice (Erlang-C)":
    st.markdown("### 📞 Inbound Voice — Erlang-C")
    st.caption(
        "For inbound queued voice traffic only. Assumes random (Poisson) arrivals, no abandonments. "
        "**Use interval-level inputs for accuracy** — monthly averages understate peak staffing needs."
    )

    st.info(
        "💡 Erlang-C works best at 15–30 min intervals. "
        "Monthly inputs give a planning approximation — treat results as a floor, not a ceiling.",
        icon="ℹ️"
    )

    c1, c2, c3 = st.columns(3)
    calls_per_hour  = c1.number_input("Calls per hour (peak interval)", value=120, step=5, min_value=1,
                                       help="Peak arrival rate. For monthly planning, use your busiest hour average.")
    aht_seconds     = c2.number_input("AHT — Average Handle Time (seconds)", value=240, step=10, min_value=10,
                                       help="Talk time + hold time + after-call work (wrap-up).")
    sl_target_pct   = c3.slider("Service Level target %", 50, 99, 80, 1, format="%d%%",
                                 help="% of calls to be answered within the target answer time.")

    c4, c5, c6 = st.columns(3)
    sl_seconds      = c4.number_input("Answer within (seconds)", value=20, step=5, min_value=1,
                                       help="The 'T' in '80% in 20 seconds'.")
    shrink_pct_v    = c5.slider("Shrinkage %", 0, 40, 15, 1, format="%d%%")
    max_agents      = c6.number_input("Max agents to model", value=60, step=5, min_value=5,
                                       help="Search ceiling for the Erlang-C solver.")

    # ── Erlang-C core ─────────────────────────────────────────
    def erlang_c(N, A):
        """Probability that a call has to wait (Erlang-C formula)."""
        if N <= A:
            return 1.0  # unstable — more traffic than agents
        # Compute (A^N / N!) / ((A^N / N!) + (1 - A/N) * sum_{k=0}^{N-1} A^k/k!)
        try:
            # Use log-space to avoid overflow
            log_AN_Nfact = N * math.log(A) - sum(math.log(k) for k in range(1, N + 1))
            sum_terms = sum(
                math.exp(k * math.log(A) - sum(math.log(j) for j in range(1, k + 1)))
                for k in range(N)
            )
            numerator   = math.exp(log_AN_Nfact)
            denominator = numerator + (1 - A / N) * sum_terms
            return numerator / denominator if denominator else 1.0
        except (OverflowError, ValueError):
            return 1.0

    def service_level(N, A, aht, t):
        """SL = 1 - C(N,A) * exp(-(N-A) * t/AHT)"""
        if N <= A:
            return 0.0
        c = erlang_c(N, A)
        return 1 - c * math.exp(-(N - A) * (t / aht))

    def asa(N, A, aht):
        """Average Speed of Answer in seconds."""
        if N <= A:
            return float('inf')
        c = erlang_c(N, A)
        return (c * aht) / (N - A)

    # Traffic intensity (Erlangs)
    A = (calls_per_hour / 3600) * aht_seconds
    sl_target = sl_target_pct / 100

    # Find minimum agents for SL target
    min_N = math.ceil(A) + 1
    required_N = None
    for n in range(min_N, max_agents + 1):
        if service_level(n, A, aht_seconds, sl_seconds) >= sl_target:
            required_N = n
            break

    st.divider()
    st.markdown("#### Results")

    if required_N is None:
        st.error(f"Could not reach {sl_target_pct}% SL within {max_agents} agents. "
                 f"Increase max agents or reduce the SL target.")
    else:
        actual_sl   = service_level(required_N, A, aht_seconds, sl_seconds) * 100
        actual_asa  = asa(required_N, A, aht_seconds)
        actual_occ  = (A / required_N) * 100
        rostered_v  = rostered_hc(required_N, shrink_pct_v)

        results_row([
            ("Traffic Intensity", f"{A:.2f} Erl", f"{calls_per_hour}/hr × {aht_seconds}s AHT"),
            ("Productive agents needed", f"{required_N}", f"For {sl_target_pct}% SL in {sl_seconds}s"),
            ("Rostered HC (after shrinkage)", f"{math.ceil(rostered_v)}", f"{required_N} ÷ (1 − {shrink_pct_v}%)"),
            ("Achieved Service Level", f"{actual_sl:.1f}%", f"Target: {sl_target_pct}%"),
            ("Avg Speed of Answer", f"{actual_asa:.0f}s", "Expected wait time"),
            ("Occupancy", f"{actual_occ:.1f}%", "Agent utilisation"),
        ])

        occ_type, occ_msg = occ_status(actual_occ)
        st.markdown(f"<div class='{occ_type}-box'>{occ_msg}</div>", unsafe_allow_html=True)

        # SL curve — show SL vs N agents
        with st.expander("📊 Service Level curve — agents vs SL achieved", expanded=True):
            try:
                import plotly.graph_objects as go
                ns = list(range(max(1, math.ceil(A)), min(required_N + 20, max_agents + 1)))
                sls = [service_level(n, A, aht_seconds, sl_seconds) * 100 for n in ns]
                occs = [(A / n) * 100 for n in ns]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ns, y=sls, name="Service Level %",
                    mode="lines+markers", line=dict(color="#3b82f6", width=2.5),
                    hovertemplate="Agents: %{x}<br>SL: %{y:.1f}%<extra></extra>",
                    yaxis="y1"
                ))
                fig.add_trace(go.Scatter(
                    x=ns, y=occs, name="Occupancy %",
                    mode="lines", line=dict(color="#f59e0b", width=1.5, dash="dot"),
                    hovertemplate="Agents: %{x}<br>Occupancy: %{y:.1f}%<extra></extra>",
                    yaxis="y1"
                ))
                fig.add_hline(y=sl_target_pct, line_dash="dash", line_color="#10b981",
                              annotation_text=f"Target {sl_target_pct}%",
                              annotation_font_color="#10b981")
                fig.add_hline(y=85, line_dash="dot", line_color="#ef4444",
                              annotation_text="85% occ. ceiling",
                              annotation_font_color="#ef4444")
                fig.add_vline(x=required_N, line_dash="dot", line_color="#5a6480",
                              annotation_text=f"Min: {required_N}",
                              annotation_font_color="#5a6480")
                fig.update_layout(
                    plot_bgcolor="#0e1420", paper_bgcolor="#0e1420",
                    font=dict(color="#8b96b0"), height=320,
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", y=1.06, bgcolor="rgba(0,0,0,0)"),
                    xaxis=dict(showgrid=False, title="Number of Agents"),
                    yaxis=dict(showgrid=True, gridcolor="#1e2535",
                               title="% ", ticksuffix="%"),
                    hoverlabel=dict(bgcolor="#1e2535", font=dict(color="#e8edf5")),
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass

        push_to_block_ui(rostered_v, "voice")


# ═══════════════════════════════════════════════════════════════
# 3. EMAIL / ASYNC
# ═══════════════════════════════════════════════════════════════
elif work_type == "✉️ Email / Async":
    st.markdown("### ✉️ Email / Async Channel Sizing")
    st.caption(
        "For email, web chat (async), ticket queues, social media DMs. "
        "Model: volume ÷ daily capacity, with SLA compliance constraint."
    )

    c1, c2, c3 = st.columns(3)
    monthly_volume_e = c1.number_input("Monthly contacts (emails / tickets)", value=3000, step=100, min_value=1)
    aht_mins         = c2.number_input("Avg handle time per contact (minutes)", value=8, step=1, min_value=1,
                                        help="Time to read, process and respond to one contact.")
    sla_hours        = c3.number_input("SLA — respond within (hours)", value=24, step=4, min_value=1,
                                        help="Your contractual response time commitment.")

    c4, c5, c6 = st.columns(3)
    work_hours_day   = c4.number_input("Agent work hours / day", value=8, step=1, min_value=1)
    work_days_month  = c5.number_input("Working days / month", value=22, step=1, min_value=1)
    shrink_pct_e     = c6.slider("Shrinkage %", 0, 40, 15, 1, format="%d%%")

    # Calculation
    # Contacts per hour per agent
    contacts_per_agent_hour = 60 / aht_mins
    contacts_per_agent_day  = contacts_per_agent_hour * work_hours_day
    contacts_per_agent_month = contacts_per_agent_day * work_days_month

    # SLA constraint: within SLA hours, how many contacts can 1 agent handle?
    # If SLA = 24h and agent works 8h/day, effective SLA window = 1 working day
    sla_working_days = max(1, sla_hours / work_hours_day)
    # To maintain SLA, queue must never build beyond sla_working_days × daily capacity
    # Required agents = daily_volume / (contacts_per_agent_day × sla_working_days)?
    # Simpler: just size for daily throughput to clear queue within SLA
    daily_volume = monthly_volume_e / work_days_month
    productive_hc_e  = daily_volume / contacts_per_agent_day
    rostered_e       = rostered_hc(productive_hc_e, shrink_pct_e)

    # SLA risk: can they clear daily volume before SLA breaches?
    throughput_per_agent_per_sla = contacts_per_agent_hour * sla_hours
    hc_for_sla = math.ceil(daily_volume / throughput_per_agent_per_sla)

    final_hc = max(math.ceil(productive_hc_e), hc_for_sla)
    final_rostered = math.ceil(rostered_hc(final_hc, shrink_pct_e))
    utilisation_e = (monthly_volume_e / (final_hc * contacts_per_agent_month)) * 100

    st.divider()
    st.markdown("#### Results")

    results_row([
        ("Daily volume", f"{daily_volume:.0f}", f"{monthly_volume_e:,} ÷ {work_days_month} days"),
        ("Capacity per agent/day", f"{contacts_per_agent_day:.0f}", f"8h ÷ {aht_mins}min AHT × {work_hours_day}h"),
        ("Productive HC (throughput)", f"{productive_hc_e:.1f}", "Daily vol ÷ daily capacity"),
        ("HC for SLA compliance", f"{hc_for_sla}", f"Clear queue within {sla_hours}h"),
        ("Recommended HC", f"{final_hc}", "Max of throughput and SLA HC"),
        ("Rostered HC", f"{final_rostered}", f"After {shrink_pct_e}% shrinkage"),
    ])

    # SLA warning
    if hc_for_sla > math.ceil(productive_hc_e):
        st.markdown(
            f"<div class='warn-box'>⚠️ SLA is the binding constraint. "
            f"You need <b>{hc_for_sla}</b> agents to guarantee {sla_hours}h SLA — "
            f"more than pure throughput requires ({math.ceil(productive_hc_e)}).</div>",
            unsafe_allow_html=True
        )
    else:
        util_type, util_msg = occ_status(utilisation_e)
        st.markdown(f"<div class='{util_type}-box'>{util_msg}</div>", unsafe_allow_html=True)

    push_to_block_ui(final_rostered, "email")


# ═══════════════════════════════════════════════════════════════
# 4. BLENDED
# ═══════════════════════════════════════════════════════════════
elif work_type == "🔀 Blended":
    st.markdown("### 🔀 Blended — Multi-work Type")
    st.caption(
        "Agents handle multiple work types in the same shift. "
        "Set the % time each agent spends on each channel — must sum to 100%. "
        "Tool calculates HC required for each work type then combines."
    )

    st.markdown("#### Define work type mix")
    mix_c1, mix_c2 = st.columns(2)
    n_types = mix_c1.number_input("Number of work types", value=2, min_value=1, max_value=5, step=1)
    shrink_pct_b = mix_c2.slider("Shrinkage %", 0, 40, 15, 1, format="%d%%", key="blend_shrink")

    st.divider()

    type_options = ["Claims / Back-office", "Inbound Voice", "Email / Async", "Outbound", "Other"]
    work_defs = []
    total_split = 0

    for t in range(int(n_types)):
        st.markdown(f"**Work Type {t+1}**")
        bc1, bc2, bc3, bc4 = st.columns([2, 2, 2, 1])
        wtype    = bc1.selectbox("Type", type_options, key=f"blend_type_{t}")
        volume   = bc2.number_input("Monthly volume", value=2000, step=100, min_value=0,
                                     key=f"blend_vol_{t}")
        prod     = bc3.number_input(
            "Productivity (units/agent/mo)" if wtype != "Inbound Voice" else "Calls/hour",
            value=400 if wtype != "Inbound Voice" else 12,
            step=10, min_value=1, key=f"blend_prod_{t}"
        )
        split    = bc4.number_input("Agent time %", value=int(100 // n_types),
                                     min_value=1, max_value=100, step=5,
                                     key=f"blend_split_{t}")
        work_defs.append({"type": wtype, "volume": volume, "prod": prod, "split": split})
        total_split += split
        if t < int(n_types) - 1:
            st.divider()

    # Validate split
    if abs(total_split - 100) > 1:
        st.warning(f"⚠️ Agent time splits sum to {total_split}% — must equal 100%.")

    st.divider()
    st.markdown("#### Blended Results")

    blend_rows = []
    max_hc_required = 0

    for wd in work_defs:
        split_fraction = wd["split"] / 100
        # Effective productivity adjusted for time split
        eff_prod = wd["prod"] * split_fraction
        if eff_prod > 0:
            hc_for_type = wd["volume"] / eff_prod
        else:
            hc_for_type = 0
        blend_rows.append({
            "Work Type":     wd["type"],
            "Monthly Vol":   f"{wd['volume']:,}",
            "Time Split":    f"{wd['split']}%",
            "Eff. Prod/mo":  f"{eff_prod:.0f}",
            "HC Required":   f"{hc_for_type:.1f}",
        })
        max_hc_required = max(max_hc_required, hc_for_type)

    # Total blended HC = max single-constraint HC
    # (agents split time, so one pool covers all)
    blended_productive = max_hc_required
    blended_rostered   = math.ceil(rostered_hc(blended_productive, shrink_pct_b))

    # Show breakdown table
    import pandas as pd
    df_blend = pd.DataFrame(blend_rows)
    st.dataframe(df_blend.set_index("Work Type"), use_container_width=True)

    st.divider()
    results_row([
        ("Binding constraint HC", f"{blended_productive:.1f}", "Highest HC requirement across all work types"),
        ("Rostered HC (blended)", f"{blended_rostered}", f"After {shrink_pct_b}% shrinkage"),
        ("Total split check", f"{total_split}%", "Must equal 100%"),
    ])

    if total_split == 100 or abs(total_split - 100) <= 1:
        st.markdown(
            f"<div class='ok-box'>✅ With <b>{blended_rostered}</b> rostered agents handling "
            f"{int(n_types)} work types at the defined splits, "
            f"all volume targets should be met.</div>",
            unsafe_allow_html=True
        )

    push_to_block_ui(blended_rostered, "blended")

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.caption(
    "📐 Models used: Productivity model (Claims, Email, Blended) = volume ÷ adjusted productivity. "
    "Erlang-C (Voice) = queueing theory for Poisson arrivals, assumes no abandonments. "
    "All HC outputs are planning approximations — validate against actual interval data."
)
