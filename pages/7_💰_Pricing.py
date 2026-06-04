"""Pricing Assistant — paste competitor prices → smart suggestion + true profit."""
from __future__ import annotations
import re
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
from _components import page_header

db.init()
st.set_page_config(page_title="nirva · Pricing", page_icon="💰", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="💰", title=t("pricing.title"), subtitle=t("pricing.caption"))
onboarding.tip("pricing")


# ----- Inputs -------------------------------------------------------------

c1, c2 = st.columns([1, 2])
with c1:
    cost = st.number_input(t("pricing.cost"), min_value=0, value=15200, step=10)
    min_margin = st.number_input(t("pricing.min_margin"), min_value=0.0, max_value=80.0, value=8.0, step=0.5)
with c2:
    raw = st.text_area(
        t("pricing.competitor_prices"),
        placeholder=t("pricing.competitor_placeholder"),
        height=160,
    )

# Parse competitor prices.
prices: list[float] = []
for line in raw.splitlines():
    nums = re.findall(r"[\d.,]+", line)
    for n in nums:
        try:
            v = float(n.replace(",", ""))
            if v >= 50:  # ignore tiny numbers like "1" or "2"
                prices.append(v)
        except ValueError:
            pass


# ----- Analysis -----------------------------------------------------------

if not prices:
    st.info(t("pricing.competitor_placeholder").split("\n")[0])
    st.stop()

import statistics
avg = statistics.mean(prices)
lo = min(prices)
hi = max(prices)

m1, m2, m3 = st.columns(3)
m1.metric(t("pricing.competitor_avg"), f"฿{avg:,.0f}")
m2.metric(t("pricing.competitor_min"), f"฿{lo:,.0f}")
m3.metric(t("pricing.competitor_max"), f"฿{hi:,.0f}")


# Strategies — three different price points the user can choose from.
fees = fees_mod.load()

strategies = [
    {
        "name": "🎯 Match avg",
        "price": int(round(avg / 10) * 10),
        "note": "ขายเท่าราคากลาง — ปลอดภัย",
    },
    {
        "name": "💸 Undercut min",
        "price": int(round((lo - 50) / 10) * 10),
        "note": "ต่ำกว่าคู่แข่งถูกสุด ฿50 — เร่งขายเร็ว",
    },
    {
        "name": "💎 Premium",
        "price": int(round(hi * 1.02 / 10) * 10),
        "note": "สูงกว่าคู่แข่งสูงสุด 2% — เน้น quality + ประกัน",
    },
]

st.divider()
st.subheader(t("pricing.strategy"))

table_rows = []
warning = None

for s in strategies:
    sell = s["price"]
    per_platform = {p: fees_mod.net_profit(cost, sell, p, fees) for p in fees}
    best = max(per_platform, key=lambda p: per_platform[p]["net"])
    best_net = per_platform[best]["net"]
    best_margin = per_platform[best]["margin_pct"]

    row = {
        t("pricing.strategy"): s["name"],
        t("pricing.suggested"): sell,
        t("pricing.competitor_avg") + " Δ": f"{(sell - avg) / avg * 100:+.1f}%",
    }
    for p in fees:
        np = per_platform[p]
        label = fees[p]["label"]
        row[f"{label}\nnet"] = int(np["net"])
        row[f"{label}\n%"] = f"{np['margin_pct']:.1f}%"
    table_rows.append(row)

    # Check min margin
    if best_margin < min_margin and warning is None:
        # Compute price needed to hit min margin on best platform
        # net = sell - cost - fee(sell) - extra
        # fee ≈ sell * base_pct, so sell - cost - sell*base_pct = sell*(min_margin/100)
        # sell * (1 - base_pct - min_margin/100) = cost
        f = fees[best]
        base_pct = (f["commission_pct"] + f["payment_pct"] + f["transaction_pct"]) / 100
        vat = f["vat_on_fees"] / 100
        effective_fee_pct = base_pct * (1 + vat)
        denom = 1 - effective_fee_pct - (min_margin / 100)
        if denom > 0:
            needed = cost / denom
            warning = int(round(needed / 10) * 10)

df = pd.DataFrame(table_rows)
st.dataframe(
    df,
    width='stretch',
    hide_index=True,
    column_config={
        t("pricing.suggested"): st.column_config.NumberColumn(format="฿%d"),
    },
)

if warning:
    st.warning(t("pricing.warning_below_min", price=warning))

st.caption(t("ws.fee_note"))
