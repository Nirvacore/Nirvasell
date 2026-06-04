# nirva.sell — Changelog

Built iteratively across ~30 versions over one session. Final stats:
**17,400+ lines · 91 files · 21 pages · 10 AI tasks + custom · 14 marketplace integrations · 3 supplier scrapers · 4 payment methods · 8 carriers · 8 sign-in methods · 7 UI languages · 13 AI output languages · 17 currencies**

---

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
