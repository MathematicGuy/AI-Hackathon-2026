import { describe, expect, it } from "vitest";
import { parseAgentResponse } from "@/lib/agent-api";

function product(sku: string) {
  return {
    sku,
    productidweb: null,
    name: `Sản phẩm ${sku}`,
    brand: null,
    effective_price_vnd: 5_000_000,
    list_price_vnd: 5_500_000,
    discount_percent: 9,
    promotion_text: null,
    badges: [{ code: "best_value", label: "Đáng cân nhắc" }],
    highlights: [{ label: "Công suất", value: "1 HP" }],
    image_url: "https://cdn.example.test/product.jpg",
    product_url: `/san-pham/${sku}`,
    rating: 4.8,
    sold_count: 120,
  };
}

function comparisonPresentation() {
  return {
    type: "comparison",
    products: [product("SKU-1"), product("SKU-2")],
    comparison_rows: [
      {
        label: "Công suất",
        values: [
          { sku: "SKU-2", value: "1.5 HP" },
          { sku: "SKU-1", value: "1 HP" },
        ],
      },
    ],
    follow_up_questions: ["Xem thêm khuyến mãi?"],
    warnings: [],
  };
}

function envelope(presentation: unknown = comparisonPresentation()) {
  return {
    session_id: "session-1",
    request_id: "request-1",
    intent: "compare_products",
    text: "Nội dung dự phòng đã được kiểm chứng.",
    flags: [],
    presented_ids: ["SKU-1", "SKU-2"],
    presentation,
  };
}

describe("parseAgentResponse", () => {
  it("accepts a valid aligned comparison and future top-level fields", () => {
    const parsed = parseAgentResponse({
      ...envelope(),
      future_envelope_field: { enabled: true },
    });

    expect(parsed.session_id).toBe("session-1");
    expect(parsed.presentation?.type).toBe("comparison");
    expect(parsed.presentation?.products.map(({ sku }) => sku)).toEqual([
      "SKU-1",
      "SKU-2",
    ]);
  });

  it.each([
    ["absent", undefined],
    ["null", null],
    ["unknown discriminator", { ...comparisonPresentation(), type: "future" }],
    ["malformed shape", { ...comparisonPresentation(), products: "invalid" }],
  ])("keeps session and text when presentation is %s", (_label, value) => {
    const input = envelope(value);
    if (value === undefined) {
      delete (input as { presentation?: unknown }).presentation;
    }

    const parsed = parseAgentResponse(input);

    expect(parsed).toMatchObject({
      session_id: "session-1",
      text: "Nội dung dự phòng đã được kiểm chứng.",
    });
    expect(parsed.presentation).toBeUndefined();
  });

  it("rejects products and rows on a text presentation", () => {
    const parsed = parseAgentResponse(
      envelope({
        ...comparisonPresentation(),
        type: "text",
        comparison_rows: [],
      }),
    );

    expect(parsed.presentation).toBeUndefined();
    expect(parsed.text).toContain("dự phòng");
  });

  it("rejects duplicate recommendation product SKUs", () => {
    const parsed = parseAgentResponse(
      envelope({
        type: "recommendation",
        products: [product("SKU-1"), product("SKU-1")],
        comparison_rows: [],
        follow_up_questions: [],
        warnings: [],
      }),
    );

    expect(parsed.presentation).toBeUndefined();
  });

  it.each([
    [
      "duplicate row SKU",
      [
        { sku: "SKU-1", value: "1 HP" },
        { sku: "SKU-1", value: "1.5 HP" },
      ],
    ],
    ["missing row SKU", [{ sku: "SKU-1", value: "1 HP" }]],
    [
      "unknown row SKU",
      [
        { sku: "SKU-1", value: "1 HP" },
        { sku: "SKU-3", value: "1.5 HP" },
      ],
    ],
  ])("rejects a comparison with %s", (_label, values) => {
    const presentation = comparisonPresentation();
    presentation.comparison_rows[0].values = values;

    expect(parseAgentResponse(envelope(presentation)).presentation).toBeUndefined();
  });

  it("accepts a comparison without optional rows when products are unique", () => {
    const presentation = comparisonPresentation();
    presentation.comparison_rows = [];

    expect(parseAgentResponse(envelope(presentation)).presentation?.type).toBe(
      "comparison",
    );
  });

  it("normalizes unsafe product and image URLs to unavailable", () => {
    const unsafeProduct = {
      ...product("SKU-1"),
      product_url: "javascript:alert(1)",
      image_url: "data:image/svg+xml,unsafe",
    };
    const parsed = parseAgentResponse(
      envelope({
        type: "recommendation",
        products: [unsafeProduct],
        comparison_rows: [],
        follow_up_questions: [],
        warnings: [],
      }),
    );

    expect(parsed.presentation?.products[0]).toMatchObject({
      product_url: null,
      image_url: null,
    });
  });

  it.each([
    ["negative price", { effective_price_vnd: -1 }],
    ["negative sold count", { sold_count: -1 }],
    ["discount over 100", { discount_percent: 101 }],
    ["rating over 5", { rating: 5.1 }],
  ])("drops presentation for %s", (_label, patch) => {
    const parsed = parseAgentResponse(
      envelope({
        type: "recommendation",
        products: [{ ...product("SKU-1"), ...patch }],
        comparison_rows: [],
        follow_up_questions: [],
        warnings: [],
      }),
    );

    expect(parsed.presentation).toBeUndefined();
    expect(parsed.session_id).toBe("session-1");
  });

  it("throws only when the required envelope cannot be trusted", () => {
    expect(() => parseAgentResponse({ text: "Thiếu session" })).toThrow(
      "Invalid agent response envelope",
    );
    expect(() => parseAgentResponse({ ...envelope(), text: " " })).toThrow(
      "Invalid agent response envelope",
    );
  });
});
