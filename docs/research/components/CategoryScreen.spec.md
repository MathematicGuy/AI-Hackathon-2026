# CategoryScreen Specification

## Overview

- **Target route:** `src/app/danh-muc/[slug]/page.tsx`
- **Reference:** original `/may-lanh`
- **Interaction model:** click-driven filtering and sorting

## DOM Structure

1. Shared site shell.
2. Breadcrumb and category title.
3. Wide category campaign banner.
4. Brand/filter pills and result count.
5. Product grid and related category links.

## Styles

- Container: `max-width: 1200px`, centered.
- Filter panel: white, `border-radius: 12px`, `padding: 16px`.
- Desktop product grid: five equal columns with `12px` gaps.
- Active filter: `#288ad6` background and white text.

## Responsive Behavior

- Desktop: five columns and a single-line filter bar.
- Tablet: three columns and wrapping filters.
- Mobile: two columns, compact card spacing, horizontally scrollable pills.
