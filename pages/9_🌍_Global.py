"""Global Markets — compare net profit per country / marketplace for a single
product or your whole catalog. The killer question for cross-border sellers:
"Where should I sell this?" """
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import fees as fees_mod
import onboarding
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from i18n_inline import marketplace_fee_label
from _components import page_header

db.init()
st.set_page_config(page_title="nirva.sell · Global", page_icon="🌍", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="🌍", title=t("global.title"), subtitle=t("global.caption"))
onboarding.tip("global", "tip.global")


# ---- Single-product compare -----------------------------------------------

fees = fees_mod.load()
all_platforms = list(fees.keys())
currency = st.session_state.get("currency", "USD")

c1, c2 = st.columns([1, 2])
with c1:
    cost_thb = st.number_input(t("pricing.cost") + " (THB)", min_value=0, value=15200, step=10)
    sell_thb = st.number_input(t("common.sell") + " (THB)", min_value=0, value=17480, step=10)
with c2:
    platforms = st.multiselect(
        t("global.pick_platforms"),
        all_platforms,
        default=all_platforms,
        format_func=marketplace_fee_label,
    )

if not platforms:
    st.info(t("global.pick_at_least_one"))
    st.stop()


rows = []
for p in platforms:
    np_data = fees_mod.net_profit(cost_thb, sell_thb, p, fees)
    f = fees[p]
    sell_local = fees_mod.convert_from_thb(sell_thb, f["currency"])
    net_local = fees_mod.convert_from_thb(np_data["net"], f["currency"])
    fee_pct = (f["commission_pct"] + f["payment_pct"] + f["transaction_pct"])
    rows.append({
        t("global.platform"): marketplace_fee_label(p),
        t("global.local_currency"): f["currency"],
        t("global.sell_local"): sell_local,
        t("global.fee_pct"): f"{fee_pct:.1f}%",
        t("global.net_local"): net_local,
        t("global.margin"): np_data["margin_pct"],
    })

df = pd.DataFrame(rows).sort_values(t("global.net_local"), ascending=False).reset_index(drop=True)

st.markdown(f"### {t('global.ranking')}")
st.dataframe(
    df,
    width='stretch',
    hide_index=True,
    column_config={
        t("global.sell_local"): st.column_config.NumberColumn(format="%.2f"),
        t("global.net_local"): st.column_config.NumberColumn(format="%.2f"),
        t("global.margin"): st.column_config.NumberColumn(format="%.1f%%"),
    },
)

best = df.iloc[0]
st.success(t("global.winner", platform=best[t("global.platform")], currency=best[t("global.local_currency")], net=f"{best[t('global.net_local')]:.2f}"))


# ---- Whole-catalog scan ---------------------------------------------------

st.divider()
st.subheader(t("global.catalog_scan"))

with db.conn() as c:
    products = c.execute("SELECT id, sku, name, cost_price, sell_price FROM products").fetchall()

if not products:
    st.caption(t("catalog.empty"))
    st.stop()

# For every product compute best platform.
agg = []
for prod in products:
    cost = float(prod["cost_price"] or 0)
    sell = int(prod["sell_price"] or 0)
    if not cost or not sell:
        continue
    nets = {p: fees_mod.net_profit(cost, sell, p, fees)["net"] for p in platforms}
    best = max(nets, key=nets.get)
    agg.append({
        "SKU": prod["sku"],
        t("upload.field.name").rstrip(" *"): (prod["name"] or "")[:50],
        t("common.cost"): cost,
        t("common.sell"): sell,
        t("global.best_platform"): marketplace_fee_label(best),
        t("global.best_net_thb"): int(nets[best]),
    })

if agg:
    cat_df = pd.DataFrame(agg).sort_values(t("global.best_net_thb"), ascending=False)
    st.dataframe(
        cat_df,
        width='stretch',
        hide_index=True,
        column_config={
            t("common.cost"): st.column_config.NumberColumn(format="฿%d"),
            t("common.sell"): st.column_config.NumberColumn(format="฿%d"),
            t("global.best_net_thb"): st.column_config.NumberColumn(format="฿%d"),
        },
        height=400,
    )

    # Roll-up: which platform wins most often?
    wins = cat_df[t("global.best_platform")].value_counts()
    st.caption(t("global.win_distribution"))
    win_df = pd.DataFrame({
        t("global.platform"): wins.index,
        t("global.wins"): wins.values,
    })
    st.bar_chart(win_df.set_index(t("global.platform")))
