"""nirva — Workspace (main entry).

Single-page flow:
  Drop / paste anything → review → one click → all content ready

Run:  streamlit run app.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

import db
import intake
import generate as gen
import parser as parser_mod
import tasks as task_registry
import fees as fees_mod
import voice
import onboarding
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _components import split_images, friendly_error, toast, page_header
from _auth_gate import require_auth
from exporters import ALL as EXPORTERS
from i18n import t, current_lang
from i18n_inline import marketplace_fee_label

load_dotenv()

st.set_page_config(page_title="nirva — Workspace", page_icon="✨", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

api_key = st.session_state.get("api_key", "")
markup = st.session_state.get("markup", 15)
round_to = st.session_state.get("round_to", 10)


# ---- Header ---------------------------------------------------------------

page_header(icon="✨", title=t("ws.title"), subtitle=t("ws.subtitle"))
onboarding.first_run_banner()
onboarding.tip("workspace")


# ---- Quick actions row (shortcuts to common flows) -----------------------
# Shows the user "what else can I do?" at a glance — no jargon, big cards.
qa1, qa2, qa3, qa4 = st.columns(4)
_QA_CSS = (
    "display:block;text-decoration:none;color:inherit;"
    "padding:14px 16px;border-radius:12px;background:white;"
    "border:1px solid rgba(40,30,20,0.06);"
    "box-shadow:0 1px 2px rgba(31,31,31,0.03);"
    "transition:transform .15s ease, box-shadow .15s ease;height:100%"
)
_QA_HOVER = "this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 14px rgba(31,31,31,0.06)';"
_QA_LEAVE = "this.style.transform='';this.style.boxShadow='0 1px 2px rgba(31,31,31,0.03)';"

def _qa_card(col, *, href: str, icon: str, label: str, body: str):
    with col:
        col.page_link(href, label=f"{icon}  {label}", help=body)

_qa_card(qa1, href="pages/8_📸_Vision.py",
         icon="📸", label=t("qa.vision"), body=t("qa.vision_body"))
_qa_card(qa2, href="pages/3_🤖_Generate.py",
         icon="🤖", label=t("qa.generate"), body=t("qa.generate_body"))
_qa_card(qa3, href="pages/2_📦_Catalog.py",
         icon="📦", label=t("qa.catalog"), body=t("qa.catalog_body"))
_qa_card(qa4, href="pages/4_📜_History.py",
         icon="📜", label=t("qa.history"), body=t("qa.history_body"))

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)


# ---- Intake (file uploader + paste-text) ----------------------------------

ic1, ic2 = st.columns([3, 2])
with ic1:
    file = st.file_uploader(
        t("ws.drop_label"),
        type=["xlsx", "xls", "csv", "tsv", "pdf"],
        label_visibility="collapsed",
    )
with ic2:
    paste = st.text_area(
        t("ws.paste_label"),
        placeholder=t("ws.paste_placeholder"),
        height=130,
        label_visibility="collapsed",
    )
    # Voice input — recognized text lands in clipboard, user pastes above.
    LANG_TO_BCP47 = {
        "th": "th-TH", "en": "en-US", "zh": "zh-CN", "ja": "ja-JP",
        "ko": "ko-KR", "vi": "vi-VN", "id": "id-ID",
    }
    voice.render(
        label=t("ws.voice_btn"),
        stop_label=t("ws.voice_stop"),
        placeholder=t("ws.voice_placeholder"),
        unsupported=t("ws.voice_unsupported"),
        copied=t("ws.voice_copied"),
        lang=LANG_TO_BCP47.get(current_lang(), "th-TH"),
        height=120,
    )

# Helper buttons row.
hc1, hc2, hc3 = st.columns([1, 1, 4])
with hc1:
    demo_clicked = st.button(t("ws.try_demo"), width='stretch')
with hc2:
    if st.session_state.get("ws_df") is not None:
        if st.button(t("ws.start_over"), width='stretch'):
            for k in ("ws_df", "ws_source", "ws_results", "ws_signature"):
                st.session_state.pop(k, None)
            st.rerun()

if demo_clicked:
    from pathlib import Path
    demo_path = Path(__file__).parent / "samples" / "dealer_pricelist_demo.xlsx"
    if demo_path.exists():
        with demo_path.open("rb") as fh:
            raw_demo = fh.read()
        try:
            raw_df = parser_mod.read_any(demo_path.name, raw_demo)
            mapping = parser_mod.auto_map(list(raw_df.columns))
            normalized = parser_mod.normalize(raw_df, mapping)
            normalized["sell_price"] = normalized["cost_price"].apply(
                lambda c: parser_mod.markup_price(c, markup, round_to)
            )
            st.session_state["ws_df"] = normalized
            st.session_state["ws_source"] = t("ws.demo_source")
            st.session_state["ws_signature"] = ("__demo__", 0)
            st.rerun()
        except Exception as e:
            friendly_error(e)


# ---- Step 1: Read whatever was dropped/pasted -----------------------------

if file or paste:
    new_signature = (file.name if file else "", len(paste) if paste else 0)
    if st.session_state.get("ws_signature") != new_signature:
        st.session_state["ws_signature"] = new_signature
        with st.spinner(t("ws.reading")):
            try:
                if file:
                    raw_df, source_desc = intake.read_anything(
                        file.name, file.getvalue(), paste_text=paste, api_key=api_key,
                    )
                else:
                    raw_df, source_desc = intake.read_anything(
                        "", None, paste_text=paste, api_key=api_key,
                    )
            except ValueError as e:
                st.error(str(e))
                st.stop()
            except Exception as e:
                friendly_error(e)
                st.stop()

            # Normalize: Excel/CSV need column-mapping, PDF/paste are already normalized.
            if file and file.name.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv", ".tsv")):
                mapping = parser_mod.auto_map(list(raw_df.columns))
                normalized = parser_mod.normalize(raw_df, mapping)
            else:
                normalized = raw_df

            if normalized.empty:
                st.warning(t("ws.no_rows"))
                st.stop()

            normalized["sell_price"] = normalized["cost_price"].apply(
                lambda c: parser_mod.markup_price(c, markup, round_to)
            )
            st.session_state["ws_df"] = normalized
            st.session_state["ws_source"] = source_desc


# ---- Step 2: Show parsed table + Run button -------------------------------

df = st.session_state.get("ws_df")
if df is not None and not df.empty:
    src = st.session_state.get("ws_source", "")
    st.success(t("ws.parsed", n=len(df), source=src))

    show_cols = [c for c in ["sku", "name", "brand", "cost_price", "sell_price"] if c in df.columns]
    st.dataframe(
        df[show_cols].head(8),
        width='stretch',
        hide_index=True,
        column_config={
            "sku": st.column_config.TextColumn("SKU", width="small"),
            "name": st.column_config.TextColumn(t("upload.field.name").rstrip(" *"), width="large"),
            "brand": st.column_config.TextColumn(t("upload.field.brand"), width="small"),
            "cost_price": st.column_config.NumberColumn(t("common.cost"), format="฿%d", width="small"),
            "sell_price": st.column_config.NumberColumn(t("common.sell"), format="฿%d", width="small"),
        },
    )
    if len(df) > 8:
        st.caption(f"+ {len(df) - 8} more")

    # Estimated net profit per platform across the batch.
    fees = fees_mod.load()
    profits = {
        p: sum(
            fees_mod.net_profit(float(c), int(s), p, fees)["net"]
            for c, s in zip(df["cost_price"], df["sell_price"])
        )
        for p in fees
    }

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("upload.stat_ready"), len(df))
    m2.metric(t("upload.stat_cost"), f"฿{df['cost_price'].sum():,.0f}")
    m3.metric(t("upload.stat_sell"), f"฿{df['sell_price'].sum():,.0f}")
    best_platform = max(profits, key=profits.get)
    m4.metric(
        t("ws.best_profit", platform=marketplace_fee_label(best_platform)),
        f"฿{int(profits[best_platform]):,}",
    )

    with st.expander(t("ws.profit_breakdown"), expanded=False):
        rows = []
        for p, total in profits.items():
            label = marketplace_fee_label(p)
            base_pct = (
                fees[p]["commission_pct"] + fees[p]["payment_pct"] + fees[p]["transaction_pct"]
            )
            rows.append({
                "platform": label,
                t("ws.fee_pct"): f"{base_pct:.1f}% + VAT",
                t("ws.net_profit_col"): int(total),
            })
        import pandas as pd
        profit_df = pd.DataFrame(rows)
        st.dataframe(
            profit_df,
            width='stretch',
            hide_index=True,
            column_config={
                t("ws.net_profit_col"): st.column_config.NumberColumn(format="฿%d"),
            },
        )
        st.caption(t("ws.fee_note"))


# ---- Step 3: Generate -----------------------------------------------------

    st.markdown("<hr>", unsafe_allow_html=True)

    # Target-language selector for AI output (default = nirva UI language).
    from i18n import LANGS as UI_LANGS
    target_lang_options = list(UI_LANGS.keys()) + ["ms", "fr", "es", "de", "pt", "ar"]
    target_lang_labels = {
        **UI_LANGS,
        "ms": "Bahasa Melayu", "fr": "Français", "es": "Español",
        "de": "Deutsch", "pt": "Português", "ar": "العربية",
    }
    cc1, cc2, cc3 = st.columns([2, 1, 1])
    with cc1:
        target_lang = st.selectbox(
            t("ws.target_lang"),
            target_lang_options,
            index=target_lang_options.index(current_lang()),
            format_func=lambda c: target_lang_labels.get(c, c),
            help=t("ws.target_lang_help"),
        )
        st.session_state["target_lang"] = target_lang

    with cc2:
        # Auto-detect upcoming sale; default ON if event within 30 days.
        import live_data
        nxt_big = live_data.next_big_sale()
        within_30 = bool(nxt_big and nxt_big.get("days_until", 999) <= 30)
        auto_camp = st.checkbox(
            t("ws.auto_campaign"),
            value=within_30,
            help=t("ws.auto_campaign_help"),
        )
        st.session_state["auto_campaign"] = auto_camp
        if auto_camp and nxt_big:
            from i18n_inline import live_promo_label
            label = live_promo_label(nxt_big.get("slug", ""))
            st.caption(f"⏰ {label} — {t('live.in_n_days', n=nxt_big['days_until'])}")

    with cc3:
        use_trends = st.checkbox(
            t("ws.use_trends"),
            value=False,
            help=t("ws.use_trends_help"),
            disabled=not api_key,
        )
        st.session_state["use_trends"] = use_trends

    bc1, bc2, bc3 = st.columns([3, 1, 1])
    with bc1:
        if not api_key:
            st.info(t("generate.api_warn"))
        else:
            st.caption(t("ws.run_help", n=len(df)))
    with bc2:
        preview_btn = st.button(
            t("ws.preview_btn"),
            width='stretch',
            disabled=not api_key,
            help=t("ws.preview_help"),
        )
    with bc3:
        run_btn = st.button(
            t("ws.run_btn"),
            type="primary",
            width='stretch',
            disabled=not api_key,
        )

    # Streaming preview — generate FIRST product live so user can verify quality.
    if preview_btn:
        first = df.iloc[0].to_dict()
        st.markdown(f"**📡 {first.get('name') or first.get('sku')}**")
        live = st.empty()

        def on_chunk(_delta, accumulated):
            live.code(accumulated[-1500:], language="json")

        with st.spinner(t("generate.running")):
            from tasks import all_in_one as aio
            from generate import _with_target_lang, _with_context, _client, _stream
            client = _client(api_key)
            try:
                campaign_ctx = None
                if st.session_state.get("auto_campaign"):
                    import live_data
                    campaign_ctx = live_data.next_big_sale()
                trending_ctx: list[str] = []
                if st.session_state.get("use_trends") and first.get("category"):
                    import live_data
                    trending_ctx = live_data.cached_trending_kws(
                        [first["category"]],
                        target_market="TH" if current_lang() == "th" else "US",
                        api_key=api_key,
                    )

                base = aio.build_prompt(first)
                base = _with_context(base, campaign=campaign_ctx, trending_kws=trending_ctx)
                prompt = _with_target_lang(base, st.session_state.get("target_lang"))
                full = _stream(client, prompt, on_chunk, max_tokens=4000)
                result = {"all_payloads": aio.parse_all(full)}
            except Exception as e:
                result = {"error": f"{type(e).__name__}: {e}"}

        if "error" in result:
            st.error(result["error"])
        else:
            live.empty()
            payloads = result.get("all_payloads", {})
            st.success(t("ws.preview_done", n=len(payloads)))
            for task_key, payload in payloads.items():
                mod = task_registry.get(task_key)
                with st.expander(f"{mod.TASK['icon']} {t(f'task.{task_key}.label')}", expanded=False):
                    for f, v in payload.items():
                        if v:
                            st.markdown(f"**{f.replace('_',' ').title()}**")
                            if len(str(v)) > 80:
                                st.text(str(v)[:600])
                            else:
                                st.write(v)

    if run_btn:
        # Save products first.
        batch_id = db.create_batch(st.session_state.get("ws_source") or "workspace", len(df))
        db.upsert_products(df, batch_id)

        # One Claude call per product → all 5 single-product content types.
        rows = df.to_dict("records")
        # Re-fetch with DB ids
        with db.conn() as c:
            id_map = {
                r["sku"]: r["id"]
                for r in c.execute(
                    "SELECT id, sku FROM products WHERE sku IN ("
                    + ",".join("?" * len(rows)) + ")",
                    [r["sku"] for r in rows],
                ).fetchall()
            }
        for r in rows:
            r["id"] = id_map.get(r["sku"])

        progress = st.progress(0, text=t("generate.running"))
        def on_progress(d: int, total: int):
            progress.progress(d / total, text=f"{d}/{total}")

        # Pre-fetch context once (used for every row in the batch).
        campaign_ctx = None
        if st.session_state.get("auto_campaign"):
            import live_data
            campaign_ctx = live_data.next_big_sale()
        trending_ctx: list[str] = []
        if st.session_state.get("use_trends"):
            import live_data
            cats = list({r.get("category") for r in rows if r.get("category")})
            with st.spinner(t("ws.fetching_trends")):
                trending_ctx = live_data.cached_trending_kws(
                    cats[:4] or ["general"],
                    target_market="TH" if current_lang() == "th" else "US",
                    api_key=api_key,
                )

        try:
            results = gen.run_all_in_one(
                rows, api_key=api_key, workers=8, on_progress=on_progress,
                target_lang=st.session_state.get("target_lang"),
                campaign=campaign_ctx,
                trending_kws=trending_ctx,
            )

            ok = 0
            for r in results:
                if "error" in r:
                    continue
                payloads = r.get("all_payloads", {})
                for task_key, payload in payloads.items():
                    db.save_content(r["id"], task_key, payload)
                ok += 1

            st.session_state["ws_results"] = results
            st.success(t("ws.run_done", ok=ok, total=len(results)))
            st.balloons()

            # Fire notification — best-effort, never blocks UI on failure.
            try:
                import user_settings as us
                import notifier
                prefs = us.notify_prefs()
                if prefs.get("batch_done"):
                    notifier.notify(
                        t("notif.event_batch_done_subject", ok=ok, total=len(results)),
                        t("notif.event_batch_done_body",
                          ok=ok, total=len(results),
                          source=st.session_state.get("ws_source", "—")),
                    )
            except Exception:
                pass
        except Exception as e:
            friendly_error(e)


# ---- Step 4: Results stream ----------------------------------------------

results = st.session_state.get("ws_results")
if results:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader(t("ws.results_title"))

    # Marketplace CSV downloads (most users want this immediately)
    listing_df = db.fetch_content("listing")
    if not listing_df.empty:
        st.markdown(f"**{t('history.downloads_title')}**")
        dl_cols = st.columns(len(EXPORTERS))
        for col, (ch_key, ch_mod) in zip(dl_cols, EXPORTERS.items()):
            fname, data = ch_mod.build(listing_df)
            with col:
                st.download_button(
                    f"⬇ {ch_key.title()} CSV",
                    data=data,
                    file_name=fname,
                    mime="text/csv",
                    width='stretch',
                    key=f"dl_{ch_key}",
                )
        st.divider()

    # Per-product preview
    for r in results[:20]:
        if "error" in r:
            with st.expander(f"⚠ {r.get('sku', '?')} — error"):
                st.error(r["error"])
            continue

        sku = r.get("sku", "?")
        name = (r.get("name") or "")[:80]
        payloads: dict[str, dict] = r.get("all_payloads", {}) or {}
        done_count = len(payloads)

        chips = " ".join(
            f"{task_registry.get(k).TASK['icon']}" for k in payloads
        )
        with st.expander(f"**{sku}** — {name}    {chips}", expanded=False):
            c1, c2 = st.columns([1, 3])
            with c1:
                imgs = split_images(r.get("image_url"))
                if imgs:
                    src = imgs[0]
                    if src.startswith("http") or Path(src).exists():
                        st.image(src, width='stretch')
                st.metric(t("common.sell"), f"฿{int(r.get('sell_price') or 0):,}")
                st.caption(f"{t('common.cost')} ฿{int(r.get('cost_price') or 0):,}")
                st.caption(f"{done_count} {t('ws.contents_made')}")

            with c2:
                # Show each task in its own sub-expander.
                for task_key, payload in payloads.items():
                    mod = task_registry.get(task_key)
                    icon = mod.TASK["icon"]
                    label = t(f"task.{task_key}.label").replace(icon, "").strip()
                    st.markdown(f"**{icon} {label}**")
                    # Show each output field
                    for field, val in payload.items():
                        if not val:
                            continue
                        if field == "body_html":
                            st.code(val, language="html")
                        elif len(str(val)) > 100:
                            st.text(str(val)[:600])
                        else:
                            st.write(val)
                    st.markdown("---")

    if len(results) > 20:
        st.caption(t("ws.more_in_history", n=len(results) - 20))


# ---- Empty state ----------------------------------------------------------

elif df is None or df.empty:
    s = db.stats()
    if s["products"] > 0:
        st.info(t("ws.has_products", n=s["products"]))
    else:
        st.markdown(t("ws.empty_help"))
