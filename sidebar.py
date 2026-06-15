import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🛡️ NIST AI RMF")
        st.caption("AI Risk Management Framework 1.0")
        st.divider()
        st.page_link("app.py",                   label="Dashboard",       icon="🛡️")
        st.page_link("pages/1_Assessment.py",     label="New Assessment",  icon="📋")
        st.page_link("pages/3_Insights.py",       label="Insights",        icon="📈")
