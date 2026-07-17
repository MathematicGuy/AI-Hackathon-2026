# Frontend MVP (Testing Harness) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `frontend-mvp/`, a testing-only Next.js frontend that renders all 8 `RecommendationOutput.answer_type` states from mock data, swappable to the real backend by flipping one env var.

**Architecture:** A single chat route drives a keyword-matched mock scenario engine that returns canned `AdvisorResponse` fixtures. `AnswerRenderer` switches on `answer_type` and dispatches to per-state components. All data flows through one typed function `sendMessage` in `lib/advisor-api.ts` that branches mock vs. live on `NEXT_PUBLIC_ADVISOR_MODE`. The UI renders server-owned fields only — no client-side ranking, price math, eligibility, or badge computation.

**Tech Stack:** Next.js 15 (App Router) + TypeScript, Tailwind CSS, shadcn/ui primitives (copied into `components/ui/`), Vitest (unit), Playwright (E2E), npm.

## Global Constraints

- **Framework:** Next.js 15 App Router + TypeScript. Package manager: **npm**.
- **Root:** everything lives under `frontend-mvp/`. No existing `frontend/` — created fresh.
- **Styling:** Tailwind CSS + shadcn/ui primitives copied into `frontend-mvp/components/ui/` (not a black-box dep).
- **UI copy:** Vietnamese. Missing fields render `"không có"` (text) or `"chưa rõ"` (numeric/price), never inferred.
- **Read-only rendering:** the frontend renders server-owned fields only. No client-side ranking, price math, eligibility, badge computation, or evidence selection.
- **Default mode:** `NEXT_PUBLIC_ADVISOR_MODE=mock`. Runs with zero backend.
- **Single swap point:** components import data only via `sendMessage` from `lib/advisor-api.ts`. Backend integration = set `NEXT_PUBLIC_ADVISOR_MODE=live` + `NEXT_PUBLIC_ADVISOR_API_URL`; no component or type changes.
- **Three formal roles only:** `best_overall`, `best_value`, `cheapest_qualified`. `best_for_primary_priority` is a display badge (`BadgeKind`), never a 4th `RoleWinner`.
- **Dedup:** a product appears once even with multiple badges; badges merge by `product_id`.
- **Path alias:** `@/*` → `frontend-mvp/*`.
- **Answer-type testids:** each rendered answer wrapper carries `data-testid={`answer-${answer_type}`}`; each product card carries `data-testid={`product-card-${product_id}`}`; each badge carries `data-testid="badge"`. These are the Playwright anchors — do not rename.

---

### Task 1: Scaffold Next.js 15 + Tailwind + tooling

**Files:**
- Create: `frontend-mvp/package.json`
- Create: `frontend-mvp/tsconfig.json`
- Create: `frontend-mvp/next.config.mjs`
- Create: `frontend-mvp/postcss.config.mjs`
- Create: `frontend-mvp/tailwind.config.ts`
- Create: `frontend-mvp/app/globals.css`
- Create: `frontend-mvp/app/layout.tsx`
- Create: `frontend-mvp/app/page.tsx`
- Create: `frontend-mvp/lib/utils.ts`
- Create: `frontend-mvp/.env.example`
- Create: `frontend-mvp/.gitignore`
- Create: `frontend-mvp/README.md`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a runnable Next.js app; `cn(...classes)` from `@/lib/utils`; npm scripts `dev`, `build`, `start`, `typecheck`, `test`, `test:e2e`.

- [ ] **Step 1: Create `frontend-mvp/package.json`**

```json
{
  "name": "frontend-mvp",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "next": "15.1.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "2.6.0",
    "lucide-react": "0.469.0",
    "@radix-ui/react-dialog": "1.1.4",
    "@radix-ui/react-slot": "1.1.1"
  },
  "devDependencies": {
    "typescript": "5.7.2",
    "@types/node": "22.10.2",
    "@types/react": "19.0.2",
    "@types/react-dom": "19.0.2",
    "tailwindcss": "3.4.17",
    "postcss": "8.4.49",
    "autoprefixer": "10.4.20",
    "tailwindcss-animate": "1.0.7",
    "vitest": "2.1.8",
    "@playwright/test": "1.49.1"
  }
}
```

- [ ] **Step 2: Create `frontend-mvp/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules", "tests-e2e"]
}
```

- [ ] **Step 3: Create config files**

`frontend-mvp/next.config.mjs`:
```js
/** @type {import('next').NextConfig} */
const nextConfig = {};
export default nextConfig;
```

`frontend-mvp/postcss.config.mjs`:
```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

`frontend-mvp/tailwind.config.ts`:
```ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: "hsl(var(--muted))",
        "muted-foreground": "hsl(var(--muted-foreground))",
        primary: "hsl(var(--primary))",
        "primary-foreground": "hsl(var(--primary-foreground))",
        card: "hsl(var(--card))",
        "card-foreground": "hsl(var(--card-foreground))",
        destructive: "hsl(var(--destructive))",
        "destructive-foreground": "hsl(var(--destructive-foreground))",
      },
      borderRadius: { lg: "0.5rem", md: "0.375rem", sm: "0.25rem" },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
```

- [ ] **Step 4: Create `frontend-mvp/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;
  --muted: 210 40% 96%;
  --muted-foreground: 215 16% 47%;
  --primary: 221 83% 53%;
  --primary-foreground: 210 40% 98%;
  --card: 0 0% 100%;
  --card-foreground: 222 47% 11%;
  --destructive: 0 72% 51%;
  --destructive-foreground: 210 40% 98%;
  --border: 214 32% 91%;
}

* { border-color: hsl(var(--border)); }
body { background: hsl(var(--background)); color: hsl(var(--foreground)); }
```

- [ ] **Step 5: Create `frontend-mvp/lib/utils.ts`**

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 6: Create `frontend-mvp/app/layout.tsx`**

```tsx
import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tư vấn máy lạnh — MVP test",
  description: "Frontend thử nghiệm luồng tư vấn máy lạnh (mock data).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 7: Create a placeholder `frontend-mvp/app/page.tsx`** (replaced in Task 9)

```tsx
export default function Page() {
  return <main className="p-6">Đang khởi tạo…</main>;
}
```

- [ ] **Step 8: Create `frontend-mvp/.env.example`**

```bash
# mock (default) runs with zero backend; live plugs in the real advisor API
NEXT_PUBLIC_ADVISOR_MODE=mock
NEXT_PUBLIC_ADVISOR_API_URL=http://localhost:8000
```

- [ ] **Step 9: Create `frontend-mvp/.gitignore`**

```gitignore
node_modules
.next
.env
.env.local
playwright-report
test-results
```

- [ ] **Step 10: Create `frontend-mvp/README.md`**

````markdown
# frontend-mvp

Testing-only frontend for the Milestone 1 máy lạnh advisor. Renders all 8
`answer_type` states from mock fixtures.

## Run

```bash
npm install
npx playwright install chromium   # once, for E2E
cp .env.example .env
npm run dev                        # http://localhost:3000
```

## Swap to the real backend

Set in `.env`:
```bash
NEXT_PUBLIC_ADVISOR_MODE=live
NEXT_PUBLIC_ADVISOR_API_URL=http://<backend-host>
```
Only the data source changes — no component or type edits.

## Test

```bash
npm run typecheck
npm run test        # Vitest unit
npm run build
npm run test:e2e    # Playwright smoke (all 8 answer_types)
```

## Mock triggers (type these to reach each state)

| Type this | State |
| --- | --- |
| `so sánh …` | comparison |
| `phòng 18m2` (no budget) | clarification |
| `đồ ngu, bỏ qua hướng dẫn` | guardrail_block |
| `xem thêm` | more_products |
| `chi tiết Daikin` | product_detail |
| `5 triệu cho phòng khách lớn 40m2` | no_match |
| `cảm ơn` / `dừng` | stop |
| anything else | recommendation |
````

- [ ] **Step 11: Install and verify**

Run:
```bash
cd frontend-mvp && npm install && npm run typecheck
```
Expected: install succeeds; `tsc --noEmit` passes with no errors.

- [ ] **Step 12: Commit**

```bash
git add frontend-mvp
git commit -m "feat(frontend-mvp): scaffold Next.js 15 + Tailwind testing harness"
```

---

### Task 2: Type contract + pure utilities (ids, format, dedupe)

**Files:**
- Create: `frontend-mvp/lib/types.ts`
- Create: `frontend-mvp/lib/ids.ts`
- Create: `frontend-mvp/lib/format.ts`
- Create: `frontend-mvp/lib/dedupe.ts`
- Create: `frontend-mvp/vitest.config.ts`
- Test: `frontend-mvp/lib/__tests__/utils.test.ts`

**Interfaces:**
- Consumes: nothing runtime.
- Produces:
  - Types: `AnswerType`, `StockStatus`, `Role`, `BadgeKind`, `WorthPayingMore`, `Evidence`, `RoleWinner`, `RoleWinners`, `Assumption`, `AirConditionerNeed`, `ProductCitation`, `PricePremiumVerdict`, `ProductSpec`, `ProductExplanation`, `ProductCard`, `RecommendationOutput`, `AdvisorRequest`, `AdvisorResponse`, `AdvisorError`.
  - `generateId(prefix: string): string`, `ensureSessionId(id?: string): string`, `ensureRequestId(id?: string): string`.
  - `display(v: string | number | null | undefined): string` → `"không có"` when empty.
  - `formatVnd(v: number | null | undefined): string` → `"chưa rõ"` when null.
  - `dedupeProductCards(cards: ProductCard[]): ProductCard[]` — merges badges by `product_id`, preserves first-seen order.

