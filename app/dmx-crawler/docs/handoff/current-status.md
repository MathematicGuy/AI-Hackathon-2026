# DMX Crawler — trạng thái hiện tại và bàn giao

Ngày chụp trạng thái: **2026-07-17**

Component: `app/dmx-crawler/`

Tài liệu này là nguồn trạng thái hiện tại của component sau khi được tích hợp
vào repository chung. Các file còn lại trong `docs/handoff/` được giữ làm lịch
sử đã làm sạch; số test, manifest dữ liệu và mô tả workspace trong các tài liệu
cũ không còn đại diện cho trạng thái hiện tại.

## Tóm tắt trạng thái

- Crawler Python đã được tích hợp thành component độc lập trong `app/dmx-crawler/`.
- Parser common product content và toàn bộ specifications đã được mở rộng,
  kiểm thử offline và kiểm chứng bằng hai vòng live sample có kiểm soát.
- Crawler hiện **đang dừng**: không có bulk crawl, discovery, location crawl hay
  migration database dùng chung nào đang chạy.
- SQLite live sample chỉ là bằng chứng local. Database, JSON export, cache và
  bytecode không thuộc source package và không được đưa vào Git.
- PostgreSQL production, location flow sau thay đổi parser và độ phủ toàn catalog
  chưa được kiểm chứng end-to-end.

## Đã hoàn thành

### Tích hợp component

- Source Python, config mẫu, SQLite schema, PostgreSQL migrations, SQL hỗ trợ,
  Docker/Compose, test offline và documentation đã được đặt dưới component.
- Root `.gitignore` có rule theo phạm vi `app/dmx-crawler/` để loại `.env`,
  database, crawl output, raw data, screenshot, browser state, cache và log.
- `data/` chỉ có `data/.gitkeep` trong tập source; không đưa sample JSON/CSV
  hay live sample database vào commit.
- `config/locations.yaml` giữ province/ward phục vụ logic nhưng mọi `address`
  đều là `null`; không lưu địa chỉ khách hàng, cookie hoặc browser state.
- Docker build context loại mọi `.env.*` và runtime data; các rule cũ có thể
  re-include sample JSON/CSV đã được bỏ.

### Parser specifications tổng quát

- Lưu specifications theo danh sách group/item có thứ tự thay vì dictionary.
- Bảo toàn group, label, raw label/value, group/item ordinal và provenance.
- Không hardcode danh sách CPU, RAM, màn hình, dung tích hoặc field theo category.
- Hỗ trợ dữ liệu DOM từ `ul/li`, `table`, `dl/dt/dd`, div row và accordion
  đóng khi nội dung đã có trong HTML; hỗ trợ embedded JSON, JSON-LD và API payload
  đã được cung cấp cho parser.
- DOM là nguồn chính. Embedded JSON/JSON-LD bổ sung hoặc merge theo label đã
  Unicode-normalize; không ghi đè giá trị DOM đầy đủ bằng giá trị rút gọn.
- Field trùng label được disambiguate bằng group/value; trường hợp còn mơ hồ được
  ghi diagnostics thay vì merge tùy tiện.
- Typed parsing bảo thủ: `16 GB`, `60 Hz`, `65 inch` và `528 kWh/năm`
  được tách number/unit; `4K` và `1 x USB` giữ text, number/unit null.
- Completeness và merge diagnostics ghi số group/item, group rỗng, row thiếu
  label/value, source counts, merge/add/ambiguous events và warning.

### Model và persistence

- `specs_raw_json` giữ snapshot group/item đầy đủ, có thứ tự để có thể parse lại.
- `product_spec_values` lưu EAV theo content version, gồm group, ordinals,
  raw label/value, typed values, unit, source và provenance.
- Migration `002_rich_product_spec_values.sql` mô tả shape EAV mở rộng; migration
  không được tự động chạy trên database dùng chung trong các vòng kiểm chứng.
- Common crawl ghi HTTP status thực tế và completeness/merge diagnostics vào
  metadata JSON hiện có của `crawl_attempts`.
- `source_product_key` được tách khỏi commercial model; internal product ID
  không được ghi vào field model.
- SCD2 chỉ tạo content version khi content hash thay đổi; lần quan sát không đổi
  vẫn tạo tracking/observation nhưng không nhân đôi version hoặc spec rows.

## Bằng chứng kiểm chứng

### Offline fixtures

Fixtures bao phủ laptop, tivi và tủ lạnh với nhiều group; accordion đóng; DOM
kết hợp embedded JSON/JSON-LD; response động mô phỏng; duplicate label; và
markup `ul/li`, table, `dl/dt/dd`, div row. Assertion so toàn bộ ordered
group/item, không chỉ một vài field mẫu.

Kết quả offline đã được chạy lại ngay trước commit xuất bản và được ghi tại mục
“Validation của bản xuất bản”.

### Live sample vòng 1 — acceptance set

Phạm vi: đúng một laptop, một tivi và một tủ lạnh; common content/specifications
only; concurrency 1; không location; không discovery.

| Danh mục | Group nguồn/parser | Item nguồn/parser | EAV | HTTP/attempt |
| --- | ---: | ---: | ---: | --- |
| Laptop Asus Vivobook | 6 / 6 | 28 / 28 | 28 | 200 / 1 |
| Google Tivi TCL | 6 / 6 | 34 / 34 | 34 | 200 / 1 |
| Tủ lạnh Toshiba | 5 / 5 | 18 / 18 | 18 | 200 / 1 |
| **Tổng** | **17 / 17** | **80 / 80** | **80** | **3 success** |

