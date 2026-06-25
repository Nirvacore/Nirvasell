"""Shared sidebar — call render() once at top of every page."""
from __future__ import annotations
import os
import streamlit as st

import db
import fees as fees_mod
import auth
from i18n import LANGS, DEFAULT_LANG, t
from i18n_inline import currency_label


def render():
    # Initialize language. Order: query param > session state > default.
    try:
        url_lang = st.query_params.get("lang")
        if url_lang and url_lang in LANGS and url_lang != st.session_state.get("lang"):
            st.session_state["lang"] = url_lang
    except Exception:
        pass
    if "lang" not in st.session_state:
        st.session_state["lang"] = DEFAULT_LANG

    with st.sidebar:
        # Brand — crescent SVG mark + wordmark
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;margin:6px 0 2px'>"
            "<svg width='28' height='28' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'>"
            "<path d='M 32 14 a 18 18 0 1 0 0 36 a 14 14 0 1 1 0 -36 z' fill='#4d6c5c'/>"
            "</svg>"
            "<div style='font-family:Inter,sans-serif;font-size:20px;"
            "font-weight:600;letter-spacing:-0.02em'>"
            "nirva<span style='color:#4d6c5c'>.sell</span></div>"
            "</div>"
            f"<div style='color:#7e7e8c;font-size:12px;margin-bottom:14px;padding-left:38px'>{t('app.tagline')}</div>",
            unsafe_allow_html=True,
        )

        # ---- Spotlight search (Cmd+K) — v48 --------------------------
        # Visible button + JS that triggers it on ⌘K. World-class pattern
        # from Stripe / Linear / Notion / GitHub.
        try:
            import _spotlight
            _spotlight.render_button()
            _spotlight.maybe_render_dialog()
        except Exception:
            pass

        # ---- Current user chip ----------------------------------------
        # Avatar (from OAuth) + name + tiny role badge. Logout sits as a
        # link below — less prominent than a button, more like SaaS apps.
        u = auth.current_user()
        if u:
            avatar = u.get("avatar_url") or ""
            initial = (u.get("display_name") or u["email"])[0].upper()
            avatar_html = (
                f"<img src='{avatar}' alt='' style='width:36px;height:36px;"
                f"border-radius:50%;object-fit:cover'/>"
                if avatar else
                f"<div style='width:36px;height:36px;border-radius:50%;"
                f"background:#4d6c5c;color:white;display:flex;align-items:center;"
                f"justify-content:center;font-weight:600;font-size:15px;"
                f"font-family:Cormorant Garamond,serif'>{initial}</div>"
            )
            role_chip = (
                "<span style='display:inline-block;padding:1px 7px;border-radius:8px;"
                "background:rgba(77,108,92,0.10);color:#4d6c5c;font-size:10px;"
                "font-weight:600;letter-spacing:0.04em;margin-left:6px'>ADMIN</span>"
                if u.get("role") == "admin" else ""
            )
            st.markdown(
                "<div style='display:flex;align-items:center;gap:10px;"
                "padding:10px 0 4px;border-bottom:1px solid rgba(0,0,0,0.06);"
                "margin-bottom:12px'>"
                f"{avatar_html}"
                "<div style='min-width:0;flex:1'>"
                "<div style='color:#1f1f1f;font-size:13px;font-weight:500;"
                "white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>"
                f"{u.get('display_name') or u['email'].split('@')[0]}{role_chip}</div>"
                "<div style='color:#9a9485;font-size:11px;"
                "white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>"
                f"{u['email']}</div>"
                "</div></div>",
                unsafe_allow_html=True,
            )
            if st.button(f"↪ {t('auth.logout')}", key="_logout_btn",
                         type="tertiary", width='stretch'):
                auth.logout()
                st.rerun()

        # ---- Language switcher (always visible) ----------------------
        lang_codes = list(LANGS.keys())
        cur_idx = lang_codes.index(st.session_state.get("lang", DEFAULT_LANG))
        flags = {
            # SEA
            "th":"🇹🇭","vi":"🇻🇳","id":"🇮🇩","ms":"🇲🇾","tl":"🇵🇭",
            "my":"🇲🇲","km":"🇰🇭","lo":"🇱🇦",
            # East Asia
            "zh":"🇨🇳","ja":"🇯🇵","ko":"🇰🇷",
            # Global
            "en":"🇬🇧","es":"🇪🇸","fr":"🇫🇷","pt":"🇵🇹","de":"🇩🇪",
            "ar":"🇸🇦","hi":"🇮🇳","ru":"🇷🇺",
        }
        sel = st.selectbox(
            t("sidebar.lang"),
            lang_codes,
            index=cur_idx,
            format_func=lambda c: f"{flags.get(c,'')} {LANGS[c]}",
            key="_lang_select",
            label_visibility="collapsed",
        )
        if sel != st.session_state["lang"]:
            st.session_state["lang"] = sel
            st.rerun()

        # ---- Auto-translate UI to current language (v45) -------------
        # Show this row only when the current language has incomplete coverage
        # and the user has a Claude API key. One click → batch translate
        # every missing string → cache → reload.
        try:
            import auto_translate as _at
            _cov = _at.coverage(sel)
            if (_cov["percent"] < 95
                    and st.session_state.get("api_key")
                    and sel != "en" and sel != DEFAULT_LANG):
                if st.button(
                    f"🌐 {t('sidebar.translate_ui', n=_cov['percent'])}",
                    key="_translate_ui_btn",
                    type="tertiary",
                    width='stretch',
                ):
                    with st.spinner(t("sidebar.translating")):
                        # No progress callback inside the spinner — Streamlit
                        # re-renders the whole sidebar each step which loops.
                        _at.translate_language(
                            sel,
                            api_key=st.session_state["api_key"],
                        )
                    st.rerun()
        except Exception:
            pass

        # ---- Settings (collapsed — user configures once) -------------
        # Persistent API key: load from user DB on first paint, persist on change.
        persistent_key = ""
        if auth.current_user():
            try:
                import user_settings as us
                persistent_key = us.get("anthropic_api_key", "") or ""
            except Exception:
                pass

        # Default to expanded if API key isn't set yet — guides new users.
        has_key = bool(st.session_state.get("api_key") or persistent_key)
        with st.expander(f"⚙ {t('sidebar.settings')}", expanded=not has_key):
            api_key = st.text_input(
                t("sidebar.api_key"),
                value=st.session_state.get("api_key") or persistent_key or os.getenv("ANTHROPIC_API_KEY", ""),
                type="password",
                help=t("sidebar.api_help"),
                key="_api_key_input",
            )
            st.session_state["api_key"] = api_key

            # Save key to user DB when it changes — survives refresh + logout/login.
            if auth.current_user() and api_key and api_key != persistent_key:
                try:
                    import user_settings as us
                    us.set("anthropic_api_key", api_key)
                except Exception:
                    pass

            markup = st.slider(
                t("sidebar.markup"), 0, 100,
                st.session_state.get("markup", 15), 1,
                key="_markup_input",
            )
            st.session_state["markup"] = markup

            round_opts = [1, 5, 10, 50, 100]
            round_to = st.selectbox(
                t("sidebar.round_to"),
                round_opts,
                index=round_opts.index(st.session_state.get("round_to", 10)),
                key="_round_to_input",
            )
            st.session_state["round_to"] = round_to

        # Currency selector — display only (DB always stores THB).
        currencies = list(fees_mod.FX_RATES_VS_THB.keys())
        currency = st.selectbox(
            t("sidebar.currency"),
            currencies,
            index=currencies.index(st.session_state.get("currency", "THB")),
            format_func=lambda c: f"{c} · {currency_label(c)}",
            key="_currency_input",
        )
        st.session_state["currency"] = currency

        st.markdown(
            "<hr style='margin:14px 0 10px;border-color:rgba(255,255,255,0.04)'>",
            unsafe_allow_html=True,
        )
        s = db.stats()
        c1, c2 = st.columns(2)
        c1.metric(t("sidebar.stat_products"), s["products"])
        c2.metric(t("sidebar.stat_content"), s["content_total"])

        # Upcoming sale countdown — quiet, just a chip
        try:
            import live_data
            nxt = live_data.next_big_sale()
            if nxt and nxt["days_until"] <= 60:
                from i18n_inline import live_promo_label
                label = live_promo_label(nxt.get("slug", ""))
                st.markdown(
                    "<div style='margin-top:14px;padding:10px 12px;"
                    "background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.25);"
                    "border-radius:8px'>"
                    f"<div style='color:#7e7e8c;font-size:11px;text-transform:uppercase;"
                    f"letter-spacing:0.05em'>⏰ {t('live.next_event')}</div>"
                    f"<div style='color:#1f1f1f;font-weight:600;font-size:14px;margin-top:2px'>"
                    f"{label}</div>"
                    f"<div style='color:#6b6b6b;font-size:12px;margin-top:1px'>"
                    f"{t('live.in_n_days', n=nxt['days_until'])}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

        # ---- Footer: legal links + contact (production-ready essentials) ----
        try:
            import legal
            info = legal.get_contact()
            email_line = (
                f"<div style='margin-top:4px'>📧 <a href='mailto:{info['email']}' "
                f"style='color:#6b6b6b;text-decoration:none'>{info['email']}</a></div>"
                if info.get("email") else ""
            )
            line_line = (
                f"<div>💚 LINE: {info['line_id']}</div>"
                if info.get("line_id") else ""
            )
            st.markdown(
                "<div style='position:relative;margin-top:18px;padding-top:14px;"
                "border-top:1px solid rgba(0,0,0,0.06);color:#9a9a9a;font-size:11px;"
                "line-height:1.6'>"
                f"<a href='/Legal' target='_self' style='color:#6b6b6b;"
                f"text-decoration:none'>{t('legal.tab_tos')}</a> · "
                f"<a href='/Legal' target='_self' style='color:#6b6b6b;"
                f"text-decoration:none'>{t('legal.tab_privacy')}</a>"
                f"{email_line}{line_line}"
                "<div style='margin-top:6px;color:#aaa'>© nirva.sell · MIT</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        except Exception:
            pass