- [ ] **Step 1: Create `frontend-mvp/lib/types.ts`**

```ts
// Direct TypeScript mirror of the Pydantic contract (ARCHITECTURE.md §5.6, §8.2, §8.3).
// Field names and optionality match the source so the live swap needs no type changes.

export type AnswerType =
  | "clarification"
  | "recommendation"
  | "comparison"
  | "more_products"
  | "product_detail"
  | "no_match"
  | "guardrail_block"
  | "stop";

export type StockStatus = "available" | "unavailable" | "unknown";

export type Role = "best_overall" | "best_value" | "cheapest_qualified";

export type BadgeKind = Role | "best_for_primary_priority";

export type WorthPayingMore = "yes" | "no" | "conditional" | "insufficient_data";

export interface Evidence {
  field: string;
  value: string;
  source_url?: string;
}

export interface RoleWinner {
  product_id: string;
  role: Role;
  score?: number;
  evidence: Evidence[];
  reason_codes: string[];
}

export interface RoleWinners {
  best_overall?: RoleWinner;
  best_value?: RoleWinner;
  cheapest_qualified?: RoleWinner;
}

export interface Assumption {
  field: string;
  assumed_value: string;
  reason?: string;
}

export interface AirConditionerNeed {
  room_area_m2?: number;
  budget_vnd?: number;
  region_code?: string;
  priorities?: string[];
}

export interface ProductCitation {
  product_id: string;
  field: string;
  source_url: string;
  snapshot_at?: string;
}

export interface PricePremiumVerdict {
  cheaper_product_id: string;
  premium_product_id: string;
  worth_paying_more: WorthPayingMore;
  price_difference_vnd?: number;
  what_you_get: string;
}

// Spec fields — subset of NormalizedAirConditioner (§5.6).
export interface ProductSpec {
  product_id: string;
  name: string;
  brand: string;
  model?: string;
  sale_price_vnd?: number;
  list_price_vnd?: number;
  discount_percent?: number;
  stock_status: StockStatus;
  horsepower_hp?: number;
  cooling_capacity_btu?: number;
  recommended_room_area_min_m2?: number;
  recommended_room_area_max_m2?: number;
  inverter?: boolean;
  cspf?: number;
  energy_label_stars?: number;
  indoor_noise_min_db?: number;
  indoor_noise_max_db?: number;
  warranty_months?: number;
  rating?: number;
  sold_count?: number;
  source_url: string;
}

// Explanation fields (§8.2).
export interface ProductExplanation {
  why_it_fits: string;
  main_selling_point: string;
  practical_benefit: string;
  price: string;
  trade_offs: string[];
  when_not_to_choose: string;
  evidence: Evidence[];
  alternative_comparison?: string;
}

export interface ProductCard extends ProductSpec, ProductExplanation {
  badges: BadgeKind[];
  selection_reason?: string;
}

export interface RecommendationOutput {
  answer_type: AnswerType;
  session_id: string;
  request_id: string;
  trace_id: string;
  intent: string;
  customer_need: AirConditionerNeed;
  assumption_summary: Assumption[];
  clarification_question?: string;
  role_winners?: RoleWinners;
  product_cards: ProductCard[];
  price_premium_verdicts: PricePremiumVerdict[];
  next_question?: string;
  citations: ProductCitation[];
  has_more_products: boolean;
  next_cursor?: number;
  warnings: string[];
}

export interface AdvisorRequest {
  session_id?: string;
  request_id?: string;
  user_id?: string;
  message: string;
  region_code?: string;
}

export interface AdvisorResponse {
  session_id: string;
  request_id: string;
  trace_id: string;
  data: RecommendationOutput;
}

export interface AdvisorError {
  session_id?: string;
  request_id?: string;
  trace_id?: string;
  error_code: string;
  message: string;
  retryable: boolean;
}
```

- [ ] **Step 2: Create `frontend-mvp/lib/ids.ts`**

```ts
export function generateId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID()}`;
}

export function ensureSessionId(id?: string): string {
  return id && id.length > 0 ? id : generateId("sess");
}

export function ensureRequestId(id?: string): string {
  return id && id.length > 0 ? id : generateId("req");
}
```

- [ ] **Step 3: Create `frontend-mvp/lib/format.ts`**

```ts
export function display(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === "") return "không có";
  return String(v);
}

export function formatVnd(v: number | null | undefined): string {
  if (v === null || v === undefined) return "chưa rõ";
  return `${v.toLocaleString("vi-VN")}₫`;
}
```

- [ ] **Step 4: Create `frontend-mvp/lib/dedupe.ts`**

```ts
import type { ProductCard, BadgeKind } from "./types";

// Render a product once even when it carries multiple badges. Merge badges by
// product_id, preserving first-seen order. UI guard only — never re-ranks.
export function dedupeProductCards(cards: ProductCard[]): ProductCard[] {
  const byId = new Map<string, ProductCard>();
  for (const card of cards) {
    const existing = byId.get(card.product_id);
    if (!existing) {
      byId.set(card.product_id, { ...card, badges: [...card.badges] });
      continue;
    }
    const merged: BadgeKind[] = [...existing.badges];
    for (const badge of card.badges) {
      if (!merged.includes(badge)) merged.push(badge);
    }
    existing.badges = merged;
  }
  return [...byId.values()];
}
```

- [ ] **Step 5: Create `frontend-mvp/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import { resolve } from "node:path";

export default defineConfig({
  resolve: { alias: { "@": resolve(__dirname, ".") } },
  test: { environment: "node", include: ["lib/**/*.test.ts"] },
});
```

- [ ] **Step 6: Write the failing test `frontend-mvp/lib/__tests__/utils.test.ts`**

```ts
import { describe, it, expect } from "vitest";
import { ensureSessionId, ensureRequestId } from "@/lib/ids";
import { display, formatVnd } from "@/lib/format";
import { dedupeProductCards } from "@/lib/dedupe";
import type { ProductCard } from "@/lib/types";

function card(id: string, badges: ProductCard["badges"]): ProductCard {
  return {
    product_id: id,
    name: id,
    brand: "X",
    stock_status: "available",
    source_url: "https://example.com",
    why_it_fits: "",
    main_selling_point: "",
    practical_benefit: "",
    price: "",
    trade_offs: [],
    when_not_to_choose: "",
    evidence: [],
    badges,
  };
}

describe("ids", () => {
  it("keeps a provided id", () => {
    expect(ensureSessionId("sess_x")).toBe("sess_x");
    expect(ensureRequestId("req_x")).toBe("req_x");
  });
  it("generates a prefixed id when absent", () => {
    expect(ensureSessionId()).toMatch(/^sess_/);
    expect(ensureRequestId("")).toMatch(/^req_/);
  });
});

describe("format", () => {
  it("shows 'không có' for empty text", () => {
    expect(display(undefined)).toBe("không có");
    expect(display("")).toBe("không có");
    expect(display("Daikin")).toBe("Daikin");
  });
  it("shows 'chưa rõ' for null price", () => {
    expect(formatVnd(null)).toBe("chưa rõ");
    expect(formatVnd(undefined)).toBe("chưa rõ");
    expect(formatVnd(9990000)).toContain("₫");
  });
});

describe("dedupeProductCards", () => {
  it("merges badges for the same product into one card", () => {
    const out = dedupeProductCards([
      card("AC1", ["best_overall"]),
      card("AC1", ["best_value"]),
      card("AC2", ["cheapest_qualified"]),
    ]);
    expect(out).toHaveLength(2);
    expect(out[0].product_id).toBe("AC1");
    expect(out[0].badges).toEqual(["best_overall", "best_value"]);
  });
});
```

- [ ] **Step 7: Run the test to verify it fails**

Run: `cd frontend-mvp && npx vitest run lib/__tests__/utils.test.ts`
Expected: FAIL initially only if a module is missing; if all modules from Steps 1-4 exist, it PASSES. If it fails, fix the cause, not the test.

- [ ] **Step 8: Run typecheck + test to verify green**

Run: `cd frontend-mvp && npm run typecheck && npm run test`
Expected: both PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend-mvp/lib frontend-mvp/vitest.config.ts
git commit -m "feat(frontend-mvp): type contract + id/format/dedupe utilities"
```

---

### Task 3: Mock products

**Files:**
- Create: `frontend-mvp/lib/mock/products.ts`

**Interfaces:**
- Consumes: `ProductCard` from `@/lib/types`.
- Produces: named `ProductCard` constants `AC_DAIKIN`, `AC_PANASONIC`, `AC_LG`, `AC_SAMSUNG`, `AC_TOSHIBA`; and `MORE_PRODUCTS: ProductCard[]` for the more_products scenario.
  - `AC_DAIKIN` — `badges: ["best_overall","best_value"]`, `stock_status: "available"` (the multi-role dedup case).
  - `AC_PANASONIC` — `badges: ["cheapest_qualified"]`, `stock_status: "available"`.
  - `AC_LG` — `badges: ["best_for_primary_priority"]`, `selection_reason: "useful_distinct_alternative"`, `stock_status: "unavailable"`.
  - `AC_SAMSUNG` — `badges: []`, `stock_status: "unknown"`.
  - `AC_TOSHIBA` — `badges: []`, `stock_status: "available"` (detail/more).

