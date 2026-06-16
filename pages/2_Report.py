import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_connection
from data.questions import QUESTIONS
from pdf_export import generate_pdf
from sidebar import render_sidebar
from verdict import get_verdict

st.set_page_config(
    page_title="Compliance Report — NIST AI RMF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

render_sidebar()

TIER_BG = {
    "Minimal":      "#27ae60",
    "Limited":      "#f39c12",
    "High":         "#e74c3c",
    "Unacceptable": "#6c3483",
}
TIER_EMOJI = {
    "Minimal":      "🟢",
    "Limited":      "🟡",
    "High":         "🔴",
    "Unacceptable": "⛔",
}
FUNCTION_LABELS = {
    "govern_pct":  "🏛️ GOVERN — Policies & Accountability",
    "map_pct":     "🗺️ MAP — Data & Risk Classification",
    "measure_pct": "📊 MEASURE — Technical Risk Evaluation",
    "manage_pct":  "🛠️ MANAGE — Risk Treatment & Guardrails",
}

# ── Guard: need a selected assessment ─────────────────────────────────────────
assessment_id = st.session_state.get("selected_assessment_id")
if not assessment_id:
    st.warning("No report selected. Please open a report from the dashboard.")
    if st.button("← Back to Dashboard"):
        st.switch_page("app.py")
    st.stop()

# ── Load from DB ──────────────────────────────────────────────────────────────
conn = get_connection()
assessment = dict(conn.execute(
    "SELECT * FROM assessments WHERE id = ?", (assessment_id,)
).fetchone())
tool = dict(conn.execute(
    "SELECT * FROM tools WHERE id = ?", (assessment["tool_id"],)
).fetchone())
responses = [
    dict(r) for r in conn.execute(
        "SELECT * FROM responses WHERE assessment_id = ? ORDER BY question_id",
        (assessment_id,),
    ).fetchall()
]
conn.close()

questions_by_id = {q["id"]: q for q in QUESTIONS}
tier  = assessment["risk_tier"]
color = TIER_BG.get(tier, "#888")
emoji = TIER_EMOJI.get(tier, "")

no_responses = [r for r in responses if r["answer"] == "No"]
no_responses.sort(key=lambda x: x["risk_score"], reverse=True)

# ── Nav bar: back + PDF download ──────────────────────────────────────────────
col_back, col_pdf = st.columns([5, 1])
with col_back:
    source = st.session_state.get("report_source", "dashboard")
    if source == "insights":
        if st.button("← Back to Insights"):
            st.switch_page("pages/3_Insights.py")
    else:
        if st.button("← Back to Dashboard"):
            st.switch_page("app.py")
with col_pdf:
    pdf_bytes = bytes(generate_pdf(assessment, tool, responses, questions_by_id))
    file_name = f"NIST_RMF_{tool['name'].replace(' ', '_')}_{assessment['assessed_at'][:10]}.pdf"
    st.download_button(
        "⬇ Download PDF",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

# ── Report header ─────────────────────────────────────────────────────────────
st.markdown(f"# {tool['name']}")
st.caption(
    f"{tool['vendor']} · {tool['category']} "
    f"| Assessed {assessment['assessed_at'][:10]} by {assessment['assessor_name']} "
    f"| Next review {assessment['next_review_date']}"
)
st.markdown(
    f"<div style='display:inline-block; background:{color}; color:white; "
    f"padding:6px 20px; border-radius:20px; font-size:15px; font-weight:700; "
    f"margin-bottom:16px'>{emoji} {tier} Risk</div>",
    unsafe_allow_html=True,
)

# ── Plain-English verdict ─────────────────────────────────────────────────────
verdict_text = get_verdict(assessment, tool)
st.markdown(
    f"<div style='background:#f8f9fa; border-left:4px solid {color}; "
    f"padding:16px 20px; border-radius:4px; margin-bottom:16px; "
    f"font-size:15px; line-height:1.6; color:#2c3e50'>{verdict_text}</div>",
    unsafe_allow_html=True,
)

# ── Overall score ─────────────────────────────────────────────────────────────
col_pct, col_score, col_spacer = st.columns([1, 1, 3])
with col_pct:
    st.metric("Overall Compliance", f"{assessment['compliance_pct']}%")
    st.progress(assessment["compliance_pct"] / 100)
with col_score:
    st.metric("Risk Score", f"{assessment['total_risk_score']} / {assessment['max_possible_score']}")

st.divider()

# ── NIST function breakdown ───────────────────────────────────────────────────
st.subheader("Compliance by NIST Function")

for col_key, label in FUNCTION_LABELS.items():
    pct = assessment[col_key]
    col_label, col_bar, col_val = st.columns([3, 5, 1])
    with col_label:
        st.markdown(f"**{label}**")
    with col_bar:
        st.progress(pct / 100)
    with col_val:
        st.markdown(f"**{pct}%**")

st.divider()

# ── Top 3 priority actions ────────────────────────────────────────────────────
if no_responses:
    top3 = no_responses[:3]
    st.subheader("⚡ Top 3 Priority Actions")
    st.caption("Fix these first — highest risk, biggest compliance impact.")

    for i, r in enumerate(top3, 1):
        q    = questions_by_id[r["question_id"]]
        risk = r["risk_score"]
        badge_color = "#e74c3c" if risk >= 16 else "#f39c12" if risk >= 9 else "#3498db"

        with st.container(border=True):
            col_num, col_content, col_badge = st.columns([0.15, 8, 1])
            with col_num:
                st.markdown(
                    f"<div style='font-size:28px; font-weight:800; color:{badge_color}; "
                    f"line-height:1'>{i}</div>",
                    unsafe_allow_html=True,
                )
            with col_content:
                st.markdown(f"**{q['text']}**")
                st.markdown(
                    f"<div style='color:#27ae60; font-size:14px; margin-top:4px'>"
                    f"→ {q['fix']}</div>",
                    unsafe_allow_html=True,
                )
            with col_badge:
                st.markdown(
                    f"<div style='background:{badge_color}; color:white; text-align:center; "
                    f"padding:5px 8px; border-radius:8px; font-weight:700; font-size:13px; "
                    f"margin-top:4px'>Risk {risk}</div>",
                    unsafe_allow_html=True,
                )

    st.divider()

# ── Full gap list ─────────────────────────────────────────────────────────────
if not no_responses:
    st.success("🎉 Fully compliant — no gaps found!")
else:
    remaining = no_responses[3:]
    if remaining:
        with st.expander(f"🔧 View all {len(no_responses)} gaps (showing {len(remaining)} additional below top 3)"):
            for i, r in enumerate(remaining, 4):
                q    = questions_by_id[r["question_id"]]
                risk = r["risk_score"]
                badge_color = "#e74c3c" if risk >= 16 else "#f39c12" if risk >= 9 else "#3498db"

                with st.container(border=True):
                    col_q, col_badge = st.columns([9, 1])
                    with col_q:
                        st.markdown(f"**{i}. {q['text']}**")
                    with col_badge:
                        st.markdown(
                            f"<div style='background:{badge_color}; color:white; text-align:center; "
                            f"padding:5px 8px; border-radius:8px; font-weight:700; font-size:13px'>"
                            f"Risk {risk}</div>",
                            unsafe_allow_html=True,
                        )
                    st.info(f"**Why this matters:** {q['why']}")
                    st.markdown(
                        f"<div style='color:#27ae60; font-size:13px; padding:4px 0'>→ {q['fix']}</div>",
                        unsafe_allow_html=True,
                    )
                    refs = q["nist_ref"]
                    if q["owasp_ref"]:
                        refs += f" · {q['owasp_ref']}"
                    st.caption(f"References: {refs}  ·  Risk Score: {risk}")

# ── Compliant controls (collapsible) ─────────────────────────────────────────
yes_responses = [r for r in responses if r["answer"] == "Yes"]
if yes_responses:
    with st.expander(f"✅ {len(yes_responses)} compliant controls"):
        for r in yes_responses:
            q = questions_by_id[r["question_id"]]
            st.markdown(f"✅ **Q{q['id']}.** {q['text']}")
