"""Browse generated content by task — edit inline, regenerate, download."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import generate as gen
import tasks as task_registry
from exporters import ALL as EXPORTERS, SEA, GLOBAL
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import split_images, edit_content, empty_state, toast, friendly_error, page_header, stock_audit_card, bulk_ai_panel
import onboarding
from i18n import t
from i18n_inline import field_label, platform_name

db.init()
st.set_page_config(page_title="nirva · History", page_icon="📜", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📜", title=t("history.title"), subtitle=t("history.caption"))
onboarding.tip("history")

s = db.stats()
if s["content_total"] == 0:
    empty_state(
        icon="📜",
        title=t("history.empty_title"),
        body=t("history.empty_body"),
        cta_label=t("history.empty_cta"),
        cta_target="pages/3_🤖_Generate.py",
    )
    st.stop()

# Counts per task.
cols = st.columns(len(task_registry.ALL))
for col, (key, mod) in zip(cols, task_registry.ALL.items()):
    n = s["by_task"].get(key, 0)
    col.metric(t(f"task.{key}.label"), n)

st.divider()

options = [(k, t(f"task.{k}.label")) for k in task_registry.ALL if s["by_task"].get(k, 0) > 0]
if not options:
    st.info(t("history.empty"))
    st.stop()

idx = st.selectbox(
    t("history.select_task"),
    range(len(options)),
    format_func=lambda i: f"{options[i][1]} ({s['by_task'].get(options[i][0], 0)})",
)
task_key, _ = options[idx]
task = task_registry.get(task_key)

df = db.fetch_content(task_key)
if df.empty:
    st.info(t("history.empty"))
    st.stop()

label = t(f"task.{task_key}.label")
clean_label = label.replace(task.TASK["icon"], "").strip()
st.markdown(
    f"### {task.TASK['icon']} {clean_label} "
    f"<span style='color:#6b6b6b;font-weight:400'>· {len(df)}</span>",
    unsafe_allow_html=True,
)

# v52: Bulk AI operations panel — apply any helper (improve/shorten/emoji/
# tone-shift) to every row at once. Killer feature BigSeller doesn't have.
bulk_ai_panel(df=df, task_module=task, save_fn=db.save_content)

# Listing → pre-flight compliance check + marketplace CSV downloads.
if task_key == "listing":
    currency = st.session_state.get("currency", "USD")
    import compliance as comp

    # Pre-flight check across SEA platforms (most strict, instant feedback).
    rows_dicts = df.to_dict("records")
    with st.expander(f"🔍 {t('compliance.preflight_title')}", expanded=True):
        check_imgs = st.checkbox(
            t("compliance.check_images"),
            value=False,
            help=t("compliance.check_images_help"),
        )
        check_cols = st.columns(len(SEA))
        all_issues_by_platform = {}
        for col, (ch_key, _ch_mod) in zip(check_cols, SEA.items()):
            if check_imgs:
                issues = comp.check_batch_with_images(rows_dicts, ch_key, check_imgs=True)
            else:
                issues = comp.check_batch(rows_dicts, ch_key)
            summary = comp.summarize(issues)
            all_issues_by_platform[ch_key] = (issues, summary)
            with col:
                icon = "✅" if summary["passing"] else "❌"
                st.metric(
                    f"{icon} {platform_name(ch_key)}",
                    f"{summary['error']}🔴 {summary['warn']}🟡",
                )

        # Show details of failing platforms
        for ch_key, (issues, summary) in all_issues_by_platform.items():
            if not issues:
                continue
            sev_icons = {"error": "🔴", "warn": "🟡", "info": "🔵"}
            st.markdown(t("compliance.platform_summary",
                           platform=platform_name(ch_key),
                           errors=summary["error"],
                           warnings=summary["warn"]))
            issues_df = pd.DataFrame([{
                "": sev_icons.get(i.severity, "·"),
                "SKU": i.sku,
                t("compliance.field"): i.field,
                t("compliance.issue"): i.message,
                t("compliance.fix"): i.suggestion,
            } for i in issues[:50]])
            st.dataframe(issues_df, width='stretch', hide_index=True)

            if summary["error"] > 0:
                if st.button(
                    t("compliance.auto_fix_btn", n=summary["error"],
                      platform=platform_name(ch_key)),
                    key=f"autofix_{ch_key}",
                    width='content',
                ):
                    # Auto-truncate too-long titles
                    fixed = 0
                    for r in rows_dicts:
                        new_title = comp.truncate_title(r.get("title") or "", ch_key)
                        if new_title != (r.get("title") or ""):
                            with db.conn() as c:
                                payload_row = c.execute(
                                    "SELECT payload FROM content WHERE product_id = ? AND task = 'listing'",
                                    (r["id"],),
                                ).fetchone()
                                if payload_row:
                                    import json as _json
                                    payload = _json.loads(payload_row["payload"])
                                    payload["title"] = new_title
                                    db.save_content(r["id"], "listing", payload)
                                    fixed += 1
                    st.success(t("compliance.fixed_n", n=fixed))
                    st.rerun()

        # AI Review — Claude reads each listing for subjective issues.
        st.divider()
        cai1, cai2 = st.columns([1, 3])
        with cai1:
            api_key = st.session_state.get("api_key", "")
            run_ai_review = st.button(
                t("compliance.run_ai_review"),
                disabled=not api_key,
                width='stretch',
            )
        with cai2:
            st.caption(t("compliance.ai_review_help"))

        if run_ai_review:
            import generate as gen
            from tasks import ai_review as aireview
            progress = st.progress(0, text=t("generate.running"))
            def _on_p(d, total):
                progress.progress(d / total, text=f"{d}/{total}")
            results = gen.run_per_product(
                rows_dicts, aireview, api_key=api_key, workers=6, on_progress=_on_p,
            )
            progress.empty()
            for r in results:
                if "error" in r:
                    continue
                with st.expander(
                    f"🤖 {r['sku']} — score {r.get('score','?')}/100"
                    f" · 🔴 {r.get('n_blockers',0)}  🟡 {r.get('n_warnings',0)}",
                    expanded=int(r.get("n_blockers") or 0) > 0,
                ):
                    st.text(r.get("issues_text", ""))

    # ---- Pre-flight stock audit (v42 overselling protection) ----------
    # Surfaces over-/under-stocked SKUs BEFORE the seller pushes a CSV that
    # contains rows that will fail Shopee/Lazada/TikTok validation OR
    # (worse) get them dinged for overselling. Returns a filtered df.
    st.markdown(f"### 📊 {t('inventory.preflight_title')}")
    export_df = stock_audit_card(df)

    st.markdown(f"**{t('history.sea_downloads')}**")
    dl_cols = st.columns(len(SEA))
    for col, (ch_key, ch_mod) in zip(dl_cols, SEA.items()):
        fname, data = ch_mod.build(export_df)
        with col:
            st.download_button(
                t("history.download_btn", platform=platform_name(ch_key)),
                data=data, file_name=fname, mime="text/csv",
                width='stretch', key=f"dl_sea_{ch_key}",
            )

    st.markdown(f"**{t('history.global_downloads')} ({currency})**")
    dl_cols = st.columns(len(GLOBAL))
    for col, (ch_key, ch_mod) in zip(dl_cols, GLOBAL.items()):
        fname, data = ch_mod.build(export_df, currency=currency)
        with col:
            st.download_button(
                t("history.download_btn", platform=platform_name(ch_key)),
                data=data, file_name=fname, mime="text/csv",
                width='stretch', key=f"dl_global_{ch_key}",
            )
    st.divider()

    # ---- Multi-language export (ZIP of translated CSVs) ------------------
    st.markdown(f"### {t('history.multilang_title')}")
    st.caption(t("history.multilang_help"))

    import translate as trans
    api_key = st.session_state.get("api_key", "")
    lang_options = list(trans.LANG_NAMES.keys())

    ml_c1, ml_c2 = st.columns([3, 1])
    with ml_c1:
        target_langs = st.multiselect(
            t("history.multilang_pick"),
            lang_options,
            default=["en", "zh", "ja"],
            format_func=lambda c: trans.LANG_NAMES.get(c, c),
        )
    with ml_c2:
        platform_for_export = st.selectbox(
            t("history.multilang_platform"),
            list(SEA.keys()) + list(GLOBAL.keys()),
            format_func=platform_name,
        )

    if target_langs and api_key:
        cache = trans.cache_stats()
        st.caption(t("history.cache_stats", n=cache["total"]))

        build_btn = st.button(
            t("history.multilang_build_btn", n=len(target_langs)),
            type="primary",
            width='content',
        )
        if build_btn:
            import io as _io, zipfile, json as _json
            ch_mod = {**SEA, **GLOBAL}[platform_for_export]
            rows = df.to_dict("records")
            progress = st.progress(0, text=t("history.translating"))

            def _on_p(d, total):
                progress.progress(d / total, text=f"{d}/{total}")

            zip_buf = _io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                total_steps = len(target_langs)
                step = 0
                for lang in target_langs:
                    translated_rows = trans.translate_batch(
                        rows, lang, api_key=api_key, workers=6,
                    )
                    import pandas as _pd
                    translated_df = _pd.DataFrame(translated_rows)
                    fname, data = ch_mod.build(translated_df, currency=currency)
                    zip_name = fname.replace(".csv", f"_{lang}.csv")
                    zf.writestr(zip_name, data)
                    step += 1
                    progress.progress(step / total_steps, text=f"{lang} done")

            progress.empty()
            st.download_button(
                t("history.multilang_dl_zip", n=len(target_langs)),
                data=zip_buf.getvalue(),
                file_name=f"nirva_{platform_for_export}_multilang_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
            )
    elif target_langs and not api_key:
        st.info(t("generate.api_warn"))

    st.divider()

# Filter.
q = st.text_input(t("history.filter"), "")
if q:
    mask = df.apply(
        lambda r: q.lower() in " ".join(str(v) for v in r.values).lower(),
        axis=1,
    )
    df = df[mask]

# Per-row expander with edit + regenerate.
api_key = st.session_state.get("api_key", "")

for _, r in df.head(40).iterrows():
    sku = r["sku"]
    name = (r.get("name") or "")[:80]
    payload_full = {f: r.get(f, "") for f in task.TASK["output_fields"]}

    with st.expander(f"**{sku}** — {name}", expanded=False):
        c1, c2 = st.columns([1, 2])

        with c1:
            imgs = split_images(r.get("image_url"))
            if imgs:
                try:
                    src = imgs[0]
                    if src.startswith("http"):
                        st.image(src, width='stretch')
                    elif Path(src).exists():
                        st.image(src, width='stretch')
                except Exception:
                    pass
            else:
                st.caption(t("common.no_images"))

            st.metric(t("common.sell"), f"฿{int(r.get('sell_price') or 0):,}")
            st.caption(f"{t('upload.field.brand')}: {r.get('brand') or '—'}")
            st.caption(f"{t('upload.field.category')}: {r.get('category') or '—'}")
            st.caption(str(r.get("generated_at")))

        with c2:
            mode_key = f"mode_{r['id']}"
            mode = st.session_state.get(mode_key, "view")

            btn_cols = st.columns([1, 1, 3])
            with btn_cols[0]:
                if mode == "view":
                    if st.button(t("common.edit"), key=f"btn_edit_{r['id']}", width='stretch'):
                        st.session_state[mode_key] = "edit"
                        st.rerun()
                else:
                    if st.button("✕", key=f"btn_cancel_{r['id']}", width='stretch'):
                        st.session_state[mode_key] = "view"
                        st.rerun()
            with btn_cols[1]:
                if st.button(
                    t("common.regenerate"),
                    key=f"btn_regen_{r['id']}",
                    width='stretch',
                    disabled=not api_key,
                ):
                    with st.spinner(t("generate.running")):
                        try:
                            product_row = r.to_dict()
                            results = gen.run_per_product(
                                [product_row], task, api_key=api_key, workers=1,
                            )
                            if results and "error" not in results[0]:
                                new_payload = {
                                    f: results[0].get(f, "") for f in task.TASK["output_fields"]
                                }
                                db.save_content(int(r["id"]), task_key, new_payload)
                                st.success(t("generate.done"))
                                st.rerun()
                            else:
                                st.error(results[0].get("error", "fail"))
                        except Exception as e:
                            st.error(str(e))

            if mode == "edit":
                edit_content(int(r["id"]), task_key, payload_full, task)
            else:
                for f in task.TASK["output_fields"]:
                    val = r.get(f, "")
                    if not val:
                        continue
                    st.markdown("**" + field_label(f) + "**")
                    if f == "body_html":
                        st.code(val, language="html")
                    elif len(str(val)) > 80:
                        st.text(str(val))
                    else:
                        st.write(val)

st.divider()

csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
exported = st.download_button(
    t("history.export_all", label=clean_label, n=len(df)),
    data=csv_bytes,
    file_name=f"nirva_{task_key}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)
if exported:
    try:
        import onboarding as _ob
        _ob.mark_step("first_export")
    except Exception:
        pass
