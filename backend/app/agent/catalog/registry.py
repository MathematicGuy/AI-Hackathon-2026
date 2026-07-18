"""Category registry for the 14 real dataset categories.

Codes and sheet names mirror `data/dataset/Spec_cate_gia.xlsx` (the committed
logical format). Markers are lowercase Vietnamese detection substrings (with
common no-diacritic variants) used by need detection and the agent guardrail
scope.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Category:
    code: str
    sheet_name: str
    markers: tuple[str, ...]


CATEGORIES: tuple[Category, ...] = (
    Category("38", "Tủ Lạnh", ("tủ lạnh", "tu lanh")),
    Category("36", "Máy lạnh", ("máy lạnh", "may lanh", "điều hòa", "điều hoà", "dieu hoa")),
    Category("115", "Máy giặt", ("máy giặt", "may giat")),
    Category("116", "Máy sấy quần áo", ("máy sấy quần áo", "máy sấy đồ", "may say quan ao")),
    Category("39", "Máy rửa chén", ("máy rửa chén", "máy rửa bát", "may rua chen", "may rua bat")),
    Category("40", "Tủ mát, tủ đông", ("tủ mát", "tủ đông", "tu mat", "tu dong")),
    Category("41", "Máy nước nóng", ("máy nước nóng", "bình nóng lạnh", "may nuoc nong", "binh nong lanh")),
    Category("139", "Micro karaoke", ("micro karaoke", "mic karaoke")),
    Category("137", "Micro thu âm điện thoại", ("micro thu âm", "mic thu âm", "micro thu am")),
    Category("49", "Đồng hồ thông minh", ("đồng hồ thông minh", "smartwatch", "dong ho thong minh")),
    Category("72", "Máy tính để bàn", ("máy tính để bàn", "pc", "desktop", "máy bộ", "may tinh de ban")),
    Category("73", "Màn hình máy tính", ("màn hình máy tính", "màn hình", "man hinh")),
    Category("75", "Máy in", ("máy in", "may in")),
    Category("30", "Máy tính bảng", ("máy tính bảng", "tablet", "ipad", "may tinh bang")),
)


class CategoryRegistry:
    def __init__(self, categories: tuple[Category, ...] = CATEGORIES) -> None:
        self._categories = categories
        self._by_code = {category.code: category for category in categories}

    def all(self) -> tuple[Category, ...]:
        return self._categories

    def by_code(self, code: str) -> Category:
        return self._by_code[str(code)]

    def detect(self, text: str) -> Category | None:
        low = text.lower()
        best: Category | None = None
        best_length = 0
        for category in self._categories:
            for marker in category.markers:
                if marker in low and len(marker) > best_length:
                    best = category
                    best_length = len(marker)
        return best

    def all_markers(self) -> tuple[str, ...]:
        return tuple(
            marker
            for category in self._categories
            for marker in category.markers
        )
