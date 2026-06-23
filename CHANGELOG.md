# nirva.sell — Changelog

Built iteratively. Current stats:
**142 pages · 3,800+ i18n keys · 19 languages · 8 sign-in methods · SQLite per-user isolation**

---

---

---

---

---

---

---

---

## v99 — alerts module i18n pass (C0/F4/alerts.py)
- `alert_kind_name()` helper; `alrt.kind_*` + `alrt.msg_*` keys (6 alert types)
- Removed hardcoded Thai from `ALERT_TYPES` labels and `check_all()` messages
- 12 new keys → 19 langs

## v98 — content_cal module + live promo i18n + placeholder pass (B0/B/D4/R/d)
- New `content_cal.py` — fixes B0 runtime mismatch with `content_calendar.py`; `content_calendar` table for alerts
- `content_type_label()`, `content_status_label()`, `live_promo_label()` helpers
- Promo calendar: slug-based `live.promo_*` keys (19 langs); updated B_Live, sidebar, app, generate
- Placeholders: D4 CSV, R live chat, d Bundles name
- 33 new keys → 19 langs

## v97 — G/F/H/E/D placeholder + budget/notif pass (24 pages)
- `notif_kind_name()`, `budget_category()` helpers
- Placeholders: date/time/datetime, tax ID, voucher, fulfillment, labels, etc.
- G1 budget categories via `bgt.cat_*`; I Notifications channel kind labels
- 24 new keys → 19 langs

## v96 — Field labels / loyalty / PO / placeholder pass (4/F5/A5/B3/E5/D8/C2/C7/F9/e)
- `field_label()`, `loyalty_tier()`, `po_status()` helpers
- 32 `outfield.*` task output fields, 5 loyalty tiers, 5 PO statuses
- Common placeholders: month/date/time/tax/supplier/hashtags
- 52 new keys → 19 langs

## v95 — History/catalog/settings + placeholder pass (4/2/D6/C3/W/Z/o)
- History compliance/export channels via `platform_name()`; download btn + summary keys
- Catalog QR target, D6 carrier/platform selectboxes
- Reuse `comm.order_ph`, `promo.coupon_ph`; new `common.sku_ph`, `common.qr_custom`
- 11 new keys → 19 langs

## v94 — Platform/carrier/COD/ads label pass (w/W/c/e/K/Z/D8/A4/F9)
- `platform_name()`, `carrier_name()`, `expense_category()`, `payment_type_name()` helpers
- 16 platform + 7 carrier + COD/ads/expense keys
- Replaces `.title()` / hardcoded platform & carrier labels across 10 pages

## v93 — Report/returns/reason inline pass (X/G0/E4/C3/C)
- X Reports: best-day card, combo row, repeat ratio; `day_name()` helper
- G0 growth %, E4/C3 return reason labels via `return_reason()`
- C Alerts policy feed line; fix vi/ru translation corruption from v92
- 9 new keys → 19 langs

## v92 — Analytics/platform/format inline pass (F/E1/o/G0/C3/D2/E4/X/B0)
- Dashboard orders/units KPI, E1 platform/combo/peak/best-day lines
- `common.platform_direct`, promo budget %, tax expense line, ret SKU line
- Report peak-hour badge, content-cal status label
- 11 new keys → 19 langs

## v91 — Policy/rule/card templates (C/j/G/B4/7/G0/z/q/p/v/n/o)
- Alerts policy feed, auto-rule templates, turnover DOI/RP lines, CLV tiers
- Supplier score grades, biz health grade, promo ROI, CRM last order, etc.
- 34 new keys → 19 langs

## v90 — Residual card/detail inline pass (A6/C7/k/U/C8/B3/B2/C4/K/p/n/C5/A8/A4/w/6/G0/E1)
- 23 new keys: supplier detail, CLV lines, tax preview, scorecard dims, recon variance, etc.
- Quick-win reuse: `rst.reorder_pieces`, `common.n_*`, `cust.email`, `chan.line_aov`

