"""Loyalty Program — points, tiers, rewards for repeat customers.

Reward your best customers. Track points, tiers, and redemptions."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import loyalty as loy
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Loyalty",
                   page_icon="🎖", layout="wide")
apply_theme()
require_auth()
db.init()
loy.init()
render_sidebar()

page_header(icon="🎖", title=t("loy.title"), subtitle=t("loy.caption"))

s = loy.stats()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("👥 " + t("loy.kpi_members"), str(s["members"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("⭐ " + t("loy.kpi_outstanding"), "{:,}".format(s["total_points_outstanding"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("🎁 " + t("loy.kpi_redeemed"), "{:,}".format(s["total_redeemed"]),
                     hint="", hint_tone="ok")
with k4:
    tier_top = 0
    for tn in ["diamond", "platinum", "gold"]:
        tier_top += s["tiers"].get(tn, 0)
    metric_with_hint("👑 " + t("loy.kpi_vip"), str(tier_top),
                     hint=t("loy.vip_hint"), hint_tone="ok")


# ---- Tier overview ----------------------------------------------------------

st.divider()
st.markdown("### " + t("loy.tiers_title"))

tier_cols = st.columns(len(loy.TIERS))
for i, (tname, tinfo) in enumerate(loy.TIERS.items()):
    with tier_cols[i]:
        cnt = s["tiers"].get(tname, 0)
        st.markdown(
            "<div style='text-align:center;padding:12px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px'>"
            "<div style='font-size:1.8rem'>" + tinfo["icon"] + "</div>"
            "<div style='font-weight:600'>" + tinfo["label_th"] + "</div>"
            "<div style='font-size:12px;color:#7a7569'>ส่วนลด " + str(tinfo["discount_pct"]) + "%</div>"
            "<div style='font-size:12px;color:#9a9485'>" + str(tinfo["min_points"]) + t("loy.pts_min_suffix") + "</div>"
            "<div style='font-size:1.3rem;font-weight:600;color:#4d6c5c;margin-top:4px'>"
            + str(cnt) + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Earn points for a customer --------------------------------------------

st.divider()
st.markdown("### ➕ " + t("loy.earn_title"))

with st.form("earn_pts"):
    ec1, ec2 = st.columns(2)
    with ec1:
        with db.conn() as c:
            custs = c.execute("""
                SELECT COALESCE(buyer_phone, buyer_name) AS ckey,
                       buyer_name, COUNT(*) AS orders
                FROM orders
                WHERE buyer_name IS NOT NULL AND buyer_name != ''
                GROUP BY ckey ORDER BY orders DESC LIMIT 100
            """).fetchall()

        if custs:
            cust_opts = [c_row["ckey"] + " · " + (c_row["buyer_name"] or "") for c_row in custs]
            sel_idx = st.selectbox(t("loy.f_customer"), range(len(cust_opts)),
                                   format_func=lambda i: cust_opts[i])
            sel_cust = custs[sel_idx]["ckey"]
        else:
            sel_cust = st.text_input(t("loy.f_customer_key"))

    with ec2:
        earn_amount = st.number_input(t("loy.f_amount"), min_value=0.0,
                                      value=0.0, step=100.0)

    if st.form_submit_button(t("loy.earn_btn"), type="primary"):
        if sel_cust and earn_amount > 0:
            result = loy.earn_points(sel_cust, earn_amount)
            toast(t("loy.earned_msg", fmt={
                "pts": str(result["earned"]),
                "bal": str(result["balance"]),
            }), icon="⭐")
            st.rerun()


# ---- Redeem rewards ---------------------------------------------------------

st.divider()
st.markdown("### 🎁 " + t("loy.redeem_title"))

rw_cols = st.columns(len(loy.REWARDS))
for i, rw in enumerate(loy.REWARDS):
    with rw_cols[i]:
        st.markdown(
            "<div style='text-align:center;padding:10px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px'>"
            "<div style='font-size:1.5rem'>" + rw["icon"] + "</div>"
            "<div style='font-weight:600;font-size:13px'>" + rw["name"] + "</div>"
            "<div style='font-size:12px;color:#4d6c5c'>" + str(rw["points"]) + t("loy.pts_suffix") + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Leaderboard ------------------------------------------------------------

st.divider()
st.markdown("### 🏆 " + t("loy.leaderboard_title"))

leaders = loy.leaderboard(10)
if leaders:
    for lb in leaders:
        rank_icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(lb["rank"], str(lb["rank"]))
        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span>" + str(rank_icon) + " " + lb["tier_icon"] +
            " <strong>" + lb["customer_key"] + "</strong></span>"
            "<span style='display:flex;gap:12px'>"
            "<span style='color:#4d6c5c;font-weight:600'>"
            + "{:,}".format(lb["lifetime_points"]) + t("loy.pts_suffix") + "</span>"
            "<span style='color:#9a9485'>คงเหลือ " + "{:,}".format(lb["points"]) + "</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )
else:
    st.info(t("loy.no_members"))
