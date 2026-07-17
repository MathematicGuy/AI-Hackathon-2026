# Site reconnaissance: Điện Máy XANH

Ngày khảo sát: **2026-07-17** (Asia/Bangkok). Tài liệu này ghi lại những gì đã quan sát trực tiếp từ `https://www.dienmayxanh.com/` bằng một trình duyệt Chromium sạch và các yêu cầu HTTP đọc. Đây là căn cứ cho parser; giao diện hoặc endpoint của DMX có thể thay đổi.

## Phạm vi và giới hạn

Ba danh mục được kiểm tra:

| Mã | Trang danh mục | Prefix URL sản phẩm |
| --- | --- | --- |
| `laptop` | [/laptop](https://www.dienmayxanh.com/laptop) | `/laptop/` |
| `tivi` | [/tivi](https://www.dienmayxanh.com/tivi) | `/tivi/` |
| `tu-lanh` | [/tu-lanh](https://www.dienmayxanh.com/tu-lanh) | `/tu-lanh/` |

Chỉ thực hiện GET và các POST đọc cần thiết để lấy danh sách phường. Không thử vượt CAPTCHA, không xoay proxy/UA để né giới hạn, không gửi đơn hàng và không tự động xác nhận một địa chỉ thật. Hàm `locationConfirmV4()` thay đổi trạng thái địa điểm trong session; crawler chỉ được gọi khi operator đã cấu hình địa chỉ đại diện và chấp nhận việc đó.

## robots.txt và sitemap

[`/robots.txt`](https://www.dienmayxanh.com/robots.txt) trả HTTP 200. Các chỉ thị quan trọng đã thấy:

```text
User-agent: *
Allow: /
Disallow: /bin/
Disallow: /cms/
Disallow: /zzz/
Disallow: /price/
Disallow: /tracking/
Disallow: /aj/
Disallow: /support/

User-agent: GPTBot
Allow: /
Crawl-delay: 5

Sitemap: https://www.dienmayxanh.com/newsitemap/sitemap-cate
Sitemap: https://www.dienmayxanh.com/newsitemap/sitemap-product
Sitemap: https://www.dienmayxanh.com/newsitemap/sitemap-cateknh
Sitemap: https://www.dienmayxanh.com/newsitemap/sitemap-newsknh
Sitemap: https://www.dienmayxanh.com/newsitemap/sitemap-sieuthi
```

`/newsitemap/sitemap-product` là XML sitemap index. Nó trỏ tới các XML con dạng `/newsitemap/sitemap-product-2026-7?page=5`; XML con chứa `<url><loc>...</loc><lastmod>...</lastmod></url>`. Quy trình discovery:

1. Đọc sitemap index.
2. Đọc từng sitemap con (mới nhất trước nếu chạy giới hạn).
3. Chuẩn hóa `loc`, lọc đúng prefix ba danh mục, lưu `lastmod`.
4. Chỉ dùng trang danh mục làm fallback khi sitemap không đọc được hoặc không có URL phù hợp.

Sitemap danh mục (`sitemap-cate`) rất lớn và có nhiều URL facet; không dùng toàn bộ URL facet làm sản phẩm. Không tải các đường dẫn bị `Disallow`.

## Trang danh mục

HTML danh mục được server render. Cấu trúc đã quan sát (ví dụ `/tivi`):

```html
<ul class="listproduct">
  <li class="item __cate_1942" data-id="337187"
      data-productcode="3041094001952" data-price="24700000.0">
    <a class="main-contain" href="/tivi/...?..."
       data-id="337187" data-price="20990000.0"
       data-brand="Samsung" data-cate="Tivi" data-name="...">
      <p class="product-title">...</p>
      <strong class="price">...</strong>
      <p class="price-old">...</p>
      <span class="percent">...</span>
    </a>
  </li>
</ul>
```

Các selector/thuộc tính đang dùng trong parser:

* `li.item a.main-contain[href]` là link sản phẩm; `data-id` là mã sản phẩm DMX, còn `li[data-productcode]` là mã hàng/SKU nếu có.
* Giá hiện tại ưu tiên `a[data-price]` hoặc `strong.price`; giá gốc ưu tiên `li[data-price]` hoặc `.price-old`. Hai giá này có thể khác nhau.
* Tên: `data-name` rồi `.product-title`; thương hiệu: `data-brand`.
* Đã bán: `.rating_Compare span` (ví dụ `Đã bán 48k`); đánh giá: `.rating_Compare .vote-txt b`.
* Ảnh: `.item-img img[data-src]`, fallback `src`/`data-thumb`.
* Khuyến mãi: `.item-gift`, `.item-txt-online`, `.percent` (có thể vắng).

Một carousel “hot” cũng dùng class `listproduct` nhưng nằm trong `.owl-carousel`; phải deduplicate bằng mã sản phẩm/canonical URL. Link card có thể có `?utm_flashsale=1` hoặc fragment bộ lọc. Với URL sản phẩm, bỏ query và fragment tracking, chuyển host về `www.dienmayxanh.com`, giữ path lowercase.

## Trang chi tiết sản phẩm

Ba loại sản phẩm dùng cùng khung chi tiết. Ví dụ đã kiểm tra:

* [TCL 65P6K](https://www.dienmayxanh.com/tivi/google-tivi-tcl-ai-4k-65-inch-65p6k)
* [Toshiba GR-RS600WI-PMV(37)-SG](https://www.dienmayxanh.com/tu-lanh/tu-lanh-toshiba-inverter-460-lit-gr-rs600wi-pmv-37-sg)
* [Asus Vivobook Go E1504FA](https://www.dienmayxanh.com/laptop/asus-vivobook-go-e1504fa-r5-7520u-bq1160w)

Trang chi tiết có HTML giá trị ngay trong response HTML; trong lần quan sát không thấy một API giá riêng được gọi khi tải trang. JSON-LD Product là nguồn bổ sung, không phải nguồn duy nhất: sản phẩm laptop đã “SẢN PHẨM NGỪNG KINH DOANH” vẫn có JSON-LD với giá 0.

### Trường chung

| Trường | Nguồn quan sát |
| --- | --- |
| Tên | `h1`, rồi JSON-LD `Product.name` |
| Mã sản phẩm/model | section `.detail[data-id]`, `document.productId`, JSON-LD `sku`/`mpn`; model tên chỉ là heuristic |
| Thương hiệu | JSON-LD `brand.name`, hoặc `data-brand` |
| Giá bán/giá gốc | `.bs_price strong`/`em`; thuộc tính `data-priceorg`, `data-discountorigin` |
| Khuyến mãi | `.block__promo` (`data-scenario`, `.pr-txtb`, `.choosepromo` data attributes) |
| Đánh giá/đã bán | `.detail-rate`, `.quantity-sale`; JSON-LD `aggregateRating` là bổ sung |
| Ảnh | `#slider-default .item-img img[src|data-src|data-thumb]` |
| Mô tả | `#tab-2 .text-detail` |
| Thông số | `#tab-1 .box-specifi li`; label trong `strong`, value trong `aside` |
| Tình trạng | text “Ngừng kinh doanh”, nút mua, JSON-LD `offers.availability`; nếu không đủ bằng chứng lưu `unknown` |

Ví dụ giá tivi tại session mặc định:

```html
<div class="bs_price" data-priceorg="13640000.0"
     data-discountorigin="1650000.0">
  <strong>11.990.000₫</strong><em>13.640.000₫</em><i>(-12%)</i>
</div>
```

Thông số laptop, tivi và tủ lạnh không có cùng tập khóa. Lưu cả nhóm/label gốc và giá trị raw; chỉ chuẩn hóa khóa khi đã biết category. JSON-LD `additionalProperty` là fallback khi tab thông số không có trong HTML.

## Cơ chế địa điểm

Popup địa điểm được mở bằng `OpenLocation()`. Các tỉnh/thành mục tiêu được quan sát trực tiếp trong DOM:

| Địa điểm | `data-value`/province ID | `onclick` |
| --- | ---: | --- |
| Thành phố Hồ Chí Minh | `1027` | `changePoupProvinceV4(1027, this)` |
| Thành phố Hà Nội | `1000` | `changePoupProvinceV4(1000, this)` |
| Thành phố Đà Nẵng | `1020` | `changePoupProvinceV4(1020, this)` |

Tên hiển thị có thể có alias do thay đổi địa giới (Hồ Chí Minh/Bình Dương/Bà Rịa - Vũng Tàu; Quảng Nam/Đà Nẵng). ID số là khóa chính để so khớp; text chỉ là kiểm tra phụ.

Khi chọn tỉnh, JS hiện tại gọi request đã quan sát:

```text
POST https://www.dienmayxanh.com/Store/GetAllWardsByProvinceV4
Content-Type: application/x-www-form-urlencoded
provinceId=1000&viewName=ListWard
```

Response là HTML các anchor `.province-name.ward-name` có `data-value` và `changePoupWardV4(...)`. Popup yêu cầu thêm ward và địa chỉ đường phố:

```text
#hdLocationProvinceId
#hdLocationWardId
#hdLocationAddress
#hdLocationAddressId
#hdLocationDefault
```

`locationConfirmV4()` tạo object `newcustomer` gồm `ProvinceId`, `WardId`, `Address`, `isDefault`, `CustomerSex`, rồi POST tới `/Common/locationConfirm` cùng `cateUrl`/`productUrl`. Đây là request thay đổi session, không được gọi ngẫu nhiên hay chia sẻ giữa các địa điểm.

Sau reload, đối chiếu đồng thời:

1. JSON URL-encoded trong cookie `DMX_Personal` (`ProvinceId`, `WardId`, `ProvinceName`, `HasLocation`).
2. `#location-detail[data-province]` và text hiển thị.
3. Inline `dataDeli` (`ProductId`, `ProvinceId`, `WardId`, `Address`).

Nếu province/ward yêu cầu và trả về không khớp thì không lưu giá, tồn kho hay giao hàng; ghi `location_mismatch` vào task/error. Mỗi location phải dùng một `CookieJar`/browser context riêng. Không tái sử dụng session HCM cho Hà Nội hoặc Đà Nẵng.

## Giá, giao hàng và tồn kho theo địa điểm

Giá/khuyến mãi và một phần tình trạng được render theo cookie/session. Ban đầu `.quickdelivery .deliverytime` chỉ hiện:

```text
Chọn địa chỉ nhận hàng để biết thời gian giao.
```

Bundle `detailTGDD` hiện tại chứa hàm gọi delivery đã quan sát (không tự đoán payload khác):

```text
GET /Product/DeliveryDateTimeV4
  ?productId=<dataDeli.ProductId>
  &productCode=<dataDeli.ProductCode>
  &isTowPrice=<bool>&priceType=<n>
  &isDropShip=<document.isDropship>
  &isActiveOption2=<bool>
```

Response quan sát được là JSON `{code, msg, data: {html, runtime, ordertype}}`; HTML giao hàng được chèn vào `#status-delivery`. Bundle cũng có `/Product/GetDeliveryTime` (legacy) và các POST `/Ajax/...Stock...` cho cửa hàng gần nhất. Đây là endpoint giao diện hiện dùng, có thể đổi bất kỳ lúc nào; crawler phải coi lỗi/HTML không mong đợi là lỗi có thể retry, không suy đoán “còn hàng”.

Một GET `DeliveryDateTimeV4` với query province khác nhưng cookie HCM vẫn trả `dataDeli.ProvinceId=1027`. Vì vậy không được coi query string là bằng chứng địa điểm; chỉ cookie/DOM sau khi chọn địa điểm mới có giá trị.

## Phân loại dữ liệu và incremental crawl

* **Chung của sản phẩm:** tên, brand/model, category, mô tả, specs, gallery, mã sản phẩm. Lưu version khi content hash thay đổi.
* **Theo địa điểm:** sale/list price, promotion áp dụng, stock, ETA/phương thức giao hàng và bằng chứng location. Lưu version theo `(product, location)`.
* **Theo thời gian:** mọi version có `valid_from`/`valid_to`, `observed_at`, `crawl_run_id`; `lastmod` sitemap chỉ là tín hiệu discovery, không thay thế thời điểm quan sát.

Không crawl lại sản phẩm chung nếu response hash/content hash không đổi; giá, stock và delivery vẫn có state riêng cho từng địa điểm và lịch refresh riêng. Task/attempt/error lưu HTTP status, retry-after, response URL, returned location và traceback để có thể retry có kiểm soát.

## An toàn truy cập

Tôn trọng mức `Crawl-delay: 5` quan sát trong block `GPTBot`; crawler chọn mặc định bảo thủ `DMX_MIN_REQUEST_INTERVAL_SECONDS=5` cho mọi user-agent, retry có exponential backoff cho 408/425/429/5xx và `Retry-After`. Khi gặp 403/401, CAPTCHA, reCAPTCHA hoặc trang challenge thì dừng client/giảm tốc độ và ghi trạng thái blocked; không thử giải challenge. Chỉ dùng một User-Agent ổn định, không proxy rotation.

## Checklist tái khảo sát

Trước khi cập nhật selector hoặc location config, chạy thủ công trên một URL đại diện của mỗi category và lưu raw HTML/response headers ngoài database:

1. Kiểm tra robots và sitemap content type/namespace.
2. Kiểm tra `li.item a.main-contain`, `.bs_price`, `#location-detail`, `#tab-1`, `#tab-2`, JSON-LD.
3. Chọn từng province trong context riêng, lấy ward từ `GetAllWardsByProvinceV4`, rồi xác minh cookie/DOM.
4. Chỉ sau đó bật task location và kiểm tra mismatch/blocked path.

Khảo sát này không chạy live crawl tập dữ liệu và không xác nhận địa chỉ thực tế của người dùng.
