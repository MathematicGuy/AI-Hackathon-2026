# MegaMenu Specification

## Overview
- **Target file:** `src/components/MegaMenu.tsx`
- **Screenshot:** `docs/design-references/mega-menu-hot-reference.png`, `docs/design-references/mega-menu-info-flashsale-reference.png`
- **Interaction model:** click-to-open overlay; click or hover a left navigation row to switch panels; Escape/backdrop closes.

## DOM Structure
- Full viewport dark overlay below/around the header.
- Desktop menu is anchored to the category button and contains a left navigation list plus one active content panel.
- Mobile menu is a full-height drawer with the same groups presented as collapsible content.

## Computed Styles

### Overlay
- position: fixed; inset: 0; z-index: 70
- background: `rgba(0, 0, 0, 0.5)`

### Desktop Menu
- left list: width `230px`, height `440px`, background `#f2f4f7`, radius `0 0 0 8px`
- content panel: width `777px`, height `440px`, padding `10px`, background `#fff`, radius `0 8px 8px 0`, overflow-y auto
- left row: width `220px`, height `40px`, padding-left `12px`, font `14px/18px`
- inactive row: background `#eaecf0`; active row: white with blue bold text and right pointer
- section title: font `12px/20px`, weight `700`, margin-bottom `10px`
- item: width `70px`, margin `10px`, padding `7px 0`, radius `8px`, font `12px/16px`, centered
- icon frame: `48px × 48px`, margin-bottom `5px`; image max-size `90%`

## States & Behaviors
- Opening defaults to `Chương trình hot` and locks document scroll.
- Clicking or hovering another row switches content without navigation.
- `Thông tin - Dịch vụ tiện ích` shows two titled groups and all items captured from the original.
- All item destinations must be local routes; unsupported services open an in-app information state/toast, never the original site.
- Hover: item background becomes `#f4f8ff`; text becomes `#0068d7`.

## Assets
- Use the original menu icon URLs captured from `cdnv2.tgdd.vn`; download them to `public/images/menu/`.

## Responsive Behavior
- **Desktop >= 1024px:** exact two-column `230px + min(777px, available width)` panel anchored under the category control.
- **Tablet 768px:** centered modal up to `calc(100vw - 32px)` with `220px` navigation and fluid content.
- **Mobile 390px:** right drawer, width `min(92vw, 380px)`, category chips across the top, two-column item grid, close button always visible.
