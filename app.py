import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.db import init_db, get_connection
from sidebar import render_sidebar
from translations import t

st.set_page_config(
    page_title="AI Security Posture Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
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
render_sidebar()

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
    st.title(f"🛡️ {t('dashboard_title')}")
    st.caption("NIST AI Risk Management Framework 1.0")
with col_btn:
    st.write("")
    if st.button(t("btn_new_assessment"), type="primary", use_container_width=True):
        st.switch_page("pages/1_Assessment.py")

st.divider()

# ── Sort controls ─────────────────────────────────────────────────────────────
sort_options = [t("sort_risk"), t("sort_compliance"), t("sort_date")]
sort_by = st.radio(t("sort_by"), sort_options, horizontal=True)
sort_idx = sort_options.index(sort_by)

# ── Load data ─────────────────────────────────────────────────────────────────
conn = get_connection()
rows = conn.execute("""
    SELECT t.name, t.vendor, t.category,
           a.id AS assessment_id,
           a.compliance_pct, a.risk_tier, a.assessed_at, a.next_review_date,
           a.loi25_pct
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
if sort_idx == 0:
    tools.sort(key=lambda x: x["compliance_pct"])
elif sort_idx == 1:
    tools.sort(key=lambda x: x["compliance_pct"], reverse=True)
else:
    tools.sort(key=lambda x: x["assessed_at"], reverse=True)

# ── Cards ─────────────────────────────────────────────────────────────────────
if not tools:
    st.info(t("no_assessments"))
else:
    st.caption(f"{len(tools)} {t('tools_assessed')}")
    cols = st.columns(3)

    for i, tool in enumerate(tools):
        tier  = tool["risk_tier"]
        color = TIER_BG.get(tier, "#888")
        emoji = TIER_EMOJI.get(tier, "")
        pct   = tool["compliance_pct"]
        tier_display = t(f"tier_{tier}")

        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{tool['name']}**")
                st.caption(f"{tool['vendor']} · {tool['category']}")

                st.markdown(
                    f"<div class='tier-badge' style='background:{color}'>"
                    f"{emoji} {tier_display} {t('risk')}</div>",
                    unsafe_allow_html=True,
                )

                col_nist, col_l25 = st.columns(2)
                with col_nist:
                    st.metric(t("compliance"), f"{pct}%")
                with col_l25:
                    l25 = tool.get("loi25_pct", 100)
                    st.metric(t("loi25_score"), f"{l25}%")
                st.progress(pct / 100)

                assessed = tool["assessed_at"][:10]
                next_rev = tool["next_review_date"]
                st.caption(f"{t('assessed')} {assessed} · {t('review_due')} {next_rev}")

                if st.button(
                    t("btn_view_report"),
                    key=f"view_{tool['assessment_id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_assessment_id = tool["assessment_id"]
                    st.switch_page("pages/2_Report.py")
