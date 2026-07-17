from __future__ import annotations

import gzip
import http.cookiejar
import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Mapping, Optional

from .utils import is_captcha_or_challenge


class HTTPClientError(RuntimeError):
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        response_url: str | None = None,
        elapsed_ms: int | None = None,
        attempts: int | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.response_url = response_url
        self.elapsed_ms = elapsed_ms
        self.attempts = attempts
        self.retry_after = retry_after


class BlockedError(HTTPClientError):
    """The site returned a challenge/CAPTCHA/explicit access block."""


class RetryableHTTPError(HTTPClientError):
    retryable = True


class LocationMismatchError(HTTPClientError):
    retryable = False


@dataclass
class HTTPResponse:
    status: int
    url: str
    headers: dict[str, str]
    body: bytes
    elapsed_ms: int
    attempts: int = 1

    @property
    def text(self) -> str:
        charset = "utf-8"
        content_type = self.headers.get("content-type", "")
        if "charset=" in content_type:
            charset = content_type.split("charset=", 1)[1].split(";", 1)[0].strip()
        return self.body.decode(charset or "utf-8", errors="replace")


class RateLimiter:
    """Host-wide minimum interval and explicit backoff, safe to share."""

    def __init__(self, min_interval: float = 5.0):
        self.min_interval = max(0.0, float(min_interval))
        self._last = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            remaining = self.min_interval - (now - self._last)
            if remaining > 0:
                time.sleep(remaining)
            self._last = time.monotonic()

    def backoff(self, seconds: float) -> None:
        with self._lock:
            self._last = max(self._last, time.monotonic() + max(0.0, seconds))


def _retry_after(headers: Mapping[str, str]) -> Optional[float]:
    value = headers.get("retry-after") or headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, (parsedate_to_datetime(value).timestamp() - time.time()))
        except (TypeError, ValueError, OverflowError):
            return None


def _decode_content(body: bytes, headers: Mapping[str, str]) -> bytes:
    """Decode only encodings explicitly advertised by the HTTP response."""
    encoding = (headers.get("content-encoding") or headers.get("Content-Encoding") or "").lower()
    try:
        if "gzip" in encoding:
            return gzip.decompress(body)
        if "deflate" in encoding:
            try:
                return zlib.decompress(body)
            except zlib.error:
                return zlib.decompress(body, -zlib.MAX_WBITS)
    except (OSError, zlib.error):
        # Let the caller retry a truncated/invalid response rather than
        # treating compressed bytes as valid product HTML.
        raise RetryableHTTPError("invalid compressed HTTP response")
    return body


