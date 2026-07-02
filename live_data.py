"""Real-time data sources that update marketplace conditions for resellers.

What's here is intentionally limited to public, free, no-auth-required sources:
  • FX rates       — open.er-api.com (free, no key)
  • Promotion cal  — deterministic dates (11.11, 12.12, CNY, Songkran, BF, Cyber Mon, Prime Day, Diwali)
  • Trend signals  — Claude knows recent trends; we ask it per category

What's NOT here (would need auth or legal review):
  • Live competitor product prices
  • Marketplace order data
  • Supplier stock levels
"""
from __future__ import annotations
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

import httpx


ROOT = Path(__file__).parent
CACHE_DIR = ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ---- FX rates -------------------------------------------------------------

FX_URL = "https://open.er-api.com/v6/latest/THB"
FX_CACHE = CACHE_DIR / "fx.json"
FX_TTL_SECONDS = 6 * 3600   # 6 hours


def fetch_fx_rates(force: bool = False) -> dict:
    """Returns {ccy: rate_vs_THB, ...} or static fallback. Caches to disk.

    Result shape: {"fetched_at": ISO, "rates": {"USD": 0.0286, ...}}
    """
    if not force and FX_CACHE.exists():
        try:
            cached = json.loads(FX_CACHE.read_text())
            fetched_at = datetime.fromisoformat(cached["fetched_at"])
            if (datetime.now() - fetched_at).total_seconds() < FX_TTL_SECONDS:
                return cached
        except Exception:
            pass

    try:
        r = httpx.get(FX_URL, timeout=8.0)
        r.raise_for_status()
        data = r.json()
        if data.get("result") != "success":
            raise ValueError("FX API error")
        # The API gives rates of OTHER currencies vs THB (since we set base=THB).
        rates = {k: float(v) for k, v in data["rates"].items()}
        out = {"fetched_at": datetime.now().isoformat(), "rates": rates}
        FX_CACHE.write_text(json.dumps(out, indent=2))
        return out
    except Exception as e:
        # Return whatever's on disk, even if stale; or empty.
        if FX_CACHE.exists():
            return json.loads(FX_CACHE.read_text())
        return {"fetched_at": datetime.now().isoformat(), "rates": {}, "error": str(e)}


# ---- Promotion calendar --------------------------------------------------

# Each event: callable that returns (date, label) for the upcoming occurrence.
def _next_yearly(month: int, day: int, label: str) -> tuple[date, str]:
    today = date.today()
    candidate = date(today.year, month, day)
    if candidate < today:
        candidate = date(today.year + 1, month, day)
    return candidate, label


def _approx_lunar_new_year(today: date) -> date:
    """CNY approximations 2025-2030 (close enough for countdowns)."""
    table = {
        2025: date(2025, 1, 29),
        2026: date(2026, 2, 17),
        2027: date(2027, 2, 6),
        2028: date(2028, 1, 26),
        2029: date(2029, 2, 13),
        2030: date(2030, 2, 3),
    }
    candidate = table.get(today.year)
    if candidate and candidate >= today:
        return candidate
    return table.get(today.year + 1, date(today.year + 1, 2, 1))


def _last_thursday_november(year: int) -> date:
    """US Thanksgiving = 4th Thursday of November → Black Friday = next day."""
    d = date(year, 11, 30)
    while d.weekday() != 3:  # Thursday
        d -= timedelta(days=1)
    return d + timedelta(days=1)  # Friday


def _next_black_friday() -> tuple[date, str]:
    today = date.today()
    bf = _last_thursday_november(today.year)
    if bf < today:
        bf = _last_thursday_november(today.year + 1)
    return bf, "Black Friday"


def _next_cyber_monday() -> tuple[date, str]:
    today = date.today()
    bf = _last_thursday_november(today.year)
    cm = bf + timedelta(days=3)
    if cm < today:
        bf = _last_thursday_november(today.year + 1)
        cm = bf + timedelta(days=3)
    return cm, "Cyber Monday"