## v89 — Full 19-lang expansion (all i18n keys)
- `scripts/expand_i18n_langs.py` — translate → `scripts/i18n_lang_cache/{lang}.json` + `merge`
- All **3,782 keys** now have **19 languages** (parallel Google Translate + en fallback)
- `th+en only` count: **0**

## v88 — i18n auto-translate v82–v87 keys (19 langs)
- New `scripts/expand_i18n_langs.py` — Google Translate batch expander (resumable, UTF-8 safe)
- 221 keys from B/C pack → v87 now have all 19 `LANGS` in `i18n.py`
- Multiline `custom_task.*` prompts remain th+en only (long AI templates)

## v87 — Residual inline pass (U/b/D6/Y/z/H/2/E7/A9/6)
- `U_` customer card subline + edit form email/LINE labels
- `b_` supplier form labels, card SKUs/POs/lead, placeholders, price SKU field
- `D6` About tab HTML → `set.about_*` keys
- `Y_` batch scope target uses `common.n_skus` / `batch.scope_all`
- `z_` CRM customer option format, `H_`/`G_` Account role/user/delete word
- `2_` Catalog URL, `E7` weight ≤ kg, `A9` variant placeholders/stock, `6_` save presets btn

## v86 — Final i18n pass (I/J/A0/l_/S_/j_/s_/e_)
- `A0` motivational quotes, `l_` ABC inline labels, `I_` Notifications full form labels
- `S_` PhotoStudio backgrounds, `J_` custom task prompt/sample, `j_` rule fires line, `s_` Messages
- `e_` Calendar uses `i18n_inline.day_names_mon_first()`

## v85 — World-class i18n (format strings + shared helpers)
- Add `i18n_inline.py` — `day_name()` helper shared across pages
- Add `{n}` / `{amount}` format keys (`common.n_orders`, `rst.line_*`, `srch.*`, …)
- Wire remaining A/U/K/Z/M/7_/T_/i_ pages; refactor E1 to use `i18n_inline`

## v84 — G/H/W pack i18n (Thai source of truth)
- Replace hardcoded Thai/English inline strings in G/H/W pages and lowercase companions with `t()` keys
- Add `common.customers`, `turn.item_stock_doh`, `pay.bank_ph`, `comp.cheaper_by`, `var.cost_line`, etc.

## v83 — D/E/F pack i18n (Thai source of truth)
- Replace hardcoded Thai/English inline strings in D0–D9, E0–E8, F0–F9 pages with `t()` keys
- Add `common.remaining`, `tax.quarter_line`, `ship.carrier_margin_line`, `vou.type_*`, `skup.detail_*`, etc.
- Reuse `common.*` and `analytics.*` day keys where applicable

## v82 — B/C pack i18n (Thai source of truth)
- Replace hardcoded Thai/English inline strings in B0–B9 and C0–C9 pages with `t()` keys
- Add `common.*` inline labels + module format strings (`goal.progress_line`, `inv.subtotal_line`, …)
- Thai remains source of truth per NIRVA ecosystem i18n convention

## v81 — Policy → Knowledge Hub bridge
- `knowledge_hub.capture_policy_change()` — idempotent policy/fee events pushed into Hub
- `scripts/policy_check.py` — cron captures policy changes per user DB
- `E_📋_Policies.py` — applying fee updates saves a Decision node + toast
- `O_🛡_Compliance.py` — link + KPIs from Standards Knowledge Graph
- README updated to 142 pages

## v80 — Knowledge Ecosystem Pack (00–01, Search)
- `00_🧠_KnowledgeHub.py` — organizational knowledge graph (Vision, SOP, decisions, risks…)
- `01_📚_Standards.py` — browse Universal Compliance Graph (controls, evidence reuse, ERP mapping)
- `standards_kb/data/` — machine-readable graph (60 standards · 20 controls · 799 edges)
- `standards_kb/seed_data.py` — generator for the JSON data layer
- Global Search (`A2`) now includes Knowledge Hub results + KPI
- Spotlight (⌘K) indexes Knowledge Hub + Standards pages

