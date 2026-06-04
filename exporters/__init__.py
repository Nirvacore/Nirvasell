"""Channel-specific CSV exporters. Returns (filename, bytes) for direct download.

`SEA`     = Thailand / Southeast Asia (default currency THB)
`GLOBAL`  = Worldwide (default currency USD)
"""
from . import shopee, lazada, tiktok, shopify, amazon, ebay, etsy

SEA = {"shopee": shopee, "lazada": lazada, "tiktok": tiktok}
GLOBAL = {"shopify": shopify, "amazon": amazon, "ebay": ebay, "etsy": etsy}
ALL = {**SEA, **GLOBAL}
