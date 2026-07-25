# Project Feature Inventory

> **Repo:** Nirvacore/Nirvasell · **Stack:** Python 3.11 · Streamlit 1.56 · SQLite (per-user DB) · Anthropic Claude (BYOK)
> **Audit date:** 2026-07-12 · **Method:** full source review of all 142 pages, ~130 modules, ~76 SQLite tables (evidence cited as `file:line`)
> **Repo status per CONTRIBUTING.md:** declared *legacy reference* — new features go to `nirvacore-v1` (TypeScript). This inventory reviews what actually ships here.

---

## 1. Executive Summary

**nirva.sell** is a Streamlit "operating system for online sellers" (Thai-market focus): AI content generation for product listings, plus inventory, orders, fulfillment, finance, marketing, CRM, suppliers, and knowledge/compliance tooling — 142 pages, ~76 SQLite tables in a per-user database, 19 UI languages.

**The core product loop genuinely works end-to-end:** upload/paste/photo a supplier price list → parse (xlsx/csv/PDF/vision, real Claude calls) → generate 8 content types per product → persist → export marketplace-ready CSVs (Shopee/Lazada/TikTok/Shopify/Amazon/eBay/Etsy). Order import (5 marketplace formats), the main Dashboard P&L, fulfillment, expenses, SKU profit, goals, and the AI utilities (slip verification, quick replies, customer messages) are real and correct.

**However, roughly half of the app's pages are broken or silently wrong:**

1. **48 pages (the entire `D1`–`H9` range) crash on open** with `ImportError`: they do `from auth import require_auth`, but `require_auth` only exists in `_auth_gate.py:148` — `auth.py` never defines it. (Verified: `grep -l "from auth import require_auth" pages/*.py` → 48 files.)
2. **11 modules query a normalized `orders`+`order_items` schema that was never built.** The real `orders` table (`db.py:91-105`) is flat (`total_price`, one row per line item); there is no `order_items` table and no `total_amount` column anywhere. Dead Stock, Stock Turnover, ABC, SKU Trends, Product Score, P&L Statement, Profit Calendar, Business Health, CLV, KPI COGS, Channel Perf and Sales Goals all crash or return fake numbers.
3. **Six table-name schema collisions** (`promotions`, `bundles`, `reviews`, `purchase_orders` ×3 schemas, `customer_notes`, `settings`): two modules each `CREATE TABLE IF NOT EXISTS` the same name with incompatible columns — whichever page a user opens first wins, and the sibling page then throws `OperationalError`.
4. **Buyer data never reaches the `orders` table** — the importer routes it only to `customers` (`order_import.py:208-266`) — so shipping labels and pack slips print with blank recipients, and repeat-purchase metrics are permanently 0.
5. Of the README's **"8 sign-in methods," only email+password (and on-screen magic link) work out of the box**; 3 OAuth providers are config-gated stubs and 3 are implemented but unreachable due to a config-storage bug.

**Overall completion estimate:** ~55 pages fully functional, ~15 partial/fragile, ~68 broken outright (48 ImportError + ~20 module/page bugs), plus a handful of intentionally static pages. The working core is a solid AI listing tool with basic commerce analytics; the long tail of 100+ business pages was written against a data model that drifted and was never integration-tested. There is **no CI, no test suite** for the app (the only tests cover the unshipped `nirva_research/payroll_engine.py`).

---

## 2. Feature List by Module

Status legend: ✅ Implemented · 🟡 Partial · 🎭 Mock/static only · ❌ Broken · ⬜ Missing

### 2.1 Authentication & Accounts

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Email + password sign-in | PBKDF2-SHA256 (200k iters), brute-force lockout (5 fails/15 min) | `_auth_gate.py` unified form | `auth.py:121-275`, `_rate_limit.py` | `users`, `login_attempts` (shared `data/accounts.db`) | ✅ | Solid. First-ever signup auto-promoted to admin (`auth.py:135`) |
| Magic-link sign-in | HMAC token, 15-min TTL | `_auth_gate.py:297` | `magic_link.py` | `magic_link_throttle` | 🟡 | **Link shown on screen via `st.code` unless SMTP env is set** (`_auth_gate.py:324-327`) — no proof of inbox possession on a stock deploy |
| Google / Apple / Microsoft OAuth | Native Streamlit `st.login()` OIDC | login screen buttons | `_auth_gate.py:24-36,114` | `users` | 🎭 | Config-gated: needs `.streamlit/secrets.toml`, which is not shipped → buttons never appear |
| GitHub / Facebook / LINE OAuth | Custom OAuth flow, admin-configurable | `G_👑_Admin.py` config panel | `oauth.py` | `settings` (per-user DB) | ❌ | Code is real, but config is saved to the **admin's per-user DB** while the pre-login screen reads the fallback `listo.db` (`auth.py:426-433`) → `configured_providers()` is always empty; buttons can never render |
| Welcome email | TH/EN welcome on signup | — | `welcome_email.py` | — | 🟡 | No-op without SMTP env; the default (magic-link) signup path never calls it at all |
| Admin console | User list, promote/demote, reset password, delete user+DB | `G_👑_Admin.py` | `auth.py:181-226` | `users` | ✅ | Roles = single `user`/`admin` column; no team/multi-seat model |
| Account page | Rename, change password, GDPR export, self-delete | `H_⚙_Account.py` | `auth.py`, `data_export.py` | `users` | ✅ | |
| Legal (ToS/PDPA) | TH/EN legal text + admin overrides | `L_📄_Legal.py` (only public page) | `legal.py` | `settings` | ✅ | |