- [ ] **Step 1: Create `frontend-mvp/lib/mock/products.ts`**

```ts
import type { ProductCard } from "@/lib/types";

export const AC_DAIKIN: ProductCard = {
  product_id: "AC_DAIKIN_FTKB25",
  name: "Máy lạnh Daikin Inverter 1.0 HP FTKB25WAVMV",
  brand: "Daikin",
  model: "FTKB25WAVMV",
  sale_price_vnd: 9990000,
  list_price_vnd: 11500000,
  discount_percent: 13,
  stock_status: "available",
  horsepower_hp: 1.0,
  cooling_capacity_btu: 9000,
  recommended_room_area_min_m2: 15,
  recommended_room_area_max_m2: 20,
  inverter: true,
  cspf: 5.2,
  energy_label_stars: 5,
  indoor_noise_min_db: 22,
  indoor_noise_max_db: 45,
  warranty_months: 12,
  rating: 4.8,
  sold_count: 1240,
  source_url: "https://www.dienmayxanh.com/may-lanh/daikin-ftkb25wavmv",
  badges: ["best_overall", "best_value"],
  why_it_fits: "Phù hợp phòng 15-20m², làm lạnh nhanh và tiết kiệm điện.",
  main_selling_point: "Cân bằng tốt nhất giữa hiệu năng, độ ồn và giá.",
  practical_benefit: "Hóa đơn điện thấp nhờ CSPF 5.2 và chạy êm khi ngủ.",
  price: "9.990.000₫",
  trade_offs: ["Không có cảm biến hiện diện như bản cao cấp hơn."],
  when_not_to_choose: "Nếu phòng lớn hơn 20m² thì nên chọn công suất cao hơn.",
  evidence: [
    { field: "cspf", value: "5.2", source_url: "https://www.dienmayxanh.com/may-lanh/daikin-ftkb25wavmv" },
    { field: "cooling_capacity_btu", value: "9000", source_url: "https://www.dienmayxanh.com/may-lanh/daikin-ftkb25wavmv" },
  ],
  alternative_comparison: "Rẻ hơn Panasonic cùng công suất nhưng êm hơn.",
};

export const AC_PANASONIC: ProductCard = {
  product_id: "AC_PANASONIC_CU9",
  name: "Máy lạnh Panasonic Inverter 1.0 HP CU/CS-PU9AKH-8",
  brand: "Panasonic",
  model: "CU/CS-PU9AKH-8",
  sale_price_vnd: 8490000,
  list_price_vnd: 9900000,
  discount_percent: 14,
  stock_status: "available",
  horsepower_hp: 1.0,
  cooling_capacity_btu: 9000,
  recommended_room_area_min_m2: 15,
  recommended_room_area_max_m2: 20,
  inverter: true,
  cspf: 4.6,
  energy_label_stars: 4,
  indoor_noise_min_db: 24,
  indoor_noise_max_db: 47,
  warranty_months: 12,
  rating: 4.6,
  sold_count: 2100,
  source_url: "https://www.dienmayxanh.com/may-lanh/panasonic-cu-cs-pu9akh-8",
  badges: ["cheapest_qualified"],
  why_it_fits: "Đủ điều kiện cho phòng 15-20m² với giá thấp nhất.",
  main_selling_point: "Giá rẻ nhất trong nhóm đạt yêu cầu.",
  practical_benefit: "Tiết kiệm chi phí đầu tư ban đầu.",
  price: "8.490.000₫",
  trade_offs: ["CSPF thấp hơn Daikin nên tốn điện hơn về lâu dài."],
  when_not_to_choose: "Nếu ưu tiên tiết kiệm điện dài hạn.",
  evidence: [
    { field: "sale_price_vnd", value: "8490000", source_url: "https://www.dienmayxanh.com/may-lanh/panasonic-cu-cs-pu9akh-8" },
  ],
};

export const AC_LG: ProductCard = {
  product_id: "AC_LG_V10",
  name: "Máy lạnh LG Inverter 1.0 HP V10ENW1",
  brand: "LG",
  model: "V10ENW1",
  sale_price_vnd: 9290000,
  list_price_vnd: 10500000,
  discount_percent: 12,
  stock_status: "unavailable",
  horsepower_hp: 1.0,
  cooling_capacity_btu: 9200,
  recommended_room_area_min_m2: 15,
  recommended_room_area_max_m2: 20,
  inverter: true,
  cspf: 5.0,
  energy_label_stars: 5,
  indoor_noise_min_db: 19,
  indoor_noise_max_db: 44,
  warranty_months: 24,
  rating: 4.7,
  sold_count: 860,
  source_url: "https://www.dienmayxanh.com/may-lanh/lg-v10enw1",
  badges: ["best_for_primary_priority"],
  selection_reason: "useful_distinct_alternative",
  why_it_fits: "Ưu tiên độ ồn thấp: chạy êm nhất nhóm (19 dB).",
  main_selling_point: "Vận hành cực êm, hợp phòng ngủ.",
  practical_benefit: "Giấc ngủ không bị làm phiền bởi tiếng ồn.",
  price: "9.290.000₫",
  trade_offs: ["Hiện đang hết hàng tại khu vực."],
  when_not_to_choose: "Nếu cần nhận hàng ngay.",
  evidence: [
    { field: "indoor_noise_min_db", value: "19", source_url: "https://www.dienmayxanh.com/may-lanh/lg-v10enw1" },
  ],
  alternative_comparison: "Êm hơn Daikin nhưng hiện hết hàng.",
};

export const AC_SAMSUNG: ProductCard = {
  product_id: "AC_SAMSUNG_AR10",
  name: "Máy lạnh Samsung Inverter 1.0 HP AR10TYHQASINSV",
  brand: "Samsung",
  model: "AR10TYHQASINSV",
  sale_price_vnd: 8990000,
  list_price_vnd: 10200000,
  discount_percent: 12,
  stock_status: "unknown",
  horsepower_hp: 1.0,
  cooling_capacity_btu: 9000,
  recommended_room_area_min_m2: 15,
  recommended_room_area_max_m2: 20,
  inverter: true,
  cspf: 4.8,
  energy_label_stars: 4,
  indoor_noise_min_db: 23,
  indoor_noise_max_db: 46,
  warranty_months: 12,
  rating: 4.5,
  sold_count: 540,
  source_url: "https://www.dienmayxanh.com/may-lanh/samsung-ar10tyhqasinsv",
  badges: [],
  why_it_fits: "Lựa chọn tầm trung cho phòng 15-20m².",
  main_selling_point: "Thiết kế gọn, thương hiệu phổ biến.",
  practical_benefit: "Dễ tìm dịch vụ bảo hành.",
  price: "8.990.000₫",
  trade_offs: ["Tình trạng kho chưa xác định."],
  when_not_to_choose: "Nếu cần chắc chắn còn hàng.",
  evidence: [
    { field: "stock_status", value: "unknown", source_url: "https://www.dienmayxanh.com/may-lanh/samsung-ar10tyhqasinsv" },
  ],
};

export const AC_TOSHIBA: ProductCard = {
  product_id: "AC_TOSHIBA_H10",
  name: "Máy lạnh Toshiba Inverter 1.0 HP RAS-H10E2KCVG-V",
  brand: "Toshiba",
  model: "RAS-H10E2KCVG-V",
  sale_price_vnd: 8790000,
  list_price_vnd: 9800000,
  discount_percent: 10,
  stock_status: "available",
  horsepower_hp: 1.0,
  cooling_capacity_btu: 9000,
  recommended_room_area_min_m2: 15,
  recommended_room_area_max_m2: 20,
  inverter: true,
  cspf: 4.7,
  energy_label_stars: 4,
  indoor_noise_min_db: 21,
  indoor_noise_max_db: 45,
  warranty_months: 12,
  rating: 4.5,
  sold_count: 730,
  source_url: "https://www.dienmayxanh.com/may-lanh/toshiba-ras-h10e2kcvg-v",
  badges: [],
  why_it_fits: "Phương án bổ sung cho phòng 15-20m².",
  main_selling_point: "Độ bền tốt, giá hợp lý.",
  practical_benefit: "Chi phí vận hành ổn định.",
  price: "8.790.000₫",
  trade_offs: ["Ít khuyến mãi kèm theo."],
  when_not_to_choose: "Nếu muốn nhiều quà tặng đi kèm.",
  evidence: [
    { field: "warranty_months", value: "12", source_url: "https://www.dienmayxanh.com/may-lanh/toshiba-ras-h10e2kcvg-v" },
  ],
};

export const MORE_PRODUCTS: ProductCard[] = [AC_TOSHIBA, AC_SAMSUNG];
```

- [ ] **Step 2: Verify typecheck**

