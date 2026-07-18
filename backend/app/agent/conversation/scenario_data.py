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
            {"key": "household", "ask": "Dạ gia đình mình khoảng mấy người dùng tủ lạnh ạ (để em tư vấn dung tích phù hợp)?"},
            {"key": "budget", "ask": "Anh/chị dự định ngân sách khoảng bao nhiêu cho tủ lạnh ạ?"},
            {"key": "door_style", "ask": "Anh/chị thích kiểu ngăn đá trên, ngăn đá dưới hay side by side ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Dung tích sử dụng",
    },
    "115": {  # Máy giặt
        "questions": [
            {"key": "load", "ask": "Dạ nhà mình mấy người để em tư vấn khối lượng giặt phù hợp ạ?"},
            {"key": "door", "ask": "Anh/chị thích máy giặt cửa trước (giặt êm, tiết kiệm nước) hay cửa trên (giá tốt, dễ dùng) ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Khối lượng giặt",
    },
    "116": {  # Máy sấy quần áo
        "questions": [
            {"key": "load", "ask": "Dạ mỗi lần anh/chị cần sấy khoảng bao nhiêu kg đồ ạ?"},
            {"key": "type", "ask": "Anh/chị muốn máy sấy thông hơi (giá tốt) hay ngưng tụ/bơm nhiệt (bảo vệ vải, tiết kiệm điện) ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Khối lượng sấy",
    },
    "39": {  # Máy rửa chén
        "questions": [
            {"key": "capacity", "ask": "Dạ gia đình mình mấy người để em tư vấn số bộ chén phù hợp ạ?"},
            {"key": "install", "ask": "Anh/chị cần máy độc lập hay lắp âm tủ ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Số bộ chén dĩa",
    },
    "40": {  # Tủ mát, tủ đông
        "questions": [
            {"key": "purpose", "ask": "Dạ anh/chị dùng tủ cho kinh doanh hay gia đình ạ?"},
            {"key": "capacity", "ask": "Anh/chị cần dung tích khoảng bao nhiêu lít ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Dung tích",
    },
    "41": {  # Máy nước nóng
        "questions": [
            {"key": "type", "ask": "Dạ anh/chị cần máy nước nóng trực tiếp (gọn, dùng ngay) hay gián tiếp (nhiều người dùng) ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {},
        "performance_attribute": "Công suất",
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
        "performance_attribute": "Thời gian sử dụng pin",
    },
    "72": {  # Máy tính để bàn
        "questions": [
            {"key": "purpose", "ask": "Dạ anh/chị dùng máy tính chủ yếu cho văn phòng, gaming hay đồ họa ạ?"},
            {"key": "budget", "ask": "Ngân sách anh/chị dự định khoảng bao nhiêu ạ?"},
        ],
        "purpose_followups": {
            "gaming": [
                {"key": "gaming_display", "ask": "Anh/chị đã có màn hình chưa, và có cần màn tần số quét cao để chơi game mượt không ạ?"},
                {"key": "gaming_titles", "ask": "Anh/chị hay chơi tựa game nào để em cân card đồ họa phù hợp ạ?"},
            ],
            "đồ họa": [
                {"key": "graphics_apps", "ask": "Anh/chị dùng phần mềm đồ họa nào (Photoshop, Premiere, 3D...) để em tư vấn cấu hình ạ?"},
            ],
        },
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
        "performance_attribute": "Tần số quét",
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
