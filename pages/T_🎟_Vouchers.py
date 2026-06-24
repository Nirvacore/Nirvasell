"""Voucher Studio — design promo codes once, export per-platform CSV.

Steals the best parts of Shopee's voucher center + Lazada's voucher wallet
+ TikTok's promotion tool: festival templates, multi-platform output,
auto-suggested codes, visual status (active / scheduled / expired)."""
from __future__ import annotations
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import vouchers as v
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, toast, friendly_error
from i18n import t
from i18n_inline import voucher_tpl_label

_VOUCHER_TYPES = {
    "percent": "vouch.type_percent",
    "fixed": "vouch.type_fixed",
    "shipping": "vouch.type_shipping",
}

st.set_page_config(page_title="nirva.sell · Voucher Studio",
                   page_icon="🎟", layout="wide")
apply_theme()
require_auth()
db.init()
v.init()
render_sidebar()

page_header(icon="🎟", title=t("vouch.title"), subtitle=t("vouch.caption"))


STATUS_COLORS = {
    "active":    "#4d6c5c",
    "scheduled": "#c5963d",
    "expired":   "#c54c4c",
    "paused":    "#7a7569",
}
STATUS_ICONS = {
    "active":    "✓",
    "scheduled": "🕐",
    "expired":   "✕",
    "paused":    "⏸",
}


# ---- Festival templates (top of page) ----------------------------------
st.markdown(f"### {t('vouch.templates_title')}")
st.caption(t("vouch.templates_caption"))

template_keys = list(v.TEMPLATES.keys())
template_cols = st.columns(min(len(template_keys), 4))
for i, tk in enumerate(template_keys):
    tpl = v.TEMPLATES[tk]
    with template_cols[i % len(template_cols)]:
        if st.button(
            f"{tpl['icon']}  {voucher_tpl_label(tk)}",
            key=f"_tpl_{tk}",
            width="stretch",
        ):
            st.session_state["_voucher_template"] = tk
            st.rerun()


# ---- Form to create a voucher -----------------------------------------
st.divider()
st.markdown(f"### {t('vouch.create_title')}")

# Pre-fill from template if user just clicked one
tpl_key = st.session_state.get("_voucher_template")
defaults = {
    "code":           "",
    "label":          "",
    "discount_type":  "percent",
    "discount_value": 15,
    "min_spend":      0,
    "max_uses":       0,
    "starts_at":      date.today(),
    "expires_at":     date.today() + timedelta(days=7),
    "platforms":      ["shopee", "lazada", "tiktok"],
}
if tpl_key and tpl_key in v.TEMPLATES:
    tpl = v.TEMPLATES[tpl_key]
    s = tpl["suggested"]
    defaults.update({
        "code":           v.suggest_code(tpl_key),
        "label":          voucher_tpl_label(tpl_key),
        "discount_type":  s["discount_type"],
        "discount_value": s["discount_value"],
        "min_spend":      s["min_spend"],
        "expires_at":     date.today() + timedelta(days=s["duration_days"]),
    })

