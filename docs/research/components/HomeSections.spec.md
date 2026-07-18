# HomeSections Specification

## Overview

- **Target files:** homepage section components in `src/components/`
- **Interaction model:** time-driven hero and click-driven tabs

## Layout

- Route background: `rgb(242, 244, 247)`.
- Main content max width: `1200px`.
- Category grid: eight columns on desktop, six on tablet, three on mobile.
- Product grids: five columns desktop, three tablet, two mobile.
- Card background: `#fff`; radius `8px` to `12px`; divider `#f1f1f1`.

## Visual Tokens

- Primary blue: `#288ad6`.
- Accent yellow: `#ffe500`.
- Price red: `#d70018`.
- Product title: `14px/20px`; price: `18px`, weight `700`.

## Behaviors

- Every data card is a local link.
- Broken images show a neutral product fallback.
- Empty tabs render a clear empty state instead of a blank grid.
