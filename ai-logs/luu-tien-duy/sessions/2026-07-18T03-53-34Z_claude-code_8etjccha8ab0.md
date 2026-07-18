# AI Coding Session Log

## Session Metadata

- `member`: Lưu Tiến Duy
- `member_slug`: luu-tien-duy
- `ai_client`: claude-code
- `interface`: vscode-extension
- `session_id`: 8etjccha8ab0
- `started_at_utc`: 2026-07-18T03-53-34Z
- `task_summary`: Audit repo và xây nền tảng dữ liệu local (PostgreSQL + pgvector) + backend API cho AI Product Advisor; ingestion từ data/dataset; hoãn tích hợp frontend. Loại trừ data/aircon-m1-test-data.
- `repository`: AI-Hackathon-2026
- `branch`: data

## Objective

Xây dựng data platform chạy local trên Ubuntu bằng PostgreSQL + pgvector, đóng gói Docker Compose, ingestion cho `data/dataset/` (catalog XLSX 14 ngành, 6 chính sách Markdown, chat scenarios JSON có mask PII), backend API tối thiểu (health + advisor endpoint deterministic theo contract Pydantic). Không dùng `data/aircon-m1-test-data/`. Kết nối frontend hoãn.

## Interaction Log

### Entry 1 — 2026-07-18T03-53-34Z