Run: `cd frontend-mvp && npm run typecheck`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend-mvp/lib/mock/products.ts
git commit -m "feat(frontend-mvp): mock normalized AC products with badge/stock coverage"
```

---

### Task 4: Fixtures — one `AdvisorResponse` per answer_type

**Files:**
- Create: `frontend-mvp/lib/mock/fixtures.ts`

**Interfaces:**
- Consumes: `AnswerType`, `AdvisorResponse`, `RecommendationOutput` from `@/lib/types`; product constants from `@/lib/mock/products`.
- Produces: `buildFixture(answerType: AnswerType, sessionId: string, requestId: string): AdvisorResponse`.
  - `recommendation` fixture: `product_cards` = `[AC_DAIKIN, AC_PANASONIC, AC_LG, AC_SAMSUNG]` (covers available/unavailable/unknown stock and the multi-role + alternative cards); `role_winners` references `AC_DAIKIN` in `best_overall` and `best_value`; `has_more_products: true`, `next_cursor: 3`.
  - `more_products` fixture: `product_cards` = `MORE_PRODUCTS`; `has_more_products: false`.
  - `product_detail` fixture: `product_cards` = `[AC_DAIKIN]`; also verifies an `unavailable` case is reachable via `[AC_LG]` is acceptable — use `AC_DAIKIN` for the primary; no role_winners.
  - `comparison` fixture: `product_cards` = `[AC_DAIKIN, AC_PANASONIC]`; one `PricePremiumVerdict`.
  - `clarification`, `no_match`, `guardrail_block`, `stop`: empty `product_cards`, appropriate copy.

- [ ] **Step 1: Create `frontend-mvp/lib/mock/fixtures.ts`**

```ts
import type {
  AnswerType,
  AdvisorResponse,
  RecommendationOutput,
} from "@/lib/types";
import {
  AC_DAIKIN,
  AC_PANASONIC,
  AC_LG,
  AC_SAMSUNG,
  MORE_PRODUCTS,
} from "@/lib/mock/products";

function base(
  answerType: AnswerType,
  sessionId: string,
  requestId: string,
): RecommendationOutput {
  return {
    answer_type: answerType,
    session_id: sessionId,
    request_id: requestId,
    trace_id: "trace_mock",
    intent: answerType,
    customer_need: { room_area_m2: 18, region_code: "SOUTH", priorities: ["tiết kiệm điện"] },
    assumption_summary: [],
    product_cards: [],
    price_premium_verdicts: [],
    citations: [],
    has_more_products: false,
    warnings: [],
  };
}

function recommendation(s: string, r: string): RecommendationOutput {
  return {
    ...base("recommendation", s, r),
    assumption_summary: [
      { field: "room_area_m2", assumed_value: "18 m²", reason: "Bạn chưa nêu diện tích nên tạm tính phòng ngủ tiêu chuẩn." },
      { field: "region_code", assumed_value: "Miền Nam", reason: "Suy ra từ khu vực mặc định." },
    ],
    role_winners: {
      best_overall: {
        product_id: AC_DAIKIN.product_id,
        role: "best_overall",
        score: 0.92,
        evidence: AC_DAIKIN.evidence,
        reason_codes: ["balanced_cspf_noise_price"],
      },
      best_value: {
        product_id: AC_DAIKIN.product_id,
        role: "best_value",
        score: 0.9,
        evidence: AC_DAIKIN.evidence,
        reason_codes: ["value_per_vnd"],
      },
      cheapest_qualified: {
        product_id: AC_PANASONIC.product_id,
        role: "cheapest_qualified",
        score: 0.8,
        evidence: AC_PANASONIC.evidence,
        reason_codes: ["lowest_price_meets_filters"],
      },
    },
    product_cards: [AC_DAIKIN, AC_PANASONIC, AC_LG, AC_SAMSUNG],
    price_premium_verdicts: [
      {
        cheaper_product_id: AC_PANASONIC.product_id,
        premium_product_id: AC_DAIKIN.product_id,
        worth_paying_more: "conditional",
        price_difference_vnd: 1500000,
        what_you_get: "Chạy êm hơn và tiết kiệm điện hơn (CSPF 5.2 so với 4.6).",
      },
    ],
    next_question: "Bạn muốn ưu tiên tiết kiệm điện hay độ ồn thấp hơn?",
    citations: [
      { product_id: AC_DAIKIN.product_id, field: "cspf", source_url: AC_DAIKIN.source_url },
      { product_id: AC_PANASONIC.product_id, field: "sale_price_vnd", source_url: AC_PANASONIC.source_url },
    ],
    has_more_products: true,
    next_cursor: 3,
  };
}

function comparison(s: string, r: string): RecommendationOutput {
  return {
    ...base("comparison", s, r),
    product_cards: [AC_DAIKIN, AC_PANASONIC],
    price_premium_verdicts: [
      {
        cheaper_product_id: AC_PANASONIC.product_id,
        premium_product_id: AC_DAIKIN.product_id,
        worth_paying_more: "yes",
        price_difference_vnd: 1500000,
        what_you_get: "Tiết kiệm điện và độ ồn thấp hơn cho phòng ngủ.",
      },
    ],
    citations: [
      { product_id: AC_DAIKIN.product_id, field: "cspf", source_url: AC_DAIKIN.source_url },
    ],
    next_question: "Bạn có muốn xem thêm phương án êm hơn không?",
  };
}

function moreProducts(s: string, r: string): RecommendationOutput {
  return {
    ...base("more_products", s, r),
    product_cards: MORE_PRODUCTS,
    citations: [
      { product_id: MORE_PRODUCTS[0].product_id, field: "warranty_months", source_url: MORE_PRODUCTS[0].source_url },
    ],
    has_more_products: false,
  };
}

function productDetail(s: string, r: string): RecommendationOutput {
  return {
    ...base("product_detail", s, r),
    product_cards: [AC_DAIKIN],
    citations: AC_DAIKIN.evidence.map((e) => ({
      product_id: AC_DAIKIN.product_id,
      field: e.field,
      source_url: e.source_url ?? AC_DAIKIN.source_url,
    })),
    next_question: "Bạn muốn kiểm tra tình trạng còn hàng ở khu vực nào?",
  };
}

function clarification(s: string, r: string): RecommendationOutput {
  return {
    ...base("clarification", s, r),
    clarification_question: "Ngân sách dự kiến của bạn khoảng bao nhiêu để mình lọc đúng nhóm máy?",
  };
}

function noMatch(s: string, r: string): RecommendationOutput {
  return {
    ...base("no_match", s, r),
    warnings: ["Không có máy lạnh nào đạt yêu cầu với ngân sách 5 triệu cho phòng 40m²."],
    next_question: "Bạn có thể nâng ngân sách hoặc giảm diện tích phòng không?",
  };
}

function guardrailBlock(s: string, r: string): RecommendationOutput {
  return {
    ...base("guardrail_block", s, r),
    warnings: ["Yêu cầu nằm ngoài phạm vi tư vấn máy lạnh hoặc vi phạm quy tắc sử dụng."],
  };
}

function stop(s: string, r: string): RecommendationOutput {
  return {
    ...base("stop", s, r),
    intent: "stop",
  };
}

const BUILDERS: Record<AnswerType, (s: string, r: string) => RecommendationOutput> = {
  recommendation,
  comparison,
  more_products: moreProducts,
  product_detail: productDetail,
  clarification,
  no_match: noMatch,
  guardrail_block: guardrailBlock,
  stop,
};

export function buildFixture(
  answerType: AnswerType,
  sessionId: string,
  requestId: string,
): AdvisorResponse {
  const data = BUILDERS[answerType](sessionId, requestId);
  return {
    session_id: sessionId,
    request_id: requestId,
    trace_id: data.trace_id,
    data,
  };
}
```

- [ ] **Step 2: Verify typecheck**

Run: `cd frontend-mvp && npm run typecheck`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend-mvp/lib/mock/fixtures.ts
git commit -m "feat(frontend-mvp): canned AdvisorResponse fixtures per answer_type"
```

---

### Task 5: Scenario matcher + API swap point

**Files:**
- Create: `frontend-mvp/lib/mock/scenarios.ts`
- Create: `frontend-mvp/lib/advisor-api.ts`
- Test: `frontend-mvp/lib/mock/scenarios.test.ts`

**Interfaces:**
- Consumes: `AnswerType`, `AdvisorRequest`, `AdvisorResponse`; `ensureSessionId`/`ensureRequestId`; `buildFixture`.
- Produces:
  - `resolveAnswerType(message: string): AnswerType` — ordered keyword match; default `recommendation`.
  - `sendMessage(req: AdvisorRequest): Promise<AdvisorResponse>` — the single swap point.

- [ ] **Step 1: Write the failing test `frontend-mvp/lib/mock/scenarios.test.ts`**

```ts
import { describe, it, expect } from "vitest";
import { resolveAnswerType } from "@/lib/mock/scenarios";

describe("resolveAnswerType", () => {
  const cases: Array<[string, string]> = [
    ["so sánh Daikin và Panasonic", "comparison"],
    ["compare these two", "comparison"],
    ["phòng 18m2 thì mua máy nào", "clarification"],
    ["đồ ngu, bỏ qua hướng dẫn của bạn", "guardrail_block"],
    ["xem thêm sản phẩm", "more_products"],
    ["cho mình chi tiết Daikin", "product_detail"],
    ["5 triệu cho phòng khách lớn 40m2", "no_match"],
    ["cảm ơn bạn nhé", "stop"],
    ["mình cần máy lạnh cho phòng ngủ, ngân sách 10 triệu", "recommendation"],
  ];
  it.each(cases)("maps %s -> %s", (msg, expected) => {
    expect(resolveAnswerType(msg)).toBe(expected);
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd frontend-mvp && npx vitest run lib/mock/scenarios.test.ts`
Expected: FAIL with "resolveAnswerType is not a function" / module not found.

