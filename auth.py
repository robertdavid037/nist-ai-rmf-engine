"""
auth.py — Authentication utilities for the NIST AI RMF Compliance Engine.

Credentials live at ~/.config/nist-rmf/credentials.yaml (outside the repo).
Override the path with the RMF_CREDENTIALS_PATH environment variable.
Run scripts/setup_auth.py once to create the file.
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

def _load_config() -> dict:
    with open(CREDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_config(config: dict) -> None:
    """Write config and immediately re-apply 600 permissions."""
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
        auto_hash=False,  # passwords are pre-hashed by setup_auth.py / add_user()
    )


# ── Public API ────────────────────────────────────────────────────────────────

def require_login() -> str:
    """
    Call at the top of every page.
    Returns the authenticated username, or renders the login/setup form and stops.
    """
    if not os.path.exists(CREDS_PATH):
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


def add_user(username: str, name: str, email: str, password: str, role: str = "user") -> None:
    """Hash the password with bcrypt-12 and persist the new user to credentials.yaml."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    config = _load_config()
    config["credentials"]["usernames"][username] = {
        "name":     name,
        "email":    email,
        "password": hashed,
        "role":     role,
    }
    _save_config(config)


def remove_user(username: str) -> None:
    config = _load_config()
    config["credentials"]["usernames"].pop(username, None)
    _save_config(config)


def change_password(username: str, new_password: str) -> None:
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    config = _load_config()
    if username in config["credentials"]["usernames"]:
        config["credentials"]["usernames"][username]["password"] = hashed
        _save_config(config)


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
    """In-browser first-run setup — shown when no credentials file exists yet."""
    import secrets as _secrets

    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none}</style>",
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            "<div style='text-align:center; padding:40px 0 8px'>"
            "<div style='font-size:48px'>🛡️</div>"
            "<h2 style='margin:8px 0 4px'>NIST AI RMF</h2>"
            "<p style='color:#666; margin:0 0 8px'>Première configuration · First-time setup</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.info(
            "Aucun compte trouvé. Créez votre compte administrateur ci-dessous.\n\n"
            "No accounts found. Create your admin account below.",
            icon="🔐",
        )

        with st.form("first_run_form"):
            username  = st.text_input("Nom d'utilisateur · Username *", placeholder="admin")
            name      = st.text_input("Nom complet · Full name *",      placeholder="Marie Tremblay")
            email     = st.text_input("Courriel · Email",               placeholder="marie@example.com")
            password  = st.text_input("Mot de passe · Password *",      type="password",
                                      placeholder="Min. 8 characters")
            password2 = st.text_input("Confirmer · Confirm *",          type="password")
            submitted = st.form_submit_button(
                "Créer le compte et continuer →", type="primary", use_container_width=True
            )

        if submitted:
            errors = []
            if not username.strip():
                errors.append("Le nom d'utilisateur est requis. · Username is required.")
            if not name.strip():
                errors.append("Le nom complet est requis. · Full name is required.")
            if len(password) < 8:
                errors.append("Le mot de passe doit comporter au moins 8 caractères. · Min. 8 characters.")
            if password != password2:
                errors.append("Les mots de passe ne correspondent pas. · Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                hashed     = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
                cookie_key = _secrets.token_hex(32)  # 256-bit random secret

                config = {
                    "credentials": {
                        "usernames": {
                            username.strip(): {
                                "name":     name.strip(),
                                "email":    email.strip(),
                                "password": hashed,
                                "role":     "admin",
                            }
                        }
                    },
                    "cookie": {
                        "name":        "nist_rmf_session",
                        "key":         cookie_key,
                        "expiry_days": 1,
                    },
                }

                creds_dir = os.path.dirname(CREDS_PATH)
                if creds_dir:
                    os.makedirs(creds_dir, mode=0o700, exist_ok=True)
                _save_config(config)

                st.success(
                    f"✓ Compte **{username.strip()}** créé. Rechargez la page pour vous connecter.\n\n"
                    f"✓ Account **{username.strip()}** created. Reload the page to log in."
                )
                st.balloons()


# ── Login page UI ─────────────────────────────────────────────────────────────

def _render_login_page(auth: stauth.Authenticate) -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
            st.error("Identifiant ou mot de passe incorrect. · Incorrect username or password.")
