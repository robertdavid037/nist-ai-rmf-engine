"""
auth.py — Authentication utilities for the NIST AI RMF Compliance Engine.

Credentials are loaded from two sources, in priority order:
  1. Streamlit Cloud Secrets (st.secrets) — for cloud deployment
  2. ~/.config/nist-rmf/credentials.yaml  — for local deployment

Run scripts/setup_auth.py for local setup, or use the in-browser wizard
which also shows the TOML to paste into Streamlit Cloud Secrets.
"""
import os
import stat

import bcrypt
import streamlit as st
import streamlit_authenticator as stauth
import yaml

CREDS_PATH: str = os.environ.get(
    "RMF_CREDENTIALS_PATH",
    os.path.expanduser("~/.config/nist-rmf/credentials.yaml"),
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _secrets_available() -> bool:
    try:
        return "credentials" in st.secrets and "cookie" in st.secrets
    except Exception:
        return False


def is_cloud_mode() -> bool:
    """True when running on Streamlit Cloud (secrets only, no local YAML file)."""
    return _secrets_available() and not os.path.exists(CREDS_PATH)


def _config_available() -> bool:
    return _secrets_available() or os.path.exists(CREDS_PATH)


def _deep_dict(obj) -> dict:
    """Recursively convert Streamlit AttrDict sections to plain dicts."""
    if hasattr(obj, "to_dict"):
        return {k: _deep_dict(v) for k, v in obj.to_dict().items()}
    if hasattr(obj, "items"):
        return {k: _deep_dict(v) for k, v in obj.items()}
    return obj


def _load_config() -> dict:
    """Load from st.secrets (cloud) first, then fall back to local YAML."""
    if _secrets_available():
        return {
            "credentials": _deep_dict(st.secrets["credentials"]),
            "cookie":      _deep_dict(st.secrets["cookie"]),
        }
    with open(CREDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_config(config: dict) -> None:
    """Write to local YAML with 600 permissions. Raises on cloud-only mode."""
    if is_cloud_mode():
        raise RuntimeError(
            "Running in Streamlit Cloud secrets-only mode. "
            "Update credentials via the Streamlit Cloud Secrets dashboard."
        )
    creds_dir = os.path.dirname(CREDS_PATH)
    if creds_dir:
        os.makedirs(creds_dir, mode=0o700, exist_ok=True)
    with open(CREDS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    os.chmod(CREDS_PATH, stat.S_IRUSR | stat.S_IWUSR)


def _make_authenticator() -> stauth.Authenticate:
    config = _load_config()
    return stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=False,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def require_login() -> str:
    """
    Call at the top of every page.
    Returns the authenticated username, or renders the login/setup form and stops.
    """
    if not _config_available():
        _render_first_run_setup()
        st.stop()

    auth = _make_authenticator()

    if st.session_state.get("authentication_status") is not True:
        _render_login_page(auth)
        st.stop()

    return str(st.session_state["username"])


def render_logout_button() -> None:
    """Render a logout button in the current location (call from within st.sidebar)."""
    if st.session_state.get("authentication_status") is True:
        auth = _make_authenticator()
        name = st.session_state.get("name", st.session_state.get("username", ""))
        st.caption(f"👤 {name}")
        auth.logout("🚪 Déconnexion / Logout", location="sidebar", key="sidebar_logout")


def is_admin() -> bool:
    """True if the logged-in user has role='admin' in credentials.yaml."""
    username = st.session_state.get("username")
    if not username or not os.path.exists(CREDS_PATH):
        return False
    config = _load_config()
    user = config["credentials"]["usernames"].get(username, {})
    return user.get("role", "user") == "admin"


def add_user(username: str, name: str, email: str, password: str, role: str = "user") -> tuple[bool, str]:
    """Hash password with bcrypt-12 and persist. Returns (success, error_message)."""
    try:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        config = _load_config()
        config["credentials"]["usernames"][username] = {
            "name":     name,
            "email":    email,
            "password": hashed,
            "role":     role,
        }
        _save_config(config)
        return True, ""
    except RuntimeError as e:
        return False, str(e)


def remove_user(username: str) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    try:
        config = _load_config()
        config["credentials"]["usernames"].pop(username, None)
        _save_config(config)
        return True, ""
    except RuntimeError as e:
        return False, str(e)


def change_password(username: str, new_password: str) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    try:
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        config = _load_config()
        if username in config["credentials"]["usernames"]:
            config["credentials"]["usernames"][username]["password"] = hashed
            _save_config(config)
        return True, ""
    except RuntimeError as e:
        return False, str(e)


def list_users() -> list[dict]:
    """Return user records (username, name, email, role) — never passwords."""
    config = _load_config()
    return [
        {
            "username": uname,
            "name":     data.get("name", ""),
            "email":    data.get("email", ""),
            "role":     data.get("role", "user"),
        }
        for uname, data in config["credentials"]["usernames"].items()
    ]


# ── First-run setup wizard ────────────────────────────────────────────────────

def _render_first_run_setup() -> None:
    """
    In-browser first-run setup.
    - Local mode: writes credentials.yaml and reloads.
    - Cloud mode: generates TOML and shows step-by-step Streamlit Cloud secrets instructions.
    """
    import secrets as _secrets

    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none}</style>",
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            "<div style='text-align:center; padding:40px 0 16px'>"
            "<div style='font-size:48px'>🛡️</div>"
            "<h2 style='margin:8px 0 4px'>NIST AI RMF</h2>"
            "<p style='color:#666; margin:0 0 8px'>First-time setup · Première configuration</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.info(
            "No accounts configured yet. Fill in the form to create your admin account.",
            icon="🔐",
        )

        with st.form("first_run_form"):
            username  = st.text_input("Username *",   placeholder="admin")
            name      = st.text_input("Full name *",  placeholder="Marie Tremblay")
            email     = st.text_input("Email",        placeholder="you@company.com")
            password  = st.text_input("Password *",   type="password", placeholder="Min. 8 characters")
            password2 = st.text_input("Confirm password *", type="password")
            submitted = st.form_submit_button(
                "Generate credentials →", type="primary", use_container_width=True
            )

        if submitted:
            errors = []
            if not username.strip():
                errors.append("Username is required.")
            if not name.strip():
                errors.append("Full name is required.")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters.")
            if password != password2:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                hashed     = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
                cookie_key = _secrets.token_hex(32)

                config = {
                    "credentials": {"usernames": {
                        username.strip(): {
                            "name":     name.strip(),
                            "email":    email.strip(),
                            "password": hashed,
                            "role":     "admin",
                        }
                    }},
                    "cookie": {
                        "name":        "nist_rmf_session",
                        "key":         cookie_key,
                        "expiry_days": 1,
                    },
                }

                # Try to write locally first
                local_written = False
                try:
                    _save_config(config)
                    local_written = True
                except Exception:
                    pass

                if local_written:
                    st.success(f"✓ Account **{username.strip()}** created. Reload the page to log in.")
                    st.balloons()
                else:
                    # Cloud mode — show the TOML to paste into Streamlit Cloud secrets
                    toml = (
                        f'[cookie]\n'
                        f'name = "nist_rmf_session"\n'
                        f'key = "{cookie_key}"\n'
                        f'expiry_days = 1\n\n'
                        f'[credentials.usernames.{username.strip()}]\n'
                        f'name = "{name.strip()}"\n'
                        f'email = "{email.strip()}"\n'
                        f'password = "{hashed}"\n'
                        f'role = "admin"\n'
                    )
                    st.success("✓ Credentials generated. Follow the 3 steps below to activate them.")
                    st.markdown("### How to activate (30 seconds)")
                    st.markdown(
                        "**Step 1** — Copy everything in the box below:"
                    )
                    st.code(toml, language="toml")
                    st.markdown(
                        "**Step 2** — In the Streamlit Cloud dashboard, open your app, "
                        "click the **⋮ menu** (top-right) → **Settings** → **Secrets**, "
                        "paste the text above, and click **Save**."
                    )
                    st.markdown(
                        "**Step 3** — Come back here and **reload this page**. "
                        f"Log in with username `{username.strip()}` and the password you just entered."
                    )
                    st.warning(
                        "Keep this TOML safe — it contains your hashed password. "
                        "Do not share it publicly."
                    )


# ── Login page UI ─────────────────────────────────────────────────────────────

def _render_login_page(auth: stauth.Authenticate) -> None:
    import time

    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none}</style>",
        unsafe_allow_html=True,
    )

    # ── Brute-force throttle ──────────────────────────────────────────────────
    _MAX_ATTEMPTS  = 5
    _LOCKOUT_SECS  = 30
    attempts  = st.session_state.setdefault("_login_attempts", 0)
    locked_at = st.session_state.get("_login_locked_at")

    if locked_at:
        elapsed = time.time() - locked_at
        if elapsed < _LOCKOUT_SECS:
            remaining = int(_LOCKOUT_SECS - elapsed)
            _, col, _ = st.columns([1, 2, 1])
            with col:
                st.markdown(
                    "<div style='text-align:center; padding:40px 0 24px'>"
                    "<div style='font-size:48px'>🛡️</div>"
                    "<h2 style='margin:8px 0 4px'>NIST AI RMF</h2>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.error(
                    f"Too many failed attempts. Try again in {remaining} seconds. · "
                    f"Trop de tentatives. Réessayez dans {remaining} secondes."
                )
            return
        else:
            st.session_state["_login_attempts"] = 0
            st.session_state["_login_locked_at"] = None

    # ── Login form ────────────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            "<div style='text-align:center; padding: 40px 0 24px'>"
            "<div style='font-size:48px'>🛡️</div>"
            "<h2 style='margin:8px 0 4px'>NIST AI RMF</h2>"
            "<p style='color:#666; margin:0'>Moteur de conformité IA · AI Compliance Engine</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        auth.login(location="main")

        status = st.session_state.get("authentication_status")
        if status is False:
            st.session_state["_login_attempts"] = attempts + 1
            if st.session_state["_login_attempts"] >= _MAX_ATTEMPTS:
                st.session_state["_login_locked_at"] = time.time()
                st.error(
                    f"Too many failed attempts. Login disabled for {_LOCKOUT_SECS} seconds. · "
                    f"Trop de tentatives. Connexion désactivée pendant {_LOCKOUT_SECS} secondes."
                )
            else:
                remaining_attempts = _MAX_ATTEMPTS - st.session_state["_login_attempts"]
                st.error(
                    f"Incorrect username or password. {remaining_attempts} attempt(s) remaining. · "
                    f"Identifiant ou mot de passe incorrect. {remaining_attempts} tentative(s) restante(s)."
                )
