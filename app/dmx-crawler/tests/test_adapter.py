from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import quote

from dmx_crawler.adapters.dmx import DMXAdapter
from dmx_crawler.config import Settings
from dmx_crawler.http import LocationMismatchError
from dmx_crawler.models import LocationConfig


ROOT = Path(__file__).parent
PRODUCT = (ROOT / 'fixtures' / 'product_laptop.html').read_text(encoding='utf-8')
DELIVERY = (ROOT / 'fixtures' / 'delivery_hcm.json').read_text(encoding='utf-8')


class Response:
    def __init__(self, body: str):
        self.body = body.encode('utf-8')
        self.status = 200
        self.url = 'https://www.dienmayxanh.com/test'
        self.headers = {'content-type': 'application/json'}
        self.elapsed_ms = 1

    @property
    def text(self):
        return self.body.decode('utf-8')


class FakeClient:
    def __init__(self, delivery: str = DELIVERY):
        self.posts = []
        self.gets = []
        self.delivery = delivery
        self._cookies = {}

    def post_form(self, url, values, headers=None):
        self.posts.append((url, dict(values)))
        payload = {
            'ProvinceId': values['newcustomer[ProvinceId]'],
            'WardId': values['newcustomer[WardId]'],
            'HasLocation': True,
        }
        self._cookies['DMX_Personal'] = quote(json.dumps(payload))
        return Response('{"status":1}')

    def get(self, url, headers=None):
        self.gets.append(url)
        return Response(PRODUCT if '/Product/DeliveryDateTimeV4' not in url else self.delivery)

    def cookies(self):
        return dict(self._cookies)


class AdapterLocationTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(min_request_interval_seconds=0)
        self.hcm = LocationConfig(
            code='hcm', name='TP.HCM', province_id=3, province_name='Hồ Chí Minh',
            ward_id=26734, ward_name='Phường Bến Nghé', address='TEST HCM LOCATION', aliases=('Sài Gòn',),
        )
        self.hanoi = LocationConfig(
            code='hanoi', name='Hà Nội', province_id=1, province_name='Hà Nội',
            ward_id=1, ward_name='Phường Trúc Bạch', address='TEST HANOI LOCATION',
        )

    def test_location_confirmation_payload_and_delivery_match(self):
        client = FakeClient()
        adapter = DMXAdapter(self.settings, client)
        adapter.select_location(self.hcm)
        page = adapter.fetch_product('https://www.dienmayxanh.com/laptop/acer-a315', 'laptop', self.hcm)
        self.assertEqual(page.location_snapshot.returned_location['province_id'], 3)
        self.assertIn('/Common/locationConfirm', client.posts[0][0])
        self.assertEqual(client.posts[0][1]['newcustomer[WardId]'], 26734)
        self.assertTrue(any('/Product/DeliveryDateTimeV4?' in url for url in client.gets))

    def test_mismatch_fails_closed_before_caller_can_save(self):
        client = FakeClient()
        adapter = DMXAdapter(self.settings, client)
        adapter.select_location(self.hanoi)
        with self.assertRaises(LocationMismatchError):
            adapter.fetch_product('https://www.dienmayxanh.com/laptop/acer-a315', 'laptop', self.hanoi)

    def test_sessions_have_independent_cookie_jars(self):
        first, second = FakeClient(), FakeClient()
        a, b = DMXAdapter(self.settings, first), DMXAdapter(self.settings, second)
        a.select_location(self.hcm)
        b.select_location(self.hanoi)
        self.assertNotEqual(first.cookies()['DMX_Personal'], second.cookies()['DMX_Personal'])
        self.assertEqual(a.location.code, 'hcm')
        self.assertEqual(b.location.code, 'hanoi')


if __name__ == '__main__':
    unittest.main()
