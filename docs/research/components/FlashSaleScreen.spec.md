# FlashSaleScreen Specification

## Overview
- **Target file:** `src/components/FlashSalePage.tsx`
- **Route:** `src/app/flashsale/page.tsx`
- **Screenshot:** `docs/design-references/mega-menu-info-flashsale-reference.png`
- **Interaction model:** tabs and sort buttons filter local data; cards navigate to local product detail pages.

## DOM Structure
- Shared site header and mega menu.
- World Cup campaign hero with background stadium, campaign artwork, rules strip and hotline.
- Sticky/scrollable campaign category navigation.
- Repeated sale groups with image title, sort controls, responsive product grids and load-more control.

## Computed Styles
- hero background source: `de956ecb3e56aa9d649d40c3b6dcfa05.jpg`, centered top
- hero desktop height: `500px`; campaign artwork: `1200px × 460px`
- campaign content max-width: `1200px`
- headline image: `1200px × 200px`
- sale group background: `#279bea`; product gap `10px`
- desktop product width from original carousel: `228px`, five visible columns
- body campaign background continues dark blue to blue; cards remain white

## States & Behaviors
- Category tabs: `Flashsale`, `Điện lạnh`, `Điện tử`, `Gia dụng`, `Máy lọc nước`, `Việc Bếp Dễ Dàng`, `Sức khoẻ - Làm đẹp`, `Hàng tiện ích`.
- Sort states: `Nổi bật`, `% giảm nhiều`, `Giá thấp đến cao`.
- Empty filter renders a contextual empty state with reset button.
- `Xem thể lệ` opens a local modal; hotline uses `tel:`; cards use `/san-pham/[slug]`.
- Load more reveals another deterministic batch and reports success via toast.

## Assets
- Campaign background, campaign artwork, category banner and group-title art from the original CDN, stored under `public/images/flashsale/`.
- Product assets reuse the catalog and `SafeImage` fallback.

## Responsive Behavior
- **Desktop 1440px:** 1200px content, five product columns.
- **Tablet 768px:** three product columns; hero artwork uses cover/contain crop; tabs scroll horizontally.
- **Mobile 390px:** two product columns; hero reduces to about 280px; rules and hotline wrap; controls remain horizontally scrollable with no page overflow.
