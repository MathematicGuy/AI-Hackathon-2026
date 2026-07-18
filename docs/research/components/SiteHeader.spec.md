# SiteHeader Specification

## Overview

- **Target file:** `src/components/Header.tsx`
- **Interaction model:** click-driven menu, search and location selector

## Computed Styles

- Body font: `Arial, Helvetica, sans-serif`.
- Main header background: `rgb(40, 138, 214)`.
- Content max width: `1200px`.
- Search control height: `40px`; background `#fff`; pill radius `9999px`.
- Quick links row: light gray background with blue `14px` links.

## States

- Header actions: blue tint on hover, `translateY(1px)` on active, lower opacity when disabled.
- Search: inline error below input and toast on invalid submit.
- Category menu and location picker: fixed overlay, close on explicit button or successful selection.

## Responsive Behavior

- Desktop: all controls in one row, quick links visible.
- Tablet: search remains flexible; account label can collapse.
- Mobile: logo and actions on first row, search occupies full second row, quick links horizontally scroll.
