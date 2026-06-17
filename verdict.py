FUNCTION_PLAIN = {
    "en": {
        "govern_pct":  "governance and policy",
        "map_pct":     "data classification and access controls",
        "measure_pct": "technical risk controls",
        "manage_pct":  "risk management and guardrails",
    },
    "fr": {
        "govern_pct":  "gouvernance et politiques",
        "map_pct":     "classification des données et contrôles d'accès",
        "measure_pct": "contrôles techniques des risques",
        "manage_pct":  "gestion des risques et garde-fous",
    },
}

VERDICTS = {
    "en": {
        "Minimal": (
            "{tool} is well-governed and operating within acceptable risk boundaries. "
            "With a compliance score of {pct}%, the majority of AI risk controls are in place. "
            "The remaining gaps are low-priority and can be addressed through routine maintenance. "
            "No immediate action is required."
        ),
        "Limited": (
            "{tool} is partially compliant but has notable gaps that need attention. "
            "At {pct}% compliance, controls are missing in {weak1} and {weak2} "
            "that could expose your organization to data leakage or regulatory risk. "
            "A remediation plan should be in place within 30 days."
        ),
        "High": (
            "{tool} is operating at significant risk. "
            "With a compliance score of {pct}%, critical controls are missing — "
            "particularly in {weak1} and {weak2}. "
            "This tool should not process sensitive business data until the priority gaps below are resolved."
        ),
        "Unacceptable": (
            "{tool} poses an unacceptable level of risk to your organization. "
            "At {pct}% compliance, fundamental AI governance controls are absent across "
            "{weak1} and {weak2}. "
            "Immediate escalation to senior leadership is recommended. "
            "Consider suspending this tool for any sensitive operations until critical gaps are resolved."
        ),
    },
    "fr": {
        "Minimal": (
            "{tool} est bien gouverné et fonctionne dans des limites de risque acceptables. "
            "Avec un score de conformité de {pct}%, la majorité des contrôles de risque IA sont en place. "
            "Les lacunes restantes sont de faible priorité et peuvent être comblées lors de la maintenance courante. "
            "Aucune action immédiate n'est requise."
        ),
        "Limited": (
            "{tool} est partiellement conforme mais présente des lacunes notables qui nécessitent une attention. "
            "À {pct}% de conformité, des contrôles manquent dans {weak1} et {weak2}, "
            "ce qui pourrait exposer votre organisation à des risques de fuite de données ou de non-conformité réglementaire. "
            "Un plan de remédiation devrait être en place dans les 30 jours."
        ),
        "High": (
            "{tool} fonctionne à un niveau de risque significatif. "
            "Avec un score de conformité de {pct}%, des contrôles critiques sont manquants — "
            "notamment dans {weak1} et {weak2}. "
            "Cet outil ne devrait pas traiter de données commerciales sensibles tant que les lacunes prioritaires ci-dessous ne sont pas résolues."
        ),
        "Unacceptable": (
            "{tool} représente un niveau de risque inacceptable pour votre organisation. "
            "À {pct}% de conformité, les contrôles fondamentaux de gouvernance IA sont absents dans "
            "{weak1} et {weak2}. "
            "Une escalade immédiate à la haute direction est recommandée. "
            "Envisagez de suspendre cet outil pour toute opération sensible jusqu'à ce que les lacunes critiques soient résolues."
        ),
    },
}


def get_verdict(assessment, tool, lang="fr"):
    """Return a plain-English or French verdict string for this assessment."""
    tier      = assessment["risk_tier"]
    pct       = assessment["compliance_pct"]
    tool_name = tool["name"]

    fn_scores  = {k: assessment[k] for k in FUNCTION_PLAIN["en"]}
    sorted_fns = sorted(fn_scores.items(), key=lambda x: x[1])
    plain      = FUNCTION_PLAIN.get(lang, FUNCTION_PLAIN["en"])
    weak1      = plain[sorted_fns[0][0]]
    weak2      = plain[sorted_fns[1][0]]

    lang_verdicts = VERDICTS.get(lang, VERDICTS["en"])
    template = lang_verdicts.get(tier, lang_verdicts["High"])
    return template.format(tool=tool_name, pct=pct, weak1=weak1, weak2=weak2)