### 2.2 AI Content Generation (core product)

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Workspace all-in-one flow | Drop file/paste → parse → markup pricing → 1 Claude call/product → 8 content types | `app.py` | `intake.py`, `parser.py`, `generate.py`, `tasks/all_in_one.py` | `batches`, `products`, `content` | ✅ | Model `claude-haiku-4-5`; streaming preview; docs say "5 types," code emits 8 |
| Task plugins (12) | listing, FB/LINE posts, TikTok script/live, ads, email, Q&A, bundle, promotion, AI review, review reply | `3_🤖_Generate.py` | `tasks/*.py` | `content` | ✅ | Real Thai prompts, JSON parsing, per-row error isolation |
| Custom AI tasks | User-defined prompt templates that behave like built-in tasks | `J_✏_Custom_Tasks.py` | `custom_tasks.py` | `custom_tasks` | ✅ | Custom key can silently shadow a built-in task (`tasks/__init__.py:23`) |
| File intake (xlsx/csv/PDF/paste) | Auto column-mapping incl. Thai headers; PDF text via pypdf → Claude extraction | `app.py`, `0_🚀_Start.py` | `intake.py`, `parser.py` | `products` | ✅ | cp874 Thai-Windows CSV fallback; image-only PDFs give a clear error (no OCR) |
| Vision product capture | Photo → Claude vision (opus-4-7 → sonnet-4-6 fallback) → editable product | `8_📸_Vision.py` | `vision.py` | `products` | ✅ | Bare `except` fallback can double-bill on auth errors (`vision.py:80`); images stored as **local disk paths** in `image_url` — not durable |
| Photo Studio | Background removal + square crop + resize (Pillow + rembg), bulk ZIP | `S_📷_PhotoStudio.py` | `image_utils.py` | — | ✅ | If `rembg` missing it **silently returns the original image** (`image_utils.py:69-70`) |
| Marketplace exporters | Shopee/Lazada/TikTok/Shopify/Amazon/eBay/Etsy upload CSVs | `4_📜_History.py`, `app.py` | `exporters/` (7 modules) | reads `content` | ✅ | |
| Catalog | Browse/search/edit/delete products, per-row content status | `2_📦_Catalog.py` | `products.py`, `db.py` | `products`, `content` | ✅ | |
| Content history | Browse/edit/regenerate/export past generations | `4_📜_History.py` | `db.fetch_content` | `content` | ✅ | |
| Global markets calculator | Cross-border net-profit ranking across intl. platforms | `9_🌍_Global.py` | `fees.py` | `products` | ✅ | Not a translation feature (multi-language output lives in Workspace target-lang selector) |
| Reseller-scraper import | Import products+images from companion scraper SQLite DB | `5_🔌_Import.py:14` | `bridge_reseller.py` | `products`, `batches` | 🟡 | Works only if the external `reseller/data/products.db` exists; graceful otherwise |
| Voice input | Browser Web Speech → clipboard | `app.py` | `voice.py` | — | 🟡 | By-design limitation: user must paste the transcript manually |
| AI rate limiting | — | — | — | — | ⬜ | **Missing.** `_rate_limit.py` covers login only; batch generation fans out 8–16 unthrottled threads (`generate.py:123`) |
| AI cost metering | — | — | `_cost_meter.py` | `donations` | 🎭 | Docstring claims usage tracking; actual code is a donation fundraising bar. No token accounting exists |