## v79 — Inventory Intelligence Pack (H4–H9)
- `H4_☠_DeadStock.py` — slow/dead SKU detector, capital-at-risk warning, action suggestions
- `H5_🔄_StockTurnover.py` — turnover ratio + days-on-hand per SKU, reorder list
- `H6_📈_SKUTrends.py` — rising stars, declining, new products (14-day window), weekly sparklines
- `H7_🔤_ABC.py` — ABC/Pareto analysis (80/15/5 revenue rule), investment advice
- `H8_⭐_ProductScore.py` — composite health score (sales × margin × reviews) + BCG quadrant
- `H9_🏭_Wholesale.py` — tiered wholesale prices, quick quote calculator, auto price lookup
- 571 i18n keys added across v76–v79 (total 3,749)

## v78 — Finance & Docs Pack (G8–H3)
- `G8_🧾_Invoices.py` — customer invoices with dynamic line items, text render
- `G9_📄_TaxInvoice.py` — VAT 7% tax invoices with INV-YYYYMM-NNNN running serial
- `H0_💵_CashFlow.py` — daily/monthly inflow vs outflow bar chart, current-month forecast
- `H1_📱_PromptPay.py` — EMVCo QR payload + PNG (qrcode lib), payment account settings
- `H2_🗓_ProfitCalendar.py` — daily profit heatmap, weekly summary, best/worst 5 days
- `H3_📤_Export.py` — full store data export as ZIP (CSV per table), size estimate

## v77 — Content & Operations Pack (G2–G7)
- `G2_📅_ContentCalendar.py` — post scheduler across 7 platforms, status tracking, today alerts
- `G3_📋_PickPack.py` — pick list + pack slips for pending orders, copy-to-clipboard text
- `G4_🚀_Fulfillment.py` — mark shipped with tracking number, bulk CSV update
- `G5_📝_Notes.py` — notes/tasks/reminders/issues/ideas, resolve, pin-to-top
- `G6_🔴_LiveSell.py` — live session manager, real-time order logging, session summary
- `G7_🌅_DailyBriefing.py` — morning digest: yesterday KPIs + alerts + today's tasks

## v76 — Sales & Promotions Pack (F6–G1)
- `F6_📢_Promotions.py` — create/activate/pause/delete promotions (6 types)
- `F7_🎟_Vouchers.py` — voucher/coupon codes + 8 festival templates (Songkran, 11.11, etc.)
- `F8_💡_PriceOpt.py` — optimal price calculator per platform, cross-platform comparison table
- `F9_📣_AdTracker.py` — ROAS tracking per campaign, update spent/revenue inline
- `G0_📡_ChannelPerf.py` — platform revenue comparison + MoM growth by channel
- `G1_💰_BudgetTracker.py` — monthly budget limits per category, % progress bars, over-budget alert

## v75 — Financial Intelligence Pack (F0–F5)
- `F0_📊_PnL.py` — P&L statement: monthly / quarterly / annual / 6-month trend
- `F1_💹_SKUProfit.py` — per-SKU profitability with health flags (healthy/warning/thin/losing)
- `F2_🔮_Forecast.py` — demand forecast 30/60/90-day horizon, stockout risk radar
- `F3_📦_Restock.py` — restock planner: critical/urgent/soon tiers, record + receive orders
- `F4_🔔_Alerts.py` — smart alert engine (6 alert types), dismiss, configurable thresholds
- `F5_🎁_Loyalty.py` — points system, 5 membership tiers, rewards catalogue, leaderboard

