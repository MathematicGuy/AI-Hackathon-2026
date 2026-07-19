import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatbotAssistant } from "@/components/ChatbotAssistant";

const { showToast } = vi.hoisted(() => ({ showToast: vi.fn() }));

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("@/components/ToastProvider", () => ({
  useToast: () => ({ showToast }),
}));

function response(patch: Record<string, unknown> = {}) {
  return new Response(
    JSON.stringify({
      session_id: "session-1",
      request_id: "request-1",
      intent: "new_search",
      text: "Phản hồi đã kiểm chứng.",
      flags: [],
      presented_ids: [],
      presentation: {
        type: "text",
        products: [],
        comparison_rows: [],
        follow_up_questions: [],
        warnings: [],
      },
      ...patch,
    }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
}

function recommendation() {
  return {
    type: "recommendation",
    products: [
      {
        sku: "TV-1",
        productidweb: null,
        name: "TV do máy chủ chọn",
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
      },
    ],
    comparison_rows: [],
    follow_up_questions: [],
    warnings: [],
  };
}

function openChat() {
  fireEvent.click(
    screen.getByRole("button", { name: /Mở Trợ lý AI Điện máy XANH/ }),
  );
}

function send(message: string) {
  fireEvent.change(screen.getByRole("textbox", { name: "Tin nhắn" }), {
    target: { value: message },
  });
  fireEvent.click(screen.getByRole("button", { name: "Gửi tin nhắn" }));
}

describe("ChatbotAssistant agent responses", () => {
  beforeEach(() => {
    showToast.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses presentation.type instead of the query or intent and keeps the session", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        response({
          intent: "compare_products",
          text: "Cần thêm sản phẩm để so sánh.",
        }),
      )
      .mockResolvedValueOnce(
        response({
          request_id: "request-2",
          intent: "new_search",
          text: "Đây là lựa chọn phù hợp.",
          presentation: recommendation(),
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<ChatbotAssistant />);
    openChat();

    send("So sánh máy lạnh nổi bật");

    expect(await screen.findByText("Cần thêm sản phẩm để so sánh.")).toBeInTheDocument();
    expect(screen.queryByTestId("chat-comparison-result")).not.toBeInTheDocument();
    expect(screen.queryByTestId("chat-text-presentation")).not.toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.queryByRole("status", { name: "Trợ lý đang trả lời" }),
      ).not.toBeInTheDocument(),
    );

    send("Cho tôi một lựa chọn");

    expect(await screen.findByTestId("chat-recommendation-result")).toBeInTheDocument();
    expect(screen.getByText("TV do máy chủ chọn")).toBeInTheDocument();
    const secondRequest = JSON.parse(
      (fetchMock.mock.calls[1][1] as RequestInit).body as string,
    );
    expect(secondRequest).toEqual({
      session_id: "session-1",
      message: "Cho tôi một lựa chọn",
    });
  });

  it("retries the same query after an HTTP failure without stale presentation", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(response({ text: "Đã thử lại thành công." }));
    vi.stubGlobal("fetch", fetchMock);
    render(<ChatbotAssistant />);
    openChat();

    send("Tư vấn giúp tôi");
    const alert = await screen.findByRole("alert");
    expect(screen.queryByTestId("chat-comparison-result")).not.toBeInTheDocument();
    fireEvent.click(withinAlertButton(alert));

    expect(await screen.findByText("Đã thử lại thành công.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(
      JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string),
    ).toEqual({ session_id: null, message: "Tư vấn giúp tôi" });
  });
});

function withinAlertButton(alert: HTMLElement) {
  const button = alert.querySelector("button");
  if (!button) {
    throw new Error("Retry button was not rendered");
  }
  return button;
}
