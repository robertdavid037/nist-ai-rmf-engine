from fpdf import FPDF
from verdict import get_verdict

TIER_COLORS_RGB = {
    "Minimal":      (39, 174, 96),
    "Limited":      (243, 156, 18),
    "High":         (231, 76, 60),
    "Unacceptable": (108, 52, 131),
}

LM = 10   # left margin
W  = 190  # content width (A4 210mm - 10mm each side)


def _s(text):
    """Replace non-latin-1 characters so Helvetica can encode them."""
    return (text or "").replace("—", "-").replace("–", "-") \
                       .replace("‘", "'").replace("’", "'") \
                       .replace("“", '"').replace("”", '"') \
                       .replace("→", "->")


def _bar(pdf, x, y, w, h, pct):
    """Draw a coloured progress bar at absolute position (x, y)."""
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(x, y, w, h, "F")
    fill_w = w * max(pct, 0) / 100
    if pct >= 80:
        pdf.set_fill_color(39, 174, 96)
    elif pct >= 60:
        pdf.set_fill_color(243, 156, 18)
    elif pct >= 40:
        pdf.set_fill_color(231, 76, 60)
    else:
        pdf.set_fill_color(108, 52, 131)
    if fill_w > 0:
        pdf.rect(x, y, fill_w, h, "F")


