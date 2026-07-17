from __future__ import annotations

import json
import re
import unicodedata
import warnings
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.parse import urljoin

from .html import Node, attr, node_text, parse_html
from .models import (
    DeliveryInfo,
    LocationConfig,
    LocationSnapshot,
    ProductContent,
    ProductLink,
    SpecificationParseResult,
)
from .utils import (
    canonical_url,
    clean_text,
    extract_model,
    first_nonempty,
    parse_int,
    parse_percent,
    parse_price,
    parse_rating,
    parse_sold_count,
    slug_text,
    stock_status,
)


def _descendant(node: Node, selector: str) -> Node | None:
    return node.first(selector)


def _text(node: Node | None, selector: str | None = None) -> str:
    if selector:
        node = node.first(selector) if node else None
    return node_text(node)


def _attribute(node: Node | None, *names: str) -> str | None:
    for name in names:
        value = attr(node, name)
        if value:
            return value
    return None


def _json_ld(document: Node) -> dict[str, Any]:
    """Return one merged Product JSON-LD object, including ``@graph`` forms."""

    products: list[dict[str, Any]] = []

    def product_nodes(value: Any) -> Iterable[dict[str, Any]]:
        if isinstance(value, list):
            for item in value:
                yield from product_nodes(item)
            return
        if not isinstance(value, Mapping):
            return
        raw_type = value.get("@type")
        types = raw_type if isinstance(raw_type, list) else [raw_type]
        normalized_types = {slug_text(str(item)).replace(" ", "") for item in types if item}
        is_product_type = any(item == "product" or item.endswith("product") for item in normalized_types)
        if is_product_type or "additionalProperty" in value or (
            "offers" in value and any(key in value for key in ("name", "sku", "mpn", "additionalProperty"))
        ):
            yield dict(value)
        for key, nested in value.items():
            if key == "@context":
                continue
            if isinstance(nested, (Mapping, list)):
                yield from product_nodes(nested)

    seen_scripts: set[int] = set()
    for script in document.select("script#productld") + document.select('script[type="application/ld+json"]'):
        if id(script) in seen_scripts:
            continue
        seen_scripts.add(id(script))
        raw = node_text(script).strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError, json.JSONDecodeError):
            match = re.search(r"[\[{].*[\]}]", raw, flags=re.S)
            if not match:
                continue
            try:
                payload = json.loads(match.group(0))
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
        products.extend(product_nodes(payload))

    if not products:
        return {}
    merged = dict(products[0])
    additional: list[Any] = []
    for product in products:
        properties = product.get("additionalProperty")
        if isinstance(properties, list):
            additional.extend(properties)
        elif properties is not None:
            additional.append(properties)
        for key, value in product.items():
            if key != "additionalProperty" and key not in merged:
                merged[key] = value
    if additional:
        merged["additionalProperty"] = additional
    return merged


def _brand(value: Any) -> Optional[str]:
    if isinstance(value, Mapping):
        value = value.get("name")
    if isinstance(value, list):
        value = value[0] if value else None
    value = clean_text(value)
    return value or None


def _find_data_value(document: Node, attr_name: str, selectors: Iterable[str]) -> Optional[str]:
    for selector in selectors:
        for item in document.select(selector):
            value = attr(item, attr_name)
            if value:
                return value
    return None