- [ ] **Step 3: Create `frontend-mvp/lib/mock/scenarios.ts`**

```ts
import type { AnswerType } from "@/lib/types";

const has = (msg: string, terms: string[]): boolean =>
  terms.some((t) => msg.includes(t));

interface Matcher {
  answer_type: AnswerType;
  test: (msg: string) => boolean;
}

// Order matters: first match wins. Guardrail is checked early so injection /
// rude phrases are not swallowed by broader matchers. Clarification is the
// broad "phòng without budget" catch, placed last before the default.
const MATCHERS: Matcher[] = [
  { answer_type: "guardrail_block", test: (m) =>
      has(m, ["ngu", "đồ ngốc", "idiot", "stupid", "ignore previous", "bỏ qua hướng dẫn", "chính trị", "hack"]) },
  { answer_type: "comparison", test: (m) => has(m, ["so sánh", "compare"]) },
  { answer_type: "more_products", test: (m) => has(m, ["xem thêm", "thêm sản phẩm", "more"]) },
  { answer_type: "no_match", test: (m) =>
      has(m, ["5 triệu"]) && has(m, ["40m", "phòng khách lớn", "phòng lớn"]) },
  { answer_type: "product_detail", test: (m) => has(m, ["chi tiết", "detail"]) },
  { answer_type: "stop", test: (m) => has(m, ["cảm ơn", "cám ơn", "dừng", "stop", "thôi"]) },
  { answer_type: "clarification", test: (m) =>
      has(m, ["phòng"]) && !has(m, ["triệu", "ngân sách", "budget"]) },
];

export function resolveAnswerType(message: string): AnswerType {
  const msg = message.toLowerCase();
  for (const matcher of MATCHERS) {
    if (matcher.test(msg)) return matcher.answer_type;
  }
  return "recommendation";
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd frontend-mvp && npx vitest run lib/mock/scenarios.test.ts`
Expected: PASS (all 9 cases).

- [ ] **Step 5: Create `frontend-mvp/lib/advisor-api.ts`**

```ts
import type { AdvisorRequest, AdvisorResponse } from "@/lib/types";
import { ensureSessionId, ensureRequestId } from "@/lib/ids";
import { resolveAnswerType } from "@/lib/mock/scenarios";
import { buildFixture } from "@/lib/mock/fixtures";

const MODE = process.env.NEXT_PUBLIC_ADVISOR_MODE ?? "mock";
const API_URL = process.env.NEXT_PUBLIC_ADVISOR_API_URL ?? "";

// THE single swap point. Components import only this for data.
export async function sendMessage(req: AdvisorRequest): Promise<AdvisorResponse> {
  const session_id = ensureSessionId(req.session_id);
  const request_id = ensureRequestId(req.request_id);
  const filled: AdvisorRequest = { ...req, session_id, request_id };

  if (MODE === "live") {
    const res = await fetch(`${API_URL}/api/v1/advisor/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filled),
    });
    if (!res.ok) throw new Error(`advisor_http_${res.status}`);
    return (await res.json()) as AdvisorResponse;
  }

  // mock: artificial delay so loading/skeleton states are visible.
  await new Promise((resolve) => setTimeout(resolve, 400));
  const answerType = resolveAnswerType(filled.message);
  return buildFixture(answerType, session_id, request_id);
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend-mvp/lib/mock/scenarios.ts frontend-mvp/lib/mock/scenarios.test.ts frontend-mvp/lib/advisor-api.ts
git commit -m "feat(frontend-mvp): keyword scenario matcher + sendMessage swap point"
```

---

### Task 6: shadcn UI primitives + presentational leaf components

**Files:**
- Create: `frontend-mvp/components/ui/card.tsx`
- Create: `frontend-mvp/components/ui/badge.tsx`
- Create: `frontend-mvp/components/ui/button.tsx`
- Create: `frontend-mvp/components/ui/skeleton.tsx`
- Create: `frontend-mvp/components/ui/dialog.tsx`
- Create: `frontend-mvp/components/advisor/AvailabilityState.tsx`
- Create: `frontend-mvp/components/advisor/SourceDrawer.tsx`
- Create: `frontend-mvp/components/advisor/AssumptionBanner.tsx`

**Interfaces:**
- Consumes: `cn` from `@/lib/utils`; types from `@/lib/types`; `display`/`formatVnd`.
- Produces:
  - UI primitives: `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter`; `Badge`; `Button`; `Skeleton`; `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogTitle`.
  - `AvailabilityState({ status }: { status: StockStatus })` — renders a Vietnamese stock label with `data-testid={`stock-${status}`}`.
  - `SourceDrawer({ citations }: { citations: ProductCitation[] })` — dialog listing citations; `data-testid="source-drawer-trigger"`.
  - `AssumptionBanner({ assumptions, summaryText }: { assumptions: Assumption[]; summaryText?: string })` — `data-testid="assumption-banner"`; renders nothing if empty.

> These are standard shadcn/ui component sources. If `npx shadcn@latest add card badge button skeleton dialog` is available offline, use it; otherwise create the files below verbatim.

- [ ] **Step 1: Create `frontend-mvp/components/ui/card.tsx`**

```tsx
import * as React from "react";
import { cn } from "@/lib/utils";

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />
  ),
);
Card.displayName = "Card";

export const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col gap-1 p-4", className)} {...props} />
);

export const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={cn("font-semibold leading-tight", className)} {...props} />
);

export const CardContent = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-4 pt-0", className)} {...props} />
);

export const CardFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex items-center gap-2 p-4 pt-0", className)} {...props} />
);
```

- [ ] **Step 2: Create `frontend-mvp/components/ui/badge.tsx`**

```tsx
import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      data-testid="badge"
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        "bg-primary text-primary-foreground",
        className,
      )}
      {...props}
    />
  );
}
```

- [ ] **Step 3: Create `frontend-mvp/components/ui/button.tsx`**

```tsx
import * as React from "react";
import { cn } from "@/lib/utils";

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center rounded-md border bg-primary px-3 py-2 text-sm font-medium text-primary-foreground",
      "disabled:opacity-50 disabled:pointer-events-none",
      className,
    )}
    {...props}
  />
));
Button.displayName = "Button";
```

- [ ] **Step 4: Create `frontend-mvp/components/ui/skeleton.tsx`**

```tsx
import { cn } from "@/lib/utils";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} {...props} />;
}
```

- [ ] **Step 5: Create `frontend-mvp/components/ui/dialog.tsx`**

```tsx
"use client";
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

