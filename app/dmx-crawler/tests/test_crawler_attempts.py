from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dmx_crawler.adapters.dmx import DMXAdapter
from dmx_crawler.config import Settings
from dmx_crawler.crawler import Crawler
from dmx_crawler.db import Database
from dmx_crawler.http import BlockedError, HTTPResponse
from dmx_crawler.models import CategoryConfig
from dmx_crawler.parsers import parse_product_page


FIXTURE = Path(__file__).parent / "fixtures" / "specs_laptop_complete.html"


class FakeClient:
    def close(self) -> None:
        pass


class StaticResponseClient(FakeClient):
    def __init__(self, response: HTTPResponse):
        self.response = response

    def get(self, url: str) -> HTTPResponse:
        return self.response


def fake_response(url: str, *, status: int = 200, attempts: int = 2) -> HTTPResponse:
    raw = FIXTURE.read_text(encoding="utf-8")
    return HTTPResponse(
        status=status,
        url=url,
        headers={"content-type": "text/html; charset=utf-8"},
        body=raw.encode("utf-8"),
        elapsed_ms=23,
        attempts=attempts,
    )


class FakeAdapter:
    def __init__(self, settings: Settings, client: FakeClient):
        self.settings = settings
        self.client = client

    def fetch_common(self, url: str, category_code: str):
        raw = FIXTURE.read_text(encoding="utf-8")
        content = parse_product_page(raw, url, category_code)
        response = fake_response(url)
        return content, response


class BlockedAdapter:
    def __init__(self, settings: Settings, client: FakeClient):
        self.settings = settings
        self.client = client

    def fetch_common(self, url: str, category_code: str):
        raise BlockedError(
            "HTTP 403 test block",
            http_status=403,
            response_url=url,
            elapsed_ms=11,
            attempts=1,
        )


