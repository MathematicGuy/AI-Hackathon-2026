# JTBD — Trợ lý AI tư vấn sản phẩm theo nhu cầu thực

## 1. Project Snapshot

**Tên dự án tạm thời:** Trợ lý AI tư vấn sản phẩm thông minh  
**Nhóm:** AI Product / AI Engineering MVP  
**Lĩnh vực:** Bán lẻ điện máy và thương mại điện tử  
**Thị trường mục tiêu:** Khách hàng Việt Nam mua điện thoại, laptop, máy lạnh, tủ lạnh và các sản phẩm điện máy có nhiều thông số kỹ thuật.

### Bài toán đang giải quyết

Khách hàng không thực sự muốn “xem thêm thông số”; họ muốn biết sản phẩm nào phù hợp nhất với hoàn cảnh, ngân sách và ưu tiên sử dụng của mình. Tuy nhiên, các bộ lọc, bảng so sánh và chatbot FAQ hiện tại thường không hiểu đầy đủ nhu cầu, ít hỏi lại khi thiếu dữ kiện và chưa giải thích rõ sự đánh đổi giữa các lựa chọn.

Điều này khiến khách hàng mất nhiều thời gian tìm kiếm, khó chuyển nhu cầu đời sống thành tiêu chí kỹ thuật, thiếu tự tin khi ra quyết định và dễ từ bỏ hành trình mua sắm.

### MVP tập trung vào một AI Advisor có thể

1. Nhận yêu cầu bằng tiếng Việt tự nhiên.
2. Nhận diện nhu cầu, ngân sách, ưu tiên và ràng buộc.
3. Hỏi tối đa 2–3 câu có ảnh hưởng lớn đến quyết định.
4. Chuyển nhu cầu thành tiêu chí tìm kiếm và bộ lọc.
5. Truy xuất dữ liệu sản phẩm, giá, khuyến mãi và tồn kho.
6. Loại các sản phẩm không đáp ứng ràng buộc bắt buộc.
7. Xếp hạng sản phẩm theo mức độ phù hợp.
8. Đề xuất Top 3 và giải thích trade-off.
9. Dẫn nguồn cho thông số, giá, tồn kho và khuyến mãi.
10. Nói rõ khi dữ liệu không có thay vì tự suy đoán.

---

## 2. First-Principle JTBD

Khách hàng không “thuê” chatbot AI để đọc catalog thay họ.

Khách hàng thuê một cơ chế giúp họ:

> Chuyển nhu cầu sử dụng còn mơ hồ thành một quyết định mua hàng phù hợp, khả thi, dễ hiểu và đáng tin cậy.

Job-to-be-Done cốt lõi không phải là:

> “Tôi muốn sử dụng AI để so sánh sản phẩm.”

Mà là:

> “Tôi muốn biết sản phẩm nào thực sự phù hợp với hoàn cảnh của mình và vì sao tôi nên chọn nó.”

---

## 3. Market Context

Website Điện Máy XANH hiện đã hỗ trợ:

- Danh mục sản phẩm lớn.
- Bộ lọc theo giá, thương hiệu và thông số.
- Một số bộ lọc theo nhu cầu sử dụng.
- Tính năng so sánh sản phẩm.
- Trang chi tiết với thông số, giá, khuyến mãi, chính sách và review.
- Kiểm tra giá, tồn kho và khả năng giao hàng theo khu vực.
- Nội dung tư vấn chọn mua.
- Kênh hỗ trợ từ nhân viên bán hàng.

Tuy nhiên, khách hàng vẫn phải tự:

1. Xác định tiêu chí nào quan trọng.
2. Chuyển nhu cầu đời sống thành thông số kỹ thuật.
3. Chọn sản phẩm nào để đưa vào bảng so sánh.
4. Đánh giá mức chênh lệch giá có đáng hay không.
5. Kiểm tra sản phẩm có thực sự mua được tại khu vực của mình.
6. Tổng hợp thông tin từ thông số, review, khuyến mãi và chính sách.

### Khoảng trống sản phẩm

Website hiện mạnh ở ba lớp:

- **Information Layer:** thông số, mô tả, review và chính sách.
- **Navigation Layer:** danh mục, tìm kiếm, bộ lọc và so sánh.
- **Transaction Layer:** giá, tồn kho, giao hàng, trả góp và mua hàng.

Lớp còn thiếu là:

> **Decision Layer:** hiểu hoàn cảnh, xác định tiêu chí quan trọng, tạo shortlist và giải thích quyết định.

