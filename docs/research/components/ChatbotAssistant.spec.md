# ChatbotAssistant Specification

## Overview
- **Target file:** `src/components/ChatbotAssistant.tsx`
- **Screenshot:** `docs/design-references/chatbot-open-reference.png`
- **Interaction model:** global fixed launcher; click opens/closes; form submission produces deterministic local assistant replies.

## DOM Structure
- Collapsed launcher with suggestion bubble, circular bot image and `BETA` badge.
- Open panel with blue identity header, scrollable conversation, composer and two-line AI disclaimer.

## Computed Styles
- launcher bottom `80px`, desktop right `56px`; icon `55px`; suggestion max-width `250px`
- open panel desktop: width `360px`, height/max-height `520px`, right `16px`, bottom `24px`, radius `8px`, z-index above overlays
- header: height `49px`, background `#2a83e9`, padding `8px 16px`
- mascot header `28px`; message mascot `36px`; welcome bot `80px`
- conversation padding `8px 8px 16px`; incoming bubble background `#f2f5f9`, radius `20px`
- composer height about `51px`, background `#f2f5f9`, blue focus border, radius `20px`
- textarea font `15px/18px`; disclaimer `8.5px`, color `#9ca3af`

## States & Behaviors
- Collapsed, open, sending, answered, reset and failed states.
- Send is disabled for blank input; Enter submits, Shift+Enter creates a line break.
- Local intent replies cover price/promotion, warranty, delivery, store address and product recommendations.
- Unknown intent returns a helpful fallback; errors show inline retry plus toast.
- Reset clears conversation and restores the welcome message; panel closes with header X or Escape.
- Time labels are generated only after mount/submission using fixed `vi-VN` formatting, preventing hydration mismatches.

## Assets
- `chat-bot.png` and `mascot.png` from the original chatbot bundle, stored in `public/images/chatbot/`.

## Responsive Behavior
- **Desktop:** `360px × 520px`, bottom-right.
- **Tablet:** same width with 16px edge spacing.
- **Mobile <= 480px:** inset `12px`, width `calc(100vw - 24px)`, height `min(620px, calc(100dvh - 90px))`; launcher right/bottom `16px`; safe-area padding applied.
