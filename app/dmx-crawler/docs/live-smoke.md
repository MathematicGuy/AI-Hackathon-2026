# Live smoke run

Ngày 2026-07-17, chạy với `DMX_MIN_REQUEST_INTERVAL_SECONDS=5`, một URL tivi duy nhất:

`https://www.dienmayxanh.com/tivi/smart-tivi-neo-qled-samsung-ai-4k-55-inch-qa55qn80f`

Các bước đã chạy:

1. `discover --source category --category tivi --limit 1` — phát hiện mã DMX `337187`.
2. `crawl products --category tivi --limit 1 --force` — lưu content version.
3. `crawl location --location hcm --category tivi --limit 1 --force` — dùng CookieJar/session riêng, gọi ward endpoint, `/Common/locationConfirm`, trang sản phẩm và `/Product/DeliveryDateTimeV4`.

Kết quả quan sát tại thời điểm chạy (giá có thể thay đổi):

- Tên: Smart Tivi Neo QLED Samsung AI 4K 55 inch QA55QN80F
- Thương hiệu: Samsung
- Giá bán: `20.990.000` VND; giá gốc: `24.700.000` VND
- Mã tỉnh/ward trả về: `1027 / 100694` (Hồ Chí Minh / Phường Bến Thành)
- Delivery response xác nhận địa chỉ đã chọn nhưng báo sản phẩm tạm hết hàng tại địa chỉ; snapshot vẫn lưu `stock_status=out_of_stock`, không suy đoán còn hàng.

Không lưu cookie, raw HTML hoặc địa chỉ khách hàng thật trong repository. Ba location trong config được crawl bằng context độc lập; smoke run live chỉ dùng HCM để giữ tải thấp. Các test adapter offline kiểm tra Hanoi mismatch và hai CookieJar độc lập.
