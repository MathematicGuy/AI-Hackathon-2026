# Điện máy XANH Page Topology

## Shared Shell

1. Top campaign banner, full viewport width.
2. Blue header with logo, category trigger, search, account, cart and location.
3. Gray quick-link row below the main header.
4. Route content in a centered `1200px` container.
5. Support/company/ecosystem footer on all content routes except checkout.

## Route Templates

| Local route | Original template | Interaction model |
| --- | --- | --- |
| `/` | Homepage | timed hero, click-driven tabs and sliders |
| `/danh-muc/[slug]` | Industry listing such as `/may-lanh` | click-driven filters, sort and cards |
| `/san-pham/[slug]` | Product detail | gallery, package selector, cart actions |
| `/khuyen-mai/[slug]` | Promotion article | reading page and related articles |
| `/tim-kiem?q=` | Search results | query-driven listing and empty state |
| `/gio-hang` | Cart | quantity updates, remove, empty state |
| `/dang-nhap` | Purchase history login | phone validation then mock OTP state |
| `/lich-su-mua-hang` | Account and purchased-order dashboard | order filters, date range, addresses and coupons |
| `/flashsale` | World Cup campaign landing page | campaign tabs, game modal, sorting and sale cards |
| `/tien-ich/[slug]` | Information and utility service detail | validated contextual service form |
| `/thanh-toan` | Checkout | validated delivery form and order summary |

## Shared Overlays

- Mega menu: `230px` category rail plus scrollable content panel on desktop; inset modal with horizontal category rail on mobile.
- Chatbot: collapsed official launcher globally; `360x520px` desktop conversation panel and viewport-inset mobile panel.
- Date, campaign rules and game dialogs trap the visual interaction inside a dimmed backdrop and expose explicit close controls.

## Responsive Topology

- Desktop `1280px+`: full header, five product columns, two-column product detail, account sidebar and complete status row.
- Tablet `768px`: compact header, three product columns, account navigation becomes a horizontal rail and product detail stacks below gallery.
- Mobile `375px`: two-row header, horizontally scrollable navigation, two product columns, inset mega menu/chatbot and single-column account content.
