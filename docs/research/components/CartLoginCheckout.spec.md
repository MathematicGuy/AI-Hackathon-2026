# CartLoginCheckout Specification

## Overview

- **Target routes:** `/gio-hang`, `/dang-nhap`, `/thanh-toan`
- **Interaction model:** validated client forms and persistent demo cart

## Cart

- Empty state is vertically centered with a basket illustration and blue home button.
- Filled state uses a white `680px` order card, product rows, quantity controls and a red total.

## Login

- Light gray page; illustration left and white login card right on desktop.
- Phone input and blue `TIẾP TỤC` button are pill-shaped.
- Mobile stacks the illustration above the form.

## Checkout

- Delivery form and order summary are two columns on desktop and one column below `768px`.
- Invalid controls use red border, an inline message and an error toast.
- Submit success shows a confirmation state without making an external request.
