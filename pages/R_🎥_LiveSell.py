"""Live Commerce Console — companion screen for TikTok / Facebook Live.

Thai resellers do live sales on their phone in TikTok/FB. They need a
SECOND screen (laptop next to phone) that shows:
  • What product is on display right now — big price + stock at a glance
  • Countdown timer for the deal ("ลดถึงเที่ยงคืนเท่านั้น")
  • CF tally — paste chat → extract "CF1 / CF2 / +1" patterns, count viewers
  • One-click swap to next SKU
  • AI caption generator for the current product (uses tiktok_live task)

Zero competitor in TH has this integrated. Page365 ProLive does live chat
automation but no big-screen seller console."""
from __future__ import annotations
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import inventory as inv
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, toast, friendly_error
from i18n import t

st.set_page_config(page_title="nirva.sell · Live Console",
                   page_icon="🎥", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🎥", title=t("livesell.title"), subtitle=t("livesell.caption"))


# ---- State -------------------------------------------------------------

if "_live_started_at" not in st.session_state:
    st.session_state["_live_started_at"] = None
if "_live_duration_min" not in st.session_state:
    st.session_state["_live_duration_min"] = 60
if "_live_current_sku" not in st.session_state:
    st.session_state["_live_current_sku"] = None
if "_live_chat_text" not in st.session_state:
    st.session_state["_live_chat_text"] = ""


# ---- Helpers -----------------------------------------------------------

def _list_products() -> pd.DataFrame:
    with db.conn() as c:
        rows = c.execute(
            "SELECT id, sku, name, brand, cost_price, sell_price, stock, "
            "image_url FROM products ORDER BY id DESC LIMIT 200"
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


# Regex matches: CF1, CF 1, +1, cf123, CF เลข, etc.
_CF_PATTERNS = [
    re.compile(r"\bCF\s*(\d+)\b", re.IGNORECASE),
    re.compile(r"\+\s*(\d+)\b"),
]

def parse_cf_tally(text: str) -> dict[int, int]:
    """Return {cf_number: count_of_mentions}."""
    tally: dict[int, int] = {}
    for pat in _CF_PATTERNS:
        for m in pat.finditer(text):
            try:
                n = int(m.group(1))
            except ValueError:
                continue
            tally[n] = tally.get(n, 0) + 1
    return tally


# ---- Top row: countdown + product picker -------------------------------

products_df = _list_products()
if products_df.empty:
    st.info(t("livesell.no_products"))
    st.stop()

cT, cP = st.columns([1, 1])

# Left: countdown clock
with cT:
    st.markdown(
        "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
        "border-radius:14px;padding:24px 28px;min-height:200px;"
        "display:flex;flex-direction:column;justify-content:center'>",
        unsafe_allow_html=True,
    )

    if st.session_state["_live_started_at"] is None:
        st.markdown(
            f"<div style='font-size:11px;text-transform:uppercase;"
            f"letter-spacing:0.10em;color:#7a7569;text-align:center'>"
            f"{t('livesell.timer_label')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-family:\"Cormorant Garamond\",serif;font-size:3.6rem;"
            "font-weight:500;text-align:center;color:#1c1c1c;line-height:1.1;"
            "letter-spacing:-0.02em'>--:--</div>",
            unsafe_allow_html=True,
        )
        ca, cb = st.columns([2, 1])
        with ca:
            dur = st.number_input(
                t("livesell.duration_min"), 5, 240,
                st.session_state["_live_duration_min"], 5,
                label_visibility="collapsed",
            )
        with cb:
            if st.button(t("livesell.start"), type="primary", width="stretch"):
                st.session_state["_live_started_at"] = time.time()
                st.session_state["_live_duration_min"] = int(dur)
                st.rerun()
    else:
        elapsed = time.time() - st.session_state["_live_started_at"]
        total_sec = st.session_state["_live_duration_min"] * 60
        remaining = max(0, total_sec - int(elapsed))
        mm, ss = remaining // 60, remaining % 60
        color = "#4d6c5c" if remaining > 600 else ("#c5963d" if remaining > 60 else "#c54c4c")
        st.markdown(
            f"<div style='font-size:11px;text-transform:uppercase;"
            f"letter-spacing:0.10em;color:#7a7569;text-align:center'>"
            f"{'⏱ ' + t('livesell.timer_live') if remaining > 0 else '⏰ ' + t('livesell.timer_done')}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:5rem;"
            f"font-weight:500;text-align:center;color:{color};line-height:1;"
            f"letter-spacing:-0.03em;font-variant-numeric:tabular-nums'>"
            f"{mm:02d}:{ss:02d}</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button(t("livesell.reset"), width="stretch"):
                st.session_state["_live_started_at"] = None
                st.rerun()
        with c2:
            if st.button(t("livesell.refresh"), type="primary", width="stretch"):
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# Right: current product display
with cP:
    # SKU picker
    sku_list = products_df["sku"].tolist()
    cur_sku = st.session_state["_live_current_sku"]
    if cur_sku not in sku_list:
        cur_sku = sku_list[0]
    sel_sku = st.selectbox(
        t("livesell.pick_product"),
        options=sku_list,
        index=sku_list.index(cur_sku),
        format_func=lambda s: (lambda r:
            f"{s} · {r['name'][:40]}" if not r.empty else s
        )(products_df[products_df["sku"] == s].iloc[0]) if (products_df["sku"] == s).any() else s,
    )
    st.session_state["_live_current_sku"] = sel_sku
    prod = products_df[products_df["sku"] == sel_sku].iloc[0]

    stock_n = inv.parse_stock(prod.get("stock"))
    price = int(prod.get("sell_price") or 0)
    img_urls = [u for u in (prod.get("image_url") or "").split("|") if u]

    st.markdown(
        f"<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
        f"border-radius:14px;padding:24px 28px;min-height:200px'>"
        f"<div style='font-size:11px;text-transform:uppercase;"
        f"letter-spacing:0.10em;color:#7a7569'>"
        f"{t('livesell.on_air')}</div>"
        f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.8rem;"
        f"font-weight:500;color:#1c1c1c;line-height:1.2;margin-top:6px'>"
        f"{prod.get('name','')}</div>"
        f"<div style='display:flex;gap:24px;margin-top:14px;align-items:baseline'>"
        f"<div><span style='color:#7a7569;font-size:11px;text-transform:uppercase;"
        f"letter-spacing:0.10em'>{t('livesell.price')}</span><br/>"
        f"<span style='font-family:\"Cormorant Garamond\",serif;font-size:2.4rem;"
        f"font-weight:500;color:#4d6c5c'>฿{price:,}</span></div>"
        f"<div><span style='color:#7a7569;font-size:11px;text-transform:uppercase;"
        f"letter-spacing:0.10em'>{t('livesell.stock')}</span><br/>"
        f"<span style='font-family:\"Cormorant Garamond\",serif;font-size:2.4rem;"
        f"font-weight:500;color:{'#4d6c5c' if stock_n > 5 else '#c5963d' if stock_n > 0 else '#c54c4c'}'>"
        f"{stock_n}</span></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)


# ---- Bottom row: CF tracker + AI caption ------------------------------

cL, cR = st.columns([1, 1])

with cL:
    st.markdown(f"### 📋 {t('livesell.cf_tracker')}")
    st.caption(t("livesell.cf_hint"))
    chat_text = st.text_area(
        t("livesell.paste_chat"),
        value=st.session_state["_live_chat_text"],
        height=180,
        label_visibility="collapsed",
        placeholder="CF1\nCF1\n+1\nCF2 ของแถมไหม\nCF1 หนูเอาด้วยค่ะ\nCF3",
    )
    st.session_state["_live_chat_text"] = chat_text

    tally = parse_cf_tally(chat_text)
    if tally:
        total_orders = sum(tally.values())
        st.markdown(
            f"<div style='display:flex;gap:12px;flex-wrap:wrap;margin-top:8px'>"
            + "".join(
                f"<div style='background:rgba(77,108,92,0.06);border:0.5px solid "
                f"rgba(77,108,92,0.18);border-radius:8px;padding:8px 14px;"
                f"font-family:\"Cormorant Garamond\",serif;font-size:1.1rem'>"
                f"<span style='color:#7a7569;font-size:11px;letter-spacing:0.10em;"
                f"text-transform:uppercase'>CF{cf}</span> "
                f"<strong style='color:#1c1c1c;font-size:1.4rem'>×{n}</strong></div>"
                for cf, n in sorted(tally.items())
            )
            + "</div>"
            f"<div style='margin-top:14px;color:#7a7569;font-size:13px'>"
            f"{t('livesell.total_cf', n=total_orders)}</div>",
            unsafe_allow_html=True,
        )
    elif chat_text.strip():
        st.caption(t("livesell.no_cf_found"))


with cR:
    st.markdown(f"### 🤖 {t('livesell.ai_caption')}")
    st.caption(t("livesell.ai_caption_hint"))

    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.caption(t("livesell.api_warn"))
    else:
        if st.button(t("livesell.generate_now"), type="primary", width="stretch"):
            with st.spinner(t("generate.running")):
                try:
                    from tasks import tiktok_live
                    prompt = tiktok_live.build_prompt({
                        "sku":        prod["sku"],
                        "name":       prod["name"],
                        "brand":      prod.get("brand", ""),
                        "category":   "",
                        "cost_price": prod.get("cost_price", 0),
                        "sell_price": prod.get("sell_price", 0),
                        "specs":      "",
                    })
                    from anthropic import Anthropic
                    msg = Anthropic(api_key=api_key).messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1500,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    parsed = tiktok_live.parse(msg.content[0].text)
                    st.session_state["_live_ai_pack"] = parsed
                    toast(t("livesell.ai_done"), icon="🤖")
                except Exception as e:
                    friendly_error(e)

        pack = st.session_state.get("_live_ai_pack")
        if pack:
            st.markdown(f"**🎬 {t('livesell.hook')}**")
            st.markdown(
                f"<div style='background:#fbf9f3;border:0.5px solid rgba(40,30,20,0.07);"
                f"border-radius:10px;padding:12px 14px;font-size:13px;"
                f"line-height:1.6'>{pack.get('go_live_hook','')}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**🔥 {t('livesell.captions_10')}**")
            st.text_area(
                "captions",
                value=pack.get("captions", ""),
                height=180,
                label_visibility="collapsed",
            )
            st.markdown(f"**🎯 {t('livesell.closer')}**")
            st.markdown(
                f"<div style='background:#fbf9f3;border:0.5px solid rgba(40,30,20,0.07);"
                f"border-radius:10px;padding:12px 14px;font-size:13px;"
                f"line-height:1.6'>{pack.get('closer','')}</div>",
                unsafe_allow_html=True,
            )

st.divider()
st.caption(t("livesell.disclaimer"))