class CrawlerAttemptMetadataTests(unittest.TestCase):
    def test_common_crawl_persists_actual_response_and_parser_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(str(Path(tempdir) / "crawler.db"))
            settings = Settings(database_url=str(Path(tempdir) / "crawler.db"), min_request_interval_seconds=0)
            crawler = Crawler(
                settings=settings,
                db=db,
                categories=[
                    CategoryConfig(
                        code="laptop",
                        name="Laptop",
                        url="https://example.test/laptop",
                        path_prefix="/laptop/",
                    )
                ],
                locations=[],
            )
            try:
                with patch("dmx_crawler.crawler.DMXAdapter", FakeAdapter), patch.object(
                    crawler, "_client", return_value=FakeClient()
                ):
                    stats = crawler.crawl_url("https://example.test/laptop/fixture", ["laptop"])
                self.assertEqual((stats.succeeded, stats.failed, stats.blocked, stats.discovered), (1, 0, 0, 0))
                row = db.fetchone("SELECT * FROM crawl_attempts")
                self.assertEqual((row["http_status"], row["latency_ms"], row["outcome"]), (200, 23, "success"))
                metadata = json.loads(row["response_metadata_json"])
                self.assertEqual(metadata["http"]["transport_attempt_count"], 2)
                self.assertEqual(metadata["http"]["content_type"], "text/html; charset=utf-8")
                self.assertEqual(metadata["specifications"]["group_count"], 3)
                self.assertEqual(metadata["specifications"]["total_item_count"], 6)
                self.assertEqual(metadata["specifications"]["empty_groups"], [])
                self.assertEqual(metadata["specifications"]["warnings"], [])
                merge = metadata["specifications"]["merge_diagnostics"]
                self.assertEqual(
                    (merge["merged_count"], merge["added_count"], merge["ambiguous_count"]),
                    (2, 2, 0),
                )
                serialized = json.dumps(metadata).casefold()
                self.assertNotIn("cookie", serialized)
                self.assertNotIn("authorization", serialized)
            finally:
                db.close()

    def test_adapter_preserves_response_when_parse_fails(self) -> None:
        url = "https://example.test/laptop/parse-failure"
        response = fake_response(url, attempts=1)
        adapter = DMXAdapter(Settings(min_request_interval_seconds=0), StaticResponseClient(response))
        with patch("dmx_crawler.adapters.dmx.parse_product_page", side_effect=ValueError("bad product markup")):
            with self.assertRaises(ValueError) as caught:
                adapter.fetch_common(url, "laptop")
        self.assertIs(caught.exception.http_response, response)

    def test_parse_failure_after_http_200_persists_actual_status(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            url = "https://example.test/laptop/parse-failure"
            db = Database(str(Path(tempdir) / "parse-failure.db"))
            crawler = Crawler(
                settings=Settings(database_url=str(Path(tempdir) / "parse-failure.db"), min_request_interval_seconds=0),
                db=db,
                categories=[CategoryConfig("laptop", "Laptop", "https://example.test/laptop", "/laptop/")],
                locations=[],
            )
            response = fake_response(url, attempts=1)
            try:
                with patch.object(crawler, "_client", return_value=StaticResponseClient(response)), patch(
                    "dmx_crawler.adapters.dmx.parse_product_page", side_effect=ValueError("bad product markup")
                ):
                    stats = crawler.crawl_url(url, ["laptop"])
                self.assertEqual((stats.failed, stats.blocked), (1, 0))
                attempt = db.fetchone("SELECT * FROM crawl_attempts")
                self.assertEqual((attempt["http_status"], attempt["latency_ms"], attempt["outcome"]), (200, 23, "error"))
                metadata = json.loads(attempt["response_metadata_json"])
                self.assertEqual(metadata["http"]["transport_attempt_count"], 1)
                self.assertEqual(metadata["http"]["response_bytes"], len(response.body))
            finally:
                db.close()

    def test_persistence_failure_after_http_200_keeps_status_and_spec_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(str(Path(tempdir) / "persistence-failure.db"))
            crawler = Crawler(
                settings=Settings(database_url=str(Path(tempdir) / "persistence-failure.db"), min_request_interval_seconds=0),
                db=db,
                categories=[CategoryConfig("laptop", "Laptop", "https://example.test/laptop", "/laptop/")],
                locations=[],
            )
            try:
                with patch("dmx_crawler.crawler.DMXAdapter", FakeAdapter), patch.object(
                    crawler, "_client", return_value=FakeClient()
                ), patch.object(db, "record_content", side_effect=RuntimeError("write failed")):
                    stats = crawler.crawl_url("https://example.test/laptop/persistence-failure", ["laptop"])
                self.assertEqual((stats.failed, stats.blocked), (1, 0))
                attempt = db.fetchone("SELECT * FROM crawl_attempts")
                self.assertEqual((attempt["http_status"], attempt["latency_ms"], attempt["outcome"]), (200, 23, "error"))
                metadata = json.loads(attempt["response_metadata_json"])
                self.assertEqual(metadata["specifications"]["group_count"], 3)
                self.assertEqual(metadata["specifications"]["total_item_count"], 6)
                self.assertEqual(metadata["specifications"]["warnings"], [])
            finally:
                db.close()

    def test_blocked_response_status_is_persisted_on_attempt_and_error(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(str(Path(tempdir) / "blocked.db"))
            crawler = Crawler(
                settings=Settings(database_url=str(Path(tempdir) / "blocked.db"), min_request_interval_seconds=0),
                db=db,
                categories=[CategoryConfig("laptop", "Laptop", "https://example.test/laptop", "/laptop/")],
                locations=[],
            )
            try:
                with patch("dmx_crawler.crawler.DMXAdapter", BlockedAdapter), patch.object(
                    crawler, "_client", return_value=FakeClient()
                ):
                    stats = crawler.crawl_url("https://example.test/laptop/blocked", ["laptop"])
                self.assertEqual((stats.blocked, stats.failed), (1, 0))
                attempt = db.fetchone("SELECT * FROM crawl_attempts")
                error = db.fetchone("SELECT * FROM crawl_errors")
                self.assertEqual((attempt["http_status"], attempt["latency_ms"], attempt["outcome"]), (403, 11, "error"))
                self.assertEqual((error["http_status"], error["attempt_id"]), (403, attempt["id"]))
                metadata = json.loads(attempt["response_metadata_json"])
                self.assertEqual(metadata["http"]["transport_attempt_count"], 1)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
