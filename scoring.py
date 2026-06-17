from datetime import datetime, timedelta
from database.db import get_connection
from data.questions import QUESTIONS

NIST_QUESTIONS  = [q for q in QUESTIONS if q.get("framework", "NIST") == "NIST"]
LOI25_QUESTIONS = [q for q in QUESTIONS if q.get("framework") == "LOI25"]

QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS}

MAX_POSSIBLE   = sum(q["default_risk"] for q in NIST_QUESTIONS)   # 214
LOI25_MAX      = sum(q["default_risk"] for q in LOI25_QUESTIONS)   # 120

FUNCTION_QUESTIONS = {
    "GOVERN":  [q["id"] for q in NIST_QUESTIONS if q["function"] == "GOVERN"],
    "MAP":     [q["id"] for q in NIST_QUESTIONS if q["function"] == "MAP"],
    "MEASURE": [q["id"] for q in NIST_QUESTIONS if q["function"] == "MEASURE"],
    "MANAGE":  [q["id"] for q in NIST_QUESTIONS if q["function"] == "MANAGE"],
}

LOI25_IDS = [q["id"] for q in LOI25_QUESTIONS]


def calculate_scores(responses):
    """
    responses: list of dicts with keys: question_id, answer
    Returns a dict of all calculated scores including loi25_pct.
    """
    risk_by_q = {}
    for r in responses:
        q_id = r["question_id"]
        risk_by_q[q_id] = 0 if r["answer"] == "Yes" else QUESTIONS_BY_ID[q_id]["default_risk"]

    # NIST score
    nist_risk  = sum(risk_by_q.get(q_id, 0) for q_id in [q["id"] for q in NIST_QUESTIONS])
    compliance_pct = round((1 - nist_risk / MAX_POSSIBLE) * 100)

    # Loi 25 score
    loi25_risk = sum(risk_by_q.get(q_id, 0) for q_id in LOI25_IDS)
    loi25_pct  = round((1 - loi25_risk / LOI25_MAX) * 100) if LOI25_MAX > 0 else 100

    def fn_pct(q_ids):
        fn_risk = sum(risk_by_q.get(q, 0) for q in q_ids)
        fn_max  = sum(QUESTIONS_BY_ID[q]["default_risk"] for q in q_ids)
        return round((1 - fn_risk / fn_max) * 100)

    return {
        "total_risk_score": nist_risk,
        "max_possible_score": MAX_POSSIBLE,
        "compliance_pct":  compliance_pct,
        "risk_tier":       pct_to_tier(compliance_pct),
        "govern_pct":      fn_pct(FUNCTION_QUESTIONS["GOVERN"]),
        "map_pct":         fn_pct(FUNCTION_QUESTIONS["MAP"]),
        "measure_pct":     fn_pct(FUNCTION_QUESTIONS["MEASURE"]),
        "manage_pct":      fn_pct(FUNCTION_QUESTIONS["MANAGE"]),
        "loi25_pct":       loi25_pct,
    }


def pct_to_tier(pct):
    if pct >= 80:
        return "Minimal"
    if pct >= 60:
        return "Limited"
    if pct >= 40:
        return "High"
    return "Unacceptable"


def save_assessment(tool_name, vendor, category, assessor_name, responses):
    """
    Saves a new assessment + responses to the database.
    Returns the new assessment_id.
    """
    scores = calculate_scores(responses)
    conn   = get_connection()

    row = conn.execute("SELECT id FROM tools WHERE name = ?", (tool_name,)).fetchone()
    if row:
        tool_id = row["id"]
    else:
        cur = conn.execute(
            "INSERT INTO tools (name, vendor, category) VALUES (?, ?, ?)",
            (tool_name, vendor, category),
        )
        tool_id = cur.lastrowid

    now         = datetime.now()
    next_review = now + timedelta(days=90)

    cur = conn.execute(
        """INSERT INTO assessments
           (tool_id, assessor_name, assessed_at, next_review_date,
            total_risk_score, max_possible_score, compliance_pct, risk_tier,
            govern_pct, map_pct, measure_pct, manage_pct, loi25_pct)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            tool_id, assessor_name,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            next_review.strftime("%Y-%m-%d"),
            scores["total_risk_score"],
            scores["max_possible_score"],
            scores["compliance_pct"],
            scores["risk_tier"],
            scores["govern_pct"],
            scores["map_pct"],
            scores["measure_pct"],
            scores["manage_pct"],
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
    conn.close()
    return assessment_id
