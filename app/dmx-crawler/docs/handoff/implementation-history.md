# Lịch sử triển khai

Ngày bàn giao: 2026-07-17

## Trạng thái bàn giao

Phiên triển khai đã dừng mọi thao tác crawl. Trong bước bàn giao này chỉ có ba tài liệu trong docs/handoff được tạo; source code, cấu hình runtime, migration, dữ liệu và test không bị chỉnh sửa. Không commit và không push.

Tài liệu chỉ ghi thông tin kỹ thuật cần thiết. Các giá trị xác thực, trạng thái phiên, dữ liệu header thô và địa chỉ chi tiết không được chép vào đây.

## Mục tiêu ban đầu

Xây dựng một crawler dễ bảo trì cho ba danh mục Laptop, Tivi và Tủ lạnh của Điện Máy XANH, với các yêu cầu chính:

- Khám phá URL sản phẩm từ sitemap trước, fallback về trang danh mục.
- Thu thập dữ liệu chung của sản phẩm và dữ liệu biến đổi theo địa điểm/thời gian.
- Hỗ trợ TP.HCM, Hà Nội và Đà Nẵng bằng các session độc lập.
- Lưu lịch sử giá, tồn kho, giao hàng, crawl run và lỗi retry.
- Crawl tăng dần, có rate limit, backoff, phát hiện location mismatch và dừng trước cơ chế chống bot.
- Có CLI, SQL schema/migration, Docker, dữ liệu mẫu, test và tài liệu vận hành.
- Khảo sát hành vi thực tế của website trước khi cố định selector, luồng chọn địa điểm hoặc cách đọc dữ liệu.

## Những thành phần đã triển khai

### Source crawler

- dmx_crawler/cli.py và dmx_crawler/__main__.py: CLI cho init database, discovery, crawl dữ liệu chung, crawl từng location, crawl toàn bộ location, retry lỗi, doctor và export.
- dmx_crawler/discovery.py: sitemap-first discovery, lọc danh mục, chuẩn hóa/deduplicate URL và fallback trang danh mục.
- dmx_crawler/http.py: HTTP client có request interval dùng chung, retry/backoff, Retry-After, challenge detection và session state tách biệt.
- dmx_crawler/crawler.py: orchestration run/task/attempt, lịch incremental, crawl dữ liệu chung và theo location.
- dmx_crawler/adapters/dmx.py: adapter riêng cho hành vi Điện Máy XANH, chọn location, đọc bằng chứng location, product page và delivery payload.
- dmx_crawler/parsers.py, dmx_crawler/html.py và dmx_crawler/utils.py: parse giá, số lượng bán, JSON-LD/HTML, thông số, canonical URL, location comparison và fingerprint.
- dmx_crawler/models.py và dmx_crawler/config.py: model dữ liệu và nạp cấu hình.
- dmx_crawler/db.py: persistence SQLite, dedupe, SCD2, EAV, crawl audit, retry state và export.

### Database, cấu hình và vận hành

- dmx_crawler/sqlite_schema.sql: schema local/sample.
- migrations/001_initial.sql: migration PostgreSQL.
- sql/compare_prices.sql: truy vấn so sánh snapshot giá hiện tại giữa ba location.
- config/categories.yaml: ba danh mục.
- config/locations.yaml: ba location logic; tài liệu này không sao chép giá trị địa chỉ chi tiết.
- Dockerfile, docker-compose.yml, .dockerignore và .env.example.
- scripts/create_sample.py cùng data/sample.json và data/sample.csv.
- README.md, docs/site-reconnaissance.md và docs/live-smoke.md.
- Bộ test offline trong tests/ và fixtures tương ứng.

## Các quyết định kiến trúc

- Chọn Python 3.11+, tổ chức theo modular monolith để CLI, crawler, parser và persistence có ranh giới rõ nhưng vận hành đơn giản.
- Core ưu tiên thư viện chuẩn; SQLite là mặc định cho local/sample, PostgreSQL là đích production.
- Adapter website tách khỏi crawler chung để có thể thay selector/flow khi website đổi mà không làm lan rộng thay đổi.
- Sitemap là nguồn discovery ưu tiên. Trang danh mục chỉ là fallback.
- URL được canonicalize; identity ưu tiên source product key, fallback canonical URL hash. Không deduplicate chỉ theo tên hoặc model.
- Giá VND lưu bằng integer để tránh sai số số thực.
- Dữ liệu chung và dữ liệu theo location có fingerprint, lịch refresh và version riêng.
- Rate limit dùng một limiter dùng chung trong tiến trình để các session location không vô tình cộng dồn tốc độ.
- Hành vi an toàn là fail closed: location không khớp, response thiếu bằng chứng hoặc parser không chắc chắn thì ghi lỗi/unknown, không suy đoán và không tạo snapshot sai.
- Khi gặp challenge hoặc giới hạn truy cập nghiêm trọng, client dừng hoặc backoff; hệ thống không giải CAPTCHA và không triển khai cơ chế né chống bot.

