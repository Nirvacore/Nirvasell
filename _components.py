"""Reusable UI components — image grids, product detail panel, content editor,
and v31 polish helpers (toast / empty-state / friendly errors)."""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
import streamlit as st

import db
import tasks as task_registry
from i18n import t


# ---- v31 polish helpers -------------------------------------------------

def toast(message: str, *, icon: str = "✓") -> None:
    """Auto-dismissing notification (Streamlit 1.27+). Falls back to st.success
    if the runtime is older."""
    try:
        st.toast(message, icon=icon)
    except Exception:
        st.success(f"{icon} {message}")


def friendly_error(exc: Exception, hint: str = "") -> None:
    """Replace raw `KeyError: 'foo'` style messages with a Thai-friendly format.
    Includes a collapsed expander with the raw traceback for debugging.
    Also writes the full traceback to data/errors.log for operator triage."""
    name = type(exc).__name__
    msg = str(exc) or "—"
    # Operator-side: structured log line for tail/grep
    try:
        import error_log, auth
        u = auth.current_user()
        error_log.log(exc, where="ui.friendly_error",
                      user_id=(u or {}).get("id"),
                      extra={"hint": hint})
    except Exception:
        pass

    # v50: also surface in the unified events feed so the user notices
    try:
        import events
        events.log(
            category="ai" if name in ("RateLimitError","AuthenticationError",
                                      "TimeoutError") else "system",
            severity="error",
            title=f"🔴 {name}",
            body=msg[:200],
            meta={"hint": hint},
        )
    except Exception:
        pass
    friendly = {
        "FileNotFoundError":   "หาไฟล์ไม่เจอ — ตรวจ path หรือลอง upload อีกครั้ง",
        "PermissionError":     "ไม่มีสิทธิ์เข้าถึงไฟล์ / โฟลเดอร์นี้",
        "JSONDecodeError":     "ข้อมูล JSON เสีย — AI อาจตอบกลับไม่สมบูรณ์ ลองรันใหม่",
        "TimeoutError":        "หมดเวลาในการเชื่อมต่อ — เน็ตช้าหรือ server ตอบช้า",
        "ConnectionError":     "เชื่อมต่ออินเทอร์เน็ตไม่ได้ — เช็ค WiFi",
        "AuthenticationError": "API key ไม่ถูกต้อง — ตรวจค่าในแถบด้านข้าง",
        "RateLimitError":      "เรียก AI บ่อยเกินไป — รอ 30 วิแล้วลองใหม่",
        "KeyError":            f"ไม่พบ field ที่ต้องการ ({msg}) — ไฟล์อาจมี column ขาด",
        "ValueError":          f"ค่าที่ใส่ไม่ถูกต้อง: {msg}",
        "ModuleNotFoundError": f"ขาด python module ({msg}) — รัน `pip install -r requirements.txt`",
    }
    line = friendly.get(name, f"{name}: {msg}")
    if hint:
        line = f"{line}\n\n💡 {hint}"
    st.error(line)
    with st.expander("รายละเอียดเชิงเทคนิค", expanded=False):
        st.code(f"{name}: {msg}", language="text")


def stock_audit_card(df, *, low_threshold: int = 5) -> "pd.DataFrame":
    """Pre-flight stock check + optional 'exclude OOS' toggle. Renders a card
    that surfaces over-/under-stocked SKUs BEFORE the user downloads CSVs.
    Returns the dataframe to use for export (filtered if user chose to)."""
    import inventory
    rep = inventory.audit(df, low_threshold=low_threshold)
    if rep["total"] == 0:
        return df

    # Three-up summary chips
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("inventory.ok"), rep["ok"])
    c2.metric(t("inventory.low"), rep["low"])
    c3.metric(t("inventory.out"), rep["out"])
    c4.metric(t("inventory.assumed"), rep["assumed"])

    # Banner if there are OOS items
    if rep["out"] > 0:
        st.warning(
            f"⚠ {t('inventory.oos_warn', n=rep['out'])}: "
            f"`{'`, `'.join(rep['out_skus'][:5])}`"
            + ("…" if len(rep["out_skus"]) > 5 else "")
        )
        exclude_oos = st.checkbox(
            t("inventory.exclude_oos"),
            value=True,
            help=t("inventory.exclude_oos_help"),
            key="_stock_exclude_oos",
        )
        if exclude_oos:
            df = inventory.filter_in_stock(df)
            st.caption(t("inventory.after_filter", n=len(df)))

    if rep["assumed"] > 0:
        with st.expander(t("inventory.assumed_expand", n=rep["assumed"])):
            st.caption(t("inventory.assumed_hint"))

    return df


