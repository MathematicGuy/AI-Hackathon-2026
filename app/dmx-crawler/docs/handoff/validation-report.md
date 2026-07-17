# Báo cáo kiểm chứng

Ngày tổng hợp: 2026-07-17

## Kết luận

Bản hiện tại đã có bằng chứng cho syntax check, 32 unit tests, Docker static checks và một live smoke test giới hạn ở một sản phẩm Tivi tại TP.HCM. Việc tổng hợp báo cáo không chạy thêm crawler, không sửa source, không commit và không push.

## 32 unit tests đã pass

Command đã chạy:

~~~bash
python -m unittest discover -s tests -v
~~~

Kết quả:

~~~text
Ran 32 tests
OK
~~~

Các nhóm hành vi được bao phủ:

- Parse giá VND ở dạng hiển thị, số JSON và hậu tố rút gọn.
- Parse số lượng đã bán, gồm dấu thập phân và hậu tố nghìn/triệu.
- Parse thông số kỹ thuật từ HTML và dữ liệu có cấu trúc.
- Chuẩn hóa URL, bỏ tracking, canonicalization và hash fallback.
- So sánh location theo mã/tên chuẩn hóa.
- Dedupe theo source product key và canonical URL hash.
- SCD2 cho content và location, gồm trường hợp payload không đổi.
- Discovery qua sitemap và fallback category fixture.
- HTTP retry, backoff/challenge classification.
- Session isolation giữa location.
- Location mismatch không ghi snapshot.
- Parser/adapter với fixture category, product và delivery.

Toàn bộ unit test là offline; fixture được lưu có chủ đích trong tests/fixtures.

## Syntax check

Command đã chạy:

~~~bash
python -m compileall -q dmx_crawler tests scripts
~~~

Kết quả: không có syntax error. Lần kiểm tra package ghi nhận 15 file Python trong dmx_crawler được compile thành công.

Ngoài compileall, các module được import trong quá trình chạy unit test và CLI smoke, cung cấp thêm bằng chứng rằng dependency/import graph chính hoạt động trong môi trường phiên.

## Docker checks

Hai static check đã chạy:

~~~bash
docker compose config --quiet
docker build --check .
~~~

Kết quả:

- docker compose config --quiet: pass.
- docker build --check .: pass, không có cảnh báo được ghi nhận.
- Compose không tự khởi động live crawl.
- Chưa thực hiện docker compose build đầy đủ, chưa kéo/cài image end-to-end và chưa chạy service bằng container.

Do đó trạng thái Docker là cấu hình hợp lệ ở mức static, không phải xác nhận production deployment.

## Live smoke test

### Phạm vi

- Một danh mục: Tivi.
- Một sản phẩm.
- Một location: TP.HCM.
- Request interval tối thiểu được giữ ở mức cấu hình tuân thủ.
- Discovery, crawl common và crawl location được chạy tuần tự.
- Database tạm được dùng để đối chiếu và không được giữ lại trong repository.

### Kết quả

| Hạng mục | Kết quả |
| --- | --- |
| Discovery category, limit 1 | Thành công, phát hiện 1 URL |
| Common product crawl | Thành công, ghi 1 content version |
| Parse tên/thương hiệu/giá | Thành công |
| Location session isolation | Thành công cho location được thử |
| Location evidence comparison | Khớp |
| Location snapshot | Ghi 1 version |
| Stock status quan sát | out_of_stock |
| CAPTCHA/challenge bypass | Không thực hiện |
| Phát hiện block trong smoke cuối | Không |
| Dữ liệu thử tạm | Đã loại bỏ sau kiểm tra |

Trước lần smoke thành công, challenge detector từng coi dấu vết reCAPTCHA thụ động trên trang bình thường là block. Điều kiện đã được thu hẹp để chỉ dừng khi có tín hiệu challenge thực sự; regression test liên quan đã pass.

## Đối chiếu nội dung file

Workspace hiện không phải Git worktree, nên git diff thông thường không thể cung cấp working-tree diff. Khi cần xác nhận file mới, chế độ git diff --no-index được dùng để đọc diff mà không commit hoặc thay đổi metadata repository.

Ba tài liệu handoff được kiểm tra theo các tiêu chí:

- Tồn tại đúng đường dẫn yêu cầu.
- UTF-8 đọc lại được.
- Có đủ heading/nội dung bắt buộc.
- Không chứa giá trị xác thực, trạng thái phiên, header request thô, secret hoặc địa chỉ chi tiết.
- Chỉ tài liệu trong docs/handoff thay đổi trong bước bàn giao.

## Những giới hạn của quá trình kiểm thử

- Unit tests dùng fixture nên không chứng minh website hiện tại chưa thay selector/response shape.
- Chỉ một sản phẩm và một location được kiểm chứng live.
- Chưa có live smoke Hà Nội, Đà Nẵng hoặc all-locations.
- Chưa crawl full sitemap/full catalog.
- Chưa chạy PostgreSQL thật; migration production chưa được xác nhận end-to-end.
- Chưa build/run Docker image đầy đủ.
- Chưa đo throughput, memory, database growth hoặc hành vi scheduler dài hạn.
- Chưa kiểm chứng retry live bằng cách chủ động tạo 429/5xx; việc tạo tải như vậy không phù hợp.
- Chưa kiểm chứng challenge thật và không thử vượt cơ chế chống bot.
- Chưa đánh giá toàn bộ biến thể sản phẩm ngừng kinh doanh, thiếu giá hoặc giao hàng đặc biệt.
- Kết quả giá/tồn kho/giao hàng trong smoke chỉ đúng tại thời điểm quan sát và location thử.
- Kết quả 32 tests và syntax/Docker/live smoke là kết quả đã ghi nhận trước khi yêu cầu dừng; chúng không được chạy lại trong bước handoff.
