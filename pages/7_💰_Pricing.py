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


# ---- v58: AI Price Optimizer — find optimal price per platform -----------

st.divider()
st.subheader(f"🎯 {t('pricing.optimizer_title')}")
st.caption(t("pricing.optimizer_help"))

import price_optimizer as po

cO1, cO2, cO3 = st.columns(3)
with cO1:
    opt_cost = st.number_input(
        t("pricing.opt_cost"), min_value=0.0, value=float(cost), step=10.0,
        key="_opt_cost",
    )
with cO2:
    opt_margin = st.number_input(
        t("pricing.opt_margin"), min_value=1.0, max_value=80.0,
        value=20.0, step=1.0, key="_opt_margin",
    )
with cO3:
    opt_ship = st.number_input(
        t("pricing.opt_shipping"), min_value=0.0, value=0.0, step=5.0,
        key="_opt_ship",
    )

if opt_cost > 0:
    comparisons = po.compare_platforms(
        cost=opt_cost, target_margin_pct=opt_margin, shipping=opt_ship,
    )

    for r in comparisons:
        if r.get("error"):
            st.markdown(
                "<div style='padding:10px 14px;background:rgba(197,76,76,0.06);"
                "border-radius:8px;margin-bottom:6px;font-size:13px'>"
                "❌ <strong>" + r.get("platform_label", r["platform"]) + "</strong> — "
                + t("pricing.margin_too_high", max=r.get("max_margin", 0)) +
                "</div>",
                unsafe_allow_html=True,
            )
            continue

        suggested = r["suggested"]
        actual_m = r["actual_margin_pct"]
        fee_pct = r["fee_rate_pct"]
        color = "#4d6c5c" if actual_m >= opt_margin else "#c5963d"

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-radius:10px;margin-bottom:6px'>"
            "<div><strong>" + r.get("platform_label", r["platform"]) + "</strong>"
            "<span style='color:#7a7569;font-size:12px;margin-left:8px'>"
            "fee " + str(fee_pct) + "%</span></div>"
            "<div style='display:flex;gap:18px;align-items:baseline'>"
            "<div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;"
            "font-weight:500;color:#1c1c1c'>฿" + "{:,}".format(suggested) + "</div>"
            "<div style='color:" + color + ";font-size:13px;font-weight:600'>"
            + "{:.1f}".format(actual_m) + "% margin</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )

    # Quick "what if" — seller types a price and sees margin per platform
    st.markdown(f"#### 🔍 {t('pricing.whatif_title')}")
    whatif_price = st.number_input(
        t("pricing.whatif_price"), min_value=0.0,
        value=float(comparisons[0].get("suggested", 0)) if comparisons else 0.0,
        step=10.0, key="_whatif",
    )
    if whatif_price > 0:
        wf_cols = st.columns(min(len(comparisons), 4))
        for i, r in enumerate(comparisons[:4]):
            m = po.margin_at_price(opt_cost, whatif_price, r["platform"], opt_ship)
            tone = "#4d6c5c" if m["margin_pct"] >= 15 else (
                "#c5963d" if m["margin_pct"] >= 5 else "#c54c4c")
            with wf_cols[i]:
                st.markdown(
                    "<div style='text-align:center;padding:10px'>"
                    "<div style='font-size:11px;text-transform:uppercase;"
                    "letter-spacing:0.10em;color:#7a7569'>"
                    + r.get("platform_label", r["platform"])[:12] + "</div>"
                    "<div style='font-family:Cormorant Garamond,serif;"
                    "font-size:1.6rem;color:" + tone + "'>"
                    + "{:.1f}".format(m["margin_pct"]) + "%</div>"
                    "<div style='font-size:12px;color:#7a7569'>net ฿"
                    + "{:,.0f}".format(m["net"]) + "</div></div>",
                    unsafe_allow_html=True,
                )