class RespectfulClient:
    """Synchronous HTTP client with one independent CookieJar per instance."""

    RETRY_STATUSES = {408, 425, 429, 500, 502, 503, 504}
    # Paths observed in DMX robots.txt; product/location endpoints used by
    # this project are outside these prefixes.
    ROBOTS_DISALLOWED_PREFIXES = ('/bin/', '/cms/', '/zzz/', '/price/', '/tracking/', '/aj/', '/support/')

    def __init__(
        self,
        user_agent: str,
        min_interval: float = 5.0,
        timeout: float = 30.0,
        max_attempts: int = 3,
        rng: random.Random | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_attempts = max(1, int(max_attempts))
        self.rate_limiter = rate_limiter or RateLimiter(min_interval)
        self.rng = rng or random.Random()
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.blocked = False

    def _request(self, method: str, url: str, data: bytes | None = None, headers: Mapping[str, str] | None = None) -> HTTPResponse:
        if self.blocked:
            raise BlockedError("client paused after an access challenge")
        path = urllib.parse.urlsplit(url).path.lower()
        if any(path.startswith(prefix) for prefix in self.ROBOTS_DISALLOWED_PREFIXES):
            raise HTTPClientError(f"URL is disallowed by observed robots.txt: {path}")
        request_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.5",
            "Accept-Language": "vi,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
        }
        request_headers.update(headers or {})
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            self.rate_limiter.wait()
            started = time.monotonic()
            req = urllib.request.Request(url, data=data, headers=request_headers, method=method.upper())
            try:
                with self.opener.open(req, timeout=self.timeout) as response:
                    raw_body = response.read()
                    response_headers = {k.lower(): v for k, v in response.headers.items()}
                    try:
                        body = _decode_content(raw_body, response_headers)
                    except RetryableHTTPError as decode_error:
                        raise RetryableHTTPError(
                            str(decode_error),
                            http_status=int(response.status),
                            response_url=response.geturl(),
                            elapsed_ms=int((time.monotonic() - started) * 1000),
                            attempts=attempt,
                            retry_after=_retry_after(response_headers),
                        ) from decode_error
                    result = HTTPResponse(int(response.status), response.geturl(), response_headers, body, int((time.monotonic() - started) * 1000), attempt)
                    if is_captcha_or_challenge(result.text, result.headers) or result.status in {401, 403}:
                        self.blocked = True
                        raise BlockedError(
                            f"access challenge or HTTP {result.status} from {url}",
                            http_status=result.status,
                            response_url=result.url,
                            elapsed_ms=result.elapsed_ms,
                            attempts=attempt,
                        )
                    if result.status in self.RETRY_STATUSES:
                        raise RetryableHTTPError(
                            f"HTTP {result.status} from {url}",
                            http_status=result.status,
                            response_url=result.url,
                            elapsed_ms=result.elapsed_ms,
                            attempts=attempt,
                            retry_after=_retry_after(result.headers),
                        )
                    return result
            except urllib.error.HTTPError as error:
                raw_body = error.read() if hasattr(error, "read") else b""
                response_headers = {k.lower(): v for k, v in error.headers.items()} if error.headers else {}
                try:
                    body = _decode_content(raw_body, response_headers)
                except RetryableHTTPError as decode_error:
                    last_error = decode_error
                    body = raw_body
                status = int(error.code)
                response_url = error.geturl() if hasattr(error, "geturl") else url
                elapsed_ms = int((time.monotonic() - started) * 1000)
                retry_after = _retry_after(response_headers)
                if is_captcha_or_challenge(body.decode("utf-8", errors="replace"), response_headers) or status in {401, 403}:
                    self.blocked = True
                    raise BlockedError(
                        f"access challenge or HTTP {status} from {url}",
                        http_status=status,
                        response_url=response_url,
                        elapsed_ms=elapsed_ms,
                        attempts=attempt,
                        retry_after=retry_after,
                    ) from error
                if status not in self.RETRY_STATUSES:
                    raise HTTPClientError(
                        f"HTTP {status} from {url}",
                        http_status=status,
                        response_url=response_url,
                        elapsed_ms=elapsed_ms,
                        attempts=attempt,
                        retry_after=retry_after,
                    ) from error
                last_error = RetryableHTTPError(
                    f"HTTP {status} from {url}",
                    http_status=status,
                    response_url=response_url,
                    elapsed_ms=elapsed_ms,
                    attempts=attempt,
                    retry_after=retry_after,
                )
                self.rate_limiter.backoff(retry_after if retry_after is not None else min(60.0, 2 ** (attempt - 1) + self.rng.random()))
            except BlockedError:
                raise
            except (urllib.error.URLError, TimeoutError, OSError, RetryableHTTPError) as error:
                last_error = error
                if attempt >= self.max_attempts:
                    break
                self.rate_limiter.backoff(min(60.0, 2 ** (attempt - 1) + self.rng.random()))
        details = {
            "http_status": getattr(last_error, "http_status", None),
            "response_url": getattr(last_error, "response_url", None),
            "elapsed_ms": getattr(last_error, "elapsed_ms", None),
            "attempts": getattr(last_error, "attempts", None) or self.max_attempts,
            "retry_after": getattr(last_error, "retry_after", None),
        }
        raise RetryableHTTPError(
            f"request failed after {self.max_attempts} attempts: {url}",
            **details,
        ) from last_error

    def get(self, url: str, headers: Mapping[str, str] | None = None) -> HTTPResponse:
        return self._request("GET", url, headers=headers)

    def post_form(self, url: str, values: Mapping[str, object], headers: Mapping[str, str] | None = None) -> HTTPResponse:
        data = urllib.parse.urlencode(values, doseq=True).encode("utf-8")
        post_headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest"}
        post_headers.update(headers or {})
        return self._request("POST", url, data=data, headers=post_headers)

    def cookies(self) -> dict[str, str]:
        return {cookie.name: cookie.value for cookie in self.jar}

    def close(self) -> None:
        # urllib's opener has no persistent socket pool requiring close, but a
        # method makes lifecycle ownership explicit for the service/CLI.
        self.blocked = True


def json_body(response: HTTPResponse) -> dict:
    try:
        value = json.loads(response.text)
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {}
