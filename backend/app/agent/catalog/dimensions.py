"""Per-category product dimensions: the evidence-based feature registry.

Every entry was verified against the real workbook (field-profile audit,
2026-07-18): only attributes with meaningful fill rates are listed, and all
placeholder values ("Hãng không công bố", "Đang cập nhật", "Không"...) parse
as missing so the bot never claims a spec the maker did not publish.

The registry powers preference-driven suggestion roles, multi-dimension
comparison, and deep follow-up answers ("màn nào nét hơn?", "thang đo là
gì?"). Semi-independent per category (Cường's direction): each ngành evolves
its own dimension list without touching the graph.
"""

import re
from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct

PLACEHOLDERS = {
    "hãng không công bố",
    "đang cập nhật",
    "không",
    "không có",
    "null",
    "none",
    "",
}

_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")


@dataclass(frozen=True, slots=True)
class Dimension:
    key: str  # attribute name exactly as in the data
    label: str  # customer-facing Vietnamese name
    kind: str  # numeric_higher | numeric_lower | ordinal | enum_info | feature
    superlative: str  # role label when this dimension wins ("Sắc nét nhất")
    explain: str  # what the measure means ("càng thấp phản hồi càng nhanh")
    unit: str = ""
    pref_markers: tuple[str, ...] = ()
    ordinal_map: tuple[tuple[str, int], ...] = ()  # keyword -> rank, first match
    # Normalize a raw numeric to a comparable unit (e.g. ngày -> giờ, TB -> GB).
    normalize_units: tuple[tuple[str, float], ...] = ()


def is_placeholder(value: object) -> bool:
    return value is None or str(value).strip().lower() in PLACEHOLDERS


def _first_number(text: str) -> float | None:
    match = _NUMBER.search(text)
    return float(match.group(1).replace(",", ".")) if match else None


def dimension_value(product: GenericProduct, dim: Dimension):
    """Parsed, comparable value or None. Never guesses on placeholders."""
    raw = product.attributes.get(dim.key)
    if is_placeholder(raw):
        return None
    text = str(raw).strip()
    low = text.lower()
    if dim.kind == "ordinal":
        for keyword, rank in dim.ordinal_map:
            if keyword in low:
                return rank
        return None
    if dim.kind in ("numeric_higher", "numeric_lower"):
        number = _first_number(text)
        if number is None:
            return None
        for unit_marker, factor in dim.normalize_units:
            if unit_marker in low:
                return number * factor
        return number
    if dim.kind == "feature":
        return not low.startswith("không")
    return text  # enum_info: cleaned display text


def dimension_display(product: GenericProduct, dim: Dimension) -> str | None:
    """Raw text for rendering (verbatim from the record, validator-safe)."""
    raw = product.attributes.get(dim.key)
    if is_placeholder(raw):
        return None
    return str(raw).strip()


def better_of(a, b, dim: Dimension) -> int:
    """-1 if a wins, 1 if b wins, 0 if tie/not rankable."""
    if a is None or b is None or a == b:
        return 0
    if dim.kind in ("numeric_higher", "ordinal"):
        return -1 if a > b else 1
    if dim.kind == "numeric_lower":
        return -1 if a < b else 1
    if dim.kind == "feature":
        return -1 if (a and not b) else (1 if (b and not a) else 0)
    return 0


_RESOLUTION_ORDINAL = (
    ("8k", 6),
    ("5k", 5),
    ("4.5k", 5),
    ("4k", 4),
    ("uhd", 4),
    ("2k", 3),
    ("qhd", 3),
    ("wqhd", 3),
    ("full hd", 2),
    ("fhd", 2),
    ("retina", 4),
    ("hd", 1),
)

