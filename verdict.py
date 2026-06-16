FUNCTION_PLAIN = {
    "govern_pct":  "governance and policy",
    "map_pct":     "data classification and access controls",
    "measure_pct": "technical risk controls",
    "manage_pct":  "risk management and guardrails",
}

VERDICTS = {
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
}


def get_verdict(assessment, tool):
    """Return a plain-English verdict string for this assessment."""
    tier      = assessment["risk_tier"]
    pct       = assessment["compliance_pct"]
    tool_name = tool["name"]

    fn_scores  = {k: assessment[k] for k in FUNCTION_PLAIN}
    sorted_fns = sorted(fn_scores.items(), key=lambda x: x[1])
    weak1 = FUNCTION_PLAIN[sorted_fns[0][0]]
    weak2 = FUNCTION_PLAIN[sorted_fns[1][0]]

    template = VERDICTS.get(tier, VERDICTS["High"])
    return template.format(tool=tool_name, pct=pct, weak1=weak1, weak2=weak2)
