import streamlit as st
import sys
import os
import pandas as pd
import altair as alt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth import require_login
from database.db import init_db, get_connection
from sidebar import render_sidebar
from translations import t

st.set_page_config(
    page_title="Insights — NIST AI RMF",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

init_db()
username = require_login()
render_sidebar()

st.title(t("insights_title"))
st.caption(t("insights_caption"))

# ── Load data (scoped to logged-in user) ──────────────────────────────────────
conn = get_connection()
rows = conn.execute("""
    SELECT t.name AS tool_name, a.id, a.assessor_name, a.assessed_at,
           a.compliance_pct, a.risk_tier, a.next_review_date
    FROM assessments a
    JOIN tools t ON t.id = a.tool_id
    WHERE t.username = ?
    ORDER BY a.assessed_at
""", (username,)).fetchall()
conn.close()

all_data = [dict(r) for r in rows]

if not all_data:
    st.info(t("no_data_insights"))
    st.stop()

df = pd.DataFrame(all_data)
df["date"] = pd.to_datetime(df["assessed_at"].str[:10])

# ── Section 1: Compliance Trend ────────────────────────────────────────────────
st.subheader(t("trend_title"))

# Portfolio average: after each event, mean of the latest score per tool
tool_latest = {}
portfolio_rows = []
for _, row in df.sort_values("date").iterrows():
    tool_latest[row["tool_name"]] = row["compliance_pct"]
    avg = round(sum(tool_latest.values()) / len(tool_latest))
    portfolio_rows.append({"date": row["date"], "compliance_pct": avg})

portfolio_df = (
    pd.DataFrame(portfolio_rows)
    .drop_duplicates(subset=["date"], keep="last")
)

# Individual tool lines — colored, with point markers
tool_lines = (
    alt.Chart(df)
    .mark_line(point=alt.OverlayMarkDef(filled=True, size=60), strokeWidth=2)
    .encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%b %Y")),
        y=alt.Y("compliance_pct:Q", title="Compliance %", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("tool_name:N", title="Tool"),
        tooltip=[
            alt.Tooltip("tool_name:N", title="Tool"),
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("compliance_pct:Q", title="Compliance %"),
            alt.Tooltip("risk_tier:N", title="Risk Tier"),
        ],
    )
)

# Portfolio average — thick dark line
portfolio_line = (
    alt.Chart(portfolio_df)
    .mark_line(
        strokeWidth=4,
        color="#1a252f",
        point=alt.OverlayMarkDef(color="#1a252f", filled=True, size=80),
    )
    .encode(
        x=alt.X("date:T"),
        y=alt.Y("compliance_pct:Q"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("compliance_pct:Q", title="Portfolio Average"),
        ],
    )
)

st.altair_chart((tool_lines + portfolio_line).properties(height=350), use_container_width=True)
st.caption(t("chart_caption"))

st.divider()

# ── Section 2: Audit Log ───────────────────────────────────────────────────────
st.subheader(t("audit_log_title"))

TIER_BG = {
    "Minimal":      "#27ae60",
    "Limited":      "#f39c12",
    "High":         "#e74c3c",
    "Unacceptable": "#6c3483",
}

tool_names = sorted(set(r["tool_name"] for r in all_data))
selected_tool = st.selectbox(
    "Filter", [t("filter_all")] + tool_names, label_visibility="collapsed"
)

filter_label = t("filter_all")
filtered = (
    all_data if selected_tool == filter_label
    else [r for r in all_data if r["tool_name"] == selected_tool]
)
filtered = sorted(filtered, key=lambda x: x["assessed_at"], reverse=True)

COL_W = [2, 1.5, 1.5, 1, 1.5, 1.5, 1]

# Header row
hcols = st.columns(COL_W)
for col, label in zip(hcols, [
    t("col_tool"), t("col_date"), t("col_assessor"),
    t("col_compliance"), t("col_risk_tier"), t("col_next_review"), "",
]):
    col.markdown(label)

st.divider()

for row in filtered:
    tier  = row["risk_tier"]
    color = TIER_BG.get(tier, "#888")
    tier_display = t(f"tier_{tier}")
    cols  = st.columns(COL_W)
    cols[0].write(row["tool_name"])
    cols[1].write(row["assessed_at"][:10])
    cols[2].write(row["assessor_name"])
    cols[3].write(f"{row['compliance_pct']}%")
    cols[4].markdown(
        f"<span style='background:{color}; color:white; padding:2px 10px; "
        f"border-radius:10px; font-size:12px; font-weight:600'>{tier_display}</span>",
        unsafe_allow_html=True,
    )
    cols[5].write(row["next_review_date"])
    if cols[6].button(t("btn_view"), key=f"ins_{row['id']}"):
        st.session_state.selected_assessment_id = row["id"]
        st.session_state.report_source = "insights"
        st.switch_page("pages/2_Report.py")
