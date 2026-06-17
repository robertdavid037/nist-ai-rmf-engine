import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.questions import QUESTIONS
from scoring import save_assessment
from sidebar import render_sidebar
from translations import t, qt

st.set_page_config(
    page_title="New Assessment — NIST AI RMF",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

render_sidebar()

lang = st.session_state.get("lang", "fr")

if st.button(t("btn_back_dashboard")):
    st.switch_page("app.py")

st.title(t("assessment_title"))
st.caption(t("assessment_caption"))
st.divider()

# ── Tool + assessor info ──────────────────────────────────────────────────────
TOOL_OPTIONS = [
    "ChatGPT",
    "ChatGPT Team",
    "Microsoft Copilot",
    "Google Workspace AI (Gemini)",
    "GitHub Copilot",
    "HubSpot AI",
    "Salesforce Einstein",
    "Zapier AI",
    "Make AI",
    t("other_tool"),
]

TOOL_CATALOG = {
    "ChatGPT":                        {"vendor": "OpenAI",             "category": "Productivity"},
    "ChatGPT Team":                   {"vendor": "OpenAI",             "category": "Productivity"},
    "Microsoft Copilot":              {"vendor": "Microsoft",          "category": "Productivity"},
    "Google Workspace AI (Gemini)":   {"vendor": "Google",             "category": "Productivity"},
    "GitHub Copilot":                 {"vendor": "GitHub / Microsoft", "category": "Code"},
    "HubSpot AI":                     {"vendor": "HubSpot",            "category": "CRM"},
    "Salesforce Einstein":            {"vendor": "Salesforce",         "category": "CRM"},
    "Zapier AI":                      {"vendor": "Zapier",             "category": "Automation"},
    "Make AI":                        {"vendor": "Make",               "category": "Automation"},
}

col1, col2 = st.columns(2)
with col1:
    tool_selection = st.selectbox(t("tool_being_assessed"), TOOL_OPTIONS)
with col2:
    assessor_name = st.text_input(
        t("assessor_name"),
        placeholder=t("assessor_placeholder"),
    )

other_label = t("other_tool")
if tool_selection == other_label:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        custom_name = st.text_input(t("tool_name_label"), placeholder=t("tool_name_ph"))
    with col_b:
        custom_vendor = st.text_input(t("vendor_label"), placeholder=t("vendor_ph"))
    with col_c:
        custom_category = st.text_input(t("category_label"), placeholder=t("category_ph"))
    tool_name = custom_name
    vendor    = custom_vendor
    category  = custom_category
else:
    tool_name = tool_selection
    vendor    = TOOL_CATALOG[tool_selection]["vendor"]
    category  = TOOL_CATALOG[tool_selection]["category"]

st.divider()

# ── Questions ─────────────────────────────────────────────────────────────────
FUNCTION_HEADERS = {
    "GOVERN": t("fn_govern"),
    "MAP":    t("fn_map"),
    "MEASURE":t("fn_measure"),
    "MANAGE": t("fn_manage"),
}

yes_label = t("answer_yes")
no_label  = t("answer_no")

responses = []
current_function = None

for q in QUESTIONS:
    fn = q["function"]
    if fn != current_function:
        current_function = fn
        st.subheader(FUNCTION_HEADERS[fn])

    q_id     = q["id"]
    q_text   = qt(q, "text", lang)
    q_why    = qt(q, "why",  lang)

    with st.container(border=True):
        st.markdown(f"**Q{q_id}. {q_text}**")
        ref_str = f"*{q['nist_ref']}"
        if q["owasp_ref"]:
            ref_str += f" · {q['owasp_ref']}"
        ref_str += "*"
        st.caption(ref_str)

        answer_label = st.radio(
            "Answer",
            [yes_label, no_label],
            key=f"q{q_id}_answer",
            horizontal=True,
            label_visibility="collapsed",
        )
        answer = "Yes" if answer_label == yes_label else "No"

        if answer == "No":
            st.info(f"{t('why_matters')} {q_why}")
            st.metric(t("risk_score"), q["default_risk"])

    responses.append({
        "question_id": q_id,
        "answer": answer,
    })

# ── Submit bar ────────────────────────────────────────────────────────────────
st.divider()
no_count  = sum(1 for r in responses if r["answer"] == "No")
yes_count = len(responses) - no_count

col_submit, col_tally = st.columns([2, 3])
with col_tally:
    st.caption(f"✅ {yes_count} {t('compliant_count')}  ·  ⚠️ {no_count} {t('gaps_count')}")
with col_submit:
    submit = st.button(
        t("btn_generate"),
        type="primary",
        use_container_width=True,
    )

if submit:
    if not tool_name.strip():
        st.error(t("err_tool_name"))
        st.stop()
    if not assessor_name.strip():
        st.error(t("err_assessor"))
        st.stop()

    with st.spinner(t("spinner_saving")):
        assessment_id = save_assessment(
            tool_name.strip(), vendor, category,
            assessor_name.strip(), responses,
        )

    st.session_state.selected_assessment_id = assessment_id
    st.switch_page("pages/2_Report.py")
