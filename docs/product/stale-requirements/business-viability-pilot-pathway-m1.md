# Chỉ số kinh doanh, giả thuyết khả thi và lộ trình Pilot — Milestone 1

> **Trạng thái:** Baseline bổ sung (additive) — không thay đổi hành vi trong
> product contract đã freeze.
> **Phạm vi:** Trợ lý tư vấn máy lạnh M1 là lát cắt dọc đầu tiên; đề bài đối
> tác bao trùm mọi ngành hàng Điện Máy Xanh (điện thoại, tai nghe, máy lạnh,
> tủ lạnh, laptop, robot).
> **Nguồn:** `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md`
> (D1/D3/E/F/H2), `PROJECT_MANAGEMENT.md` §5,
> `docs/product/air-conditioner-advisor-m1-contract.md`.
> **Ngôn ngữ:** Tiếng Việt — tài liệu này là deliverable hướng ban giám khảo
> và đối tác doanh nghiệp.

## 1. KPI kinh doanh đo được

Mỗi Outcome trong đề bài (mục D1) được gắn với chỉ số đo được. Chỉ số kỹ
thuật lấy từ release gate M1.9 (Langfuse, bộ 26 case); chỉ số kinh doanh đo
trong pilot.

| # | Outcome đề bài (D1) | Chỉ số | Cách đo | Mục tiêu |
|---|---|---|---|---|
| 1 | Hiểu đúng nhu cầu thật từ tiếng Việt tự nhiên | Intent accuracy; need-extraction correctness | Bộ eval 26 case qua Langfuse | ≥ 0.90 |
| 2 | Biết hỏi ngược khi thiếu thông tin | Clarification decision accuracy | Bộ eval + đánh giá chuyên gia ngành hàng | ≥ 0.85 |
| 3 | So sánh dễ hiểu, tập trung lợi ích thực tế | Main Selling Point relevance; tradeoff quality; next-question relevance | Chấm điểm mô hình có hiệu chuẩn + human review | ≥ 0.85 |
| 4 | Top 3 phù hợp kèm trade-off | Role-winner correctness; human helpfulness | Golden regression `AIRCON-M1-001` + bộ eval + human review | ≥ 0.90 / ≥ 0.80 |
| 5 | Không bịa thông số, giá, khuyến mãi, tồn kho | Hallucination nghiêm trọng; output schema pass; citation đầy đủ | Deterministic assertions (release blockers) | 0 vi phạm / 100% pass |

Chỉ số kinh doanh đo trong pilot (baseline lấy ở 2 tuần đầu, so sánh A/B với
trải nghiệm bộ lọc hiện có khi hạ tầng cho phép):

| Chỉ số pilot | Định nghĩa | Nguồn đo |
|---|---|---|
| Tỉ lệ hội thoại ra khuyến nghị | % hội thoại đạt tới bộ top-3 hợp lệ (proxy chuyển đổi) | Langfuse trace (`answer_type=recommendation`) |
| CTR vào trang sản phẩm | % card khuyến nghị được bấm vào | Sự kiện frontend |
| Deflection tư vấn viên | % hội thoại không cần chuyển sang nhân viên | Log kênh tư vấn của pilot |
| Time-to-decision | Số lượt hỏi và thời gian đến khuyến nghị được chấp nhận | Langfuse session |
| CSAT sau hội thoại | Khảo sát 1 câu cuối hội thoại | Frontend |
| Chi phí LLM / hội thoại | Tổng cost token Nano + DeepSeek mỗi session | Langfuse cost metrics |
| Latency | Hỏi ngược p95 ≤ 3s; khuyến nghị p95 ≤ 8s (nội bộ); đề bài yêu cầu so sánh top 3 < 5s với dữ liệu demo | Langfuse |

## 2. Giả thuyết business viability

Mỗi giả thuyết có cách kiểm chứng cụ thể trong pilot; chưa giả thuyết nào
được coi là đã chứng minh.

- **H1 — Chuyển đổi:** Tư vấn theo nhu cầu (hỏi ngược + top 3 + trade-off)
  tăng tỉ lệ bấm vào sản phẩm và thêm-vào-giỏ so với bộ lọc/bảng so sánh
  tĩnh. *Kiểm chứng:* A/B trong pilot, chỉ số CTR và tỉ lệ ra khuyến nghị.
