# AI Coding Session Log

## Session Metadata

- `member`: Lưu Tiến Duy
- `member_slug`: luu-tien-duy
- `ai_client`: Codex
- `interface`: chat
- `session_id`: parser-live-fix-r7n4q2
- `started_at_utc`: 2026-07-17T13:30:00Z
- `task_summary`: Sửa normalization, DOM–JSON-LD merge, typed parsing, diagnostics và HTTP status; kiểm thử rồi crawl lại đúng ba URL mẫu.
- `repository`: AI-Hackathon-2026
- `branch`: main

## Objective

Sửa parser/persistence theo acceptance criteria đã chỉ định, bổ sung regression
tests, xác nhận toàn bộ test pass, xóa riêng sample artifacts cũ và crawl lại
đúng một laptop, một tivi, một tủ lạnh mà không discovery hoặc location.

## Interaction Log

### Entry 1 — 2026-07-17T13:30:00Z

- Human request summary: Yêu cầu sửa DOM label/value, merge JSON-LD, typed parsing, diagnostics/HTTP status/model mapping, bổ sung regression tests và controlled recrawl ba URL.
- AI response or decision summary: Bắt đầu bằng session logging và Harness intake bắt buộc; chưa chỉnh code hoặc gọi mạng.
- Sanitized terminal, CLI, and tool actions: Đọc canonical logging policy, hướng dẫn thành viên và session template; tạo session log.
- Command and tool exit status: Thành công.
- Outcome or important output summary: Preflight logging hoàn tất; sẵn sàng chạy Harness và khảo sát component.
- Files affected or inspected: Tạo session log hiện tại; đọc các file policy logging.
- Validation performed: Kiểm tra đủ metadata và cấu trúc section bắt buộc.
- Validation result: Đạt.
- Redactions or logging limitations: Không ghi cookie, token, header, payload live hoặc dữ liệu cá nhân.

### Entry 2 — 2026-07-17T13:38:00Z

- Human request summary: Thay đổi behavior parser/persistence và controlled recrawl cần đi qua Harness change workflow.
- AI response or decision summary: Phân loại `change request`, lane `high-risk` vì chạm external provider behavior, durable attempt metadata và behavior đã có test; phạm vi vẫn bị khóa ở component, regression tests và đúng ba URL.
- Sanitized terminal, CLI, and tool actions: Thử bootstrap trực tiếp rồi qua `bash`; thử query active matrix; đọc Feature Intake, Context Rules, Harness/Architecture/Test Matrix và high-risk templates.
- Command and tool exit status: Bootstrap trực tiếp exit 126 do script không executable; qua `bash` exit 1 vì thiếu pinned Harness CLI; matrix query exit 127 vì binary không tồn tại. Các tài liệu đọc thành công.
- Outcome or important output summary: Không thể ghi intake/story/trace durable bằng Harness CLI. Tiếp tục best-effort implementation theo user allow-list và ghi friction trong session log, không cài hoặc sửa Harness.
- Files affected or inspected: Chỉ đọc Harness docs/scripts và component file inventory; chưa sửa source.
- Validation performed: Xác nhận `scripts/bin/harness-cli` không tồn tại và bootstrap fail-closed.
- Validation result: Harness operational workflow unavailable; component work chưa bị chặn.
- Redactions or logging limitations: Không ghi environment values hoặc payload external.

### Entry 3 — 2026-07-17T13:48:00Z