Đây là vị trí của giải pháp AI.

---

## 4. Job Executors

### Primary Job Executor

**Khách hàng mua sắm online**, đặc biệt là người:

- Không có kiến thức chuyên sâu về sản phẩm.
- Chỉ biết hoàn cảnh sử dụng nhưng không biết thông số cần chọn.
- Đang phân vân giữa nhiều lựa chọn tương tự.
- Có ngân sách hoặc ràng buộc rõ ràng.
- Muốn chọn nhanh nhưng vẫn cần đủ căn cứ để tin tưởng.

### Secondary Job Executors

- **Nhân viên tư vấn bán hàng:** cần giảm câu hỏi lặp lại và chuẩn hóa tư vấn.
- **Đội vận hành thương mại điện tử:** cần giảm tỷ lệ rời trang và tăng chuyển đổi.
- **Chuyên gia ngành hàng:** cần chuyển tri thức tư vấn thành logic có thể tái sử dụng.
- **Doanh nghiệp bán lẻ:** cần phục vụ lượng lớn khách hàng mà không tăng tương ứng chi phí nhân sự.

---

## 5. Core JTBD

### Dành cho khách hàng

> **Khi** tôi cần mua một sản phẩm điện máy nhưng có quá nhiều lựa chọn và không hiểu hết các thông số kỹ thuật,  
> **tôi muốn** mô tả nhu cầu bằng ngôn ngữ tự nhiên, được hỏi thêm một vài câu quan trọng và nhận ba sản phẩm phù hợp nhất,  
> **để tôi có thể** đưa ra quyết định mua hàng nhanh, tự tin và tránh chọn nhầm sản phẩm.

### Dành cho doanh nghiệp

> **Khi** khách hàng có ý định mua nhưng chưa đủ tự tin để chọn sản phẩm,  
> **doanh nghiệp muốn** tự động hóa quá trình khai thác nhu cầu, thu hẹp lựa chọn và giải thích đề xuất dựa trên dữ liệu thật,  
> **để** tăng tỷ lệ chuyển đổi, giảm tải nhân viên và chuẩn hóa chất lượng tư vấn.

---

## 6. Các loại Job

### Functional Job

- Chuyển nhu cầu đời sống thành tiêu chí lựa chọn.
- Thu hẹp hàng chục hoặc hàng trăm SKU xuống còn ba lựa chọn.
- Hiểu sản phẩm nào phù hợp nhất và vì sao.
- Biết phải đánh đổi điều gì khi chọn từng sản phẩm.
- Xác minh giá, khuyến mãi, tồn kho và chính sách.
- Tránh chọn sản phẩm không phù hợp với nhu cầu thực tế.

### Emotional Job

- Cảm thấy yên tâm rằng mình không mua sai.
- Không bị choáng ngợp bởi quá nhiều thông tin.
- Không cảm thấy bị ép mua sản phẩm đắt hơn.
- Có cảm giác kiểm soát được quyết định.
- Tin rằng lời tư vấn dựa trên nhu cầu của mình.

### Social Job

- Có thể giải thích lựa chọn với gia đình hoặc người cùng chi trả.
- Được nhìn nhận là người mua hàng hợp lý.
- Tránh bị đánh giá là mua hớ hoặc chọn sai.

### Business Job

- Tăng tỷ lệ khách hoàn thành quá trình lựa chọn.
- Giảm thời gian tư vấn trung bình.
- Giảm câu hỏi FAQ lặp lại.
- Tăng tính nhất quán giữa các nhân viên và kênh bán hàng.
- Giảm tư vấn sai hoặc đề xuất sản phẩm không còn tồn kho.
- Thu thập insight có cấu trúc về nhu cầu khách hàng.

---

## 7. Job Executor Segments

### Need-aware, Spec-unaware

Biết mình cần gì trong đời sống nhưng không biết thông số tương ứng.

> “Tôi cần máy lạnh cho phòng ngủ, ít ồn và đỡ tốn điện.”

### Option-aware, Trade-off-uncertain

Đã có hai hoặc ba sản phẩm nhưng không biết khác biệt có đáng kể không.

> “Sản phẩm A đắt hơn sản phẩm B ba triệu thì tôi nhận thêm được gì?”

### Budget-constrained Shopper

Ưu tiên ngân sách, trả góp hoặc khuyến mãi nhưng vẫn cần đáp ứng nhu cầu tối thiểu.

### Installation-sensitive Shopper

