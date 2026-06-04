"""Find higher-quality product images from public sources.

Sources tried in order:
  1. Wikipedia / Wikimedia REST API  — free, legal (CC), best quality
  2. Brand official site via DuckDuckGo HTML search — find product page,
     extract og:image meta tag
  3. Fallback to whatever image the supplier gave us

All fetches are cached to data/cache/img_*.json so we never hit the same
source twice for the same product.
"""
from __future__ import annotations
import hashlib
import json
import re
import urllib.parse
from pathlib import Path

import httpx

import sourcing


ROOT = Path(__file__).parent
CACHE_DIR = ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# Brand → preferred official domain (for site: filtered search)
BRAND_DOMAIN = {
    "cisco": "cisco.com",
    "hp": "hp.com",
    "hpe": "hpe.com",
    "microsoft": "microsoft.com",
    "logitech": "logitech.com",
    "razer": "razer.com",
    "samsung": "samsung.com",
    "wd": "westerndigital.com",
    "western digital": "westerndigital.com",
    "seagate": "seagate.com",
    "ubiquiti": "ui.com",
    "zyxel": "zyxel.com",
    "tp-link": "tp-link.com",
    "tplink": "tp-link.com",
    "netgear": "netgear.com",
    "linksys": "linksys.com",
    "dell": "dell.com",
    "lenovo": "lenovo.com",
    "asus": "asus.com",
    "acer": "acer.com",
    "apple": "apple.com",
    "sony": "sony.com",
    "lg": "lg.com",
    "canon": "canon.com",
    "epson": "epson.com",
    "brother": "brother.com",
}


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _cache_key(brand: str, model: str) -> str:
    h = hashlib.md5(f"{_norm(brand)}|{_norm(model)}".encode()).hexdigest()[:12]
    return h


def _cache_path(brand: str, model: str) -> Path:
    return CACHE_DIR / f"img_{_cache_key(brand, model)}.json"


def _cached(brand: str, model: str) -> dict | None:
    p = _cache_path(brand, model)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def _save_cache(brand: str, model: str, data: dict):
    _cache_path(brand, model).write_text(json.dumps(data, ensure_ascii=False, indent=2))


# ---- Wikipedia ----------------------------------------------------------

UA = "nirva.sell/1.0 (https://nirva.sell; resellers tools)"
WIKI_HEADERS = {"User-Agent": UA, "Accept": "application/json"}


_GENERIC_IMG_RX = re.compile(
    r"(logo|building|headquarters?|hq|campus|sign|wordmark|seal)",
    re.I,
)


def _is_useful_wiki_image(url: str, resolved_title: str, brand: str, search_term: str) -> bool:
    """Filter out brand-landing-page images (logos, HQ, sign-with-name)."""
    if _GENERIC_IMG_RX.search(url):
        return False
    # If the article title is *just* the brand name (no model after), it's
    # probably the company page, not a product page.
    title_l = resolved_title.lower()
    brand_l = brand.lower().strip()
    if title_l in (brand_l, brand_l.replace(" ", "_")):
        return False
    # Must mention the search term in the title OR be very specific
    search_l = search_term.lower()
    if search_l and search_l not in title_l and not any(
        tok in title_l for tok in search_l.split() if len(tok) > 2
    ):
        return False
    return True


def fetch_wikipedia_image(brand: str, model: str) -> str | None:
    """Look up `{Brand} {Model}` on English Wikipedia REST API."""
    title_candidates = [
        f"{brand} {model}".replace(" ", "_"),
        model.replace(" ", "_") if model else "",
        f"{brand}_{model}".replace(" ", "_"),
    ]
    for title in [t for t in title_candidates if t.strip()]:
        try:
            r = httpx.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}",
                timeout=6.0,
                follow_redirects=True,
                headers=WIKI_HEADERS,
            )
            if not r.is_success:
                continue
            data = r.json()
            if data.get("type") == "disambiguation":
                continue
            resolved_title = data.get("title", "")
            for key in ("originalimage", "thumbnail"):
                if key in data:
                    img_url = data[key]["source"]
                    if _is_useful_wiki_image(img_url, resolved_title, brand, model):
                        return img_url
                    break  # don't use either if the page is generic
        except Exception:
            continue
    return None


