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
from scoring import calculate_scores, QUESTIONS_BY_ID

# ─────────────────────────────────────────────────────────────────────────────
# Demo answers per tool — 18 entries, one per question (Yes or No)
# Risk scores are pre-baked per question (see data/questions.py default_risk)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_TOOLS = [
    {
        "name": "Microsoft Copilot",
        "vendor": "Microsoft",
        "category": "Productivity",
        "assessor": "Demo Assessment",
        "days_ago": 15,
        # Q1–Q18: "Yes" = compliant, "No" = gap (uses default_risk from questions)
        "answers": [
            "Yes",   # Q1  Written policy
            "Yes",   # Q2  Designated AI owner
            "Yes",   # Q3  Employee training
            "Yes",   # Q4  AI inventory
            "Yes",   # Q5  Data protection measures
            "Yes",   # Q6  Access restrictions
            "Yes",   # Q7  Third-party API review
            "Yes",   # Q8  Input filtering
            "Yes",   # Q9  Prompt injection defense
            "Yes",   # Q10 Output controls
            "Yes",   # Q11 Human review of decisions
            "Yes",   # Q12 Output validation
            "Yes",   # Q13 Third-party data review
            "No",    # Q14 Bias/hallucination eval     → risk 6
            "Yes",   # Q15 Audit logs
            "Yes",   # Q16 Incident isolation plan
            "Yes",   # Q17 Guardrails
            "No",    # Q18 Periodic review             → risk 6
        ],
    },
    {
        "name": "ChatGPT",
        "vendor": "OpenAI",
        "category": "Productivity",
        "assessor": "Demo Assessment",
        "days_ago": 30,
        "answers": [
            "No",    # Q1  No written policy           → risk 12
            "No",    # Q2  No designated AI owner      → risk 9
            "Yes",   # Q3  Training exists
            "Yes",   # Q4  Inventory exists
            "No",    # Q5  No data protection          → risk 20
            "Yes",   # Q6  Access restrictions
            "Yes",   # Q7  API reviewed
            "No",    # Q8  No input filtering          → risk 16
            "No",    # Q9  No injection defense        → risk 20
            "Yes",   # Q10 Output controls
            "Yes",   # Q11 Human review exists
            "Yes",   # Q12 Output validated
            "Yes",   # Q13 Data sources reviewed
            "No",    # Q14 No bias eval                → risk 6
            "No",    # Q15 No audit logs               → risk 20
            "Yes",   # Q16 Incident plan
            "Yes",   # Q17 Guardrails in place
            "Yes",   # Q18 Periodic review
        ],
    },
    {
        "name": "HubSpot AI",
        "vendor": "HubSpot",
        "category": "CRM",
        "assessor": "Demo Assessment",
        "days_ago": 7,
        "answers": [
            "Yes",   # Q1  Written policy
            "Yes",   # Q2  Designated AI owner
            "No",    # Q3  No employee training        → risk 9
            "Yes",   # Q4  AI inventory
            "No",    # Q5  No data protection          → risk 20
            "Yes",   # Q6  Access restrictions
            "Yes",   # Q7  API reviewed
            "No",    # Q8  No input filtering          → risk 16
            "Yes",   # Q9  Prompt injection handled
            "Yes",   # Q10 Output controls
            "Yes",   # Q11 Human review exists
            "Yes",   # Q12 Output validated
            "Yes",   # Q13 Data sources reviewed
            "No",    # Q14 No bias eval                → risk 6
            "Yes",   # Q15 Audit logs
            "Yes",   # Q16 Incident plan
            "Yes",   # Q17 Guardrails in place
            "No",    # Q18 Infrequent review           → risk 6
        ],
    },
]


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
        # Build responses in the format calculate_scores expects
        responses = [
            {"question_id": i + 1, "answer": ans}
            for i, ans in enumerate(tool_data["answers"])
        ]

        scores = calculate_scores(responses)
        tier = scores["risk_tier"]

        # Insert tool
        cur = conn.execute(
            "INSERT INTO tools (name, vendor, category) VALUES (?, ?, ?)",
            (tool_data["name"], tool_data["vendor"], tool_data["category"]),
        )
        tool_id = cur.lastrowid

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
                scores["total_risk_score"],
                scores["max_possible_score"],
                scores["compliance_pct"],
                tier,
                scores["govern_pct"],
                scores["map_pct"],
                scores["measure_pct"],
                scores["manage_pct"],
            ),
        )
        assessment_id = cur.lastrowid

        # Insert responses
        for r in responses:
            risk_score = 0 if r["answer"] == "Yes" else QUESTIONS_BY_ID[r["question_id"]]["default_risk"]
            conn.execute(
                """INSERT INTO responses
                   (assessment_id, question_id, answer, likelihood, impact, risk_score)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (assessment_id, r["question_id"], r["answer"], 0, 0, risk_score),
            )

        conn.commit()
        print(f"  OK  {tool_data['name']:25s} - {scores['compliance_pct']:3d}% compliant | {tier} risk")

    conn.close()
    print("\nDatabase seeded successfully -> database/assessments.db")


if __name__ == "__main__":
    seed()