- Human request summary: Sửa parser/persistence/model/HTTP metadata và bổ sung regression tests trước controlled recrawl.
- AI response or decision summary: Triển khai DOM-primary merge, conservative typed parsing, model/source-key separation và attempt metadata trên cột hiện có; không đổi schema/migration.
- Sanitized terminal, CLI, and tool actions: Audit focused code/tests; patch helper và standard patch gặp lỗi sandbox/format nên dùng deterministic Python replacements với backup `/tmp` và review unified diff; chạy syntax check và toàn bộ unittest.
- Command and tool exit status: Core syntax check exit 0. Lượt test đầu có 3 expected failures do semantics cũ; sau cập nhật tests, 52 tests exit 0.
- Outcome or important output summary: DOM label/value được tách; JSON-LD subset merge provenance vào DOM; ambiguous match được cảnh báo; typed parsing không còn nhận `4K` hoặc `1 x USB`; HTTP status/diagnostics được persist; numeric internal ID không còn ghi vào model.
- Files affected or inspected: Sửa parser, utils, HTTP client, DMX adapter, crawler, DB attempt persistence và tests; tạo một offline crawler-attempt test file.
- Validation performed: `py_compile` core modules; `python -m unittest discover -s tests -v`.
- Validation result: 52/52 tests pass; chưa xóa sample hoặc gọi live network.
- Redactions or logging limitations: Không ghi raw fixture bodies, external payload, cookie, token hoặc header nhạy cảm.

### Entry 4 — 2026-07-17T14:02:00Z

- Human request summary: Chỉ crawl lại sau khi toàn bộ regression test pass và phải giữ đúng counts/provenance/HTTP diagnostics.
- AI response or decision summary: Rà soát độc lập phát hiện cleanup DOM chạy hai lần; sửa để cleanup đúng một lần. Đồng thời giữ HTTP response evidence khi parse hoặc persistence lỗi sau HTTP 200 và khóa snapshot/EAV bằng full-shape tests.
- Sanitized terminal, CLI, and tool actions: Replay offline evidence cũ; bổ sung regression cho value bắt đầu bằng label, duplicate labels, merge accounting, typed values, parse/persistence failure và invalid compressed response; chạy compileall, unittest và pytest.
- Command and tool exit status: Compileall exit 0; unittest 60/60 exit 0; pytest 60 tests + 19 subtests exit 0.
- Outcome or important output summary: Replay offline đạt laptop 6/28, tivi 6/34, tủ lạnh 5/18; giá trị “Bộ xử lý AiPQ” được giữ nguyên; không group rỗng, added hoặc ambiguous merge.
- Files affected or inspected: Sửa parser, adapter, crawler, HTTP client và tests specification/persistence/attempt/HTTP; không đổi schema hoặc migration.
- Validation performed: Full unit suite và replay lossless trên ba artifact cũ.
- Validation result: Đạt toàn bộ; đủ điều kiện xóa sample cũ và recrawl.
- Redactions or logging limitations: Không ghi raw HTML, response body, cookie, token hoặc auth header.

### Entry 5 — 2026-07-17T14:15:23Z

- Human request summary: Xóa riêng sample cũ rồi crawl lại đúng ba URL, concurrency 1, common content/specs only, không location/discovery.
- AI response or decision summary: Xóa chính xác sáu artifact cũ, gửi tuần tự đúng ba request đã xác nhận, dừng check sau từng URL, rồi export/audit toàn bộ SQLite local.
- Sanitized terminal, CLI, and tool actions: Chạy ba lệnh crawl-product tuần tự với rate limit 5 giây và max attempts 3; export JSON; assertion toàn bộ ordered snapshot/EAV; kiểm tra diagnostics, models, HTTP status, task/run scope, git diff/status.
- Command and tool exit status: Cả ba crawl exit 0 và mỗi run succeeded=1, failed=blocked=discovered=0. Audit exit 0 sau khi sửa tên cột read-only từ stats_json sang counters_json. git diff --check exit 0.
- Outcome or important output summary: Laptop 6/28, tivi 6/34, tủ lạnh 5/18; tổng EAV 80; snapshot/EAV bằng nhau; HTTP 200 và transport attempt 1 cho cả ba; mọi item source=dom/provenance=[dom,json_ld]; added=ambiguous=0; location rows và non-common tasks bằng 0.
- Files affected or inspected: Tạo lại live-sample.db, products.json, ba JSON sản phẩm và crawl-audit-summary.json trong data/schema-sample; đọc TRACE_SPEC; cập nhật log này.
- Validation performed: Assertion 80 item, group/order/raw/typed/source/provenance; no label-prefix/pipe; model khác internal source key; no location/discovery; artifact inventory; git diff --check và git status --short.
- Validation result: Tất cả acceptance criteria đạt.
- Redactions or logging limitations: Chỉ lưu common product content/specifications và diagnostics đã whitelist; không lưu cookie, auth headers, browser state hoặc location offer.