Quan tâm đến diện tích, vị trí lắp đặt, phí vật tư, thời gian giao và khả năng có hàng.

### Validation-seeking Shopper

Đã nghiêng về một sản phẩm nhưng cần xác minh bằng thông số, review và chính sách.

---

## 8. Job Stories

### Khám phá nhu cầu

**JS1.** Khi tôi mô tả nhu cầu bằng ngôn ngữ đời thường, tôi muốn hệ thống hiểu ý chính, để tôi không phải biết tên các thông số kỹ thuật.

**JS2.** Khi yêu cầu còn thiếu dữ kiện, tôi muốn hệ thống chỉ hỏi những câu thực sự làm thay đổi kết quả, để quá trình tư vấn không trở thành một bảng khảo sát dài.

**JS3.** Khi tôi chưa xác định rõ ưu tiên, tôi muốn hệ thống đưa ra các lựa chọn dễ hiểu như “tiết kiệm điện hay làm lạnh nhanh”, để tôi nhận ra điều mình thực sự cần.

### Chuyển nhu cầu thành tiêu chí

**JS4.** Khi AI đã hiểu nhu cầu, tôi muốn nó tự chuyển nhu cầu thành tiêu chí và bộ lọc phù hợp, để tôi không phải tự chọn từng thông số.

**JS5.** Khi tôi đưa ra nhiều mong muốn, tôi muốn AI phân biệt điều nào là bắt buộc và điều nào có thể đánh đổi, để không loại bỏ quá nhiều sản phẩm phù hợp.

### Tìm và thu hẹp lựa chọn

**JS6.** Khi có quá nhiều sản phẩm phù hợp sơ bộ, tôi muốn AI tự loại các sản phẩm vi phạm ngân sách hoặc ràng buộc bắt buộc.

**JS7.** Khi nhiều sản phẩm có thông số gần giống nhau, tôi muốn chúng được xếp hạng theo hoàn cảnh sử dụng của tôi, thay vì theo độ phổ biến hoặc giá cao nhất.

**JS8.** Khi không có sản phẩm đáp ứng toàn bộ yêu cầu, tôi muốn biết tiêu chí nào cần nới lỏng và kết quả sẽ thay đổi ra sao.

### So sánh và giải thích

**JS9.** Khi nhận danh sách đề xuất, tôi muốn biết rõ vì sao từng sản phẩm phù hợp, để có thể kiểm tra logic tư vấn.

**JS10.** Khi hai sản phẩm đều tốt, tôi muốn AI giải thích sự đánh đổi giữa giá, hiệu năng, độ bền và chi phí sử dụng.

**JS11.** Khi một sản phẩm đắt hơn, tôi muốn biết khoản tiền thêm đó đổi lấy lợi ích thực tế nào và có liên quan đến nhu cầu của tôi hay không.

**JS12.** Khi gặp thuật ngữ như BTU, inverter, RAM hoặc công suất tiêu thụ, tôi muốn chúng được chuyển thành tác động thực tế.

### Xác minh và quyết định

**JS13.** Khi giá, khuyến mãi và tồn kho phụ thuộc khu vực, tôi muốn chỉ nhận các sản phẩm có thể mua hoặc giao đến địa chỉ của mình.

**JS14.** Khi AI đề cập đến giá, khuyến mãi hoặc tồn kho, tôi muốn biết nguồn và thời điểm cập nhật.

**JS15.** Khi AI sử dụng review, tôi muốn phân biệt rõ đâu là thông số chính thức và đâu là trải nghiệm chủ quan.

**JS16.** Khi hệ thống không có dữ liệu, tôi muốn nó nói rõ điều chưa biết thay vì tự suy đoán.

### Tiếp tục hành động

**JS17.** Khi đã chọn được sản phẩm, tôi muốn xem chi tiết, kiểm tra cửa hàng, thêm vào giỏ hoặc liên hệ nhân viên mà không phải bắt đầu lại.

**JS18.** Khi nhân viên tiếp nhận cuộc hội thoại, họ muốn thấy bản tóm tắt nhu cầu và ràng buộc đã thu thập, để không phải hỏi lại khách hàng.

### Quyền riêng tư

**JS19.** Khi hệ thống sử dụng vị trí, lịch sử mua hoặc hành vi duyệt web để cá nhân hóa, tôi muốn biết dữ liệu nào được sử dụng và có quyền từ chối.

---

## 9. JTBD Job Map