with st.form("create_voucher"):
    c1, c2, c3 = st.columns([2, 3, 2])
    with c1:
        n_code = st.text_input(t("vouch.f_code"),
                                value=defaults["code"],
                                placeholder=t("vou.festival_code_ph"))
        st.caption(t("vouch.code_hint"))
    with c2:
        n_label = st.text_input(t("vouch.f_label"),
                                 value=defaults["label"],
                                 placeholder=t("vouch.label_placeholder"))
    with c3:
        n_type = st.selectbox(
            t("vouch.f_type"),
            ["percent", "fixed", "shipping"],
            index=["percent","fixed","shipping"].index(defaults["discount_type"]),
            format_func=lambda k: t(_VOUCHER_TYPES[k]),
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        if n_type == "shipping":
            n_value = 0
            st.markdown("&nbsp;", unsafe_allow_html=True)
        else:
            n_value = st.number_input(
                t("vouch.value_pct_or_baht") if n_type == "percent" else "฿",
                min_value=0.0, value=float(defaults["discount_value"]), step=1.0,
            )
    with c5:
        n_min = st.number_input(
            t("vouch.f_min_spend"),
            min_value=0.0, value=float(defaults["min_spend"]), step=50.0,
        )
    with c6:
        n_max = st.number_input(
            t("vouch.f_max_uses"),
            min_value=0, value=int(defaults["max_uses"]), step=10,
            help=t("vouch.max_uses_help"),
        )

    c7, c8, c9 = st.columns(3)
    with c7:
        n_starts = st.date_input(t("vouch.f_starts"), value=defaults["starts_at"])
    with c8:
        n_expires = st.date_input(t("vouch.f_expires"), value=defaults["expires_at"])
    with c9:
        n_platforms = st.multiselect(
            t("vouch.f_platforms"),
            options=["shopee", "lazada", "tiktok"],
            default=defaults["platforms"],
            format_func=lambda p: {"shopee":"🛒 Shopee","lazada":"🟧 Lazada","tiktok":"🎵 TikTok"}.get(p, p),
        )

    if st.form_submit_button(t("vouch.create_btn"), type="primary"):
        ok, msg = v.add(
            code=n_code, label=n_label,
            discount_type=n_type, discount_value=n_value,
            min_spend=n_min, max_uses=n_max,
            starts_at=n_starts.isoformat(),
            expires_at=n_expires.isoformat(),
            platforms=n_platforms,
        )
        if ok:
            st.session_state.pop("_voucher_template", None)
            toast(t("vouch.created"), icon="🎟")
            st.rerun()
        else:
            st.error(msg)


# ---- Active vouchers list + per-platform CSV export -------------------
st.divider()
rows = v.all_vouchers()
if not rows:
    st.info(t("vouch.empty"))
else:
    st.markdown(f"### {t('vouch.active_title')} · {len(rows)}")

    # Render each voucher as a compact card
    for r in rows:
        live_status = v.status_for(r)
        sc = STATUS_COLORS[live_status]
        si = STATUS_ICONS[live_status]
        discount_str = v.format_discount(r)
        platforms_chip = " · ".join(
            {"shopee":"🛒 Shopee","lazada":"🟧 Lazada","tiktok":"🎵 TikTok"}.get(p, p)
            for p in (r.get("platforms") or "").split(",") if p
        ) or "—"

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                f"<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
                f"border-left:3px solid {sc};border-radius:10px;padding:14px 18px;"
                f"margin-bottom:10px'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:baseline;margin-bottom:4px'>"
                f"<div><span style='font-family:\"JetBrains Mono\",monospace;"
                f"font-size:1.05rem;font-weight:600;color:#1c1c1c'>{r['code']}</span>"
                f"<span style='color:#7a7569;margin-left:10px;font-size:13px'>"
                f"{r['label']}</span></div>"
                f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.4rem;"
                f"font-weight:500;color:{sc}'>{discount_str}</div></div>"
                f"<div style='color:#7a7569;font-size:12px'>"
                f"{si} {live_status} · {platforms_chip} · "
                f"min ฿{int(r.get('min_spend') or 0):,} · "
                f"{r.get('starts_at','-')} → {r.get('expires_at','-')}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with cB:
            ca1, ca2 = st.columns(2)
            with ca1:
                if live_status != "paused":
                    if st.button("⏸", key=f"_pause_{r['id']}",
                                 type="tertiary", width="stretch",
                                 help=t("vouch.pause")):
                        v.pause(r["id"])
                        st.rerun()
                else:
                    if st.button("▶", key=f"_resume_{r['id']}",
                                 type="tertiary", width="stretch",
                                 help=t("vouch.resume")):
                        v.resume(r["id"])
                        st.rerun()
            with ca2:
                if st.button("🗑", key=f"_del_{r['id']}",
                             type="tertiary", width="stretch",
                             help=t("common.delete")):
                    v.delete(r["id"])
                    toast(t("common.deleted"), icon="🗑")
                    st.rerun()


    # ---- Per-platform CSV download row ---------------------------------
    st.divider()
    st.markdown(f"### {t('vouch.export_title')}")
    st.caption(t("vouch.export_caption"))

    dl_cols = st.columns(3)
    for col, plat_key in zip(dl_cols, ["shopee", "lazada", "tiktok"]):
        fn, prefix = v.PLATFORM_EXPORTERS[plat_key]
        # Filter only vouchers that include this platform
        plat_vouchers = [
            r for r in rows
            if plat_key in (r.get("platforms") or "").split(",")
        ]
        with col:
            data = fn(plat_vouchers) if plat_vouchers else b""
            label = {"shopee":"🛒 Shopee","lazada":"🟧 Lazada","tiktok":"🎵 TikTok"}[plat_key]
            st.download_button(
                f"⬇ {label}  ({len(plat_vouchers)})",
                data=data,
                file_name=f"nirva_{prefix}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key=f"_dl_{plat_key}",
                disabled=not plat_vouchers,
                width="stretch",
            )

st.divider()
st.caption(t("vouch.disclaimer"))
