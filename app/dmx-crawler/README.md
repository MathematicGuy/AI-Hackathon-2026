# DMX Crawler

Hệ thống crawl có kiểm soát cho ba danh mục **Laptop**, **Tivi** và **Tủ lạnh** trên Điện Máy XANH. Thiết kế tách dữ liệu chung của sản phẩm khỏi snapshot giá/tồn kho/giao hàng theo địa điểm, đồng thời lưu version theo thời gian, crawl run, attempt và lỗi để retry.

> Trạng thái: repository đã có parser HTML/JSON-LD, sitemap discovery, HTTP client có rate limit/backoff, schema SQLite/PostgreSQL, CLI và config ba địa điểm. Build/start container không tự live crawl; trạng thái/handoff hiện tại được ghi tại [`docs/handoff/current-status.md`](docs/handoff/current-status.md).

Chi tiết bằng chứng selector, cookie và endpoint đã kiểm tra nằm tại [docs/site-reconnaissance.md](docs/site-reconnaissance.md). Kết quả smoke live tối thiểu lịch sử được ghi tại [docs/live-smoke.md](docs/live-smoke.md); bằng chứng parser/specifications mới nhất và các giới hạn còn lại nằm trong [current status](docs/handoff/current-status.md).

## Nguyên tắc vận hành