def bulk_ai_panel(*, df, task_module, save_fn, default_field: str | None = None) -> None:
    """Bulk-apply an AI helper to every row in `df`. Used on History page.

    Args:
        df: pandas DataFrame of content rows (must have `id` column = product_id)
        task_module: the task plugin (so we know what fields exist)
        save_fn: callable(product_id, task_key, payload_dict) → saves to DB
        default_field: which output field to default the picker to

    Pattern:
        1. user picks operation + field
        2. preview first 2 transformations
        3. user clicks "Apply to all 50" → progress bar → done
    """
    import _ai_helpers
    api_key = st.session_state.get("api_key", "")
    if not api_key or df is None or df.empty:
        return

    task_key = task_module.TASK["key"]
    fields = task_module.TASK.get("output_fields") or []
    if not fields:
        return

    with st.expander(f"⚡ {t('bulk.title', n=len(df))}", expanded=False):
        st.caption(t("bulk.help"))

        cA, cB, cC = st.columns([2, 2, 1])
        with cA:
            field = st.selectbox(
                t("bulk.field"),
                options=fields,
                index=fields.index(default_field) if default_field in fields else 0,
                key=f"_bulk_field_{task_key}",
            )
        with cB:
            op = st.selectbox(
                t("bulk.operation"),
                options=list(_ai_helpers.HELPERS.keys()),
                format_func=lambda k: (_ai_helpers.HELPERS[k]["icon"] + " "
                                       + t(_ai_helpers.HELPERS[k]["label_key"])),
                key=f"_bulk_op_{task_key}",
            )
        with cC:
            shorten_chars = 60
            if op == "shorten":
                shorten_chars = st.number_input(
                    t("bulk.max_chars"), 20, 200, 60, 5,
                    key=f"_bulk_max_{task_key}",
                )

        # Preview — show first 2 before/after pairs as a sanity check
        preview_rows = df.head(2).to_dict("records")
        if st.button(t("bulk.preview"), key=f"_bulk_preview_{task_key}",
                     type="tertiary"):
            with st.spinner(t("bulk.previewing")):
                for r in preview_rows:
                    orig = (r.get(field) or "").strip()
                    if not orig:
                        continue
                    extra = {"max_chars": int(shorten_chars)} if op == "shorten" else {}
                    ok, new = _ai_helpers.apply(op, orig, api_key, **extra)
                    st.markdown(
                        f"<div style='border:1px solid rgba(0,0,0,0.08);"
                        f"border-radius:8px;padding:10px 12px;margin-bottom:8px'>"
                        f"<div style='color:#7a7569;font-size:11px'>SKU {r.get('sku','?')}</div>"
                        f"<div style='color:#999;font-size:13px;text-decoration:line-through'>"
                        f"{orig[:120]}</div>"
                        f"<div style='color:#1f1f1f;font-size:13px;margin-top:4px'>"
                        f"→ {new[:120] if ok else f'Error: {new}'}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        cR1, cR2 = st.columns([3, 1])
        with cR1:
            confirm = st.checkbox(
                t("bulk.confirm_check", n=len(df), field=field),
                key=f"_bulk_confirm_{task_key}",
            )
        with cR2:
            run = st.button(
                t("bulk.run", n=len(df)),
                key=f"_bulk_run_{task_key}",
                type="primary", width="stretch", disabled=not confirm,
            )

        if run and confirm:
            prog = st.progress(0, text=t("bulk.running"))
            ok_n, err_n = 0, 0
            rows = df.to_dict("records")
            total = len(rows)
            for i, r in enumerate(rows, 1):
                orig = (r.get(field) or "").strip()
                if not orig:
                    continue
                extra = {"max_chars": int(shorten_chars)} if op == "shorten" else {}
                got_ok, new_val = _ai_helpers.apply(op, orig, api_key, **extra)
                if got_ok:
                    payload = {f: r.get(f, "") for f in fields}
                    payload[field] = new_val
                    try:
                        save_fn(r["id"], task_key, payload)
                        ok_n += 1
                    except Exception:
                        err_n += 1
                else:
                    err_n += 1
                prog.progress(i / total, text=f"{i}/{total}")
            prog.empty()
            try:
                import events as _events
                _events.log(
                    category="ai", severity="success",
                    title=f"⚡ Bulk AI: {ok_n}/{total} updated",
                    body=f"Op={op} · Field={field}",
                )
            except Exception:
                pass
            st.success(t("bulk.done", ok=ok_n, total=total, err=err_n))
            st.rerun()


def ai_chip_row(*, state_key: str, helpers: list[str] | None = None,
                shorten_max: int = 60) -> None:
    """Notion-style "/" AI quick-action chip row. Renders 5 small buttons
    above a text input. Click a chip → AI transforms the text in-place via
    Claude. The text being transformed lives in `st.session_state[state_key]`.

    Caller pattern:
        st.text_area("...", key="my_text")
        ai_chip_row(state_key="my_text")

    Requires an API key in session_state["api_key"]; degrades gracefully
    (hides chips) when no key is set."""
    import _ai_helpers
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return  # silent — no API key, no chips

    if helpers is None:
        helpers = list(_ai_helpers.HELPERS.keys())

    cols = st.columns(len(helpers))
    for col, key in zip(cols, helpers):
        meta = _ai_helpers.HELPERS.get(key)
        if not meta:
            continue
        try:
            label = t(meta["label_key"])
        except Exception:
            label = key.title()
        with col:
            if st.button(
                f"{meta['icon']} {label}",
                key=f"_ai_chip_{state_key}_{key}",
                type="tertiary",
                width="stretch",
            ):
                current = st.session_state.get(state_key, "") or ""
                if not current.strip():
                    st.toast(t("ai_help.empty"), icon="✏")
                    return
                with st.spinner(f"{meta['icon']} AI..."):
                    extra = {"max_chars": shorten_max} if key == "shorten" else {}
                    ok, result = _ai_helpers.apply(key, current, api_key, **extra)
                if ok:
                    st.session_state[state_key] = result
                    st.toast(t("ai_help.done"), icon=meta["icon"])
                    st.rerun()
                else:
                    st.error(result)


def metric_with_hint(label: str, value, *, hint: str = "",
                     hint_target: str | None = None,
                     hint_tone: str = "info",
                     delta=None) -> None:
    """Etsy-style metric — value above, contextual action hint below.

    `hint_tone`:
      • "info"    → neutral gray (informational)
      • "warn"    → amber (something needs attention soon)
      • "ok"      → sage green (positive — keep doing this)
      • "danger"  → red (action required now)

    `hint_target` (optional) — if set, makes the hint a clickable page-link
    via Streamlit's native page_link so user can jump to fix immediately."""
    st.metric(label=label, value=value, delta=delta)
    if not hint:
        return
    colors = {
        "info":   "#7a7569",
        "warn":   "#c5963d",
        "ok":     "#4d6c5c",
        "danger": "#c54c4c",
    }
    color = colors.get(hint_tone, colors["info"])
    icon_map = {"info": "💡", "warn": "⚠", "ok": "✓", "danger": "🔴"}
    icon = icon_map.get(hint_tone, "💡")
    if hint_target:
        # Render as a page_link so the chip is clickable
        st.page_link(hint_target, label=f"{icon} {hint}")
    else:
        st.markdown(
            f"<div style='color:{color};font-size:11px;line-height:1.5;"
            f"margin-top:-8px'>{icon} {hint}</div>",
            unsafe_allow_html=True,
        )


def page_header(*, icon: str, title: str, subtitle: str = "") -> None:
    """Polished Zen page header — Cormorant Garamond serif + wabi-sabi
    brush divider below. Matches the landing/auth aesthetic so the app
    feels like one cohesive product, not a Streamlit demo.

    v57: dramatic serif size + airy line-height + brush mark."""
    sub_html = (
        f"<div style='color:#7a7569;font-size:14px;margin-top:6px;"
        f"line-height:1.6'>{subtitle}</div>"
        if subtitle else ""
    )
    st.markdown(
        "<div class='nirva-mark' style='margin:6px 0 12px'>"
        "<div style='display:flex;align-items:flex-start;gap:16px'>"
        f"<div style='font-size:34px;line-height:1;margin-top:8px;"
        f"opacity:0.92'>{icon}</div>"
        "<div style='flex:1;min-width:0'>"
        "<div style='font-family:\"Cormorant Garamond\",\"EB Garamond\",Georgia,serif;"
        "font-size:2.4rem;font-weight:500;letter-spacing:-0.018em;line-height:1.15;"
        f"color:#1c1c1c'>{title}</div>"
        f"{sub_html}"
        "</div></div></div>",
        unsafe_allow_html=True,
    )


def empty_state(*, icon: str, title: str, body: str,
                cta_label: str | None = None,
                cta_target: str | None = None) -> None:
    """Friendly placeholder for pages/tabs that have no data yet. Renders a
    centered card with optional page-link CTA."""
    cta_html = ""
    if cta_label and cta_target:
        st.markdown(
            f"<div style='max-width:520px;margin:6vh auto;padding:32px;"
            f"background:#fbf9f3;border:1px solid rgba(40,30,20,0.10);"
            f"border-radius:14px;text-align:center'>"
            f"<div style='font-size:48px;line-height:1'>{icon}</div>"
            f"<div style='font-family:Cormorant Garamond,serif;font-size:1.4rem;"
            f"font-weight:500;margin-top:12px'>{title}</div>"
            f"<div style='color:#6b6b6b;font-size:14px;margin:8px 0 18px;"
            f"line-height:1.6'>{body}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        # Native page-link below the card so click works
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            st.page_link(cta_target, label=f"▶ {cta_label}",
                         icon="🚀")
    else:
        st.markdown(
            f"<div style='max-width:520px;margin:6vh auto;padding:32px;"
            f"background:#fbf9f3;border:1px solid rgba(40,30,20,0.10);"
            f"border-radius:14px;text-align:center'>"
            f"<div style='font-size:48px;line-height:1'>{icon}</div>"
            f"<div style='font-family:Cormorant Garamond,serif;font-size:1.4rem;"
            f"font-weight:500;margin-top:12px'>{title}</div>"
            f"<div style='color:#6b6b6b;font-size:14px;margin:8px 0 0;"
            f"line-height:1.6'>{body}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def split_images(image_url: str | None) -> list[str]:
    """Pipe-separated URLs/paths → clean list."""
    if not image_url:
        return []
    return [u.strip() for u in str(image_url).split("|") if u.strip()]


def image_grid(urls: list[str], cols: int = 4, height: int = 110):
    """Render a row of images. URLs can be https://... or local file paths."""
    if not urls:
        st.caption("— no images —")
        return
    columns = st.columns(cols)
    for i, src in enumerate(urls[: cols * 3]):
        with columns[i % cols]:
            try:
                if src.startswith("http"):
                    st.image(src, width='stretch')
                else:
                    p = Path(src)
                    if p.exists():
                        st.image(str(p), width='stretch')
                    else:
                        st.caption(f"missing: {p.name}")
            except Exception as e:
                st.caption(f"err: {e}")


def render_content_for_task(content_row: dict, task_module) -> None:
    """Render one piece of generated content, read-only."""
    for field in task_module.TASK["output_fields"]:
        val = content_row.get(field, "")
        if not val:
            continue
        label = field.replace("_", " ").title()
        st.markdown(f"**{label}**")
        if field == "body_html":
            st.code(val, language="html")
        elif len(str(val)) > 80:
            st.text(str(val))
        else:
            st.write(val)


def edit_content(product_id: int, task_key: str, current: dict, task_module) -> bool:
    """Editable form for a piece of content. Returns True if saved."""
    fields = task_module.TASK["output_fields"]
    long_fields = {"body_html", "description", "post", "script", "message",
                   "body_text", "pitch", "reply", "closer", "captions",
                   "go_live_hook"}
    new_values: dict[str, str] = {}
    cols = st.columns([1, 1])
    for i, field in enumerate(fields):
        with cols[i % 2]:
            val = current.get(field, "")
            label = field.replace("_", " ").title()
            field_key = f"edit_{product_id}_{task_key}_{field}"
            # Seed session_state if not yet set so chip mutations carry over
            if field_key not in st.session_state:
                st.session_state[field_key] = str(val)
            if field in long_fields:
                new_values[field] = st.text_area(
                    label, key=field_key, height=140,
                )
                # v51: Notion-style "/" chips above long fields
                ai_chip_row(state_key=field_key,
                            helpers=["improve", "shorten", "emojis",
                                     "casual", "professional"])
            else:
                new_values[field] = st.text_input(label, key=field_key)

    c1, c2 = st.columns([1, 4])
    with c1:
        save = st.button(
            t("common.save"), key=f"save_{product_id}_{task_key}", type="primary",
        )
    if save:
        # Preserve any extra payload keys (e.g., product_ids for bundles).
        merged = {**current, **new_values}
        db.save_content(product_id, task_key, merged)
        st.success(t("common.saved"))
        return True
    return False


def product_summary_row(p: dict, sell: int, cost: float) -> None:
    """Compact product header used in detail panels."""
    sku = p.get("sku") or ""
    name = p.get("name") or sku
    brand = p.get("brand") or ""
    category = p.get("category") or ""

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            f"<div style='font-size:1.1rem;font-weight:600;margin-bottom:2px'>{name}</div>"
            f"<div style='color:#6b6b6b;font-size:0.85rem'>"
            f"<code>{sku}</code> · {brand or '—'} · {category or '—'}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div style='text-align:right'>"
            f"<div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;color:#2d4a3e;font-weight:600'>"
            f"฿{sell:,}</div>"
            f"<div style='color:#6b6b6b;font-size:0.8rem'>{t('common.cost')} ฿{int(cost):,}</div>"
            "</div>",
            unsafe_allow_html=True,
        )


def content_status_chips(product_id: int) -> str:
    """HTML string of chips showing which content tasks exist for a product."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT task FROM content WHERE product_id = ?", (product_id,)
        ).fetchall()
    tasks_done = {r["task"] for r in rows}
    chips = []
    for k, m in task_registry.ALL.items():
        done = k in tasks_done
        opacity = 1.0 if done else 0.3
        tooltip = m.TASK["label"]
        icon = m.TASK["icon"]
        chips.append(
            f"<span class='nirva-tag' style='opacity:{opacity}' title='{tooltip}'>{icon}</span>"
        )
    return "".join(chips)