def upcoming_promotions(within_days: int = 365) -> list[dict]:
    today = date.today()
    events: list[tuple[date, str, str]] = []
    # (date, slug, region)
    fixed: list[tuple[int, int, str, str]] = [
        (1,  1,  "new_year_sale",        "Global"),
        (2,  14, "valentines",           "Global"),
        (3,  8,  "womens_day",           "Global"),
        (4,  13, "songkran",             "TH"),
        (5,  1,  "labor_day",            "Global"),
        (5,  5,  "mid_year_55",          "SEA"),
        (6,  6,  "brand_day_66",         "SEA"),
        (7,  7,  "mid_year_77",          "SEA"),
        (8,  8,  "brand_day_88",         "SEA"),
        (9,  9,  "super_shopping_99",    "SEA"),
        (10, 10, "brand_mega_1010",      "SEA"),
        (11, 1,  "diwali",               "IN"),
        (11, 11, "singles_day_1111",     "Global"),
        (12, 12, "year_end_1212",        "SEA"),
        (12, 25, "christmas",            "Global"),
        (12, 26, "boxing_day",           "UK/AU/CA"),
    ]
    for m, d, slug, region in fixed:
        ev_date, _ = _next_yearly(m, d, slug)
        events.append((ev_date, slug, region))

    # Dynamic events
    cny = _approx_lunar_new_year(today)
    events.append((cny, "chinese_new_year", "Asia"))
    bf, _ = _next_black_friday()
    events.append((bf, "black_friday", "Global"))
    cm, _ = _next_cyber_monday()
    events.append((cm, "cyber_monday", "Global"))

    # Amazon Prime Day — usually mid-July; we use July 16 as best-guess
    pd_date, _ = _next_yearly(7, 16, "prime_day")
    events.append((pd_date, "prime_day", "Amazon"))

    cutoff = today + timedelta(days=within_days)
    events = [e for e in events if today <= e[0] <= cutoff]
    events.sort(key=lambda e: e[0])
    return [
        {
            "date": e[0].isoformat(),
            "days_until": (e[0] - today).days,
            "slug": e[1],
            "region": e[2],
        }
        for e in events
    ]


def next_big_sale() -> dict | None:
    events = upcoming_promotions(within_days=120)
    return events[0] if events else None


# ---- Trending keywords (Claude-driven) -----------------------------------

_KW_CACHE: dict[tuple[str, str], list[dict]] = {}
_KW_CACHE_AT: dict[tuple[str, str], float] = {}
_KW_TTL = 4 * 3600  # 4h


def cached_trending_kws(categories: list[str], target_market: str = "TH",
                         api_key: str | None = None) -> list[str]:
    """Aggregate trending keywords across a set of categories, with per-pair
    4h memory cache so we don't hit Claude for every product."""
    out: list[str] = []
    seen: set[str] = set()
    for cat in set(c for c in categories if c):
        key = (cat, target_market)
        if key in _KW_CACHE and (time.time() - _KW_CACHE_AT.get(key, 0)) < _KW_TTL:
            items = _KW_CACHE[key]
        else:
            try:
                items = trending_keywords(cat, target_market, api_key=api_key)
                _KW_CACHE[key] = items
                _KW_CACHE_AT[key] = time.time()
            except Exception:
                items = []
        for it in items[:5]:
            kw = (it.get("kw") or "").strip()
            if kw and kw not in seen:
                seen.add(kw)
                out.append(kw)
    return out


def trending_keywords(category: str, target_market: str = "TH",
                      api_key: str | None = None) -> list[str]:
    """Ask Claude for currently-relevant search keywords. Claude has training-
    data knowledge of recent trends; not real-time but useful direction."""
    import os
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    prompt = (
        f"คุณคือ marketer ที่ติดตาม trend สินค้า {category} ในตลาด {target_market}\n"
        f"ปัจจุบัน (เดือน {date.today().strftime('%B %Y')}) keyword/hashtag ไหน "
        f"กำลังมาแรงในกลุ่ม {category}? ส่งกลับ JSON array ของ 10 keyword "
        f"พร้อมประมาณการ search-volume relative (low / medium / high) — ห้ามใส่ "
        f"``` หรือคำอธิบายเพิ่ม\n"
        f'[{{"kw":"...","heat":"high|medium|low","note":"..."}}, ...]'
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`")
    try:
        return json.loads(text)
    except Exception:
        return []
