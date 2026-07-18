# Điện máy XANH Behaviors

## Shared

- Header search validates at least two characters and navigates to local `/tim-kiem`.
- Category trigger opens a local overlay menu. Location trigger opens a four-city selector.
- Mega-menu categories switch in place; every campaign and service destination resolves to a local route.
- Route changes use Next.js client navigation and a short page entrance transition.
- Product images use an error fallback so blocked CDN requests do not leave blank cards.
- Success and failure actions surface a toast. Forms keep an inline error next to the invalid input.
- The root layout suppresses extension-injected attribute differences while deterministic server/client snapshots prevent app-created hydration mismatches.

## Homepage

- Hero advances every four seconds and can be selected by dots.
- Flash sale and featured tabs replace product cards with a fade transition.
- Category, product, campaign, article and tag interactions navigate to local routes.

## Listing And Search

- Filter pills and price sorting are client-side and preserve a visible empty state.
- Product cards lift by `2px` and gain a light shadow on hover.
- Mobile lists keep two columns and reduce card padding and type size.

## Product And Cart

- Product thumbnail click changes the active gallery image.
- Package selection updates the selected price without server/client time-based values.
- Add-to-cart persists after mount in `localStorage`; the server snapshot remains empty to avoid hydration differences.
- Cart quantity has a minimum of one. Removing the last item shows the cloned empty-cart screen.

## Forms

- Login accepts Vietnamese phone numbers in the `0xxxxxxxxx` format.
- Successful login stores the local account snapshot and navigates to `/lich-su-mua-hang`.
- Checkout requires name, phone, city, district and address.
- Mock submit actions never call the original site.

## Account And Flash Sale

- Account status tabs show a loading skeleton before applying the local filter; the first visit keeps the cloned empty state and can reveal contextual sample orders.
- Address, coupon and date-range actions validate input and report success or failure through inline messages and toast notifications.
- Flash Sale tabs, sorting and load-more controls update a local product set; unavailable campaign groups render a deliberate empty state.
- The football game and campaign rules open local dialogs and never redirect to the original campaign.

## Chatbot

- The global launcher expands into a responsive conversation panel with welcome, reset, close, input and quick-link controls.
- Replies are deterministic local intents for products, pricing, warranty, delivery and stores; no external AI or original-site API is called.
- Empty input is rejected, simulated request failure shows a clear error with a retry action, and successful messages remain in the conversation log.
