import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth import require_login, is_admin, is_cloud_mode, add_user, remove_user, change_password, list_users
from sidebar import render_sidebar

st.set_page_config(
    page_title="Admin — NIST AI RMF",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

require_login()
render_sidebar()

if not is_admin():
    st.error("⛔ Accès refusé — cette page est réservée aux administrateurs.")
    st.stop()

st.title("⚙️ Administration — Gestion des utilisateurs")
st.caption("Seuls les comptes avec le rôle **admin** peuvent accéder à cette page.")

if is_cloud_mode():
    st.warning(
        "**Mode Streamlit Cloud détecté.** Les modifications effectuées ici ne seront pas "
        "sauvegardées — les credentials sont gérés via les Secrets Streamlit Cloud. "
        "Pour ajouter ou modifier un utilisateur, mettez à jour le TOML dans "
        "**⋮ → Settings → Secrets** sur le tableau de bord Streamlit Cloud.\n\n"
        "**Streamlit Cloud mode detected.** Changes made here will not be saved — "
        "credentials are managed via Streamlit Cloud Secrets. To add or change a user, "
        "update the TOML in **⋮ → Settings → Secrets** on the Streamlit Cloud dashboard.",
        icon="☁️",
    )

st.divider()

# ── Current users ──────────────────────────────────────────────────────────────
st.subheader("👥 Utilisateurs actuels")

users = list_users()
if users:
    for u in users:
        role_badge = "🔑 admin" if u["role"] == "admin" else "👤 user"
        with st.container(border=True):
            col_info, col_actions = st.columns([4, 2])
            with col_info:
                st.markdown(f"**{u['name']}** (`{u['username']}`)")
                st.caption(f"{u['email']}  ·  {role_badge}")
            with col_actions:
                if u["username"] != st.session_state.get("username"):
                    if st.button(
                        "🗑️ Supprimer",
                        key=f"del_{u['username']}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        ok, err = remove_user(u["username"])
                        if ok:
                            st.success(f"Utilisateur **{u['username']}** supprimé.")
                            st.rerun()
                        else:
                            st.error(err)
                else:
                    st.caption("*(compte actif)*")
else:
    st.info("Aucun utilisateur.")

st.divider()

# ── Add user ───────────────────────────────────────────────────────────────────
st.subheader("➕ Ajouter un utilisateur")
st.caption("Le mot de passe est haché avec bcrypt (coût 12) avant d'être enregistré.")

with st.form("add_user_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        new_username  = st.text_input("Nom d'utilisateur *", placeholder="ex. : client_acme")
        new_name      = st.text_input("Nom complet *",       placeholder="ex. : Marie Tremblay")
        new_email     = st.text_input("Courriel",            placeholder="marie@acme.com")
    with col2:
        new_password  = st.text_input("Mot de passe *", type="password", placeholder="Min. 8 caractères")
        new_password2 = st.text_input("Confirmer le mot de passe *", type="password")
        new_role      = st.selectbox("Rôle", ["user", "admin"])

    submitted = st.form_submit_button("Créer l'utilisateur", type="primary", use_container_width=True)

if submitted:
    errors = []
    if not new_username.strip():
        errors.append("Le nom d'utilisateur est requis.")
    elif any(u["username"] == new_username.strip() for u in users):
        errors.append(f"Le nom d'utilisateur **{new_username}** existe déjà.")
    if not new_name.strip():
        errors.append("Le nom complet est requis.")
    if len(new_password) < 8:
        errors.append("Le mot de passe doit comporter au moins 8 caractères.")
    if new_password != new_password2:
        errors.append("Les mots de passe ne correspondent pas.")
    # Guard against obvious weak passwords
    if new_password.lower() in ("password", "password123", "12345678", "admin123", "demo1234"):
        errors.append("Mot de passe trop simple — choisissez-en un plus fort.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        ok, err = add_user(new_username.strip(), new_name.strip(), new_email.strip(), new_password, new_role)
        if ok:
            st.success(f"✓ Utilisateur **{new_username}** créé avec le rôle **{new_role}**.")
            st.rerun()
        else:
            st.error(err)

st.divider()

# ── Change password ────────────────────────────────────────────────────────────
st.subheader("🔑 Réinitialiser un mot de passe")

with st.form("change_pw_form", clear_on_submit=True):
    target_user  = st.selectbox("Utilisateur", [u["username"] for u in users])
    new_pw       = st.text_input("Nouveau mot de passe *", type="password", placeholder="Min. 8 caractères")
    new_pw2      = st.text_input("Confirmer *",            type="password")
    pw_submitted = st.form_submit_button("Réinitialiser", type="secondary", use_container_width=True)

if pw_submitted:
    if len(new_pw) < 8:
        st.error("Le mot de passe doit comporter au moins 8 caractères.")
    elif new_pw != new_pw2:
        st.error("Les mots de passe ne correspondent pas.")
    else:
        ok, err = change_password(target_user, new_pw)
        if ok:
            st.success(f"✓ Mot de passe de **{target_user}** réinitialisé.")
        else:
            st.error(err)
