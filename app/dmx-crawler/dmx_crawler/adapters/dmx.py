from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any, Mapping
from urllib.parse import urlencode, urljoin

from ..config import Settings
from ..http import BlockedError, HTTPClientError, HTTPResponse, LocationMismatchError, RespectfulClient, json_body
from ..models import DeliveryInfo, LocationConfig, LocationSnapshot, ParsedPage
from ..parsers import parse_delivery_response, parse_product_page
from ..utils import clean_text, location_matches, parse_cookie_json


class DMXAdapter:
    """Verified Điện Máy XANH HTTP adapter.

    The location flow mirrors the live site observed during reconnaissance:
    ``/Common/locationConfirm`` receives the selected province, ward and
    address, and ``/Product/DeliveryDateTimeV4`` renders delivery HTML using
    the session cookies.  Every adapter has its own CookieJar; callers must
    instantiate one adapter/client per location.
    """

    def __init__(self, settings: Settings, client: RespectfulClient):
        self.settings = settings
        self.client = client
        self.location: LocationConfig | None = None
        self._location_confirmed = False

    @property
    def base_url(self) -> str:
        return self.settings.site_base_url.rstrip('/')

    def _location_payload(self, location: LocationConfig, product_url: str = '') -> dict[str, object]:
        # Names and parameter casing are taken from the site's live
        # locationConfirmV4 JavaScript function.
        return {
            'newcustomer[ProvinceId]': location.province_id,
            'newcustomer[WardId]': location.ward_id,
            'newcustomer[Address]': location.address,
            'newcustomer[isDefault]': 'true',
            'newcustomer[CustomerSex]': 0,
            'cateUrl': '',
            'productUrl': product_url,
        }

    def verify_ward(self, location: LocationConfig) -> bool:
        """Ask the verified ward endpoint and check that the configured ward exists."""
        endpoint = self.base_url + '/Store/GetAllWardsByProvinceV4'
        response = self.client.post_form(endpoint, {
            'provinceId': location.province_id,
            'viewName': 'ListWard',
        })
        body = response.text
        # Ward ids appear in data-id/value attributes in the live popup.  Do
        # not accept an unrelated province merely because the request returned
        # HTTP 200.
        return bool(re.search(r'(?<!\d)' + re.escape(str(location.ward_id)) + r'(?!\d)', body))

    def select_location(self, location: LocationConfig, product_url: str = '', verify_ward: bool = False) -> dict[str, str]:
        if verify_ward and not self.verify_ward(location):
            raise LocationMismatchError(
                f'configured ward {location.ward_id} was not returned for province {location.province_id}'
            )
        endpoint = self.base_url + '/Common/locationConfirm'
        response = self.client.post_form(endpoint, self._location_payload(location, product_url))
        payload = json_body(response)
        if payload and payload.get('status') not in (1, '1', True):
            raise LocationMismatchError(f'location confirmation rejected: {payload}')
        cookies = self.client.cookies()
        personal = parse_cookie_json(cookies.get('DMX_Personal'))
        province = personal.get('ProvinceId', personal.get('provinceId'))
        ward = personal.get('WardId', personal.get('wardId'))
        try:
            province_id = int(province or 0)
            ward_id = int(ward or 0)
        except (TypeError, ValueError):
            province_id, ward_id = 0, 0
        if province_id != location.province_id or ward_id != location.ward_id:
            raise LocationMismatchError(
                f'cookie location mismatch: requested {location.province_id}/{location.ward_id}, '
                f'returned {province_id}/{ward_id}'
            )
        self.location = location
        self._location_confirmed = True
        return cookies

    def _require_location(self, location: LocationConfig | None = None) -> LocationConfig:
        selected = location or self.location
        if not selected or not self._location_confirmed:
            raise LocationMismatchError('location must be confirmed in this independent session first')
        return selected

    @staticmethod
    def _identifier(raw_html: str, content: Any, name: str) -> str | None:
        patterns = {
            'product_id': [
                r'(?:document\.)?productId\s*=\s*["\']?(\d+)',
                r'["\']ProductId["\']\s*:\s*["\']?(\d+)',
                r'data-productid\s*=\s*["\'](\d+)',
            ],
            'product_code': [
                r'data-productcode\s*=\s*["\']([^"\']+)',
                r'["\']ProductCode["\']\s*:\s*["\']([^"\']+)',
            ],
        }
        for pattern in patterns.get(name, []):
            match = re.search(pattern, raw_html, flags=re.I)
            if match:
                return clean_text(match.group(1))
        if name == 'product_id':
            candidate = getattr(content, 'source_product_key', None)
            if candidate and str(candidate).isdigit():
                return str(candidate)
        if name == 'product_code':
            candidate = getattr(content, 'product_code', None)
            if candidate:
                return str(candidate)
        return None

    def fetch_delivery(self, raw_html: str, content: Any, location: LocationConfig | None = None) -> DeliveryInfo:
        selected = self._require_location(location)
        product_id = self._identifier(raw_html, content, 'product_id')
        product_code = self._identifier(raw_html, content, 'product_code') or product_id or ''
        if not product_id:
            raise LocationMismatchError('product id was not present; refusing to infer delivery endpoint parameters')
        dropship_match = re.search(r'document\.isDropship\s*=\s*(true|false)', raw_html, flags=re.I)
        is_drop_ship = dropship_match.group(1).lower() if dropship_match else 'false'
        query = urlencode({
            'productId': product_id,
            'productCode': product_code,
            'isTowPrice': 'false',
            'priceType': 0,
            'isDropShip': is_drop_ship,
            'isActiveOption2': 'false',
        })
        endpoint = self.base_url + '/Product/DeliveryDateTimeV4?' + query
        response = self.client.get(endpoint, headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json,text/plain,*/*'})
        delivery = parse_delivery_response(response.body)
        evidence = delivery.returned_location
        if not evidence or not location_matches(asdict(selected), evidence, require_ward=True):
            raise LocationMismatchError(
                f'delivery location mismatch for {selected.code}: requested {selected.province_id}/{selected.ward_id}; '
                f'returned {evidence}'
            )
        return delivery

    def fetch_product(self, url: str, category_code: str, location: LocationConfig | None = None) -> ParsedPage:
        selected = self._require_location(location)
        response = self.client.get(url)
        content = parse_product_page(response.text, url, category_code)
        evidence = content.source_location.get('evidence', {})
        # Product HTML normally contains province evidence even when delivery
        # has not been loaded.  A missing or different province is unsafe.
        if not evidence or not location_matches(asdict(selected), evidence, require_ward=False):
            raise LocationMismatchError(
                f'product page location mismatch for {selected.code}: requested {selected.province_id}, returned {evidence}'
            )
        delivery = self.fetch_delivery(response.text, content, selected)
        location_data = content.source_location
        snapshot = LocationSnapshot(
            sale_price=location_data.get('sale_price'),
            list_price=location_data.get('list_price'),
            promotion=location_data.get('promotion') or {},
            stock_status=delivery.status if delivery.status != 'unknown' else content.stock_status,
            stock_raw=content.stock_raw or delivery.raw_text,
            delivery=delivery,
            returned_location=delivery.returned_location,
        )
        return ParsedPage(content=content, location_snapshot=snapshot)

    def fetch_common(self, url: str, category_code: str) -> tuple[Any, HTTPResponse]:
        response = self.client.get(url)
        try:
            content = parse_product_page(response.text, url, category_code)
        except Exception as exc:
            # Preserve transport evidence even when parsing fails after a
            # successful response. The crawler persists only whitelisted
            # metadata from this response; headers/body are never serialized.
            setattr(exc, "http_response", response)
            raise
        return content, response
