# AccountOrdersScreen Specification

## Overview
- **Target file:** `src/components/AccountOrdersScreen.tsx`
- **Route:** `src/app/lich-su-mua-hang/page.tsx`
- **Screenshot:** `docs/design-references/account-orders-reference.png`
- **Interaction model:** click-driven account navigation, order status filters and date-range modal.

## DOM Structure
- Page background `#f1f3f6`, shared header, max-width `1200px` account grid.
- Left account sidebar with purchased orders, address book, coupons, logout and VIP points card.
- Main order area with title/date range, seven status tabs and order list/empty state.

## Computed Styles
- desktop columns approximately `400px 1fr` with `37px` gap in the screenshot; implementation uses `280px 1fr` within 1200px to preserve the original proportions at normal viewport.
- sidebar active row height `54px`, pale gray background and green icon.
- status buttons height `48px`, white background, `1px #c7c7c7` border; active border/text `#0068d7`.
- content card white with minimum height `465px`.
- empty illustration blue shopping bag, title `24px`, helper text `16px`, local category shortcut buttons.
- VIP card background `#fff7c9`, radius `12px`.

## States & Behaviors
- Seven filters: all, pending, confirmed, shipping, delivered, cancelled and successful.
- Include contextual mock orders in non-default filters; `Tất cả` defaults to the screenshot empty state until sample-data toggle is selected.
- Date range modal validates start <= end and formats dates with `vi-VN`.
- Sidebar pages display local panels and clear empty states; logout redirects to `/dang-nhap` with toast.

## Responsive Behavior
- **Desktop 1280px:** two columns and horizontal status row.
- **Tablet 768px:** sidebar becomes a horizontal account menu; tabs scroll.
- **Mobile 375px:** one column, condensed title/date controls, full-width empty state and two-column quick-category buttons.
