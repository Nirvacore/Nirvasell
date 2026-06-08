"""Demand Forecast — predict next 30/60/90 days sales per SKU."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import demand_forecast as df
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Forecast",
                   page_icon="🔮", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🔮", title=t("fcast.title"), subtitle=t("fcast.caption"))

horizon = st.select_slider(
    t("fcast.f_horizon"),
    options=[7, 14, 30, 60, 90],
    value=30, key="_fcast_horizon",
)

s = df.summary()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📦 " + t("fcast.kpi_skus"), str(s["skus_forecasted"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("💰 " + t("fcast.kpi_revenue"),
                     "฿{:,.0f}".format(s["forecast_revenue_30d"]),
                     hint=t("fcast.revenue_hint"), hint_tone="ok")
with k3:
    metric_with_hint("📈 " + t("fcast.kpi_rising"), str(s["rising_skus"]),
                     hint="", hint_tone="ok")
with k4:
    metric_with_hint("⚠️ " + t("fcast.kpi_risks"), str(s["stockout_risks"]),
                     hint=t("fcast.risk_hint") if s["stockout_risks"] > 0 else "",
                     hint_tone="danger" if s["stockout_risks"] > 0 else "ok")

# ---- Stockout risks --------------------------------------------------------
risks = df.stockout_risk(horizon)
if risks:
    st.divider()
    st.markdown("### 🚨 " + t("fcast.risk_title") + " (" + str(len(risks)) + ")")
    for r in risks:
        r_color = "#c54c4c" if r["risk_level"] == "high" else "#c5963d"
        st.markdown(
            "<div style='padding:8px 14px;border-left:3px solid " + r_color + ";"
            "border-bottom:0.5px solid rgba(40,30,20,0.04)'>"
            "<div style='display:flex;justify-content:space-between'>"
            "<span><strong>" + r["sku"] + "</strong></span>"
            "<span style='display:flex;gap:12px;font-size:12px'>"
            "<span>สต็อก " + str(r["current_stock"]) + "</span>"
            "<span>ต้องการ " + str(r["forecast_need"]) + "</span>"
            "<span style='color:" + r_color + ";font-weight:600'>"
            "ขาด " + str(r["deficit"]) + " · " + str(r["coverage_days"]) + " วัน</span>"
            "</span></div></div>",
            unsafe_allow_html=True,
        )

# ---- Full forecast table ---------------------------------------------------
st.divider()
st.markdown("### " + t("fcast.table_title"))

trend_filter = st.selectbox(
    t("fcast.f_trend"),
    ["all", "rising", "stable", "declining"],
    format_func=lambda x: {
        "all": "🔍 " + t("fcast.all"),
        "rising": "📈 " + t("fcast.rising"),
        "stable": "➡️ " + t("fcast.stable"),
        "declining": "📉 " + t("fcast.declining"),
    }.get(x, x),
    key="_fcast_trend",
)

forecasts = df.forecast_all(horizon)
if trend_filter != "all":
    forecasts = [f for f in forecasts if f["trend"] == trend_filter]

if not forecasts:
    st.info(t("fcast.empty"))
    st.stop()

for item in forecasts:
    trend_icon = {"rising": "📈", "stable": "➡️", "declining": "📉"}.get(
        item["trend"], "?"
    )
    trend_color = {"rising": "#4d6c5c", "stable": "#7a7569",
                   "declining": "#c54c4c"}.get(item["trend"], "#7a7569")
    conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(
        item.get("confidence", "low"), "?"
    )

    st.markdown(
        "<div style='padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
        "<span><strong>" + item["sku"] + "</strong>"
        " " + trend_icon +
        " <span style='font-size:11px;color:" + trend_color + "'>"
        + item["trend"] + " " + ("+" if item["trend_pct"] > 0 else "") +
        str(item["trend_pct"]) + "%</span>"
        " " + conf_icon + "</span>"
        "<span style='display:flex;gap:12px;font-size:13px'>"
        "<span>เฉลี่ย " + str(item["avg_weekly_recent"]) + " ชิ้น/สัปดาห์</span>"
        "<span style='font-weight:600'>พยากรณ์ " + str(item["forecast_qty"]) +
        " ชิ้น</span>"
        "<span style='color:#4d6c5c;font-weight:600'>"
        "฿{:,.0f}".format(item["forecast_revenue"]) + "</span>"
        "</span></div>"
        "<div style='display:flex;gap:2px;margin-top:4px'>"
        + "".join(
            "<div style='flex:1;background:" +
            ("#4d6c5c" if w > 0 else "rgba(40,30,20,0.1)") +
            ";height:16px;border-radius:2px;opacity:" +
            str(min(1.0, 0.3 + w / max(item["weekly_history"]) * 0.7)
                if max(item["weekly_history"]) > 0 else 0.3) +
            "'></div>"
            for w in item["weekly_history"]
        ) +
        "</div></div>",
        unsafe_allow_html=True,
    )

st.caption(t("fcast.disclaimer"))