| Job Step | Người dùng cần hoàn thành | Vai trò của AI | Outcome mong muốn |
|---|---|---|---|
| 1. Nhận biết nhu cầu | Xác định vấn đề cần giải quyết | Cho phép mô tả tự nhiên | Bắt đầu mà không cần biết thông số |
| 2. Mô tả hoàn cảnh | Cung cấp ngân sách, người dùng, không gian | Trích xuất dữ kiện chính | AI hiểu đúng ngữ cảnh |
| 3. Làm rõ | Trả lời câu hỏi quan trọng | Hỏi tối đa 2–3 câu ảnh hưởng lớn | Ít câu hỏi nhưng tăng độ chính xác |
| 4. Xác định ưu tiên | Chọn tiêu chí bắt buộc và có thể đánh đổi | Phân loại hard/soft constraints | Tránh lọc sai |
| 5. Chuyển đổi tiêu chí | Biến nhu cầu thành thông số | Map nhu cầu vào bộ lọc | Không cần hiểu kỹ thuật |
| 6. Kiểm tra khả thi | Loại sản phẩm không đáp ứng | Kiểm tra giá, tồn kho và khu vực | Chỉ giữ lựa chọn có thể mua |
| 7. Tạo shortlist | Thu hẹp xuống ba lựa chọn | Ranking theo mức độ phù hợp | Danh sách đủ nhỏ để quyết định |
| 8. So sánh | Hiểu khác biệt giữa các lựa chọn | Giải thích bằng lợi ích thực tế | So sánh dễ hiểu |
| 9. Đánh giá trade-off | Biết mình phải hy sinh điều gì | Nêu rõ “được gì – mất gì” | Quyết định có căn cứ |
| 10. Xác minh | Kiểm tra nguồn và độ mới dữ liệu | Gắn nguồn cho nhận định | Tăng độ tin cậy |
| 11. Quyết định | Chọn hoặc điều chỉnh ưu tiên | Cho phép rerank nhanh | Tự tin chọn sản phẩm |
| 12. Hành động | Mua, thêm giỏ hoặc gặp nhân viên | Chuyển toàn bộ context | Không đứt gãy hành trình |

---

## 10. Desired Outcomes

1. Giảm thời gian cần thiết để thu hẹp lựa chọn xuống còn ba sản phẩm.
2. Tăng khả năng khách hàng hiểu vì sao một sản phẩm phù hợp.
3. Giảm số lượng thông số khách hàng phải tự diễn giải.
4. Giảm khả năng đề xuất sản phẩm vi phạm ngân sách hoặc ràng buộc bắt buộc.
5. Giảm số câu hỏi làm rõ không ảnh hưởng đến kết quả.
6. Tăng độ chính xác khi xác định mục đích và hoàn cảnh sử dụng.
7. Tăng khả năng phát hiện khi dữ liệu đầu vào chưa đủ.
8. Giảm nguy cơ sử dụng giá, khuyến mãi hoặc tồn kho không có nguồn.
9. Tăng mức độ tin tưởng vào đề xuất.
10. Tăng khả năng hoàn thành bước tiếp theo trong hành trình mua hàng.
11. Giảm số trang và sản phẩm khách hàng phải mở để tự nghiên cứu.
12. Giảm số câu nhân viên cần hỏi lại khi tiếp nhận cuộc tư vấn.

---

## 11. Pain Points

### Trước khi so sánh

- Không biết phải bắt đầu bằng tiêu chí nào.
- Không biết nhu cầu thực tế tương ứng với thông số nào.
- Bộ lọc yêu cầu người dùng đã hiểu sản phẩm.
- Nội dung review dài và có thể mâu thuẫn nhau.
- Khó xác định tiêu chí bắt buộc và tiêu chí có thể đánh đổi.

### Trong khi so sánh

- Quá nhiều SKU và thông số.
- Bảng so sánh cho thấy khác biệt nhưng không giải thích khác biệt đó có quan trọng hay không.
- Không rõ sản phẩm đắt hơn có tạo ra giá trị thực tế hay không.
- Khuyến mãi và tồn kho thay đổi theo thời gian hoặc địa điểm.
- Chatbot thường trả lời chung chung.
- Người dùng phải tự tổng hợp thông tin từ nhiều trang.

### Sau khi nhận đề xuất

- Không biết lời tư vấn dựa trên dữ liệu hay do AI suy đoán.
- Không hiểu nguyên nhân sản phẩm được xếp hạng cao.
- Khó trình bày lại lựa chọn với người thân.
- Phải chuyển sang nhiều trang để kiểm tra giá và chính sách.
- Khi chuyển cho nhân viên, khách hàng phải mô tả lại nhu cầu.