## v74 — Customer & Operations Pack (E3–E8)
- `E3_👥_Customers.py` — customer list, VIP/dormant views, tier badges (Bronze→Diamond)
- `E4_🔄_Returns.py` — return logging, loss tracking, by-reason/platform/SKU analysis
- `E5_🛒_PurchaseOrders.py` — PO creation with line items, send/receive stock flow
- `E6_💬_QuickReplies.py` — reply templates with variable substitution, bump-use tracking
- `E7_🚚_Shipping.py` — carrier comparison, COD fee calc, true margin after shipping
- `E8_🎯_RFM.py` — RFM segmentation (9 segments), segment heatmap, customer drill-down

## v73 — Reviews, Expenses & Analytics Pack (D7–E2)
- `D7_⭐_Reviews.py` — review tracker with reply workflow, by-SKU and by-platform views
- `D8_💰_Expenses.py` — expense logger, monthly summary, category chart
- `D9_🌟_Influencers.py` — influencer CRM, commission tracking, mark-paid flow
- `E0_⚡_FlashSale.py` — flash sale manager with active-now banner
- `E1_📈_Analytics.py` — AOV trend, hourly/daily heatmaps, platform growth, repeat rate
- `E2_🏆_KPIs.py` — 16-metric health scorecard with colour-coded health score 0–100

## v72 — COD, Restock & Supplier Pack (D1–D6)
- Sourcing, COD management, restock planner, supplier ledger, notes pages

## v71 — Core Operations Pack (C5–D0)
- Orders, inventory, stock history, customer management

## v53–v70 — AI Content Engine + Marketplace Integrations
- AI tasks: listing, LINE, Facebook, TikTok, email, Q&A, promotion, bundle, all-in-one
- Marketplace exporters: Shopee, Lazada, TikTok Shop, Amazon, eBay, Etsy, Shopify
- Vision intake (image → product data), QR code scanner

## v30 — GitHub / Facebook / LINE login (no-file-edit setup)
- `oauth.py` — generic OAuth2 client for GitHub, Facebook, LINE (the 3 popular non-OIDC providers)
- **Admin UI configures everything** — paste client_id/secret in `👑 Admin` page → button appears on login screen instantly. No `secrets.toml` editing, no restart needed.
- HMAC-signed `state` token (CSRF protection) using the magic-link secret — no extra DB table
- Per-provider profile normalizer translates each provider's idiosyncratic JSON into our `{provider, sub, email, name, avatar}` shape
- GitHub: handles private-email edge case via `/user/emails` fallback
- LINE: synthesizes placeholder email when scope doesn't return one (so account creation still works)
- Callback handled via query params (`?oauth=...&code=...&state=...`) — no custom routes
- 7 new i18n keys × 7 langs = 49 new translations (total 663 keys)
- Now 8 ways to sign in: Email+password · Magic link · Google · Apple · Microsoft · GitHub · Facebook · LINE

## v29 — Easy sign-in (Google / Apple / Microsoft + email magic link)
- **Native OIDC** via Streamlit 1.42+ `st.login()` — Google · Apple · Microsoft buttons appear automatically when configured in `.streamlit/secrets.toml`. Zero custom OAuth code.
- **Magic-link login** (`magic_link.py`) — passwordless email flow with HMAC-signed self-contained tokens (no DB cleanup), 15-min TTL, 60-sec per-email throttle. Falls back to inline link if SMTP isn't configured (dev-friendly).
- **Smart account linking** in `auth.login_or_create_oauth()` — match by `(provider, sub)` → match by email (auto-attach OAuth to existing password user) → create new (first user = admin)
- **Schema migration** (idempotent `PRAGMA table_info` probe) adds `avatar_url`, `oauth_provider`, `oauth_sub` columns + composite index — no data loss for existing accounts
- **`_auth_gate.py` rebuild** — social buttons row, "or" divider, Email-link tab (default), classic email+password tabs, demo button
- **Templates**: `.streamlit/secrets.toml.example` documents Google/Apple/Microsoft setup; `.env.example` adds `APP_URL` for magic-link URL building
- 11 new i18n keys × 7 langs = 77 new translations (total 656 keys)
- Smoke-tested: mint→consume, signature-tampering rejection, throttle behavior, idempotent OAuth, email→OAuth account linking, first-user-admin promotion

