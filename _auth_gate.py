"""Tiny helper: every page calls require_auth() at the top. If not logged in
it renders the login/signup form and stops execution.

v29: adds social login (Google / Apple / Microsoft via Streamlit's native
OIDC) + passwordless email magic-link.
v30: adds GitHub / Facebook / LINE via custom OAuth2 (configured in the
admin UI — no file editing). Falls back to email/password if none of those
are configured."""
from __future__ import annotations
import streamlit as st

import auth
import magic_link
import oauth as social_oauth
from i18n import t


# Streamlit 1.42+ ships native OIDC via st.login(). We check feature
# presence lazily so older installs still run.
def _has_native_oauth() -> bool:
    return hasattr(st, "login") and hasattr(st, "user")


def _oauth_providers_configured() -> list[str]:
    """Look at .streamlit/secrets.toml for [auth.PROVIDER] sections."""
    if not _has_native_oauth():
        return []
    out = []
    try:
        sec = st.secrets.get("auth", {})
        for k in ("google", "apple", "microsoft"):
            if isinstance(sec.get(k), dict) and sec[k].get("client_id"):
                out.append(k)
    except Exception:
        pass
    return out


def _try_consume_magic_link() -> bool:
    """If `?ml=<token>` is in the URL, verify it + log the user in.
    Returns True if a login happened — caller should st.rerun() shortly."""
    qp = st.query_params if hasattr(st, "query_params") else {}
    token = qp.get("ml") if hasattr(qp, "get") else None
    if not token:
        return False
    data = magic_link.consume(token)
    if not data:
        st.error(t("auth.magic_invalid"))
        # Strip the bad param so refresh doesn't keep failing
        try:
            del qp["ml"]
        except Exception:
            pass
        return False
    try:
        user = auth.login_or_create_email(data["email"], name=data.get("name") or "")
    except Exception as e:
        st.error(f"{type(e).__name__}: {e}")
        return False
    auth.login_user(user)
    # Wipe the token from the URL bar so it can't be replayed
    try:
        del qp["ml"]
    except Exception:
        pass
    return True


def _try_consume_social_oauth() -> bool:
    """Custom OAuth2 callback for GitHub/Facebook/LINE. URL pattern after the
    provider bounces back is `?oauth=<provider>&code=xxx&state=yyy`."""
    qp = st.query_params if hasattr(st, "query_params") else {}
    if not hasattr(qp, "get"):
        return False
    provider = qp.get("oauth")
    code = qp.get("code")
    state = qp.get("state")
    if not (provider and code and state):
        return False
    # Already logged in via this round-trip? Bail out.
    if auth.current_user():
        return False
    try:
        callback = _detect_app_url() + "/"
        profile = social_oauth.handle_callback(
            code=code, state=state, callback_url=callback,
        )
    except Exception as e:
        st.error(f"{type(e).__name__}: {e}")
        return False
    if not profile:
        st.error(t("auth.oauth_failed"))
        for k in ("oauth", "code", "state"):
            try: del qp[k]
            except Exception: pass
        return False
    try:
        user = auth.login_or_create_oauth(
            provider=profile["provider"], sub=profile["sub"],
            email=profile["email"], name=profile.get("name", ""),
            avatar=profile.get("avatar", ""),
        )
    except Exception as e:
        st.error(f"{type(e).__name__}: {e}")
        return False
    auth.login_user(user)
    # Wipe the callback params so refresh doesn't replay
    for k in ("oauth", "code", "state"):
        try: del qp[k]
        except Exception: pass
    return True


def _try_consume_oauth() -> bool:
    """Streamlit native: after a successful OAuth round-trip, st.user.is_logged_in
    is True. Translate that into our DB-backed user."""
    if not _has_native_oauth():
        return False
    try:
        u = st.user
        if not getattr(u, "is_logged_in", False):
            return False
    except Exception:
        return False
    # We already have a session user — skip
    if auth.current_user():
        return False
    try:
        provider = getattr(u, "iss", "") or ""  # provider hostname
        provider_key = "google" if "google" in provider \
                  else "apple" if "apple" in provider \
                  else "microsoft" if "microsoft" in provider \
                  else "oidc"
        user = auth.login_or_create_oauth(
            provider=provider_key,
            sub=getattr(u, "sub", "") or "",
            email=getattr(u, "email", "") or "",
            name=getattr(u, "name", "") or "",
            avatar=getattr(u, "picture", "") or "",
        )
    except Exception as e:
        st.error(f"{type(e).__name__}: {e}")
        return False
    auth.login_user(user)
    return True