---

## 12. Forces of Progress

### Push

- Tốn nhiều thời gian nghiên cứu.
- Lo mua sai sản phẩm có giá trị cao.
- Thông số kỹ thuật khó hiểu.
- Nhận nhiều lời khuyên trái chiều.
- Không muốn trao đổi dài với nhân viên.

### Pull

- Chỉ cần mô tả nhu cầu bằng ngôn ngữ tự nhiên.
- Nhận Top 3 thay vì danh sách dài.
- Có giải thích dễ hiểu và cá nhân hóa.
- Có nguồn cho dữ liệu quan trọng.
- Có thể điều chỉnh ưu tiên và nhận đề xuất mới ngay.

### Anxiety

- AI có thể bịa thông tin.
- Hệ thống có thể thiên vị sản phẩm đắt hoặc tồn kho nhiều.
- Thông tin giá và khuyến mãi có thể cũ.
- Không rõ dữ liệu cá nhân được sử dụng thế nào.
- Lời tư vấn có thể thiếu hiểu biết ngành hàng.

### Habit

- Hỏi nhân viên bán hàng.
- Tìm review trên Google, YouTube hoặc mạng xã hội.
- Chọn thương hiệu quen thuộc.
- Chọn sản phẩm bán chạy nhất.
- Mua mẫu tương tự sản phẩm cũ.

---

## 13. MVP Use Case ưu tiên

### Ngành hàng đề xuất

**Máy lạnh**, vì nhu cầu có quan hệ rõ với diện tích phòng, mức độ nắng, loại không gian, độ ồn, công suất, mức tiêu thụ điện, khu vực lắp đặt và chi phí lắp đặt.

### Prompt ví dụ

> “Tôi cần máy lạnh dưới 20 triệu cho phòng ngủ 18 m², muốn tiết kiệm điện và chạy êm.”

### Flow đề xuất

#### Bước 1 — Trích xuất nhu cầu

- Ngành hàng: máy lạnh.
- Ngân sách tối đa: 20 triệu.
- Diện tích: 18 m².
- Không gian: phòng ngủ.
- Ưu tiên: tiết kiệm điện và ít ồn.

#### Bước 2 — Phát hiện dữ kiện còn thiếu

AI chỉ hỏi các biến có thể thay đổi việc lọc hoặc xếp hạng:

1. Phòng có bị nắng trực tiếp hoặc ở tầng áp mái không?
2. Khu vực lắp đặt ở đâu để kiểm tra tồn kho và giao hàng?
3. Ưu tiên chạy êm hay giảm chi phí mua ban đầu hơn?

#### Bước 3 — Chuyển nhu cầu thành tiêu chí

- Công suất phù hợp với diện tích.
- Inverter.
- Dưới 20 triệu.
- Ưu tiên độ ồn thấp.
- Có hàng tại khu vực.
- Phù hợp với phòng ngủ.
- Có dữ liệu giá và thông số đầy đủ.

#### Bước 4 — Lọc ứng viên

Loại sản phẩm:

- Vượt ngân sách.
- Công suất không phù hợp.
- Không đáp ứng ràng buộc bắt buộc.
- Không có hàng tại khu vực nếu tồn kho là yêu cầu bắt buộc.
- Thiếu dữ liệu quan trọng để tư vấn an toàn.

#### Bước 5 — Xếp hạng Top 3

- **Phù hợp nhất tổng thể.**
- **Tiết kiệm ngân sách nhất.**
- **Ưu tiên chạy êm hoặc tiết kiệm điện nhất.**

#### Bước 6 — Giải thích

Mỗi đề xuất cần có:

- Lý do phù hợp.
- Một điểm yếu quan trọng.
- Chênh lệch với các lựa chọn còn lại.
- Giá và tồn kho có nguồn.
- Trường hợp không nên chọn.
- Link đến trang sản phẩm.

---

## 14. Phạm vi MVP

### Trong phạm vi

- Một ngành hàng ưu tiên.
- Hội thoại tiếng Việt.
- Trích xuất intent và tiêu chí.
- Tối đa 2–3 câu hỏi làm rõ.
- Truy xuất catalog mẫu.
- Hard filtering theo ràng buộc bắt buộc.
- Ranking theo mức độ phù hợp.
- So sánh tối thiểu ba sản phẩm.
- Giải thích trade-off.
- Hiển thị nguồn dữ liệu.
- Guardrail khi thiếu thông tin.
- Trace cơ bản của quá trình truy xuất và xếp hạng.
- Chuyển context sang trang sản phẩm hoặc nhân viên tư vấn.

