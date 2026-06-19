"""Price History — track cost and sell price changes per SKU over time."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import price_history as ph
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Price History",
                   page_icon="📉", layout="wide")
apply_theme()
require_auth()
db.init()
ph.init()
render_sidebar()

page_header(icon="📉", title=t("phist.title"), subtitle=t("phist.caption"))

s = ph.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("📝 " + t("phist.kpi_changes"), str(s["total_changes"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("📅 " + t("phist.kpi_this_month"), str(s["this_month"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("📦 " + t("phist.kpi_skus"), str(s["skus_with_history"]),
                     hint="", hint_tone="info")

# ---- Update price (with history) -------------------------------------------
st.divider()
st.markdown("### ✏️ " + t("phist.update_title"))

with st.form("update_price"):
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, cost_price, sell_price FROM products ORDER BY sku"
        ).fetchall()

    if not products:
        st.info(t("phist.no_products"))
    else:
        prod_opts = [
            p["sku"] + " — " + (p["name"] or "")[:25] +
            " (" + t("common.cost_price") + " ฿" + "{:,.0f}".format(p["cost_price"] or 0) +
            " / " + t("common.sell_price") + " ฿" + "{:,.0f}".format(p["sell_price"] or 0) + ")"
            for p in products
        ]
        sel_idx = st.selectbox(
            t("phist.f_sku"), range(len(prod_opts)),
            format_func=lambda i: prod_opts[i],
            key="_ph_sku",
        )
        selected_prod = products[sel_idx]

        uc1, uc2, uc3 = st.columns(3)
        with uc1:
            new_cost = st.number_input(
                t("phist.f_new_cost"),
                value=float(selected_prod["cost_price"] or 0),
                min_value=0.0, step=10.0, key="_ph_cost",
            )
        with uc2:
            new_sell = st.number_input(
                t("phist.f_new_sell"),
                value=float(selected_prod["sell_price"] or 0),
                min_value=0.0, step=10.0, key="_ph_sell",
            )
        with uc3:
            reason = st.text_input(
                t("phist.f_reason"),
                placeholder=t("phist.reason_ph"),
            )

        if st.form_submit_button(t("phist.update_btn"), type="primary"):
            sku = selected_prod["sku"]
            old_cost = selected_prod["cost_price"] or 0
            old_sell = selected_prod["sell_price"] or 0

            if new_cost != old_cost or new_sell != old_sell:
                ph.update_price_with_record(
                    sku,
                    new_cost=new_cost if new_cost != old_cost else None,
                    new_sell=new_sell if new_sell != old_sell else None,
                    reason=reason.strip(),
                )
                toast(t("phist.updated"), icon="✓")
                st.rerun()
            else:
                st.info(t("phist.no_change"))

# ---- SKU price trend -------------------------------------------------------
st.divider()
st.markdown("### 📊 " + t("phist.trend_title"))

if products:
    sel_view_idx = st.selectbox(
        t("phist.f_view_sku"),
        range(len(products)),
        format_func=lambda i: products[i]["sku"] + " — " +
        (products[i]["name"] or "")[:30],
        key="_ph_view",
    )
    view_sku = products[sel_view_idx]["sku"]
    trend = ph.price_trend(view_sku)

    if not trend.get("has_history"):
        st.info(t("phist.no_history"))
    else:
        import pandas as pd

        cost_pts = trend.get("cost_points", [])
        sell_pts = trend.get("sell_points", [])

        if cost_pts or sell_pts:
            dates = sorted(set(
                [p["date"] for p in cost_pts] +
                [p["date"] for p in sell_pts]
            ))
            cost_map = {p["date"]: p["price"] for p in cost_pts}
            sell_map = {p["date"]: p["price"] for p in sell_pts}

            df_data = []
            for d in dates:
                df_data.append({
                    "date": d,
                    t("common.cost_price"): cost_map.get(d),
                    t("common.sell_price"): sell_map.get(d),
                })

            df = pd.DataFrame(df_data).set_index("date")
            st.line_chart(df)

# ---- Recent changes feed ---------------------------------------------------
st.divider()
st.markdown("### " + t("phist.recent_title"))

recent = ph.recent_changes(30, 30)
if not recent:
    st.info(t("phist.no_recent"))
else:
    for r in recent:
        cost_d = r.get("cost_delta")
        sell_d = r.get("sell_delta")

        parts = []
        if r["old_cost"] is not None and r["new_cost"] is not None:
            arrow = "↑" if (r["new_cost"] > r["old_cost"]) else "↓"
            c_color = "#c54c4c" if arrow == "↑" else "#4d6c5c"
            parts.append(
                "<span style='color:" + c_color + "'>ทุน " + arrow +
                " ฿{:,.0f}".format(r["old_cost"]) + "→฿{:,.0f}".format(r["new_cost"]) +
                "</span>"
            )
        if r["old_sell"] is not None and r["new_sell"] is not None:
            arrow = "↑" if (r["new_sell"] > r["old_sell"]) else "↓"
            s_color = "#4d6c5c" if arrow == "↑" else "#c54c4c"
            parts.append(
                "<span style='color:" + s_color + "'>ราคาขาย " + arrow +
                " ฿{:,.0f}".format(r["old_sell"]) + "→฿{:,.0f}".format(r["new_sell"]) +
                "</span>"
            )

        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "align-items:center;padding:8px 14px;"
            "border-bottom:0.5px solid rgba(40,30,20,0.04)'>"
            "<div>"
            "<strong>" + r["sku"] + "</strong>"
            " <span style='color:#9a9485;font-size:11px'>"
            + (r.get("product_name") or "")[:25] + "</span>"
            + (" " + " · ".join(parts) if parts else "") +
            ("  <span style='color:#9a9485;font-size:11px'>— " +
             r["reason"] + "</span>" if r.get("reason") else "") +
            "</div>"
            "<span style='font-size:11px;color:#9a9485'>"
            + r["change_date"][:10] + "</span></div>",
            unsafe_allow_html=True,
        )