- Human request summary: Audit repo (Phase 1), sau đó xây data platform Postgres+pgvector + Docker Compose + ingestion + schema + backend API; loại trừ `data/aircon-m1-test-data/`. Người dùng chốt: embeddings qua API, migration SQL thuần, phạm vi data+API trước, hoãn frontend.
- AI response or decision summary: Hoàn tất audit Phase 1 (đọc PROJECT_MANAGEMENT, README, docs product/architecture, contracts, dữ liệu thật). Phát hiện: chưa có DB/server; specs XLSX khác nhau/ngành → JSONB; buy_product.json hỏng; policy md không có heading; drift backend↔frontend. Viết plan được duyệt. Bắt đầu implement theo plan.
- Sanitized terminal, CLI, and tool actions: Đọc file cấu hình/dữ liệu; parse XLSX bằng zipfile (read-only); jq inspect JSON; kiểm tra docker/uv/jq; `date -u` + sinh session id.
- Command and tool exit status: 0 (các lệnh inspect thành công).
- Outcome or important output summary: Xác định 14 sheet catalog; Máy lạnh 1039, Tủ Lạnh 1692 sp; `data/dataset/` không tracked (ignored bởi `/data/`); backend chưa có FastAPI server.
- Files affected or inspected: (inspected) PROJECT_MANAGEMENT.md, README.md, docs/README.md, docs/product/architecture/air-conditioner-advisor-m1.md, backend/app/contracts/schemas.py, backend/app/config/model_settings.py, data/dataset/*.
- Validation performed: Chưa (mới bắt đầu implement).
- Validation result: None
- Redactions or logging limitations: Chỉ đọc khóa `TEAM_MEMBER` trong `.env`; không đọc/ghi giá trị secret khác.

### Entry 2 — 2026-07-18 (product data platform)

- Human request summary: Chỉ làm product trước; giữ nguyên 100% cột product gốc (không thêm/bớt); tạm không đụng policy/markdown/json. Duyệt schema trước khi tạo. Chốt: 1 bảng products + attributes JSONB verbatim + tách brands/categories.
- AI response or decision summary: Xây infra Docker (pgvector), migration runner (SQL thuần), schema catalog, ingestion XLSX. Trình bày schema để duyệt trước. Phát hiện `productidweb` KHÔNG unique (2494 dòng trùng) → đổi khóa nghiệp vụ sang `sku` (unique tuyệt đối, 0 null) để không mất dòng nào. Sửa bug migrate runner (dùng autocommit để transaction() commit thật).
- Sanitized terminal, CLI, and tool actions: uv sync; docker compose up db (dev override loopback 55432); migrate; ingest x2; psql đếm; pytest.
- Command and tool exit status: 0 sau khi sửa (ban đầu migrate rollback do transaction lồng, đã fix).
- Outcome or important output summary: 8746 products (=8746 distinct sku, 0 mất), 129 brands, 14 categories; ingest lần 2 = 8746 skipped (idempotent); pgvector 0.8.5; attributes giữ nguyên header gốc tiếng Việt. Test: 7 ingestion + 159 full suite pass.
- Files affected or inspected: xem Files Touched.
- Validation performed: migrate; ingest x2 (idempotency); psql counts; pytest.
- Validation result: Pass.
- Redactions or logging limitations: Mật khẩu DB local dev (throwaway) không ghi vào log; chỉ đọc TEAM_MEMBER từ .env.

### Entry 3 — 2026-07-18 (Product Catalog API)

- Human request summary: Xây Product Catalog API trên Postgres hiện có (không advisor/policy/chat). 8 endpoint; SKU là identifier; search có attribute_filters (7 operator whitelist) validate key theo category; SQL parameterized; tách routes/schemas/services/repositories; SQL chỉ trong repository; OpenAPI examples + error envelope thống nhất; unit + integration test; verify luồng thật API→repo→Postgres 8746; không sửa frontend, không /advisor/respond. Audit trước, rồi commit+push lên branch data.
- AI response or decision summary: Audit (FastAPI có sẵn, chưa có api/services/repositories). Trình bày contract + file list, được duyệt. Triển khai FastAPI (pool psycopg), repository (toàn bộ SQL parameterized + filter/order builder), service (validate key theo category, page_size max 100, compare ≤5, same-category). Fix `list_brands` AmbiguousParameter bằng cast `::text`. Thêm host port configurable (BACKEND_PORT) do :8000 bị project khác chiếm.
- Sanitized terminal, CLI, and tool actions: uv sync (+psycopg-pool); pytest (unit+integration+full); docker compose build+up backend; curl các endpoint qua host :8080.
- Command and tool exit status: 0 (sau fix list_brands).
- Outcome or important output summary: 8 endpoint hoạt động; integration test chạy TestClient→repo→Postgres thật (8746). curl: /health up, categories total 14 sum 8746, search R-32 máy lạnh total 697 (rẻ nhất 5.190.000, attributes verbatim), key sai → 422 error envelope. Test: 36 API + full 195 pass.
- Files affected or inspected: xem Files Touched.
- Validation performed: pytest (36 API tests, full 195); docker container E2E curl.
- Validation result: Pass.
- Redactions or logging limitations: Không ghi secret; DB password local dev không ghi.

## Files Touched

- Created (data platform): docs/decisions/0012-postgres-pgvector-data-platform.md; backend/app/config/db_settings.py; backend/app/db/{__init__,connection,migrate}.py; backend/migrations/{0001_extensions,0002_catalog}.sql; backend/app/ingestion/{__init__,hashing,catalog,run}.py; scripts/ingest.py; infra/{docker-compose.yml,docker-compose.dev.yml,backend.Dockerfile}; backend/tests/unit/ingestion/{test_hashing,test_catalog}.py; this session log
- Created (catalog API): backend/app/api/{__init__,main,deps,errors}.py; backend/app/api/schemas/{__init__,common,catalog}.py; backend/app/api/routes/{__init__,health,categories,brands,products}.py; backend/app/repositories/{__init__,catalog_repository}.py; backend/app/services/{__init__,catalog_service}.py; backend/tests/unit/api/{test_filter_builder,test_catalog_service}.py; backend/tests/integration/api/test_catalog_endpoints.py
- Changed: pyproject.toml (+psycopg[binary], +openpyxl, +psycopg-pool); .env.example (DB/embedding/dataset/CORS vars); .gitignore (data/processed/); README.md (data platform + API sections); infra/docker-compose.yml (BACKEND_PORT); .env (appended local DB config, not committed)
- Deleted: None
- Materially inspected: PROJECT_MANAGEMENT.md, README.md, docs/README.md, docs/team/now/README.md, docs/product/architecture/air-conditioner-advisor-m1.md, backend/app/contracts/schemas.py, frontend-mvp/lib/types.ts, backend/app/config/model_settings.py, backend/app/tools/catalog_adapter.py, data/dataset/* (formats + all 14 sheet headers)

## Validation

- Checks performed: uv sync; alembic-free SQL migrate; catalog ingest (2 passes); psql counts + verbatim attributes; pytest (ingestion + full suite)
- Results: 8746 products / 8746 distinct sku / 129 brands / 14 categories; pass-2 fully idempotent (8746 skipped); pgvector 0.8.5 enabled; 166 tests pass (7 new + 159 existing)

## Errors and Blockers

- Errors: (fixed) migrate runner rolled back DDL due to nested transaction on a non-autocommit connection; (fixed) compose interpolation of POSTGRES_PASSWORD (moved db to env_file); (data) productidweb not unique → switched key to sku.
- Blockers: harness-cli binary not installed in this environment → Harness intake/matrix commands cannot run (documented limitation); identity luu-tien-duy not mapped to a tracker in docs/team/now (data-platform/infra work, flagged in ADR).
- Disposition: Resolved code issues; governance limitations documented, work proceeded per explicit user direction.

## Final Outcome

- Status: Product data platform + Product Catalog API done and pushed to branch data. KB/chat/advisor out of scope (other teams / not requested).
- Outcome summary: Local Postgres+pgvector data platform + read-only Product Catalog API (8 endpoints, SKU identifier, whitelisted attribute filters validated per category, parameterized SQL, layered routes/services/repositories, unified errors, OpenAPI examples). 195 tests pass; container E2E verified.
- Unresolved work: (out of this scope) knowledge base + embeddings, chat + PII, /advisor/respond, frontend integration.
- Suggested next actions: Other teams build KB/chat; agent team wraps the catalog API tools; reconcile backend↔frontend contract when integrating.

## Redaction Summary

- Redactions applied: Chỉ đọc `TEAM_MEMBER` từ `.env`; không ghi giá trị secret.
- Logging limitations: None
- Sensitive values were not intentionally recorded: Yes
