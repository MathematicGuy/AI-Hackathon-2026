# Brand Identity & Design Tokens: Điện máy XANH

This document records the exact styles and design tokens extracted from the target website.

## Colors

| Token Name | Computed Value | Description |
| :--- | :--- | :--- |
| **Brand Blue (Primary)** | `#0088dd` | Main brand color for headers, menus, search magnifying glass, active elements, and highlights. |
| **Brand Yellow (Accent)**| `#fff100` / `#ffd400` | Secondary accent color used in the logo, location editor buttons, and special discount highlights. |
| **Page BG** | `#f3f3f3` | Main content background. Light gray to give high contrast to white product cards. |
| **Card BG** | `#ffffff` | Pure white. Used for sections, dropdown menus, and product cards. |
| **Text Main** | `#333333` | Primary body text. Highly legible charcoal black. |
| **Text Secondary/Muted**| `#666666` / `#999999` | Secondary description texts, specifications, sold count, and original strikethrough prices. |
| **Text Alert/Price** | `#bf0811` / `#d0021b` | Main price color, discount percentages, and countdown clock labels. |
| **Borders & Dividers** | `#e0e0e0` / `#f1f1f1` | Thin separation borders between items and list sections. |

## Typography

- **Font Family:** `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` (Standard Vietnamese web font stack).
- **Sizes & Line Heights:**
  - Horizontal sub-navbar links: `14px` (`0.875rem`), line-height `1.4`
  - Section Headings: `20px` (`1.25rem`), font-weight `bold` (`700`)
  - Product Card Title: `14px` (`0.875rem`), line-height `1.4`, font-weight `medium` (`500`)
  - Product Card Price: `16px` (`1rem`), font-weight `bold` (`700`)
  - Muted Specifications: `12px` (`0.75rem`), line-height `1.3`

## Spacing & Layout

- **Maximum Page Container Width:** `1200px` (centered on screen, with gutters for mobile viewports).
- **Grid Layouts:**
  - Category Circle/Grid Items: 8 columns on desktop (width ~120px each).
  - Product Grid (Showcase/Suggestions): 5 columns on desktop (card width ~228px, grid gap `15px`).
  - Tech Topics Grid: 4 columns on desktop.

## Border Radius & Elevation

- **Card Rounded Corners:** `8px` (`0.5rem`) or `12px` (`0.75rem`).
- **Button Rounded Corners:** `4px` (`0.25rem`) or `24px` (`1.5rem`) for rounded pills.
- **Product Card Hover Shadow:** `0 4px 15px rgba(0, 0, 0, 0.08)` with a translation effect of `translateY(-3px)`.
