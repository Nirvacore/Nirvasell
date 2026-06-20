"""Monthly P&L Report + Order Analytics.

THE page every seller needs for tax filing and business decisions.
Shows true profit after ALL deductions, peak selling hours, and trends."""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import profit_report as pnl
import order_analytics as oa
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Reports",
                   page_icon="📊", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📊", title=t("report.title"), subtitle=t("report.caption"))


# ---- Month selector -------------------------------------------------------

now = datetime.now()
months_list = []
for i in range(12):
    y = now.year
    m = now.month - i
    if m <= 0:
        m += 12
        y -= 1
    months_list.append(f"{y}-{m:02d}")

c1, c2 = st.columns([1, 4])
with c1:
    selected_month = st.selectbox(
        t("report.month_select"),
        months_list,
        index=0,
        format_func=lambda m: m,
    )


# ---- Monthly P&L ----------------------------------------------------------

st.divider()
st.markdown("### " + t("report.pnl_title"))

try:
    data = pnl.monthly_pnl(selected_month)
except Exception as e:
    st.error(str(e))
    st.stop()

if data["order_count"] == 0:
    st.info(t("report.no_data"))
else:
    # KPI row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        metric_with_hint(
            t("report.revenue"), "{:,.0f}".format(data["revenue"]),
            hint="", hint_tone="info",
        )
    with k2:
        metric_with_hint(
            t("report.cogs"), "-{:,.0f}".format(data["cogs"]),
            hint="", hint_tone="info",
        )
    with k3:
        metric_with_hint(
            t("report.fees"), "-{:,.0f}".format(data["platform_fees"]),
            hint="", hint_tone="info",
        )
    with k4:
        metric_with_hint(
            t("report.expenses"), "-{:,.0f}".format(data["expenses"]),
            hint="", hint_tone="info",
        )
    with k5:
        net_tone = "danger" if data["net_profit"] < 0 else "ok"
        metric_with_hint(
            t("report.net_profit"),
            "{:,.0f}".format(data["net_profit"]),
            hint=t("report.net_margin") + ": " + "{:.1f}%".format(data["net_margin"]),
            hint_tone=net_tone,
        )

    # Waterfall breakdown
    st.markdown("#### " + t("report.breakdown"))

    items = [
        (t("report.revenue"), data["revenue"], "#4d6c5c"),
        (t("report.cogs"), -data["cogs"], "#c54c4c"),
        (t("report.gross_profit"), data["gross_profit"], "#4d6c5c" if data["gross_profit"] > 0 else "#c54c4c"),
        (t("report.fees"), -data["platform_fees"], "#c5963d"),
        (t("report.expenses"), -data["expenses"], "#c5963d"),
    ]
    # Expense breakdown
    for cat, amt in data.get("expense_breakdown", {}).items():
        cat_label = t("exp.cat_" + cat)
        items.append(("  - " + cat_label, -amt, "#9a9485"))
    items.extend([
        (t("report.returns_loss"), -data["returns_loss"], "#c54c4c"),
        (t("report.net_profit"), data["net_profit"],
         "#4d6c5c" if data["net_profit"] > 0 else "#c54c4c"),
    ])

    for label, amount, color in items:
        is_total = label in (t("report.gross_profit"), t("report.net_profit"))
        weight = "700" if is_total else "400"
        border = "border-top:1px solid rgba(40,30,20,0.1);" if is_total else ""
        sign = "+" if amount > 0 else ""
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:8px 14px;" + border +
            "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span style='font-weight:" + weight + "'>" + label + "</span>"
            "<span style='color:" + color + ";font-weight:" + weight +
            ";font-variant-numeric:tabular-nums'>" +
            sign + "{:,.0f}".format(amount) + " ฿</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Download CSV
    csv_data = pnl.to_csv(data)
    st.download_button(
        t("report.download_csv"),
        data=csv_data.encode("utf-8-sig"),
        file_name="pnl_" + selected_month + ".csv",
        mime="text/csv",
    )

    # 6-month trend
    st.markdown("#### " + t("report.trend_title"))
    try:
        import pandas as pd
        trend = pnl.multi_month_pnl(6)
        if len(trend) > 1:
            tdf = pd.DataFrame(trend)
            chart_df = tdf.set_index("month")[["revenue", "net_profit"]]
            chart_df.columns = [t("report.revenue"), t("report.net_profit")]
            st.line_chart(chart_df, width="stretch")
        else:
            st.caption(t("report.need_more_data"))
    except Exception:
        st.caption(t("report.need_more_data"))