* Ưu tiên [`/newsitemap/sitemap-product`](https://www.dienmayxanh.com/newsitemap/sitemap-product), fallback về trang danh mục.
* Tôn trọng `robots.txt` và `Crawl-delay: 5`; không gọi đường dẫn bị disallow.
* Một HTTP client/cookie jar hoặc browser context **riêng cho từng địa điểm**.
* Không lưu snapshot location nếu province/ward yêu cầu không khớp cookie `DMX_Personal`, `#location-detail[data-province]` và inline `dataDeli`.
* Dừng client khi gặp CAPTCHA/challenge/401/403; giảm tốc/retry 408, 425, 429 và 5xx theo `Retry-After` + exponential backoff. Không giải CAPTCHA, proxy rotation hay giả lập né anti-bot.
* Giá VND lưu bằng integer; URL sản phẩm chuẩn hóa và deduplicate bằng DMX product ID, fallback canonical URL hash. Không merge chỉ theo tên/model.

## Kiến trúc

```text
sitemap index ──> sitemap children ──> discovered product URLs
       │                       fallback: category HTML
       v
products/product_urls ──> common product crawl ──> content versions/specs/media
       │
       ├── isolated HCM session ──> location versions + observations
       ├── isolated Hanoi session ─> location versions + observations
       └── isolated Danang session ─> location versions + observations

crawl_runs ──> crawl_tasks ──> crawl_attempts ──> crawl_errors/retry
```

Module chính:

| Module | Trách nhiệm |
| --- | --- |
| `dmx_crawler.discovery` | Đọc sitemap index/child, lọc category, fallback category HTML |
| `dmx_crawler.http` | CookieJar riêng, rate limit, retry/backoff, phát hiện challenge |
| `dmx_crawler.parsers` | Parse card, product, specs, giá, khuyến mãi, location evidence và delivery HTML/JSON |
| `dmx_crawler.db` | Run/task/error, dedupe, content/location version, incremental state, export |
| `config/categories.yaml` | Danh mục và URL prefix |
| `config/locations.yaml` | Province/ward/address đại diện và aliases |
| `migrations/001_initial.sql` | PostgreSQL baseline legacy trong `public` |
| `migrations/002_rich_product_spec_values.sql` | Backfill cột/index specifications trước khi split |
| `migrations/003_split_catalog_crawler_schemas.sql` | Chuyển in-place 18 bảng sang `catalog`/`crawler` |
| `dmx_crawler/sqlite_schema.sql` | Schema SQLite cho local/sample |

## Mô hình dữ liệu

* `products`, `product_urls`: identity/canonical URL; unique theo `(source, source_product_key)` khi có và `(source, canonical_url_hash)`.
* `product_content_versions`: tên, brand, model, mô tả, rating, sold, status chung; một current row (`valid_to IS NULL`) trên mỗi sản phẩm.
* `spec_definitions`, `product_spec_values`: khóa specs theo category, vẫn giữ `raw_label`/`raw_value` để thêm loại sản phẩm mới mà không migration cột.
* `media_assets`, `product_version_media`: gallery deduplicate theo URL hash.
* `product_location_versions`: sale/list price, promotion, stock, delivery và returned-location evidence theo `(product, location)`; `valid_from`/`valid_to` tạo lịch sử giá.
* `crawl_runs`, `crawl_tasks`, `crawl_attempts`, `crawl_errors`: audit và retry; lỗi location mismatch không sinh snapshot.
* `product_crawl_state`, `product_location_crawl_state`: `next_due_at`, response hash, unchanged/failure streak cho incremental scheduling.
* `crawl_observations`: ghi cả lần crawl không đổi, tách “đã quan sát” khỏi “đã tạo version mới”.

Dữ liệu chung (tên, brand/model, mô tả, specs, ảnh) và dữ liệu theo location (giá, promotion, stock, delivery) có lịch refresh/hash riêng. `sitemap_lastmod` chỉ là tín hiệu để lên lịch, không thay thế lịch sử quan sát.

Trên PostgreSQL, chín bảng dữ liệu sản phẩm nằm trong schema `catalog`; chín bảng run/task/attempt/error/incremental nằm trong `crawler`. Hai schema dùng chung một database và cùng một nguồn dữ liệu sản phẩm. SQLite không có PostgreSQL schema nên tiếp tục dùng đúng 18 tên bảng phẳng trong một file database.

## Cài đặt local

Yêu cầu Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
set -a; source .env; set +a
mkdir -p data
```

SQLite là mặc định zero-dependency. PostgreSQL cần extra và migration phải được operator chạy tường minh, không được chạy trong lúc crawl:

```bash
python -m pip install -e '.[postgres,dev]'
export DMX_DATABASE_URL='postgresql://dmx:dmx@localhost:5432/dmx'

# Database mới
psql -v ON_ERROR_STOP=1 "$DMX_DATABASE_URL" -f migrations/001_initial.sql
psql -v ON_ERROR_STOP=1 "$DMX_DATABASE_URL" -f migrations/002_rich_product_spec_values.sql
psql -v ON_ERROR_STOP=1 "$DMX_DATABASE_URL" -f migrations/003_split_catalog_crawler_schemas.sql

# Database legacy đã có 001/002: chỉ chạy migration 003
psql -v ON_ERROR_STOP=1 "$DMX_DATABASE_URL" -f migrations/003_split_catalog_crawler_schemas.sql
python -m dmx_crawler init-db
```

Migration 003 chỉ xét allow-list 18 bảng ứng dụng; bảng khác trong `public` không ảnh hưởng. Nó chuyển in-place khi đủ 18 bảng legacy, xác minh/no-op khi đã split đầy đủ, và rollback với danh sách sai lệch khi schema thiếu hoặc split dở. Chạy lại migration 003 là idempotent. `Database.initialize()` trên PostgreSQL chỉ readiness-check và fail fast; nó không chạy lại 001/002/003. `ALTER TABLE ... SET SCHEMA` lấy `ACCESS EXCLUSIVE` lock, vì vậy production cần maintenance window ngắn và rollout migration/code phối hợp.

Không commit `.env`, database, HTML raw hoặc cookie/session.

## Cấu hình

`.env.example`:

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `DMX_DATABASE_URL` | `sqlite:///data/dmx.db` | SQLite path hoặc PostgreSQL DSN |
| `DMX_SITE_BASE_URL` | `https://www.dienmayxanh.com` | Origin được phép |
| `DMX_USER_AGENT` | contact placeholder | Thay bằng UA có contact hợp lệ |
| `DMX_MIN_REQUEST_INTERVAL_SECONDS` | `5` | Không đặt thấp hơn robots crawl-delay |
| `DMX_REQUEST_TIMEOUT_SECONDS` | `30` | Timeout mỗi request |
| `DMX_MAX_ATTEMPTS` | `3` | Tổng attempt cho lỗi tạm thời |
| `DMX_LOCATIONS_FILE` | `config/locations.yaml` | Config location |
| `DMX_CATEGORIES_FILE` | `config/categories.yaml` | Config category |

Province ID đã quan sát ngày 2026-07-17: HCM `1027`, Hà Nội `1000`, Đà Nẵng `1020`. Ward ID và địa chỉ đại diện trong `config/locations.yaml` phải được operator kiểm tra lại qua popup hiện tại trước live crawl; DMX có thể đổi mã/tên theo địa giới. Không dùng địa chỉ khách hàng thật trong fixture hoặc log.

## CLI

CLI đã được triển khai bằng `argparse`; mọi lệnh live tạo `crawl_runs`, task/attempt và lỗi retry tương ứng. `--limit` nên dùng cho smoke test; mặc định crawler chỉ lấy record đến `next_due_at`, còn `--force` bỏ qua lịch incremental. `--source category` là fallback khi sitemap không khả dụng.

```bash
# SQLite: khởi tạo bảng và seed config; PostgreSQL: chỉ verify schema đã migrate rồi seed
python -m dmx_crawler init-db

# Khám phá URL, ưu tiên sitemap
python -m dmx_crawler discover --categories laptop,tivi,tu-lanh --source auto --limit 30

# Crawl dữ liệu chung (có alias crawl-product/crawl-products)
python -m dmx_crawler crawl products --categories laptop,tivi,tu-lanh --only-due --limit 30
python -m dmx_crawler crawl-product --url https://www.dienmayxanh.com/tivi/google-tivi-tcl-ai-4k-65-inch-65p6k --force

# Crawl một địa điểm trong session riêng, hoặc lần lượt cả ba session
python -m dmx_crawler crawl location --location hcm --only-due --limit 10
python -m dmx_crawler crawl all-locations --only-due --limit 10

# Retry lỗi tạm thời chưa resolve và export snapshot hiện tại
python -m dmx_crawler retry-errors --limit 50
python -m dmx_crawler export --format json --output data/export.json --limit 100
python -m dmx_crawler export --format csv --output data/export.csv --limit 100
```

Smoke test hoàn toàn offline và dữ liệu mẫu có thể tái tạo bằng:

```bash
python scripts/create_sample.py
```

Script đọc fixture đã lưu, ghi SQLite mẫu, rồi sinh `data/sample.json` và `data/sample.csv`; nó không gửi request ra Internet. Với live crawl, command location luôn tạo `CookieJar`/client mới, gọi chọn province → ward → address, xác minh cookie/DOM/delivery evidence trước khi ghi. Khi gặp CAPTCHA/challenge thì client dừng, không giải hoặc né cơ chế chống bot.

## Docker

Build image không tạo network request tới DMX ngoài việc cài package từ local source:

```bash
docker compose build
cp .env.example .env
docker compose run --rm crawler --help
```

Khởi tạo/crawl mẫu có giới hạn sau khi đã xác minh config:

```bash
docker compose run --rm crawler init-db
docker compose run --rm crawler discover --categories laptop,tivi,tu-lanh --source sitemap --limit 10
```

`./data` được mount để giữ SQLite/export, `./config` mount read-only. Compose không tự lên lịch hoặc tự live crawl; dùng cron/orchestrator bên ngoài và giữ concurrency thấp.

Muốn dùng PostgreSQL local, bật profile, chạy migration explicit rồi để `init-db` chỉ verify/seed:

```bash
docker compose --profile postgres up -d postgres
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U dmx -d dmx < migrations/001_initial.sql
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U dmx -d dmx < migrations/002_rich_product_spec_values.sql
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U dmx -d dmx < migrations/003_split_catalog_crawler_schemas.sql
# .env: DMX_DATABASE_URL=postgresql://dmx:dmx-local-only@postgres:5432/dmx
docker compose run --rm crawler init-db
```

Mật khẩu Compose chỉ dành cho local development; thay credential và dùng secret manager trong production. `ALTER TABLE ... SET SCHEMA` giữ ACL của table nhưng không tự cấp `USAGE` trên schema mới. Migration không hardcode role: deployment phải cấp frontend role `USAGE`/`SELECT` trên `catalog` mà không cấp `USAGE` trên `crawler`; crawler role cần quyền trên cả hai schema và các sequence tương ứng. `Database.export_current()` là read path catalog-only; các lệnh crawler/CLI vẫn dùng operator role để seed config và ghi operational state.

## Test

```bash
python -m compileall -q dmx_crawler tests scripts
python -m unittest discover -s tests -v
pytest -q

# Chỉ dùng PostgreSQL local/disposable; test tự tạo và xóa database riêng
DMX_TEST_POSTGRES_ADMIN_URL=postgresql://<admin>/postgres \
  python -m unittest tests.test_postgres_schema_split -v
```

Test quan trọng cần bao phủ: parse giá (`11.990.000₫`, `12690000.0`), sold (`5,4k`, `48k`), specs theo group, canonical URL bỏ tracking, location ID/text comparison, dedupe product ID/URL hash, CAPTCHA detection và location mismatch no-write. Test parser phải dùng fixture HTML đã lưu có chủ đích; test mặc định không truy cập internet.

## Query so sánh giá HCM/Hà Nội/Đà Nẵng

Query đầy đủ có tại [sql/compare_prices.sql](sql/compare_prices.sql). Ví dụ PostgreSQL cho current snapshot:

```sql
WITH current_price AS (
    SELECT plv.product_id, l.code, plv.sale_price, plv.stock_status
    FROM catalog.product_location_versions plv
    JOIN catalog.locations l ON l.id = plv.location_id
    WHERE plv.valid_to IS NULL
      AND l.code IN ('hcm', 'hanoi', 'danang')
)
SELECT p.id, pcv.name,
       MAX(cp.sale_price) FILTER (WHERE cp.code = 'hcm') AS price_hcm,
       MAX(cp.sale_price) FILTER (WHERE cp.code = 'hanoi') AS price_hanoi,
       MAX(cp.sale_price) FILTER (WHERE cp.code = 'danang') AS price_danang,
       MAX(cp.stock_status) FILTER (WHERE cp.code = 'hcm') AS stock_hcm,
       MAX(cp.stock_status) FILTER (WHERE cp.code = 'hanoi') AS stock_hanoi,
       MAX(cp.stock_status) FILTER (WHERE cp.code = 'danang') AS stock_danang
FROM catalog.products p
JOIN catalog.product_content_versions pcv ON pcv.product_id = p.id AND pcv.valid_to IS NULL
JOIN current_price cp ON cp.product_id = p.id
WHERE p.id = '<product uuid>'
GROUP BY p.id, pcv.name;
```

Bỏ `WHERE p.id = ...` để so sánh toàn bộ sản phẩm. Lịch sử giá dùng cùng bảng nhưng không lọc `valid_to IS NULL`, sắp xếp theo `valid_from`.

## Giới hạn đã biết

Selector/API là bằng chứng tại thời điểm khảo sát, không phải API public ổn định. Giá/giao hàng có thể yêu cầu ward + địa chỉ đầy đủ; city-only cookie `HasLocation=false` chỉ cho giá mặc định và không đủ làm ETA. Sản phẩm ngừng kinh doanh có thể thiếu `.bs_price`; không chuyển giá 0 thành “còn hàng”. Mọi thay đổi cấu trúc phải dẫn đến parser error/unknown và fixture mới, không fallback bằng dữ liệu bịa.
