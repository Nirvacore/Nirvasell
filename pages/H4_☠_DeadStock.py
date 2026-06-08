"""H4 Dead Stock Detector — find slow/dead SKUs before they eat capital."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import dead_stock as ds
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("dead.title"))
st.caption(t("dead.caption"))

days = st.segmented_control(t("dead.period"), [30, 60, 90], default=60,
    format_func=lambda d: str(d) + t("dead.days"))
summary = ds.summary(days=int(days or 60))

c1, c2, c3 = st.columns(3)
c1.metric(t("dead.kpi_dead"), summary.get("dead_count",0),
          delta_color="inverse" if summary.get("dead_count",0) > 0 else "off")
c2.metric(t("dead.kpi_slow"), summary.get("slow_count",0))
c3.metric(t("dead.kpi_value"), "฿{:,.0f}".format(summary.get("dead_stock_value",0)),
          delta_color="inverse" if summary.get("dead_stock_value",0) > 0 else "off")

if summary.get("dead_stock_value",0) > 0:
    st.warning("⚠️ " + t("dead.capital_warning") + " ฿{:,.0f}".format(summary.get("dead_stock_value",0)))

st.divider()
items = ds.detect(days=int(days or 60))
if not items:
    st.success(t("dead.all_clear"))
else:
    actions = ds.suggest_actions(items)
    action_map = {a.get("sku"): a for a in actions} if actions else {}

    for item in items:
        sku   = item.get("sku","?")
        name  = item.get("name") or sku
        stock = item.get("stock",0)
        val   = item.get("stock_value",0)
        age   = item.get("days_no_sale",0)
        status= item.get("status","slow")
        color = "#c54c4c" if status == "dead" else "#c5963d"
        label = ("☠️" if status=="dead" else "🐌") + " **" + name + "**" + \
                " · " + sku + " · " + str(stock) + t("dead.pcs") + \
                " · ฿{:,.0f}".format(val) + " · " + str(age) + t("dead.no_sale_days")
        with st.expander(label):
            action_info = action_map.get(sku,{})
            suggestion  = action_info.get("suggestion") or action_info.get("action","")
            disc_price  = action_info.get("discount_price",0)
            col1, col2 = st.columns(2)
            col1.write(t("dead.cost_price") + ": ฿{:,.2f}".format(item.get("cost_price",0)))
            col2.write(t("dead.sell_price") + ": ฿{:,.2f}".format(item.get("sell_price",0)))
            if suggestion:
                st.html("<div style='color:" + color + ";font-size:0.85rem;margin-top:4px'>💡 " +
                        suggestion + (" — ฿{:,.0f}".format(disc_price) if disc_price else "") +
                        "</div>")
