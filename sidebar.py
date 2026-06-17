import streamlit as st
from translations import t, set_lang


def render_sidebar():
    with st.sidebar:
        # Language toggle — French default (Loi 101)
        lang = st.session_state.get("lang", "fr")
        col_fr, col_en = st.columns(2)
        with col_fr:
            if st.button(
                "🇫🇷 Français",
                use_container_width=True,
                type="primary" if lang == "fr" else "secondary",
                key="lang_fr",
            ):
                set_lang("fr")
                st.rerun()
        with col_en:
            if st.button(
                "🇬🇧 English",
                use_container_width=True,
                type="primary" if lang == "en" else "secondary",
                key="lang_en",
            ):
                set_lang("en")
                st.rerun()

        st.markdown("## 🛡️ NIST AI RMF")
        st.caption(t("sidebar_subtitle"))
        st.divider()
        st.page_link("app.py",                   label=t("nav_dashboard"),   icon="🛡️")
        st.page_link("pages/1_Assessment.py",     label=t("nav_assessment"),  icon="📋")
        st.page_link("pages/3_Insights.py",       label=t("nav_insights"),    icon="📈")
