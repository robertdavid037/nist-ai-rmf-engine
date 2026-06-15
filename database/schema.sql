-- NIST AI RMF Compliance Engine — Database Schema
--
-- 3 tables:
--   tools        → the AI tools being assessed (ChatGPT, Copilot, etc.)
--   assessments  → one row per completed assessment session
--   responses    → one row per question per assessment (18 rows per assessment)

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: tools
-- Each AI tool a company uses gets one row here.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tools (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,   -- e.g. "Microsoft Copilot"
    vendor      TEXT,                   -- e.g. "Microsoft"
    category    TEXT,                   -- e.g. "Productivity", "Code", "CRM"
    created_at  TEXT DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: assessments
-- One row per assessment run. Stores the final calculated scores.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assessments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id             INTEGER NOT NULL REFERENCES tools(id),
    assessor_name       TEXT DEFAULT 'Unknown',
    assessed_at         TEXT DEFAULT (datetime('now')),
    next_review_date    TEXT,           -- assessed_at + 90 days

    -- Scoring (calculated from responses)
    total_risk_score    INTEGER DEFAULT 0,   -- sum of all L×I scores (0 = perfect)
    max_possible_score  INTEGER DEFAULT 450, -- 18 questions × max 25 each
    compliance_pct      INTEGER DEFAULT 100, -- 100 - (risk/max * 100)
    risk_tier           TEXT DEFAULT 'Minimal', -- Minimal / Limited / High / Unacceptable

    -- Per-function compliance breakdown (for the dashboard drill-down)
    govern_pct          INTEGER DEFAULT 100,
    map_pct             INTEGER DEFAULT 100,
    measure_pct         INTEGER DEFAULT 100,
    manage_pct          INTEGER DEFAULT 100
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: responses
-- One row per question per assessment. 18 rows for every assessment.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS responses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id   INTEGER NOT NULL REFERENCES assessments(id),
    question_id     INTEGER NOT NULL,   -- 1–18, matches QUESTIONS list in data/questions.py
    answer          TEXT NOT NULL,      -- "Yes" or "No"
    likelihood      INTEGER DEFAULT 0,  -- 1–5 (only used when answer = "No")
    impact          INTEGER DEFAULT 0,  -- 1–5 (only used when answer = "No")
    risk_score      INTEGER DEFAULT 0,  -- likelihood × impact (0 if answer = "Yes")
    notes           TEXT DEFAULT ''     -- optional free text from assessor
);
