"""Supplier registry — friendly names, icons, and setup metadata for the
upstream reseller/ scrapers. Used by pages/5_🔌_Import.py and Sourcing.

Adding a new supplier:
  1. Add an entry below
  2. Add a matching scraper module in reseller/scrapers/{key}.py
  3. Wire it into reseller/run.py (setup + scrape commands)
  4. Set the SUPPLIER_USER / SUPPLIER_PASS env vars (or paste creds in UI)

The `source` key matches what reseller/scrapers/{key}.py writes into the
products.source column. Bridge prefixes SKUs as `{SOURCE_UPPER}-xxx`.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Supplier:
    key: str             # internal id, matches products.source
    name: str            # display name
    icon: str            # emoji
    domain: str          # public-facing URL
    category: str        # e.g. "IT distributor", "Solar / EV"
    notes: str           # short blurb shown in the UI

    @property
    def sku_prefix(self) -> str:
        return self.key.upper()


REGISTRY: dict[str, Supplier] = {
    s.key: s for s in [
        Supplier(
            key="synnex",
            name="Synnex",
            icon="🖥️",
            domain="synnex.co.th",
            category="IT distributor",
            notes="Notebooks · accessories · components",
        ),
        Supplier(
            key="vstecs",
            name="VSTECS",
            icon="🏢",
            domain="online.vstecs.co.th",
            category="IT distributor",
            notes="Networking · enterprise IT · peripherals",
        ),
        Supplier(
            key="solar",
            name="Integra Re Solar",
            icon="☀️",
            domain="solarshop.integra-re.co.th",
            category="Solar / EV / Alt energy",
            notes="Panels · inverters · batteries · mounting",
        ),
    ]
}


def get(key: str) -> Supplier | None:
    return REGISTRY.get((key or "").lower())


def display(key: str) -> str:
    """Pretty label for any source key — falls back to titlecase."""
    s = get(key)
    if s:
        return f"{s.icon} {s.name}"
    return (key or "?").title()


def all_suppliers() -> list[Supplier]:
    return list(REGISTRY.values())
