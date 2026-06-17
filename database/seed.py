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
# Each tool has 4 assessments spread across ~6 months so the trend chart
# tells a real story. Answers: 26 entries per assessment (Q1–Q26).
#
# NIST risk scores (Q1–Q18), MAX = 214:
#   Q1:12  Q2:9   Q3:9   Q4:6   Q5:20  Q6:15  Q7:12  Q8:16  Q9:20
#   Q10:12 Q11:9  Q12:9  Q13:6  Q14:6  Q15:20 Q16:12 Q17:15 Q18:6
#
# Loi 25 risk scores (Q19–Q26), MAX = 120:
#   Q19:20 Q20:20 Q21:16 Q22:15 Q23:12 Q24:12 Q25:16 Q26:9
# ─────────────────────────────────────────────────────────────────────────────

DEMO_TOOLS = [
    {
        "name": "Microsoft Copilot",
        "vendor": "Microsoft",
        "category": "Productivity",
        "assessments": [
            {
                # 180d ago — NIST 71% Limited | Loi25 53%
                # NIST No: Q3(9) Q4(6) Q8(16) Q9(20) Q14(6) Q18(6) = 63 risk
                # Loi25 No: Q19(20) Q22(15) Q23(12) Q26(9) = 56 risk
                "assessor": "Demo Assessment", "days_ago": 180,
                "answers": [
                    "Yes", "Yes", "No",  "No",   # Q1–Q4
                    "Yes", "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "No",                 # Q17–Q18
                    "No",  "Yes", "Yes", "No",  "No",  "Yes", "Yes", "No",  # Q19–Q26
                ],
            },
            {
                # 120d ago — NIST 80% Minimal | Loi25 63%
                # NIST No: Q8(16) Q9(20) Q14(6) = 42 risk
                # Loi25 No: Q20(20) Q22(15) Q26(9) = 44 risk
                "assessor": "Demo Assessment", "days_ago": 120,
                "answers": [
                    "Yes", "Yes", "Yes", "Yes",  # Q1–Q4
                    "Yes", "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "Yes", "No",  "Yes", "No",  "Yes", "Yes", "Yes", "No",  # Q19–Q26
                ],
            },
            {
                # 60d ago — NIST 88% Minimal | Loi25 76%
                # NIST No: Q4(6) Q9(20) = 26 risk
                # Loi25 No: Q20(20) Q26(9) = 29 risk
                "assessor": "Demo Assessment", "days_ago": 60,
                "answers": [
                    "Yes", "Yes", "Yes", "No",   # Q1–Q4
                    "Yes", "Yes", "Yes", "Yes",  # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "Yes", "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "Yes", "No",  "Yes", "Yes", "Yes", "Yes", "Yes", "No",  # Q19–Q26
                ],
            },
            {
                # 15d ago — NIST 94% Minimal | Loi25 83%
                # NIST No: Q14(6) Q18(6) = 12 risk
                # Loi25 No: Q19(20) = 20 risk
                "assessor": "Demo Assessment", "days_ago": 15,
                "answers": [
                    "Yes", "Yes", "Yes", "Yes",  # Q1–Q4
                    "Yes", "Yes", "Yes", "Yes",  # Q5–Q8
                    "Yes", "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "No",                 # Q17–Q18
                    "No",  "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes",  # Q19–Q26
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
                # 180d ago — NIST 32% Unacceptable | Loi25 28%
                # NIST No: Q1(12) Q2(9) Q3(9) Q4(6) Q5(20) Q6(15) Q8(16) Q9(20) Q10(12) Q14(6) Q15(20) = 145
                # Loi25 No: Q19(20) Q20(20) Q21(16) Q22(15) Q25(16) = 87 risk
                "assessor": "Demo Assessment", "days_ago": 180,
                "answers": [
                    "No",  "No",  "No",  "No",   # Q1–Q4
                    "No",  "No",  "Yes", "No",   # Q5–Q8
                    "No",  "No",  "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "No",  "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "No",  "No",  "No",  "No",  "Yes", "Yes", "No",  "Yes",  # Q19–Q26
                ],
            },
            {
                # 120d ago — NIST 41% High | Loi25 41%
                # NIST No: Q1(12) Q2(9) Q3(9) Q5(20) Q6(15) Q8(16) Q9(20) Q14(6) Q15(20) = 127
                # Loi25 No: Q19(20) Q20(20) Q21(16) Q22(15) = 71 risk
                "assessor": "Demo Assessment", "days_ago": 120,
                "answers": [
                    "No",  "No",  "No",  "Yes",  # Q1–Q4
                    "No",  "No",  "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "No",  "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "No",  "No",  "No",  "No",  "Yes", "Yes", "Yes", "Yes",  # Q19–Q26
                ],
            },
            {
                # 60d ago — NIST 48% High | Loi25 50%
                # NIST No: Q1(12) Q2(9) Q3(9) Q5(20) Q8(16) Q9(20) Q14(6) Q15(20) = 112
                # Loi25 No: Q20(20) Q21(16) Q22(15) Q26(9) = 60 risk
                "assessor": "Demo Assessment", "days_ago": 60,
                "answers": [
                    "No",  "No",  "No",  "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "No",  "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "Yes", "No",  "No",  "No",  "Yes", "Yes", "Yes", "No",  # Q19–Q26
                ],
            },
            {
                # 30d ago — NIST 52% High | Loi25 58%
                # NIST No: Q1(12) Q2(9) Q5(20) Q8(16) Q9(20) Q14(6) Q15(20) = 103
                # Loi25 No: Q19(20) Q22(15) Q25(16) = 51 risk
                "assessor": "Demo Assessment", "days_ago": 30,
                "answers": [
                    "No",  "No",  "Yes", "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "No",  "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "No",  "Yes", "Yes", "No",  "Yes", "Yes", "No",  "Yes",  # Q19–Q26
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
                # 150d ago — NIST 83% Minimal | Loi25 43%
                # NIST No: Q8(16) Q9(20) = 36 risk
                # Loi25 No: Q19(20) Q20(20) Q21(16) Q23(12) = 68 risk
                "assessor": "Demo Assessment", "days_ago": 150,
                "answers": [
                    "Yes", "Yes", "Yes", "Yes",  # Q1–Q4
                    "Yes", "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "Yes", "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "No",  "No",  "No",  "Yes", "No",  "Yes", "Yes", "Yes",  # Q19–Q26
                ],
            },
            {
                # 90d ago — NIST 76% Limited | Loi25 58%
                # NIST No: Q3(9) Q5(20) Q8(16) Q14(6) = 51 risk
                # Loi25 No: Q20(20) Q21(16) Q22(15) = 51 risk
                "assessor": "Demo Assessment", "days_ago": 90,
                "answers": [
                    "Yes", "Yes", "No",  "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "Yes", "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "Yes", "No",  "No",  "No",  "Yes", "Yes", "Yes", "Yes",  # Q19–Q26
                ],
            },
            {
                # 42d ago — NIST 67% Limited (dip) | Loi25 50%
                # NIST No: Q3(9) Q5(20) Q8(16) Q9(20) Q14(6) = 71 risk
                # Loi25 No: Q20(20) Q21(16) Q22(15) Q26(9) = 60 risk
                "assessor": "Demo Assessment", "days_ago": 42,
                "answers": [
                    "Yes", "Yes", "No",  "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "Yes", "No",  "No",  "No",  "Yes", "Yes", "Yes", "No",  # Q19–Q26
                ],
            },
            {
                # 7d ago — NIST 73% Limited (recovering) | Loi25 67%
                # NIST No: Q3(9) Q5(20) Q8(16) Q14(6) Q18(6) = 57 risk
                # Loi25 No: Q22(15) Q25(16) Q26(9) = 40 risk
                "assessor": "Demo Assessment", "days_ago": 7,
                "answers": [
                    "Yes", "Yes", "No",  "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "Yes", "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "No",                 # Q17–Q18
                    "Yes", "Yes", "Yes", "No",  "Yes", "Yes", "No",  "No",  # Q19–Q26
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
                # 120d ago — NIST 41% High | Loi25 58%
                # NIST No: Q1(12) Q2(9) Q3(9) Q5(20) Q6(15) Q8(16) Q9(20) Q14(6) Q15(20) = 127
                # Loi25 No: Q19(20) Q22(15) Q25(16) = 51 risk
                "assessor": "Demo Assessment", "days_ago": 120,
                "answers": [
                    "No",  "No",  "No",  "Yes",  # Q1–Q4
                    "No",  "No",  "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "No",  "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "No",  "Yes", "Yes", "No",  "Yes", "Yes", "No",  "Yes",  # Q19–Q26
                ],
            },
            {
                # 75d ago — NIST 57% High | Loi25 67%
                # NIST No: Q1(12) Q2(9) Q3(9) Q5(20) Q8(16) Q9(20) Q14(6) = 92 risk
                # Loi25 No: Q22(15) Q25(16) Q26(9) = 40 risk
                "assessor": "Demo Assessment", "days_ago": 75,
                "answers": [
                    "No",  "No",  "No",  "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "Yes", "Yes", "Yes", "No",  "Yes", "Yes", "No",  "No",  # Q19–Q26
                ],
            },
            {
                # 42d ago — NIST 68% Limited | Loi25 74%
                # NIST No: Q5(20) Q8(16) Q9(20) Q14(6) Q18(6) = 68 risk
                # Loi25 No: Q22(15) Q25(16) = 31 risk
                "assessor": "Demo Assessment", "days_ago": 42,
                "answers": [
                    "Yes", "Yes", "Yes", "Yes",  # Q1–Q4
                    "No",  "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "No",  "Yes", "Yes",  # Q13–Q16
                    "Yes", "No",                 # Q17–Q18
                    "Yes", "Yes", "Yes", "No",  "Yes", "Yes", "No",  "Yes",  # Q19–Q26
                ],
            },
            {
                # 14d ago — NIST 79% Limited | Loi25 83%
                # NIST No: Q3(9) Q8(16) Q9(20) = 45 risk
                # Loi25 No: Q19(20) = 20 risk
                "assessor": "Demo Assessment", "days_ago": 14,
                "answers": [
                    "Yes", "Yes", "No",  "Yes",  # Q1–Q4
                    "Yes", "Yes", "Yes", "No",   # Q5–Q8
                    "No",  "Yes", "Yes", "Yes",  # Q9–Q12
                    "Yes", "Yes", "Yes", "Yes",  # Q13–Q16
                    "Yes", "Yes",                # Q17–Q18
                    "No",  "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes",  # Q19–Q26
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
                    govern_pct, map_pct, measure_pct, manage_pct, loi25_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tool_id, assessment_data["assessor"],
                    assessed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    next_review.strftime("%Y-%m-%d"),
                    scores["total_risk_score"], scores["max_possible_score"],
                    scores["compliance_pct"], tier,
                    scores["govern_pct"], scores["map_pct"],
                    scores["measure_pct"], scores["manage_pct"],
                    scores["loi25_pct"],
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