def generate_pdf(assessment, tool, responses, questions_by_id):
    """Return bytes of a restructured PDF compliance report."""
    pdf = FPDF()
    pdf.set_margins(LM, 10, LM)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    tier     = assessment["risk_tier"]
    tier_rgb = TIER_COLORS_RGB.get(tier, (100, 100, 100))

    # ── Header bar ────────────────────────────────────────────────────────────
    pdf.set_fill_color(20, 52, 80)
    pdf.rect(0, 0, 210, 26, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(LM, 5)
    pdf.cell(W, 8, "NIST AI RMF Compliance Report")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(LM, 16)
    pdf.cell(W, 6, f"CONFIDENTIAL  |  Generated {assessment['assessed_at'][:10]}")

    # ── Tool identity ─────────────────────────────────────────────────────────
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(LM, 32)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(W, 8, _s(tool["name"]), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(LM)
    pdf.cell(W, 6, _s(f"{tool['vendor']} / {tool['category']}"), ln=True)
    pdf.set_x(LM)
    pdf.cell(W, 6, _s(f"Assessor: {assessment['assessor_name']}"), ln=True)
    pdf.set_x(LM)
    pdf.cell(W, 6, f"Date: {assessment['assessed_at'][:10]}  |  Next Review: {assessment['next_review_date']}", ln=True)

    # ── Plain-English verdict block ───────────────────────────────────────────
    pdf.ln(4)
    verdict_text = _s(get_verdict(assessment, tool))

    # Light grey background box
    verdict_y = pdf.get_y()
    pdf.set_fill_color(245, 245, 245)
    # Draw box first (estimate height), then write text on top
    pdf.set_draw_color(*tier_rgb)
    # Left accent bar
    pdf.set_fill_color(*tier_rgb)
    pdf.rect(LM, verdict_y, 3, 28, "F")
    # Grey background
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(LM + 3, verdict_y, W - 3, 28, "F")

    pdf.set_xy(LM + 7, verdict_y + 4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(W - 7, 6, "Executive Summary", ln=True)
    pdf.set_x(LM + 7)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(44, 62, 80)
    pdf.multi_cell(W - 10, 5, verdict_text)

    # ── Risk summary coloured block ───────────────────────────────────────────
    pdf.ln(4)
    block_y = pdf.get_y()
    pdf.set_fill_color(*tier_rgb)
    pdf.rect(LM, block_y, W, 20, "F")
    pdf.set_text_color(255, 255, 255)

    pdf.set_font("Helvetica", "B", 24)
    pdf.set_xy(LM + 4, block_y + 2)
    pdf.cell(34, 14, f"{assessment['compliance_pct']}%")

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(LM + 42, block_y + 3)
    pdf.cell(100, 7, f"{tier.upper()} RISK")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(LM + 42, block_y + 11)
    pdf.cell(100, 6, f"Risk Score: {assessment['total_risk_score']} / {assessment['max_possible_score']}")

    # ── NIST function breakdown ───────────────────────────────────────────────
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(LM, block_y + 28)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(W, 7, "Compliance by NIST Function", ln=True)

    functions = [
        ("GOVERN - Policies & Accountability",  assessment["govern_pct"]),
        ("MAP - Data & Risk Classification",     assessment["map_pct"]),
        ("MEASURE - Technical Risk Evaluation",  assessment["measure_pct"]),
        ("MANAGE - Risk Treatment & Guardrails", assessment["manage_pct"]),
    ]
    for fname, fpct in functions:
        row_y = pdf.get_y()
        pdf.set_x(LM)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(75, 7, fname)
        pdf.cell(12, 7, f"{fpct}%")
        _bar(pdf, 100, row_y + 1.5, 100, 4, fpct)
        pdf.ln(8)

    # ── Top 3 priority actions ────────────────────────────────────────────────
    no_responses = [r for r in responses if r["answer"] == "No"]
    no_responses.sort(key=lambda x: x["risk_score"], reverse=True)

    if no_responses:
        pdf.ln(4)
        pdf.set_x(LM)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(W, 7, "Top 3 Priority Actions", ln=True)
        pdf.set_x(LM)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(W, 5, "Fix these first - highest risk, biggest compliance impact.", ln=True)
        pdf.ln(2)

        for i, r in enumerate(no_responses[:3], 1):
            q        = questions_by_id.get(r["question_id"], {})
            q_text   = _s(q.get("text", f"Question {r['question_id']}"))
            q_fix    = _s(q.get("fix", ""))
            risk     = r["risk_score"]

            if risk >= 16:
                badge_rgb = (231, 76, 60)
            elif risk >= 9:
                badge_rgb = (243, 156, 18)
            else:
                badge_rgb = (52, 152, 219)

            action_y = pdf.get_y()
            pdf.set_fill_color(*badge_rgb)
            pdf.rect(LM, action_y, 3, 18, "F")
            pdf.set_fill_color(252, 252, 252)
            pdf.rect(LM + 3, action_y, W - 3, 18, "F")

            pdf.set_xy(LM + 7, action_y + 2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(W - 30, 5, f"{i}. {q_text}  [Risk: {risk}]")

            pdf.set_x(LM + 7)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(39, 174, 96)
            pdf.multi_cell(W - 12, 5, f"-> {q_fix}")

            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

    # ── Full priority fix list ────────────────────────────────────────────────
    pdf.ln(4)
    pdf.set_x(LM)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(W, 7, "Full Gap Analysis", ln=True)

    if not no_responses:
        pdf.set_x(LM)
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(W, 7, "No gaps found - fully compliant!", ln=True)
    else:
        for i, r in enumerate(no_responses, 1):
            q        = questions_by_id.get(r["question_id"], {})
            q_text   = _s(q.get("text",    f"Question {r['question_id']}"))
            q_why    = _s(q.get("why",     ""))
            q_fix    = _s(q.get("fix",     ""))
            nist_ref = _s(q.get("nist_ref",  ""))
            owasp_ref= _s(q.get("owasp_ref", "") or "")

            pdf.set_x(LM)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(W, 5, f"{i}. {q_text}  [Risk: {r['risk_score']}]")

            pdf.set_x(LM)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(W, 5, f"   {q_why}")

            pdf.set_x(LM)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(39, 174, 96)
            pdf.multi_cell(W, 5, f"   -> {q_fix}")

            refs = f"   {nist_ref}"
            if owasp_ref:
                refs += f"  /  {owasp_ref}"
            refs += f"  /  Risk Score: {r['risk_score']}"
            pdf.set_x(LM)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(60, 80, 160)
            pdf.multi_cell(W, 5, refs)

            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(-15)
    pdf.set_x(LM)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(W, 6, "Generated by NIST AI RMF Compliance Engine  |  Confidential", align="C")

    return bytes(pdf.output())
