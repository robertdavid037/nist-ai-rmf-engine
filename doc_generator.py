import os
from datetime import date

from data.questions import QUESTIONS

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

TEMPLATE_FILES = {
    "acceptable_use":    "ai_acceptable_use_policy",
    "automated_decision":"automated_decision_notice",
    "vendor_risk":       "ai_vendor_risk_summary",
}

_TIER_FR = {
    "Minimal":      "Minimal",
    "Limited":      "Limité",
    "High":         "Élevé",
    "Unacceptable": "Inacceptable",
}
_TIER_EN = {
    "Minimal":      "Minimal",
    "Limited":      "Limited",
    "High":         "High",
    "Unacceptable": "Unacceptable",
}


def _build_gaps_list(responses, questions_by_id, lang):
    no_responses = sorted(
        [r for r in responses if r["answer"] == "No"],
        key=lambda x: x["risk_score"],
        reverse=True,
    )
    if not no_responses:
        return "  Aucune lacune identifiée." if lang == "fr" else "  No gaps identified."

    lines = []
    for i, r in enumerate(no_responses[:10], 1):
        q = questions_by_id.get(r["question_id"], {})
        text = (q.get("text_fr") or q.get("text", f"Question {r['question_id']}")) if lang == "fr" \
               else q.get("text", f"Question {r['question_id']}")
        fix = (q.get("fix_fr") or q.get("fix", "")) if lang == "fr" else q.get("fix", "")
        ref = q.get("loi25_ref") or q.get("nist_ref", "")
        score = r["risk_score"]

        ref_part = f"[{ref} | Score: {score}]" if ref else f"[Score: {score}]"
        lines.append(f"  {i}. {ref_part} {text}")
        if fix:
            action_label = "Action requise" if lang == "fr" else "Required action"
            lines.append(f"     {action_label}: {fix}")
        lines.append("")

    return "\n".join(lines)


def generate_doc(template_name, assessment, tool, responses, questions_by_id,
                 lang="fr", org_name=None):
    """Return a filled policy document string ready for download."""
    if org_name is None or not org_name.strip():
        org_name = "[Votre Organisation]" if lang == "fr" else "[Your Organization]"

    file_base = TEMPLATE_FILES[template_name]
    path = os.path.join(TEMPLATE_DIR, f"{file_base}_{lang}.txt")
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    tier = assessment["risk_tier"]
    gaps_list = _build_gaps_list(responses, questions_by_id, lang)

    replacements = {
        "tool_name":         tool["name"],
        "vendor":            tool["vendor"],
        "category":          tool["category"],
        "org_name":          org_name,
        "assessed_at":       assessment["assessed_at"][:10],
        "assessor_name":     assessment["assessor_name"],
        "date":              str(date.today()),
        "next_review_date":  assessment["next_review_date"],
        "compliance_pct":    str(assessment["compliance_pct"]),
        "loi25_pct":         str(assessment.get("loi25_pct", 100)),
        "risk_tier":         tier,
        "risk_tier_fr":      _TIER_FR.get(tier, tier),
        "risk_tier_en":      _TIER_EN.get(tier, tier),
        "govern_pct":        str(assessment["govern_pct"]),
        "map_pct":           str(assessment["map_pct"]),
        "measure_pct":       str(assessment["measure_pct"]),
        "manage_pct":        str(assessment["manage_pct"]),
        "total_risk_score":  str(assessment["total_risk_score"]),
        "max_possible_score":str(assessment["max_possible_score"]),
        "gaps_count":        str(sum(1 for r in responses if r["answer"] == "No")),
        "gaps_list":         gaps_list,
    }

    for key, value in replacements.items():
        raw = raw.replace(f"{{{key}}}", value)

    return raw
