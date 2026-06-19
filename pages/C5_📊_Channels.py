"""Channel Performance — compare revenue share across selling platforms."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import channel_performance as cp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Channels",
                   page_icon="📊", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📊", title=t("ch.title"), subtitle=t("ch.caption"))

days = st.select_slider(
    t("ch.f_days"), options=[7, 14, 30, 60, 90], value=30, key="_ch_days"
)

s = cp.summary(days)
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("📡 " + t("ch.kpi_channels"), str(s["total_channels"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🏆 " + t("ch.kpi_top"), s["top_channel"],
                     hint="฿{:,.0f}".format(s.get("top_revenue", 0)),
                     hint_tone="ok")
with k3:
    metric_with_hint("💰 " + t("ch.kpi_revenue"),
                     "฿{:,.0f}".format(s["total_revenue"]),
                     hint="", hint_tone="info")

st.divider()

stats = cp.channel_stats(days)
if not stats:
    st.info(t("ch.empty"))
    st.stop()

# ---- Revenue share bar chart ------------------------------------------------
st.markdown("### 📊 " + t("ch.share_title"))

for ch in stats:
    bar_pct = ch["share_pct"]
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px'>"
        "<span style='width:110px;font-size:13px'>" +
        ch["icon"] + " <strong>" + ch["label"] + "</strong></span>"
        "<div style='flex:1;background:rgba(40,30,20,0.06);border-radius:3px;height:22px'>"
        "<div style='width:" + str(bar_pct) + "%;height:100%;background:" +
        ch["color"] + ";border-radius:3px;display:flex;align-items:center;"
        "padding-left:8px'>"
        "<span style='font-size:11px;color:white;font-weight:600'>"
        + ("฿{:,.0f}".format(ch["revenue"]) if bar_pct > 12 else "") +
        "</span></div></div>"
        "<span style='width:45px;font-size:12px;text-align:right'>"
        + str(bar_pct) + "%</span></div>",
        unsafe_allow_html=True,
    )

# ---- Detail table -----------------------------------------------------------
st.divider()
st.markdown("### " + t("ch.detail_title"))

for ch in stats:
    with st.expander(
        ch["icon"] + " " + ch["label"] +
        " · ฿{:,.0f}".format(ch["revenue"]) +
        " · " + str(ch["orders"]) + " " + t("common.orders")
    ):
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1:
            st.metric(t("ch.d_orders"), str(ch["orders"]))
        with dc2:
            st.metric(t("ch.d_avg"), "฿{:,.0f}".format(ch["avg_order"]))
        with dc3:
            st.metric(t("ch.d_fees"), "฿{:,.0f}".format(ch["platform_fees"]))
        with dc4:
            st.metric(t("ch.d_net"), "฿{:,.0f}".format(ch["net_revenue"]))

        top_skus = cp.top_skus_by_channel(ch["platform"], days)
        if top_skus:
            st.markdown("**Top SKUs:**")
            for sku_r in top_skus:
                st.markdown(
                    "<div style='font-size:12px;padding:2px 0'>"
                    "📦 <strong>" + sku_r["sku"] + "</strong>"
                    " · " + str(sku_r["total_qty"]) + " " + t("common.pieces") +
                    " · ฿{:,.0f}".format(sku_r["revenue"]) + "</div>",
                    unsafe_allow_html=True,
                )