## v28 — Production deploy package (Docker + ops)
- `Dockerfile` — multi-stage build: builder compiles wheels, runtime is slim with no compilers (smaller image + smaller attack surface), runs as non-root `nirva` user, built-in `/_stcore/health` probe
- `docker-compose.yml` — single-host compose with healthcheck, memory caps (400M reservation / 1.5G limit), data volume, port bound to 127.0.0.1 only (forces reverse-proxy)
- `.dockerignore` — keeps build context small, prevents secrets/data leaking into image
- `.env.example` — documented template for every env var the platform reads (Claude key · PromptPay · Stripe · Cloudinary · SMTP · Telegram · LINE · Webhook · 3 supplier creds · markup)
- `scripts/backup.sh` — daily tar of every per-user DB to `backups/`, prunes after 14 days, optional Telegram success ping
- `scripts/healthcheck.sh` — external probe for UptimeRobot / cron
- `DEPLOY.md` — 10-min-to-domain guide: TL;DR · Streamlit Cloud · Cloudflare Tunnel · Docker on VPS · HTTPS via Caddy/nginx+certbot · backups · uptime · cron · scaling · troubleshooting · security checklist · $6/mo cost projection
- Validated: `docker compose config` passes, all bash scripts pass `bash -n`, all Python passes `py_compile`

