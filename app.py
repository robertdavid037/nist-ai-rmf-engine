import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.db import init_db, get_connection

st.set_page_config(
    page_title="AI Security Posture Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none; }
    .tier-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 16px;
        font-size: 13px;
        font-weight: 700;
        color: white;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

init_db()

TIER_BG = {
    "Minimal": "#27ae60",
    "Limited": "#f39c12",
    "High": "#e74c3c",
    "Unacceptable": "#6c3483",
}
TIER_EMOJI = {
    "Minimal": "🟢",
    "Limited": "🟡",
    "High": "🔴",
    "Unacceptable": "⛔",
}

# ── Top bar ───────────────────────────────────────────────────────────────────
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("🛡️ AI Security Posture Dashboard")
    st.caption("NIST AI Risk Management Framework 1.0")
with col_btn:
    st.write("")
    if st.button("＋ New Assessment", type="primary", use_container_width=True):
        st.switch_page("pages/1_Assessment.py")

st.divider()

# ── Sort controls ─────────────────────────────────────────────────────────────
sort_by = st.radio(
    "Sort by:",
    ["Risk (Highest First)", "Compliance (Highest First)", "Date (Most Recent)"],
    horizontal=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
conn = get_connection()
rows = conn.execute("""
    SELECT t.name, t.vendor, t.category,
           a.id AS assessment_id,
           a.compliance_pct, a.risk_tier, a.assessed_at, a.next_review_date
    FROM tools t
    JOIN assessments a ON a.tool_id = t.id
    WHERE a.id = (
        SELECT id FROM assessments
        WHERE tool_id = t.id
        ORDER BY assessed_at DESC
        LIMIT 1
    )
""").fetchall()
conn.close()

tools = [dict(r) for r in rows]

# Apply sort
if sort_by == "Risk (Highest First)":
    tools.sort(key=lambda x: x["compliance_pct"])
elif sort_by == "Compliance (Highest First)":
    tools.sort(key=lambda x: x["compliance_pct"], reverse=True)
else:
    tools.sort(key=lambda x: x["assessed_at"], reverse=True)

# ── Cards ─────────────────────────────────────────────────────────────────────
if not tools:
    st.info("No assessments yet. Click **＋ New Assessment** to get started.")
else:
    st.caption(f"{len(tools)} tool{'s' if len(tools) != 1 else ''} assessed")
    cols = st.columns(3)

    for i, tool in enumerate(tools):
        tier = tool["risk_tier"]
        color = TIER_BG.get(tier, "#888")
        emoji = TIER_EMOJI.get(tier, "")
        pct = tool["compliance_pct"]

        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{tool['name']}**")
                st.caption(f"{tool['vendor']} · {tool['category']}")

                st.markdown(
                    f"<div class='tier-badge' style='background:{color}'>{emoji} {tier} Risk</div>",
                    unsafe_allow_html=True,
                )

                st.metric("Compliance", f"{pct}%")
                st.progress(pct / 100)

                assessed = tool["assessed_at"][:10]
                next_rev = tool["next_review_date"]
                st.caption(f"Assessed {assessed} · Review due {next_rev}")

                if st.button(
                    "View Full Report →",
                    key=f"view_{tool['assessment_id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_assessment_id = tool["assessment_id"]
                    st.switch_page("pages/2_Report.py")
