from __future__ import annotations

import unittest

from dmx_crawler.http import HTTPClientError, RateLimiter, RespectfulClient, RetryableHTTPError


class FakeCompressedResponse:
    status = 200
    headers = {"content-encoding": "gzip", "content-type": "text/html"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return b"not-a-valid-gzip-stream"

    def geturl(self) -> str:
        return "https://example.test/laptop/redirected"


class FakeOpener:
    def open(self, request, timeout=None):
        return FakeCompressedResponse()


class HTTPPolicyTests(unittest.TestCase):
    def test_observed_robots_disallow_is_rejected_before_network(self):
        client = RespectfulClient('test', min_interval=0)
        with self.assertRaises(HTTPClientError):
            client.get('https://www.dienmayxanh.com/support/private')

    def test_invalid_compressed_200_preserves_status_url_and_attempt_count(self):
        client = RespectfulClient("test", min_interval=0, max_attempts=1)
        client.opener = FakeOpener()
        with self.assertRaises(RetryableHTTPError) as caught:
            client.get("https://example.test/laptop/original")
        self.assertEqual(caught.exception.http_status, 200)
        self.assertEqual(caught.exception.response_url, "https://example.test/laptop/redirected")
        self.assertEqual(caught.exception.attempts, 1)
        self.assertIsNotNone(caught.exception.elapsed_ms)

    def test_rate_limiter_can_be_shared_by_clients(self):
        limiter = RateLimiter(0)
        a = RespectfulClient('a', rate_limiter=limiter)
        b = RespectfulClient('b', rate_limiter=limiter)
        self.assertIs(a.rate_limiter, b.rate_limiter)


if __name__ == '__main__':
    unittest.main()