def require_auth() -> dict:
    """Render login UI if user is not authenticated. Returns user dict.

    Modern minimal pattern: ONE auth mode is visible at a time. User toggles
    between login / signup / magic-link via a single text link at the bottom.
    Modes:
      • signin  — welcome-back; email + password
      • signup  — new account; email + name + password
      • magic   — passwordless; email + (optional name)
    Default mode = whichever the user last used, else 'signin' for repeat
    visitors / 'magic' for first-time."""
    user = auth.current_user()
    if user:
        return user

    auth.init()

    # Came in via magic link? OAuth callback?
    if _try_consume_magic_link():
        st.rerun()
    if _try_consume_social_oauth():
        st.rerun()
    if _try_consume_oauth():
        st.rerun()

    # Apply auth-only background + decorations. Streamlit strips <script>, so
    # instead of toggling a body class we inject a <style> block that targets
    # the live DOM directly.
    st.markdown("""
    <style>
      [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(ellipse at top, rgba(77,108,92,0.07) 0%, transparent 60%),
          linear-gradient(180deg, #faf7ef 0%, #f4f0e6 100%) !important;
      }
      header[data-testid="stHeader"] { background: transparent !important; }
      [data-testid="stDecoration"] { display: none !important; }
      [data-testid="stToolbar"] { display: none !important; }
      /* Hide sidebar on the login screen — distracting; sidebar reappears
         once authenticated. */
      section[data-testid="stSidebar"] { display: none !important; }
      [data-testid="collapsedControl"] { display: none !important; }
      /* Pull the main column up a bit since header is hidden */
      .block-container { padding-top: 2rem !important; max-width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

    providers = _oauth_providers_configured()
    social_providers = social_oauth.configured_providers()
    any_social = bool(providers or social_providers)

    # ---- Language switcher (top-right, floating) ------------------------
    _language_switcher()

    # ---- v54: Vercel-style ONE input ONE button ------------------------
    # No tabs. No mode switcher. No "what's the difference between signin/
    # signup". Just: enter email → continue. If account exists, magic link.
    # If not, account is created on first click. Password is optional later.
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # Hero — crescent + wordmark + tagline
        st.markdown(
            "<div class='nirva-auth-brand' style='margin-top:7vh'>"
            "<svg class='crescent' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg' "
            "style='width:60px;height:60px;margin-bottom:14px'>"
            "<path d='M 32 12 a 20 20 0 1 0 0 40 a 16 16 0 1 1 0 -40 z' fill='#4d6c5c'/>"
            "</svg>"
            "<div class='wordmark' style='font-size:2.4rem;font-weight:500;"
            "font-family:Cormorant Garamond,serif;letter-spacing:-0.02em'>"
            "nirva<span style='color:#4d6c5c'>.sell</span></div>"
            f"<div class='tagline' style='color:#7a7569;font-size:14px;"
            f"margin-top:6px'>{t('app.tagline')}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        # ---- The card — minimal as possible -------------------------------
        st.markdown(
            "<div class='nirva-auth-card' style='max-width:380px;margin:18px auto'>"
            f"<h1 class='nirva-auth-head' style='font-size:1.5rem;text-align:center'>"
            f"{t('auth.continue_title')}</h1>"
            f"<div class='nirva-auth-sub' style='text-align:center;margin-bottom:20px'>"
            f"{t('auth.continue_sub')}</div>",
            unsafe_allow_html=True,
        )

        # Social — primary, on top, branded big buttons
        if any_social:
            if providers:
                _provider_buttons(providers)
            if social_providers:
                _social_provider_buttons(social_providers)
            st.markdown(
                f"<div class='nirva-auth-divider' style='margin:14px 0 10px'>"
                f"<span>{t('auth.or')}</span></div>",
                unsafe_allow_html=True,
            )

        # ONE email input + ONE button — like Vercel
        _unified_form()

        # Close card
        st.markdown("</div>", unsafe_allow_html=True)

        # Compact footer
        st.markdown(
            "<div class='nirva-auth-footer' style='max-width:380px;margin:14px auto 0;"
            "text-align:center;color:#9a9485;font-size:11px;line-height:1.7'>"
            f"{t('auth.footer_agree')} "
            f"<a href='/Legal' style='color:#7a7569'>{t('legal.tab_tos')}</a> · "
            f"<a href='/Legal' style='color:#7a7569'>{t('legal.tab_privacy')}</a>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Tiny "use password instead" — hidden behind expander for power users
        with st.expander(t("auth.use_password"), expanded=False):
            _signin_form()

    # Dead code removed in v54 — Vercel minimal pattern, no tabs, no mode switcher.
    fc1, fc2, fc3 = st.columns(3)
    _feature_card_legacy = (
        "background:white;border-radius:14px;padding:22px 20px;"
    )
    with fc1:
        st.markdown(
            "<!-- features hidden in v54 minimal mode -->",
            unsafe_allow_html=True,
        )
    with fc2:
        st.markdown(
            f"<div style='{feature_card_css}'>"
            "<!-- v54 — minimal landing, no feature cards -->",
            unsafe_allow_html=True,
        )
    with fc3:
        st.markdown(
            "<!-- v54 — minimal landing, no feature cards -->",
            unsafe_allow_html=True,
        )

    st.stop()


# ---- v54: Unified "Continue with email" form -----------------------------
# Vercel-style: one email input, one button. If account exists → magic link
# sent (or password used if user provided one). If account doesn't exist →
# created on first click; magic link sent.

def _unified_form():
    with st.form("unified_form", clear_on_submit=False):
        email = st.text_input(
            t("auth.email"),
            key="unified_email",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )
        ok_click = st.form_submit_button(
            t("auth.continue_with_email"),
            type="primary", width='stretch',
        )
        if ok_click:
            if not auth.valid_email(email):
                st.error(t("auth.bad_email"))
                return
            # Throttle (same as the old magic-link form)
            allowed, wait = magic_link.throttle_check(email)
            if not allowed:
                st.warning(t("auth.magic_throttle", n=wait))
                return
            app_url = _detect_app_url()
            ok, info = magic_link.send(email, app_url=app_url)
            if ok:
                st.success(t("auth.magic_sent"))
            else:
                # SMTP not configured — show link inline for dev/test use
                if info.startswith("http"):
                    st.info(t("auth.magic_no_smtp"))
                    st.code(info)
                else:
                    st.error(info)


# ---- Per-mode forms (used inside the "use password" expander) ----------

def _signin_form():
    with st.form("signin_form", clear_on_submit=False):
        email = st.text_input(t("auth.email"), key="signin_email",
                              placeholder="you@example.com")
        pw = st.text_input(t("auth.password"), type="password",
                           key="signin_pw", placeholder="••••••••")
        ok_click = st.form_submit_button(t("auth.login_btn"),
                                          type="primary", width='stretch')
        if ok_click:
            ok, result = auth.login(email, pw)
            if ok:
                auth.login_user(result)
                st.rerun()
            else:
                st.error(result)
    # "Forgot password?" — single click switches to magic-link mode so the user
    # can recover via email without us inventing a separate reset flow.
    cf1, cf2 = st.columns([3, 2])
    with cf2:
        if st.button(t("auth.forgot_pw"), key="_forgot_pw",
                     type="tertiary", width='stretch'):
            st.session_state["auth_mode"] = "magic"
            st.toast(t("auth.forgot_pw_hint"), icon="✉")
            st.rerun()


def _signup_form():
    with st.form("signup_form", clear_on_submit=False):
        email = st.text_input(t("auth.email"), key="signup_email",
                              placeholder="you@example.com")
        name = st.text_input(t("auth.display_name"), key="signup_name",
                             placeholder=t("auth.display_name_placeholder"))
        pw = st.text_input(t("auth.password"), type="password",
                            key="signup_pw", help=t("auth.password_help"),
                            placeholder="••••••••")
        # Tiny ToS acknowledgement — required for PDPA / GDPR compliance.
        # Pre-checked so it doesn't break the happy-path; user can untick.
        agree = st.checkbox(t("auth.agree_tos"), value=True, key="signup_agree")
        ok_click = st.form_submit_button(t("auth.signup_btn"),
                                          type="primary", width='stretch')
        if ok_click:
            if not agree:
                st.error(t("auth.must_agree_tos"))
                return
            ok, msg = auth.signup(email, pw, name)
            if ok:
                # Fire-and-forget welcome email (no-ops if SMTP not configured).
                try:
                    import welcome_email
                    from i18n import current_lang
                    welcome_email.send(email, name=name or "", lang=current_lang())
                except Exception:
                    pass
                ok2, user = auth.login(email, pw)
                if ok2:
                    auth.login_user(user)
                    st.rerun()
            else:
                st.error(msg)


def _magic_form_inline():
    """Same as _magic_link_form() but without the caption header (header
    is now the mode subhead)."""
    with st.form("magic_form", clear_on_submit=False):
        m_email = st.text_input(t("auth.email"), key="magic_email",
                                placeholder="you@example.com")
        ok_click = st.form_submit_button(t("auth.magic_send"),
                                          type="primary", width='stretch')
        if ok_click:
            if not auth.valid_email(m_email):
                st.error(t("auth.bad_email"))
                return
            allowed, wait = magic_link.throttle_check(m_email)
            if not allowed:
                st.warning(t("auth.magic_throttle", n=wait))
                return
            app_url = _detect_app_url()
            ok, info = magic_link.send(m_email, app_url=app_url)
            if ok:
                st.success(t("auth.magic_sent"))
            else:
                if info.startswith("http"):
                    st.warning(t("auth.magic_no_smtp"))
                    st.code(info)
                else:
                    st.error(info)


# ---- Helpers ------------------------------------------------------------

def _switch_prompt(mode: str) -> str:
    """Prompt above the toggle buttons. Phrased like the leading platforms:
        signin → 'New to nirva?'
        signup → 'Already have an account?'
        magic  → 'Prefer a password?'"""
    return {
        "signin": t("auth.prompt_new_here"),
        "signup": t("auth.prompt_have_account"),
        "magic":  t("auth.prompt_prefer_password"),
    }.get(mode, "")


def _login_as_demo():
    try:
        import subprocess
        from pathlib import Path
        script = Path(__file__).parent / "scripts" / "seed_demo.py"
        subprocess.run(
            ["/Library/Developer/CommandLineTools/usr/bin/python3", str(script)],
            check=False, capture_output=True, timeout=30,
        )
    except Exception:
        pass
    ok, user = auth.login("demo@nirva.sell", "demopass123")
    if ok:
        auth.login_user(user)
        st.rerun()
    else:
        st.error(t("auth.demo_unavailable"))


# ---- Sub-components ----------------------------------------------------

_PROVIDER_META = {
    "google":    {"label": "Google",    "icon": "🇬",  "color": "#4285f4"},
    "apple":     {"label": "Apple ID",  "icon": "",  "color": "#000000"},
    "microsoft": {"label": "Microsoft", "icon": "Ⓜ", "color": "#0078d4"},
}


def _provider_buttons(providers: list[str]):
    """Native-OIDC buttons (Google / Apple / Microsoft via st.login())."""
    for p in providers:
        meta = _PROVIDER_META.get(p, {"label": p.title(), "icon": "🔑", "color": "#444"})
        label = f"{meta['icon']} {t('auth.signin_with').format(provider=meta['label'])}"
        if st.button(label, key=f"oauth_{p}", width='stretch'):
            try:
                st.login(p)
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")


def _social_provider_buttons(providers: list[str]):
    """Custom OAuth2 buttons (GitHub / Facebook / LINE) — config in admin UI."""
    callback = _detect_app_url() + "/"
    for p in providers:
        meta = social_oauth.PROVIDERS.get(p, {})
        icon = meta.get("icon", "🔑")
        label_text = meta.get("label", p.title())
        label = f"{icon} {t('auth.signin_with').format(provider=label_text)}"
        url = social_oauth.authorize_url(p, callback)
        if not url:
            continue
        # st.link_button renders as a link tag so the browser does a real
        # top-level navigation (required by OAuth — popups won't work).
        st.link_button(label, url, width='stretch')


def _magic_link_form():
    st.caption(t("auth.magic_help"))
    with st.form("magic_form", clear_on_submit=False):
        m_email = st.text_input(t("auth.email"), key="magic_email")
        m_name = st.text_input(t("auth.display_name_optional"), key="magic_name")
        submitted = st.form_submit_button(t("auth.magic_send"),
                                           type="primary", width='stretch')
        if submitted:
            if not auth.valid_email(m_email):
                st.error(t("auth.bad_email"))
                return
            allowed, wait = magic_link.throttle_check(m_email)
            if not allowed:
                st.warning(t("auth.magic_throttle", n=wait))
                return
            app_url = _detect_app_url()
            ok, info = magic_link.send(m_email, app_url=app_url, name=m_name or "")
            if ok:
                st.success(t("auth.magic_sent"))
            else:
                # SMTP not configured — show the link inline so dev users
                # can still log in. Production deploys should configure SMTP.
                if info.startswith("http"):
                    st.warning(t("auth.magic_no_smtp"))
                    st.code(info)
                else:
                    st.error(info)


def _detect_app_url() -> str:
    """Best-effort: env override > sensible localhost default."""
    import os
    return (os.getenv("APP_URL", "") or "http://localhost:8501").rstrip("/")


# ---- v36: Language switcher + email-provider hint ----------------------

def _language_switcher():
    """Floating language picker, top-right. Sidebar is hidden on the auth
    screen, so users wouldn't otherwise have a way to switch language."""
    from i18n import LANGS, current_lang
    cur = current_lang()
    # Native flag-ish labels — visually scannable in the dropdown
    flags = {
        # SEA
        "th": "🇹🇭", "vi": "🇻🇳", "id": "🇮🇩", "ms": "🇲🇾", "tl": "🇵🇭",
        "my": "🇲🇲", "km": "🇰🇭", "lo": "🇱🇦",
        # East Asia
        "zh": "🇨🇳", "ja": "🇯🇵", "ko": "🇰🇷",
        # Global
        "en": "🇬🇧", "es": "🇪🇸", "fr": "🇫🇷", "pt": "🇵🇹", "de": "🇩🇪",
        "ar": "🇸🇦", "hi": "🇮🇳", "ru": "🇷🇺",
    }
    options = list(LANGS.keys())
    labels = {k: f"{flags.get(k, '')} {LANGS[k]}" for k in options}

    # Lay out a thin row at the top with a small selectbox on the right.
    # Streamlit doesn't let us absolutely-position widgets easily, so we use
    # columns to push the selector right.
    cL, _, cR = st.columns([6, 6, 2])
    with cR:
        choice = st.selectbox(
            label="lang", label_visibility="collapsed",
            options=options,
            index=options.index(cur) if cur in options else 0,
            format_func=lambda k: labels[k],
            key="_auth_lang_picker",
        )
        if choice != cur:
            st.session_state["lang"] = choice
            # Persist to user_settings so it survives login (best-effort —
            # no-op pre-login since no user DB exists yet).
            try:
                import user_settings as us
                us.set("lang", choice)
            except Exception:
                pass
            st.rerun()


def _email_provider_hint():
    """When no OAuth providers are configured, surface a friendly row that
    tells the user 'magic-link works with any email — Gmail, Outlook, iCloud,
    Yahoo'. Builds trust without faking OAuth buttons that don't work."""
    badges = [
        ("Gmail",    "#ea4335"),
        ("Outlook",  "#0078d4"),
        ("iCloud",   "#1f1f1f"),
        ("Yahoo",    "#6001d2"),
    ]
    chips = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:4px;"
        f"padding:4px 10px;border-radius:999px;background:white;"
        f"border:1px solid rgba(40,30,20,0.08);font-size:12px;"
        f"font-weight:500;color:{color};margin:2px 3px'>"
        f"<span style='width:6px;height:6px;border-radius:50%;background:{color}'></span>"
        f"{name}</span>"
        for name, color in badges
    )
    st.markdown(
        "<div style='text-align:center;margin:0 0 22px;padding:14px 16px;"
        "background:rgba(77,108,92,0.04);border-radius:10px;"
        "border:1px dashed rgba(77,108,92,0.18)'>"
        f"<div style='color:#4a4a4a;font-size:13px;margin-bottom:8px;"
        f"font-weight:500'>{t('auth.email_works_with')}</div>"
        f"<div>{chips}</div>"
        f"<div style='color:#9a9485;font-size:11px;margin-top:8px;"
        f"line-height:1.5'>{t('auth.email_no_oauth_needed')}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
