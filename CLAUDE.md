# NIST AI RMF Compliance Engine — Project Context

## What This Is
A lightweight, zero-friction AI Governance compliance assessment tool and dynamic risk matrix based on the NIST AI Risk Management Framework (AI RMF 1.0). POC phase: local machine, demo-ready, built to attract investment and early clients.

## Business Context
- **Target market:** SMBs (small-medium businesses)
- **Use case:** Sell as a GRC service — show clients their AI security posture, generate compliance reports
- **Phase 1 goal:** POC to demo to investors and prospects, run locally
- **Final product vision:** Nagomi Security-style dashboard — every AI tool a company uses, scored, tracked, with audit dates

## Confirmed Stack
- **UI + Backend:** Python + Streamlit (free, open source)
- **Database:** SQLite (zero infrastructure, built into Python)
- **PDF export:** fpdf2 or weasyprint library
- **Export format:** PDF (client-facing) + JSON (future n8n integration)

## NIST AI RMF Core Functions (the 4 assessment pillars)
- **GOVERN** — Corporate AI policies, accountability, training data boundaries
- **MAP** — AI system classification (inputs, outputs, third-party APIs, user impact)
- **MEASURE** — Technical risk evaluation (OWASP LLM Top 10, MITRE ATLAS)
- **MANAGE** — Risk treatment, guardrails, drift monitoring, audit logs

## Assessment Design (confirmed)
- **Questions:** Pre-built fixed set of ~15–20 questions mapped to NIST + OWASP LLM Top 10
- **Scoring:** Likelihood (1–5) × Impact (1–5) = Risk Score → Risk Tier
- **Risk tiers:** Minimal / Limited / High / Unacceptable
- **AI tools (pre-populated):**
  - ChatGPT / ChatGPT Team
  - Microsoft Copilot
  - Google Workspace AI (Gemini)
  - GitHub Copilot
  - HubSpot AI
  - Salesforce Einstein
  - Zapier AI
  - Make AI
  - Other (free text)

## Dashboard Design (confirmed)
- **Default view:** All assessed tools as cards showing compliance %, risk tier badge, last assessed date
- **Sort controls:** By Risk (highest first) | By Compliance (most compliant first) | By Date
- **Drill-in:** Click any tool card → full report + risk breakdown
- **Pre-seeded demo data:** 3 fake assessments (Copilot, ChatGPT, HubSpot AI) loaded at launch

## Report Design (confirmed)
- **On-screen:** Risk score gauge, color-coded tier badge, compliance % per NIST function, prioritized fix list
- **Download:** PDF button — top right of the on-screen report
- **Silent export:** JSON saved alongside (for future n8n use)

## Demo Flow (60-second pitch)
1. Open app → dashboard loads with 3 pre-seeded tools
2. Sort by Risk → red tool (highest risk) rises to top
3. Click it → full compliance report loads on screen
4. Hit "Download PDF" → professional report saves
5. Run a live assessment on a new tool → show the intake form → submit → report generates

## How Claude Should Help in This Project
- User has zero coding background — explain every step like they're new to this
- Always provide step-by-step setup guides (especially for SQLite, virtual environments)
- Write working code, not pseudocode
- Test that commands actually run on Ubuntu before suggesting
- Keep files small and readable — no over-engineering
- Ask before making architectural decisions

## Build Status
- [x] Grill-me design session complete
- [x] Stack confirmed: Python + Streamlit + SQLite
- [x] Dashboard design confirmed
- [x] Report design confirmed
- [x] Environment setup — Python 3.14.4, venv at ./venv, streamlit + fpdf2 installed
- [x] Assessment questions researched and finalized — 18 questions in data/questions.py
- [x] SQLite schema designed — 3 tables: tools, assessments, responses
- [x] Demo data pre-seeded — Copilot 96%, HubSpot 86%, ChatGPT 55%
- [x] Dashboard built — app.py, 3-column cards, sort controls, tier badges
- [x] Assessment form built — pages/1_Assessment.py, 18 questions, L×I sliders on each No
- [x] Scoring engine built — scoring.py, calculate_scores(), save_assessment()
- [x] On-screen report built — pages/2_Report.py, function breakdown, prioritized fix list
- [x] PDF export built — pdf_export.py, coloured risk block + progress bars + fix list
- [ ] End-to-end demo test passed
