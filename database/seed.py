"""
Seed script — populates the database with 3 realistic demo assessments.
Run once: python3 database/seed.py

Safe to re-run: clears existing data first, then re-inserts.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import get_connection, init_db

# ─────────────────────────────────────────────────────────────────────────────
# Demo answers per tool
# Each entry: (question_id, answer, likelihood, impact)
# Yes → likelihood=0, impact=0, risk_score=0
# No  → likelihood and impact set realistically for that tool
# ─────────────────────────────────────────────────────────────────────────────

DEMO_TOOLS = [
    {
        "name": "Microsoft Copilot",
        "vendor": "Microsoft",
        "category": "Productivity",
        "assessor": "Demo Assessment",
        "days_ago": 15,
        # Q1–Q18 answers: "Yes" or ("No", likelihood, impact)
        "answers": [
            ("Yes",  0, 0),   # Q1  Written policy
            ("Yes",  0, 0),   # Q2  Designated AI owner
            ("Yes",  0, 0),   # Q3  Employee training
            ("Yes",  0, 0),   # Q4  AI inventory
            ("Yes",  0, 0),   # Q5  Data protection measures
            ("Yes",  0, 0),   # Q6  Access restrictions
            ("Yes",  0, 0),   # Q7  Third-party API review
            ("No",   2, 3),   # Q8  Input filtering          → score 6
            ("No",   2, 4),   # Q9  Prompt injection defense → score 8
            ("Yes",  0, 0),   # Q10 Output controls
            ("Yes",  0, 0),   # Q11 Human review of decisions
            ("Yes",  0, 0),   # Q12 Output validation
            ("Yes",  0, 0),   # Q13 Third-party data review
            ("No",   1, 2),   # Q14 Bias/hallucination eval  → score 2
            ("Yes",  0, 0),   # Q15 Audit logs
            ("Yes",  0, 0),   # Q16 Incident isolation plan
            ("Yes",  0, 0),   # Q17 Guardrails
            ("No",   1, 2),   # Q18 Periodic review          → score 2
        ],
    },
    {
        "name": "ChatGPT",
        "vendor": "OpenAI",
        "category": "Productivity",
        "assessor": "Demo Assessment",
        "days_ago": 30,
        "answers": [
            ("No",   3, 4),   # Q1  No written policy        → score 12
            ("No",   3, 3),   # Q2  No designated AI owner   → score 9
            ("No",   2, 3),   # Q3  No training              → score 6
            ("No",   2, 3),   # Q4  No inventory             → score 6
            ("No",   4, 5),   # Q5  No data protection       → score 20
            ("No",   3, 5),   # Q6  No access restrictions   → score 15
            ("No",   3, 4),   # Q7  No API review            → score 12
            ("No",   4, 5),   # Q8  No input filtering       → score 20
            ("No",   4, 5),   # Q9  No injection defense     → score 20
            ("No",   3, 4),   # Q10 No output controls       → score 12
            ("No",   3, 4),   # Q11 No human review          → score 12
            ("No",   3, 3),   # Q12 No output validation     → score 9
            ("Yes",  0, 0),   # Q13 Third-party data OK
            ("No",   2, 3),   # Q14 No bias eval             → score 6
            ("No",   4, 5),   # Q15 No audit logs            → score 20
            ("No",   2, 3),   # Q16 No incident plan         → score 6
            ("No",   3, 4),   # Q17 No guardrails            → score 12
            ("No",   2, 3),   # Q18 No periodic review       → score 6
        ],
    },
    {
        "name": "HubSpot AI",
        "vendor": "HubSpot",
        "category": "CRM",
        "assessor": "Demo Assessment",
        "days_ago": 7,
        "answers": [
            ("Yes",  0, 0),   # Q1  Written policy
            ("Yes",  0, 0),   # Q2  Designated AI owner
            ("No",   2, 3),   # Q3  Partial training         → score 6
            ("Yes",  0, 0),   # Q4  AI inventory
            ("No",   3, 4),   # Q5  Partial data protection  → score 12
            ("Yes",  0, 0),   # Q6  Access restrictions
            ("Yes",  0, 0),   # Q7  API reviewed
            ("No",   3, 4),   # Q8  No input filtering       → score 12
            ("No",   3, 4),   # Q9  No injection defense     → score 12
            ("No",   2, 3),   # Q10 Partial output controls  → score 6
            ("Yes",  0, 0),   # Q11 Human review exists
            ("Yes",  0, 0),   # Q12 Output validated
            ("Yes",  0, 0),   # Q13 Data sources reviewed
            ("No",   2, 3),   # Q14 No bias eval             → score 6
            ("Yes",  0, 0),   # Q15 Audit logs
            ("No",   2, 3),   # Q16 No incident plan         → score 6
            ("Yes",  0, 0),   # Q17 Guardrails in place
            ("No",   2, 2),   # Q18 Infrequent review        → score 4
        ],
    },
]

# Which questions belong to which NIST function (for per-function % breakdown)
FUNCTION_QUESTIONS = {
    "GOVERN":  [1, 2, 3, 4],
    "MAP":     [5, 6, 7, 8],
    "MEASURE": [9, 10, 11, 12, 13, 14],
    "MANAGE":  [15, 16, 17, 18],
}
MAX_PER_QUESTION = 25  # 5 × 5


def calculate_scores(answers):
    """Return (total_risk, compliance_pct, govern_pct, map_pct, measure_pct, manage_pct)."""
    risk_by_q = {}
    for i, (answer, likelihood, impact) in enumerate(answers, start=1):
        risk_by_q[i] = 0 if answer == "Yes" else likelihood * impact

    total_risk = sum(risk_by_q.values())
    max_total = len(answers) * MAX_PER_QUESTION
    compliance_pct = round((1 - total_risk / max_total) * 100)

    def fn_pct(q_ids):
        fn_risk = sum(risk_by_q[q] for q in q_ids)
        fn_max = len(q_ids) * MAX_PER_QUESTION
        return round((1 - fn_risk / fn_max) * 100)

    return (
        total_risk,
        compliance_pct,
        fn_pct(FUNCTION_QUESTIONS["GOVERN"]),
        fn_pct(FUNCTION_QUESTIONS["MAP"]),
        fn_pct(FUNCTION_QUESTIONS["MEASURE"]),
        fn_pct(FUNCTION_QUESTIONS["MANAGE"]),
    )


def compliance_to_tier(pct):
    if pct >= 80: return "Minimal"
    if pct >= 60: return "Limited"
    if pct >= 40: return "High"
    return "Unacceptable"


def seed(skip_init=False):
    if not skip_init:
        print("Initialising database...")
        init_db()

    conn = get_connection()

    # Clear existing demo data
    conn.execute("DELETE FROM responses")
    conn.execute("DELETE FROM assessments")
    conn.execute("DELETE FROM tools")
    conn.commit()
    print("Cleared existing data.")

    for tool_data in DEMO_TOOLS:
        # Insert tool
        cur = conn.execute(
            "INSERT INTO tools (name, vendor, category) VALUES (?, ?, ?)",
            (tool_data["name"], tool_data["vendor"], tool_data["category"]),
        )
        tool_id = cur.lastrowid

        # Calculate scores
        answers = tool_data["answers"]
        (total_risk, compliance_pct, gov_pct, map_pct, meas_pct, man_pct) = calculate_scores(answers)
        tier = compliance_to_tier(compliance_pct)

        assessed_at = datetime.now() - timedelta(days=tool_data["days_ago"])
        next_review = assessed_at + timedelta(days=90)

        # Insert assessment
        cur = conn.execute(
            """INSERT INTO assessments
               (tool_id, assessor_name, assessed_at, next_review_date,
                total_risk_score, max_possible_score, compliance_pct, risk_tier,
                govern_pct, map_pct, measure_pct, manage_pct)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tool_id, tool_data["assessor"],
                assessed_at.strftime("%Y-%m-%d %H:%M:%S"),
                next_review.strftime("%Y-%m-%d"),
                total_risk, len(answers) * MAX_PER_QUESTION,
                compliance_pct, tier,
                gov_pct, map_pct, meas_pct, man_pct,
            ),
        )
        assessment_id = cur.lastrowid

        # Insert responses (one per question)
        for q_id, (answer, likelihood, impact) in enumerate(answers, start=1):
            risk_score = 0 if answer == "Yes" else likelihood * impact
            conn.execute(
                """INSERT INTO responses
                   (assessment_id, question_id, answer, likelihood, impact, risk_score)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (assessment_id, q_id, answer, likelihood, impact, risk_score),
            )

        conn.commit()
        print(f"  ✅ {tool_data['name']:25s} — {compliance_pct:3d}% compliant | {tier} risk")

    conn.close()
    print("\nDatabase seeded successfully → database/assessments.db")


if __name__ == "__main__":
    seed()
