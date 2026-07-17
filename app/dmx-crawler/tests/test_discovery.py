from __future__ import annotations

import unittest

from dmx_crawler.config import Settings
from dmx_crawler.discovery import Discoverer
from dmx_crawler.models import CategoryConfig


class Response:
    def __init__(self, text: str):
        self.text = text


class FakeClient:
    def __init__(self):
        self.urls = []
        self.payloads = {
            'https://www.dienmayxanh.com/newsitemap/sitemap-product': '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://www.dienmayxanh.com/newsitemap/sitemap-product-2026-7?page=1</loc></sitemap></sitemapindex>',
            'https://www.dienmayxanh.com/newsitemap/sitemap-product-2026-7?page=1': '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.dienmayxanh.com/laptop/Acer-A315?utm_source=x</loc><lastmod>2026-07-17</lastmod></url><url><loc>https://www.dienmayxanh.com/tivi/tcl-65</loc></url><url><loc>https://www.dienmayxanh.com/news/story</loc></url></urlset>',
        }

    def get(self, url):
        self.urls.append(url)
        return Response(self.payloads[url])


class SitemapDiscoveryTests(unittest.TestCase):
    def test_sitemap_index_and_child_are_filtered_and_canonicalized(self):
        settings = Settings(min_request_interval_seconds=0)
        categories = [
            CategoryConfig('laptop', 'Laptop', 'https://www.dienmayxanh.com/laptop', '/laptop/'),
            CategoryConfig('tivi', 'Tivi', 'https://www.dienmayxanh.com/tivi', '/tivi/'),
        ]
        client = FakeClient()
        links = Discoverer(settings, categories, client).discover(['laptop', 'tivi'], source='sitemap')
        self.assertEqual([link.category_code for link in links], ['laptop', 'tivi'])
        self.assertEqual(links[0].url, 'https://www.dienmayxanh.com/laptop/acer-a315')
        self.assertEqual(links[0].lastmod, '2026-07-17')
        self.assertEqual(len(client.urls), 2)


if __name__ == '__main__':
    unittest.main()
