import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatComparisonResult } from "@/components/chat/ChatComparisonResult";
import type {
  AgentPresentation,
  AgentPresentedProduct,
} from "@/types/agent";

function product(
  sku: string,
  patch: Partial<AgentPresentedProduct> = {},
): AgentPresentedProduct {
  return {
    sku,
    productidweb: null,
    name: `Sản phẩm ${sku}`,
    brand: null,
    effective_price_vnd: null,
    list_price_vnd: null,
    discount_percent: null,
    promotion_text: null,
    badges: [],
    highlights: [],
    image_url: null,
    product_url: null,
    rating: null,
    sold_count: null,
    ...patch,
  };
}

const noOp = () => undefined;

describe("ChatComparisonResult", () => {
  it("renders one recommendation card with all server badges and honest nulls", () => {
    const presentation: AgentPresentation = {
      type: "recommendation",
      products: [
        product("SKU-1", {
          name: "Máy lạnh do máy chủ chọn",
          effective_price_vnd: 5_000_000,
          list_price_vnd: 5_000_000,
          discount_percent: 0,
          badges: [
            { code: "best_value", label: "Giá trị tốt" },
            { code: "future_role", label: "Nhãn mới từ máy chủ" },
          ],
          highlights: [{ label: "Công suất", value: null }],
        }),
      ],
      comparison_rows: [],
      follow_up_questions: [],
      warnings: [],
    };

    render(
      <ChatComparisonResult
        presentation={presentation}
        disabled={false}
        onNavigate={noOp}
        onSuggestion={noOp}
      />,
    );

    expect(screen.getAllByTestId("chat-presentation-product-SKU-1")).toHaveLength(1);
    expect(screen.getByText("Giá trị tốt")).toBeInTheDocument();
    expect(screen.getByText("Nhãn mới từ máy chủ")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Chưa có hình ảnh" })).toBeInTheDocument();
    expect(screen.getByText("Chưa có liên kết sản phẩm")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getAllByText("Chưa có dữ liệu").length).toBeGreaterThan(2);
    expect(screen.getAllByText(/5\.000\.000/)).toHaveLength(1);
    expect(screen.queryByText("-0%")).not.toBeInTheDocument();
  });

  it("renders only server-supplied comparison labels, values, links and follow-ups", () => {
    const onSuggestion = vi.fn();
    const presentation: AgentPresentation = {
      type: "comparison",
      products: [
        product("PHONE-A", {
          name: "Điện thoại A",
          product_url: "/san-pham/phone-a",
        }),
        product("PHONE-B", { name: "Điện thoại B" }),
      ],
      comparison_rows: [
        {
          label: "Bộ nhớ",
          values: [
            { sku: "PHONE-A", value: "128 GB" },
            { sku: "PHONE-B", value: null },
          ],
        },
      ],
      follow_up_questions: ["So sánh camera?"],
      warnings: ["Giá có thể thay đổi theo khu vực."],
    };

    render(
      <ChatComparisonResult
        presentation={presentation}
        disabled={false}
        onNavigate={noOp}
        onSuggestion={onSuggestion}
      />,
    );

    const table = screen.getByRole("table");
    expect(within(table).getByText("Bộ nhớ")).toBeInTheDocument();
    expect(within(table).getByText("128 GB")).toBeInTheDocument();
    expect(screen.getAllByTestId(/chat-presentation-product-/)).toHaveLength(2);
    expect(screen.getAllByRole("link")).toHaveLength(1);
    expect(screen.getByRole("region", { name: "Bảng có thể cuộn ngang" })).toHaveAttribute(
      "tabindex",
      "0",
    );
    expect(screen.queryByText("Công suất")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "So sánh camera?" }));
    expect(onSuggestion).toHaveBeenCalledWith("So sánh camera?");
  });

  it("does not mount comparison UI for an empty text presentation", () => {
    const presentation: AgentPresentation = {
      type: "text",
      products: [],
      comparison_rows: [],
      follow_up_questions: [],
      warnings: [],
    };

    const { container } = render(
      <ChatComparisonResult
        presentation={presentation}
        disabled={false}
        onNavigate={noOp}
        onSuggestion={noOp}
      />,
    );

    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});