## v27 — Order fulfillment loop (close the cycle)
- `fulfillment.py` — bulk tracking assignment + per-platform shipment CSV (Shopee/Lazada/TikTok column shapes) + printable HTML label generator
- 8 carriers wired: Kerry · Flash · Thailand Post · J&T · Ninja Van · BEST · SCG · DHL — each with the platform-specific code Shopee/Lazada/TikTok expects in their bulk uploads
- Page `K_📦_Fulfillment.py` — split-pane Pending / History tabs, bulk data-editor for pasting tracking #s, per-platform CSV downloads, A6 label HTML with Print button
- DB migration via `PRAGMA table_info` probe — adds tracking_number, carrier, shipped_at, buyer_* columns without breaking existing rows
- Inventory auto-decrement: stock drops when orders are imported AND when marked shipped (idempotent — re-importing same CSV doesn't double-deduct)
- 31 new i18n keys × 7 langs = 217 new translations (total 645 keys)

## v26 — Real payment processing (PromptPay + Stripe)
- `payments.py` — local EMVCo PromptPay QR generator (no API account needed, no fees), Stripe Payment Link wrapper, Buy Me a Coffee / GitHub Sponsors link slots
- Phone (10-digit), national ID (13-digit), and e-wallet (15-digit) PromptPay IDs all supported
- Dynamic QR with locked amount or static "any amount" QR; CRC-16/CCITT-FALSE checksum
- `donations` table — honor-system log (user reports what they sent); admin confirms/reconciles
- Support page: tabbed UI (📱 PromptPay / 💳 Stripe / ☕ Other), admin-only payment-settings panel with live preview, recent-donation dataframe + per-currency totals
- 30 new i18n keys × 7 langs = 210 new translations (total 829 strings)

## v25 — Solar / EV supplier (Integra Re)
- `reseller/scrapers/solar.py` — Magento-style scraper for solarshop.integra-re.co.th (panels · inverters · batteries · mounting)
- `reseller/config.py` — `SOLAR_USER` / `SOLAR_PASS` env vars (creds never hardcoded — only env or UI paste)
- `reseller/run.py` — `setup solar` + included in default `scrape` pipeline
- `suppliers.py` — central registry with display names, icons, categories; `display(key)` formatter used by Import + Sourcing pages
- Bridge auto-detects `SOLAR-xxx` SKUs; Sourcing groups by supplier with friendly names

## v24 — Onboarding wizard (4-step guided setup)
- `onboarding.py` — state machine (`mark_step`, `current_step`, `progress`, `is_complete`, `reset`) persisted via `user_settings`
- `pages/0_🚀_Start.py` — 4-step guided wizard with inline product-creation form + page-link jumps to Vision/Import/Generate/History
- `app.py` — first-run banner at top of Workspace shows progress + CTA until user dismisses
- Auto-credit: `mark_step("first_generate")` fires when Generate page batch completes; `mark_step("first_export")` fires on History CSV download
- `autodetect_progress()` reads catalog/history counts so milestones already met (CSV import etc) credit retroactively
- 37 new i18n strings × 7 langs = 259 new translations (total 579 strings)

## v23 — Custom AI tasks (extensible without code)
- `custom_tasks.py` — per-user task definitions in SQLite (key/label/icon/blurb/prompt/output_fields)
- `CustomTask` wrapper class quacks like a built-in task plugin (TASK dict + `build_prompt` + `parse`)
- `tasks/__init__.py` — `_DynamicRegistry` proxy merges built-in + user-custom at runtime
- Page: ✏ Custom Tasks — create / edit / delete + in-page test runner against sample product info
- Custom tasks auto-appear in Generate page, Workspace flows, all_in_one. Override built-ins by key collision.

## v22 — Wired notifications + persistent settings
- `user_settings.py` — per-user key/value store (API key, prefs persist across logins)
- Auto-fire notification after Workspace batch done
- Auto-fire notification from `scripts/policy_check.py` cron when policy changes
- Notification preferences UI (5 event toggles)

## v21 — Multi-channel notifications scaffold
- `notifier.py` — Email (SMTP), Telegram, LINE Notify, generic Webhook (Slack/Discord/Zapier)
- Per-user `notify_channels` table
- Page: 🔔 Notifications — add/edit/test channels, broadcast test

## v20 — Account settings + GDPR export
- Page: ⚙ Account — edit profile, change password, export all data as ZIP, self-delete
- `data_export.py` — GDPR-grade ZIP (account.json, raw SQLite, CSV dumps, images, README)
- `auth.py`: `change_password()`, `update_display_name()`

## v19 — Admin console
- Auto-promote first user to `admin`
- Page: 👑 Admin — user list, role/password/delete actions, last-admin safety rail
- `auth.is_admin()`, `reset_password()`, `set_role()`, `delete_user()` (with DB cascade)

## v18 — Multi-tenant auth
- `auth.py` — PBKDF2-SHA256 (stdlib), signup/login, sessions, per-user DB paths
- `_auth_gate.py` — login wall on every page
- Sidebar user chip + logout
- `db.py` — dynamic path: `data/users/{id}.db` per user

## v17 — Performance dashboard
- Page: 📈 Dashboard — KPIs (revenue/cost/profit/margin), daily chart, channel mix, top SKUs, dead stock
- `order_import.py` — multi-marketplace CSV parser (Shopee/Lazada/TikTok/Shopify/Amazon) with auto-detect

## v16 — Multi-language CSV export
- `translate.py` — Claude translator + persistent cache (zero re-translation cost)
- Pick N languages → ZIP of per-language CSVs (any platform format)
- 13 target languages

## v15 — Pre-flight compliance
- `compliance.py` — rule registry (length/forbidden/required/image specs per platform)
- Pre-flight check in History → 🔴 errors / 🟡 warnings
- Auto-fix (truncate title preserving word boundary)
- `tasks/ai_review.py` — Claude subjective review (honest/tone/brand-safe)
- Image dimension/aspect validation (Pillow)
- `scripts/policy_check.py` — cron runner for policy diffs

## v14 — Policy watcher
- `policy_watcher.py` — fetch marketplace policy URLs, hash diff, Claude extracts fees
- Page: 📋 Policies — manage sources, fetch/paste, apply diff to `fee_overrides.json`

## v13 — Smart Sourcing (multi-supplier optimizer)
- `sourcing.py` — auto-match by brand + model code regex
- Page: 🔀 Sourcing — multi-supplier groups, 3 criteria (price/stock/weighted), savings vs max
- `product_groups` table

## v12 — Live data (FX + promotions + trends)
- `live_data.py` — open.er-api FX (166 currencies, 6h cache), promo calendar (11.11, BF, CNY, Songkran), Claude trending keywords
- Page: 📊 Live — FX rates with delta vs static, promo countdown, AI-driven keyword trends

## v11 — Vision intake + QR
- Drop product photos → Claude Vision auto-fills product fields (name/brand/specs/est_price/confidence)
- QR codes in Catalog detail (Shopee/Lazada/custom URL targets)
- Streaming preview button in Workspace
- Image utilities: per-platform resize, background removal (rembg)
- Markdown / Notion export

## v10 — nirva.sell rebrand + global expansion
- Renamed from Listo → nirva.sell
- Multi-currency display (17 currencies, sidebar selector)
- 4 global marketplace exporters: Shopify, Amazon Flat File, eBay File Exchange, Etsy
- Multi-language AI content generation (target_lang param in all_in_one)
- Page: 🌍 Global Markets — per-platform profit ranking, catalog-wide scan, "best platform" recommendation

## v9 — Ethical pricing model
- LICENSE: MIT (open source)
- Page: 💝 Support — pay-what-you-can tiers (฿0 free forever, ฿99 coffee, ฿199 dev, ฿499 sponsor)
- Updated landing.html with free + voluntary contribution
- Pledge: no overcharge, no data selling, no dark patterns

## v8 — Reseller success features
- `fees.py` — platform fees with VAT for Shopee/Lazada/TikTok TH
- `tasks/customer_qa.py` — 8 Q&A pairs per product (chat support time saver)
- `tasks/promotion.py` — flash sale copy with urgency + discount math
- `tasks/all_in_one.py` — single Claude call → 7 content types (listing/LINE/FB/TikTok/email/Q&A/promo)
- Net profit display per platform in Workspace
- Pricing Assistant page

## v7 — Zen minimal UI
- Theme rebuild: paper cream background, ink text, sage accent, Cormorant Garamond serif
- Multi-page Streamlit: Workspace + Catalog + Generate + History + Import + Settings + Pricing + Vision

## v6 — Multi-page workspace + persistence
- SQLite DB for products + generated content
- Plugin-based task modules (generic AI batch runner)
- 6 initial tasks: marketplace listing, LINE broadcast, FB post, TikTok script, email blast, bundle
- Catalog + Generate + History pages

## v5 — Listo (commercial pivot)
- Streamlit single-page: drop → AI → multi-channel CSV
- Smart parser auto-detects Thai/English columns, strips ฿/commas
- 3 marketplace exporters: Shopee, Lazada, TikTok
- Landing page with comparison table

## v4 — Web dashboard
- Flask app wrapping the CLI as a real dashboard
- Live stats from DB, task buttons, log streaming
- Background task runner with stdout capture

## v3 — Cloudinary + preview + status
- `uploader.py` — Cloudinary upload (free tier)
- HTML preview generator
- Price change tracking + DB stats command

## v2 — End-to-end pipeline
- Synnex + VSTECS Playwright scrapers (storage_state persistence)
- SQLite store
- Claude listing generator (parallel batch)
- Shopee/Lazada/TikTok CSV exporters
- One-command CLI: `python run.py go`

## v1 — Project scaffold
- Initial Python project: Playwright + Anthropic + dotenv + SQLite
- Project structure: scrapers/, exporters/, generator/, db.py, run.py
