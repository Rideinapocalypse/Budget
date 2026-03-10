"""
CCBudget — Target Margin Calculator
Standalone what-if tool. Read-only — never writes to budget blocks.
"""

import math
import streamlit as st

st.set_page_config(
    page_title="Target Margin — CCBudget",
    page_icon="🎯",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card {
    background:#1e2535; border:1px solid #2a3347;
    border-radius:8px; padding:16px; text-align:center;
}
.metric-val  { color:#e8edf5; font-size:22px; font-weight:700; }
.metric-lbl  { color:#8b96b0; font-size:11px; margin-top:4px; }
.metric-sub  { color:#8b96b0; font-size:11px; margin-top:2px; }
.result-box  {
    border-radius:8px; padding:18px 24px; margin-top:12px;
    border:1px solid #2a3347;
}
.result-green { background:#0f2318; border-color:#10b98155; }
.result-red   { background:#2d1f1f; border-color:#ef444455; }
.result-amber { background:#2a2010; border-color:#f59e0b55; }
.answer-val   { font-size:32px; font-weight:700; }
.answer-lbl   { color:#8b96b0; font-size:12px; margin-top:4px; }
.section-hdr  {
    font-size:11px; font-weight:700; letter-spacing:.08em;
    text-transform:uppercase; color:#5a6480;
    border-bottom:1px solid #2a3347; padding-bottom:4px;
    margin-bottom:16px; margin-top:8px;
}
.hint-box {
    background:#1e2535; border:1px solid #3b82f655;
    border-radius:6px; padding:10px 14px;
    color:#8b96b0; font-size:13px; margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

def metric_card(label, value, sub="", color="#e8edf5"):
    return (
        f"<div class='metric-card'>"
        f"<div class='metric-val' style='color:{color}'>{value}</div>"
        f"<div class='metric-lbl'>{label}</div>"
        f"{'<div class=metric-sub>' + sub + '</div>' if sub else ''}"
        f"</div>"
    )

def result_box(label, value, sub, status="green"):
    cls = f"result-{status}"
    color = {"green":"#10b981","red":"#ef4444","amber":"#f59e0b"}.get(status,"#e8edf5")
    return (
        f"<div class='result-box {cls}'>"
        f"<div class='answer-val' style='color:{color}'>{value}</div>"
        f"<div class='answer-lbl'>{label}</div>"
        f"{'<div style=\"color:#8b96b0;font-size:12px;margin-top:6px\">' + sub + '</div>' if sub else ''}"
        f"</div>"
    )

# ── Pull globals from budget session state ────────────────────
g_fx     = st.session_state.get("g_fx",     51.0)
g_hours  = st.session_state.get("g_hours",  180)
g_shrink = st.session_state.get("g_shrink", 0.15)

# ── Header ────────────────────────────────────────────────────
st.markdown("## 🎯 Target Margin Calculator")
st.caption(
    "What-if tool — never modifies your budget. "
    "Three modes: solve for Unit Price, solve for HC, or check your current margin gap."
)
st.divider()

# ── Mode selector ─────────────────────────────────────────────
mode = st.radio(
    "What do you want to solve for?",
    [
        "💶 Min Unit Price — given HC, what rate do I need?",
        "👥 Max HC — given a rate, how many agents can I afford?",
        "📊 Margin Check — given HC + rate, what margin am I at?",
    ],
    horizontal=False, key="tm_mode"
)
st.divider()

# ── Shared cost inputs ────────────────────────────────────────
st.markdown("<div class='section-hdr'>Cost Inputs</div>", unsafe_allow_html=True)

ci1, ci2, ci3, ci4 = st.columns(4)
salary     = ci1.number_input("Base Salary (TRY/mo)", value=30000, step=500, min_value=0, key="tm_salary")
ctc        = ci2.number_input("CTC multiplier", value=1.70, step=0.05, min_value=1.0, key="tm_ctc",
                               help="Salary × CTC covers employer costs, benefits etc.")
bonus_pct  = ci3.number_input("Bonus %", value=0.10, step=0.01, min_value=0.0, key="tm_bonus",
                               help="As a decimal, e.g. 0.10 = 10%")
meal       = ci4.number_input("Meal card (TRY/mo)", value=5850, step=50, min_value=0, key="tm_meal")

ci5, ci6, ci7, ci8 = st.columns(4)
fx         = ci5.number_input("FX Rate (EUR/TRY)", value=float(g_fx), step=0.5, min_value=0.1, key="tm_fx")
hours      = ci6.number_input("Worked hrs/agent/mo", value=int(g_hours), step=1, min_value=1, key="tm_hours")
shrink_pct = ci7.slider("Shrinkage %", 0, 40, int(g_shrink * 100), 1, format="%d%%", key="tm_shrink")
overhead_eur = ci8.number_input("Monthly overhead (EUR)", value=0, step=100, min_value=0, key="tm_overhead",
                                 help="Any fixed monthly overhead to include in the cost base (EUR).")

# Derived per-agent cost
shrink      = shrink_pct / 100
eff_hrs     = hours * (1 - shrink)
cost_per_agent_try = salary * ctc * (1 + bonus_pct) + meal
cost_per_agent_eur = cost_per_agent_try / fx if fx else 0

st.markdown(
    f"<div class='hint-box'>"
    f"Cost per agent: <b>₺{cost_per_agent_try:,.0f}/mo</b> = "
    f"<b>€{cost_per_agent_eur:,.2f}/mo</b>  ·  "
    f"Effective hrs/agent: <b>{eff_hrs:.1f}h</b>  ·  "
    f"Cost/hr: <b>€{cost_per_agent_eur/eff_hrs:.2f}</b>"
    f"</div>",
    unsafe_allow_html=True
)

st.divider()

# ═══════════════════════════════════════════════════════════════
# MODE 1 — Solve for Min Unit Price
# ═══════════════════════════════════════════════════════════════
if mode.startswith("💶"):
    st.markdown("<div class='section-hdr'>Solve for Minimum Unit Price</div>", unsafe_allow_html=True)
    m1c1, m1c2 = st.columns(2)
    hc            = m1c1.number_input("Headcount (HC)", value=10, step=1, min_value=1, key="tm_hc")
    target_margin = m1c2.slider("Target margin %", 0, 60, 20, 1, format="%d%%", key="tm_target_margin")

    total_cost_eur = hc * cost_per_agent_eur + overhead_eur
    total_hrs      = hc * eff_hrs
    # Revenue needed = cost / (1 - margin%)
    target_margin_dec = target_margin / 100
    if target_margin_dec >= 1:
        st.error("Target margin must be below 100%.")
    elif total_hrs == 0:
        st.error("Effective hours is 0 — check shrinkage and hours inputs.")
    else:
        rev_needed   = total_cost_eur / (1 - target_margin_dec)
        min_up       = rev_needed / total_hrs
        breakeven_up = total_cost_eur / total_hrs  # at 0% margin

        r1, r2, r3, r4 = st.columns(4)
        r1.markdown(metric_card("Total Monthly Cost", f"€{total_cost_eur:,.0f}",
                                f"{hc} agents + €{overhead_eur:,.0f} overhead"), unsafe_allow_html=True)
        r2.markdown(metric_card("Billable Hours", f"{total_hrs:,.0f}h",
                                f"{hc} HC × {eff_hrs:.1f}h"), unsafe_allow_html=True)
        r3.markdown(metric_card("Break-even Price", f"€{breakeven_up:.2f}/hr",
                                "0% margin"), unsafe_allow_html=True)
        r4.markdown(metric_card("Revenue Needed", f"€{rev_needed:,.0f}",
                                f"at {target_margin}% margin"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            result_box(
                f"Minimum Unit Price for {target_margin}% margin",
                f"€{min_up:.2f}/hr",
                f"Anything below €{breakeven_up:.2f}/hr loses money. "
                f"Every €1 above break-even adds €{total_hrs:,.0f} monthly margin.",
                "green"
            ), unsafe_allow_html=True
        )

        # Sensitivity table — margin at different UPs
        st.markdown("<br>**Rate sensitivity** — margin at different unit prices:", unsafe_allow_html=True)
        sens_cols = st.columns(6)
        for idx, delta in enumerate([-4, -2, 0, 2, 4, 6]):
            test_up  = max(0, min_up + delta)
            test_rev = test_up * total_hrs
            test_mgn = (test_rev - total_cost_eur) / test_rev * 100 if test_rev else 0
            color    = "#10b981" if test_mgn >= target_margin else "#ef4444"
            label    = f"€{test_up:.2f}/hr"
            sens_cols[idx].markdown(
                metric_card(label, f"{test_mgn:.1f}%",
                            "✅" if test_mgn >= target_margin else "⚠️", color),
                unsafe_allow_html=True
            )

# ═══════════════════════════════════════════════════════════════
# MODE 2 — Solve for Max HC
# ═══════════════════════════════════════════════════════════════
elif mode.startswith("👥"):
    st.markdown("<div class='section-hdr'>Solve for Maximum HC</div>", unsafe_allow_html=True)
    m2c1, m2c2, m2c3 = st.columns(3)
    unit_price    = m2c1.number_input("Unit Price (EUR/hr)", value=15.0, step=0.5, min_value=0.1, key="tm_up")
    target_margin = m2c2.slider("Target margin %", 0, 60, 20, 1, format="%d%%", key="tm_target_margin2")
    volume_hrs    = m2c3.number_input("Total billable hours needed/mo", value=0, step=100, min_value=0,
                                       key="tm_vol_hrs",
                                       help="Leave 0 to solve purely from cost budget. "
                                            "Enter a value to also check if HC covers your volume.")

    target_margin_dec = target_margin / 100
    # Max cost allowed = revenue × (1 - margin%)
    # Revenue = HC × eff_hrs × UP → solve for HC
    # max_cost = HC × eff_hrs × UP × (1 - margin%) - overhead
    # HC × cost_per_agent_eur = HC × eff_hrs × UP × (1-m%) - overhead
    # HC × [cost_per_agent_eur - eff_hrs × UP × (1-m%)] = -overhead
    rev_per_agent = eff_hrs * unit_price
    margin_pool_per_agent = rev_per_agent * (1 - target_margin_dec)

    if margin_pool_per_agent <= 0:
        st.error("Unit price is too low — revenue per agent can't cover costs at this margin target.")
    elif cost_per_agent_eur <= 0:
        st.error("Cost per agent is 0 — check salary inputs.")
    else:
        # cost_per_agent_eur ≤ margin_pool_per_agent to be profitable per agent
        if cost_per_agent_eur > margin_pool_per_agent:
            st.markdown(
                result_box(
                    "Cannot achieve target margin at this rate",
                    "0 agents",
                    f"Cost/agent (€{cost_per_agent_eur:.2f}) exceeds allowed cost "
                    f"at {target_margin}% margin (€{margin_pool_per_agent:.2f}). "
                    f"You need a rate of at least €{cost_per_agent_eur/eff_hrs/(1-target_margin_dec):.2f}/hr.",
                    "red"
                ), unsafe_allow_html=True
            )
        else:
            # overhead eats into HC budget
            # total_cost = HC × cost_per_agent + overhead ≤ total_rev × (1 - margin%)
            # total_rev = HC × eff_hrs × UP
            # HC × cost_per_agent + overhead ≤ HC × eff_hrs × UP × (1-m%)
            # HC × (eff_hrs × UP × (1-m%) - cost_per_agent) ≥ overhead
            denominator = margin_pool_per_agent - cost_per_agent_eur
            if denominator <= 0:
                max_hc = 0
            else:
                max_hc = math.floor((- overhead_eur) / (cost_per_agent_eur - margin_pool_per_agent))

            # Re-check with overhead
            max_hc = max(0, max_hc)
            actual_rev  = max_hc * eff_hrs * unit_price
            actual_cost = max_hc * cost_per_agent_eur + overhead_eur
            actual_mgn  = (actual_rev - actual_cost) / actual_rev * 100 if actual_rev else 0

            r1, r2, r3, r4 = st.columns(4)
            r1.markdown(metric_card("Max HC", str(max_hc), f"at {target_margin}% margin"), unsafe_allow_html=True)
            r2.markdown(metric_card("Monthly Revenue", f"€{actual_rev:,.0f}",
                                    f"{max_hc} HC × {eff_hrs:.1f}h × €{unit_price}/hr"), unsafe_allow_html=True)
            r3.markdown(metric_card("Monthly Cost", f"€{actual_cost:,.0f}",
                                    f"incl. €{overhead_eur:,.0f} overhead"), unsafe_allow_html=True)
            r4.markdown(metric_card("Actual Margin", f"{actual_mgn:.1f}%",
                                    "✅" if actual_mgn >= target_margin else "⚠️",
                                    "#10b981" if actual_mgn >= target_margin else "#f59e0b"), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            status = "green" if max_hc > 0 else "red"
            st.markdown(
                result_box(
                    f"Maximum HC for {target_margin}% margin at €{unit_price}/hr",
                    f"{max_hc} agents",
                    f"Adding agent #{max_hc+1} would drop margin below {target_margin}%. "
                    f"Revenue/agent: €{rev_per_agent:.2f}  ·  Cost/agent: €{cost_per_agent_eur:.2f}",
                    status
                ), unsafe_allow_html=True
            )

            if volume_hrs > 0:
                hc_for_volume = math.ceil(volume_hrs / eff_hrs) if eff_hrs else 0
                st.markdown("<br>", unsafe_allow_html=True)
                if hc_for_volume <= max_hc:
                    st.markdown(
                        result_box(
                            "Volume check",
                            f"✅ {hc_for_volume} HC needed for {volume_hrs:,}h volume",
                            f"Within your HC budget of {max_hc}. "
                            f"You have {max_hc - hc_for_volume} agents of headroom.",
                            "green"
                        ), unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        result_box(
                            "Volume check",
                            f"⚠️ {hc_for_volume} HC needed but max is {max_hc}",
                            f"You're short by {hc_for_volume - max_hc} agents. "
                            f"To cover volume AND hit {target_margin}% margin, "
                            f"you need €{(actual_cost + (hc_for_volume - max_hc) * cost_per_agent_eur) / (volume_hrs * (1 - target_margin_dec)):.2f}/hr.",
                            "red"
                        ), unsafe_allow_html=True
                    )

# ═══════════════════════════════════════════════════════════════
# MODE 3 — Margin Check
# ═══════════════════════════════════════════════════════════════
elif mode.startswith("📊"):
    st.markdown("<div class='section-hdr'>Margin Check</div>", unsafe_allow_html=True)
    m3c1, m3c2, m3c3 = st.columns(3)
    hc          = m3c1.number_input("Headcount (HC)", value=10, step=1, min_value=1, key="tm_hc3")
    unit_price  = m3c2.number_input("Unit Price (EUR/hr)", value=15.0, step=0.5, min_value=0.0, key="tm_up3")
    target_mgn  = m3c3.slider("Target margin %", 0, 60, 20, 1, format="%d%%", key="tm_tgt3")

    total_cost  = hc * cost_per_agent_eur + overhead_eur
    total_hrs   = hc * eff_hrs
    total_rev   = total_hrs * unit_price
    margin_eur  = total_rev - total_cost
    margin_pct  = margin_eur / total_rev * 100 if total_rev else 0
    breakeven   = total_cost / total_hrs if total_hrs else 0
    gap_pct     = margin_pct - target_mgn
    gap_up      = unit_price - breakeven * (1 / (1 - target_mgn/100)) if target_mgn < 100 else 0

    r1, r2, r3, r4, r5 = st.columns(5)
    r1.markdown(metric_card("Revenue", f"€{total_rev:,.0f}", f"{total_hrs:,.0f}h × €{unit_price}/hr"), unsafe_allow_html=True)
    r2.markdown(metric_card("Cost", f"€{total_cost:,.0f}", f"{hc} HC + overhead"), unsafe_allow_html=True)
    r3.markdown(metric_card("Gross Margin", f"€{margin_eur:,.0f}", f"{margin_pct:.1f}%",
                            "#10b981" if margin_eur >= 0 else "#ef4444"), unsafe_allow_html=True)
    r4.markdown(metric_card("Break-even Price", f"€{breakeven:.2f}/hr", "0% margin"), unsafe_allow_html=True)
    r5.markdown(metric_card("Target", f"{target_mgn}%",
                            "✅ achieved" if margin_pct >= target_mgn else f"⚠️ {abs(gap_pct):.1f}pp short",
                            "#10b981" if margin_pct >= target_mgn else "#ef4444"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if margin_pct >= target_mgn:
        needed_up = total_cost / (total_hrs * (1 - target_mgn/100)) if total_hrs and target_mgn < 100 else 0
        st.markdown(
            result_box(
                f"You're above target — {margin_pct:.1f}% vs {target_mgn}% target",
                f"+{gap_pct:.1f}pp headroom",
                f"You could drop your rate to €{needed_up:.2f}/hr and still hit {target_mgn}%. "
                f"Or absorb {math.floor(margin_eur / cost_per_agent_eur) if cost_per_agent_eur else 0} more agents before falling below target.",
                "green"
            ), unsafe_allow_html=True
        )
    elif margin_eur >= 0:
        needed_up = total_cost / (total_hrs * (1 - target_mgn/100)) if total_hrs and target_mgn < 100 else 0
        st.markdown(
            result_box(
                f"Profitable but below target — {margin_pct:.1f}% vs {target_mgn}% target",
                f"Need €{needed_up:.2f}/hr to hit {target_mgn}%",
                f"Currently €{unit_price:.2f}/hr. Gap = €{needed_up - unit_price:.2f}/hr. "
                f"Or reduce HC by {math.ceil((total_cost - total_rev * (1-target_mgn/100)) / cost_per_agent_eur) if cost_per_agent_eur else 0} agents.",
                "amber"
            ), unsafe_allow_html=True
        )
    else:
        st.markdown(
            result_box(
                f"Loss-making — need at least €{breakeven:.2f}/hr to break even",
                f"€{margin_eur:,.0f} monthly loss",
                f"You're €{abs(unit_price - breakeven):.2f}/hr below break-even. "
                f"At current rate, max affordable HC is "
                f"{math.floor((total_rev * (1-target_mgn/100) - overhead_eur) / cost_per_agent_eur) if cost_per_agent_eur else 0}.",
                "red"
            ), unsafe_allow_html=True
        )

    # Margin bridge — show what moves the needle
    st.divider()
    st.markdown("#### What moves your margin?")
    bridge_cols = st.columns(4)
    impact_up1    = (total_hrs * 1) / total_rev * 100 if total_rev else 0
    impact_hc1    = (-cost_per_agent_eur) / total_rev * 100 if total_rev else 0
    impact_sal500 = (-500 / fx * hc) / total_rev * 100 if total_rev and fx else 0
    impact_shr2   = (hc * hours * 0.02 * unit_price) / total_rev * 100 if total_rev else 0

    bridge_cols[0].markdown(metric_card("+€1/hr on rate",    f"{impact_up1:+.1f}pp",  "margin impact", "#10b981"), unsafe_allow_html=True)
    bridge_cols[1].markdown(metric_card("-1 HC",             f"{impact_hc1:+.1f}pp",  "margin impact", "#10b981"), unsafe_allow_html=True)
    bridge_cols[2].markdown(metric_card("-₺500 salary",      f"{impact_sal500:+.1f}pp","margin impact", "#10b981"), unsafe_allow_html=True)
    bridge_cols[3].markdown(metric_card("-2pp shrinkage",    f"{impact_shr2:+.1f}pp", "margin impact", "#10b981"), unsafe_allow_html=True)

st.divider()
st.caption(
    "📐 All calculations use: Revenue = HC × (hours × (1−shrinkage)) × unit price. "
    "Cost = HC × salary × CTC × (1+bonus) + meal cards, converted at FX rate. "
    "Overhead added on top. This tool is read-only — no budget data is modified."
)
