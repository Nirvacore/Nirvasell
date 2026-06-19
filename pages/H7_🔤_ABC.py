"""H7 ABC Analysis — classify SKUs by revenue contribution (A/B/C)."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import abc_analysis as abc
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("abcx.title"))
st.caption(t("abcx.caption"))

summary = abc.summary()
CLASS_COLORS = {"A":"#4d6c5c","B":"#c5963d","C":"#9a9485"}
CLASS_ICONS  = {"A":"⭐","B":"🔵","C":"⚫"}

c1, c2, c3 = st.columns(3)
for col, cls in zip([c1, c2, c3], ["A","B","C"]):
    info = summary.get(cls, {})
    col.metric(
        CLASS_ICONS[cls] + " " + t("abcx.class_" + cls),
        str(info.get("count",0)) + t("abcx.skus"),
        delta=t("abcx.revenue") + ": " + str(round(info.get("revenue_pct",0),1)) + "%",
        delta_color="off"
    )

invest = abc.investment_advice()
if invest:
    st.info("💡 " + str(invest) if isinstance(invest, str) else "💡 " + invest.get("advice",""))

st.divider()
tab_all, tab_a, tab_b, tab_c = st.tabs([
    t("abcx.tab_all"), "⭐ A", "🔵 B", "⚫ C"
])

def _render_items(items):
    if not items:
        st.info(t("abcx.empty"))
        return
    for item in items:
        cls     = item.get("class","C")
        sku     = item.get("sku","?")
        name    = item.get("name") or sku
        rev_pct = item.get("revenue_pct",0)
        cum_pct = item.get("cumulative_pct",0)
        rev     = item.get("total_revenue",0)
        sv      = item.get("stock_value",0)
        color   = CLASS_COLORS.get(cls,"#9a9485")
        icon    = CLASS_ICONS.get(cls,"⚫")
        label   = icon + " **" + name + "**" + \
                  t("abcx.expander_rev", pct=str(rev_pct)) + \
                  " · ฿{:,.0f}".format(rev) + \
                  t("abcx.expander_stock", amount="{:,.0f}".format(sv))
        with st.expander(label):
            c1, c2, c3 = st.columns(3)
            c1.metric(t("abcx.revenue"), "฿{:,.0f}".format(rev))
            c2.metric(t("abcx.stock_value"), "฿{:,.0f}".format(sv))
            c3.metric(t("abcx.cumulative"), str(cum_pct) + "%")
            qty = item.get("total_qty",0)
            st.write(t("abcx.qty_sold") + ": " + str(qty) +
                     " | " + t("abcx.cost") + ": ฿{:,.2f}".format(item.get("cost_price",0)) +
                     " | " + t("abcx.sell") + ": ฿{:,.2f}".format(item.get("sell_price",0)))
            st.html("<div style='color:" + color + ";font-size:0.8rem;margin-top:2px'>" +
                    t("abcx.class") + " " + cls + "</div>")

with tab_all:
    all_items = abc.classify()
    _render_items(all_items)

with tab_a:
    _render_items(abc.class_items("A"))

with tab_b:
    _render_items(abc.class_items("B"))

with tab_c:
    _render_items(abc.class_items("C"))
