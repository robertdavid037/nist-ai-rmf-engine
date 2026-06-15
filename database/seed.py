"""
Seed script — populates the database with demo assessments.
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
# Each tool has a list of assessments so we can demo trend lines.
# GitHub Copilot has 4 assessments showing a rising compliance trend.
# Answers: 18 entries per assessment, "Yes" = compliant, "No" = gap.
# ─────────────────────────────────────────────────────────────────────────────

DEMO_TOOLS = [
    {
        "name": "Microsoft Copilot",
        "vendor": "Microsoft",
        "category": "Productivity",
        "assessments": [
            {
                "assessor": "Demo Assessment",
                "days_ago": 15,
                # Q14 (bias eval, 6) and Q18 (periodic review, 6) are gaps → 94% Minimal
                "answers": [
                    "Yes", "Yes", "Yes", "Yes",   # Q1–Q4
                    "Yes", "Yes", "Yes", "Yes",   # Q5–Q8
                    "Yes", "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",   # Q13–Q16
                    "Yes", "No",                  # Q17–Q18
                ],
            },
        ],
    },
    {
        "name": "ChatGPT",
        "vendor": "OpenAI",
        "category": "Productivity",
        "assessments": [
            {
                "assessor": "Demo Assessment",
                "days_ago": 30,
                # Q1(12), Q2(9), Q5(20), Q8(16), Q9(20), Q14(6), Q15(20) are gaps → 52% High
                "answers": [
                    "No",  "No",  "Yes", "Yes",   # Q1–Q4
                    "No",  "Yes", "Yes", "No",    # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "No",  "No",  "Yes",   # Q13–Q16
                    "Yes", "Yes",                 # Q17–Q18
                ],
            },
        ],
    },
    {
        "name": "HubSpot AI",
        "vendor": "HubSpot",
        "category": "CRM",
        "assessments": [
            {
                "assessor": "Demo Assessment",
                "days_ago": 7,
                # Q3(9), Q5(20), Q8(16), Q14(6), Q18(6) are gaps → 73% Limited
                "answers": [
                    "Yes", "Yes", "No",  "Yes",   # Q1–Q4
                    "No",  "Yes", "Yes", "No",    # Q5–Q8
                    "Yes", "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",   # Q13–Q16
                    "Yes", "No",                  # Q17–Q18
                ],
            },
        ],
    },
    {
        "name": "GitHub Copilot",
        "vendor": "GitHub / Microsoft",
        "category": "Code",
        "assessments": [
            {
                "assessor": "Demo Assessment",
                "days_ago": 120,
                # Q1(12),Q2(9),Q3(9),Q5(20),Q6(15),Q8(16),Q9(20),Q14(6),Q15(20) → 41% High
                "answers": [
                    "No",  "No",  "No",  "Yes",   # Q1–Q4
                    "No",  "No",  "Yes", "No",    # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "No",  "No",  "Yes",   # Q13–Q16
                    "Yes", "Yes",                 # Q17–Q18
                ],
            },
            {
                "assessor": "Demo Assessment",
                "days_ago": 75,
                # Q1(12),Q2(9),Q3(9),Q5(20),Q8(16),Q9(20),Q14(6) → 57% High
                "answers": [
                    "No",  "No",  "No",  "Yes",   # Q1–Q4
                    "No",  "Yes", "Yes", "No",    # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",   # Q13–Q16
                    "Yes", "Yes",                 # Q17–Q18
                ],
            },
            {
                "assessor": "Demo Assessment",
                "days_ago": 42,
                # Q5(20),Q8(16),Q9(20),Q14(6),Q18(6) → 68% Limited
                "answers": [
                    "Yes", "Yes", "Yes", "Yes",   # Q1–Q4
                    "No",  "Yes", "Yes", "No",    # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",   # Q13–Q16
                    "Yes", "No",                  # Q17–Q18
                ],
            },
            {
                "assessor": "Demo Assessment",
                "days_ago": 14,
                # Q3(9),Q8(16),Q9(20) → 79% Limited
                "answers": [
                    "Yes", "Yes", "No",  "Yes",   # Q1–Q4
                    "Yes", "Yes", "Yes", "No",    # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",   # Q9–Q12
                    "Yes", "Yes", "Yes", "Yes",   # Q13–Q16
                    "Yes", "Yes",                 # Q17–Q18
                ],
            },
        ],
    },
]


def seed(skip_init=False):
    if not skip_init:
        print("Initialising database...")
        init_db()

    conn = get_connection()

    conn.execute("DELETE FROM responses")
    conn.execute("DELETE FROM assessments")
    conn.execute("DELETE FROM tools")
    conn.commit()
    print("Cleared existing data.")

    for tool_data in DEMO_TOOLS:
        cur = conn.execute(
            "INSERT INTO tools (name, vendor, category) VALUES (?, ?, ?)",
            (tool_data["name"], tool_data["vendor"], tool_data["category"]),
        )
        tool_id = cur.lastrowid

        for assessment_data in tool_data["assessments"]:
            responses = [
                {"question_id": i + 1, "answer": ans}
                for i, ans in enumerate(assessment_data["answers"])
            ]
            scores = calculate_scores(responses)
            tier = scores["risk_tier"]

            assessed_at = datetime.now() - timedelta(days=assessment_data["days_ago"])
            next_review = assessed_at + timedelta(days=90)

            cur = conn.execute(
                """INSERT INTO assessments
                   (tool_id, assessor_name, assessed_at, next_review_date,
                    total_risk_score, max_possible_score, compliance_pct, risk_tier,
                    govern_pct, map_pct, measure_pct, manage_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tool_id, assessment_data["assessor"],
                    assessed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    next_review.strftime("%Y-%m-%d"),
                    scores["total_risk_score"], scores["max_possible_score"],
                    scores["compliance_pct"], tier,
                    scores["govern_pct"], scores["map_pct"],
                    scores["measure_pct"], scores["manage_pct"],
                ),
            )
            assessment_id = cur.lastrowid

            for r in responses:
                risk_score = 0 if r["answer"] == "Yes" else QUESTIONS_BY_ID[r["question_id"]]["default_risk"]
                conn.execute(
                    """INSERT INTO responses
                       (assessment_id, question_id, answer, likelihood, impact, risk_score)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (assessment_id, r["question_id"], r["answer"], 0, 0, risk_score),
                )

            conn.commit()
            print(f"  OK  {tool_data['name']:25s} ({assessment_data['days_ago']:3d}d ago) "
                  f"- {scores['compliance_pct']:3d}% | {tier}")

    conn.close()
    print("\nDatabase seeded successfully.")


if __name__ == "__main__":
    seed()
