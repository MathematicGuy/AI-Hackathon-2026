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