DIMENSIONS: dict[str, tuple[Dimension, ...]] = {
    "73": (  # Màn hình máy tính — fills: phân giải 90%, đáp ứng 90%, sáng 91%
        Dimension(
            key="Độ phân giải", label="Độ phân giải", kind="ordinal",
            superlative="Sắc nét nhất",
            explain="độ phân giải càng cao hình càng nét (Full HD < 2K/QHD < 4K/UHD)",
            pref_markers=("nét", "sắc nét", "xem phim", "làm việc", "văn phòng", "phân giải"),
            ordinal_map=_RESOLUTION_ORDINAL,
        ),
        Dimension(
            key="Thời gian đáp ứng", label="Thời gian đáp ứng", kind="numeric_lower",
            superlative="Phản hồi nhanh nhất", unit="ms",
            explain="thời gian đáp ứng càng thấp hình chuyển động càng mượt, hợp chơi game",
            pref_markers=("game", "gaming", "mượt", "fps", "đáp ứng"),
        ),
        Dimension(
            key="Độ sáng", label="Độ sáng", kind="numeric_higher",
            superlative="Màn sáng nhất", unit="cd/m²",
            explain="độ sáng (nit) càng cao càng dễ nhìn ở phòng sáng",
            pref_markers=("sáng", "phòng sáng"),
        ),
        Dimension(
            key="Độ phủ màu", label="Độ phủ màu", kind="numeric_higher",
            superlative="Màu chuẩn nhất", unit="%",
            explain="độ phủ màu (sRGB/DCI-P3) càng cao màu càng chuẩn, hợp đồ họa",
            pref_markers=("đồ họa", "màu", "thiết kế", "dựng"),
        ),
        Dimension(
            key="Kích thước màn hình", label="Kích thước màn hình",
            kind="numeric_higher", superlative="Màn rộng nhất", unit="inch",
            explain="kích thước màn hình tính theo inch đường chéo",
            pref_markers=("rộng", "màn lớn", "to"),
        ),
        Dimension(
            key="Tấm nền", label="Tấm nền", kind="enum_info", superlative="",
            explain="tấm nền IPS cho góc nhìn rộng và màu đẹp, VA cho độ tương phản cao",
            pref_markers=("ips", "va", "tấm nền", "góc nhìn"),
        ),
        Dimension(
            key="Điện năng tiêu thụ", label="Điện năng tiêu thụ",
            kind="numeric_lower", superlative="Tiết kiệm điện nhất", unit="W",
            explain="công suất tiêu thụ (W) càng thấp càng tiết kiệm điện",
            pref_markers=("tiết kiệm điện", "điện năng"),
        ),
    ),
    "72": (  # Máy tính để bàn
        Dimension(
            key="RAM", label="RAM", kind="numeric_higher",
            superlative="RAM cao nhất", unit="GB",
            explain="RAM càng nhiều chạy đa nhiệm càng mượt",
            pref_markers=("ram", "đa nhiệm"),
        ),
        Dimension(
            key="Ổ cứng", label="Ổ cứng", kind="numeric_higher",
            superlative="Lưu trữ lớn nhất", unit="GB",
            explain="dung lượng lưu trữ; SSD nhanh hơn HDD",
            pref_markers=("ổ cứng", "lưu trữ", "ssd"),
            normalize_units=(("tb", 1000.0),),
        ),
        Dimension(
            key="Bộ nhớ", label="Card đồ họa (VRAM)", kind="numeric_higher",
            superlative="Card mạnh nhất", unit="GB",
            explain="VRAM card rời càng cao chơi game/đồ họa càng khỏe",
            pref_markers=("card", "gpu", "game", "gaming", "đồ họa"),
        ),
        Dimension(
            key="Công nghệ CPU", label="CPU", kind="enum_info", superlative="",
            explain="dòng chip xử lý (Intel Core/Apple M/AMD Ryzen)",
            pref_markers=("chip", "cpu"),
        ),
        Dimension(
            key="Hệ điều hành", label="Hệ điều hành", kind="enum_info",
            superlative="", explain="hệ điều hành cài sẵn",
            pref_markers=("windows", "mac"),
        ),
    ),
    "38": (  # Tủ Lạnh
        Dimension(
            key="Dung tích sử dụng", label="Dung tích sử dụng",
            kind="numeric_higher", superlative="Dung tích lớn nhất", unit="lít",
            explain="dung tích càng lớn chứa được càng nhiều, hợp nhà đông người",
            pref_markers=("đông người", "nhiều đồ", "dung tích", "gia đình"),
        ),
        Dimension(
            key="Dung tích ngăn đá", label="Dung tích ngăn đá",
            kind="numeric_higher", superlative="Ngăn đá lớn nhất", unit="lít",
            explain="ngăn đá lớn hợp trữ đông thực phẩm nhiều",
            pref_markers=("trữ đông", "ngăn đá", "đông lạnh"),
        ),
        Dimension(
            key="Kiểu dáng", label="Kiểu dáng", kind="enum_info", superlative="",
            explain="ngăn đá trên/dưới hay Side by Side",
            pref_markers=("side by side", "ngăn đá trên", "ngăn đá dưới"),
        ),
        Dimension(
            key="Công nghệ tiết kiệm điện", label="Công nghệ tiết kiệm điện",
            kind="feature", superlative="Có Inverter tiết kiệm điện",
            explain="máy có Inverter chạy êm và tiết kiệm điện hơn",
            pref_markers=("tiết kiệm điện", "inverter"),
        ),
    ),
    "36": (  # Máy lạnh
        Dimension(
            key="Phạm vi sử dụng", label="Phạm vi làm lạnh", kind="enum_info",
            superlative="", explain="diện tích phòng phù hợp mà hãng công bố",
            pref_markers=("phòng", "diện tích"),
        ),
        Dimension(
            key="Độ ồn", label="Độ ồn", kind="numeric_lower",
            superlative="Chạy êm nhất", unit="dB",
            explain="độ ồn (dB) càng thấp máy chạy càng êm, hợp phòng ngủ",
            pref_markers=("êm", "ồn", "ngủ", "yên tĩnh"),
        ),
        Dimension(
            key="Loại Inverter", label="Inverter", kind="feature",
            superlative="Có Inverter tiết kiệm điện",
            explain="máy Inverter tiết kiệm điện khi chạy dài",
            pref_markers=("tiết kiệm điện", "inverter"),
        ),
        Dimension(
            key="Loại máy", label="Loại máy", kind="enum_info", superlative="",
            explain="1 chiều chỉ làm lạnh, 2 chiều có thêm sưởi ấm",
            pref_markers=("2 chiều", "sưởi"),
        ),
    ),
    "115": (  # Máy giặt — data NAY có spec (audit 2026-07-18: tải 70%, cửa 77%)
        Dimension(
            key="Khối lượng tải chính", label="Khối lượng giặt",
            kind="numeric_higher", superlative="Giặt được nhiều nhất", unit="kg",
            explain="khối lượng giặt (kg) càng lớn giặt được càng nhiều đồ mỗi mẻ",
            pref_markers=("đông người", "nhiều đồ", "chăn", "gia đình"),
        ),
        Dimension(
            key="Loại sản phẩm", label="Kiểu cửa", kind="enum_info",
            superlative="", explain="cửa trước giặt êm tiết kiệm nước, cửa trên giá tốt dễ dùng",
            pref_markers=("cửa trước", "cửa trên"),
        ),
        Dimension(
            key="Tốc độ quay vắt tối đa", label="Tốc độ vắt",
            kind="numeric_higher", superlative="Vắt khô nhanh nhất", unit="vòng/phút",
            explain="tốc độ vắt càng cao đồ càng khô nhanh sau giặt",
            pref_markers=("vắt", "khô nhanh"),
        ),
        Dimension(
            key="Loại Inverter", label="Inverter", kind="feature",
            superlative="Có Inverter tiết kiệm điện",
            explain="máy Inverter chạy êm và tiết kiệm điện",
            pref_markers=("tiết kiệm điện", "inverter"),
        ),
    ),
    "116": (  # Máy sấy quần áo
        Dimension(
            key="Khối lượng tải chính", label="Khối lượng sấy",
            kind="numeric_higher", superlative="Sấy được nhiều nhất", unit="kg",
            explain="khối lượng sấy (kg) mỗi mẻ",
            pref_markers=("đông người", "nhiều đồ"),
        ),
        Dimension(
            key="Loại sản phẩm", label="Công nghệ sấy", kind="enum_info",
            superlative="", explain="sấy bơm nhiệt tiết kiệm điện nhất, thông hơi giá tốt",
            pref_markers=("bơm nhiệt", "tiết kiệm điện"),
        ),
        Dimension(
            key="Điện năng tiêu thụ", label="Điện năng tiêu thụ",
            kind="numeric_lower", superlative="Tiết kiệm điện nhất", unit="W",
            explain="công suất (W) càng thấp càng đỡ tốn điện",
            pref_markers=("điện năng",),
        ),
    ),
    "39": (  # Máy rửa chén
        # "Số lượng" mixes two counts ("3 - 4 bữa ăn Việt (13 bộ Châu Âu)") —
        # a naive first-number parse would rank by bữa ăn, so display-only.
        Dimension(
            key="Số lượng", label="Sức chứa", kind="enum_info",
            superlative="", explain="số bữa ăn Việt / bộ chén Châu Âu rửa được mỗi lần",
            pref_markers=("đông người", "nhiều chén", "gia đình"),
        ),
        Dimension(
            key="Độ ồn", label="Độ ồn", kind="numeric_lower",
            superlative="Chạy êm nhất", unit="dB",
            explain="độ ồn càng thấp chạy càng êm",
            pref_markers=("êm", "ồn"),
        ),
        Dimension(
            key="Tiêu thụ nước", label="Nước mỗi lần rửa", kind="numeric_lower",
            superlative="Tiết kiệm nước nhất", unit="lít",
            explain="lượng nước mỗi lần rửa càng thấp càng tiết kiệm",
            pref_markers=("tiết kiệm nước", "nước"),
        ),
    ),
    "40": (  # Tủ mát, tủ đông
        Dimension(
            key="Dung tích tổng", label="Dung tích tổng", kind="numeric_higher",
            superlative="Dung tích lớn nhất", unit="lít",
            explain="dung tích càng lớn trữ được càng nhiều",
            pref_markers=("dung tích", "nhiều đồ", "kinh doanh"),
        ),
        Dimension(
            key="Loại sản phẩm", label="Loại tủ", kind="enum_info",
            superlative="", explain="tủ đông trữ đông sâu, tủ mát để đồ uống/rau củ",
            pref_markers=("tủ đông", "tủ mát"),
        ),
        Dimension(
            key="Công nghệ tiết kiệm điện", label="Inverter", kind="feature",
            superlative="Có Inverter tiết kiệm điện",
            explain="Inverter giúp tiết kiệm điện khi chạy liên tục",
            pref_markers=("tiết kiệm điện", "inverter"),
        ),
        Dimension(
            key="Độ ồn", label="Độ ồn", kind="numeric_lower",
            superlative="Chạy êm nhất", unit="dB",
            explain="độ ồn càng thấp càng êm",
            pref_markers=("êm", "ồn"),
        ),
    ),
    "41": (  # Máy nước nóng
        Dimension(
            key="Công suất đầu ra", label="Công suất", kind="numeric_higher",
            superlative="Làm nóng mạnh nhất", unit="W",
            explain="công suất càng cao nước nóng càng nhanh",
            pref_markers=("nóng nhanh", "công suất"),
        ),
        Dimension(
            key="Dung lượng dung tích", label="Dung tích bình",
            kind="numeric_higher", superlative="Bình chứa lớn nhất", unit="lít",
            explain="bình chứa lớn đủ nước nóng cho nhiều người tắm liên tục",
            pref_markers=("đông người", "gia đình", "bình chứa"),
        ),
        Dimension(
            key="Loại máy", label="Loại máy", kind="enum_info", superlative="",
            explain="trực tiếp nóng liền, gián tiếp có bình chứa, năng lượng mặt trời tiết kiệm điện",
            pref_markers=("trực tiếp", "gián tiếp", "năng lượng mặt trời"),
        ),
        Dimension(
            key="Tính năng an toàn", label="Tính năng an toàn", kind="enum_info",
            superlative="", explain="chống giật ELCB, chống bỏng, chống thấm",
            pref_markers=("an toàn", "chống giật"),
        ),
    ),
    "30": (  # Máy tính bảng
        Dimension(
            key="RAM", label="RAM", kind="numeric_higher",
            superlative="RAM cao nhất", unit="GB",
            explain="RAM càng nhiều đa nhiệm càng mượt",
            pref_markers=("ram", "đa nhiệm"),
        ),
        Dimension(
            key="Dung lượng lưu trữ", label="Bộ nhớ trong", kind="numeric_higher",
            superlative="Bộ nhớ lớn nhất", unit="GB",
            explain="bộ nhớ trong càng lớn chứa được càng nhiều ứng dụng/phim",
            pref_markers=("bộ nhớ", "lưu trữ"),
        ),
        Dimension(
            key="Kích thước màn hình", label="Kích thước màn hình",
            kind="numeric_higher", superlative="Màn lớn nhất", unit="inch",
            explain="màn càng lớn xem phim/ghi chú càng thoải mái",
            pref_markers=("màn lớn", "xem phim", "học"),
        ),
        Dimension(
            key="Mạng di động", label="Mạng di động", kind="enum_info",
            superlative="", explain="bản 4G/5G lắp SIM dùng ngoài trời, bản WiFi giá tốt hơn",
            pref_markers=("4g", "5g", "sim"),
        ),
    ),
    "49": (  # Đồng hồ thông minh
        Dimension(
            key="Thời gian sử dụng", label="Thời lượng pin",
            kind="numeric_higher", superlative="Pin trâu nhất", unit="giờ",
            explain="thời lượng pin quy về giờ; đồng hồ thể thao thường trâu hơn smartwatch màn đẹp",
            pref_markers=("pin", "pin trâu"),
            normalize_units=(("ngày", 24.0), ("tuần", 168.0)),
        ),
        Dimension(
            key="Chuẩn chống nước, bụi", label="Chống nước", kind="enum_info",
            superlative="", explain="chuẩn ATM càng cao bơi/lặn càng an tâm",
            pref_markers=("chống nước", "bơi", "lặn"),
        ),
        Dimension(
            key="Màn hình hiển thị", label="Loại màn hình", kind="enum_info",
            superlative="", explain="AMOLED/OLED màu đẹp, MIP tiết kiệm pin ngoài trời",
            pref_markers=("amoled", "màn đẹp"),
        ),
        Dimension(
            key="Thực hiện cuộc gọi", label="Nghe gọi", kind="enum_info",
            superlative="", explain="có/không nghe gọi ngay trên đồng hồ",
            pref_markers=("nghe gọi", "cuộc gọi"),
        ),
    ),
    "75": (  # Máy in
        Dimension(
            key="Tốc độ in", label="Tốc độ in", kind="numeric_higher",
            superlative="In nhanh nhất", unit="trang/phút",
            explain="số trang in được mỗi phút",
            pref_markers=("nhanh", "tốc độ"),
        ),
        Dimension(
            key="Chất lượng in (độ nét)", label="Độ nét in", kind="numeric_higher",
            superlative="In nét nhất", unit="dpi",
            explain="độ phân giải in (dpi) càng cao bản in càng nét",
            pref_markers=("nét", "chất lượng"),
        ),
        Dimension(
            key="Loại sản phẩm", label="Loại máy in", kind="enum_info",
            superlative="", explain="laser trắng đen in văn bản rẻ/bền, in phun màu in ảnh màu",
            pref_markers=("màu", "in màu", "laser", "in ảnh"),
        ),
        Dimension(
            key="Kết nối", label="Kết nối", kind="enum_info", superlative="",
            explain="có WiFi in không dây từ điện thoại",
            pref_markers=("wifi", "không dây"),
        ),
    ),
    "137": (  # Micro thu âm điện thoại
        Dimension(
            key="Khoảng cách truyền", label="Khoảng cách truyền",
            kind="numeric_higher", superlative="Truyền xa nhất", unit="m",
            explain="khoảng cách thu không dây tối đa",
            pref_markers=("xa", "khoảng cách"),
        ),
        Dimension(
            key="Thời gian sử dụng", label="Thời lượng pin", kind="enum_info",
            superlative="", explain="thời gian dùng liên tục mỗi lần sạc",
            pref_markers=("pin",),
        ),
        Dimension(
            key="Tính năng cơ bản", label="Tính năng", kind="enum_info",
            superlative="", explain="lọc tiếng ồn, tự động kết nối...",
            pref_markers=("lọc ồn", "khử ồn"),
        ),
    ),
    "139": (  # Micro karaoke
        Dimension(
            key="Độ méo tiếng", label="Độ méo tiếng", kind="numeric_lower",
            superlative="Tiếng sạch nhất", unit="%",
            explain="độ méo tiếng càng thấp giọng càng trung thực",
            pref_markers=("tiếng", "méo"),
        ),
        Dimension(
            key="Loại sản phẩm", label="Loại micro", kind="enum_info",
            superlative="", explain="có dây ổn định, không dây tiện di chuyển",
            pref_markers=("không dây", "có dây"),
        ),
    ),
}