# ---- Order Analytics -------------------------------------------------------

st.divider()
st.markdown("### " + t("analytics.title"))

with db.conn() as c:
    has_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

if not has_orders:
    st.info(t("report.no_data"))
    st.stop()

# Peak hours + Best day
col_h, col_d = st.columns(2)

with col_h:
    st.markdown("#### " + t("analytics.peak_hours"))
    hourly = oa.hourly_distribution()
    if hourly:
        import pandas as pd
        hdf = pd.DataFrame(hourly)
        hdf["label"] = hdf["hour"].apply(lambda h: "{:02d}:00".format(h))
        hdf = hdf.set_index("label")
        st.bar_chart(hdf[["revenue"]], width="stretch")

        peaks = oa.peak_hours(3)
        for p in peaks:
            st.markdown(
                "<span style='background:rgba(77,108,92,0.1);padding:3px 10px;"
                "border-radius:8px;font-size:13px;margin-right:6px'>"
                + t("report.peak_hour_badge",
                    hour="{:02d}".format(p["hour"]),
                    amount="{:,.0f}".format(p.get("revenue", 0)))
                + "</span>",
                unsafe_allow_html=True,
            )
        st.caption(t("analytics.peak_hint"))
    else:
        st.caption(t("report.no_data"))

DAY_NAMES = {
    0: t("analytics.sun"), 1: t("analytics.mon"), 2: t("analytics.tue"),
    3: t("analytics.wed"), 4: t("analytics.thu"), 5: t("analytics.fri"),
    6: t("analytics.sat"),
}

with col_d:
    st.markdown("#### " + t("analytics.best_day"))
    daily = oa.daily_distribution()
    if daily:
        import pandas as pd
        ddf = pd.DataFrame(daily)
        ddf["label"] = ddf["dow"].map(DAY_NAMES)
        ddf = ddf.set_index("label")
        st.bar_chart(ddf[["revenue"]], width="stretch")

        best = oa.best_day()
        if best:
            day_name = DAY_NAMES.get(best["dow"], "?")
            st.markdown(
                "<div style='text-align:center;padding:8px;background:rgba(77,108,92,0.06);"
                "border-radius:10px;margin-top:8px'>"
                "👑 " + t("analytics.best_is") + " <strong>" + day_name +
                "</strong> — ฿" + "{:,.0f}".format(best.get("revenue", 0)) +
                "</div>",
                unsafe_allow_html=True,
            )
    else:
        st.caption(t("report.no_data"))


# AOV + Repeat rate
col_a, col_r = st.columns(2)

with col_a:
    st.markdown("#### " + t("analytics.aov_trend"))
    aov = oa.aov_trend()
    if aov:
        import pandas as pd
        adf = pd.DataFrame(aov)
        adf["aov"] = adf["aov"].round(0)
        adf = adf.set_index("month")
        st.line_chart(adf[["aov"]], width="stretch")
    else:
        st.caption(t("report.no_data"))

with col_r:
    st.markdown("#### " + t("analytics.repeat_rate"))
    rr = oa.repeat_purchase_rate()
    st.markdown(
        "<div style='text-align:center;padding:20px;background:rgba(77,108,92,0.04);"
        "border-radius:12px'>"
        "<div style='font-size:2.5rem;font-weight:600;color:#4d6c5c'>"
        + str(rr["repeat_rate"]) + "%</div>"
        "<div style='color:#7a7569;font-size:13px'>"
        + str(rr["repeat_buyers"]) + " / " + str(rr["total_buyers"]) + " " +
        t("analytics.buyers_repeat") + "</div></div>",
        unsafe_allow_html=True,
    )


# Frequently bought together
st.markdown("#### " + t("analytics.combos"))
combos = oa.top_combos()
if combos:
    for c in combos:
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>🔗 " + c["sku_a"] + " + " + c["sku_b"] + "</div>"
            "<div style='color:#4d6c5c;font-weight:600'>" +
            str(c["freq"]) + " " + t("analytics.times") + "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.caption(t("analytics.combo_hint"))
else:
    st.caption(t("analytics.no_combos"))
