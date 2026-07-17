# Vietnam Innovation Challenge 2026
**Đà Nẵng · 17–19 tháng 7 năm 2026**

## ĐỀ BÀI CHO ĐỐI TÁC DOANH NGHIỆP
### Enterprise Problem Brief Submission Template

📌 **Hướng dẫn sử dụng:** Điền đầy đủ các trường được tô vàng. Các trường để trống hoặc điền "N/A" có thể ảnh hưởng đến chất lượng giải pháp mà các đội thi đề xuất. Hạn nộp: vui lòng xác nhận với ban tổ chức.

---

### PHẦN A — THÔNG TIN ĐỐI TÁC / PARTNER INFORMATION

| Trường thông tin | Nội dung |
| :--- | :--- |
| **Tên tổ chức / Organization** | CÔNG TY CỔ PHẦN ĐẦU TƯ ĐIỆN MÁY XANH *(Ghi tên chính thức như trên giấy phép đăng ký)* |
| **Ngành / Sector** | Bán lẻ |
| **Người liên hệ / Point of Contact** | Phạm Duy Tùng — Trưởng phòng RD |
| **Website / LinkedIn** | [dienmayxanh.com](https://www.dienmayxanh.com) |

---

### PHẦN B — TRACK THAM GIA / CHALLENGE TRACK
*Chọn track phù hợp với bài toán của bạn (chọn 1):*

- [ ] 🏥 Y Tế & Sức Khỏe
- [ ] 🎓 Giáo Dục & Đào Tạo
- [ ] 🌪 Phòng Chống Thiên Tai
- [ ] 💡 Đổi Mới Sáng Tạo
- [x] 🏢 Năng Suất SME
- [ ] 🏛 Chính Phủ Thông Minh
- [ ] 🌾 Nông Nghiệp
- [ ] Khác / Other: ______

---

### PHẦN C — MÔ TẢ BÀI TOÁN / PROBLEM STATEMENT

#### C1. Tên bài toán / Problem Title
*Viết ngắn gọn, rõ ràng — đây là tên sẽ hiển thị trên nền tảng hackathon và truyền thông*

*   **[Tiếng Việt]:** Trợ lý AI so sánh và tư vấn sản phẩm theo nhu cầu thật của khách hàng
*   **[English]:** AI Product Comparison Advisor Based on Real Customer Needs

#### C2. Bối cảnh & Vấn đề / Context & Problem Background
*Mô tả tình trạng hiện tại: ai đang gặp khó khăn, tần suất xảy ra, quy mô ảnh hưởng. Tối thiểu 150 từ.*

##### Bối cảnh hiện tại
Khi mua các sản phẩm như điện thoại, tai nghe, máy lạnh, tủ lạnh hoặc laptop, khách hàng thường không chỉ cần xem thông số kỹ thuật. Họ cần biết sản phẩm nào thật sự phù hợp với hoàn cảnh sử dụng của mình: ngân sách bao nhiêu, dùng cho ai, không gian như thế nào, ưu tiên tiết kiệm điện hay hiệu năng, cần bền hay cần đẹp, muốn trả góp hay săn khuyến mãi. Tuy nhiên, phần lớn hệ thống so sánh sản phẩm hiện nay chỉ liệt kê thông số cạnh nhau như công suất, dung tích, RAM, bộ nhớ, kích thước, giá bán hoặc thương hiệu. Cách này khiến khách hàng phổ thông khó hiểu và khó ra quyết định.

##### Ai đang gặp vấn đề này? (đối tượng bị ảnh hưởng)
Khách hàng mua sắm online, nhân viên tư vấn bán hàng, đội vận hành thương mại điện tử và doanh nghiệp bán lẻ có nhiều SKU đều bị ảnh hưởng. Khách hàng mất nhiều thời gian để chọn sản phẩm; nhân viên phải trả lời lặp lại các câu hỏi giống nhau; doanh nghiệp khó chuyển đổi traffic thành đơn hàng nếu trải nghiệm tư vấn không đủ tốt.

##### Quy mô / tần suất xảy ra
Vấn đề xảy ra hằng ngày trên các website, app thương mại điện tử, fanpage và kênh tư vấn sản phẩm. Với các ngành hàng có nhiều thông số như điện máy, điện thoại, laptop, máy lạnh, tủ lạnh, chỉ một khác biệt nhỏ về nhu cầu sử dụng cũng có thể làm thay đổi khuyến nghị sản phẩm.

##### Đã có giải pháp nào cho vấn đề này trên thị trường mà a/c biết chưa, nếu có thì nhược điểm của các giải pháp đó là gì
Các website hiện nay thường có bộ lọc, bảng so sánh thông số, chatbot FAQ hoặc công cụ recommendation cơ bản. Nhược điểm là chúng ít hỏi ngược để hiểu nhu cầu thật, ít giải thích trade-off, không luôn gắn với tồn kho/khuyến mãi thực tế và thường trình bày bằng ngôn ngữ kỹ thuật khó hiểu với khách phổ thông.

##### Hiện tại tổ chức đang xử lý vấn đề này như thế nào?
Doanh nghiệp thường dựa vào bộ lọc sản phẩm, nội dung mô tả, review, nhân viên tư vấn và chatbot trả lời kịch bản. Cách làm này vẫn phụ thuộc nhiều vào kinh nghiệm người bán, khó scale vào giờ cao điểm và chưa cá nhân hóa tốt theo ngữ cảnh mua hàng.

##### Điều gì khiến đây là thời điểm phù hợp để giải bằng AI?
AI ngôn ngữ tự nhiên và RAG có thể hiểu câu hỏi tiếng Việt, hỏi thêm thông tin còn thiếu, truy xuất catalog/giá/tồn kho/review/chính sách, rồi giải thích lựa chọn bằng ngôn ngữ dễ hiểu. Đây là bài toán phù hợp để AI tạo giá trị thương mại trực tiếp: giảm tải tư vấn, tăng trải nghiệm khách hàng và hỗ trợ tăng tỷ lệ chuyển đổi.

#### C3. Câu hỏi trọng tâm / Core Challenge Question
*Diễn đạt bài toán dưới dạng câu hỏi 'Làm thế nào để…' giúp các đội thi hiểu đúng trọng tâm cần giải quyết*

> **Làm thế nào để xây dựng một trợ lý AI có thể hiểu nhu cầu thật của khách hàng, chủ động hỏi thêm thông tin còn thiếu và so sánh sản phẩm theo ngôn ngữ dễ hiểu, thay vì chỉ liệt kê thông số kỹ thuật?**

---

### PHẦN D — KẾT QUẢ MONG ĐỢI / EXPECTED OUTCOMES

#### D1. Kết quả mong đợi / Expected Outcome
*Một giải pháp 'tốt' trông như thế nào? Hãy cụ thể — tránh dùng từ ngữ chung chung*

| # | Kết quả / Outcome | Có thể đo lường bằng |
|---|-------------------|----------------------|
| **1** | Hiểu đúng nhu cầu thật của khách hàng từ mô tả tự nhiên bằng tiếng Việt. | Bộ test tình huống khách hàng; tỉ lệ phân loại đúng nhu cầu, ngân sách, ưu tiên và ràng buộc. |
| **2** | Biết hỏi ngược các câu quan trọng khi thông tin đầu vào chưa đủ. | Demo hội thoại; số câu hỏi làm rõ phù hợp; đánh giá từ chuyên gia ngành hàng. |
| **3** | So sánh được nhiều sản phẩm bằng ngôn ngữ dễ hiểu, tập trung vào lợi ích thực tế thay vì chỉ liệt kê thông số. | Bài test so sánh sản phẩm; điểm đánh giá chất lượng giải thích và độ dễ hiểu. |
| **4** | Đề xuất top 3 sản phẩm phù hợp nhất, có giải thích trade-off giữa các lựa chọn. | Độ phù hợp của top 3; kiểm tra lý do đề xuất; khả năng giải thích ưu/nhược điểm. |
| **5** | Không bịa thông số, giá bán, khuyến mãi hoặc tồn kho; mọi thông tin phải dựa trên dữ liệu được cung cấp. | Tỷ lệ hallucination; kiểm tra đối chiếu với catalog/giá/tồn kho; log nguồn dữ liệu. |

#### D2. Deliverables tối thiểu / Minimum Deliverables
*Giải pháp cần đạt được gì sau 48 giờ để được chấm điểm?*

*   [x] Prototype chatbot web có thể demo được (live URL hoặc video).
*   [x] Code repository public GitHub.
*   [x] Kiến trúc AI có thể giải thích được: RAG/catalog retrieval, product ranking, guardrail chống bịa thông tin.
*   [x] Lộ trình pilot / triển khai thực tế 1–2 trang.
*   [x] Khác: dữ liệu catalog mẫu, flow hỏi ngược khách hàng, so sánh tối thiểu 3 sản phẩm, đề xuất top 3 kèm trade-off.

#### D3. Định nghĩa 'Pilot Pathway' / Pilot Pathway Definition
*Nếu một đội thắng giải, cơ hội triển khai thực tế tại tổ chức của bạn trông như thế nào?*

*   **Quy mô pilot:** 1 website/app bán lẻ hoặc 1 nhóm ngành hàng thử nghiệm như máy lạnh, tủ lạnh, điện thoại, tivi hoặc laptop; 1.000–10.000 lượt hội thoại thử nghiệm.
*   **Thời gian thử nghiệm:** 3 tháng, bắt đầu sau hackathon khi có dữ liệu catalog, giá, tồn kho và chính sách mẫu.
*   **Cam kết từ tổ chức:** Cung cấp dữ liệu sản phẩm đã làm sạch/anonymize, chuyên gia ngành hàng hỗ trợ đánh giá câu trả lời, môi trường test và phản hồi nghiệp vụ.
*   **Điều kiện để ký hợp đồng pilot:** Demo đạt KPI về độ đúng thông tin sản phẩm, không hallucination nghiêm trọng, giao diện dễ dùng, có log nguồn dữ liệu và có khả năng tích hợp API catalog/stock/promotion.

---

### PHẦN E — DỮ LIỆU & TÀI NGUYÊN / DATA & RESOURCES

#### E1. Dữ liệu được cung cấp / Available Data
*Mô tả chi tiết dữ liệu bạn cung cấp để các đội thi xây dựng giải pháp*

| Tên dataset | Mô tả nội dung | Định dạng | Cách truy cập |
| :--- | :--- | :--- | :--- |
| **Product Catalog** | Danh sách sản phẩm theo ngành hàng: điện thoại, tai nghe, máy lạnh, tủ lạnh, laptop, robot; gồm tên, brand, category, thông số, ảnh, mô tả. | CSV / JSON / API | Link / Trực tiếp / NDA |
| **Policy & FAQ** | Chính sách bảo hành, trả góp, giao hàng, lắp đặt, đổi trả và các FAQ tư vấn phổ biến. | DOC / Markdown / JSON | Trực tiếp / NDA |
| **Customer Need Scenarios** | Bộ tình huống nhu cầu khách hàng mẫu | CSV / JSONL | Link / Trực tiếp / NDA |

#### E2. Giới hạn & Điều kiện dữ liệu / Data Constraints

*   **Giới hạn:** Dữ liệu có được sử dụng sau hackathon không?
    *   [x] Chỉ trong hackathon
    *   [ ] Có
    *   [x] Cần NDA nếu dùng dữ liệu thật
*   **Dữ liệu có thông tin cá nhân (PII) không?**
    *   [x] Không đối với dữ liệu demo
    *   [ ] Có, đã anonymize
    *   [ ] Có, cần thỏa thuận
*   **Yêu cầu bảo mật đặc biệt:** Không lưu raw dữ liệu khách hàng thật; không hiển thị thông tin nội bộ về giá vốn; mọi dữ liệu demo nên được giả lập hoặc anonymize.

#### E3. Tài nguyên khác / Additional Resources
*   **API nội bộ (ghi rõ tên & endpoint):** API mock catalog, price, promotion, stock, review; endpoint chi tiết cung cấp khi thi.
*   **Tài liệu nghiệp vụ / SOP / quy trình nội bộ:** chính sách tư vấn, bảo hành, trả góp, giao hàng, lắp đặt, đổi trả.
*   **Ngân sách cloud credits cho đội thắng:** N/A.
*   **Chuyên gia domain sẵn sàng hỗ trợ trong 48h:** chuyên gia ngành hàng điện máy/điện thoại và đại diện đội thương mại điện tử.

---

### PHẦN F — TIÊU CHÍ CHẤM ĐIỂM TRACK / JUDGING CRITERIA

*Ban tổ chức đã có rubric chung (Problem Relevance 20%, AI-Native Architecture 20%, Technical Execution 15%, Deployment 15%, Feasibility 15%, Startup Potential 15%). Phần này để bổ sung tiêu chí đặc thù của track (e.g: workflow integration, multilingual support, human-in-the-loop design, etc.)*

| Tiêu chí đặc thù của track / Custom Criterion | Mô tả / Description | Trọng số (%) |
| :--- | :--- | :---: |
| **Hiểu nhu cầu & hỏi ngược thông minh** | AI phải nhận diện đúng nhu cầu, ngân sách, ràng buộc sử dụng và biết hỏi thêm khi thiếu thông tin quan trọng. | 10% |
| **So sánh sản phẩm có giải thích trade-off** | Không chỉ liệt kê thông số; phải giải thích bằng ngôn ngữ khách hàng phổ thông, nêu rõ ưu/nhược điểm giữa các lựa chọn. | 10% |
| **Tính đúng dữ liệu & chống hallucination** | Thông số, giá, tồn kho, khuyến mãi phải có nguồn từ catalog/API; có guardrail khi dữ liệu không có hoặc không chắc chắn. | 10% |
| **Tổng cộng** | | **30%** |

---

### PHẦN G — CAM KẾT TỪ ĐỐI TÁC / PARTNER COMMITMENTS
*Các cam kết này giúp các đội thi nhận được hỗ trợ tốt nhất và tăng khả năng triển khai thực tế sau hackathon.*

---

### PHẦN H — YÊU CẦU KỸ THUẬT / TECHNICAL REQUIREMENTS
*Điền các yêu cầu kỹ thuật mà giải pháp BẮT BUỘC phải đáp ứng. Chỉ ghi những gì thực sự cần — càng ít ràng buộc, các đội càng sáng tạo hơn.*

#### H1. Ngôn ngữ / Language Requirements
*Giải pháp cần hỗ trợ ngôn ngữ nào? Mức độ yêu cầu ra sao?*

| Ngôn ngữ / Language | Mức độ / Level | Ghi chú / Notes |
| :--- | :--- | :--- |
| **Tiếng Việt** | Bắt buộc | Hỗ trợ tiếng Việt tự nhiên, có dấu/không dấu, văn nói, viết tắt và ngôn ngữ mua sắm phổ thông. |
| **Ngôn ngữ địa phương khác** | Tùy chọn | Không bắt buộc. |
| **Đa ngôn ngữ đồng thời** | Ưu tiên | Ưu tiên xử lý code-switching Việt-Anh trong tên sản phẩm, thông số và review. |

*   **Yêu cầu xử lý ngôn ngữ đặc thù khác:** Hiểu tiếng Việt mua sắm thực tế, có thể có lỗi chính tả, viết tắt, từ địa phương, đơn vị đo như m², HP, BTU, GB, lít, inch; giải thích thông số kỹ thuật bằng ngôn ngữ dễ hiểu cho khách hàng phổ thông.

#### H2. Context địa phương / Local Context Requirements
*Giải pháp cần 'hiểu' gì về bối cảnh tại Việt Nam, khu vực Đông Nam Á hoặc địa phương cụ thể để hoạt động đúng?*

| Yêu cầu context / Context Requirement | Bắt buộc | Mô tả cụ thể / Details |
| :--- | :---: | :--- |
| **Hiểu văn hóa / phong tục địa phương** | Có | Hiểu cách giao tiếp lịch sự, tư vấn gần gũi trong tiếng Việt; tránh gây cảm giác ép mua hoặc phóng đại quá mức. |
| **Tuân thủ quy định pháp lý** | Có | Không yêu cầu pháp lý chuyên sâu; cần tuân thủ bảo vệ dữ liệu khách hàng nếu dùng dữ liệu thật. |
| **Hiểu đặc thù hành chính / địa lý** | Ưu tiên | Ưu tiên hiểu khu vực/cửa hàng để kiểm tra tồn kho và giao/lắp đặt nếu có dữ liệu. |
| **Xử lý dữ liệu thị trường** | Có | Bắt buộc hiểu tiền tệ VND, giá khuyến mãi, trả góp, đơn vị đo sản phẩm, đặc thù điện máy/điện thoại tại Việt Nam. |
| **Tích hợp hệ thống hành chính có sẵn** | Không | Không bắt buộc tích hợp hệ thống hành chính. |
| **Yêu cầu context đặc thù khác** | Có | Hiểu logic tư vấn theo ngành hàng: máy lạnh theo diện tích/phòng nắng/độ ồn; tủ lạnh theo số người; điện thoại theo camera/pin/game; laptop theo công việc. |

#### H3. Yêu cầu hạ tầng & hiệu năng / Infrastructure & Performance

*   **Môi trường triển khai:**
    *   [ ] Cloud (AWS/GCP/Azure)
    *   [x] On-premise
    *   [ ] Edge/thiết bị
    *   [ ] Không yêu cầu cụ thể
*   **Kết nối internet:**
    *   [x] Bắt buộc có internet cho demo web/API
    *   [ ] Phải hoạt động offline
    *   [ ] Cả hai tùy ngữ cảnh
*   **Thiết bị người dùng cuối:**
    *   [x] Web browser
    *   [ ] Mobile app
    *   [ ] Desktop
    *   [ ] Không yêu cầu cụ thể
*   **Yêu cầu tốc độ phản hồi:** Phản hồi gợi ý/hỏi ngược trong < 3 giây với dữ liệu demo; so sánh top 3 sản phẩm trong < 5 giây.
*   **Bảo mật & quyền riêng tư:** Không lưu dữ liệu khách hàng thật nếu chưa được phép; log cần mask thông tin nhạy cảm; không bịa dữ liệu nếu API/catalog không có.
*   **API / hệ thống cần tích hợp:** Price API, Promotion API hoặc dữ liệu mock tương đương.
*   **Ngôn ngữ lập trình / Framework:** Không yêu cầu cụ thể; ưu tiên giải pháp có kiến trúc rõ, dễ chạy lại và có thể triển khai thực tế.

---

### PHẦN I — KỲ VỌNG VỀ GIẢI PHÁP TỐT / WHAT A GREAT SOLUTION LOOKS LIKE
*Phần này giúp các đội thi hiểu được 'tầm nhìn' của bạn — không phải để giới hạn sáng tạo, mà để họ biết hướng đến đúng đích. Càng cụ thể càng tốt.*

#### I1. Mô tả giải pháp lý tưởng / Ideal Solution Description
*Nếu có một giải pháp hoàn hảo sau 48 giờ, nó trông như thế nào? Mô tả bằng ngôn ngữ người dùng cuối.*

Một khách hàng vào website bán lẻ và hỏi: *“Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m², tiết kiệm điện, ít ồn.”*

Thay vì trả lời ngay bằng danh sách sản phẩm khô khan, AI hỏi thêm vài câu quan trọng: phòng ngủ hay phòng khách, có bị nắng trực tiếp không, khu vực lắp đặt ở đâu, ưu tiên chạy êm hay làm lạnh nhanh, có muốn trả góp hoặc khuyến mãi không.

Sau khi đủ thông tin, AI truy xuất catalog, giá, khuyến mãi, tồn kho và review. AI đề xuất top 3 sản phẩm phù hợp nhất, giải thích bằng ngôn ngữ dễ hiểu: sản phẩm nào chạy êm hơn cho phòng ngủ, sản phẩm nào tiết kiệm điện hơn, sản phẩm nào giá tốt hơn, sản phẩm nào không nên chọn vì công suất thấp hoặc không phù hợp với phòng nhiều nắng. Đặc biệt là không dùng các thuật ngữ marketing cho khách hàng, dùng ngôn ngữ, cách diễn đạt bình dân để khách hàng hiểu.

Mỗi đề xuất đều có lý do, điểm đánh đổi và nguồn dữ liệu. Nếu không có thông tin về giá, tồn kho hoặc khuyến mãi, AI phải nói rõ là chưa có dữ liệu thay vì tự bịa. Giải pháp lý tưởng giúp khách ra quyết định nhanh hơn, giảm tải cho nhân viên tư vấn và tăng khả năng chuyển đổi trên kênh online.

#### I2. Điều bạn KHÔNG muốn thấy / Anti-patterns to Avoid
*Liệt kê những giải pháp sẽ không được đánh giá cao dù kỹ thuật tốt — giúp đội thi không đi sai hướng*

*   [x] Giải pháp chỉ chạy được với dữ liệu sạch / lý tưởng, không xử lý được dữ liệu sản phẩm thực tế, thiếu field, sai đơn vị hoặc mô tả không đồng nhất.
*   [x] Sản phẩm yêu cầu người dùng cuối phải có kỹ năng kỹ thuật cao hoặc bắt khách tự hiểu bảng thông số phức tạp.
*   [x] Giải pháp phụ thuộc hoàn toàn vào API nước ngoài không ổn định hoặc quá đắt để scale trong môi trường bán lẻ lớn.
*   [x] Demo chỉ là mockup / slideshow, không có AI thực sự truy xuất catalog, so sánh và sinh tư vấn phía sau.
*   [x] Không có kế hoạch triển khai thực tế, không có cơ chế tích hợp catalog/giá/tồn kho/review.
*   [x] Khác: chatbot trả lời chung chung, sản phẩm nào cũng nói tốt, bịa giá/tồn kho/khuyến mãi, không hỏi lại khi thiếu thông tin quan trọng.

#### I3. Ví dụ giải pháp truyền cảm hứng / Inspirational Examples
*Chia sẻ 1–3 sản phẩm / dự án (trong nước hoặc quốc tế) mà bạn thấy đang đi đúng hướng — không cần là giải pháp y hệt, chỉ cần gợi đúng spirit*

| Tên sản phẩm / dự án | Tại sao bạn thích / What you like about it | Link (nếu có) |
| :--- | :--- | :--- |
| **Website bán lẻ có bộ lọc & so sánh sản phẩm** | Có dữ liệu catalog, giá, khuyến mãi, tồn kho và review; là nền tốt để AI nâng cấp thành tư vấn theo nhu cầu. | N/A |
| **Chatbot thương mại điện tử** | Cho thấy khách hàng quen tương tác dạng hội thoại, nhưng cần nâng cấp từ FAQ sang tư vấn có dữ liệu và có giải thích. | N/A |
| **Product recommendation engine** | Gợi ý sản phẩm theo hành vi và dữ liệu, nhưng cần thêm khả năng hỏi-ngược, giải thích trade-off và hội thoại tự nhiên. | N/A |
