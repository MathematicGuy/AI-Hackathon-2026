# Transfer manifest

Ngày tổng hợp: 2026-07-17

## Nguyên tắc chuyển giao

Chỉ chuyển source, cấu hình mẫu, schema/migration, test fixture có chủ đích, dữ liệu sample đã kiểm soát và documentation. Không chuyển runtime state, database crawl, raw capture, thông tin xác thực, hồ sơ phiên hoặc dữ liệu địa chỉ chi tiết ngoài các file cấu hình đã được phê duyệt.

Danh sách dưới đây là allow-list cho project hiện tại.

## Danh sách file source cần chuyển

~~~text
pyproject.toml
dmx_crawler/__init__.py
dmx_crawler/__main__.py
dmx_crawler/cli.py
dmx_crawler/config.py
dmx_crawler/crawler.py
dmx_crawler/db.py
dmx_crawler/discovery.py
dmx_crawler/html.py
dmx_crawler/http.py
dmx_crawler/models.py
dmx_crawler/parsers.py
dmx_crawler/utils.py
dmx_crawler/adapters/__init__.py
dmx_crawler/adapters/dmx.py
dmx_crawler/infrastructure/__init__.py
~~~

## File cấu hình cần chuyển

~~~text
.env.example
.dockerignore
Dockerfile
docker-compose.yml
config/categories.yaml
config/locations.yaml
~~~

Lưu ý: chuyển .env.example, không chuyển file .env runtime. File location được chuyển nguyên file đã review; không sao chép các giá trị location chi tiết vào ticket, chat hoặc tài liệu bổ sung.

## File migration và SQL cần chuyển

~~~text
migrations/001_initial.sql
dmx_crawler/sqlite_schema.sql
sql/compare_prices.sql
~~~

- migrations/001_initial.sql là schema PostgreSQL production.
- dmx_crawler/sqlite_schema.sql là schema SQLite local/sample.
- sql/compare_prices.sql là query so sánh giá hiện tại giữa TP.HCM, Hà Nội và Đà Nẵng.

## File test cần chuyển

~~~text
tests/__init__.py
tests/test_adapter.py
tests/test_database.py
tests/test_discovery.py
tests/test_http.py
tests/test_parsers.py
tests/test_utils.py
tests/fixtures/category_laptop.html
tests/fixtures/product_laptop.html
tests/fixtures/delivery_hcm.json
~~~

Fixtures là dữ liệu offline đã được chọn lọc. Trước khi chuyển sang môi trường khác, vẫn nên kiểm tra lại rằng fixture không bị thay bằng raw capture ngoài ý muốn.

## Documentation cần chuyển

~~~text
README.md
docs/site-reconnaissance.md
docs/live-smoke.md
docs/handoff/implementation-history.md
docs/handoff/validation-report.md
docs/handoff/transfer-manifest.md
~~~

## Script và dữ liệu mẫu cần chuyển

~~~text
scripts/create_sample.py
data/sample.json
data/sample.csv
~~~

data/sample.json và data/sample.csv là sample có chủ đích, không phải export live đầy đủ.

## File tuyệt đối không được chuyển

Không chuyển bất kỳ mục nào sau đây, kể cả khi chúng xuất hiện cục bộ sau một lần chạy:

~~~text
.env
.env.local
.env.*
!.env.example

data/*.db
data/*.sqlite
data/*.sqlite3
data/*.db-wal
data/*.db-shm
data/raw/
data/export*
data/live*
*.log

.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

browser-profile/
session-state/
network-capture/
request-dumps/
response-dumps/

.agents/
.codex/
.git/
tmp/
temp/
~~~

Ngoài các pattern trên, tuyệt đối loại khỏi gói chuyển:

- File database hoặc export sinh từ crawl live.
- Raw HTML/JSON chưa được review.
- Network trace và request/response dump.
- Giá trị xác thực, secret, trạng thái phiên hoặc header thô.
- Địa chỉ khách hàng hoặc địa chỉ thử chi tiết.
- Log tool/agent, shell history và artifact trong thư mục tạm.
- Metadata Git nếu mục tiêu là source snapshot; việc chuyển repository Git phải là quy trình riêng đã được phê duyệt.

Không dùng glob phủ định trong lệnh copy một cách mù quáng. Nên tạo archive từ allow-list ở các phần trên.

## Cấu trúc project hiện tại

~~~text
.
├── .dockerignore
├── .env.example
├── Dockerfile
├── README.md
├── docker-compose.yml
├── pyproject.toml
├── config/
│   ├── categories.yaml
│   └── locations.yaml
├── data/
│   ├── sample.csv
│   └── sample.json
├── dmx_crawler/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── crawler.py
│   ├── db.py
│   ├── discovery.py
│   ├── html.py
│   ├── http.py
│   ├── models.py
│   ├── parsers.py
│   ├── sqlite_schema.sql
│   ├── utils.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── dmx.py
│   └── infrastructure/
│       └── __init__.py
├── docs/
│   ├── live-smoke.md
│   ├── site-reconnaissance.md
│   └── handoff/
│       ├── implementation-history.md
│       ├── transfer-manifest.md
│       └── validation-report.md
├── migrations/
│   └── 001_initial.sql
├── scripts/
│   └── create_sample.py
├── sql/
│   └── compare_prices.sql
└── tests/
    ├── __init__.py
    ├── test_adapter.py
    ├── test_database.py
    ├── test_discovery.py
    ├── test_http.py
    ├── test_parsers.py
    ├── test_utils.py
    └── fixtures/
        ├── category_laptop.html
        ├── delivery_hcm.json
        └── product_laptop.html
~~~

## Trình tự kiểm tra gói chuyển đề xuất

1. Tạo gói chỉ từ allow-list.
2. Đối chiếu danh sách file với manifest này.
3. Quét secret và dữ liệu nhạy cảm bằng công cụ của tổ chức.
4. Xác nhận không có database, raw capture, log hoặc runtime state.
5. Ở môi trường đích, tạo file runtime từ .env.example bằng kênh quản lý secret riêng.
6. Chạy syntax check và 32 unit tests offline.
7. Chạy Docker static checks.
8. Chỉ chạy live smoke sau khi operator review location config, robots/rate limit và cấp phép vận hành.