- **H2 — Chi phí vận hành đủ thấp để scale:** Kiến trúc hybrid giữ chi phí
  biên thấp: ranking/lọc hoàn toàn deterministic (không tốn LLM); LLM chỉ
  dùng cho intent (GPT-5.4 Nano — model nhỏ) và giải thích
  (`deepseek/deepseek-v4-flash` qua OpenRouter — model chi phí thấp).
  *Kiểm chứng:* đo chi phí LLM/hội thoại thật qua Langfuse trong pilot và
  so với ngưỡng do DMX xác nhận (đề xuất khởi điểm: dưới chi phí một phút
  tư vấn của nhân viên). Giảm rủi ro anti-pattern I2 ("phụ thuộc API nước
  ngoài đắt đỏ"): mọi thành phần LLM đều thay được qua cấu hình, phần lõi
  quyết định không phụ thuộc LLM.
- **H3 — Giảm tải tư vấn viên:** Trợ lý xử lý được phần lớn câu hỏi lặp lại
  ở giờ cao điểm. *Kiểm chứng:* deflection rate và phản hồi của đội tư vấn
  trong pilot.
- **H4 — Mở rộng đa ngành hàng với chi phí giảm dần:** Phần lõi (guardrail,
  state, hỏi ngược, ranking theo vai trò, giải thích có căn cứ) tái dùng
  được; mỗi ngành hàng mới chỉ cần schema nhu cầu + quy tắc fit + ranking
  policy + bộ eval theo logic ngành ở mục H2 của đề bài. *Kiểm chứng:* thời
  gian và khối lượng code để thêm ngành hàng thứ hai (tủ lạnh) trong giai
  đoạn cuối pilot.

**Rủi ro chính:** dữ liệu catalog thực tế thiếu field/sai đơn vị (đề bài I2
yêu cầu xử lý được — normalization đã thiết kế reject-not-guess);
hallucination làm mất lòng tin đối tác (chặn bằng output guardrail + release
blocker = 0); latency vượt ngưỡng khi dùng API ngoài; phạm vi dữ liệu chỉ
được dùng trong hackathon, dữ liệu thật cần NDA (E2).

## 3. Lộ trình Pilot (theo định nghĩa D3 của đề bài)

**Phạm vi:** 1 website/app bán lẻ, nhóm ngành hàng máy lạnh; 1.000–10.000
lượt hội thoại thử nghiệm; 3 tháng, bắt đầu sau hackathon khi DMX cung cấp
dữ liệu catalog, giá, tồn kho và chính sách mẫu.

**Giai đoạn:**

| Giai đoạn | Thời gian | Nội dung | Cổng ra (gate) |
|---|---|---|---|
| 0. Chuẩn bị | Tuần 0–2 | Ký NDA; nhận data catalog/policy/scenario (E1); tích hợp API mock price/promotion/stock (E3); chạy lại release gate M1.9 trên data thật | Data validation pass; release gate pass |
| 1. Soft launch | Tuần 3–6 | Bật cho traffic nội bộ + chuyên gia ngành hàng đánh giá câu trả lời; hiệu chỉnh clarification/ranking theo phản hồi nghiệp vụ | 0 hallucination nghiêm trọng; helpfulness ≥ 0.80 theo chuyên gia |
| 2. Mở rộng | Tuần 7–12 | Mở % traffic thật tăng dần đến 1.000–10.000 hội thoại; A/B với trải nghiệm hiện có; đo đủ bộ KPI pilot ở mục 1 | KPI kỹ thuật giữ ngưỡng; KPI kinh doanh có baseline + so sánh |
| 3. Tổng kết | Cuối tháng 3 | Báo cáo go/no-go: KPI, chi phí, phản hồi, kế hoạch ngành hàng thứ hai | Quyết định mở rộng chính thức |

**Điều kiện ký hợp đồng pilot (từ D3):** demo đạt KPI độ đúng thông tin sản
phẩm; không hallucination nghiêm trọng; giao diện dễ dùng; có log nguồn dữ
liệu cho mọi claim; tích hợp được API catalog/stock/promotion.

**Phân vai (RACI rút gọn):**

| Việc | Đội dự án | Điện Máy Xanh |
|---|---|---|
| Vận hành hệ thống, sửa lỗi, đo lường | R/A | I |
| Cung cấp data sạch/anonymize, API, môi trường test | I | R/A |
| Đánh giá chất lượng câu trả lời theo ngành hàng | C | R (chuyên gia ngành hàng) |
| Quyết định go/no-go và phạm vi mở rộng | C | A |

**Yêu cầu dữ liệu và bảo mật (E1/E2):** catalog theo ngành hàng, policy &
FAQ, bộ tình huống nhu cầu khách; không lưu PII, không hiển thị giá vốn,
data demo giả lập/anonymize; log mask thông tin nhạy cảm.

**Lộ trình mở rộng đa ngành hàng (sau pilot máy lạnh):**

1. **Tủ lạnh** — tư vấn theo số người/gia đình (logic H2 của đề bài).
2. **Điện thoại** — theo camera/pin/game.
3. **Laptop** — theo loại công việc.
4. Tai nghe, robot và các ngành còn lại theo cùng khuôn: schema nhu cầu +
   quy tắc fit + ranking policy + bộ eval case riêng cho từng ngành, tái
   dùng toàn bộ lõi guardrail/state/giải thích.

## 4. Tài liệu liên quan

- Đề bài đối tác: `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md`
- Ngưỡng release kỹ thuật: `PROJECT_MANAGEMENT.md` §5 và PRD §9
- Hợp đồng sản phẩm M1: `docs/product/air-conditioner-advisor-m1-contract.md`