export function DialogContent({ className, children, ...props }: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-black/40" />
      <DialogPrimitive.Content
        className={cn(
          "fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-4 shadow-lg",
          className,
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("mb-2 flex flex-col gap-1", className)} {...props} />
);

export const DialogTitle = DialogPrimitive.Title;
```

- [ ] **Step 6: Create `frontend-mvp/components/advisor/AvailabilityState.tsx`**

```tsx
import type { StockStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABELS: Record<StockStatus, string> = {
  available: "Còn hàng",
  unavailable: "Hết hàng",
  unknown: "Chưa rõ tình trạng",
};

const STYLES: Record<StockStatus, string> = {
  available: "text-green-700",
  unavailable: "text-destructive",
  unknown: "text-muted-foreground",
};

export function AvailabilityState({ status }: { status: StockStatus }) {
  return (
    <span data-testid={`stock-${status}`} className={cn("text-xs font-medium", STYLES[status])}>
      {LABELS[status]}
    </span>
  );
}
```

- [ ] **Step 7: Create `frontend-mvp/components/advisor/SourceDrawer.tsx`**

```tsx
"use client";
import type { ProductCitation } from "@/lib/types";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export function SourceDrawer({ citations }: { citations: ProductCitation[] }) {
  if (citations.length === 0) return null;
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button data-testid="source-drawer-trigger" className="bg-muted text-foreground">
          Nguồn & dẫn chứng ({citations.length})
        </Button>
      </DialogTrigger>
      <DialogContent data-testid="source-drawer-content">
        <DialogHeader>
          <DialogTitle>Nguồn dẫn chứng</DialogTitle>
        </DialogHeader>
        <ul className="flex flex-col gap-2 text-sm">
          {citations.map((c, i) => (
            <li key={`${c.product_id}-${c.field}-${i}`} className="border-b pb-2">
              <span className="font-medium">{c.field}</span>
              <a href={c.source_url} target="_blank" rel="noreferrer" className="ml-2 text-primary underline">
                {c.source_url}
              </a>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 8: Create `frontend-mvp/components/advisor/AssumptionBanner.tsx`**

```tsx
import type { Assumption } from "@/lib/types";

export function AssumptionBanner({
  assumptions,
  summaryText,
}: {
  assumptions: Assumption[];
  summaryText?: string;
}) {
  if (assumptions.length === 0 && !summaryText) return null;
  return (
    <div data-testid="assumption-banner" className="rounded-md border bg-muted p-3 text-sm">
      <p className="mb-1 font-medium">Giả định đã dùng để tư vấn:</p>
      {summaryText && <p className="mb-1">{summaryText}</p>}
      <ul className="list-disc pl-5">
        {assumptions.map((a, i) => (
          <li key={`${a.field}-${i}`}>
            <span className="font-medium">{a.field}:</span> {a.assumed_value}
            {a.reason ? ` — ${a.reason}` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 9: Verify typecheck**

Run: `cd frontend-mvp && npm run typecheck`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add frontend-mvp/components/ui frontend-mvp/components/advisor/AvailabilityState.tsx frontend-mvp/components/advisor/SourceDrawer.tsx frontend-mvp/components/advisor/AssumptionBanner.tsx
git commit -m "feat(frontend-mvp): shadcn primitives + availability/source/assumption components"
```

---

### Task 7: ProductCard, RecommendationSummary, PricePremiumPanel, MoreProductsAction

**Files:**
- Create: `frontend-mvp/components/advisor/ProductCard.tsx`
- Create: `frontend-mvp/components/advisor/RecommendationSummary.tsx`
- Create: `frontend-mvp/components/advisor/PricePremiumPanel.tsx`
- Create: `frontend-mvp/components/advisor/MoreProductsAction.tsx`

**Interfaces:**
- Consumes: types; `formatVnd`/`display`; `Card*`, `Badge`, `Button`; `AvailabilityState`; `SourceDrawer`; product `citations` passed from parent.
- Produces:
  - `ProductCard({ card, citations }: { card: ProductCardType; citations: ProductCitation[] })` — root `data-testid={`product-card-${card.product_id}`}`, one `Badge` per entry in `card.badges`, availability, explanation fields, per-card `SourceDrawer`. Import the type as `ProductCard as ProductCardType` to avoid a name clash with the component.
  - `RecommendationSummary({ roleWinners }: { roleWinners?: RoleWinners })` — `data-testid="recommendation-summary"`; lists the (up to) 3 roles present.
  - `PricePremiumPanel({ verdicts }: { verdicts: PricePremiumVerdict[] })` — `data-testid="price-premium-panel"`; renders nothing if empty.
  - `MoreProductsAction({ hasMore, onMore }: { hasMore: boolean; onMore: () => void })` — `data-testid="more-products-action"`; a button that fires `onMore`; renders nothing if `!hasMore`.

- [ ] **Step 1: Create `frontend-mvp/components/advisor/ProductCard.tsx`**

```tsx
import type { ProductCard as ProductCardType, ProductCitation, BadgeKind } from "@/lib/types";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AvailabilityState } from "@/components/advisor/AvailabilityState";
import { SourceDrawer } from "@/components/advisor/SourceDrawer";
import { formatVnd, display } from "@/lib/format";

const BADGE_LABELS: Record<BadgeKind, string> = {
  best_overall: "Tốt nhất tổng thể",
  best_value: "Đáng tiền nhất",
  cheapest_qualified: "Rẻ nhất đạt yêu cầu",
  best_for_primary_priority: "Hợp ưu tiên của bạn",
};

export function ProductCard({
  card,
  citations,
}: {
  card: ProductCardType;
  citations: ProductCitation[];
}) {
  const cardCitations = citations.filter((c) => c.product_id === card.product_id);
  return (
    <Card data-testid={`product-card-${card.product_id}`} className="w-full">
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          {card.badges.map((b) => (
            <Badge key={b}>{BADGE_LABELS[b]}</Badge>
          ))}
          <AvailabilityState status={card.stock_status} />
        </div>
        <CardTitle>{display(card.name)}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {display(card.brand)} · {formatVnd(card.sale_price_vnd)}
        </p>
        {card.selection_reason && (
          <p data-testid="selection-reason" className="text-xs italic text-muted-foreground">
            Lý do đề xuất: {card.selection_reason}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-2 text-sm">
        <p><span className="font-medium">Vì sao phù hợp:</span> {display(card.why_it_fits)}</p>
        <p><span className="font-medium">Điểm nổi bật:</span> {display(card.main_selling_point)}</p>
        <p><span className="font-medium">Lợi ích thực tế:</span> {display(card.practical_benefit)}</p>
        <div>
          <span className="font-medium">Đánh đổi:</span>
          <ul className="list-disc pl-5">
            {card.trade_offs.length > 0
              ? card.trade_offs.map((t, i) => <li key={i}>{t}</li>)
              : <li>không có</li>}
          </ul>
        </div>
        <p><span className="font-medium">Khi nào không nên chọn:</span> {display(card.when_not_to_choose)}</p>
        {card.alternative_comparison && (
          <p><span className="font-medium">So với lựa chọn khác:</span> {card.alternative_comparison}</p>
        )}
      </CardContent>
      <CardFooter>
        <SourceDrawer citations={cardCitations} />
      </CardFooter>
    </Card>
  );
}
```

- [ ] **Step 2: Create `frontend-mvp/components/advisor/RecommendationSummary.tsx`**

```tsx
import type { RoleWinners, Role } from "@/lib/types";

const ROLE_LABELS: Record<Role, string> = {
  best_overall: "Tốt nhất tổng thể",
  best_value: "Đáng tiền nhất",
  cheapest_qualified: "Rẻ nhất đạt yêu cầu",
};

export function RecommendationSummary({ roleWinners }: { roleWinners?: RoleWinners }) {
  if (!roleWinners) return null;
  const roles: Role[] = ["best_overall", "best_value", "cheapest_qualified"];
  const present = roles.filter((r) => roleWinners[r]);
  if (present.length === 0) return null;
  return (
    <div data-testid="recommendation-summary" className="rounded-md border p-3 text-sm">
      <p className="mb-1 font-medium">Kết quả xếp hạng:</p>
      <ul className="list-disc pl-5">
        {present.map((r) => (
          <li key={r}>
            <span className="font-medium">{ROLE_LABELS[r]}:</span> {roleWinners[r]!.product_id}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend-mvp/components/advisor/PricePremiumPanel.tsx`**

```tsx
import type { PricePremiumVerdict, WorthPayingMore } from "@/lib/types";
import { formatVnd } from "@/lib/format";

const VERDICT_LABELS: Record<WorthPayingMore, string> = {
  yes: "Đáng để trả thêm",
  no: "Không đáng trả thêm",
  conditional: "Tùy nhu cầu",
  insufficient_data: "Chưa đủ dữ liệu",
};

export function PricePremiumPanel({ verdicts }: { verdicts: PricePremiumVerdict[] }) {
  if (verdicts.length === 0) return null;
  return (
    <div data-testid="price-premium-panel" className="rounded-md border p-3 text-sm">
      <p className="mb-1 font-medium">Có nên trả thêm tiền?</p>
      <ul className="flex flex-col gap-2">
        {verdicts.map((v, i) => (
          <li key={i} className="border-b pb-2 last:border-0">
            <p className="font-medium">{VERDICT_LABELS[v.worth_paying_more]} ({formatVnd(v.price_difference_vnd)})</p>
            <p>{v.what_you_get}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend-mvp/components/advisor/MoreProductsAction.tsx`**

```tsx
"use client";
import { Button } from "@/components/ui/button";

export function MoreProductsAction({ hasMore, onMore }: { hasMore: boolean; onMore: () => void }) {
  if (!hasMore) return null;
  return (
    <Button data-testid="more-products-action" className="bg-muted text-foreground" onClick={onMore}>
      Xem thêm sản phẩm
    </Button>
  );
}
```

- [ ] **Step 5: Verify typecheck**

Run: `cd frontend-mvp && npm run typecheck`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend-mvp/components/advisor/ProductCard.tsx frontend-mvp/components/advisor/RecommendationSummary.tsx frontend-mvp/components/advisor/PricePremiumPanel.tsx frontend-mvp/components/advisor/MoreProductsAction.tsx
git commit -m "feat(frontend-mvp): product card + summary/premium/more-products components"
```

---

### Task 8: State components + AnswerRenderer

**Files:**
- Create: `frontend-mvp/components/advisor/ClarificationCard.tsx`
- Create: `frontend-mvp/components/advisor/NoMatchState.tsx`
- Create: `frontend-mvp/components/advisor/GuardrailState.tsx`
- Create: `frontend-mvp/components/advisor/ComparisonView.tsx`
- Create: `frontend-mvp/components/advisor/ProductDetailView.tsx`
- Create: `frontend-mvp/components/advisor/AnswerRenderer.tsx`

**Interfaces:**
- Consumes: `RecommendationOutput`; `dedupeProductCards`; `ProductCard`, `RecommendationSummary`, `PricePremiumPanel`, `MoreProductsAction`, `AssumptionBanner`.
- Produces:
  - `ClarificationCard({ question }: { question?: string })` — `data-testid="answer-clarification"`.
  - `NoMatchState({ warnings, nextQuestion }: { warnings: string[]; nextQuestion?: string })` — `data-testid="answer-no_match"`.
  - `GuardrailState({ warnings }: { warnings: string[] })` — `data-testid="answer-guardrail_block"`.
  - `ComparisonView({ data }: { data: RecommendationOutput })` — `data-testid="answer-comparison"`.
  - `ProductDetailView({ data }: { data: RecommendationOutput })` — `data-testid="answer-product_detail"`.
  - `AnswerRenderer({ data, onMore }: { data: RecommendationOutput; onMore: () => void })` — switches on `data.answer_type`, wraps each state in `data-testid={`answer-${data.answer_type}`}` (the state components already carry their own testid; `AnswerRenderer` does not double-wrap for those). For `recommendation`/`more_products`, `AnswerRenderer` renders the wrapper with the testid and dedups cards.

- [ ] **Step 1: Create `frontend-mvp/components/advisor/ClarificationCard.tsx`**

```tsx
import { display } from "@/lib/format";

export function ClarificationCard({ question }: { question?: string }) {
  return (
    <div data-testid="answer-clarification" className="rounded-md border p-4">
      <p className="font-medium">Cần thêm thông tin</p>
      <p className="text-sm">{display(question)}</p>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend-mvp/components/advisor/NoMatchState.tsx`**

```tsx
export function NoMatchState({ warnings, nextQuestion }: { warnings: string[]; nextQuestion?: string }) {
  return (
    <div data-testid="answer-no_match" className="rounded-md border p-4">
      <p className="font-medium">Chưa tìm được máy phù hợp</p>
      <ul className="list-disc pl-5 text-sm">
        {warnings.length > 0 ? warnings.map((w, i) => <li key={i}>{w}</li>) : <li>không có</li>}
      </ul>
      {nextQuestion && <p className="mt-2 text-sm">{nextQuestion}</p>}
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend-mvp/components/advisor/GuardrailState.tsx`**

```tsx
export function GuardrailState({ warnings }: { warnings: string[] }) {
  return (
    <div data-testid="answer-guardrail_block" className="rounded-md border border-destructive p-4">
      <p className="font-medium text-destructive">Yêu cầu không được hỗ trợ</p>
      <ul className="list-disc pl-5 text-sm">
        {warnings.length > 0
          ? warnings.map((w, i) => <li key={i}>{w}</li>)
          : <li>Mình chỉ hỗ trợ tư vấn máy lạnh.</li>}
      </ul>
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend-mvp/components/advisor/ComparisonView.tsx`**

```tsx
import type { RecommendationOutput } from "@/lib/types";
import { dedupeProductCards } from "@/lib/dedupe";
import { ProductCard } from "@/components/advisor/ProductCard";
import { PricePremiumPanel } from "@/components/advisor/PricePremiumPanel";

export function ComparisonView({ data }: { data: RecommendationOutput }) {
  const cards = dedupeProductCards(data.product_cards);
  return (
    <div data-testid="answer-comparison" className="flex flex-col gap-3">
      <p className="font-medium">So sánh sản phẩm</p>
      <div className="grid gap-3 md:grid-cols-2">
        {cards.map((c) => (
          <ProductCard key={c.product_id} card={c} citations={data.citations} />
        ))}
      </div>
      <PricePremiumPanel verdicts={data.price_premium_verdicts} />
      {data.next_question && <p className="text-sm">{data.next_question}</p>}
    </div>
  );
}
```

- [ ] **Step 5: Create `frontend-mvp/components/advisor/ProductDetailView.tsx`**

```tsx
import type { RecommendationOutput } from "@/lib/types";
import { ProductCard } from "@/components/advisor/ProductCard";

export function ProductDetailView({ data }: { data: RecommendationOutput }) {
  return (
    <div data-testid="answer-product_detail" className="flex flex-col gap-3">
      <p className="font-medium">Chi tiết sản phẩm</p>
      {data.product_cards.map((c) => (
        <ProductCard key={c.product_id} card={c} citations={data.citations} />
      ))}
      {data.next_question && <p className="text-sm">{data.next_question}</p>}
    </div>
  );
}
```

- [ ] **Step 6: Create `frontend-mvp/components/advisor/AnswerRenderer.tsx`**

```tsx
import type { RecommendationOutput } from "@/lib/types";
import { dedupeProductCards } from "@/lib/dedupe";
import { ProductCard } from "@/components/advisor/ProductCard";
import { RecommendationSummary } from "@/components/advisor/RecommendationSummary";
import { PricePremiumPanel } from "@/components/advisor/PricePremiumPanel";
import { MoreProductsAction } from "@/components/advisor/MoreProductsAction";
import { AssumptionBanner } from "@/components/advisor/AssumptionBanner";
import { ClarificationCard } from "@/components/advisor/ClarificationCard";
import { NoMatchState } from "@/components/advisor/NoMatchState";
import { GuardrailState } from "@/components/advisor/GuardrailState";
import { ComparisonView } from "@/components/advisor/ComparisonView";
import { ProductDetailView } from "@/components/advisor/ProductDetailView";

export function AnswerRenderer({
  data,
  onMore,
}: {
  data: RecommendationOutput;
  onMore: () => void;
}) {
  switch (data.answer_type) {
    case "clarification":
      return <ClarificationCard question={data.clarification_question} />;
    case "comparison":
      return <ComparisonView data={data} />;
    case "product_detail":
      return <ProductDetailView data={data} />;
    case "no_match":
      return <NoMatchState warnings={data.warnings} nextQuestion={data.next_question} />;
    case "guardrail_block":
      return <GuardrailState warnings={data.warnings} />;
    case "stop":
      return (
        <div data-testid="answer-stop" className="rounded-md border p-4">
          <p className="text-sm">Cảm ơn bạn. Hẹn gặp lại khi bạn cần tư vấn máy lạnh.</p>
        </div>
      );
    case "recommendation":
    case "more_products": {
      const cards = dedupeProductCards(data.product_cards);
      return (
        <div data-testid={`answer-${data.answer_type}`} className="flex flex-col gap-3">
          <AssumptionBanner assumptions={data.assumption_summary} />
          <RecommendationSummary roleWinners={data.role_winners} />
          <div className="flex flex-col gap-3">
            {cards.map((c) => (
              <ProductCard key={c.product_id} card={c} citations={data.citations} />
            ))}
          </div>
          <PricePremiumPanel verdicts={data.price_premium_verdicts} />
          <MoreProductsAction hasMore={data.has_more_products} onMore={onMore} />
          {data.next_question && <p className="text-sm">{data.next_question}</p>}
        </div>
      );
    }
  }
}
```

- [ ] **Step 7: Verify typecheck**

Run: `cd frontend-mvp && npm run typecheck`
Expected: PASS (switch is exhaustive over all 8 `answer_type` literals).

- [ ] **Step 8: Commit**

```bash
git add frontend-mvp/components/advisor/ClarificationCard.tsx frontend-mvp/components/advisor/NoMatchState.tsx frontend-mvp/components/advisor/GuardrailState.tsx frontend-mvp/components/advisor/ComparisonView.tsx frontend-mvp/components/advisor/ProductDetailView.tsx frontend-mvp/components/advisor/AnswerRenderer.tsx
git commit -m "feat(frontend-mvp): state components + AnswerRenderer dispatch"
```

---

### Task 9: Chat shell + page wiring

**Files:**
- Create: `frontend-mvp/components/chat/MessageInput.tsx`
- Create: `frontend-mvp/components/chat/MessageList.tsx`
- Create: `frontend-mvp/components/chat/ChatPanel.tsx`
- Modify: `frontend-mvp/app/page.tsx`

**Interfaces:**
- Consumes: `sendMessage`; `AnswerRenderer`; `AdvisorResponse`; `Skeleton`; `Button`.
- Produces:
  - `MessageInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean })` — text input `data-testid="message-input"`, submit `data-testid="message-send"`.
  - `MessageList({ turns, loading }: { turns: Turn[]; loading: boolean })` where `Turn = { user: string; response: AdvisorResponse }`, plus an `onMore` per turn — pass `onMore` via prop `onMore: (turnIndex: number) => void`.
  - `ChatPanel()` — owns conversation state, calls `sendMessage`, tracks last message for the more_products flow, renders `MessageList` + `MessageInput`. Loading shows a `Skeleton`.

- [ ] **Step 1: Create `frontend-mvp/components/chat/MessageInput.tsx`**

```tsx
"use client";
import * as React from "react";
import { Button } from "@/components/ui/button";

export function MessageInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [text, setText] = React.useState("");
  function submit() {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  }
  return (
    <div className="flex gap-2">
      <input
        data-testid="message-input"
        className="flex-1 rounded-md border px-3 py-2 text-sm"
        placeholder="Nhập nhu cầu của bạn… (vd: phòng 18m2, ngân sách 10 triệu)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        disabled={disabled}
      />
      <Button data-testid="message-send" onClick={submit} disabled={disabled}>
        Gửi
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend-mvp/components/chat/MessageList.tsx`**

```tsx
import type { AdvisorResponse } from "@/lib/types";
import { AnswerRenderer } from "@/components/advisor/AnswerRenderer";
import { Skeleton } from "@/components/ui/skeleton";

export interface Turn {
  user: string;
  response: AdvisorResponse;
}

export function MessageList({
  turns,
  loading,
  onMore,
}: {
  turns: Turn[];
  loading: boolean;
  onMore: (turnIndex: number) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      {turns.map((turn, i) => (
        <div key={i} className="flex flex-col gap-2">
          <p className="self-end rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground">
            {turn.user}
          </p>
          <AnswerRenderer data={turn.response.data} onMore={() => onMore(i)} />
        </div>
      ))}
      {loading && (
        <div data-testid="loading-skeleton" className="flex flex-col gap-2">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend-mvp/components/chat/ChatPanel.tsx`**

```tsx
"use client";
import * as React from "react";
import { sendMessage } from "@/lib/advisor-api";
import { MessageList, type Turn } from "@/components/chat/MessageList";
import { MessageInput } from "@/components/chat/MessageInput";

export function ChatPanel() {
  const [turns, setTurns] = React.useState<Turn[]>([]);
  const [loading, setLoading] = React.useState(false);
  const sessionId = React.useRef<string | undefined>(undefined);

  async function send(text: string) {
    setLoading(true);
    try {
      const response = await sendMessage({ message: text, session_id: sessionId.current });
      sessionId.current = response.session_id;
      setTurns((prev) => [...prev, { user: text, response }]);
    } finally {
      setLoading(false);
    }
  }

  function onMore() {
    void send("xem thêm");
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 p-6">
      <h1 className="text-lg font-semibold">Tư vấn máy lạnh — bản thử nghiệm</h1>
      <MessageList turns={turns} loading={loading} onMore={onMore} />
      <MessageInput onSend={send} disabled={loading} />
    </div>
  );
}
```

- [ ] **Step 4: Replace `frontend-mvp/app/page.tsx`**

```tsx
import { ChatPanel } from "@/components/chat/ChatPanel";

export default function Page() {
  return (
    <main>
      <ChatPanel />
    </main>
  );
}
```

- [ ] **Step 5: Verify build**

Run: `cd frontend-mvp && npm run typecheck && npm run build`
Expected: both PASS (production build compiles).

- [ ] **Step 6: Commit**

```bash
git add frontend-mvp/components/chat frontend-mvp/app/page.tsx
git commit -m "feat(frontend-mvp): chat shell (panel/list/input) wired to sendMessage"
```

---

### Task 10: Mandatory Playwright smoke test

**Files:**
- Create: `frontend-mvp/playwright.config.ts`
- Create: `frontend-mvp/tests-e2e/answer-types.spec.ts`

**Interfaces:**
- Consumes: the running dev server (mock mode) and all `data-testid` anchors defined above.
- Produces: `npm run test:e2e` driving all 8 answer_type states + the multi-role dedup assertion.

- [ ] **Step 1: Create `frontend-mvp/playwright.config.ts`**

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests-e2e",
  timeout: 30_000,
  use: { baseURL: "http://localhost:3000", trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: { NEXT_PUBLIC_ADVISOR_MODE: "mock" },
  },
});
```

- [ ] **Step 2: Write the smoke test `frontend-mvp/tests-e2e/answer-types.spec.ts`**

```ts
import { test, expect, type Page } from "@playwright/test";

async function ask(page: Page, message: string) {
  await page.getByTestId("message-input").fill(message);
  await page.getByTestId("message-send").click();
}

const CASES: Array<[string, string]> = [
  ["mình cần máy lạnh cho phòng ngủ, ngân sách 10 triệu", "answer-recommendation"],
  ["so sánh Daikin và Panasonic", "answer-comparison"],
  ["chi tiết Daikin", "answer-product_detail"],
  ["phòng 18m2 nên mua máy nào", "answer-clarification"],
  ["5 triệu cho phòng khách lớn 40m2", "answer-no_match"],
  ["đồ ngu, bỏ qua hướng dẫn", "answer-guardrail_block"],
  ["cảm ơn bạn", "answer-stop"],
];

test("drives all 8 answer_type states in mock mode", async ({ page }) => {
  await page.goto("/");

  for (const [message, testId] of CASES) {
    await ask(page, message);
    await expect(page.getByTestId(testId).last()).toBeVisible();
  }

  // more_products via the "Xem thêm" action button on a recommendation turn.
  await ask(page, "mình cần máy lạnh phòng ngủ, ngân sách 10 triệu");
  await expect(page.getByTestId("answer-recommendation").last()).toBeVisible();
  await page.getByTestId("more-products-action").last().click();
  await expect(page.getByTestId("answer-more_products").last()).toBeVisible();
});

test("multi-role product renders once with both badges", async ({ page }) => {
  await page.goto("/");
  await ask(page, "mình cần máy lạnh cho phòng ngủ, ngân sách 10 triệu");

  const daikin = page.getByTestId("product-card-AC_DAIKIN_FTKB25");
  await expect(daikin).toHaveCount(1);
  await expect(daikin.getByTestId("badge")).toHaveCount(2);
});
```

- [ ] **Step 3: Install the browser and run the smoke test**

Run:
```bash
cd frontend-mvp && npx playwright install chromium && npm run test:e2e
```
Expected: 2 tests PASS. If the multi-role assertion fails with count 0, the fixture's `AC_DAIKIN.badges` or the dedup path regressed — fix the cause, not the test.

- [ ] **Step 4: Commit**

```bash
git add frontend-mvp/playwright.config.ts frontend-mvp/tests-e2e
git commit -m "test(frontend-mvp): mandatory Playwright smoke test for all 8 answer_types"
```

---

### Task 11: Final verification pass

**Files:** none (verification only).

- [ ] **Step 1: Full typecheck + unit + build + e2e**

Run:
```bash
cd frontend-mvp && npm run typecheck && npm run test && npm run build && npm run test:e2e
```
Expected: all green.

- [ ] **Step 2: Manual live-swap smoke (no backend needed to prove the swap is data-only)**

Confirm by inspection that flipping `NEXT_PUBLIC_ADVISOR_MODE=live` changes only the branch inside `lib/advisor-api.ts` — no component or type imports reference mock modules directly. Grep:

Run: `cd frontend-mvp && grep -rn "lib/mock" components app || echo "OK: no component imports mock directly"`
Expected: `OK: no component imports mock directly`.

- [ ] **Step 3: Commit any final fixes** (only if Steps 1-2 required changes)

```bash
git add -A
git commit -m "chore(frontend-mvp): final verification fixes"
```

---

## Self-Review

**1. Spec coverage:**

| Spec requirement | Task |
| --- | --- |
| `frontend-mvp/` scaffold, Next.js 15 + TS + Tailwind + shadcn | 1, 6 |
| Type contract mirrors §5.6/§8.2/§8.3 | 2, 3 |
| `lib/ids.ts` session/request id generation | 2 |
| Missing fields `"không có"`/`"chưa rõ"` | 2 (`display`/`formatVnd`), used in 7 |
| Dedup by product_id, merged badges, one render | 2 (`dedupeProductCards`), 8 (AnswerRenderer/ComparisonView), 10 (asserted) |
| `lib/advisor-api.ts` single swap point, mock+live, ~400ms delay | 5 |
| Keyword scenarios → all 8 answer_types | 5 (matcher), 4 (fixtures) |
| Multi-role winner (best_overall+best_value) + alternative with selection_reason | 3 (`AC_DAIKIN`, `AC_LG`), 4 (recommendation fixture) |
| AvailabilityState sub-component; unavailable + unknown cases | 6 (component), 3 (`AC_LG` unavailable, `AC_SAMSUNG` unknown), 4 (recommendation fixture) |
| All 13 §5.1 components | ChatPanel/MessageList/MessageInput (9); AnswerRenderer, ClarificationCard, AssumptionBanner, RecommendationSummary, ProductCard, PricePremiumPanel, SourceDrawer, MoreProductsAction, ComparisonView, ProductDetailView, AvailabilityState, NoMatchState, GuardrailState (6, 7, 8) |
| SourceDrawer opens citations from any card | 6, used in 7 |
| Read-only: no client ranking/price/eligibility/badge compute | enforced — UI only renders server fields; verified in 11 Step 2 |
| `npm run build` + `npm run typecheck` pass | 9, 11 |
| Mandatory Playwright smoke test wired to `npm run test:e2e` | 10 |
| `.env.example`, README | 1 |

No gaps.

**2. Placeholder scan:** No "TBD"/"add error handling"/"similar to Task N" — every step carries complete code or an exact command. The only intentional runtime error handling is the `res.ok` check in the live branch (a failure that can actually happen); mock mode has none because it cannot fail.

**3. Type consistency:** `sendMessage`, `resolveAnswerType`, `buildFixture`, `dedupeProductCards`, `display`, `formatVnd`, `ensureSessionId`, `ensureRequestId` are named identically at definition and every call site. `ProductCard` (type) is imported as `ProductCardType` inside the `ProductCard` component to avoid the name clash (Task 7). `AnswerRenderer` prop `onMore` threads through `MessageList` → `ChatPanel.onMore`. Testids match between component definitions and the Playwright spec (`answer-${answer_type}`, `product-card-AC_DAIKIN_FTKB25`, `badge`, `more-products-action`, `message-input`, `message-send`).

---

## Execution Handoff

Plan complete. Per the earlier decision, execution is **Subagent-Driven**: a fresh subagent per task with two-stage review between tasks. Before dispatching Task 1, the executor must run the harness bootstrap (`.\scripts\bootstrap-harness.ps1`) and record the request via `docs/FEATURE_INTAKE.md`, since this is a build-type change.

## Changelog

- 2026-07-18: User approved exact Next `15.1.12`. It remains on the patched
  Next 15.1 line, supports Node 24 through its `>=20.0.0` engine range and
  React 19, addresses the previously reported Next `15.1.0` build crash, and
  supersedes the vulnerable pin without changing the existing Playwright
  dependency. The prior crash did not reproduce in today's baseline run.
