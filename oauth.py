"""Custom OAuth2 client for providers that don't fit Streamlit's native OIDC
(`st.login()`). Supports GitHub, Facebook, and LINE — the three providers
most popular outside the Google/Apple/Microsoft trio that Streamlit handles
natively.

Why a separate module?
  • Streamlit native OAuth needs secrets.toml + restart — annoying for admins
  • These providers stash config in `user_settings` so admins can paste
    client_id/secret in the UI and the button appears instantly
  • State signed with the magic-link HMAC secret — no DB table needed

The flow:
  1. User clicks "Sign in with GitHub" on the login page
  2. We mint a signed `state` token, redirect them to GitHub's authorize URL
  3. GitHub bounces back to ?oauth=github&code=xxx&state=yyy
  4. _auth_gate.py reads those params, validates `state`, exchanges `code`
     for an access token, fetches the user's profile, calls
     auth.login_or_create_oauth() → done.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlencode

import httpx

import user_settings as us
import magic_link  # for the HMAC secret


# ---- Provider catalog ---------------------------------------------------

# Each provider needs: client_id, client_secret. Endpoints + scopes are
# fixed per-provider and live here. To add a new OAuth2 provider, add an
# entry below and it shows up in admin UI + login automatically.

PROVIDERS = {
    "google": {
        "icon":           "🇬",
        "color":          "#4285f4",
        "authorize":      "https://accounts.google.com/o/oauth2/v2/auth",
        "token":          "https://oauth2.googleapis.com/token",
        "userinfo":       "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope":          "openid email profile",
        "setup_url":      "https://console.cloud.google.com/apis/credentials",
        "setup_hint":     "Create OAuth client → Web app → paste the callback URL below as the Authorized redirect URI",
    },
    "microsoft": {
        "icon":           "Ⓜ",
        "color":          "#0078d4",
        # `common` lets any Microsoft account (work / school / personal) log in.
        "authorize":      "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token":          "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo":       "https://graph.microsoft.com/v1.0/me",
        "scope":          "openid email profile User.Read",
        "setup_url":      "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
        "setup_hint":     "App registrations → New → Redirect URI (Web) = the callback URL below → Certificates & secrets → New client secret",
    },
    "github": {
        "icon":           "🐙",
        "color":          "#24292e",
        "authorize":      "https://github.com/login/oauth/authorize",
        "token":          "https://github.com/login/oauth/access_token",
        "userinfo":       "https://api.github.com/user",
        "userinfo_email": "https://api.github.com/user/emails",
        "scope":          "read:user user:email",
        "setup_url":      "https://github.com/settings/developers",
        "setup_hint":     "New OAuth App → Authorization callback URL = the URL below",
    },
    "facebook": {
        "icon":           "📘",
        "color":          "#1877f2",
        "authorize":      "https://www.facebook.com/v18.0/dialog/oauth",
        "token":          "https://graph.facebook.com/v18.0/oauth/access_token",
        "userinfo":       "https://graph.facebook.com/me?fields=id,name,email,picture",
        "scope":          "email public_profile",
        "setup_url":      "https://developers.facebook.com/apps/",
        "setup_hint":     "Create app → Facebook Login → Settings → Valid OAuth Redirect URIs = the URL below",
    },
    "line": {
        "icon":           "💚",
        "color":          "#06c755",
        "authorize":      "https://access.line.me/oauth2/v2.1/authorize",
        "token":          "https://api.line.me/oauth2/v2.1/token",
        "userinfo":       "https://api.line.me/v2/profile",
        "scope":          "profile openid email",
        "setup_url":      "https://developers.line.biz/console/",
        "setup_hint":     "Create LINE Login channel → Callback URL = the URL below",
    },
}


# ---- Config storage (per-admin, via user_settings) ----------------------

def get_config(provider: str) -> dict:
    """Return the saved client_id / client_secret for a provider."""
    return {
        "client_id":     us.get(f"oauth.{provider}.client_id", "") or "",
        "client_secret": us.get(f"oauth.{provider}.client_secret", "") or "",
    }


def set_config(provider: str, client_id: str, client_secret: str) -> None:
    us.set(f"oauth.{provider}.client_id", (client_id or "").strip())
    us.set(f"oauth.{provider}.client_secret", (client_secret or "").strip())


def configured_providers() -> list[str]:
    """Which providers have valid config and can show login buttons?"""
    out = []
    for key in PROVIDERS:
        cfg = get_config(key)
        if cfg["client_id"] and cfg["client_secret"]:
            out.append(key)
    return out


# ---- State token (CSRF protection) --------------------------------------
# Reuses the magic-link HMAC secret so we don't manage another key.

_STATE_TTL = 600  # 10 min


def _mint_state(provider: str) -> str:
    payload = json.dumps({
        "p":     provider,
        "exp":   int(time.time()) + _STATE_TTL,
        "nonce": secrets.token_hex(8),
    }, separators=(",", ":")).encode()
    sig = hmac.new(magic_link._get_secret(), payload, hashlib.sha256).digest()
    return (base64.urlsafe_b64encode(payload).rstrip(b"=").decode() + "."
            + base64.urlsafe_b64encode(sig).rstrip(b"=").decode())


def _verify_state(token: str) -> str | None:
    """Returns the provider name if valid, else None."""
    try:
        p_b64, s_b64 = token.split(".")
        payload = base64.urlsafe_b64decode(p_b64 + "=" * (-len(p_b64) % 4))
        sig = base64.urlsafe_b64decode(s_b64 + "=" * (-len(s_b64) % 4))
    except Exception:
        return None
    expected = hmac.new(magic_link._get_secret(), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(payload.decode())
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    return data.get("p")


# ---- Authorize URL builder ----------------------------------------------

def authorize_url(provider: str, callback_url: str) -> str | None:
    """Build the URL to redirect the user to for the OAuth dance."""
    p = PROVIDERS.get(provider)
    cfg = get_config(provider)
    if not p or not cfg["client_id"]:
        return None
    state = _mint_state(provider)
    params = {
        "client_id":     cfg["client_id"],
        "redirect_uri":  callback_url,
        "scope":         p["scope"],
        "response_type": "code",
        "state":         state,
    }
    return p["authorize"] + "?" + urlencode(params)


# ---- Callback handler — exchanges code → user info ----------------------

def handle_callback(*, code: str, state: str, callback_url: str) -> dict | None:
    """Returns {provider, sub, email, name, avatar} on success, None on fail.
    Caller passes the result to auth.login_or_create_oauth()."""
    provider = _verify_state(state)
    if not provider:
        return None
    p = PROVIDERS.get(provider)
    cfg = get_config(provider)
    if not p or not cfg["client_id"]:
        return None

    # ----- Step 1: exchange the code for an access_token -----
    token_payload = {
        "client_id":     cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code":          code,
        "redirect_uri":  callback_url,
        "grant_type":    "authorization_code",
    }
    try:
        r = httpx.post(
            p["token"],
            data=token_payload,
            headers={"Accept": "application/json"},
            timeout=15,
        )
    except Exception:
        return None
    if not r.is_success:
        return None
    try:
        tok = r.json()
    except Exception:
        return None
    access_token = tok.get("access_token")
    if not access_token:
        return None

    # ----- Step 2: fetch the user's profile -----
    headers = {"Authorization": f"Bearer {access_token}",
               "Accept": "application/json"}
    try:
        r = httpx.get(p["userinfo"], headers=headers, timeout=15)
    except Exception:
        return None
    if not r.is_success:
        return None
    info = r.json()

    return _normalize_profile(provider, info, access_token, headers)


def _normalize_profile(provider: str, info: dict, access_token: str,
                       headers: dict) -> dict | None:
    """Translate each provider's idiosyncratic profile shape into a common
    dict: {provider, sub, email, name, avatar}."""
    if provider == "google":
        sub = str(info.get("sub", ""))
        email = info.get("email", "") if info.get("email_verified", True) else ""
        name = info.get("name", "") or info.get("given_name", "")
        avatar = info.get("picture", "") or ""
        if not (sub and email):
            return None
        return {"provider": "google", "sub": sub, "email": email,
                "name": name, "avatar": avatar}

    if provider == "microsoft":
        sub = str(info.get("id", ""))
        # MS returns 'mail' for AAD work accounts, 'userPrincipalName' for personal
        email = info.get("mail") or info.get("userPrincipalName") or ""
        name = info.get("displayName") or info.get("givenName") or ""
        avatar = ""  # MS Graph requires a separate /me/photo call; skip for now
        if not (sub and email):
            return None
        return {"provider": "microsoft", "sub": sub, "email": email,
                "name": name, "avatar": avatar}

    if provider == "github":
        sub = str(info.get("id", ""))
        name = info.get("name") or info.get("login") or ""
        avatar = info.get("avatar_url") or ""
        email = info.get("email") or ""
        # GitHub hides the primary email behind the /user/emails endpoint if
        # the user marked it private. Fetch it explicitly.
        if not email:
            try:
                r = httpx.get(PROVIDERS["github"]["userinfo_email"],
                              headers=headers, timeout=10)
                if r.is_success:
                    for e in r.json():
                        if e.get("primary") and e.get("verified"):
                            email = e.get("email", "")
                            break
                    if not email:
                        # Fall back to any verified email
                        for e in r.json():
                            if e.get("verified"):
                                email = e.get("email", "")
                                break
            except Exception:
                pass
        if not (sub and email):
            return None
        return {"provider": "github", "sub": sub, "email": email,
                "name": name, "avatar": avatar}

    if provider == "facebook":
        sub = str(info.get("id", ""))
        email = info.get("email") or ""
        name = info.get("name", "")
        avatar = (info.get("picture", {}) or {}).get("data", {}).get("url", "")
        if not (sub and email):
            # FB users can withhold email — caller surfaces the error
            return None
        return {"provider": "facebook", "sub": sub, "email": email,
                "name": name, "avatar": avatar}

    if provider == "line":
        # LINE returns userId/displayName/pictureUrl; email is in the id_token
        # if we requested the openid scope. Best-effort.
        sub = info.get("userId") or ""
        name = info.get("displayName") or ""
        avatar = info.get("pictureUrl") or ""
        email = ""
        # LINE doesn't always return email — use a placeholder so the account
        # can still link to a magic-link user later by their actual email.
        if not email and sub:
            email = f"{sub}@line.local"  # synthetic; user can change later
        if not sub:
            return None
        return {"provider": "line", "sub": sub, "email": email,
                "name": name, "avatar": avatar}

    return None