## Cơ chế crawl đa địa điểm

Mỗi location được xử lý bằng một client và session state mới, không dùng chung session giữa TP.HCM, Hà Nội và Đà Nẵng.

Luồng location được thiết kế như sau:

1. Nạp một location logic từ config.
2. Tạo client/session riêng.
3. Thực hiện luồng chọn tỉnh/thành, phường/xã và điểm giao đại diện theo hành vi đã khảo sát.
4. Tải lại trang sản phẩm và dữ liệu giao hàng trong chính session đó.
5. Thu thập bằng chứng location trả về từ nhiều lớp dữ liệu của trang/response.
6. So sánh location yêu cầu với location website trả về bằng mã định danh và tên đã chuẩn hóa.
7. Chỉ khi khớp mới ghi product_location_versions và crawl_observations.
8. Nếu mismatch, ghi attempt/error để retry nhưng không ghi snapshot giá, tồn kho hoặc giao hàng.
9. Lệnh all-locations chạy tuần tự các context độc lập; nếu phát hiện block/challenge thì dừng hoặc giảm tải thay vì tiếp tục qua location khác.

Thiết kế này tránh trường hợp giá của location trước rò sang location sau.

## Cách lưu database, SCD2 và EAV

### Identity và chống trùng

- products giữ identity sản phẩm.
- product_urls giữ canonical URL và URL đã quan sát.
- Unique key theo nguồn và source product key khi có.
- Canonical URL hash là khóa fallback.
- Việc phát hiện lại cùng sản phẩm cập nhật metadata discovery, không tạo sản phẩm mới.

### SCD2 cho dữ liệu theo thời gian

- product_content_versions lưu version của tên, thương hiệu, model, mô tả, đánh giá, số đã bán và trạng thái chung.
- product_location_versions lưu version riêng theo cặp product/location cho giá bán, giá gốc, khuyến mãi, tồn kho, giao hàng và bằng chứng location.
- Bản hiện tại có valid_to rỗng.
- Sau mỗi lần crawl, payload đã chuẩn hóa được băm và so với bản hiện tại.
- Nếu không đổi, không tạo version mới; crawl_observations vẫn ghi nhận lần quan sát và scheduler cập nhật next_due_at.
- Nếu đổi, transaction đóng version cũ bằng valid_to rồi thêm version mới với valid_from.
- Version location độc lập, vì vậy thay đổi tại một thành phố không đóng version của thành phố khác.

### EAV cho thông số kỹ thuật

- spec_definitions quản lý khóa thông số chuẩn theo category và giữ nhãn nguồn.
- product_spec_values liên kết content version với definition, raw label/raw value và giá trị chuẩn hóa khi có.
- Laptop, Tivi và Tủ lạnh có thể có tập thuộc tính khác nhau mà không cần thêm cột/migration cho từng thông số mới.
- Giá trị gốc vẫn được giữ để có thể re-normalize sau này.

### Audit, incremental và retry

- crawl_runs: một lần chạy CLI.
- crawl_tasks: đơn vị công việc theo discovery/common/location.
- crawl_attempts và crawl_errors: lịch sử attempt, phân loại lỗi tạm thời/vĩnh viễn và trạng thái retry.
- product_crawl_state và product_location_crawl_state: next_due_at, response hash, unchanged streak và failure streak.
- crawl_observations: phân biệt một lần đã quan sát với một lần đã tạo version mới.

## Lỗi apply_patch đã gặp

Thao tác apply_patch nhằm cập nhật file sau đã thất bại trước khi patch được áp dụng:

~~~text
/home/dholmes/Project_personal/Crawler/dmx_crawler/db.py
~~~

Stderr được ghi nhận nguyên văn:

~~~text
apply_patch verification failed: Failed to read file to update /home/dholmes/Project_personal/Crawler/dmx_crawler/db.py: fs sandbox helper failed with status exit status: 1: bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
~~~

Nguyên nhân biểu hiện ở sandbox helper/bwrap, không phải lỗi cú pháp của diff. Sau lỗi này, apply_patch không được lặp lại.

Trong bước tạo tài liệu handoff, lần thử đầu bằng một heredoc ghép dài cũng chưa ghi file vì shell parser báo unmatched backtick. Kiểm tra sau đó xác nhận docs/handoff chưa tồn tại, nên không có file dở dang.

