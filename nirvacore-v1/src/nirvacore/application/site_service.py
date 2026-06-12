"""Site use cases."""
from __future__ import annotations

from nirvacore.domain.errors import NotFound
from nirvacore.domain.ids import SiteId, new_site_id
from nirvacore.domain.site import Site

from .ports import SiteRepository


class SiteService:
    def __init__(self, sites: SiteRepository) -> None:
        self._sites = sites

    def register(self, name: str, address: str = "") -> Site:
        site = Site(id=new_site_id(), name=name.strip(), address=address.strip())
        self._sites.add(site)
        return site

    def deactivate(self, site_id: SiteId) -> Site:
        site = self._require(site_id)
        site.deactivate()
        self._sites.save(site)
        return site

    def list_active(self) -> list[Site]:
        return self._sites.list_active()

    def _require(self, site_id: SiteId) -> Site:
        site = self._sites.get(site_id)
        if site is None:
            raise NotFound(f"site {site_id} not found")
        return site
