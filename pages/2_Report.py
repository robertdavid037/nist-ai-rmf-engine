import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth import require_login
from database.db import init_db, get_connection, update_response_status
from data.questions import QUESTIONS
from pdf_export import generate_pdf
from doc_generator import generate_doc
from scoring import live_scores
from sidebar import render_sidebar
from verdict import get_verdict
from translations import t, qt

st.set_page_config(
    page_title="Compliance Report — NIST AI RMF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

init_db()
username = require_login()
render_sidebar()

lang = st.session_state.get("lang", "fr")

STATUS_KEYS = ["open", "in_progress", "resolved"]


def _save_status(resp_id):
    new_status = st.session_state[f"status_{resp_id}"]
    update_response_status(resp_id, new_status)


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

# ── Guard: need a selected assessment ─────────────────────────────────────────
assessment_id = st.session_state.get("selected_assessment_id")
if not assessment_id:
    st.warning(t("no_report_warning"))
    if st.button(t("btn_back_dashboard")):
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

# Ownership guard — prevent accessing another user's reports via direct ID
if tool.get("username", "") not in ("", username):
    st.error("⛔ Accès refusé — ce rapport ne vous appartient pas.")
    st.stop()

questions_by_id = {q["id"]: q for q in QUESTIONS}
tier  = assessment["risk_tier"]
color = TIER_BG.get(tier, "#888")
emoji = TIER_EMOJI.get(tier, "")

nist_ids   = [q["id"] for q in QUESTIONS if q.get("framework", "NIST") == "NIST"]
loi25_ids  = [q["id"] for q in QUESTIONS if q.get("framework") == "LOI25"]

no_responses       = [r for r in responses if r["answer"] == "No" and r["question_id"] in nist_ids]
no_responses.sort(key=lambda x: x["risk_score"], reverse=True)
loi25_no_responses = [r for r in responses if r["answer"] == "No" and r["question_id"] in loi25_ids]
loi25_no_responses.sort(key=lambda x: x["risk_score"], reverse=True)

# ── Nav bar: back + PDF download ──────────────────────────────────────────────
col_back, col_pdf = st.columns([5, 1])
with col_back:
    source = st.session_state.get("report_source", "dashboard")
    if source == "insights":
        if st.button(t("btn_back_insights")):
            st.switch_page("pages/3_Insights.py")
    else:
        if st.button(t("btn_back_dashboard")):
            st.switch_page("app.py")
with col_pdf:
    pdf_bytes = bytes(generate_pdf(assessment, tool, responses, questions_by_id, lang=lang))
    file_name = f"NIST_RMF_{tool['name'].replace(' ', '_')}_{assessment['assessed_at'][:10]}.pdf"
    st.download_button(
        t("btn_download_pdf"),
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

# ── Policy document downloads ─────────────────────────────────────────────────
with st.expander(t("docs_section_label"), expanded=False):
    org_name = st.text_input(
        t("docs_org_name_label"),
        placeholder=t("docs_org_name_ph"),
        key="doc_org_name",
    )

    doc_col1, doc_col2, doc_col3 = st.columns(3)

    with doc_col1:
        aup_text = generate_doc(
            "acceptable_use", assessment, tool, responses, questions_by_id,
            lang=lang, org_name=org_name or None,
        )
        aup_fname = f"Politique_UtilisationAcceptable_{tool['name'].replace(' ', '_')}_{assessment['assessed_at'][:10]}.txt"
        st.download_button(
            t("btn_doc_aup"),
            data=aup_text.encode("utf-8"),
            file_name=aup_fname,
            mime="text/plain",
            use_container_width=True,
        )

    with doc_col2:
        adn_text = generate_doc(
            "automated_decision", assessment, tool, responses, questions_by_id,
            lang=lang, org_name=org_name or None,
        )
        adn_fname = f"Avis_DecisionAutomatisee_{tool['name'].replace(' ', '_')}_{assessment['assessed_at'][:10]}.txt"
        st.download_button(
            t("btn_doc_adn"),
            data=adn_text.encode("utf-8"),
            file_name=adn_fname,
            mime="text/plain",
            use_container_width=True,
        )

    with doc_col3:
        vrs_text = generate_doc(
            "vendor_risk", assessment, tool, responses, questions_by_id,
            lang=lang, org_name=org_name or None,
        )
        vrs_fname = f"SommaireRisque_{tool['name'].replace(' ', '_')}_{assessment['assessed_at'][:10]}.txt"
        st.download_button(
            t("btn_doc_vrs"),
            data=vrs_text.encode("utf-8"),
            file_name=vrs_fname,
            mime="text/plain",
            use_container_width=True,
        )

# ── Report header ─────────────────────────────────────────────────────────────
st.markdown(f"# {tool['name']}")
st.caption(
    f"{tool['vendor']} · {tool['category']} "
    f"| {t('assessed')} {assessment['assessed_at'][:10]} · {assessment['assessor_name']} "
    f"| {t('review_due')} {assessment['next_review_date']}"
)
tier_display = t(f"tier_{tier}")
st.markdown(
    f"<div style='display:inline-block; background:{color}; color:white; "
    f"padding:6px 20px; border-radius:20px; font-size:15px; font-weight:700; "
    f"margin-bottom:16px'>{emoji} {tier_display} {t('risk')}</div>",
    unsafe_allow_html=True,
)

# ── Plain-English verdict ─────────────────────────────────────────────────────
verdict_text = get_verdict(assessment, tool, lang=lang)
st.markdown(
    f"<div style='background:#f8f9fa; border-left:4px solid {color}; "
    f"padding:16px 20px; border-radius:4px; margin-bottom:16px; "
    f"font-size:15px; line-height:1.6; color:#2c3e50'>{verdict_text}</div>",
    unsafe_allow_html=True,
)

# ── Overall score ─────────────────────────────────────────────────────────────
current = live_scores(responses)
live_pct = current["compliance_pct"]
original_pct = assessment["compliance_pct"]
delta = live_pct - original_pct

col_orig, col_live, col_score, col_spacer = st.columns([1, 1, 1, 2])
with col_orig:
    st.metric(t("original_score_label"), f"{original_pct}%")
    st.progress(original_pct / 100)
with col_live:
    st.metric(
        t("live_score_label"),
        f"{live_pct}%",
        delta=f"+{delta}%" if delta > 0 else (f"{delta}%" if delta < 0 else None),
    )
    st.progress(live_pct / 100)
with col_score:
    st.metric(t("risk_score_label"), f"{assessment['total_risk_score']} / {assessment['max_possible_score']}")

st.divider()

# ── NIST function breakdown ───────────────────────────────────────────────────
st.subheader(t("compliance_by_fn"))

FUNCTION_LABELS = {
    "govern_pct":  t("fn_govern"),
    "map_pct":     t("fn_map"),
    "measure_pct": t("fn_measure"),
    "manage_pct":  t("fn_manage"),
}

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
    st.subheader(t("top3_title"))
    st.caption(t("top3_caption"))

    for i, r in enumerate(top3, 1):
        q    = questions_by_id[r["question_id"]]
        risk = r["risk_score"]
        badge_color = "#e74c3c" if risk >= 16 else "#f39c12" if risk >= 9 else "#3498db"
        resp_status = r.get("status", "open")

        with st.container(border=True):
            col_num, col_content, col_badge = st.columns([0.15, 8, 1])
            with col_num:
                st.markdown(
                    f"<div style='font-size:28px; font-weight:800; color:{badge_color}; "
                    f"line-height:1'>{i}</div>",
                    unsafe_allow_html=True,
                )
            with col_content:
                st.markdown(f"**{qt(q, 'text', lang)}**")
                st.markdown(
                    f"<div style='color:#27ae60; font-size:14px; margin-top:4px'>"
                    f"→ {qt(q, 'fix', lang)}</div>",
                    unsafe_allow_html=True,
                )
            with col_badge:
                st.markdown(
                    f"<div style='background:{badge_color}; color:white; text-align:center; "
                    f"padding:5px 8px; border-radius:8px; font-weight:700; font-size:13px; "
                    f"margin-top:4px'>{t('risk')} {risk}</div>",
                    unsafe_allow_html=True,
                )

            col_status, col_notes = st.columns([1, 3])
            with col_status:
                status_idx = STATUS_KEYS.index(resp_status) if resp_status in STATUS_KEYS else 0
                st.selectbox(
                    t("status_label"),
                    STATUS_KEYS,
                    index=status_idx,
                    format_func=lambda s: {
                        "open": t("status_open"),
                        "in_progress": t("status_in_progress"),
                        "resolved": t("status_resolved"),
                    }[s],
                    key=f"status_{r['id']}",
                    on_change=_save_status,
                    args=(r["id"],),
                )
            with col_notes:
                notes_key = f"notes_{r['id']}"
                notes_val = st.text_area(
                    t("notes_label"),
                    value=r.get("notes", "") or "",
                    height=80,
                    placeholder=t("notes_ph"),
                    key=notes_key,
                    label_visibility="collapsed",
                )
                if st.button(t("btn_save_notes"), key=f"savenotes_{r['id']}"):
                    update_response_status(r["id"], st.session_state.get(f"status_{r['id']}", resp_status), notes_val)
                    st.toast("✓ Saved" if lang == "en" else "✓ Sauvegardé")

    st.divider()

# ── Full gap list ─────────────────────────────────────────────────────────────
if not no_responses:
    st.success(t("fully_compliant"))
else:
    remaining = no_responses[3:]
    if remaining:
        total = len(no_responses)
        with st.expander(
            f"🔧 {total} gaps — {len(remaining)} additional" if lang == "en"
            else f"🔧 {total} lacunes — {len(remaining)} supplémentaires"
        ):
            for i, r in enumerate(remaining, 4):
                q    = questions_by_id[r["question_id"]]
                risk = r["risk_score"]
                badge_color = "#e74c3c" if risk >= 16 else "#f39c12" if risk >= 9 else "#3498db"
                resp_status = r.get("status", "open")

                with st.container(border=True):
                    col_q, col_badge = st.columns([9, 1])
                    with col_q:
                        st.markdown(f"**{i}. {qt(q, 'text', lang)}**")
                    with col_badge:
                        st.markdown(
                            f"<div style='background:{badge_color}; color:white; text-align:center; "
                            f"padding:5px 8px; border-radius:8px; font-weight:700; font-size:13px'>"
                            f"{t('risk')} {risk}</div>",
                            unsafe_allow_html=True,
                        )
                    st.info(f"{t('why_matters_bold')}{qt(q, 'why', lang)}")
                    st.markdown(
                        f"<div style='color:#27ae60; font-size:13px; padding:4px 0'>"
                        f"→ {qt(q, 'fix', lang)}</div>",
                        unsafe_allow_html=True,
                    )
                    refs = q["nist_ref"]
                    if q["owasp_ref"]:
                        refs += f" · {q['owasp_ref']}"
                    st.caption(f"{t('references')} {refs}  ·  {t('risk_score_ref')} {risk}")

                    col_status, col_notes = st.columns([1, 3])
                    with col_status:
                        status_idx = STATUS_KEYS.index(resp_status) if resp_status in STATUS_KEYS else 0
                        st.selectbox(
                            t("status_label"),
                            STATUS_KEYS,
                            index=status_idx,
                            format_func=lambda s: {
                                "open": t("status_open"),
                                "in_progress": t("status_in_progress"),
                                "resolved": t("status_resolved"),
                            }[s],
                            key=f"status_{r['id']}",
                            on_change=_save_status,
                            args=(r["id"],),
                        )
                    with col_notes:
                        notes_key = f"notes_{r['id']}"
                        notes_val = st.text_area(
                            t("notes_label"),
                            value=r.get("notes", "") or "",
                            height=80,
                            placeholder=t("notes_ph"),
                            key=notes_key,
                            label_visibility="collapsed",
                        )
                        if st.button(t("btn_save_notes"), key=f"savenotes_{r['id']}"):
                            update_response_status(r["id"], st.session_state.get(f"status_{r['id']}", resp_status), notes_val)
                            st.toast("✓ Saved" if lang == "en" else "✓ Sauvegardé")

# ── Loi 25 section ───────────────────────────────────────────────────────────
st.divider()
st.subheader(t("loi25_section"))

loi25_pct   = assessment.get("loi25_pct", 100)
loi25_color = "#27ae60" if loi25_pct >= 80 else "#f39c12" if loi25_pct >= 60 else "#e74c3c" if loi25_pct >= 40 else "#6c3483"

col_l25, col_l25_bar, col_l25_val = st.columns([2, 5, 1])
with col_l25:
    st.metric(t("loi25_score"), f"{loi25_pct}%")
with col_l25_bar:
    st.write("")
    st.progress(loi25_pct / 100)
with col_l25_val:
    st.write("")

st.caption(t("loi25_disclaimer"))

if not loi25_no_responses:
    st.success(t("loi25_compliant"))
else:
    for i, r in enumerate(loi25_no_responses, 1):
        q    = questions_by_id[r["question_id"]]
        risk = r["risk_score"]
        badge_color = "#e74c3c" if risk >= 16 else "#f39c12" if risk >= 9 else "#3498db"
        resp_status = r.get("status", "open")

        with st.container(border=True):
            col_q, col_badge = st.columns([9, 1])
            with col_q:
                st.markdown(f"**{i}. {qt(q, 'text', lang)}**")
                st.caption(f"{t('loi25_ref_label')} {q.get('loi25_ref', q['nist_ref'])}")
            with col_badge:
                st.markdown(
                    f"<div style='background:{badge_color}; color:white; text-align:center; "
                    f"padding:5px 8px; border-radius:8px; font-weight:700; font-size:13px'>"
                    f"{t('risk')} {risk}</div>",
                    unsafe_allow_html=True,
                )
            st.info(f"{t('why_matters_bold')}{qt(q, 'why', lang)}")
            st.markdown(
                f"<div style='color:#27ae60; font-size:13px; padding:4px 0'>"
                f"→ {qt(q, 'fix', lang)}</div>",
                unsafe_allow_html=True,
            )
            col_status, col_notes = st.columns([1, 3])
            with col_status:
                status_idx = STATUS_KEYS.index(resp_status) if resp_status in STATUS_KEYS else 0
                st.selectbox(
                    t("status_label"),
                    STATUS_KEYS,
                    index=status_idx,
                    format_func=lambda s: {
                        "open": t("status_open"),
                        "in_progress": t("status_in_progress"),
                        "resolved": t("status_resolved"),
                    }[s],
                    key=f"status_{r['id']}",
                    on_change=_save_status,
                    args=(r["id"],),
                )
            with col_notes:
                notes_key = f"notes_{r['id']}"
                notes_val = st.text_area(
                    t("notes_label"),
                    value=r.get("notes", "") or "",
                    height=80,
                    placeholder=t("notes_ph"),
                    key=notes_key,
                    label_visibility="collapsed",
                )
                if st.button(t("btn_save_notes"), key=f"savenotes_{r['id']}"):
                    update_response_status(r["id"], st.session_state.get(f"status_{r['id']}", resp_status), notes_val)
                    st.toast("✓ Saved" if lang == "en" else "✓ Sauvegardé")

# ── Compliant controls (collapsible) ─────────────────────────────────────────
yes_responses = [r for r in responses if r["answer"] == "Yes"]
if yes_responses:
    label = (
        f"✅ {len(yes_responses)} {t('compliant_controls')}"
    )
    with st.expander(label):
        for r in yes_responses:
            q = questions_by_id[r["question_id"]]
            st.markdown(f"✅ **Q{q['id']}.** {qt(q, 'text', lang)}")
