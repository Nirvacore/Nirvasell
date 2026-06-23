"""Live Data — FX rates, promotion calendar, trending keywords.

Auto-refreshes FX every 6 hours (cached). Promotion calendar is deterministic
so it always works offline. Trending keywords need an API key."""
from __future__ import annotations
import sys
from datetime import datetime, date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import live_data
import fees as fees_mod
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from i18n_inline import live_promo_label
from _components import page_header

db.init()
st.set_page_config(page_title="nirva.sell · Live", page_icon="📊", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📊", title=t("live.title"), subtitle=t("live.caption"))


# ---- FX rates -----------------------------------------------------------

st.markdown(f"## {t('live.fx_title')}")

c1, c2 = st.columns([3, 1])
with c2:
    if st.button(t("live.fx_refresh"), width='stretch'):
        live_data.fetch_fx_rates(force=True)
        st.rerun()

fx = live_data.fetch_fx_rates()
rates = fx.get("rates") or {}
fetched_at = fx.get("fetched_at", "")
if fetched_at:
    try:
        when = datetime.fromisoformat(fetched_at)
        age_minutes = (datetime.now() - when).total_seconds() / 60
        if age_minutes < 60:
            age_label = f"{int(age_minutes)} {t('live.minutes_ago')}"
        else:
            age_label = f"{int(age_minutes / 60)} {t('live.hours_ago')}"
        c1.caption(f"{t('live.fetched_at')}: {fetched_at[:16]} ({age_label})")
    except Exception:
        c1.caption(fetched_at)

if not rates:
    st.warning(t("live.fx_unavailable"))
else:
    # Show the top currencies resellers care about
    priority = ["USD", "EUR", "GBP", "JPY", "CNY", "SGD", "AUD",
                "MYR", "IDR", "VND", "PHP", "KRW", "HKD", "TWD", "INR", "AED"]
    table = []
    for cc in priority:
        if cc in rates:
            static = fees_mod.FX_RATES_VS_THB.get(cc)
            live = rates[cc]
            delta = (live - static) / static * 100 if static else 0
            table.append({
                t("live.currency"): cc,
                t("live.label"): fees_mod.CURRENCY_LABELS.get(cc, ""),
                f"฿1 {t('live.equals')}": live,
                f"{t('live.vs_static')} %": delta,
            })
    df = pd.DataFrame(table)
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            f"฿1 {t('live.equals')}": st.column_config.NumberColumn(format="%.4f"),
            f"{t('live.vs_static')} %": st.column_config.NumberColumn(format="%+.2f%%"),
        },
    )


# ---- Promotion calendar -------------------------------------------------

st.markdown(f"## {t('live.promos_title')}")
st.caption(t("live.promos_help"))

events = live_data.upcoming_promotions(within_days=365)
if not events:
    st.info(t("live.no_promos"))
else:
    # Big countdown card for the next one
    nxt = events[0]
    label = live_promo_label(nxt["slug"])
    days = nxt["days_until"]
    st.markdown(
        f"<div style='background:rgba(77,108,92,0.08);border:1.5px solid #4d6c5c;"
        f"border-radius:14px;padding:24px;text-align:center;margin-bottom:14px'>"
        f"<div style='color:#6b6b6b;font-size:0.85rem;text-transform:uppercase;"
        f"letter-spacing:0.06em'>{t('live.next_event')}</div>"
        f"<div style='font-family:Cormorant Garamond,serif;font-size:2rem;"
        f"font-weight:500;color:#1f1f1f;margin:6px 0'>{label}</div>"
        f"<div style='color:#4d6c5c;font-size:1.2rem;font-weight:500'>"
        f"{t('live.in_n_days', n=days)} ({nxt['date']}) · {nxt['region']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Full table
    rows = [{
        t("live.event"): live_promo_label(e["slug"]),
        t("live.date"): e["date"],
        t("live.days_until"): e["days_until"],
        t("live.region"): e["region"],
    } for e in events]
    pdf = pd.DataFrame(rows)
    st.dataframe(pdf, width='stretch', hide_index=True, height=420)


# ---- Trending keywords (AI) ---------------------------------------------

st.markdown(f"## {t('live.trends_title')}")
st.caption(t("live.trends_caption"))

api_key = st.session_state.get("api_key", "")
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    category = st.text_input(t("live.trend_category"), "")
with c2:
    market = st.selectbox(
        t("live.trend_market"),
        ["TH", "US", "JP", "ID", "VN", "PH", "SG", "MY"],
        index=0,
    )
with c3:
    fetch_btn = st.button(
        t("live.fetch_trends"),
        type="primary",
        width='stretch',
        disabled=not (api_key and category),
    )

if fetch_btn:
    with st.spinner(t("generate.running")):
        try:
            results = live_data.trending_keywords(category, market, api_key=api_key)
            if results:
                heat_emoji = {"high": "🔥", "medium": "📈", "low": "•"}
                rows = [{
                    t("live.keyword"): r.get("kw", ""),
                    t("live.heat"): f"{heat_emoji.get(r.get('heat'),'')} {r.get('heat','')}",
                    t("live.note"): r.get("note", ""),
                } for r in results]
                st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
            else:
                st.info(t("common.no_results"))
        except Exception as e:
            st.error(str(e))


# ---- Action: turn nearest sale into a campaign --------------------------

st.markdown(f"## {t('live.action_title')}")
nxt_big = live_data.next_big_sale()
if nxt_big and nxt_big["days_until"] <= 60:
    label = live_promo_label(nxt_big["slug"])
    st.success(
        t("live.action_suggest",
          n=nxt_big["days_until"],
          event=label,
          date=nxt_big["date"])
    )
    st.caption(t("live.action_hint"))
