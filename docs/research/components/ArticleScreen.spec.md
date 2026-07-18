# ArticleScreen Specification

## Overview

- **Target route:** `src/app/khuyen-mai/[slug]/page.tsx`
- **Interaction model:** reading page with related navigation

## Layout And Styles

- Main article column: about `820px`; related rail: about `320px`.
- Heading: `30px`, weight `700`, line-height about `1.25`.
- Metadata: `14px`, muted gray.
- Article body: `17px`, line-height `1.75`; images full column width.
- Tables scroll horizontally on narrow screens.

## Responsive Behavior

- Desktop: article plus related rail.
- Tablet/mobile: single column; related cards move below article.
