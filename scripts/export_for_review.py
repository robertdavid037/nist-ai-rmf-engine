#!/usr/bin/env python3
"""
Export all source files into a single review_bundle.txt.
Safe to paste into Gemini, Codex, or any AI review tool.
No credentials, no DB, no secrets.

Run from the project root:
    python scripts/export_for_review.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "review_bundle.txt")

# Files to include, in logical reading order
INCLUDE = [
    "requirements.txt",
    "database/schema.sql",
    "data/questions.py",
    "scoring.py",
    "translations.py",
    "verdict.py",
    "auth.py",
    "sidebar.py",
    "doc_generator.py",
    "pdf_export.py",
    "database/db.py",
    "database/seed.py",
    "app.py",
    "pages/0_Admin.py",
    "pages/1_Assessment.py",
    "pages/2_Report.py",
    "pages/3_Insights.py",
    "templates/ai_acceptable_use_policy_fr.txt",
    "templates/ai_acceptable_use_policy_en.txt",
    "templates/automated_decision_notice_fr.txt",
    "templates/automated_decision_notice_en.txt",
    "templates/ai_vendor_risk_summary_fr.txt",
    "templates/ai_vendor_risk_summary_en.txt",
    "scripts/setup_auth.py",
]

SEP = "=" * 80

lines = [
    SEP,
    "NIST AI RMF COMPLIANCE ENGINE — FULL SOURCE REVIEW BUNDLE",
    "Generated for external code review. No credentials or sensitive data.",
    f"Files: {len(INCLUDE)}",
    SEP,
    "",
]

total_chars = 0
missing = []

for rel_path in INCLUDE:
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        missing.append(rel_path)
        continue

    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    total_chars += len(content)
    ext = rel_path.rsplit(".", 1)[-1] if "." in rel_path else "text"
    lang_hint = {"py": "python", "sql": "sql", "txt": "text", "toml": "toml"}.get(ext, "text")

    lines += [
        "",
        SEP,
        f"FILE: {rel_path}",
        SEP,
        f"```{lang_hint}",
        content.rstrip(),
        "```",
    ]

lines += [
    "",
    SEP,
    f"END OF BUNDLE — {len(INCLUDE) - len(missing)} files, ~{total_chars:,} characters",
    SEP,
]

if missing:
    lines += ["", "WARNING: files not found (skipped):"]
    for m in missing:
        lines.append(f"  - {m}")

output = "\n".join(lines)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(output)

est_tokens = total_chars // 4
print(f"✓  review_bundle.txt written ({total_chars:,} chars, ~{est_tokens:,} tokens)")
print(f"   Fits in: Gemini 1.5 Pro (1M), GPT-4o (128K)", end="")
print(" ✓" if est_tokens < 100_000 else " — may need splitting for smaller models")
if missing:
    print(f"   Skipped {len(missing)} missing file(s): {', '.join(missing)}")
print(f"\n   File saved to: {OUT}")
