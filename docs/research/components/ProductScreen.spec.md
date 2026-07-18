# ProductScreen Specification

## Overview

- **Target route:** `src/app/san-pham/[slug]/page.tsx`
- **Reference:** original Casper QC-09IU36A detail page
- **Interaction model:** gallery, package selection and cart actions

## DOM Structure

1. Breadcrumb and product title/rating row.
2. Two-column product area: gallery left, purchase card right.
3. Commitments and product highlights.
4. Technical specification table.
5. Related product carousel/grid.

## Styles

- Main content max width: `1200px`.
- Gallery and purchase panel: white background, `16px` radius.
- Purchase campaign block: orange gradient; selected package has blue border.
- Price: `24px`, weight `700`, color `#d70018`.
- Primary buy action: `#f57c00`; cart action: white with blue border.

## Responsive Behavior

- Desktop: `minmax(0, 1.25fr) minmax(360px, .8fr)`.
- Tablet/mobile: one column; purchase panel follows gallery; action buttons wrap.
