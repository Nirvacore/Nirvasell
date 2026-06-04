"""Performance Dashboard — close the loop. Upload orders → see what actually
sold + made profit. Reveals dead stock, best channel, top SKUs."""
from __future__ import annotations
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import order_import as oi
import fees as fees_mod
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from _components import page_header, metric_with_hint

db.init()
st.set_page_config(page_title="nirva.sell · Dashboard", page_icon="📈", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📈", title=t("dashboard.title"), subtitle=t("dashboard.caption"))


# ---- Upload orders -------------------------------------------------------

with st.expander(t("dashboard.upload_title"), expanded=True):
    st.caption(t("dashboard.upload_help"))
    up = st.file_uploader(
        t("dashboard.upload_label"),
        type=["csv", "xlsx", "xls", "tsv"],
        accept_multiple_files=False,
    )
    if up:
        raw = up.getvalue()
        try:
            raw_df = oi.read_orders_csv(raw, up.name)
        except Exception as e:
            st.error(str(e))
            st.stop()

        detected = oi.detect_platform(list(raw_df.columns))
        c1, c2 = st.columns([2, 1])
        with c1:
            st.success(t("dashboard.parsed", n=len(raw_df), platform=detected or "?"))
        with c2:
            platform = st.selectbox(
                t("dashboard.platform_label"),
                list(oi.SCHEMAS.keys()),
                index=list(oi.SCHEMAS.keys()).index(detected) if detected else 0,
            )

        normalized = oi.normalize(raw_df, platform)
        if normalized.empty:
            st.warning(t("dashboard.no_valid"))
        else:
            st.dataframe(
                normalized[["order_id", "sku", "qty", "unit_price", "total_price", "order_date"]].head(10),
                width='stretch',
                hide_index=True,
            )

            if st.button(t("dashboard.save_btn", n=len(normalized)), type="primary"):
                n = oi.save_orders(normalized)
                st.success(t("dashboard.saved", n=n))
                st.rerun()


# ---- Aggregate metrics ---------------------------------------------------

with db.conn() as c:
    total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

if total_orders == 0:
    st.info(t("dashboard.no_orders"))
    st.stop()

# Date filter
c_dr1, c_dr2 = st.columns([1, 4])
with c_dr1:
    days = st.selectbox(
        t("dashboard.range"),
        [7, 30, 90, 365, 9999],
        index=1,
        format_func=lambda d: {
            7: "7 " + t("dashboard.days"),
            30: "30 " + t("dashboard.days"),
            90: "90 " + t("dashboard.days"),
            365: "1 " + t("dashboard.year"),
            9999: t("dashboard.all_time"),
        }[d],
    )

cutoff = (datetime.now() - timedelta(days=days)).isoformat() if days < 9999 else "1900-01-01"

with db.conn() as c:
    # All orders + product join for cost data
    orders_df = pd.read_sql_query(
        """
        SELECT o.*, p.name AS product_name, p.brand, p.cost_price, p.sell_price
        FROM orders o
        LEFT JOIN products p ON p.id = o.product_id
        WHERE o.order_date >= ?
        """,
        c,
        params=(cutoff,),
    )

if orders_df.empty:
    st.info(t("dashboard.no_orders_window"))
    st.stop()

# Compute profit per order (revenue - cost - fee)
fees = fees_mod.load()
def _profit_row(r):
    cost = float(r.get("cost_price") or 0) * (r.get("qty") or 1)
    rev = float(r.get("total_price") or 0)
    fee = fees_mod.platform_fee(rev, r.get("platform") or "", fees)
    return rev - cost - fee

orders_df["profit"] = orders_df.apply(_profit_row, axis=1)
orders_df["cost_total"] = orders_df["cost_price"].fillna(0) * orders_df["qty"]


# ---- Top-line KPIs -------------------------------------------------------

st.divider()
total_rev = orders_df["total_price"].sum()
total_cost = orders_df["cost_total"].sum()
total_profit = orders_df["profit"].sum()
margin = (total_profit / total_rev * 100) if total_rev else 0
order_count = len(orders_df)
unit_count = int(orders_df["qty"].sum())

# v49: Etsy-style — every KPI carries an actionable hint underneath
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    metric_with_hint(
        t("dashboard.kpi_revenue"), f"฿{total_rev:,.0f}",
        hint=t("dashboard.hint_revenue") if total_rev == 0 else "",
        hint_target="pages/5_🔌_Import.py" if total_rev == 0 else None,
        hint_tone="warn" if total_rev == 0 else "info",
    )
with m2:
    metric_with_hint(
        t("dashboard.kpi_cost"), f"฿{total_cost:,.0f}",
        hint=t("dashboard.hint_cost") if total_cost == 0 else "",
        hint_target="pages/2_📦_Catalog.py" if total_cost == 0 else None,
        hint_tone="warn" if total_cost == 0 else "info",
    )
with m3:
    metric_with_hint(
        t("dashboard.kpi_profit"), f"฿{total_profit:,.0f}",
        hint=t("dashboard.hint_loss") if total_profit < 0 else "",
        hint_tone="danger" if total_profit < 0 else "info",
    )
with m4:
    # Margin tone tiers: <5 danger, <10 warn, ≥10 ok
    m_tone = "danger" if margin < 5 else ("warn" if margin < 10 else "ok")
    m_hint = (t("dashboard.hint_margin_low") if margin < 10
              else t("dashboard.hint_margin_ok") if margin >= 20 else "")
    metric_with_hint(
        t("dashboard.kpi_margin"), f"{margin:.1f}%",
        hint=m_hint,
        hint_target="pages/D_🔀_Sourcing.py" if margin < 10 else None,
        hint_tone=m_tone,
    )
with m5:
    metric_with_hint(
        t("dashboard.kpi_orders"), f"{order_count} / {unit_count}u",
        hint=t("dashboard.hint_no_orders") if order_count == 0 else "",
        hint_target="pages/5_🔌_Import.py" if order_count == 0 else None,
        hint_tone="info",
    )


# ---- Daily revenue chart -------------------------------------------------

st.markdown(f"### {t('dashboard.daily_chart')}")
orders_df["order_date_d"] = pd.to_datetime(orders_df["order_date"], errors="coerce").dt.date
daily = (
    orders_df.dropna(subset=["order_date_d"])
    .groupby("order_date_d")[["total_price", "profit"]]
    .sum()
    .rename(columns={"total_price": t("dashboard.kpi_revenue"), "profit": t("dashboard.kpi_profit")})
)
if not daily.empty:
    st.line_chart(daily, width='stretch')


# ---- Channel mix ---------------------------------------------------------

st.markdown(f"### {t('dashboard.channel_mix')}")
channel = orders_df.groupby("platform").agg(
    revenue=("total_price", "sum"),
    profit=("profit", "sum"),
    orders=("order_id", "count"),
).reset_index()
channel["margin %"] = (channel["profit"] / channel["revenue"] * 100).round(1)
st.dataframe(
    channel,
    width='stretch',
    hide_index=True,
    column_config={
        "revenue": st.column_config.NumberColumn(format="฿%.0f"),
        "profit":  st.column_config.NumberColumn(format="฿%.0f"),
    },
)


# ---- Top performers + dead stock -----------------------------------------

t_col, d_col = st.columns(2)

with t_col:
    st.markdown(f"### {t('dashboard.top_skus')}")
    top = (
        orders_df.groupby(["sku", "product_name"])
        .agg(units=("qty", "sum"), revenue=("total_price", "sum"), profit=("profit", "sum"))
        .reset_index()
        .sort_values("profit", ascending=False)
        .head(10)
    )
    st.dataframe(
        top,
        width='stretch',
        hide_index=True,
        column_config={
            "revenue": st.column_config.NumberColumn(format="฿%.0f"),
            "profit":  st.column_config.NumberColumn(format="฿%.0f"),
        },
    )

with d_col:
    st.markdown(f"### {t('dashboard.dead_stock')}")
    st.caption(t("dashboard.dead_stock_help"))
    with db.conn() as c:
        all_products = pd.read_sql_query(
            "SELECT id, sku, name, cost_price, sell_price FROM products",
            c,
        )
    selling_skus = set(orders_df["sku"].dropna().unique())
    dead = all_products[~all_products["sku"].isin(selling_skus)]
    if dead.empty:
        st.success(t("dashboard.no_dead"))
    else:
        st.dataframe(
            dead[["sku", "name", "cost_price", "sell_price"]].head(20),
            width='stretch',
            hide_index=True,
            column_config={
                "cost_price": st.column_config.NumberColumn(format="฿%.0f"),
                "sell_price": st.column_config.NumberColumn(format="฿%.0f"),
            },
        )
        st.caption(t("dashboard.dead_n", n=len(dead)))