### 2.3 Orders, Fulfillment & Logistics

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Order import | Auto-detect Shopee/Lazada/TikTok/Shopify/Amazon CSV/XLSX; dedupe; stock decrement; auto-create customers | `F_📈_Dashboard.py:31-70` | `order_import.py` | `orders`, `customers`, `customer_orders` | ✅ | **Buyer name/phone/address parsed but never written to `orders`** → downstream label/slip/analytics gaps. Stock decrement writes a regex-substituted *string* back to `stock` (`order_import.py:303-317`) |
| Manual order entry | — | — | — | — | ⬜ | Missing; import files are the only way in |
| Marketplace APIs | Live order/product sync | — | — | — | ⬜ | **No marketplace API integration anywhere** — 100 % file import |
| Fulfillment | Unshipped list, bulk tracking assign, mark shipped (updates `orders.status` + stock), platform shipment CSVs, HTML labels | `K_📦_Fulfillment.py` ✅ / `G4` ❌ | `fulfillment.py` | `orders` (+ ALTERed cols) | 🟡 | Works via K; G4 is ImportError-dead **and** calls `mark_shipped(notes=…)` which doesn't exist. Labels print blank recipients (root defect above) |
| Pick & Pack | SKU pick list + pack slips | `i_📋_PickPack.py` ✅ / `G3` ❌ | `pick_pack.py` | `orders`, `products` | ❌ (effectively) | Pending filter wants status `new/pending/confirmed` but imports write `paid` (`pick_pack.py:18-20` vs `order_import.py:220`) → imported orders never appear |
| Shipping comparison | 7 Thai carriers by weight/COD/ETA | `a_🚚_Shipping.py` ✅ / `E7` ❌ | `shipping_calc.py` | — | 🟡 | Rates hardcoded "approximate 2024-25" (`shipping_calc.py:6-8`); no admin UI; carrier keys inconsistent with `fulfillment`/`tracking` |
| Tracking | Carrier tracking **URL templates** + customer message | inside `K_📦` | `tracking.py` | — | 🟡 | Link generation only; no carrier API/status polling |
| Returns | Log returns, loss analytics | `W_↩_Returns.py` ✅ / `E4` ❌ / `C3` ❌ | `returns.py` | `returns` | 🟡 | C3 loads but crashes (`s["this_month"]`, `rt.PLATFORMS` don't exist). **Returns never restore stock or update order status** |
| COD tracker | COD lifecycle, pending cash, double-shipping loss | `Z_📮_COD.py` ✅ / `D1` ❌ | `cod_tracker.py` | `cod_orders` | ✅ | Separate from `orders` — double data entry |
| Slip verification | Bank-slip image → Claude vision OCR + forgery heuristics vs expected amount | `P_📱_Slip.py` | `slip_verify.py` | — (events log) | ✅ | Real AI, honest disclaimer; **not** wired to orders (no "mark paid") |
| PromptPay QR | EMVCo payload + QR per amount | `A_💝_Support.py` ✅ / `H1` ❌ | `payments.py:75-141` | — | ✅ | Payload verified spec-correct incl. CRC-16/CCITT-FALSE |
| Label generator | Plain-text packing/address labels | `D4_🏷_Labels.py` ❌ | `label_generator.py` | `orders` | ❌ | Page ImportError-dead; module's from-order path also broken (`sqlite3.Row.get()` + nonexistent `order_items`) |
| Batch ops | CSV bulk stock/price updates | `Y_⚡_BatchOps.py` | `batch_ops.py` | `products` | ✅ | |
| Order analytics | Peak hours, AOV trend, combos, repeat rate | `X_📊_Reports.py` ✅ / `E1` ❌ | `order_analytics.py` | `orders` | 🟡 | Repeat-purchase rate permanently 0 (no buyer data in `orders`) |
| Live data | FX rates (real API), promo calendar, AI trending keywords | `B_📊_Live.py` | `live_data.py` | — | ✅ | |
| Today digest | 6 "needs attention" buckets | `N_📥_Today.py` | inline SQL | multiple | ✅ | "AI errors" bucket queries error rows that are never persisted → always empty |

### 2.4 Products, Inventory & Stock Analytics

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Product variants | Variant groups, cartesian generation, per-variant stock | `A9_🎨_Variants.py` | `product_variants.py` | `variant_groups`, `product_variants` | 🟡 | Siloed: never reconciled to `products.stock`; invisible to all analytics |
| Price history | Record price changes, trend chart | `B2_📉_PriceHistory.py` | `price_history.py` | `price_changes` | ✅ | A second, unused `price_history` table in `db.py:67-72` is dead schema |
| Price optimizer | Optimal price from cost/margin/fees | `F8_💡_PriceOpt.py` ❌ | `price_optimizer.py` | — | ❌ | Module fine; page DOA (ImportError) **and** calls a nonexistent `round_psych=` kwarg + wrong result keys — no page drives it correctly |
| Restock planner | Velocity → reorder qty; order/receive log | `A6_📦_Restock.py` ✅ / `F3` ❌ | `restock_planner.py` | `restock_config`, `restock_history` | ✅ | Receive does `stock+?` arithmetic — breaks on free-text stock |
| Smart restock | Second restock engine embedded in Catalog | `2_📦_Catalog.py:348` | `smart_restock.py` | `orders`, `products` | ✅ | Different formula & hardcoded 7-day lead vs restock_planner → two pages give different "days until out" |
| Stock reconciliation | Physical count vs system, write-back | `A8_🔢_StockRecon.py` | `stock_recon.py` | `stock_counts`, `stock_count_items` | ✅ | int−str TypeError risk on free-text stock |
| Dead stock | Idle-stock detection + advice | `m` ❌ / `H4` ❌ | `dead_stock.py:21-27` | joins `order_items` | ❌ | `no such table: order_items` — both pages crash |
| Stock turnover | Turnover ratio + days-on-hand | `q` ❌ / `H5` ❌ | `stock_turnover.py:27` | joins `order_items` | ❌ | Same root cause |
| ABC analysis | Pareto revenue classes | `l` ❌ / `H7` ❌ | `abc_analysis.py:21` | joins `order_items` | ❌ | Same; both pages also carry their own latent render bugs |
| SKU trends | Rising/declining/new SKUs | `t` ❌ / `H6` ❌ | `sku_trends.py:29,105` | joins `order_items` | ❌ | Same |
| Product score / BCG | Composite health score + quadrants | `B7` ❌ / `H8` ❌ | `product_score.py:37` | `SUM(total_amount)` | ❌ | Column doesn't exist |
| Demand forecast | Moving-average + trend forecast | `B8_🔮_Forecast.py` ✅ / `F2` ❌ | `demand_forecast.py` | `orders` | ✅ | One of the few analytics written against the real schema; F2 twin reads wrong keys (KeyError) |
| Inventory text parser | "5 ชิ้น"/"หมด" → int; OOS pre-flight | (library) | `inventory.py` | — | ✅ | Blank stock silently defaults to 99 units (`inventory.py:35`) — overselling risk |

### 2.5 Finance & Reporting

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Main dashboard | Revenue/cost/expenses/true-profit/margin KPIs, daily chart, channel mix, top SKUs + order-import UI | `F_📈_Dashboard.py` | inline + `fees.py`, `expenses.py` | `orders`, `products`, `expenses`, `returns` | ✅ | The strongest finance surface; all real data |
| Monthly P&L + CSV | Revenue−COGS−fees−expenses−returns | `X_📊_Reports.py` | `profit_report.py` | same | ✅ | The *working* P&L engine |
| P&L statement (formal) | Period statement | `A7` ❌ / `F0` ❌ | `pnl_statement.py:24…` | `total_amount` | ❌ | Competing engine, crashes; two P&L engines disagree by design |
| Cash flow (historical) | In/out by day/month | `C8` ❌ / `H0` ❌ | `cash_flow.py:19…` | `expenses.expense_date` | ❌ | Column is `date`; H0 additionally reads keys the module never returns |
| Cash flow forecast | Pending COD + unsettled − POs − return reserve; runway | `h_💧_CashFlow.py` | `cashflow.py` | `cod_orders`, `orders`, `purchase_orders`, `returns` | ✅ | Distinct feature from `cash_flow.py` despite the name; guarded, correct |
| Expenses | Full CRUD + categories + monthly summary | `V_💸` ✅ / `D8` ❌ | `expenses.py` | `expenses` | ✅ | Canonical `date` column that 5 other modules got wrong |
| Budget tracker | Budgets vs actual spend | `u` ❌ / `G1` ❌ | `budget_tracker.py:82` | `budgets`, `expenses` | ❌ | `expense_date` + `%%Y-%%m` strftime bug; budget categories don't even match expense categories |
| Tax report (PIT/VAT) | Quarterly/annual estimate, ฿1.8 M VAT threshold | `D2` ❌ | `tax_report.py:47,53` | `expenses` | ❌ | Page DOA + module `expense_date` crash; VAT-check part is fine |
| Tax invoice (ใบกำกับภาษี) | VAT 7 %, running INV-YYYYMM-NNNN, buyer TIN | `k_🧾` ✅ / `G9` ❌ | `tax_invoice.py` | `tax_invoices` | ✅ | Plain-text output only, no PDF |
| Invoices/receipts | Header + line items + preview | `C2_🧾` ✅ / `G8` ❌ | `invoices.py` | `invoices`, `invoice_items` | 🟡 | No status transitions or payment tracking; `COUNT(*)+1` numbering collides after any delete (`invoices.py:47-51`); overlaps tax_invoice (two parallel invoice systems) |
| SKU profit | True per-SKU profit incl. fees + returns | `f` ✅ / `F1` ❌ | `sku_profit.py` | `orders`, `products`, `returns` | ✅ | |
| Profit calendar | Daily profit heatmap | `r` ❌ / `H2` ❌ | `profit_calendar.py:23` | `order_items` | ❌ | |
| Sales goals | Targets vs actuals | `C9_🎯` ✅ / `x` ❌ | `goal_tracker.py` (✅, table `goals`) vs `goals.py` (❌, table `sales_goals`) | | 🟡 | Duplicate systems: `goal_tracker` live+correct; `goals.py` is a broken dead twin |
| KPI scorecard | 16 KPIs + health score | `E2` ❌ | `kpi_scorecard.py:61,75` | phantom `order_items`, `expense_date` | ❌ | Page DOA; module also **silently wrong** (COGS/expenses always 0 → margin ≈ 100 %) |
| Business health score | Composite 0-100 score | `v` ❌ | `biz_health.py:77,105,212` | `total_amount`, `order_items` | ❌ | |
| Daily briefing | Yesterday + alerts + today's tasks | `A0` ❌ / `G7` ❌ | `daily_briefing.py:31,184` | `total_amount` | ❌ | |
| Commissions | Staff % commissions, mark paid | `B5_👤` | `commissions.py` | `staff`, `commission_records` | ✅ | Manual sale amounts — not derived from orders |
| Quick calculator | Margin/break-even/ROI/discount tools | `A4_🧮` | `quick_calc.py` | — | ✅ | |
| Platform fees | Fee rates per marketplace | Dashboard etc. (`fees.py`) / `D5` ❌ (`platform_fees.py`) | both | — | 🟡 | **Two modules with contradictory hardcoded rates** (Shopee 6.42 %+3.21 % vs 3 %+2 %); only `fees.py` has an override file |

### 2.6 Marketing & Sales Channels

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Promotions (system A) | Coupon-style promo records with lifecycle | `C1_🎯` ✅ / `F6` ❌ | `promotions.py` | `promotions` | 🟡 | **Schema collision with promo_engine** (same table name); `apply_to_order()` never called — promos never touch real orders |
| Promo engine (system B) | Budget/ROI promo planner | `o_🎪_Promos.py` | `promo_engine.py` | `promotions` (collision!) | ❌/🟡 | Whichever of C1/o is opened second breaks; `record_redemption()` never called → ROI always 0 |
| Flash sales | Time-boxed sales w/ auto status | `E0` ❌ | `flash_sale.py` | `flash_sales` | ❌ (page) | Module fine; page DOA. `record_use()` never called. Third overlapping discount system |
| Vouchers | Code generator + per-marketplace CSV export | `T_🎟` ✅ / `F7` ❌ | `vouchers.py` | `vouchers` | ✅ | Redemption intentionally untracked (docstring) |
| Loyalty | Points/tiers/redeem/leaderboard | `A5_🎖` ✅ / `F5` ❌ | `loyalty.py` | `loyalty_points`, `loyalty_history` | 🟡 | Manual-only: points never auto-earned from orders |
| Bundles (A) | Manual bundles + component stock roll-up | `C4_🎁` | `bundles.py` | `bundles`, `bundle_items` | 🟡 | **Schema collision with bundle_engine** on `bundles` |
| Bundle engine (B) | Co-purchase-driven bundle suggestions | `d_🎁` | `bundle_engine.py` | `bundles` (collision!) | 🟡 | Its co-purchase SQL actually matches the real schema |
| Content calendar (A) | Revenue-target content planner | `B0_📅` | `content_cal.py` | `content_calendar` | ✅ | Also feeds `alerts.py` |
| Content calendar (B) | Social post planner + best-time suggestion | `e_📅` ✅ / `G2` ❌ | `content_calendar.py` | `content_posts` | ✅ | Duplicate concept, different tables; no AI-post wiring |
| Ads tracker | Manual ROAS/CPC/CTR per campaign | `c_📣` ✅ / `F9` ❌ | `ads_tracker.py` | `ad_campaigns` | ✅ | No ad-platform APIs |
| Influencer tracker | Creators + commission accrual | `D9` ❌ | `influencer_tracker.py` | `influencers`, `influencer_sales` | ❌ (page) | Module fine, only page is DOA; manual entry; promo codes not matched to orders |
| Live sell (tracker) | Manual session + per-item sale logging | `B6_📺` ✅ / `G6` ❌ | `live_sell_tracker.py` | `live_sessions`, `live_orders` | ✅ | Manual logging, not real-time |
| Live sell (CF tally) | Paste live-comments → CF tally + AI comment packs | `R_🎥_LiveSell.py` | inline + Claude | session state only | 🟡 | Third live-sell surface; persists nothing, shares no data with B6/G6 |
| Competitor watch | Manual competitor price comparison | `y_🔍` | `competitor_watch.py` | `competitor_prices` | ✅ | No scraping by design |
| Channel performance (A) | Platform revenue/AOV/trend | `C5_📊` | `channel_performance.py` | `orders` | 🟡 | Works except `top_skus_by_channel` (phantom `order_items`) |
| Channel performance (B) | Platform comparison + growth | `w` ❌ / `G0` ❌ | `channel_perf.py:22-91` | `total_amount`, `buyer_*`, `order_items` | ❌ | Fully broken duplicate |
| Message templates (A) | `{placeholder}` templates, 8 Thai seeds | `s_💬` | `msg_templates.py` | `msg_templates` | ✅ | |
| Message templates (B) | Platform-tagged templates | `B9_💬` | `message_templates.py` | `message_templates` | ✅ | Duplicate feature, different table (no collision) |
| Quick replies | FAQ kit + Claude reply generation | `Q_💬` ✅ / `E6` ❌ | `quick_replies.py` | `quick_replies` | ✅ | |
| Wholesale pricing | Qty-tier pricing + quote builder | `B4_🏷` ✅ / `H9` ❌ | `wholesale_pricing.py` | `wholesale_tiers` | ✅ | Reference tool; not wired to any order path |
| Multi-supplier sourcing | Cluster same product across suppliers, pick best offer | `D_🔀_Sourcing.py` ❌ | `sourcing.py` | `products`, `product_groups` | ❌ (page) | Page calls `page_header()` without importing it → NameError (`D_🔀_Sourcing.py`); module is sound |

### 2.7 Customers & CRM

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Customer directory | Auto-built from order imports; VIP tiers, dormancy | `U_👥` ✅ / `E3` ❌ | `customers.py` | `customers`, `customer_orders` | ✅ | Only entry path is import — no manual "add customer." E3 twin has KeyErrors on top of DOA |
| AI customer messages | Segment-aware Claude message drafting | `U_👥_Customers.py:212` | `customer_ai.py` | — | ✅ | No churn prediction (that's in broken CLV); no batch rate limiting |
| CRM notes/tags/follow-ups | Per-customer keyed by phone/name string | `z_📇_CRM.py` ❌ | `customer_crm.py` | `customer_notes`, `customer_tags`, `customer_followups` | ❌ | Page queries `orders.buyer_name`+`total_amount` → OperationalError; `customer_key` unrelated to `customers.id`; `customer_notes` schema collides with customer_segments' copy |
| Segments | Tag-based segmentation | `C6_👥` ❌ | `customer_segments.py:63-74` | reads `orders.buyer_name` | ❌ | Buyer columns NULL/absent → empty or crash |
| RFM | Quintile RFM, 9 segments | `g_🎯` ✅ / `E8` ❌ | `rfm.py` | `customers` | ✅ | The one customer analytic on the right data model |
| CLV | Lifetime value + churn risk | `n_💎_CLV.py` ❌ | `clv.py:24` | `SUM(orders.total_amount)` | ❌ | Always OperationalError |
| Reviews (tracker) | Manual review log, unanswered negatives | `B1_⭐` | `review_tracker.py` | `reviews` | 🟡 | **Schema collision with review_manager on the same `reviews` table** — whichever page is opened second breaks |
| Reviews (manager) | Status workflow (new/replied/…) | `D7` ❌ | `review_manager.py` | `reviews` (collision!) | ❌ | Page also DOA |
| Operational notes | Memos vs SKU/order/customer/supplier | `D0_📝` ✅ / `G5` ❌ | `notes.py` | `notes` | ✅ | G5 twin invents its own type vocab + no-op pin |

### 2.8 Suppliers, Purchasing, Knowledge & Ops

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| Supplier mgmt (A) | CRUD + per-SKU cost compare + simple PO log | `b_🏭` | `supplier_mgmt.py` | `supplier_contacts`, `supplier_prices`, `purchase_orders` (schema A) | ✅ | |
| Supplier directory (B) | Second CRUD + linked SKUs + terms | `C7_🏭` | `supplier_directory.py` | `suppliers`, `supplier_skus` | 🟡 | Duplicate of A on disjoint tables; join on `purchase_orders.supplier` crashes if schema A won |
| Supplier scorecard | A–D grades on price/delivery/volume | `p_🏆` ❌ | `supplier_score.py:81,121` | `supplier_prices` | ❌ | Selects nonexistent `price` column + `Row.get()` AttributeError |
| Purchase orders (real) | Draft→sent→partial/received; **receiving increments `products.stock`** | `B3_🛒` 🟡 / `E5` ❌ | `purchase_orders.py:114-133` | `purchase_orders` (schema B), `po_items` | 🟡 | **`purchase_orders` has 3 incompatible schemas across modules.** B3 (the only live page) has no "send" button, so POs are stuck in draft — the receive/stock path is unreachable in practice because E5 (which can send) is ImportError-dead |
| Pricelist intake | Dealer catalogs → products (Claude for PDF/paste) | `5_🔌_Import.py` | `intake.py` | `products` | ✅ | Doesn't populate `supplier_prices` — no link to scorecards |
| Knowledge Hub | Node/edge knowledge graph (20 node types) + graphviz map | `00_🧠` | `knowledge_hub.py` | `kh_nodes`, `kh_edges` | ✅ | Manual CRUD, not AI; opt-in starter seed |
| Standards graph | Static compliance catalog (61 orgs / 73 standards) | `01_📚` | `standards_kb/` (JSON) | — | ✅ | Reference browser only — no per-shop compliance tracking |
| Policy watcher | Fetch/paste marketplace policy → Claude fee extraction → apply + KH capture | `E_📋_Policies.py` ❌ | `policy_watcher.py` | JSON files + `kh_nodes` | ❌ (page) | Module real (httpx + Claude); page has `page_header` NameError; marketplace pages often SPA-blocked → paste path |
| Compliance page | Static standards-status matrix (public) | `O_🛡` | static | — | 🎭 | Separate `compliance.py` module = real listing pre-flight validator (unrelated to this page) |
| Alerts (aggregator) | 6 signal types w/ thresholds & dismissals | `C0` ❌ / `F4` ❌ | `alerts.py:121` | `alert_config`, `alert_dismissals` | ❌ | `low_stock` queries nonexistent `products.active`, unguarded → both pages crash. On-page-load only, no cron |
| Alerts (events feed) | Event log + reseller-scraper diffs + policy alerts | `C_🔔_Alerts.py` | `events.py`, `bridge_reseller` | `events` | ✅ | Third alerts page, unrelated architecture |
| Auto rules | If/then rules + run log | `j_⚙` | `auto_rules.py` | `auto_rules`, `rule_log` | 🟡 | **No background execution** — manual "Run now" only; 2/7 triggers implemented; 5/6 actions are log-only stubs (only LINE notify is real — against a dead API) |
| Team tasks | Kanban-lite tasks + assignees | `D3` ❌ | `team_tasks.py` | `tasks`, `team_members` | ❌ (page) | Module works, page DOA. Per-user DB → assignees are labels; **no real multi-user collaboration** |
| Notification channels | Email/Telegram/LINE/webhook config + test | `I_🔔` | `notifier.py` | `notify_channels` | ✅ | LINE channel targets the **discontinued LINE Notify API** (`notifier.py:157`; service ended 2025-03) |

### 2.9 Platform Infrastructure

| Feature | Description | Frontend | Backend/API | Database | Status | Notes |
|---|---|---|---|---|---|---|
| i18n (19 languages) | `t()` with chosen→en→th→key fallback | all pages | `i18n.py` (98k lines), `auto_translate.py` | `translations` | 🟡 | th/en curated; 12 secondary languages fallback-heavy; `data/i18n_auto/` not shipped |
| Theme & sidebar | Design system + nav + spotlight (⌘K) | `_theme.py`, `_sidebar.py`, `_spotlight.py` | — | — | ✅ | `theme.py`/`sidebar.py` are 4-line compat shims (not dead code) |
| Global search | Cross-table SQL search | `A2_🔎` | `global_search.py` | multiple | ✅ | |
| Backup/restore | Full DB zip download **and** restore | `A3_💾` | `backup_mgr.py` | — | ✅ | Restore keeps `.db.bak`; validation uses a hardcoded shared `/tmp` path |
| Export center | Per-table CSVs (BOM for Thai Excel) | `A1_📤` ✅ / `H3` ❌ | `export_center.py` | 5 tables | 🟡 | One of its queries also references `order_items` (`export_center.py:40`) |
| GDPR export | Account JSON + DB + CSVs + images ZIP | `H_⚙_Account.py` | `data_export.py` | — | ✅ | |
| Error log | Rotating JSON-line log | — | `error_log.py` | file | ✅ | |
| Onboarding | First-run banner, milestone-aware tips | all pages | `onboarding.py` | `settings` | ✅ | |
| Donations | PromptPay/Stripe-link/BMAC honor-system support | `A_💝` | `payments.py` | `donations` | ✅ | |
| Deployment | Multi-stage Dockerfile (non-root, healthcheck), compose, deploy.sh | — | `Dockerfile`, `docker-compose.yml` | — | ✅ | |
| CI / tests | — | — | — | — | ⬜ | **No `.github/workflows`, no app test suite.** Only `nirva_research/test_payroll_engine.py` (29 tests for an unshipped engine) |
| Static comparison page | Marketing competitor matrix | `M_⚖_Compare.py` | — | — | 🎭 | Hardcoded, public — by design |
| nirva_os / nirva_research / standards_kb docs | Strategy blueprints, payroll rules engine, compliance graph | — | JSON + loaders | — | ✅ (reference) | Explicitly reference material for the TypeScript rewrite, not app features |

---

## 3. Feature List by User Role

The app has exactly **three effective roles** (there is no team/staff login model — `team_members` and `staff` are label tables inside one owner's per-user DB).

**Public visitor (not signed in)**
- View Legal/ToS/PDPA (`L_📄_Legal.py`), the static Compliance matrix (`O_🛡`), the static competitor Compare page (`M_⚖`), and the landing page (`landing.html`).
- Sign up / sign in via email+password or magic link (on-screen unless SMTP configured). OAuth buttons do not appear on a stock deploy.

**Authenticated seller (role `user`)** — everything in section 2 that isn't broken, on their own isolated SQLite DB:
- Working today: full AI content pipeline (workspace, generate, custom tasks, vision, photo studio, exporters), catalog, order import + Dashboard P&L, fulfillment (K), returns (W), COD (Z), slip verify, batch ops, reports (X), expenses, SKU profit, cash-flow forecast, goals (C9), tax invoices (k), commissions, quick calc, vouchers, loyalty (manual), bundles/promotions (fragile), ads/influencer/live-sell/competitor trackers (manual), quick replies, message templates, customers + RFM + AI messages, suppliers (b), knowledge hub, standards browser, notifications, backup, GDPR export, search.
- Broken for them: everything in the D1–H9 page range, most stock analytics, CLV/CRM/segments, alerts (C0/F4), sourcing, policies, supplier score, and the finance pages listed in §2.5.

**Admin (role `admin`; first signup auto-promoted)**
- Everything above, plus user management (list/promote/reset/delete users incl. their DBs) in `G_👑_Admin.py`, OAuth provider config (currently ineffective, §2.1), legal-text overrides, donation/support configuration, and server-cost target for the cost meter.

---

## 4. Implemented Features (working end-to-end)

Verified real code paths reading/writing real tables:

- **AI content pipeline** — intake (xlsx/csv/PDF/paste/vision) → 12+1 generation tasks → `content` table → 7 marketplace CSV exporters (`app.py`, `generate.py`, `tasks/`, `exporters/`).
- **Custom AI task builder** (`custom_tasks.py`), **Photo Studio** (`image_utils.py`), **AI quick replies** (`quick_replies.py`), **AI customer messages** (`customer_ai.py`), **AI slip verification** (`slip_verify.py`), **AI trending keywords + real FX API** (`live_data.py`).
- **Order import** for 5 marketplace formats with dedupe, stock decrement, and automatic customer extraction (`order_import.py`).
- **Main Dashboard** true-profit KPIs and **monthly P&L in Reports X** (`profit_report.py`), **SKU profit** (`sku_profit.py`), **cash-flow forecast** (`cashflow.py`), **expenses CRUD** (`expenses.py`), **goals** (`goal_tracker.py`), **commissions**, **quick calc**, **Thai tax invoices** (`tax_invoice.py`, text output).
- **Fulfillment via page K** — mark-shipped updates order status/stock, platform shipment CSVs, print-HTML labels (minus recipient data).
- **COD tracker (Z), returns log (W), batch ops (Y), PromptPay EMVCo QR (`payments.py`)**.
- **Auth (email+password) with real password hashing and login rate limiting; admin console; GDPR export; backup/restore; notification channels (email/Telegram/webhook); global search; knowledge hub graph; standards browser; restock planner + smart restock; stock reconciliation; price history; variants (siloed); demand forecast (B8); RFM (g); customer directory (U); supplier mgmt (b); wholesale tiers; vouchers; message templates ×2; content calendars ×2; ads/influencer/live-sell/competitor trackers (manual-entry)**.
- **Deployment**: production-grade Dockerfile, compose, healthcheck; runs fully offline except AI/FX/notify calls.

---

## 5. Partially Implemented Features

- **Magic link & welcome/notification email** — real SMTP code, but on-screen/no-op without env config (`magic_link.py:118-176`, `welcome_email.py:24-26`).
- **Purchase orders** — full lifecycle incl. stock-incrementing receive exists (`purchase_orders.py:114-133`), but the only live page (B3) cannot send a PO and the page that can (E5) is ImportError-dead → the lifecycle is unreachable in practice.
- **Promotions / promo engine / flash sale / vouchers / loyalty** — four discount systems plus loyalty, all standalone record-keeping; none applies to or reads from `orders` (`promotions.apply_to_order`, `promo_engine.record_redemption`, `flash_sale.record_use` are never called from any page).
- **Auto rules** — persistence and UI exist, but no background execution; 2/7 triggers evaluatable, 5/6 actions are log-only stubs (`auto_rules.py:146-218`).
- **Invoices** — create/list/preview only; no status transitions, no payment tracking, fragile `COUNT(*)+1` numbering (`invoices.py:47-51`).
- **Channel performance (C5)** — headline stats work; top-SKUs sub-feature broken (phantom `order_items`).
- **Pick & pack** — real logic, but its "pending" status filter never matches imported orders' `paid` status (`pick_pack.py:18-20`).
- **Order analytics** — works except repeat-purchase/top-buyers (buyer data never lands in `orders`).
- **i18n** — 19 languages declared; ~12 are fallback-heavy without running the optional auto-translate batch.
- **Variants** — functional but a stock silo invisible to every analytic and to `products.stock`.
- **Team tasks / commissions staff** — single-user task labels, not real multi-user collaboration (per-user SQLite).
- **Bridge reseller import (5_🔌)** — complete code, but useful only when the external scraper DB exists.
- **Live sell** — two disconnected systems (persistent tracker B6/G6 vs ephemeral CF-tally R).

---

## 6. UI-only / Mock-only Features

- **`M_⚖_Compare.py`** — hardcoded competitor comparison matrix; no data, no backend (marketing page by design).
- **`O_🛡_Compliance.py`** — hardcoded standards-status list; does not read any compliance state (links to the static standards browser).
- **AI cost meter (`_cost_meter.py`)** — presents as usage/cost tracking in its docstring; actually a donation fundraising progress bar. No token accounting exists anywhere.
- **Google/Apple/Microsoft login buttons** — appear only with a `secrets.toml` that is not shipped; GitHub/Facebook/LINE buttons can never appear due to the config-storage bug (§2.1) even though the admin UI happily saves the config.
- **Auto-rule actions** `flag_product`, `auto_reorder`, `adjust_price`, `tag_customer` — selectable in the UI, but execute as log-strings only (`auto_rules.py:211-218`).
- **Support-tier cards** (`A_💝_Support.py`) — informational only, "no actual checkout" (by design).
- **Today page "AI errors" bucket** — queries error payloads that the generation path never persists → permanently empty (`N_📥_Today.py:91-97` vs `app.py:422-427`).
- **`orders.buyer_name/buyer_phone/buyer_address` columns** — created by `fulfillment.init()` and *read* by labels/pack-slips/analytics, but no code path ever writes them.

---

## 7. Missing Features

Expected from the project's own README/positioning but absent:

- **Marketplace API integrations** — no Shopee/Lazada/TikTok API client anywhere; all order/product data is manual file import. "Tracking" is URL templates, not carrier APIs.
- **`order_items` table** — 11 modules were written against it (`label_generator, profit_calendar, sku_trends, abc_analysis, stock_turnover, goals, channel_performance, biz_health, channel_perf, kpi_scorecard, dead_stock`); it is never created.
- **Manual order entry and manual customer creation** — no forms exist for either.
- **PDF output** for invoices/tax invoices/labels (all plain text; `tax_invoice.py:8` says "upgrade to PDF later").
- **Order-linked discounting** — no path applies promotions/vouchers/loyalty/wholesale tiers to an order or price.
- **Background jobs/cron inside the app** — alerts, auto-rules and briefings compute on page load only (shell scripts in `scripts/` exist but are outside the app).
- **AI usage metering & rate limiting** (BYOK cost visibility) — absent.
- **Real multi-user/team access** — per-user DB isolation precludes shared workspaces; `team_members`/`staff` are labels.
- **Review import** — reviews are manual entry only despite marketplace-centric positioning.
- **Stock restoration on returns**, and **linkage of COD records/slip verification to orders**.
- **CI pipeline and application test suite** — none.

---

## 8. Bugs, Inconsistencies, and Technical Risks

Ranked by blast radius:

1. **48 dead pages — `from auth import require_auth` (`ImportError`).** Every page from `D1_💳_COD.py` to `H9_🏭_Wholesale.py`. `require_auth` lives only in `_auth_gate.py:148`. One-line shim in `auth.py` (or a mass import fix) revives the entire range. *(Verified directly.)*
2. **Phantom normalized schema.** No `order_items` table, no `orders.total_amount`, no `expenses.expense_date` — but 13+ modules query them (see §7 and `pnl_statement.py:24`, `cash_flow.py:19`, `clv.py:24`, `alerts.py:121` (`products.active`), `biz_health.py:105`, `kpi_scorecard.py:61,75`, `goals.py:115-148`, `profit_calendar.py:23`, `channel_perf.py:22-91`, `customer_segments.py:63`, `tax_report.py:47`, `budget_tracker.py:82`, `supplier_score.py:81`). Result: ~20 additional pages crash or show wrong numbers.
3. **Six `CREATE TABLE IF NOT EXISTS` name collisions with incompatible columns** — first-visited page wins, sibling breaks: `promotions` (`promotions.py:25` vs `promo_engine.py:21`), `bundles` (`bundles.py` vs `bundle_engine.py`), `reviews` (`review_tracker.py:23` vs `review_manager.py:18`), `purchase_orders` (three schemas: `supplier_mgmt.py:44`, `purchase_orders.py:22`, plus `supplier_score`/`alerts` reading a third shape), `customer_notes` (`customer_crm.py:14` vs `customer_segments.py:31`), `settings` (`user_settings.py:20` vs `shop_settings.py:24`).
4. **Silently wrong finance numbers:** KPI scorecard's `_safe` wrappers turn schema errors into zeros → margin ≈ 100 % and net profit = revenue (`kpi_scorecard.py`). Contradictory hardcoded fee tables (`fees.py:73-76` Shopee 6.42 %+3.21 % vs `platform_fees.py:8-16` 3 %+2 %) make different pages report different profits for the same order. `%%Y-%%m` strftime bugs guarantee empty matches (`goals.py:116`, `budget_tracker.py:82`).
5. **Buyer data pipeline gap** — labels/pack slips unshippable, repeat-rate 0 (`order_import.py:208-266`).
6. **Custom OAuth config written to the wrong DB** (admin's per-user DB vs pre-login `listo.db`, `auth.py:426-433`) — feature can never activate.
7. **LINE Notify targets a discontinued API** (`line_notify.py:22`, `notifier.py:157`; service shut down 2025-03) — Settings LINE panel, notify channel and the one real auto-rule action all dead.
8. **Runtime crashers in "working-generation" pages:** `C3_↩_Returns` (`s["this_month"]`, `rt.PLATFORMS`), `E3_👥_Customers` / `E8_🎯_RFM` (KeyErrors on keys their module never returns), `D_🔀_Sourcing` & `E_📋_Policies` (`page_header` used without import → NameError), `l_🔤_ABC` (string unary `+`), `H0` reading nonexistent cash-flow keys.
9. **Data-type erosion:** `products.stock` is `INTEGER` by schema but `order_import._decrement_stock` writes back regex-processed strings (`order_import.py:303-317`); blank stock defaults to 99 (`inventory.py:35`); downstream arithmetic (turnover, recon variance, PO receive) can TypeError.
10. **Security posture:** API keys, LINE tokens and OAuth client secrets stored plaintext in SQLite (`user_settings.py:11-13`); magic-link tokens displayed on screen by default; backup validation writes to a shared hardcoded `/tmp` path (`backup_mgr.py:53`).
11. **No AI throttling/cost control:** up to 16 concurrent Claude calls with no backoff or budget (`generate.py:123`, `pages/3_🤖_Generate.py:126`).
12. **Duplication debt:** ~35 features have 2–3 page copies from two codebase "generations" (old `theme/auth/sidebar` imports vs new `_theme/_auth_gate/_sidebar`); the old generation is broken wholesale (#1) and, where it loads, consistently reads stale dict keys. Duplicated *modules*: `cash_flow`≠`cashflow` (both live, one broken), `goals` (dead) vs `goal_tracker` (live), `channel_perf` (broken) vs `channel_performance`, `restock_planner`+`smart_restock` (different answers to the same question), `msg_templates`+`message_templates`, `content_cal`+`content_calendar`, three supplier modules, two invoice systems, two review modules, two bundle modules, three promo systems, three alerts pages, three live-sell surfaces. Dead schema: `db.py:67-72` `price_history` table (superseded by `price_changes`).
13. **No CI / no tests** for the application; Streamlit's `showSidebarNavigation` exposes all 142 pages including every broken duplicate.

---

## 9. Recommended Next Steps

Priority order (highest leverage first):

1. **Fix the auth import (1 line).** Add `from _auth_gate import require_auth  # re-export` to `auth.py` (or rewrite the 48 imports). Instantly revives a third of the app. Then smoke-test each revived page — several have second-layer bugs (G4, H0, F2, H4-H8, E1…).
2. **Reconcile the data model.** Decide on the flat `orders` schema (it's what ships) and sweep the 13+ modules to `total_price`/`date`/no-`order_items`/no-`active`, or create a real `order_items` migration. This un-breaks Dead Stock, Turnover, ABC, Trends, Product Score, P&L Statement, Profit Calendar, BizHealth, CLV, KPIs, Goals(x), Channel Perf, Tax Report, Budget, Alerts.
3. **Resolve the six table-name collisions.** Pick one module per table (suggested keepers: `promotions.py`, `bundles.py`, `review_tracker.py`, `purchase_orders.py`, `customer_crm.py`, `user_settings.py`), rename or delete the rivals, and add a startup migration for existing user DBs.
4. **Write buyer fields into `orders` on import** (or make labels/pack-slips/analytics read from `customers`/`customer_orders`). This fixes shipping labels, pack slips, repeat-rate, segments, and CRM in one stroke.
5. **Delete or hide the losing duplicates.** Keep one canonical page per feature and remove the stale twin (the entire broken generation), collapse `goals.py`, `channel_perf.py`, one supplier module, one invoice system, one message-template module. This shrinks the audit surface by ~40 pages.
6. **Fix small crashers in otherwise-good pages:** `C3` Returns keys, `E3`/`E8` KeyErrors, `D_Sourcing`/`E_Policies` missing `page_header` import, `l_ABC` string concat, `pick_pack` status filter (`paid`), B3 PO send button, `supplier_score` column names.
7. **Unify fee rates** into `fees.py` with the override file as the single source; delete `platform_fees.py`'s rival table.
8. **Truth-in-UI pass:** remove or clearly label the stub auto-rule actions, the dead LINE Notify integration (migrate to LINE Messaging API), the unreachable OAuth config panel, and the README's "8 sign-in methods" claim.
9. **Add a minimal safety net:** a CI job that (a) imports every page module headlessly, (b) runs every module's `init()` against one fresh DB to catch schema collisions, and (c) runs a seed-and-query smoke test with `scripts/seed_demo.py`. Items 1–3 would all have been caught by (a)+(b).
10. **Longer term** (consistent with CONTRIBUTING.md's freeze): port the ~15 genuinely working, differentiated modules (AI pipeline, order import, profit engine, fulfillment, PromptPay, slip verify) to `nirvacore-v1` rather than continuing to maintain 142 Streamlit pages.

---

### Needs verification (not fully confirmed in this audit)

- `7_💰_Pricing.py` page internals (not individually audited; assumed part of the fees/markup flow).
- Actual behavior of Streamlit native OAuth if `secrets.toml` were provided (env-dependent).
- Whether any production deploy sets SMTP/LINE/Telegram env vars (runtime config, not code).
- `scripts/` cron tooling (`policy_check.py` etc.) — read as out-of-app utilities; not exercised.
