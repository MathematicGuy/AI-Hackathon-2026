from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
import unicodedata
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


_SPACE_RE = re.compile(r"\s+")
_PRICE_RE = re.compile(r"(?<!\d)(\d[\d\s.,]*)(?!\d)")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    value = html_lib.unescape(str(value)).replace("\xa0", " ")
    return _SPACE_RE.sub(" ", value).strip()


def slug_text(value: str) -> str:
    """Accent-insensitive comparison used only for matching evidence."""
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFD", value)
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def canonical_url(url: str, base_url: str = "https://www.dienmayxanh.com") -> str:
    """Normalize product URLs without guessing product identity.

    DMX category cards append tracking query strings such as
    ``utm_flashsale=1``.  Sitemap URLs are already canonical; dropping query
    and fragment is safe for the product paths observed during reconnaissance.
    """

    absolute = urljoin(base_url.rstrip("/") + "/", url.strip())
    parts = urlsplit(absolute)
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    if host == "dienmayxanh.com":
        host = "www.dienmayxanh.com"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = "/" + path.strip("/").lower()
    # Keep no query/fragment: observed product query parameters are tracking.
    return urlunsplit((scheme, host, path, "", ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()


def parse_price(value: Any) -> Optional[int]:
    """Parse a VND amount from DMX/Vietnamese text.

    Examples: ``21.090.000₫``, ``23990000.0`` and ``12,5 triệu``.  VND is
    stored as an integer number of đồng; floating point is never used.
    """

    if value is None:
        return None
    text = clean_text(value).lower()
    if not text or any(token in text for token in ("liên hệ", "contact")):
        return None
    multiplier = 1
    if "tỷ" in text or "ty" in text:
        multiplier = 1_000_000_000
    elif "triệu" in text or "trieu" in text or re.search(r"\btr\b", text):
        multiplier = 1_000_000
    elif re.search(r"(?:\d[\d.,]*)\s*m\b", text):
        multiplier = 1_000_000
    elif re.search(r"(?:\d[\d.,]*)\s*k\b", text):
        multiplier = 1_000

    # Remove currency words but retain separators and a possible decimal.
    text = re.sub(r"(?:₫|đ|vnd|vnđ|usd|\$)", " ", text)
    match = _PRICE_RE.search(text)
    if not match:
        return None
    token = match.group(1).replace(" ", "")
    if not token:
        return None

    # A trailing .0 is emitted by DMX data attributes, not a fractional đồng.
    if re.fullmatch(r"\d+\.0+", token):
        number = float(token)
    else:
        dots = token.count(".")
        commas = token.count(",")
        if dots and commas:
            # Last separator is decimal only when it has 1–2 trailing digits;
            # otherwise both are thousands separators.
            last = max(token.rfind("."), token.rfind(","))
            tail = token[last + 1 :]
            if len(tail) in (1, 2):
                number = float(token[:last].replace(".", "").replace(",", "") + "." + tail)
            else:
                number = float(token.replace(".", "").replace(",", ""))
        elif dots or commas:
            sep = "." if dots else ","
            pieces = token.split(sep)
            if len(pieces) > 2 or (len(pieces) == 2 and len(pieces[-1]) == 3):
                number = float("".join(pieces))
            elif len(pieces) == 2 and len(pieces[-1]) in (1, 2):
                # Decimal notation, mostly useful for ``12,5 triệu``.
                number = float(pieces[0] + "." + pieces[1])
            else:
                number = float("".join(pieces))
        else:
            number = float(token)
    return int(round(number * multiplier))


def parse_percent(value: Any) -> Optional[float]:
    if value is None:
        return None
    match = re.search(r"-?\s*(\d+(?:[.,]\d+)?)\s*%", clean_text(value))
    return float(match.group(1).replace(",", ".")) if match else None


def parse_rating(value: Any) -> Optional[float]:
    if value is None:
        return None
    match = re.search(r"(?<!\d)([0-5](?:[.,]\d{1,2})?)(?!\d)", clean_text(value))
    if not match:
        return None
    number = float(match.group(1).replace(",", "."))
    return number if 0 <= number <= 5 else None


def parse_sold_count(value: Any) -> Optional[int]:
    """Parse the abbreviated ``Đã bán 4,4k`` notation used by cards."""

    if value is None:
        return None
    text = clean_text(value).lower().replace("đã bán", "").strip()
    text = text.replace(" ", "")
    if not text:
        return None
    multiplier = 1
    if "triệu" in text or "trieu" in text:
        multiplier = 1_000_000
        text = re.sub(r"triệu|trieu", "", text)
    elif text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    text = re.sub(r"[^0-9.,]", "", text)
    if not text:
        return None
    if "," in text and "." in text:
        last = max(text.rfind(","), text.rfind("."))
        tail = text[last + 1 :]
        number = float(text[:last].replace(",", "").replace(".", "") + "." + tail)
    elif "," in text or "." in text:
        sep = "," if "," in text else "."
        parts = text.split(sep)
        if len(parts) == 2 and len(parts[1]) <= 2:
            number = float(parts[0] + "." + parts[1])
        else:
            number = float("".join(parts))
    else:
        number = float(text)
    return int(round(number * multiplier))


def parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    match = re.search(r"\d[\d.,]*", clean_text(value))
    if not match:
        return None
    return parse_price(match.group(0))


def fingerprint(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        value = {str(k): value[k] for k in sorted(value)}
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def extract_model(name: str, sku: Optional[str] = None) -> Optional[str]:
    name = clean_text(name)
    # Common DMX form: ``Brand ... - MODEL (specs...)``.
    match = re.search(r"\s[-–]\s*([A-Za-z0-9][A-Za-z0-9._/+-]{3,})\b", name)
    if match:
        candidate = match.group(1).strip(".,")
        if candidate.lower() not in {"inch", "gb", "tb"}:
            return candidate
    # Prefer an alphanumeric token containing a digit (QA55QN80F,
    # GR-RS600WI-PMV) over generic technology words such as QLED or AI.
    generic = {"QLED", "OLED", "LED", "SMART", "TIVI", "TV", "AI", "INVERTER", "ULTRA"}
    compound_candidates = re.findall(
        r"\b((?=[A-Z0-9()/_-]*[A-Z])(?=[A-Z0-9()/_-]*\d)[A-Z0-9]{2,}(?:[-_/][A-Z0-9()]+)+)\b",
        name.upper(),
    )
    for candidate in compound_candidates:
        if candidate not in generic:
            return candidate
    candidates = re.findall(
        r"\b((?=[A-Z0-9/_-]*[A-Z])(?=[A-Z0-9/_-]*\d)[A-Z0-9]{3,}(?:[-_/][A-Z0-9]+)*)\b",
        name.upper(),
    )
    for candidate in candidates:
        if candidate not in generic:
            return candidate
    for candidate in candidates:
        if candidate not in generic and candidate not in {"INCH", "GB", "TB"}:
            return candidate
    fallback = clean_text(sku)
    return fallback if fallback and not fallback.isdigit() else None


def stock_status(text: Any, availability: Any = None) -> tuple[str, str]:
    raw = clean_text(text)
    low = slug_text(raw)
    av = clean_text(availability).lower()
    if "ngung kinh doanh" in low or "het hang" in low or "outofstock" in av:
        return "out_of_stock", raw
    if "preorder" in av or "dat truoc" in low:
        return "preorder", raw
    if "in stock" in av or "instock" in av or "con hang" in low or "mua ngay" in low:
        return "in_stock", raw
    if "sap het" in low or "limited" in av:
        return "limited", raw
    return "unknown", raw


def location_matches(requested: Mapping[str, Any], evidence: Mapping[str, Any], require_ward: bool = False) -> bool:
    """Strictly compare requested and returned DMX location evidence."""

    try:
        req_province = int(requested.get("province_id", 0) or 0)
        got_province = int(evidence.get("province_id", 0) or 0)
    except (TypeError, ValueError):
        return False
    if req_province <= 0 or got_province != req_province:
        return False
    if require_ward:
        try:
            req_ward = int(requested.get("ward_id", 0) or 0)
            got_ward = int(evidence.get("ward_id", 0) or 0)
        except (TypeError, ValueError):
            return False
        if req_ward <= 0 or got_ward != req_ward:
            return False
    # If text is supplied, require it to contain a configured alias/name.  A
    # numeric ID remains authoritative; text can be an administrative alias.
    text = slug_text(" ".join(str(evidence.get(k, "")) for k in ("province_name", "location_text")))
    aliases = [requested.get("name", ""), requested.get("province_name", "")]
    aliases.extend(requested.get("aliases", ()) or ())
    aliases = [slug_text(a) for a in aliases if a]
    if text and aliases and not any(alias and alias in text for alias in aliases):
        return False
    return True


def canonical_product_key(url: str, source_product_key: Optional[str] = None) -> str:
    """A deterministic dedupe key; never merge by name/model."""
    return f"dmx:id:{source_product_key}" if source_product_key else f"dmx:url:{url_hash(url)}"


def parse_cookie_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        decoded = __import__("urllib.parse", fromlist=["unquote"]).unquote(value)
        data = json.loads(decoded)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {}


def is_captcha_or_challenge(body: str, headers: Mapping[str, str] | None = None) -> bool:
    """Detect an actual access challenge, not a passive reCAPTCHA library.

    DMX pages can load ``recaptcha/api.js`` for checkout/telemetry even when
    the product page is normal.  Script source alone is therefore not proof
    of a challenge.  We strip script/style blocks and inspect visible text,
    form/widget markers, and explicit challenge response headers.
    """
    raw = body or ""
    header_text = " ".join(f"{k}:{v}" for k, v in (headers or {}).items()).lower()
    if re.search(r"(?:cf-mitigated|x-captcha|x-challenge|challenge-platform|cf-chl-|captcha-required)\s*[:=]", header_text):
        return True
    if re.search(r"access\s*denied|verify\s+you\s+are\s+human|enable\s+javascript\s+and\s+cookies|challenge-platform|cf-chl-", raw, flags=re.I):
        return True
    markup = re.sub(r"<script\b[^>]*>.*?</script\s*>|<style\b[^>]*>.*?</style\s*>", " ", raw, flags=re.I | re.S)
    markup = re.sub(r"<!--.*?-->", " ", markup, flags=re.S)
    # A visible widget/class is meaningful; hidden response inputs commonly
    # exist on every normal DMX page and must not trigger a false block.
    widget_markup = re.sub(r"<(?:input|textarea)\b[^>]*>", " ", markup, flags=re.I)
    if re.search(r"(?:class|id)=[\"'][^\"']*(?:captcha|recaptcha)[^\"']*[\"']", widget_markup, flags=re.I):
        return True
    visible_text = re.sub(r"<[^>]+>", " ", markup)
    if re.search(r"(?:captcha|recaptcha)", visible_text, flags=re.I):
        return True
    return False


def safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def first_nonempty(values: Iterable[Any]) -> Any:
    for value in values:
        if value is not None and clean_text(value):
            return value
    return None