Snapshot/EAV tương đương cho cả ba sản phẩm; không group rỗng, omission,
ambiguous merge hoặc field JSON-LD thật sự nằm ngoài DOM. Khác biệt giá trị ngắn
hơn từ JSON-LD được giữ trong diagnostics, không làm mất giá trị DOM.

### Idempotence và SCD2

Ba URL vòng 1 được crawl lại tuần tự vào cùng database:

| Metric | Trước | Sau |
| --- | ---: | ---: |
| Products | 3 | 3 |
| Content versions | 3 | 3 |
| Product spec EAV rows | 80 | 80 |

Cả ba lần trả `unchanged=1`; content version ID và content hash của từng sản
phẩm không đổi. Run/task/attempt/observation tăng đúng ba record theo audit
design, nhưng không sinh content version hoặc spec row mới.

### Live sample vòng 2 — shape mở rộng

Trước request đầu tiên, local database được backup bằng SQLite online backup và
đối chiếu integrity/logical table hashes. Sau đó chỉ ba URL đã xác nhận được
crawl tuần tự, vẫn common/specifications only và không discovery/location.

| Danh mục | Group nguồn/parser | Item nguồn/parser | EAV mới | HTTP/attempt |
| --- | ---: | ---: | ---: | --- |
| Laptop Asus TUF | 6 / 6 | 26 / 26 | 26 | 200 / 1 |
| Smart Tivi OLED Samsung | 6 / 6 | 34 / 34 | 34 | 200 / 1 |
| Tủ lạnh Aqua Multi Door | 5 / 5 | 18 / 18 | 18 | 200 / 1 |
| **Tổng mới** | **17 / 17** | **78 / 78** | **78** | **3 success** |

Database local sau vòng 2 có 6 products, 6 content versions và 158 EAV rows;
location versions vẫn bằng 0. Không warning, omission, group rỗng, ambiguous
merge hoặc JSON-LD-only field. Ba sản phẩm cũ giữ nguyên version ID, hash,
`valid_from` và spec count. Field path mới duy nhất so với sản phẩm đầu tiên
cùng danh mục là `Công nghệ âm thanh / Các công nghệ khác` trên tivi vòng 2.

### Inventory schema local

- 18 application tables với tổng 191 cột.
- Một bảng SQLite nội bộ `sqlite_sequence` với 2 cột.
- Tổng vật lý: 19 bảng, 193 cột.

## Validation của bản xuất bản

Trước commit, chạy lại hoàn toàn offline:

```bash
python -m compileall -q dmx_crawler tests scripts
python -m unittest discover -s tests -v
pytest -q
docker compose config --quiet
```

Kết quả chạy lại trong phiên xuất bản:

- `compileall`: pass, không có syntax error.
- `unittest`: 60/60 tests pass.
- `pytest`: 60 tests và 19 subtests pass.
- `docker compose config --quiet`: pass; không build, pull hoặc start container.

## Đang làm và việc còn lại

Tại thời điểm chụp trạng thái, không có crawl job đang chạy. Công việc của phiên
phát hành là đóng gói source, test và tài liệu đã kiểm chứng vào một branch Git
mới không phải `main`.

Các việc kỹ thuật còn lại, chưa tự động thực hiện:

1. Sửa heuristic commercial model cho hai shape vòng 2:
   - Asus TUF hiện lưu chuỗi cấu hình `12500H/8GB/512GB/4GB` thay vì mã `HN074W`.
   - Aqua hiện lưu `AQR-M536XA(SL`, thiếu dấu ngoặc đóng cuối model.
2. Kiểm thử PostgreSQL end-to-end, gồm transaction/attempt-error linkage và
   migration 002 trên database thử riêng; chưa chạy trên database dùng chung.
3. Kiểm chứng nội dung thực sự chỉ xuất hiện sau JavaScript, iframe/shadow DOM
   hoặc endpoint động chưa được truyền vào parser.
4. Đưa location crawl sang cùng mức diagnostics/HTTP-status coverage của common
   crawl và kiểm chứng lại bằng phạm vi riêng được phê duyệt.
5. Mở rộng matrix sản phẩm/markup trước bulk crawl; không suy rộng sáu sản phẩm
   sample thành độ phủ toàn catalog.

## Runtime, privacy và Git boundary

Các artifact sau tồn tại hoặc có thể được tạo local nhưng không thuộc commit:

- `data/schema-sample/*.db` và backup database;
- JSON audit/export trong `data/schema-sample/`;
- `.env`, cookie, browser/session state, raw response, screenshot và log;
- `__pycache__/`, `.pytest_cache/`, `*.pyc` và cache công cụ.

Không ghi raw HTTP payload, credential, customer address, internal database ID
hoặc session state vào tài liệu này. Public product names chỉ được dùng để mô tả
evidence; runtime databases vẫn ở local và bị Git ignore.

## Release gate cho bước tiếp theo

Chỉ tiếp tục live crawl hoặc location crawl khi có phạm vi URL/location rõ ràng,
rate limit/concurrency được phê duyệt và operator kiểm tra lại cấu hình. Không tự
chạy discovery, migration production, bulk crawl, commit thêm hoặc merge vào
`main` chỉ từ tài liệu này.
