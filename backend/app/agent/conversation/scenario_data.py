"""Per-category cold-start scripts, ordered by material impact.

Question order encodes which feature matters most for each category and is
asked first (Cường's requirement); `purpose_followups` adds preference-aware
follow-ups once the usage purpose is known (e.g. gaming → display/GPU).
`performance_attribute` names the spec used by the deterministic
best_performance role. NEEDS DOMAIN-EXPERT REVIEW — marked provisional.
"""

SCENARIOS: dict[str, dict] = {
    "36": {  # Máy lạnh
        "questions": [
            {"key": "room_area", "ask": "Dạ anh/chị lắp máy lạnh cho phòng khoảng bao nhiêu m² ạ?"},
            {"key": "budget", "ask": "Anh/chị dự định ngân sách khoảng bao nhiêu cho máy lạnh ạ?"},
            {"key": "priority", "ask": "Anh/chị ưu tiên tiết kiệm điện, chạy êm hay làm lạnh nhanh ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Phạm vi sử dụng",
    },
    "38": {  # Tủ Lạnh
        "questions": [
            {"key": "household", "ask": "Dạ gia đình mình khoảng mấy người dùng tủ lạnh ạ (để em tư vấn dung tích phù hợp)?", "example": "nhà 2 người hay 4-5 người"},
            {"key": "budget", "ask": "Anh/chị dự định ngân sách khoảng bao nhiêu cho tủ lạnh ạ?", "example": "tầm 8-12 triệu"},
            {"key": "door_style", "ask": "Anh/chị thích kiểu ngăn đá trên, ngăn đá dưới hay side by side ạ?", "example": "ngăn đá trên gọn giá tốt, side by side rộng cho nhà đông người"},
        ],
        "purpose_followups": {},
        "purpose_example": "trữ đông thực phẩm nhiều hay chủ yếu để thức ăn dùng trong ngày",
        "performance_attribute": "Dung tích sử dụng",
    },
    "115": {  # Máy giặt
        "questions": [
            {"key": "load", "ask": "Dạ nhà mình mấy người để em tư vấn khối lượng giặt phù hợp ạ?", "example": "nhà 2 người tầm 8kg, 4-5 người tầm 9-10kg"},
            {"key": "door", "ask": "Anh/chị thích máy giặt cửa trước (giặt êm, tiết kiệm nước) hay cửa trên (giá tốt, dễ dùng) ạ?", "example": "cửa trước giặt êm, cửa trên giá tốt"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?", "example": "tầm 6-10 triệu"},
        ],
        "purpose_followups": {},
        # Real data: Máy giặt rows carry no spec columns (mirror + prices
        # only) — performance role is skipped with disclosure.
        "performance_attribute": None,
    },
    "116": {  # Máy sấy quần áo
        "questions": [
            {"key": "load", "ask": "Dạ mỗi lần anh/chị cần sấy khoảng bao nhiêu kg đồ ạ?"},
            {"key": "type", "ask": "Anh/chị muốn máy sấy thông hơi (giá tốt) hay ngưng tụ/bơm nhiệt (bảo vệ vải, tiết kiệm điện) ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Khối lượng tải chính",
    },
    "39": {  # Máy rửa chén
        "questions": [
            {"key": "capacity", "ask": "Dạ gia đình mình mấy người để em tư vấn số bộ chén phù hợp ạ?"},
            {"key": "install", "ask": "Anh/chị cần máy độc lập hay lắp âm tủ ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Công suất đầu ra",
    },
    "40": {  # Tủ mát, tủ đông
        "questions": [
            {"key": "purpose", "ask": "Dạ anh/chị dùng tủ cho kinh doanh hay gia đình ạ?"},
            {"key": "capacity", "ask": "Anh/chị cần dung tích khoảng bao nhiêu lít ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        # Real data has no reliable capacity column for this sheet.
        "performance_attribute": None,
    },
    "41": {  # Máy nước nóng
        "questions": [
            {"key": "type", "ask": "Dạ anh/chị cần máy nước nóng trực tiếp (gọn, dùng ngay) hay gián tiếp (nhiều người dùng) ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Công suất đầu ra",
    },
    "139": {  # Micro karaoke
        "questions": [
            {"key": "setup", "ask": "Dạ anh/chị hát với loa kéo, dàn karaoke hay loa bluetooth ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": None,
    },
    "137": {  # Micro thu âm điện thoại
        "questions": [
            {"key": "purpose", "ask": "Dạ anh/chị thu âm để livestream, quay video hay hát ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": None,
    },
    "49": {  # Đồng hồ thông minh
        "questions": [
            {"key": "phone_os", "ask": "Dạ anh/chị đang dùng iPhone hay điện thoại Android ạ (để em chọn đồng hồ tương thích)?"},
            {"key": "purpose", "ask": "Anh/chị đeo chủ yếu để theo dõi sức khỏe, thể thao hay nghe gọi ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {
            "thể thao": [{"key": "sport_gps", "ask": "Anh/chị có cần GPS và chống nước khi chạy bộ/bơi không ạ?"}],
        },
        # Real data exposes charge time / face size, not battery life.
        "performance_attribute": None,
    },
    "72": {  # Máy tính để bàn
        "questions": [
            {"key": "purpose", "ask": "Dạ anh/chị dùng máy tính chủ yếu cho văn phòng, gaming hay đồ họa ạ?", "example": "văn phòng, chơi game hay dựng video"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?", "example": "tầm 15-20 triệu"},
        ],
        "purpose_followups": {
            # "gam" matches BOTH "gaming" and "chơi game" ("game" is not a
            # substring of "gaming") — the live transcript's "anh chơi game
            # FPS" must trigger the gaming follow-ups.
            "gam": [
                {"key": "gaming_display", "ask": "Anh/chị đã có màn hình chưa, và có cần màn tần số quét cao để chơi game mượt không ạ?"},
                {"key": "gaming_titles", "ask": "Anh/chị hay chơi tựa game nào để em cân card đồ họa phù hợp ạ?"},
            ],
            "đồ họa": [
                {"key": "graphics_apps", "ask": "Anh/chị dùng phần mềm đồ họa nào (Photoshop, Premiere, 3D...) để em tư vấn cấu hình ạ?"},
            ],
        },
        "purpose_example": "văn phòng nhẹ nhàng, chơi game hay làm đồ họa",
        "performance_attribute": "RAM",
    },
    "73": {  # Màn hình máy tính
        "questions": [
            {"key": "size", "ask": "Dạ anh/chị muốn màn hình khoảng bao nhiêu inch ạ?"},
            {"key": "purpose", "ask": "Anh/chị dùng màn hình cho văn phòng, gaming hay đồ họa ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {
            "gaming": [{"key": "refresh", "ask": "Anh/chị có cần tần số quét cao (144Hz trở lên) để chơi game không ạ?"}],
        },
        "performance_attribute": "Kích thước màn hình",
    },
    "75": {  # Máy in
        "questions": [
            {"key": "color", "ask": "Dạ anh/chị cần in màu hay chỉ in đen trắng ạ?"},
            {"key": "volume", "ask": "Anh/chị in cho gia đình hay văn phòng (số lượng nhiều) ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Tốc độ in",
    },
    "30": {  # Máy tính bảng
        "questions": [
            {"key": "purpose", "ask": "Dạ anh/chị mua máy tính bảng cho bé học, giải trí hay làm việc/vẽ ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {
            "vẽ": [{"key": "stylus", "ask": "Anh/chị có cần bút cảm ứng đi kèm để vẽ/ghi chú không ạ?"}],
            "học": [{"key": "kid", "ask": "Bé nhà mình học online nhiều không ạ, để em ưu tiên máy pin khỏe màn lớn?"}],
        },
        "performance_attribute": "RAM",
    },
}
