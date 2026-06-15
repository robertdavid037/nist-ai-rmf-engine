import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.questions import QUESTIONS
from scoring import save_assessment
from sidebar import render_sidebar

st.set_page_config(
    page_title="New Assessment — NIST AI RMF",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

render_sidebar()

if st.button("← Back to Dashboard"):
    st.switch_page("app.py")

st.title("📋 New AI Tool Assessment")
st.caption("Answer all 18 questions to generate a full NIST AI RMF compliance report.")
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
    "Other (enter manually)",
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
    tool_selection = st.selectbox("AI Tool Being Assessed", TOOL_OPTIONS)
with col2:
    assessor_name = st.text_input("Your Name (Assessor)", placeholder="e.g. Jane Smith")

if tool_selection == "Other (enter manually)":
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        custom_name = st.text_input("Tool Name", placeholder="e.g. Notion AI")
    with col_b:
        custom_vendor = st.text_input("Vendor", placeholder="e.g. Notion")
    with col_c:
        custom_category = st.text_input("Category", placeholder="e.g. Productivity")
    tool_name = custom_name
    vendor = custom_vendor
    category = custom_category
else:
    tool_name = tool_selection
    vendor = TOOL_CATALOG[tool_selection]["vendor"]
    category = TOOL_CATALOG[tool_selection]["category"]

st.divider()

# ── Questions ─────────────────────────────────────────────────────────────────
FUNCTION_HEADERS = {
    "GOVERN": "🏛️ GOVERN — Policies & Accountability",
    "MAP":    "🗺️ MAP — Data & Risk Classification",
    "MEASURE":"📊 MEASURE — Technical Risk Evaluation",
    "MANAGE": "🛠️ MANAGE — Risk Treatment & Guardrails",
}

responses = []
current_function = None

for q in QUESTIONS:
    fn = q["function"]
    if fn != current_function:
        current_function = fn
        st.subheader(FUNCTION_HEADERS[fn])

    q_id = q["id"]

    with st.container(border=True):
        st.markdown(f"**Q{q_id}. {q['text']}**")
        ref_str = f"*{q['nist_ref']}"
        if q["owasp_ref"]:
            ref_str += f" · {q['owasp_ref']}"
        ref_str += "*"
        st.caption(ref_str)

        answer = st.radio(
            "Answer",
            ["Yes", "No"],
            key=f"q{q_id}_answer",
            horizontal=True,
            label_visibility="collapsed",
        )

        if answer == "No":
            st.info(f"**Why this matters:** {q['why']}")
            st.metric("Risk Score", q["default_risk"])

    responses.append({
        "question_id": q_id,
        "answer": answer,
    })

# ── Submit bar ────────────────────────────────────────────────────────────────
st.divider()
no_count = sum(1 for r in responses if r["answer"] == "No")
yes_count = len(responses) - no_count

col_submit, col_tally = st.columns([2, 3])
with col_tally:
    st.caption(f"✅ {yes_count} compliant  ·  ⚠️ {no_count} gaps identified")
with col_submit:
    submit = st.button(
        "Generate Compliance Report →",
        type="primary",
        use_container_width=True,
    )

if submit:
    if not tool_name.strip():
        st.error("Please enter the tool name.")
        st.stop()
    if not assessor_name.strip():
        st.error("Please enter your name.")
        st.stop()

    with st.spinner("Calculating scores and saving assessment..."):
        assessment_id = save_assessment(
            tool_name.strip(), vendor, category,
            assessor_name.strip(), responses,
        )

    st.session_state.selected_assessment_id = assessment_id
    st.switch_page("pages/2_Report.py")
