"""Pay-what-you-can support page. No paywall, no dark patterns —
just honest costs and ways to help.

v26 update: now wires up real PromptPay QR + Stripe Payment Link + honor-
system donation log. See payments.py."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import payments
import auth
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from _components import page_header

st.set_page_config(page_title="nirva.sell · Support", page_icon="💝", layout="wide")
apply_theme()
require_auth()
render_sidebar()
payments.init()

page_header(icon="💝", title=t("support.title"), subtitle=t("support.caption"))


# ---- Why free ------------------------------------------------------------

st.markdown("## " + t("support.why_title"))
st.markdown(t("support.why_body"))


# ---- Honest costs --------------------------------------------------------

st.markdown("## " + t("support.costs_title"))
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("support.cost_claude"), "BYOK")
c1.caption(t("support.cost_claude_note"))
c2.metric(t("support.cost_hosting"), "$5/mo")
c2.caption(t("support.cost_hosting_note"))
c3.metric(t("support.cost_domain"), "$30/yr")
c3.caption(t("support.cost_domain_note"))
c4.metric(t("support.cost_dev"), "♥")
c4.caption(t("support.cost_dev_note"))


# ---- Tiers (informational, no actual checkout) ---------------------------

st.markdown("## " + t("support.tiers_title"))
st.caption(t("support.tiers_caption"))

tiers = [
    {
        "amount": t("support.tier_free_label"),
        "monthly": "฿0",
        "what": t("support.tier_free_what"),
        "primary": False,
    },
    {
        "amount": t("support.tier_coffee_label"),
        "monthly": "฿99",
        "what": t("support.tier_coffee_what"),
        "primary": False,
    },
    {
        "amount": t("support.tier_dev_label"),
        "monthly": "฿199",
        "what": t("support.tier_dev_what"),
        "primary": True,
    },
    {
        "amount": t("support.tier_sponsor_label"),
        "monthly": "฿499+",
        "what": t("support.tier_sponsor_what"),
        "primary": False,
    },
]

cols = st.columns(len(tiers))
for col, tier in zip(cols, tiers):
    with col:
        bg = "rgba(77,108,92,0.08)" if tier["primary"] else "transparent"
        border = "#4d6c5c" if tier["primary"] else "rgba(40,30,20,0.10)"
        st.markdown(
            f"<div style='background:{bg};border:1.5px solid {border};"
            f"border-radius:12px;padding:18px;min-height:240px;display:flex;"
            f"flex-direction:column;justify-content:space-between'>"
            f"<div>"
            f"<div style='font-family:Cormorant Garamond,serif;font-size:1.6rem;"
            f"font-weight:500;color:#1f1f1f'>{tier['monthly']}</div>"
            f"<div style='color:#6b6b6b;font-size:13px;margin:4px 0 12px'>"
            f"{tier['amount']}</div>"
            f"<div style='font-size:14px;line-height:1.6;color:#3d3d3d'>"
            f"{tier['what']}</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )


# ---- Pay-what-you-can ----------------------------------------------------

st.markdown("## " + t("support.pwyc_title"))
st.markdown(t("support.pwyc_body"))


# ---- v42: Running cost meter (radical transparency) ---------------------
# Per competitor analysis: reframe "donation" as "community-funded server cost"
# — show this month's raised vs target so users see exactly what they fund.
st.markdown(f"### 📊 {t('cost.title')}")
import _cost_meter
_cost_meter.render(st, t)


# ---- Ways to give (real, working) ----------------------------------------

st.markdown("## " + t("support.how_title"))

settings = payments.get_settings()
configured = bool(settings["promptpay_id"]) or bool(settings["stripe_link"]) \
             or bool(settings["bmac_url"]) or bool(settings["github_sponsors"])

if not configured:
    st.info(t("support.not_configured"))
    if auth.is_admin():
        st.caption(t("support.admin_configure_hint"))

# ---- Tab 1: PromptPay QR ------------------------------------------------
t1, t2, t3 = st.tabs([
    f"📱 {t('support.way_promptpay')}",
    f"💳 {t('support.way_stripe')}",
    f"☕ {t('support.way_other')}",
])

with t1:
    if not settings["promptpay_id"]:
        st.caption(t("support.promptpay_unset"))
    else:
        cP1, cP2 = st.columns([1, 1])
        with cP1:
            amount = st.number_input(
                t("support.pp_amount"),
                min_value=0.0, value=99.0, step=10.0,
                help=t("support.pp_amount_help"),
            )
            png = payments.promptpay_qr_png(
                settings["promptpay_id"],
                amount=amount if amount > 0 else None,
            )
            if png:
                st.image(png, width=280)
                if settings["promptpay_name"]:
                    st.caption(f"→ {settings['promptpay_name']}")
                st.caption(t("support.pp_scan_hint"))
            else:
                st.error(t("support.pp_invalid_id"))
        with cP2:
            st.markdown(f"**{t('support.pp_after_pay')}**")
            with st.form("log_promptpay"):
                amt_paid = st.number_input(
                    t("support.pp_amount_sent"), min_value=0.0, value=amount, step=10.0,
                )
                note = st.text_input(t("support.pp_note"), placeholder=t("support.pp_note_placeholder"))
                if st.form_submit_button(t("support.pp_log"), type="primary"):
                    payments.log_donation(
                        amount=amt_paid, currency="THB",
                        method="promptpay", note=note,
                    )
                    st.success(t("support.thanks"))
                    st.balloons()

with t2:
    if not settings["stripe_link"]:
        st.caption(t("support.stripe_unset"))
    else:
        st.markdown(
            f"<div style='background:#fbf9f3;border:1px solid rgba(40,30,20,0.10);"
            f"border-radius:12px;padding:24px;text-align:center'>"
            f"<div style='font-size:48px'>💳</div>"
            f"<div style='font-weight:600;margin:12px 0'>{t('support.stripe_title')}</div>"
            f"<div style='color:#6b6b6b;font-size:13px;margin-bottom:16px'>"
            f"{t('support.stripe_body')}</div>"
            f"<a href='{settings['stripe_link']}' target='_blank' "
            f"style='display:inline-block;background:#4d6c5c;color:white;"
            f"padding:10px 22px;border-radius:8px;text-decoration:none;"
            f"font-weight:500'>→ {t('support.stripe_open')}</a>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(t("support.stripe_after"))
        with st.expander(t("support.pp_log")):
            with st.form("log_stripe"):
                amt = st.number_input(t("support.pp_amount_sent"), min_value=0.0, value=5.0, step=1.0)
                cur = st.selectbox(t("common.currency"), ["USD", "EUR", "THB", "GBP", "JPY"])
                note = st.text_input(t("support.pp_note"))
                if st.form_submit_button(t("support.pp_log"), type="primary"):
                    payments.log_donation(amount=amt, currency=cur, method="stripe", note=note)
                    st.success(t("support.thanks"))

with t3:
    cO1, cO2 = st.columns(2)
    with cO1:
        if settings["bmac_url"]:
            st.markdown(
                f"<div style='background:#fbf9f3;border:1px solid rgba(40,30,20,0.10);"
                f"border-radius:12px;padding:20px;text-align:center'>"
                f"<div style='font-size:36px'>☕</div>"
                f"<div style='font-weight:600;margin:8px 0'>{t('support.way_coffee')}</div>"
                f"<a href='{settings['bmac_url']}' target='_blank' "
                f"style='color:#4d6c5c;text-decoration:none;font-weight:500'>"
                f"→ buymeacoffee.com</a></div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption(t("support.bmac_unset"))
    with cO2:
        if settings["github_sponsors"]:
            st.markdown(
                f"<div style='background:#fbf9f3;border:1px solid rgba(40,30,20,0.10);"
                f"border-radius:12px;padding:20px;text-align:center'>"
                f"<div style='font-size:36px'>💚</div>"
                f"<div style='font-weight:600;margin:8px 0'>{t('support.way_github')}</div>"
                f"<a href='{settings['github_sponsors']}' target='_blank' "
                f"style='color:#4d6c5c;text-decoration:none;font-weight:500'>"
                f"→ GitHub Sponsors</a></div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption(t("support.github_unset"))


# ---- Admin: Configure payment settings ---------------------------------

if auth.is_admin():
    st.divider()
    with st.expander(f"⚙ {t('support.admin_settings')}"):
        st.caption(t("support.admin_settings_hint"))
        with st.form("payment_settings"):
            pp_id = st.text_input(
                t("support.cfg_promptpay_id"),
                value=settings["promptpay_id"],
                help=t("support.cfg_promptpay_id_help"),
            )
            pp_name = st.text_input(
                t("support.cfg_promptpay_name"),
                value=settings["promptpay_name"],
            )
            stripe_link = st.text_input(
                t("support.cfg_stripe_link"),
                value=settings["stripe_link"],
                help=t("support.cfg_stripe_link_help"),
            )
            bmac = st.text_input(
                t("support.cfg_bmac_url"),
                value=settings["bmac_url"],
            )
            gh = st.text_input(
                t("support.cfg_github_url"),
                value=settings["github_sponsors"],
            )
            if st.form_submit_button(t("common.save"), type="primary"):
                payments.set_settings(
                    promptpay_id=pp_id, promptpay_name=pp_name,
                    stripe_link=stripe_link, bmac_url=bmac,
                    github_sponsors=gh,
                )
                st.success(t("common.saved"))
                st.rerun()

        # Donation log preview
        st.divider()
        st.markdown(f"**{t('support.recent_donations')}**")
        rows = payments.list_donations(limit=20)
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(
                df[["created_at", "amount", "currency", "method", "note", "confirmed"]],
                hide_index=True, width='stretch',
            )
            totals = payments.total_received(confirmed_only=False)
            st.caption(
                t("support.totals") + ": " +
                " · ".join(f"{cur} {amt:,.2f}" for cur, amt in totals.items())
            )
        else:
            st.caption(t("support.no_donations"))


# ---- Other ways ----------------------------------------------------------

st.markdown("## " + t("support.other_title"))
st.markdown(t("support.other_body"))


# ---- Footer pledge -------------------------------------------------------

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;padding:20px;color:#6b6b6b;font-size:14px'>"
    f"{t('support.pledge')}"
    "</div>",
    unsafe_allow_html=True,
)