## Cách chuyển sang Path.write_text và heredoc

Sau lỗi sandbox helper, các lần ghi file hợp lệ được giới hạn trong repository và thực hiện bằng Python pathlib:

- Nội dung được cấp qua quoted heredoc để shell không nội suy ký tự Markdown.
- File được ghi bằng Path.write_text với encoding UTF-8.
- Parent directory được tạo bằng Path.mkdir với parents=True và exist_ok=True.
- Không ghi ra ngoài /home/dholmes/Project_personal/Crawler.
- Sau khi ghi, file được đọc lại, kiểm tra heading bắt buộc, rà mẫu dữ liệu nhạy cảm và xác nhận bằng git diff chế độ no-index vì workspace hiện không phải Git worktree.

## Các command đã chạy

Danh sách dưới đây là các command chính được ghi nhận trong phiên; không phải bản sao đầy đủ shell history. Biến môi trường, đường dẫn database tạm và chi tiết location được lược bỏ có chủ đích.

### Kiểm tra source và unit test

~~~bash
python -m compileall -q dmx_crawler tests scripts
python -m unittest discover -s tests -v
~~~

### CLI và dữ liệu mẫu

~~~bash
python -m dmx_crawler init-db
python -m dmx_crawler doctor
python scripts/create_sample.py
python -m dmx_crawler export --format json --output data/sample.json
python -m dmx_crawler export --format csv --output data/sample.csv
~~~

### Docker static checks

~~~bash
docker compose config --quiet
docker build --check .
~~~

### Live smoke có giới hạn

~~~bash
python -m dmx_crawler discover --source category --category tivi --limit 1
python -m dmx_crawler crawl products --category tivi --limit 1 --force
python -m dmx_crawler crawl location --location hcm --category tivi --limit 1 --force
~~~

Live smoke chỉ dùng một sản phẩm và một location. Không có live command nào được chạy trong bước tạo handoff này.

### Xác nhận thay đổi khi không có Git worktree

~~~bash
git diff --no-index ...
~~~

Workspace không có metadata Git hợp lệ, nên chế độ no-index được dùng để xem nội dung file mới mà không commit.

## Kết quả unit test

Command đã ghi nhận:

~~~bash
python -m unittest discover -s tests -v
~~~

Kết quả cuối cùng của phiên:

~~~text
Ran 32 tests
OK
~~~

Phạm vi gồm parse giá, số lượng bán, thông số, URL, location comparison, dedupe, discovery, HTTP retry/challenge, adapter/session isolation, mismatch no-write và SCD2 database.

## Kết quả live smoke test

Smoke test live cuối cùng đã hoàn tất với tải tối thiểu:

- Discovery từ fallback category trả về đúng một URL Tivi.
- Crawl common thành công cho một sản phẩm và ghi một content version.
- Crawl location TP.HCM dùng session độc lập và ghi một location version.
- Bằng chứng location trả về khớp location logic yêu cầu.
- Giá bán và giá gốc được parse thành số nguyên VND.
- Website trả trạng thái tạm hết hàng cho điểm thử; crawler lưu stock_status là out_of_stock, không suy đoán còn hàng.
- Database smoke tạm được loại bỏ sau khi đối chiếu.
- Một false positive trong challenge detector do dấu vết reCAPTCHA thụ động trên trang bình thường đã được sửa và đưa vào test trước smoke thành công.

Chi tiết nhận dạng sản phẩm, location cụ thể và trạng thái phiên không được lặp lại trong tài liệu handoff này.

## Những phần chưa kiểm chứng

- Chưa chạy end-to-end live cho Hà Nội và Đà Nẵng.
- Chưa chạy lệnh all-locations live đủ cả ba location.
- Chưa crawl toàn bộ sitemap hoặc toàn bộ ba catalog.
- Fallback trang danh mục chưa được chứng minh cho mọi kiểu phân trang/lazy-load thực tế.
- PostgreSQL migration đã có nhưng chưa được kiểm thử runtime end-to-end với PostgreSQL thật.
- Docker mới qua static checks; chưa build image đầy đủ và chưa chạy compose service end-to-end.
- Chưa stress test concurrency, database lớn hoặc scheduler chạy dài ngày.
- Chưa chủ động kiểm chứng live 429/Retry-After hay challenge thật; không nên tạo tải chỉ để kích hoạt chúng.
- Selector và response shape có thể thay đổi theo website; cần fixture/recon mới khi parser báo unknown.
- Dữ liệu sample sinh từ fixture, không đại diện cho độ phủ catalog.
- Location config phải được operator kiểm tra lại trước lần live tiếp theo.
