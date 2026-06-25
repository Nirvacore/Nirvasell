"""Customer CRM — know your buyers, spot VIPs, re-engage dormant ones.

Repeat customers are 5x cheaper to sell to than new ones. This page
gives home sellers the one thing no Thai platform provides: a unified
customer view across Shopee + Lazada + TikTok."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import customers as cust
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import platform_list_display

st.set_page_config(page_title="nirva.sell · Customers",
                   page_icon="👥", layout="wide")
apply_theme()
require_auth()
db.init()
cust.init()
render_sidebar()

page_header(icon="👥", title=t("cust.title"), subtitle=t("cust.caption"))


# ---- KPI overview -------------------------------------------------------

s = cust.stats()

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_with_hint(
        t("cust.kpi_total"), str(s["total"]),
        hint=t("cust.hint_import") if s["total"] == 0 else "",
        hint_target="pages/F_📈_Dashboard.py" if s["total"] == 0 else None,
        hint_tone="warn" if s["total"] == 0 else "info",
    )
with m2:
    metric_with_hint(
        t("cust.kpi_repeat"), f"{s['repeat']} ({s['repeat_pct']}%)",
        hint=t("cust.hint_repeat_low") if s["repeat_pct"] < 15 else "",
        hint_tone="warn" if s["repeat_pct"] < 15 else "ok",
    )
with m3:
    metric_with_hint(
        t("cust.kpi_vip"), str(s["vip"]),
        hint="" if s["vip"] else t("cust.hint_no_vip"),
        hint_tone="info",
    )
with m4:
    metric_with_hint(
        t("cust.kpi_avg_spent"), f"฿{s['avg_spent']:,.0f}",
        hint="",
        hint_tone="info",
    )


# ---- Search + filter tabs -----------------------------------------------

search_q = st.text_input(
    t("cust.search"),
    placeholder=t("cust.search_placeholder"),
    label_visibility="collapsed",
)

tab_all, tab_vip, tab_dormant = st.tabs([
    f"👥 {t('cust.tab_all')}",
    f"💎 {t('cust.tab_vip')}",
    f"😴 {t('cust.tab_dormant')}",
])


# ---- All customers -------------------------------------------------------

def _render_customer_card(c_data: dict):
    t_key = cust.tier(c_data.get("order_count", 0))
    t_icon = cust.TIER_ICONS[t_key]
    t_color = cust.TIER_COLORS[t_key]
    plat_icons = platform_list_display(c_data.get("platforms") or "")
    subline = (
        t("common.n_orders", n=str(c_data.get("order_count", 0)))
        + " · " + plat_icons
        + " · " + t("cust.last_prefix") + ": "
        + (c_data.get("last_order") or "—")[:10]
    )

    cA, cB = st.columns([5, 2])
    with cA:
        st.markdown(
            f"<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            f"border-left:3px solid {t_color};border-radius:10px;padding:14px 18px;"
            f"margin-bottom:8px'>"
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:baseline;margin-bottom:4px'>"
            f"<div><span style='font-size:15px;font-weight:600;color:#1c1c1c'>"
            f"{t_icon} {c_data.get('name','—')}</span>"
            f"<span style='color:{t_color};font-size:11px;margin-left:8px;"
            f"text-transform:uppercase;letter-spacing:0.08em'>{t_key}</span></div>"
            f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.3rem;"
            f"font-weight:500;color:#4d6c5c'>฿{c_data.get('total_spent',0):,.0f}</div></div>"
            f"<div style='color:#7a7569;font-size:12px'>"
            f"📦 {subline}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with cB:
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("👁", key=f"_cv_{c_data['id']}",
                         type="tertiary", width="stretch",
                         help=t("cust.view_orders")):
                st.session_state["_cust_detail_id"] = c_data["id"]
                st.rerun()
        with ca2:
            if st.button("✏", key=f"_ce_{c_data['id']}",
                         type="tertiary", width="stretch",
                         help=t("common.edit")):
                st.session_state["_cust_edit_id"] = c_data["id"]
                st.rerun()


with tab_all:
    if search_q.strip():
        customers = cust.search(search_q)
        st.caption(t("cust.search_results", n=len(customers), q=search_q))
    else:
        sort_col = st.columns([1, 4])
        with sort_col[0]:
            sort_by = st.selectbox(
                t("cust.sort"),
                ["total_spent", "order_count", "last_order", "name"],
                format_func=lambda k: {
                    "total_spent": "💰 " + t("cust.sort_spent"),
                    "order_count": "📦 " + t("cust.sort_orders"),
                    "last_order":  "📅 " + t("cust.sort_recent"),
                    "name":        "🔤 " + t("cust.sort_name"),
                }.get(k, k),
                label_visibility="collapsed",
            )
        customers = cust.all_customers(sort=sort_by)

    if not customers:
        st.info(t("cust.empty"))
        st.caption(t("cust.empty_hint"))
    else:
        for c_data in customers:
            _render_customer_card(c_data)


with tab_vip:
    vips = cust.vip_customers(min_orders=3)
    if not vips:
        st.info(t("cust.no_vip_yet"))
    else:
        st.caption(t("cust.vip_count", n=len(vips)))
        for c_data in vips:
            _render_customer_card(c_data)


with tab_dormant:
    st.caption(t("cust.dormant_help"))
    dormant_days = st.selectbox(
        t("cust.dormant_days"),
        [14, 30, 60, 90],
        index=1,
        format_func=lambda d: f"{d} {t('dashboard.days')}",
        label_visibility="collapsed",
    )
    dormants = cust.dormant_customers(days=dormant_days)
    if not dormants:
        st.success(t("cust.no_dormant"))
    else:
        st.warning(t("cust.dormant_count", n=len(dormants)))
        for c_data in dormants:
            _render_customer_card(c_data)


# ---- Customer detail drawer (order history) ----------------------------

detail_id = st.session_state.get("_cust_detail_id")
if detail_id:
    c_info = cust.get(detail_id)
    if c_info:
        st.divider()
        t_key = cust.tier(c_info.get("order_count", 0))
        t_icon = cust.TIER_ICONS[t_key]
        st.markdown(
            f"### {t_icon} {c_info['name']} — {t('cust.order_history')}"
        )
        cols_info = st.columns(4)
        cols_info[0].markdown(f"**📱 {t('cust.phone')}:** {c_info.get('phone') or '—'}")
        cols_info[1].markdown(f"**📧 {t('cust.email')}:** {c_info.get('email') or '—'}")
        cols_info[2].markdown(f"**💚 {t('cust.line')}:** {c_info.get('line_id') or '—'}")
        cols_info[3].markdown(f"**📝 {t('cust.note')}:** {c_info.get('note') or '—'}")

        orders = cust.orders_for(detail_id)
        if orders:
            import pandas as pd
            df = pd.DataFrame(orders)
            show = [c for c in ["order_date", "platform", "order_id", "product", "amount"]
                    if c in df.columns]
            st.dataframe(df[show], hide_index=True, width="stretch")
        else:
            st.caption(t("cust.no_orders_recorded"))

        # v59: AI message generator for this customer
        api_key = st.session_state.get("api_key", "")
        if api_key:
            st.markdown(f"#### 🤖 {t('cust.ai_message')}")
            ai_cols = st.columns(4)
            segments = ["dormant", "vip_thank", "welcome", "promo"]
            seg_labels = {
                "dormant": "😴 " + t("cust.seg_dormant"),
                "vip_thank": "💎 " + t("cust.seg_vip"),
                "welcome": "👋 " + t("cust.seg_welcome"),
                "promo": "🎯 " + t("cust.seg_promo"),
            }
            for i, seg in enumerate(segments):
                with ai_cols[i]:
                    if st.button(seg_labels[seg], key=f"_ai_{seg}_{detail_id}",
                                 width="stretch", type="tertiary"):
                        with st.spinner(t("generate.running")):
                            try:
                                import customer_ai
                                import user_settings as _us
                                _us.init()
                                shop = _us.get("fulfill.seller_name", "") or t("cust.default_shop")
                                msg = customer_ai.generate_message(
                                    segment=seg, customer=c_info,
                                    shop_name=shop, api_key=api_key,
                                )
                                st.session_state["_cust_ai_msg"] = msg
                            except Exception as e:
                                st.error(str(e))

            ai_msg = st.session_state.get("_cust_ai_msg")
            if ai_msg:
                st.text_area(t("cust.ai_result"), value=ai_msg, height=120,
                             key="_ai_msg_display")

        if st.button(t("common.close"), key="_close_detail"):
            st.session_state.pop("_cust_detail_id", None)
            st.session_state.pop("_cust_ai_msg", None)
            st.rerun()


# ---- Customer edit drawer -----------------------------------------------

edit_id = st.session_state.get("_cust_edit_id")
if edit_id:
    c_info = cust.get(edit_id)
    if c_info:
        st.divider()
        st.markdown(f"### ✏ {t('cust.edit_title')}")
        with st.form("_cust_edit_form"):
            ne_name = st.text_input(t("cust.f_name"), value=c_info.get("name", ""))
            c1, c2 = st.columns(2)
            with c1:
                ne_phone = st.text_input(t("cust.phone"), value=c_info.get("phone", ""))
                ne_email = st.text_input(t("cust.f_email"), value=c_info.get("email", ""))
            with c2:
                ne_line = st.text_input(t("cust.f_line"), value=c_info.get("line_id", ""))
                ne_note = st.text_area(t("cust.note"), value=c_info.get("note", ""), height=80)
            ca, cb = st.columns(2)
            with ca:
                if st.form_submit_button(t("common.save"), type="primary", width="stretch"):
                    cust.update(edit_id, name=ne_name, phone=ne_phone,
                                email=ne_email, line_id=ne_line, note=ne_note)
                    st.session_state.pop("_cust_edit_id", None)
                    toast(t("common.saved"), icon="✓")
                    st.rerun()
            with cb:
                if st.form_submit_button(t("common.cancel"), width="stretch"):
                    st.session_state.pop("_cust_edit_id", None)
                    st.rerun()
