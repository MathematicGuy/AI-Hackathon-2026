from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urlsplit

from .config import Settings
from .http import BlockedError, RetryableHTTPError, RespectfulClient
from .models import CategoryConfig, ProductLink
from .parsers import parse_category_page
from .utils import canonical_url


SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class SitemapEntry:
    url: str
    lastmod: str | None = None


def _xml_root(text: str) -> ET.Element:
    return ET.fromstring(text.lstrip("\ufeff"))


class Discoverer:
    def __init__(self, settings: Settings, categories: list[CategoryConfig], client: RespectfulClient):
        self.settings = settings
        self.categories = {item.code: item for item in categories if item.active}
        self.client = client

    def sitemap_children(self, max_sitemaps: int | None = None) -> list[str]:
        response = self.client.get(self.settings.site_base_url + self.settings.sitemap_index_path)
        root = _xml_root(response.text)
        children = [node.text.strip() for node in root.findall("sm:sitemap/sm:loc", SITEMAP_NS) if node.text]
        # Newest months/pages first makes --limit useful without downloading the
        # entire historical index.  The full mode still visits every child.
        children.sort(reverse=True)
        return children if not max_sitemaps else children[:max_sitemaps]

    def sitemap_links(self, category_codes: list[str], limit: int | None = None, max_sitemaps: int | None = None) -> list[ProductLink]:
        wanted = {self.categories[code].path_prefix.lower().rstrip("/") + "/" for code in category_codes if code in self.categories}
        if not wanted:
            return []
        links: list[ProductLink] = []
        seen: set[str] = set()
        for child in self.sitemap_children(max_sitemaps):
            response = self.client.get(child)
            try:
                root = _xml_root(response.text)
            except ET.ParseError:
                continue
            for item in root.findall("sm:url", SITEMAP_NS):
                loc = item.find("sm:loc", SITEMAP_NS)
                if loc is None or not loc.text:
                    continue
                url = canonical_url(loc.text, self.settings.site_base_url)
                path = urlsplit(url).path.lower()
                category = next((code for code in category_codes if path.startswith("/" + code.lower().strip("/") + "/")), None)
                if category is None or not any(path.startswith(prefix) for prefix in wanted) or url in seen:
                    continue
                seen.add(url)
                lastmod = item.find("sm:lastmod", SITEMAP_NS)
                lastmod_value = lastmod.text.strip() if lastmod is not None and lastmod.text else None
                # PostgreSQL stores sitemap_lastmod as DATE; retain the ISO
                # date portion while accepting full ISO timestamps.
                if lastmod_value and len(lastmod_value) >= 10 and lastmod_value[4] == '-' and lastmod_value[7] == '-':
                    lastmod_value = lastmod_value[:10]
                links.append(ProductLink(url=url, category_code=category, lastmod=lastmod_value, source="sitemap"))
                if limit and len(links) >= limit:
                    return links
        return links

    def category_links(self, category_codes: list[str], limit: int | None = None) -> list[ProductLink]:
        links: list[ProductLink] = []
        seen: set[str] = set()
        for code in category_codes:
            category = self.categories.get(code)
            if not category:
                continue
            response = self.client.get(category.url)
            for link in parse_category_page(response.text, code, self.settings.site_base_url):
                if link.url in seen:
                    continue
                seen.add(link.url)
                links.append(link)
                if limit and len(links) >= limit:
                    return links
        return links

    def discover(self, category_codes: list[str], source: str = "auto", limit: int | None = None, max_sitemaps: int | None = None) -> list[ProductLink]:
        if source in {"auto", "sitemap"}:
            try:
                links = self.sitemap_links(category_codes, limit, max_sitemaps)
                if links or source == "sitemap":
                    return links
            except (BlockedError, RetryableHTTPError):
                # A challenge/rate limit is host-wide; never issue fallback
                # category requests after the site has asked us to slow/stop.
                raise
            except Exception:
                if source == "sitemap":
                    raise
        return self.category_links(category_codes, limit)