# The dimension the generic "best performance" role uses per category (the
# old scenario `performance_attribute` stays as fallback for categories not
# listed here). Monitors: resolution — NOT screen size (live-test 3 finding).
# Categories absent here (36, 39, 40, 49, 137, 139) keep the legacy
# `performance_attribute` path unchanged — additive only, never regressive.
HEADLINE: dict[str, str] = {
    "73": "Độ phân giải",
    "72": "RAM",
    "38": "Dung tích sử dụng",
    "115": "Khối lượng giặt",
    "116": "Khối lượng sấy",
    "41": "Công suất",
    "30": "RAM",
    "75": "Tốc độ in",
}


def dimensions_for(category_code: str | None) -> tuple[Dimension, ...]:
    return DIMENSIONS.get(category_code or "", ())


def find_dimension(category_code: str | None, label_or_key: str) -> Dimension | None:
    for dim in dimensions_for(category_code):
        if dim.key == label_or_key or dim.label == label_or_key:
            return dim
    return None


def headline_dimension(category_code: str | None) -> Dimension | None:
    label = HEADLINE.get(category_code or "")
    return find_dimension(category_code, label) if label else None


def preferred_dimensions(
    category_code: str | None, need
) -> list[Dimension]:
    """Rank dimensions by how strongly the captured need points at them."""
    if need is None:
        return []
    signals: list[str] = []
    if need.usage_purpose:
        signals.append(need.usage_purpose.lower())
    signals.extend(p.lower() for p in need.priorities)
    signals.extend(str(v).lower() for v in need.attribute_constraints.values())
    if not signals:
        return []
    scored: list[tuple[int, int, Dimension]] = []
    for index, dim in enumerate(dimensions_for(category_code)):
        hits = sum(
            1
            for marker in dim.pref_markers
            for signal in signals
            if marker in signal
        )
        if hits:
            scored.append((-hits, index, dim))
    scored.sort()
    return [dim for _, _, dim in scored]


def rankable(dim: Dimension) -> bool:
    return dim.kind in ("numeric_higher", "numeric_lower", "ordinal", "feature")


def metric_explanation(category_code: str | None) -> str | None:
    """Transparent 'thang đo' answer: which measures the bot judges by."""
    dims = [d for d in dimensions_for(category_code) if rankable(d)]
    if not dims:
        return None
    parts = [f"{d.label} ({d.explain})" for d in dims[:4]]
    return "; ".join(parts)