## Files Touched

- Created: Session log hiện tại; `app/dmx-crawler/tests/test_crawler_attempts.py`; fresh local artifacts `data/schema-sample/live-sample.db`, `products.json`, `laptop.json`, `tivi.json`, `tu-lanh.json`, `crawl-audit-summary.json`.
- Changed: `app/dmx-crawler/dmx_crawler/parsers.py`, `utils.py`, `http.py`, `adapters/dmx.py`, `crawler.py`, `db.py`; `tests/test_specifications.py`, `test_spec_persistence.py`, `test_parsers.py`, `test_database.py`, `test_utils.py`, `test_http.py`; session log hiện tại.
- Replaced: Sáu artifact sample cũ được xóa bằng target path rõ ràng rồi tái tạo từ controlled recrawl.
- Deleted without replacement: None.
- Materially inspected: Logging/Harness policies, `docs/TRACE_SPEC.md`, parser/model/persistence/tests, old sample evidence và fresh SQLite audit data.
- Explicitly untouched: Schema/migration, location config/flow, root docs, Harness DB/schema, `.git`, crawler project cũ.

## Validation

- Checks performed: Core syntax compilation; `python -m compileall -q dmx_crawler tests scripts`; full unittest; pytest; replay offline old evidence; three sequential controlled requests; ordered snapshot/EAV audit; HTTP/diagnostics/model audit; no-location/no-discovery audit; `git diff --check`; `git status --short`.
- Results: Compileall pass; unittest 60/60 pass; pytest 60 pass + 19 subtests pass; live counts 6/28, 6/34, 5/18; total EAV 80; all snapshot/EAV equivalent; all HTTP 200; all diagnostics persisted; no supplemental JSON-LD-only field; git diff check pass.

## Errors and Blockers

- Errors: Harness bootstrap/query unavailable because pinned CLI is absent; apply_patch sandbox helper repeatedly failed with loopback RTM_NEWADDR, so deterministic guarded Python replacements were used and reviewed; one new test expected merge count 1 instead of evidence-backed 2 and was corrected; first audit referenced nonexistent `crawl_runs.stats_json`, then used actual `counters_json`.
- Blockers: Durable Harness intake/story/trace could not be created because `scripts/bin/harness-cli` is missing.
- Disposition: Không cài hoặc sửa Harness ngoài scope; mọi component/live acceptance vẫn được kiểm chứng. Session log captures detailed trace evidence.

## Final Outcome

- Status: Complete.
- Outcome summary: Parser/merge/typed/model/attempt metadata fixes hoàn tất; sample cũ được thay thế; đúng ba URL controlled crawl đều đạt acceptance với 80/80 EAV rows.
- Unresolved work: PostgreSQL-specific attempt/error FK return path và location-crawl attempt metadata vẫn là operational debt ngoài common-only sample scope; không ảnh hưởng ba run SQLite hiện tại.
- Suggested next actions: Review artifacts và diff; chỉ mở rộng URL set sau một xác nhận riêng.
- Duration estimate: 2723 seconds.
- Token estimate: Unavailable in this interface.
- Confirmations: Không commit, push, đổi branch, discovery, location crawl hoặc migration; không sửa project crawler cũ.

## Redaction Summary

- Redactions applied: None.
- Logging limitations: Chỉ ghi tóm tắt; không ghi dữ liệu nhạy cảm hoặc payload live.
- Sensitive values were not intentionally recorded: Yes.