def _parse_data_deli(raw_html: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    patterns = {
        "province_id": r"dataDeli\.ProvinceId\s*=\s*([0-9]+)",
        "district_id": r"dataDeli\.DistrictId\s*=\s*([0-9]+)",
        "ward_id": r"dataDeli\.WardId\s*=\s*([0-9]+)",
        "product_id": r"dataDeli\.ProductId\s*=\s*([0-9]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, raw_html)
        if match:
            result[key] = int(match.group(1))
    for key, pattern in {
        "province_name": r'dataDeli\.ProvinceName\s*=\s*["\']([^"\']*)',
        "district_name": r'dataDeli\.DistrictName\s*=\s*["\']([^"\']*)',
        "ward_name": r'dataDeli\.WardName\s*=\s*["\']([^"\']*)',
        "address": r'dataDeli\.Address\s*=\s*["\']([^"\']*)',
    }.items():
        match = re.search(pattern, raw_html)
        if match:
            result[key] = clean_text(match.group(1))
    return result


def parse_location_evidence(raw_html: str, document: Node | None = None) -> dict[str, Any]:
    document = document or parse_html(raw_html)
    result = _parse_data_deli(raw_html)
    location = document.first("#location-detail")
    if location:
        province = attr(location, "data-province")
        if province and province.isdigit():
            result.setdefault("province_id", int(province))
        result["location_text"] = node_text(location)
    affiliate = re.search(r'ProductsAffiliate\s*=\s*(\{.*?\})\s*;', raw_html, flags=re.S)
    if affiliate:
        try:
            data = json.loads(affiliate.group(1))
            if isinstance(data, dict) and data.get("provinceId") is not None:
                result.setdefault("province_id", int(data["provinceId"]))
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
    return result


_SPEC_ROOT_MARKERS = (
    "box specifi",
    "specification",
    "specifications",
    "technical spec",
    "product spec",
    "product specs",
    "specs",
    "parameter",
    "thong so",
    "thongso",
)
_SPEC_SECTION_TITLES = (
    "thong so ky thuat",
    "thong tin ky thuat",
    "technical specifications",
    "product specifications",
    "specs",
    "specifications",
)
_SPEC_CONTAINER_KEYS = {
    "additionalproperty",
    "attributes",
    "parameters",
    "parametergroups",
    "properties",
    "specgroups",
    "specificationgroups",
    "specification",
    "specifications",
    "specs",
    "rows",
    "entries",
    "groups",
    "groupedspecs",
    "technicalspecifications",
    "thongsokythuat",
}
_GROUP_NAME_KEYS = ("group", "groupName", "section", "sectionName", "category", "title", "name")
_GROUP_ITEM_KEYS = ("items", "attributes", "parameters", "properties", "specifications", "specs", "values", "rows", "entries", "children")
_ITEM_LABEL_KEYS = ("label", "name", "key", "title", "propertyName", "displayName", "propertyID")
_ITEM_VALUE_KEYS = ("value", "values", "text", "displayValue", "rawValue", "content", "valueReference", "valueNumber", "valueBoolean")


def _compact_key(value: Any) -> str:
    return slug_text(clean_text(value)).replace(" ", "")


def _mapping_get(value: Mapping[str, Any], names: Sequence[str]) -> Any:
    lookup = {_compact_key(key): item for key, item in value.items()}
    for name in names:
        key = _compact_key(name)
        if key in lookup:
            return lookup[key]
    return None


def _raw_node_text(node: Node | None) -> str:
    """Return visible source text before whitespace normalization.

    ``HTMLParser`` has already resolved character references, so exact source
    bytes cannot be reconstructed.  Whitespace and all visible descendant text
    are nevertheless retained here, while ``value`` is normalized separately.
    """

    return node.text_content().strip() if node else ""


def _json_raw_text(value: Any) -> str:
    if isinstance(value, (Mapping, list, tuple)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
    return "" if value is None else str(value)


def _json_value_text(value: Any) -> str:
    if isinstance(value, Mapping):
        nested = _mapping_get(value, ("text", "value", "displayValue", "name"))
        if nested is not None and nested is not value:
            return _json_value_text(nested)
        return clean_text(json.dumps(value, ensure_ascii=False, default=str))
    if isinstance(value, (list, tuple)):
        return "; ".join(part for part in (_json_value_text(item) for item in value) if part)
    raw = "" if value is None else str(value)
    if "<" in raw and ">" in raw:
        return node_text(parse_html(raw))
    return clean_text(raw)


def _normalized_merge_text(value: Any, *, strip_trailing_colon: bool = False) -> str:
    """Normalize source text for matching without changing persisted display text."""

    text = unicodedata.normalize("NFKC", clean_text(value))
    if strip_trailing_colon:
        text = re.sub(r"\s*[:：]+\s*$", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _normalized_label_key(value: Any) -> str:
    return _normalized_merge_text(value, strip_trailing_colon=True)


def _normalized_value_key(value: Any) -> str:
    return _normalized_merge_text(value)


def _clean_spec_label(value: Any) -> str:
    text = unicodedata.normalize("NFKC", clean_text(value))
    return re.sub(r"\s*[:：]+\s*$", "", text).strip()


def _dom_value_only(raw_value: Any, raw_label: Any) -> str:
    """Remove a repeated DOM label and parser separators from a row value."""

    value = unicodedata.normalize("NFC", "" if raw_value is None else str(raw_value)).strip()
    label = _clean_spec_label(raw_label)
    if label:
        value = re.sub(
            rf"^\s*{re.escape(label)}\s*[:：]?[\s|]*",
            "",
            value,
            count=1,
            flags=re.IGNORECASE,
        )
    # Pipes here are parser-created separators between DOM value nodes, not
    # part of the specification value contract.
    return re.sub(r"\s*\|\s*", "\n", value).strip()


_TYPED_UNITS = {
    "%": "%",
    "b": "B",
    "kb": "KB",
    "mb": "MB",
    "gb": "GB",
    "tb": "TB",
    "hz": "Hz",
    "khz": "kHz",
    "mhz": "MHz",
    "ghz": "GHz",
    "w": "W",
    "kw": "kW",
    "wh": "Wh",
    "kwh": "kWh",
    "kwh/năm": "kWh/năm",
    "kwh/nam": "kWh/năm",
    "mm": "mm",
    "cm": "cm",
    "m": "m",
    "inch": "inch",
    "inches": "inch",
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "lít": "lít",
    "lit": "lít",
    "litre": "litre",
    "liter": "liter",
}


def _normalized_spec_value(raw_value: Any) -> dict[str, Any]:
    raw_text = _json_raw_text(raw_value)
    value_text = _json_value_text(raw_value)
    normalized_slug = slug_text(value_text)
    value_boolean: bool | None = None
    if normalized_slug in {"co", "yes", "true"}:
        value_boolean = True
    elif normalized_slug in {"khong", "no", "false"}:
        value_boolean = False

    value_number: int | float | None = None
    unit: str | None = None
    number_only = re.fullmatch(r"\s*([+-]?\d+(?:[.,]\d+)?)\s*", value_text)
    measurement = re.fullmatch(
        r"\s*([+-]?\d+(?:[.,]\d+)?)\s*([^\d\s,.;:()]+)\s*",
        value_text,
    )
    token: str | None = None
    if number_only:
        token = number_only.group(1)
    elif measurement:
        candidate_unit = _normalized_merge_text(measurement.group(2))
        canonical_unit = _TYPED_UNITS.get(candidate_unit)
        if canonical_unit:
            token = measurement.group(1)
            unit = canonical_unit
    if token is not None:
        try:
            parsed = float(token.replace(",", "."))
            value_number = int(parsed) if parsed.is_integer() else parsed
        except ValueError:
            value_number = None
            unit = None

    return {
        "value": value_text,
        "raw_value": raw_text,
        "value_text": value_text,
        "value_number": value_number,
        "value_boolean": value_boolean,
        "value_json": raw_value if isinstance(raw_value, (Mapping, list, tuple)) else {},
        "unit": unit,
    }


def _spec_item(label: Any, raw_value: Any, source: str) -> dict[str, Any] | None:
    raw_label = _json_raw_text(label)
    normalized_label = _clean_spec_label(re.sub(r"<[^>]+>", " ", raw_label))
    if source == "dom":
        raw_value = _dom_value_only(raw_value, raw_label)
    normalized = _normalized_spec_value(raw_value)
    if not normalized_label or not normalized["value"]:
        return None
    return {
        "group": "",
        "group_ordinal": 0,
        "label": normalized_label,
        "raw_label": raw_label,
        **normalized,
        "item_ordinal": 0,
        "ordinal": 0,
        "source": source,
        "sources": [source],
        "provenance": [source],
    }


def _node_marker_text(node: Node) -> str:
    return slug_text(
        " ".join(
            str(node.attrs.get(name, ""))
            for name in ("id", "class", "data-section", "data-component", "aria-label")
        )
    )


def _semantic_role_node(node: Node, roles: set[str]) -> Node | None:
    for candidate in node.descendants():
        role_words = set(slug_text(" ".join((candidate.attrs.get("class", ""), candidate.attrs.get("data-role", "")))).split())
        if roles & role_words or any(any(role in word for role in roles) for word in role_words):
            return candidate
    return None


def _semantic_role_nodes(node: Node, roles: set[str]) -> list[Node]:
    """Return every semantic value/label node in document order.

    Some publishers render a single specification row as several value chips
    (for example multiple supported ports). Using only ``first()`` would
    silently discard all but the first value, so the generic row strategy must
    retain the complete set.
    """

    result: list[Node] = []
    for candidate in node.descendants():
        role_words = set(
            slug_text(" ".join((candidate.attrs.get("class", ""), candidate.attrs.get("data-role", "")))).split()
        )
        if roles & role_words or any(any(role in word for role in roles) for word in role_words):
            result.append(candidate)
    return result


def _anonymous_dom_row_children(node: Node) -> list[Node]:
    """Recognize a simple two-column row without relying on CSS class names."""

    if node.tag not in {"div", "article", "p"}:
        return []
    marker = _node_marker_text(node)
    if any(word in marker.split() for word in ("group", "section", "accordion")):
        return []
    children = [child for child in node.children if child.tag != "#text"]
    if len(children) < 2:
        return []
    structural = {"h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table", "dl", "details", "summary", "section"}
    if any(child.tag in structural for child in children):
        return []
    if not _raw_node_text(children[0]) or not any(_raw_node_text(child) for child in children[1:]):
        return []
    # Nested tables/lists/accordions are containers, not anonymous rows.
    if any(descendant.tag in structural for child in children for descendant in child.descendants()):
        return []
    return children


def _looks_like_dom_row(node: Node) -> bool:
    if node.tag in {"li", "tr", "dt"}:
        if node.tag == "li" and any(child.tag == "li" for child in node.descendants()):
            # A specification value can itself be a list. Keep the outer row
            # when it has an explicit label; its descendant list items are
            # consumed as values rather than misclassified as separate specs.
            return bool(
                node.attrs.get("data-label")
                or node.attrs.get("data-name")
                or node.first("strong")
                or node.first("label")
                or _semantic_role_node(node, {"label", "name", "key", "term"})
            )
        return True
    if node.attrs.get("data-label") or node.attrs.get("data-name"):
        return True
    marker = _node_marker_text(node)
    if node.tag in {"div", "article", "p"} and any(
        phrase in marker for phrase in ("spec row", "spec item", "parameter item", "attribute row", "property row")
    ):
        if any(candidate is not node and _looks_like_dom_row(candidate) for candidate in node.descendants()):
            return False
        return True
    if node.tag in {"div", "article", "p"} and re.search(r"(?:^| )(?:row|item)(?: |$)", marker):
        if any(candidate is not node and _looks_like_dom_row(candidate) for candidate in node.descendants()):
            return False
        return True
    if node.tag in {"div", "article", "p"}:
        if "group" in marker or "section" in marker or "accordion" in marker:
            return False
        if _semantic_role_node(node, {"label", "name", "key", "term"}) and _semantic_role_node(
            node, {"value", "content", "detail", "description"}
        ):
            return True
        return bool(_anonymous_dom_row_children(node))
    return False


def _contains_dom_row(node: Node) -> bool:
    return any(_looks_like_dom_row(candidate) for candidate in node.descendants(include_self=True))


def _is_spec_section_title(value: str) -> bool:
    normalized = slug_text(value)
    return any(title in normalized for title in _SPEC_SECTION_TITLES)


def _spec_section_present(document: Node) -> bool:
    for node in document.descendants():
        if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6", "summary"} and _is_spec_section_title(node_text(node)):
            return True
        marker = _node_marker_text(node)
        if marker and any(phrase in marker for phrase in _SPEC_ROOT_MARKERS):
            return True
    return False


def _find_spec_roots(document: Node) -> list[Node]:
    candidates: list[Node] = []
    for node in document.descendants():
        marker = _node_marker_text(node)
        has_marker = any(phrase in marker for phrase in _SPEC_ROOT_MARKERS)
        if node.tag == "details":
            # A closed accordion has no viewport state in this static tree.
            # Any recognized row under a non-empty summary is enough evidence
            # to treat it as a specification group, including anonymous div
            # rows that have no CSS marker.
            structured_rows = bool(node_text(node.first("summary"))) and any(
                _looks_like_dom_row(candidate) for candidate in node.descendants()
            )
            has_marker = has_marker or _is_spec_section_title(node_text(node.first("summary"))) or structured_rows
        if has_marker and _contains_dom_row(node):
            candidates.append(node)

    # A semantic section heading is useful even when the publisher changes all
    # CSS classes.  Use its nearest parent that actually contains a row.
    for heading in document.descendants():
        if heading.tag not in {"h1", "h2", "h3", "h4", "h5", "h6", "summary"}:
            continue
        if not _is_spec_section_title(node_text(heading)):
            continue
        parent = heading.parent
        if parent is not None and _contains_dom_row(parent):
            candidates.append(parent)

    candidate_ids = {id(node) for node in candidates}
    roots: list[Node] = []
    seen: set[int] = set()
    for node in candidates:
        if id(node) in seen:
            continue
        ancestor = node.parent
        nested = False
        while ancestor is not None:
            if id(ancestor) in candidate_ids:
                nested = True
                break
            ancestor = ancestor.parent
        if not nested:
            roots.append(node)
            seen.add(id(node))
    # A common layout places the group heading beside a ``.box-specifi`` list
    # inside a neutral tab wrapper. Promote that list to the wrapper only when
    # a direct sibling heading supplies a real group name; this avoids turning
    # the entire document/body into a specification root.
    promoted: list[Node] = []
    for root in roots:
        if root.tag not in {"ul", "ol", "table", "dl"} and "box specifi" not in _node_marker_text(root):
            continue
        parent = root.parent
        if parent is None or parent.tag == "#document":
            continue
        sibling_heading = any(
            child is not root
            and child.tag in {"h2", "h3", "h4", "h5", "h6"}
            and not _is_spec_section_title(node_text(child))
            for child in parent.children
        )
        if sibling_heading:
            promoted.append(parent)
    if not promoted:
        return roots
    promoted_ids = {id(node) for node in promoted}
    result: list[Node] = []
    for root in roots:
        parent = root.parent
        replacement = parent if parent is not None and id(parent) in promoted_ids else root
        if replacement not in result:
            result.append(replacement)
    return result


def _is_group_header(node: Node) -> bool:
    if node.tag in {"h2", "h3", "h4", "h5", "h6", "summary"}:
        return bool(node_text(node)) and not _is_spec_section_title(node_text(node))
    marker = _node_marker_text(node)
    if node.tag in {"div", "li", "button", "header"} and any(
        phrase in marker for phrase in ("group title", "group header", "section title", "accordion header", "accordion title")
    ):
        return bool(node_text(node)) and not _contains_dom_row(node)
    if node.tag in {"div", "li", "button", "header"} and "group" in marker:
        return bool(node_text(node)) and not _contains_dom_row(node)
    if node.tag == "button" and (attr(node, "aria-controls") or attr(node, "data-target")):
        return bool(node_text(node)) and not _contains_dom_row(node)
    return False


def _dom_row_value(node: Node) -> tuple[str, str, str, bool, bool]:
    """Return label/raw-label/raw-value and missing-part flags."""

    if node.tag == "tr":
        cells = [child for child in node.children if child.tag in {"th", "td"}]
        if not cells:
            cells = [child for child in node.descendants() if child.tag in {"th", "td"}]
        label_node = cells[0] if cells else None
        value_nodes = cells[1:] if len(cells) > 1 else []
        raw_label = _raw_node_text(label_node)
        raw_value = "\n".join(_raw_node_text(value) for value in value_nodes if _raw_node_text(value))
    elif node.tag == "dt":
        raw_label = _raw_node_text(node)
        value_nodes: list[Node] = []
        if node.parent:
            siblings = node.parent.children
            try:
                position = siblings.index(node)
            except ValueError:
                position = -1
            for sibling in siblings[position + 1 :]:
                if sibling.tag == "dt":
                    break
                if sibling.tag == "dd":
                    value_nodes.append(sibling)
        raw_value = "\n".join(_raw_node_text(value) for value in value_nodes if _raw_node_text(value))
    else:
        raw_label = clean_text(node.attrs.get("data-label") or node.attrs.get("data-name"))
        raw_value = node.attrs.get("data-value", "").strip()
        if not raw_label or not raw_value:
            for candidate in node.descendants():
                if not raw_label:
                    raw_label = clean_text(candidate.attrs.get("data-label") or candidate.attrs.get("data-name"))
                if not raw_value:
                    raw_value = candidate.attrs.get("data-value", "").strip()
                if raw_label and raw_value:
                    break
        label_node = (
            node.first("strong")
            or node.first("label")
            or _semantic_role_node(node, {"label", "name", "key", "term"})
        )
        semantic_values = {id(candidate) for candidate in _semantic_role_nodes(
            node, {"value", "content", "detail", "description"}
        )}
        value_nodes = [
            candidate
            for candidate in node.descendants()
            if candidate.tag in {"aside", "dd"} or id(candidate) in semantic_values
        ]
        # Prefer outer value containers and omit nested marker nodes that carry
        # the same text. Distinct sibling value nodes remain in DOM order.
        value_node_ids = {id(candidate) for candidate in value_nodes}
        unique_value_nodes: list[Node] = []
        for candidate in value_nodes:
            ancestor = candidate.parent
            nested_in_value = False
            while ancestor is not None and ancestor is not node:
                if id(ancestor) in value_node_ids:
                    nested_in_value = True
                    break
                ancestor = ancestor.parent
            if not nested_in_value and candidate is not label_node:
                unique_value_nodes.append(candidate)
        if not raw_label:
            raw_label = _raw_node_text(label_node)
        if not raw_value:
            raw_value = "\n".join(
                text for text in (_raw_node_text(candidate) for candidate in unique_value_nodes) if text
            )
        # Publishers frequently use anonymous div/span children for a row.
        # Within a recognized row, the first element is the label and the
        # remaining elements form the value; this is structural, not a field
        # or category allow-list.
        if (not raw_label or not raw_value) and node.tag in {"li", "div", "article", "p"}:
            children = (
                _anonymous_dom_row_children(node)
                if node.tag in {"div", "article", "p"}
                else [child for child in node.children if child.tag != "#text"]
            )
            if len(children) >= 2:
                if not raw_label:
                    raw_label = _raw_node_text(children[0])
                if not raw_value:
                    raw_value = "\n".join(_raw_node_text(child) for child in children[1:] if _raw_node_text(child))
        if not raw_label or not raw_value:
            complete = clean_text(_raw_node_text(node))
            if ":" in complete:
                left, right = complete.split(":", 1)
                if not raw_label:
                    raw_label = left.strip()
                if not raw_value:
                    raw_value = right.strip()
        if not raw_value and raw_label:
            complete = _raw_node_text(node)
            clean_complete = clean_text(complete)
            clean_label = clean_text(raw_label)
            if clean_complete.startswith(clean_label):
                remainder = clean_complete[len(clean_label) :].strip(" :\t")
                if remainder:
                    raw_value = remainder
    label = _clean_spec_label(raw_label)
    # _spec_item owns the single destructive label/separator cleanup.  Only
    # inspect a cleaned copy here so a legitimate value beginning with the
    # label (for example "Bộ xử lý AiPQ") cannot be stripped a second time.
    value = clean_text(_dom_value_only(raw_value, raw_label))
    return label, raw_label, raw_value, not bool(label), not bool(value)


def _extract_dom_groups(document: Node) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roots = _find_spec_roots(document)
    groups: list[dict[str, Any]] = []
    group_lookup: dict[str, dict[str, Any]] = {}
    candidate_rows = 0
    rows_missing_label = 0
    rows_missing_value = 0
    unrecognized_rows = 0

    def ensure_group(name: str) -> dict[str, Any]:
        key = slug_text(name)
        group = group_lookup.get(key)
        if group is None:
            group = {"group": clean_text(name), "items": [], "source": "dom"}
            group_lookup[key] = group
            groups.append(group)
        return group

    for root in roots:
        section_name = ""
        for heading in root.descendants():
            if heading.tag in {"h1", "h2", "h3", "h4", "h5", "h6", "summary"} and _is_spec_section_title(node_text(heading)):
                section_name = node_text(heading)
                break
        current_group_name = section_name
        consumed_rows: set[int] = set()
        for node in root.descendants(include_self=True):
            ancestor = node.parent
            inside_consumed = False
            while ancestor is not None and ancestor is not root.parent:
                if id(ancestor) in consumed_rows:
                    inside_consumed = True
                    break
                ancestor = ancestor.parent
            if inside_consumed:
                continue
            if _is_group_header(node):
                current_group_name = node_text(node)
                ensure_group(current_group_name)
                continue
            if not _looks_like_dom_row(node):
                continue
            candidate_rows += 1
            label, raw_label, raw_value, missing_label, missing_value = _dom_row_value(node)
            consumed_rows.add(id(node))
            rows_missing_label += int(missing_label)
            rows_missing_value += int(missing_value)
            if missing_label or missing_value:
                unrecognized_rows += 1
                continue
            item = _spec_item(raw_label or label, raw_value, "dom")
            if item is None:
                unrecognized_rows += 1
                continue
            ensure_group(current_group_name)["items"].append(item)

    return groups, {
        "spec_section_present": _spec_section_present(document),
        "spec_section_count": len(roots),
        "candidate_row_count": candidate_rows,
        "rows_missing_label": rows_missing_label,
        "rows_missing_value": rows_missing_value,
        "unrecognized_row_count": unrecognized_rows,
    }


def _looks_like_item_mapping(value: Mapping[str, Any]) -> bool:
    return _mapping_get(value, _ITEM_LABEL_KEYS) is not None and _mapping_get(value, _ITEM_VALUE_KEYS) is not None


def _structured_groups(container: Any, source: str, group_hint: str = "") -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []

    def add_group(name: Any, items: Iterable[dict[str, Any]]) -> None:
        parsed = [item for item in items if item is not None]
        groups.append({"group": clean_text(name), "items": parsed, "source": source})

    if isinstance(container, list):
        loose_items: list[dict[str, Any]] = []
        for entry in container:
            if isinstance(entry, Mapping) and _looks_like_item_mapping(entry):
                item = _spec_item(_mapping_get(entry, _ITEM_LABEL_KEYS), _mapping_get(entry, _ITEM_VALUE_KEYS), source)
                if item:
                    loose_items.append(item)
                continue
            if isinstance(entry, Mapping):
                nested_items = _mapping_get(entry, _GROUP_ITEM_KEYS)
                if nested_items is not None:
                    group_name = _mapping_get(entry, _GROUP_NAME_KEYS) or group_hint
                    groups.extend(_structured_groups(nested_items, source, clean_text(group_name)))
                else:
                    groups.extend(_structured_groups(entry, source, group_hint))
        if loose_items:
            add_group(group_hint, loose_items)
        return groups

    if not isinstance(container, Mapping):
        return groups
    if _looks_like_item_mapping(container):
        item = _spec_item(_mapping_get(container, _ITEM_LABEL_KEYS), _mapping_get(container, _ITEM_VALUE_KEYS), source)
        if item:
            add_group(group_hint, [item])
        return groups

    nested_items = _mapping_get(container, _GROUP_ITEM_KEYS)
    if nested_items is not None:
        group_name = _mapping_get(container, _GROUP_NAME_KEYS) or group_hint
        return _structured_groups(nested_items, source, clean_text(group_name))

    scalar_items: list[dict[str, Any]] = []
    nested: list[tuple[str, Any]] = []
    for key, value in container.items():
        if str(key).startswith("@"):
            continue
        if isinstance(value, (Mapping, list)):
            nested.append((str(key), value))
        else:
            item = _spec_item(key, value, source)
            if item:
                scalar_items.append(item)
    if scalar_items:
        add_group(group_hint, scalar_items)
    for key, value in nested:
        groups.extend(_structured_groups(value, source, key if not group_hint else group_hint))
    return groups


def _groups_from_payload(payload: Any, source: str) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    if isinstance(payload, Mapping) and (
        _looks_like_item_mapping(payload) or _mapping_get(payload, _GROUP_ITEM_KEYS) is not None
    ):
        return _structured_groups(payload, source)
    if isinstance(payload, list) and any(
        isinstance(item, Mapping)
        and (_looks_like_item_mapping(item) or _mapping_get(item, _GROUP_ITEM_KEYS) is not None)
        for item in payload
    ):
        return _structured_groups(payload, source)

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            if _looks_like_item_mapping(value) or _mapping_get(value, _GROUP_ITEM_KEYS) is not None:
                groups.extend(_structured_groups(value, source))
                return
            for key, nested in value.items():
                if _compact_key(key) in _SPEC_CONTAINER_KEYS:
                    groups.extend(_structured_groups(nested, source))
                elif isinstance(nested, (Mapping, list)):
                    visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(payload)
    return groups


def _decode_script_payload(raw: str) -> Any:
    raw = raw.strip().rstrip(";")
    try:
        return json.loads(raw)
    except (ValueError, TypeError, json.JSONDecodeError):
        pass
    match = re.search(r"(?:=|:)\s*([\[{].*[\]}])\s*;?\s*$", raw, flags=re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _embedded_groups(document: Node) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for script in document.select("script"):
        script_type = clean_text(attr(script, "type")).lower()
        if script_type == "application/ld+json":
            continue
        raw = _raw_node_text(script)
        marker = slug_text(" ".join((attr(script, "id", "") or "", attr(script, "class", "") or "")))
        structured_marker = re.search(
            r"additionalProperty|parameterGroups?|specificationGroups?|technicalSpecifications?|thong[_-]?so|specifications?|specs",
            raw,
            flags=re.I,
        )
        if script_type not in {"application/json", "application/problem+json"} and not (
            structured_marker or any(phrase in marker for phrase in ("spec", "parameter", "thong so", "initial state", "next data"))
        ):
            continue
        payload = _decode_script_payload(raw)
        if payload is not None:
            groups.extend(_groups_from_payload(payload, "embedded_json"))
    return groups


def _merge_spec_groups(
    source_groups: Sequence[tuple[str, list[dict[str, Any]]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Merge supplemental sources into DOM items without weakening DOM detail."""

    merged: list[dict[str, Any]] = []
    group_lookup: dict[str, dict[str, Any]] = {}
    merge_events: list[dict[str, Any]] = []

    def ensure_group(name: str, source: str) -> dict[str, Any]:
        key = _normalized_label_key(name)
        group = group_lookup.get(key)
        if group is None:
            group = {"group": clean_text(name), "ordinal": len(merged), "items": [], "source": source, "sources": [source]}
            group_lookup[key] = group
            merged.append(group)
        elif source not in group["sources"]:
            group["sources"].append(source)
        return group

    def append_item(group: dict[str, Any], item: dict[str, Any], source: str) -> dict[str, Any]:
        copy = dict(item)
        copy["source"] = source
        copy["sources"] = list(dict.fromkeys(copy.get("sources", [source])))
        copy["provenance"] = list(dict.fromkeys(copy.get("provenance", copy["sources"])))
        group["items"].append(copy)
        return copy

    def candidates_for(label: Any) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        label_key = _normalized_label_key(label)
        matches = [
            (group, item)
            for group in merged
            for item in group["items"]
            if _normalized_label_key(item.get("label")) == label_key
        ]
        dom_matches = [(group, item) for group, item in matches if item.get("source") == "dom"]
        return dom_matches or matches

    def value_relation(primary: Any, incoming: Any) -> str:
        primary_key = _normalized_value_key(primary)
        incoming_key = _normalized_value_key(incoming)
        if primary_key == incoming_key:
            return "equal"
        primary_tokens = set(re.findall(r"\w+", primary_key, flags=re.UNICODE))
        incoming_tokens = set(re.findall(r"\w+", incoming_key, flags=re.UNICODE))
        if incoming_key and (incoming_key in primary_key or (incoming_tokens and incoming_tokens < primary_tokens)):
            return "supplemental_subset"
        if primary_key and (primary_key in incoming_key or (primary_tokens and primary_tokens < incoming_tokens)):
            return "primary_subset"
        return "different"

    def merge_into(group: dict[str, Any], existing: dict[str, Any], incoming: dict[str, Any], source: str) -> None:
        if source not in existing["sources"]:
            existing["sources"].append(source)
        existing["provenance"] = list(dict.fromkeys(existing.get("provenance", []) + [source]))
        if source not in group["sources"]:
            group["sources"].append(source)
        relation = value_relation(existing.get("value"), incoming.get("value"))
        merge_events.append(
            {
                "action": "merged",
                "source": source,
                "group": group["group"],
                "label": existing.get("label", ""),
                "primary_value": existing.get("value", ""),
                "incoming_value": incoming.get("value", ""),
                "value_relation": relation,
            }
        )

    for source, groups in source_groups:
        for incoming_group in groups:
            name = clean_text(incoming_group.get("group"))
            if source == "dom":
                group = ensure_group(name, source)
                for item in incoming_group.get("items", []):
                    append_item(group, item, source)
                continue

            for item in incoming_group.get("items", []):
                matches = candidates_for(item.get("label"))
                group_key = _normalized_label_key(name)
                if group_key:
                    grouped = [(group, existing) for group, existing in matches if _normalized_label_key(group["group"]) == group_key]
                    if grouped:
                        matches = grouped
                if len(matches) > 1:
                    value_matches = [
                        candidate
                        for candidate in matches
                        if value_relation(candidate[1].get("value"), item.get("value")) != "different"
                    ]
                    if len(value_matches) == 1:
                        matches = value_matches
                if len(matches) == 1:
                    merge_into(matches[0][0], matches[0][1], item, source)
                    continue
                if matches:
                    merge_events.append(
                        {
                            "action": "ambiguous",
                            "source": source,
                            "label": item.get("label", ""),
                            "incoming_group": name,
                            "incoming_value": item.get("value", ""),
                            "candidate_groups": [group["group"] for group, _ in matches],
                            "candidate_values": [existing.get("value", "") for _, existing in matches],
                        }
                    )
                    continue

                target_name = name or "Thông số bổ sung"
                target_group = ensure_group(target_name, source)
                added = append_item(target_group, item, source)
                merge_events.append(
                    {
                        "action": "added",
                        "source": source,
                        "group": target_group["group"],
                        "label": added.get("label", ""),
                        "incoming_value": added.get("value", ""),
                        "synthetic_group": not bool(name),
                    }
                )

    flat: list[dict[str, Any]] = []
    for group_ordinal, group in enumerate(merged):
        group["ordinal"] = group_ordinal
        for item_ordinal, item in enumerate(group["items"]):
            item["group"] = group["group"]
            item["group_ordinal"] = group_ordinal
            item["item_ordinal"] = item_ordinal
            item["ordinal"] = item_ordinal
            flat.append(item)
    return merged, merge_events


def parse_specification_groups(
    document: Node,
    json_ld: Mapping[str, Any] | Sequence[Any] | None = None,
    api_payloads: Sequence[Any] | None = None,
) -> SpecificationParseResult:
    """Extract and merge every specification without a category field list."""

    dom_groups, dom_diagnostics = _extract_dom_groups(document)
    if not json_ld:
        json_ld = _json_ld(document)
    api_groups: list[dict[str, Any]] = []
    if isinstance(api_payloads, (Mapping, str, bytes)):
        payload_iter: Iterable[Any] = (api_payloads,)
    else:
        payload_iter = api_payloads or ()
    for payload in payload_iter:
        if isinstance(payload, (str, bytes)):
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", errors="replace")
            payload = _decode_script_payload(payload)
        if payload is not None:
            api_groups.extend(_groups_from_payload(payload, "api"))
    embedded_groups = _embedded_groups(document)
    json_ld_groups: list[dict[str, Any]] = []
    if isinstance(json_ld, Mapping):
        additional = json_ld.get("additionalProperty")
        if additional:
            json_ld_groups.extend(_structured_groups(additional, "json_ld"))
    elif isinstance(json_ld, (list, tuple)):
        json_ld_groups.extend(_structured_groups(json_ld, "json_ld"))

    source_groups = (
        ("dom", dom_groups),
        ("api", api_groups),
        ("embedded_json", embedded_groups),
        ("json_ld", json_ld_groups),
    )
    groups, merge_events = _merge_spec_groups(source_groups)
    value_differences = [
        event
        for event in merge_events
        if event.get("action") == "merged" and event.get("value_relation") != "equal"
    ]
    ambiguous_merges = [event for event in merge_events if event.get("action") == "ambiguous"]
    items = [item for group in groups for item in group["items"]]
    source_item_counts = {
        source: sum(len(group.get("items", [])) for group in candidates)
        for source, candidates in source_groups
    }
    empty_groups = [group["group"] for group in groups if not group["items"]]

    def evidence_set(candidates: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
        return {
            (slug_text(group.get("group", "")), slug_text(item.get("label", "")), clean_text(item.get("value", "")).casefold())
            for group in candidates
            for item in group.get("items", [])
        }

    dom_evidence = evidence_set(dom_groups)
    embedded_evidence = evidence_set(embedded_groups)
    warnings_list: list[str] = []
    if dom_diagnostics["spec_section_present"] and not items:
        warnings_list.append("A specification section was present but no complete specification item was parsed.")
    if dom_diagnostics["rows_missing_label"] or dom_diagnostics["rows_missing_value"]:
        warnings_list.append("Some candidate specification rows were incomplete and were not persisted.")
    if dom_diagnostics["unrecognized_row_count"]:
        warnings_list.append("Some specification markup was recognized as a row but could not be parsed completely.")
    if empty_groups:
        warnings_list.append("One or more discovered specification groups contained no complete items.")
    if ambiguous_merges:
        warnings_list.append("One or more supplemental specifications had ambiguous DOM matches and were not merged.")

    diagnostics = {
        **dom_diagnostics,
        "group_count": len(groups),
        "total_item_count": len(items),
        "item_counts": [
            {"group": group["group"], "group_ordinal": group["ordinal"], "item_count": len(group["items"])}
            for group in groups
        ],
        "empty_groups": empty_groups,
        "source_item_counts": source_item_counts,
        "dom_only_count": len(dom_evidence - embedded_evidence),
        "embedded_only_count": len(embedded_evidence - dom_evidence),
        "conflicts": value_differences,
        "ambiguous_merges": ambiguous_merges,
        "merge_diagnostics": {
            "merged_count": sum(event.get("action") == "merged" for event in merge_events),
            "added_count": sum(event.get("action") == "added" for event in merge_events),
            "ambiguous_count": len(ambiguous_merges),
            "value_differences": value_differences,
            "events": merge_events,
        },
        "warnings": warnings_list,
    }
    for message in warnings_list:
        warnings.warn(message, RuntimeWarning, stacklevel=2)
    return SpecificationParseResult(groups=groups, items=items, diagnostics=diagnostics)


def parse_specs(
    document: Node,
    json_ld: Mapping[str, Any] | Sequence[Any] | None = None,
    api_payloads: Sequence[Any] | None = None,
    diagnostics: dict[str, Any] | None = None,
    *,
    spec_payloads: Sequence[Any] | None = None,
) -> list[dict[str, Any]]:
    """Backward-compatible flat view; use ``parse_specification_groups`` for the snapshot."""

    result = parse_specification_groups(document, json_ld, api_payloads or spec_payloads)
    if diagnostics is not None:
        diagnostics.update(result.diagnostics)
    return result.items


def parse_category_page(raw_html: str, category: str, base_url: str = "https://www.dienmayxanh.com") -> list[ProductLink]:
    document = parse_html(raw_html)
    links: list[ProductLink] = []
    seen: set[str] = set()
    prefix = "/" + category.strip("/").lower() + "/"
    for card in document.select("li.item"):
        anchor = card.first("a.main-contain")
        if anchor is None:
            continue
        href = _attribute(anchor, "href")
        if not href:
            continue
        url = canonical_url(urljoin(base_url, href), base_url)
        if not urlsplit_path_starts(url, prefix):
            continue
        if url in seen:
            continue
        seen.add(url)
        sold_text = first_nonempty((_text(card, ".rating_Compare span"), _text(card, ".item-bottom")))
        image = card.first(".item-img img")
        links.append(
            ProductLink(
                url=url,
                category_code=category,
                source_product_key=_attribute(anchor, "data-id") or _attribute(card, "data-id"),
                product_code=_attribute(card, "data-productcode") or _attribute(anchor, "data-productcode"),
                source="category",
                title_hint=_attribute(anchor, "data-name") or first_nonempty((_text(card, "h3"), _text(card, ".product-title"))),
                brand_hint=_attribute(anchor, "data-brand"),
                sale_price_hint=parse_price(first_nonempty((_attribute(anchor, "data-price"), _text(card, "strong.price"), _text(card, ".price")))),
                list_price_hint=parse_price(first_nonempty((_attribute(card, "data-price"), _text(card, ".price-old")))),
                sold_hint=parse_sold_count(sold_text),
                raw={"image": _attribute(image, "data-src", "src", "data-thumb")},
            )
        )
    return links


def urlsplit_path_starts(url: str, prefix: str) -> bool:
    from urllib.parse import urlsplit

    path = urlsplit(url).path.lower()
    return path.startswith(prefix)


def _commercial_model(value: Any, source_product_key: str | None) -> str | None:
    candidate = clean_text(value)
    if not candidate or candidate.isdigit():
        return None
    if source_product_key and _normalized_merge_text(candidate) == _normalized_merge_text(source_product_key):
        return None
    return candidate


def parse_product_page(
    raw_html: str,
    url: str,
    category: str,
    *,
    spec_payloads: Sequence[Any] | None = None,
    api_payloads: Sequence[Any] | None = None,
) -> ProductContent:
    document = parse_html(raw_html)
    ld = _json_ld(document)
    name = clean_text(first_nonempty((ld.get("name"), _text(document, "h1"))))
    if not name:
        name = clean_text(_text(document, ".product-name")) or url.rstrip("/").rsplit("/", 1)[-1]
    ld_sku = clean_text(ld.get("sku")) or None
    ld_mpn = clean_text(ld.get("mpn")) or None
    product_id_match = re.search(r"document\.productId\s*=\s*['\"]?([^'\";\s]+)", raw_html)
    page_product_id = clean_text(product_id_match.group(1)) if product_id_match else None
    source_product_key = ld_sku or page_product_id or (ld_mpn if ld_mpn and ld_mpn.isdigit() else None)
    model = (
        _commercial_model(ld.get("model"), source_product_key)
        or _commercial_model(ld_mpn, source_product_key)
        or extract_model(name)
    )
    brand = _brand(ld.get("brand")) or clean_text(_attribute(document.first("[data-brand]"), "data-brand")) or None
    description = clean_text(ld.get("description")) or _text(document, "#tab-2 .text-detail") or None

    sale_price: Optional[int] = None
    list_price: Optional[int] = None
    promotion: dict[str, Any] = {}
    price_node = document.first(".bs_price") or document.first(".box-price")
    if price_node:
        sale_price = parse_price(first_nonempty((_text(price_node, "strong"), _text(price_node, ".box-price-present"), _text(price_node, ".price"))))
        list_price = parse_price(first_nonempty((_text(price_node, "em"), _text(price_node, ".box-price-old"), _text(price_node, ".price-old"))))
        if sale_price is None:
            sale_price = parse_price(first_nonempty((attr(price_node, "data-price"), attr(price_node, "data-priceorg"))))
        if list_price is None:
            list_price = parse_price(attr(price_node, "data-priceorg"))
        percent = parse_percent(first_nonempty((_text(price_node, "i"), _text(price_node, ".box-price-percent"), _text(price_node, ".percent"))))
        if percent is not None:
            promotion["discount_percent"] = percent
    offers = ld.get("offers") if isinstance(ld.get("offers"), Mapping) else {}
    sale_price = sale_price if sale_price is not None else parse_price(offers.get("price"))
    if list_price is None:
        list_price = parse_price(_find_data_value(document, "data-priceorg", (".bs_price", ".box-price")))
    promo_node = document.first(".block__promo") or document.first(".item-gift")
    if promo_node:
        promotion["text"] = node_text(promo_node)
        if attr(promo_node, "data-scenario"):
            promotion["scenario"] = attr(promo_node, "data-scenario")

    aggregate = ld.get("aggregateRating") if isinstance(ld.get("aggregateRating"), Mapping) else {}
    rating = parse_rating(first_nonempty((_text(document, ".detail-rate"), aggregate.get("ratingValue"))))
    rating_count = parse_int(first_nonempty((aggregate.get("reviewcount"), aggregate.get("reviewCount"))))
    sold = parse_sold_count(first_nonempty((_text(document, ".quantity-sale"), _text(document, ".rating_Compare span"))))
    parsed_specs = parse_specification_groups(document, ld, spec_payloads or api_payloads)
    specs = parsed_specs.items
    images: list[str] = []
    for image in document.select("#slider-default .item-img img") + document.select(".gallery .item-img img"):
        src = _attribute(image, "data-src", "data-thumb", "src")
        if src:
            src = urljoin("https://www.dienmayxanh.com", src)
            if src not in images:
                images.append(src)
    if not images:
        image = ld.get("image")
        if isinstance(image, Mapping):
            image = image.get("contentUrl") or image.get("url")
        if isinstance(image, str) and image:
            images.append(image)
    stock_raw = first_nonempty((_text(document, ".item_web_status"), _text(document, ".detail-status"), _text(document, ".box_normal"))) or ""
    availability = offers.get("availability")
    status, stock_raw = stock_status(stock_raw, availability)
    if "ngừng kinh doanh" in clean_text(document.text_content()).lower():
        status, stock_raw = "out_of_stock", "SẢN PHẨM NGỪNG KINH DOANH"
    evidence = parse_location_evidence(raw_html, document)
    return ProductContent(
        canonical_url=canonical_url(url),
        category_code=category,
        name=name,
        brand=brand,
        model=model,
        source_product_key=source_product_key,
        product_code=_find_data_value(document, "data-productcode", ("[data-productcode]",)) or None,
        description=description,
        rating=rating,
        rating_count=rating_count,
        sold_count=sold,
        specs=specs,
        specs_raw=parsed_specs.groups,
        specs_diagnostics=parsed_specs.diagnostics,
        images=images,
        stock_status=status,
        stock_raw=stock_raw,
        source_location={"evidence": evidence, "sale_price": sale_price, "list_price": list_price, "promotion": promotion},
    )


def parse_delivery_response(raw: str | bytes) -> DeliveryInfo:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    html = raw
    payload: Any = None
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError, json.JSONDecodeError):
        pass
    if isinstance(payload, Mapping):
        if int(payload.get("code", 1) or 0) == -1:
            return DeliveryInfo(status="unknown", raw_text=clean_text(payload.get("msg")))
        data = payload.get("data")
        html = data.get("html", "") if isinstance(data, Mapping) else ""
    document = parse_html(html)
    delivery = document.first(".deliverytime")
    if not delivery:
        text = node_text(document)
        return DeliveryInfo(status="unknown", raw_text=text, returned_location=_parse_data_deli(html))
    text = node_text(delivery)
    ship = node_text(delivery.first(".ship"))
    time = node_text(delivery.first(".time"))
    address = None
    match = re.search(r"Giao đến:\s*(.*?)(?:Thay đổi|$)", text, flags=re.I)
    if match:
        address = clean_text(match.group(1))
    status, _ = stock_status(text)
    if status == "unknown":
        status = "in_stock" if time or ship else "unknown"
    return DeliveryInfo(
        status=status,
        address=address,
        method=ship or None,
        eta=time or None,
        raw_text=text,
        returned_location=_parse_data_deli(html),
    )


def merge_location_snapshot(content: ProductContent, delivery: DeliveryInfo) -> LocationSnapshot:
    source = content.source_location
    return LocationSnapshot(
        sale_price=source.get("sale_price"),
        list_price=source.get("list_price"),
        promotion=source.get("promotion") or {},
        stock_status=content.stock_status if content.stock_status != "unknown" else delivery.status,
        stock_raw=content.stock_raw,
        delivery=delivery,
        returned_location={**(source.get("evidence") or {}), **(delivery.returned_location)},
    )