### Ngoài phạm vi MVP

- Tự động thanh toán.
- Tư vấn toàn bộ ngành hàng cùng lúc.
- Cá nhân hóa dài hạn.
- Dynamic pricing.
- Dự đoán hành vi mua hàng.
- Nhận diện hình ảnh không gian lắp đặt.
- Voice bot hoàn chỉnh.
- Tích hợp production với toàn bộ hệ thống nội bộ.

---

## 15. Default Assumptions

- Ngân sách là giá mua tối đa, chưa bao gồm chi phí phát sinh nếu người dùng không nói rõ.
- Tiêu chí được nói là “bắt buộc” sẽ là hard constraint.
- Màu sắc, thương hiệu và thiết kế mặc định là soft preference.
- Không giả định giá, tồn kho hoặc khuyến mãi khi API không có dữ liệu.
- Khi không có sản phẩm đáp ứng toàn bộ yêu cầu, AI phải đề nghị nới lỏng một tiêu chí.
- AI không tự nâng ngân sách nếu chưa được đồng ý.
- Thông số kỹ thuật phải được chuyển thành tác động thực tế.
- Review không được trình bày như dữ kiện kỹ thuật chính thức.
- Dữ liệu vị trí chỉ được dùng khi người dùng đồng ý.
- Cần nói rõ thời điểm cập nhật giá, tồn kho và khuyến mãi khi có thể.

---

## 16. Success Signals

| Nhóm chỉ số | Mục tiêu MVP đề xuất |
|---|---|
| Hiểu nhu cầu | Trích xuất đúng ngành hàng, ngân sách và ràng buộc trong ≥ 90% tình huống test |
| Hỏi làm rõ | Không quá 3 câu trong luồng tiêu chuẩn |
| Chất lượng câu hỏi | Mỗi câu hỏi phải có khả năng thay đổi việc lọc hoặc xếp hạng |
| Chất lượng Top 3 | Chuyên gia ngành hàng đánh giá ít nhất 80% bộ đề xuất là hợp lý |
| Tính dễ hiểu | Ít nhất 80% người thử nghiệm hiểu lý do đề xuất mà không cần tra cứu thêm |
| Grounding | 100% giá, tồn kho, khuyến mãi và thông số quan trọng có nguồn |
| Hallucination nghiêm trọng | 0 trường hợp trong bộ test chính |
| Tốc độ | Phản hồi ban đầu dưới 3 giây; Top 3 dưới 5 giây |
| Khả năng hoàn thành | Người dùng chọn được một lựa chọn hoặc biết tiêu chí cần điều chỉnh |
| Tính khả thi | Tỷ lệ sản phẩm Top 3 có thể mua hoặc giao tại khu vực |
| Business signal | Tăng tỷ lệ click trang sản phẩm, thêm giỏ hoặc liên hệ tư vấn |
| Handoff | Giảm số câu nhân viên phải hỏi lại |
| Giảm quá tải | Giảm số trang hoặc sản phẩm cần mở trước quyết định |
| Tăng tự tin | Điểm tự tin sau tư vấn cao hơn trước tư vấn |

---

## 17. North Star Outcome

> **Tỷ lệ phiên tư vấn mà khách hàng đi từ nhu cầu ban đầu đến một quyết định có căn cứ hoặc một hành động mua hàng tiếp theo, mà không cần tự nghiên cứu lại từ đầu.**

---

## 18. Product Positioning

Giải pháp không nên được định vị chỉ là:

> Chatbot recommendation.

Định vị phù hợp hơn là:

> **AI Decision Intelligence Layer for E-commerce** — lớp hỗ trợ ra quyết định cho thương mại điện tử.

AI kết nối các thành phần hiện có:

- Catalog.
- Bộ lọc.
- So sánh.
- Giá.
- Khuyến mãi.
- Tồn kho.
- Review.
- Chính sách.
- Giỏ hàng.
- Nhân viên tư vấn.

---

## 19. JTBD rút gọn

> **Khách hàng không thuê AI để đọc catalog thay họ. Họ thuê AI để biến một nhu cầu đời sống thành một lựa chọn mua hàng phù hợp, khả thi và có thể giải thích được.**
