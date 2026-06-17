import streamlit as st

TRANSLATIONS = {
    "fr": {
        # Sidebar
        "sidebar_subtitle":     "Cadre de gestion des risques IA NIST 1.0",
        "nav_dashboard":        "Tableau de bord",
        "nav_assessment":       "Nouvelle évaluation",
        "nav_insights":         "Analyses",

        # Dashboard
        "dashboard_title":      "Tableau de bord de posture IA",
        "btn_new_assessment":   "＋ Nouvelle évaluation",
        "sort_by":              "Trier par :",
        "sort_risk":            "Risque (plus élevé en premier)",
        "sort_compliance":      "Conformité (plus élevé en premier)",
        "sort_date":            "Date (plus récent en premier)",
        "no_assessments":       "Aucune évaluation pour l'instant. Cliquez sur **＋ Nouvelle évaluation** pour commencer.",
        "tools_assessed":       "outil(s) évalué(s)",
        "compliance":           "Conformité",
        "assessed":             "Évalué le",
        "review_due":           "Révision prévue le",
        "btn_view_report":      "Voir le rapport complet →",

        # Risk tiers (display)
        "tier_Minimal":         "Minimal",
        "tier_Limited":         "Limité",
        "tier_High":            "Élevé",
        "tier_Unacceptable":    "Inacceptable",
        "risk":                 "Risque",

        # NIST function labels
        "fn_govern":            "🏛️ GOVERN — Politiques & responsabilisation",
        "fn_map":               "🗺️ MAP — Classification des données & risques",
        "fn_measure":           "📊 MEASURE — Évaluation technique des risques",
        "fn_manage":            "🛠️ MANAGE — Traitement des risques & garde-fous",

        # Assessment form
        "assessment_title":     "📋 Nouvelle évaluation d'outil IA",
        "assessment_caption":   "Répondez aux 18 questions pour générer un rapport complet de conformité NIST AI RMF.",
        "btn_back_dashboard":   "← Retour au tableau de bord",
        "tool_being_assessed":  "Outil IA évalué",
        "assessor_name":        "Votre nom (évaluateur)",
        "assessor_placeholder": "ex. : Marie Tremblay",
        "other_tool":           "Autre (saisir manuellement)",
        "tool_name_label":      "Nom de l'outil",
        "vendor_label":         "Fournisseur",
        "category_label":       "Catégorie",
        "tool_name_ph":         "ex. : Notion IA",
        "vendor_ph":            "ex. : Notion",
        "category_ph":          "ex. : Productivité",
        "answer_yes":           "Oui",
        "answer_no":            "Non",
        "why_matters":          "Pourquoi c'est important :",
        "risk_score":           "Score de risque",
        "compliant_count":      "conforme(s)",
        "gaps_count":           "lacune(s) identifiée(s)",
        "btn_generate":         "Générer le rapport de conformité →",
        "err_tool_name":        "Veuillez entrer le nom de l'outil.",
        "err_assessor":         "Veuillez entrer votre nom.",
        "spinner_saving":       "Calcul des scores et sauvegarde de l'évaluation...",

        # Report page
        "btn_back_insights":    "← Retour aux analyses",
        "btn_download_pdf":     "⬇ Télécharger le PDF",
        "no_report_warning":    "Aucun rapport sélectionné. Veuillez ouvrir un rapport depuis le tableau de bord.",
        "overall_compliance":   "Conformité globale",
        "risk_score_label":     "Score de risque",
        "compliance_by_fn":     "Conformité par fonction NIST",
        "top3_title":           "⚡ 3 actions prioritaires",
        "top3_caption":         "Résolvez ces points en priorité — risque le plus élevé, impact maximal sur la conformité.",
        "why_matters_bold":     "**Pourquoi c'est important :** ",
        "references":           "Références :",
        "risk_score_ref":       "Score de risque :",
        "fully_compliant":      "🎉 Pleinement conforme — aucune lacune détectée !",
        "compliant_controls":   "contrôle(s) conforme(s)",

        # Insights page
        "insights_title":       "📈 Analyses",
        "insights_caption":     "Tendances de conformité et historique complet des évaluations de tous les outils IA.",
        "no_data_insights":     "Aucune évaluation pour l'instant. Effectuez votre première évaluation pour voir les analyses ici.",
        "trend_title":          "Tendance de conformité",
        "chart_caption":        "Lignes colorées = outils individuels  ·  Ligne sombre épaisse = moyenne du portefeuille",
        "audit_log_title":      "Journal d'audit des évaluations",
        "filter_all":           "Tous les outils",
        "col_tool":             "**Outil**",
        "col_date":             "**Date**",
        "col_assessor":         "**Évaluateur**",
        "col_compliance":       "**Conformité**",
        "col_risk_tier":        "**Niveau de risque**",
        "col_next_review":      "**Prochaine révision**",
        "btn_view":             "Voir →",

        # Loi 25 section
        "loi25_section":        "🔒 Loi 25 — Protection des renseignements personnels (Québec)",
        "loi25_score":          "Score Loi 25",
        "loi25_compliance":     "Conformité Loi 25",
        "loi25_ref_label":      "Réf. Loi 25 :",
        "loi25_gaps_title":     "Lacunes Loi 25",
        "loi25_compliant":      "🎉 Pleinement conforme à la Loi 25 — aucune lacune détectée !",
        "loi25_disclaimer":     "Ce rapport fournit une orientation basée sur les exigences publiques de la Loi 25. Consultez un avocat spécialisé en protection de la vie privée pour un avis juridique.",
        "pdf_loi25_title":      "Conformite - Loi 25 du Quebec",
        "pdf_loi25_disclaimer": "Orientation basee sur les exigences publiques de la Loi 25. Consultez un avocat specialise pour un avis juridique.",

        # PDF strings
        "pdf_title":            "Rapport de conformité NIST AI RMF",
        "pdf_confidential":     "CONFIDENTIEL  |  Généré le",
        "pdf_assessor":         "Évaluateur :",
        "pdf_date":             "Date :",
        "pdf_next_review_lbl":  "Prochaine révision :",
        "pdf_exec_summary":     "Résumé exécutif",
        "pdf_compliance_fn":    "Conformité par fonction NIST",
        "pdf_top3":             "3 actions prioritaires",
        "pdf_top3_sub":         "Résolvez ces points en priorité - risque le plus élevé, impact maximal.",
        "pdf_full_gaps":        "Analyse complète des lacunes",
        "pdf_no_gaps":          "Aucune lacune détectée - pleinement conforme !",
        "pdf_risk_label":       "Score de risque :",
        "pdf_footer":           "Généré par le Moteur de conformité NIST AI RMF  |  Confidentiel",
    },

    "en": {
        # Sidebar
        "sidebar_subtitle":     "AI Risk Management Framework 1.0",
        "nav_dashboard":        "Dashboard",
        "nav_assessment":       "New Assessment",
        "nav_insights":         "Insights",

        # Dashboard
        "dashboard_title":      "AI Security Posture Dashboard",
        "btn_new_assessment":   "＋ New Assessment",
        "sort_by":              "Sort by:",
        "sort_risk":            "Risk (Highest First)",
        "sort_compliance":      "Compliance (Highest First)",
        "sort_date":            "Date (Most Recent)",
        "no_assessments":       "No assessments yet. Click **＋ New Assessment** to get started.",
        "tools_assessed":       "tool(s) assessed",
        "compliance":           "Compliance",
        "assessed":             "Assessed",
        "review_due":           "Review due",
        "btn_view_report":      "View Full Report →",

        # Risk tiers (display)
        "tier_Minimal":         "Minimal",
        "tier_Limited":         "Limited",
        "tier_High":            "High",
        "tier_Unacceptable":    "Unacceptable",
        "risk":                 "Risk",

        # NIST function labels
        "fn_govern":            "🏛️ GOVERN — Policies & Accountability",
        "fn_map":               "🗺️ MAP — Data & Risk Classification",
        "fn_measure":           "📊 MEASURE — Technical Risk Evaluation",
        "fn_manage":            "🛠️ MANAGE — Risk Treatment & Guardrails",

        # Assessment form
        "assessment_title":     "📋 New AI Tool Assessment",
        "assessment_caption":   "Answer all 18 questions to generate a full NIST AI RMF compliance report.",
        "btn_back_dashboard":   "← Back to Dashboard",
        "tool_being_assessed":  "AI Tool Being Assessed",
        "assessor_name":        "Your Name (Assessor)",
        "assessor_placeholder": "e.g. Jane Smith",
        "other_tool":           "Other (enter manually)",
        "tool_name_label":      "Tool Name",
        "vendor_label":         "Vendor",
        "category_label":       "Category",
        "tool_name_ph":         "e.g. Notion AI",
        "vendor_ph":            "e.g. Notion",
        "category_ph":          "e.g. Productivity",
        "answer_yes":           "Yes",
        "answer_no":            "No",
        "why_matters":          "Why this matters:",
        "risk_score":           "Risk Score",
        "compliant_count":      "compliant",
        "gaps_count":           "gaps identified",
        "btn_generate":         "Generate Compliance Report →",
        "err_tool_name":        "Please enter the tool name.",
        "err_assessor":         "Please enter your name.",
        "spinner_saving":       "Calculating scores and saving assessment...",

        # Report page
        "btn_back_insights":    "← Back to Insights",
        "btn_download_pdf":     "⬇ Download PDF",
        "no_report_warning":    "No report selected. Please open a report from the dashboard.",
        "overall_compliance":   "Overall Compliance",
        "risk_score_label":     "Risk Score",
        "compliance_by_fn":     "Compliance by NIST Function",
        "top3_title":           "⚡ Top 3 Priority Actions",
        "top3_caption":         "Fix these first — highest risk, biggest compliance impact.",
        "why_matters_bold":     "**Why this matters:** ",
        "references":           "References:",
        "risk_score_ref":       "Risk Score:",
        "fully_compliant":      "🎉 Fully compliant — no gaps found!",
        "compliant_controls":   "compliant controls",

        # Insights page
        "insights_title":       "📈 Insights",
        "insights_caption":     "Compliance trends and full assessment history across all AI tools.",
        "no_data_insights":     "No assessments yet. Run your first assessment to see insights here.",
        "trend_title":          "Compliance Trend",
        "chart_caption":        "Colored lines = individual tools  ·  Dark thick line = portfolio average",
        "audit_log_title":      "Assessment Audit Log",
        "filter_all":           "All Tools",
        "col_tool":             "**Tool**",
        "col_date":             "**Date**",
        "col_assessor":         "**Assessor**",
        "col_compliance":       "**Compliance**",
        "col_risk_tier":        "**Risk Tier**",
        "col_next_review":      "**Next Review**",
        "btn_view":             "View →",

        # Loi 25 section
        "loi25_section":        "🔒 Law 25 — Personal Information Protection (Quebec)",
        "loi25_score":          "Law 25 Score",
        "loi25_compliance":     "Law 25 Compliance",
        "loi25_ref_label":      "Law 25 Ref.:",
        "loi25_gaps_title":     "Law 25 Gaps",
        "loi25_compliant":      "🎉 Fully compliant with Law 25 — no gaps found!",
        "loi25_disclaimer":     "This report provides guidance based on publicly available Law 25 requirements. Consult a Quebec privacy lawyer for legal advice.",
        "pdf_loi25_title":      "Compliance - Quebec Law 25",
        "pdf_loi25_disclaimer": "Guidance based on publicly available Law 25 requirements. Consult a privacy lawyer for legal advice.",

        # PDF strings
        "pdf_title":            "NIST AI RMF Compliance Report",
        "pdf_confidential":     "CONFIDENTIAL  |  Generated",
        "pdf_assessor":         "Assessor:",
        "pdf_date":             "Date:",
        "pdf_next_review_lbl":  "Next Review:",
        "pdf_exec_summary":     "Executive Summary",
        "pdf_compliance_fn":    "Compliance by NIST Function",
        "pdf_top3":             "Top 3 Priority Actions",
        "pdf_top3_sub":         "Fix these first - highest risk, biggest compliance impact.",
        "pdf_full_gaps":        "Full Gap Analysis",
        "pdf_no_gaps":          "No gaps found - fully compliant!",
        "pdf_risk_label":       "Risk Score:",
        "pdf_footer":           "Generated by NIST AI RMF Compliance Engine  |  Confidential",
    },
}


def t(key):
    """Return the translated string for the current session language."""
    lang = st.session_state.get("lang", "fr")
    return TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))


def set_lang(new_lang):
    """Switch language and clear assessment radio state to avoid widget conflicts."""
    keys_to_clear = [k for k in st.session_state if "_answer" in k]
    for k in keys_to_clear:
        del st.session_state[k]
    st.session_state.lang = new_lang


def qt(question, field, lang=None):
    """Return translated question field (text / why / fix). Falls back to English."""
    if lang is None:
        lang = st.session_state.get("lang", "fr")
    fr_field = field + "_fr"
    if lang == "fr" and fr_field in question and question[fr_field]:
        return question[fr_field]
    return question.get(field, "")