# ---- Brand site search --------------------------------------------------

OG_IMAGE_RX = re.compile(
    r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)
TWITTER_IMAGE_RX = re.compile(
    r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)


def _extract_og_image(html: str, base_url: str) -> str | None:
    """Pull og:image (or twitter:image) URL from a page's HTML."""
    for rx in (OG_IMAGE_RX, TWITTER_IMAGE_RX):
        m = rx.search(html)
        if m:
            img = m.group(1)
            if img.startswith("//"):
                img = "https:" + img
            elif img.startswith("/"):
                p = urllib.parse.urlparse(base_url)
                img = f"{p.scheme}://{p.netloc}{img}"
            return img
    return None


def _ddg_first_url(query: str) -> str | None:
    """DuckDuckGo HTML search → first result URL. Best-effort; may return None."""
    try:
        r = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            },
            timeout=8.0,
            follow_redirects=True,
        )
        if not r.is_success:
            return None
        # First /l/?uddg=... result
        m = re.search(r'/l/\?uddg=([^&"\'>]+)', r.text)
        if m:
            return urllib.parse.unquote(m.group(1))
        # Sometimes DDG returns direct hrefs
        m = re.search(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', r.text)
        if m:
            return urllib.parse.unquote(m.group(1))
    except Exception:
        pass
    return None


def fetch_brand_site_image(brand: str, model: str) -> str | None:
    """Find brand's official product page → extract og:image."""
    domain = BRAND_DOMAIN.get(_norm(brand))
    if not domain:
        return None
    query = f"site:{domain} {model}"
    page_url = _ddg_first_url(query)
    if not page_url:
        return None
    try:
        r = httpx.get(
            page_url,
            headers={"User-Agent": "Mozilla/5.0 nirva.sell/1.0"},
            timeout=8.0,
            follow_redirects=True,
        )
        if r.is_success:
            return _extract_og_image(r.text, page_url)
    except Exception:
        pass
    return None


# ---- Main entry point ---------------------------------------------------

def find_better_image(brand: str | None, name: str | None,
                      supplier_url: str | None = None,
                      force: bool = False) -> dict:
    """Try all sources. Returns {url, source, score, brand, model}."""
    model = sourcing.extract_model_code(name or "")
    # Search keyword: prefer extracted model, fall back to full product name
    # stripped of noise words. Without a brand we can't really search reliably.
    search_term = model or _strip_noise(name or "")
    if not brand or not search_term:
        return {"url": supplier_url, "source": "supplier", "score": 0.3,
                "brand": brand, "model": model}

    if not force:
        cached = _cached(brand, search_term)
        if cached:
            return cached

    # 1. Wikipedia
    wiki_url = fetch_wikipedia_image(brand, search_term)
    if wiki_url:
        result = {"url": wiki_url, "source": "wikipedia", "score": 0.9,
                  "brand": brand, "model": model}
        _save_cache(brand, search_term, result)
        return result

    # 2. Brand site
    brand_url = fetch_brand_site_image(brand, search_term)
    if brand_url:
        result = {"url": brand_url, "source": "brand", "score": 0.8,
                  "brand": brand, "model": model}
        _save_cache(brand, search_term, result)
        return result

    # 3. Supplier fallback
    result = {"url": supplier_url, "source": "supplier", "score": 0.5,
              "brand": brand, "model": model}
    _save_cache(brand, search_term, result)
    return result


_NOISE_RX = re.compile(
    r"\b(new|model|series|version|พิเศษ|รุ่น|ของแท้|ประกัน|ลด|free|sale)\b",
    re.I,
)


def _strip_noise(name: str) -> str:
    """Pull a clean search term from a noisy product name."""
    s = _NOISE_RX.sub(" ", name)
    s = re.sub(r"\s+", " ", s).strip()
    # Take first 4 tokens — usually brand+model+1-2 distinguishers
    return " ".join(s.split()[:4])
