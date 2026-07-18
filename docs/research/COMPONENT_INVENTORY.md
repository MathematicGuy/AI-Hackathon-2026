# Component Inventory & Layout: Điện máy XANH

This document records the exact structure and component layout of the Điện máy XANH homepage.

## Core Visual Layout

```
+-------------------------------------------------------+
|                 Top Promotional Bar                   |
+-------------------------------------------------------+
|  Logo  | [Danh mục] | [Search Bar...] | Đăng nhập | Giỏ hàng |
|  [Hồ Chí Minh]  |  máy lạnh giá tốt  |  smart tivi  | ...    |
+-------------------------------------------------------+
|        Hero Promotional Slider         | Side Banner  |
|                                        | Side Banner  |
+-------------------------------------------------------+
|                     Promo Bar                         |
+-------------------------------------------------------+
|                  Category Icon Grid                   |
+-------------------------------------------------------+
|      Flash Sale Showcase (Countdown + Tabs + Slider)  |
+-------------------------------------------------------+
|      Category / Product Lists (5-column Grid Cards)   |
+-------------------------------------------------------+
|               Tech Topics Grid (4-cols)               |
+-------------------------------------------------------+
|                       Footer                          |
+-------------------------------------------------------+
```

## Detailed Sections

### 1. Sticky Header & Navigation (`src/components/Header.tsx`)
- **Logo:** `điện máy XANH` text with yellow icon.
- **Category Button:** Click opens a list of products.
- **Search Bar:** Centered with autocomplete dropdown capabilities.
- **Location Picker:** Region name displaying a modal for switching province/city.
- **Sub-navigation links:** Horizontal row of popular tags (`máy lạnh giá tốt`, `tủ lạnh`, `quạt điều hòa`, `smart tivi`).

### 2. Promo Carousel (`src/components/HeroCarousel.tsx`)
- **Main Slider:** Left-aligned carousel, automatically sliding with pagination pills.
- **Side Banners:** Stack of two promotional banner cards.
- **Double promo banner below:** Horizontal banner cards (e.g., Paylater, bank discounts).

### 3. Category Grid (`src/components/CategoryGrid.tsx`)
- **Structure:** 8-column grid containing circular icons + category name.
- **Badges:** Absolute positioned top-left badges with labels like `"HOT"`, `"-50%"`, `"Trả góp 0%"`.

### 4. Flash Deals / Sales (`src/components/FlashSale.tsx`)
- **Clock Header:** Countdown display `"Khuyến mãi online: Chỉ còn [HH:MM:SS]"`.
- **Filters:** Tab buttons for category types (Air conditioners, washing machines, rice cookers, etc.).
- **Product list:** Horizontal slider with progress bars showing number of coupons remaining.

### 5. Product Cards (`src/components/ProductCard.tsx`)
- **Badge:** Top tag (e.g., `"Online giá rẻ quá"`).
- **Media:** Product image container.
- **Content:** Title text, sub-options / specifications (e.g. dimensions, capacity), discounted price (bold red), original price (strikethrough gray), and percent off badge.
- **Metadata:** Rating stars, sold count, and gift text `"100% CÓ QUÀ TẶNG"`.

### 6. Tech Topics Grid (`src/components/Topics.tsx`)
- **Structure:** 4-column cards containing tech news/advices.
- **Search Tag Cloud:** Bottom horizontal wrapping pills of popular search terms.

### 7. Footer (`src/components/Footer.tsx`)
- **Columns:** 4-column structured lists separating hotlines, company policies, customer services, and MWG ecosystem sister brands.
- **Copyright & Registration logos:** Ministry of Industry & Trade verification badges at the bottom.
