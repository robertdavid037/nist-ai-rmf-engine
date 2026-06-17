#!/usr/bin/env python3
"""
First-run setup: creates ~/.config/nist-rmf/credentials.yaml with:
  - admin account (role: admin)
  - demo account  (role: user)
  - cryptographically random 256-bit cookie signing key
  - file permissions set to 600 (owner read/write only)

Run: python scripts/setup_auth.py
Override default path: RMF_CREDENTIALS_PATH=/custom/path python scripts/setup_auth.py
"""
import getpass
import os
import secrets
import stat
import sys

import bcrypt
import yaml

CREDS_DIR = os.environ.get(
    "RMF_CREDENTIALS_PATH",
    os.path.expanduser("~/.config/nist-rmf/credentials.yaml"),
)
# If env var points to a directory, append filename
if os.path.isdir(CREDS_DIR):
    CREDS_DIR = os.path.join(CREDS_DIR, "credentials.yaml")
CREDS_PATH = CREDS_DIR


def hash_password(plaintext: str) -> str:
    """bcrypt with cost factor 12 — ~250ms per hash, safe against brute-force."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def prompt_password(prompt: str, min_len: int) -> str:
    while True:
        pw = getpass.getpass(prompt)
        if len(pw) < min_len:
            print(f"  ERROR: Password must be at least {min_len} characters. Try again.")
            continue
        confirm = getpass.getpass("  Confirm: ")
        if pw != confirm:
            print("  ERROR: Passwords do not match. Try again.")
            continue
        return pw


def main() -> None:
    print("\n=== NIST AI RMF — Authentication Setup ===\n")

    if os.path.exists(CREDS_PATH):
        print(f"Credentials file already exists at:\n  {CREDS_PATH}\n")
        answer = input("Overwrite? This removes all existing users. [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted — existing credentials kept.")
            sys.exit(0)

    # ── Admin account ──────────────────────────────────────────────────────────
    print("─── Admin account ────────────────────────────────────────")
    admin_display = input("Admin display name [Admin]: ").strip() or "Admin"
    admin_email   = input("Admin email: ").strip()
    print("Admin password (minimum 12 characters):")
    admin_hash = hash_password(prompt_password("  Password: ", 12))

    # ── Demo account ───────────────────────────────────────────────────────────
    print("\n─── Demo / first-client account ──────────────────────────")
    use_random = input("Generate a random demo password? [Y/n] ").strip().lower()
    if use_random in ("", "y"):
        demo_plaintext = secrets.token_urlsafe(16)
        print(f"\n  Generated demo password: \033[1m{demo_plaintext}\033[0m")
        print("  Save this — it will NOT be shown again.\n")
        demo_hash = hash_password(demo_plaintext)
    else:
        print("Demo password (minimum 8 characters):")
        demo_hash = hash_password(prompt_password("  Password: ", 8))

    # ── Cookie key ─────────────────────────────────────────────────────────────
    cookie_key = secrets.token_hex(32)  # 256-bit, never leaves the server

    config = {
        "credentials": {
            "usernames": {
                "admin": {
                    "name":     admin_display,
                    "email":    admin_email,
                    "password": admin_hash,
                    "role":     "admin",
                },
                "demo": {
                    "name":     "Demo Client",
                    "email":    "demo@example.com",
                    "password": demo_hash,
                    "role":     "user",
                },
            }
        },
        "cookie": {
            "name":        "nist_rmf_session",
            "key":         cookie_key,
            "expiry_days": 1,
        },
    }

    # ── Write with strict permissions ─────────────────────────────────────────
    creds_dir = os.path.dirname(CREDS_PATH)
    if creds_dir:
        os.makedirs(creds_dir, mode=0o700, exist_ok=True)

    with open(CREDS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    os.chmod(CREDS_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 600 — owner only

    print(f"\n✓  Credentials written to:  {CREDS_PATH}")
    print("✓  File permissions:          600 (owner read/write only)")
    print("✓  Passwords:                 bcrypt cost-factor 12")
    print("✓  Cookie signing key:        256-bit random secret\n")
    print("Start the app:")
    print("  streamlit run app.py\n")
    print("Log in with username 'admin' or 'demo'.\n")


if __name__ == "__main__":
    main()
