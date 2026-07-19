"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Copy, RefreshCw, RotateCcw, Send, Sparkles, X } from "lucide-react";
import { ChatComparisonResult } from "@/components/chat/ChatComparisonResult";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import { requestAgentReply } from "@/lib/agent-api";
import type { AgentResponse } from "@/types/agent";

const REQUEST_TIMEOUT_MS = 60_000;

interface ChatMessage {
  id: number;
  role: "assistant" | "user";
  text: string;
  time: string;
  response?: AgentResponse;
}

const QUICK_QUESTIONS = [
  "So sánh máy lạnh nổi bật",
  "Phòng 18m² nên chọn mấy HP?",
  "Máy lạnh có khuyến mãi gì?",
];

function normalizeChatQuery(query: string) {
  return query
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("vi-VN")
    .replace(/đ/g, "d");
}

function formatChatTime(date: Date) {
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
}

function statusForQuery(query: string) {
  const normalized = normalizeChatQuery(query);
  if (/chinh sach|bao hanh|doi tra|hoan tien|dieu khoan/.test(normalized)) {
    return "Em đang xem chính sách của bên em ạ…";
  }
  if (/con hang|kho|ton kho|co san/.test(normalized)) {
    return "Để em kiểm tra kho hàng ạ…";
  }
  if (/so sanh/.test(normalized)) {
    return "Em đang so sánh các mẫu giúp anh/chị ạ…";
  }
  return "Em đang lọc sản phẩm phù hợp cho anh/chị ạ…";
}

function suggestionForPath(pathname: string) {
  if (pathname === "/flashsale") {
    return "Săn deal World Cup hôm nay";
  }
  if (pathname.startsWith("/san-pham/")) {
    return "Cần em tư vấn sản phẩm này?";
  }
  if (pathname.startsWith("/danh-muc/")) {
    return "So sánh sản phẩm bán chạy";
  }
  if (pathname === "/lich-su-mua-hang") {
    return "Hỗ trợ kiểm tra đơn hàng";
  }
  return "Bạn cần tư vấn chọn sản phẩm?";
}

export function ChatbotAssistant() {
  const pathname = usePathname();
  const { showToast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [openedAt, setOpenedAt] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [pendingStatus, setPendingStatus] = useState("");
  const [failedQuery, setFailedQuery] = useState("");

  const conversationScroller = useRef<HTMLDivElement | null>(null);
  const latestPresentation = useRef<HTMLDivElement | null>(null);
  const composer = useRef<HTMLTextAreaElement | null>(null);
  const launcher = useRef<HTMLButtonElement | null>(null);
  const sessionId = useRef<string | null>(null);
  const sequence = useRef(1);

  useEffect(() => {
    if (isOpen) {
      window.requestAnimationFrame(() => composer.current?.focus());
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const latestMessage = messages[messages.length - 1];
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth";
    const scroller = conversationScroller.current;
    if (!scroller) {
      return;
    }
    if (messages.length === 0 && !isSending) {
      scroller.scrollTo({ top: 0, behavior: "auto" });
      return;
    }
    const latestPresentationData = latestMessage?.response?.presentation;
    const latestHasPresentation =
      latestMessage?.role === "assistant" &&
      latestPresentationData &&
      (latestPresentationData.type !== "text" ||
        latestPresentationData.warnings.length > 0 ||
        latestPresentationData.follow_up_questions.length > 0);
    if (latestHasPresentation && latestPresentation.current) {
      const presentationTop =
        latestPresentation.current.getBoundingClientRect().top -
        scroller.getBoundingClientRect().top +
        scroller.scrollTop;
      scroller.scrollTo({ top: Math.max(0, presentationTop - 12), behavior });
      return;
    }
    scroller.scrollTo({ top: scroller.scrollHeight, behavior });
  }, [messages, isSending, isOpen]);

  const openChat = () => {
    if (!openedAt) {
      setOpenedAt(formatChatTime(new Date()));
    }
    setIsOpen(true);
  };

  const closeChat = () => {
    setIsOpen(false);
    window.requestAnimationFrame(() => launcher.current?.focus());
  };

  const resetChat = () => {
    setMessages([]);
    setInput("");
    setFailedQuery("");
    setIsSending(false);
    sessionId.current = null;
    setOpenedAt(formatChatTime(new Date()));
    showToast({
      variant: "info",
      title: "Đã làm mới hội thoại",
      description: "Bạn có thể bắt đầu câu hỏi mới.",
    });
    window.requestAnimationFrame(() => composer.current?.focus());
  };

  const sendQuery = (query: string) => {
    const trimmed = query.trim();
    if (!trimmed || isSending) {
      return;
    }
    setMessages((current) => [
      ...current,
      {
        id: sequence.current++,
        role: "user",
        text: trimmed,
        time: formatChatTime(new Date()),
      },
    ]);
    setInput("");
    void requestReply(trimmed);
  };

  const submitMessage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    sendQuery(input);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendQuery(input);
    }
  };

  const requestReply = async (query: string) => {
    setIsSending(true);
    setFailedQuery("");
    setPendingStatus(statusForQuery(query));
    const abort = new AbortController();
    const timeout = window.setTimeout(() => abort.abort(), REQUEST_TIMEOUT_MS);

    try {
      const data = await requestAgentReply({
        session_id: sessionId.current,
        message: query,
      });
      sessionId.current = data.session_id;
      setMessages((current) => [
        ...current,
        {
          id: sequence.current++,
          role: "assistant",
          text: data.text,
          time: formatChatTime(new Date()),
          response: data,
        },
      ]);
    } catch (error) {
      const timedOut = error instanceof DOMException && error.name === "AbortError";
      setFailedQuery(query);
      showToast({
        variant: "error",
        title: timedOut ? "Phản hồi quá lâu" : "Chưa nhận được phản hồi",
        description: timedOut
          ? "Trợ lý chưa trả lời kịp. Anh/chị thử lại giúp em ạ."
          : "Không kết nối được trợ lý AI. Anh/chị có thể thử lại ngay.",
      });
    } finally {
      window.clearTimeout(timeout);
      setIsSending(false);
      setPendingStatus("");
    }
  };

  const copyMessage = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      showToast({
        variant: "success",
        title: "Đã sao chép",
        description: "Nội dung đã vào bộ nhớ tạm.",
      });
    } catch {
      showToast({
        variant: "error",
        title: "Không sao chép được",
        description: "Trình duyệt chặn quyền clipboard.",
      });
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-5 right-4 z-[80] sm:bottom-20 sm:right-14">
        <button
          ref={launcher}
          type="button"
          onClick={openChat}
          className="group flex flex-col items-end gap-2 transition hover:-translate-y-0.5 active:translate-y-0"
          aria-label={`Mở Trợ lý AI Điện máy XANH: ${suggestionForPath(pathname)}`}
        >
          <span className="max-w-[250px] rounded-[18px] bg-white px-3.5 py-2.5 text-left text-xs font-semibold leading-5 text-slate-700 shadow-[0_6px_20px_rgba(15,23,42,0.16)] transition group-hover:text-[#0754ad]">
            {suggestionForPath(pathname)}
          </span>
          <span className="relative flex size-[58px] items-center justify-center rounded-full bg-white shadow-lg ring-2 ring-white">
            <SafeImage
              src="/images/chatbot/chat-bot.png"
              alt=""
              className="size-[56px] rounded-full object-cover"
              fallbackLabel="AI"
            />
            <span className="absolute -right-2 -top-1 rounded-full bg-white px-1.5 py-px text-[9px] font-bold leading-[14px] text-slate-600 shadow-sm">
              BETA
            </span>
          </span>
        </button>
      </div>
    );
  }

  return (
    <>
      <div
        className="fixed inset-0 z-[79] bg-slate-950/25 backdrop-blur-[1px] md:hidden"
        aria-hidden="true"
        onMouseDown={closeChat}
      />
      <section
        data-testid="chatbot-panel"
        className="chatbot-panel fixed z-[80] flex flex-col overflow-hidden rounded-2xl bg-white shadow-[0_16px_48px_rgba(15,23,42,0.28)]"
        aria-label="Cửa sổ trò chuyện Trợ lý AI"
      >
        <header className="flex min-h-16 shrink-0 items-center justify-between border-b border-blue-800/20 bg-[#176fc9] px-3 py-2 text-white sm:px-4">
          <div className="flex items-center gap-2">
            <SafeImage
              src="/images/chatbot/mascot.png"
              alt=""
              className="size-9 rounded-full border border-white/30 object-cover"
              fallbackLabel="AI"
            />
            <div className="leading-tight">
              <h2 className="text-sm font-bold">Trợ lý AI Điện máy XANH</h2>
              <p className="mt-0.5 text-xs font-medium text-blue-100">Tư vấn sản phẩm & so sánh giá</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={resetChat}
              className="flex size-9 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 active:scale-95"
              aria-label="Làm mới hội thoại"
              title="Làm mới"
            >
              <RefreshCw className="size-4" />
            </button>
            <button
              type="button"
              onClick={closeChat}
              className="flex size-9 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 active:scale-95"
              aria-label="Đóng Trợ lý AI"
              title="Đóng"
            >
              <X className="size-5" />
            </button>
          </div>
        </header>

        <div
          ref={conversationScroller}
          className="chat-scrollbar min-h-0 flex-1 overscroll-y-contain overflow-y-auto px-3 pb-5 sm:px-4 space-y-3"
        >
          {messages.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-5 text-center sm:py-6">
              <SafeImage
                src="/images/chatbot/chat-bot.png"
                alt=""
                className="size-16 rounded-full border border-blue-50 sm:size-20"
                fallbackLabel="AI"
              />
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Em có thể giúp anh/chị chọn sản phẩm
                </h3>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Tư vấn nhu cầu, so sánh giá, khuyến mãi và thông số kỹ thuật.
                </p>
              </div>
              <div className="w-full max-w-xl">
                <p className="mb-2 text-xs font-semibold text-slate-500">
                  Gợi ý nhanh
                </p>
                <div className="grid gap-2 sm:flex sm:flex-wrap sm:justify-center">
                  {QUICK_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      disabled={isSending}
                      onClick={() => sendQuery(question)}
                      className="min-h-11 rounded-xl border border-blue-200 bg-blue-50 px-3.5 py-2 text-sm font-semibold text-[#0754ad] transition hover:border-blue-300 hover:bg-blue-100 active:scale-[0.98] sm:rounded-full sm:text-xs"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : null}

          {openedAt ? (
            <p className="text-center text-xs font-medium text-slate-500">
              Bắt đầu lúc {openedAt}
            </p>
          ) : null}

          {messages.map((message) => {
            const presentation =
              message.role === "assistant"
                ? message.response?.presentation
                : undefined;
            const isRichPresentation =
              presentation?.type === "recommendation" ||
              presentation?.type === "comparison";
            const shouldRenderPresentation =
              presentation &&
              (presentation.type !== "text" ||
                presentation.warnings.length > 0 ||
                presentation.follow_up_questions.length > 0);

            return (
              <div
                key={message.id}
                ref={
                  shouldRenderPresentation &&
                  message.id === messages[messages.length - 1]?.id
                    ? latestPresentation
                    : undefined
                }
                className={`scroll-mt-3 flex gap-1.5 ${isRichPresentation ? "items-start" : "items-end"} ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" ? (
                  <SafeImage
                    src="/images/chatbot/mascot.png"
                    alt=""
                    className="size-9 shrink-0 rounded-full"
                    fallbackLabel="AI"
                  />
                ) : null}
                <div
                  className={
                    isRichPresentation
                      ? "min-w-0 flex-1 text-left"
                      : `max-w-[84%] ${message.role === "user" ? "text-right" : "text-left"}`
                  }
                >
                  <div
                    className={`whitespace-pre-line rounded-[20px] px-4 py-3 text-sm leading-6 ${message.role === "user" ? "rounded-ee-none bg-[#176fc9] text-white" : "rounded-ss-none bg-slate-100 text-slate-800"}`}
                  >
                    {message.text}
                  </div>
                  {message.response?.image_url &&
                  message.response.image_type === "representative" ? (
                    <figure
                      data-testid="chat-representative-image"
                      data-mapping-version={message.response.mapping_version}
                      className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white p-2 shadow-sm"
                    >
                      <SafeImage
                        src={message.response.image_url}
                        alt="Hình ảnh minh họa cho sản phẩm được tư vấn"
                        className="mx-auto aspect-square max-h-52 w-full rounded-xl object-contain"
                        fallbackLabel="Hình ảnh minh họa"
                      />
                      <figcaption className="mt-1.5 text-center text-xs font-medium text-slate-500">
                        Hình ảnh minh họa
                      </figcaption>
                    </figure>
                  ) : null}
                  {shouldRenderPresentation ? (
                    <div
                      className={
                        isRichPresentation
                          ? "-ml-[42px] w-[calc(100%+42px)]"
                          : undefined
                      }
                    >
                      <ChatComparisonResult
                        presentation={presentation}
                        disabled={isSending}
                        onNavigate={closeChat}
                        onSuggestion={sendQuery}
                      />
                    </div>
                  ) : null}
                  <div
                    className={`mt-1 flex items-center gap-1 px-1 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <p className="text-xs font-medium text-slate-500">{message.time}</p>
                    {message.role === "assistant" ? (
                      <button
                        type="button"
                        onClick={() => copyMessage(message.text)}
                        className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-[#176fc9]"
                        aria-label="Sao chép nội dung"
                        title="Sao chép"
                      >
                        <Copy className="size-3.5" />
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}

          {isSending && pendingStatus ? (
            <div className="flex items-end gap-1.5">
              <SafeImage
                src="/images/chatbot/mascot.png"
                alt=""
                className="size-9 shrink-0 rounded-full"
                fallbackLabel="AI"
              />
              <div
                role="status"
                aria-label="Trợ lý đang trả lời"
                className="flex min-h-10 items-center gap-2 rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4 py-2 text-sm text-slate-600"
              >
                <span>{pendingStatus}</span>
                <span className="flex gap-1">
                  <span className="size-1.5 animate-bounce rounded-full bg-slate-400" />
                  <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />
                </span>
              </div>
            </div>
          ) : null}

          {failedQuery ? (
            <div role="alert" className="ml-10 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <p>Không thể nhận phản hồi cho tin nhắn này.</p>
              <button
                type="button"
                onClick={() => sendQuery(failedQuery)}
                className="mt-2 inline-flex items-center gap-1 font-semibold text-rose-700 hover:underline"
              >
                <RotateCcw className="size-4" /> Thử lại
              </button>
            </div>
          ) : null}
        </div>

        <footer className="shrink-0 border-t border-slate-200 bg-white px-3 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 sm:px-4">
          <form onSubmit={submitMessage} className="flex min-h-14 items-end rounded-[22px] border border-slate-200 bg-slate-100 px-1.5 py-1 focus-within:border-[#176fc9] focus-within:ring-2 focus-within:ring-blue-100">
            <textarea
              ref={composer}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Mô tả nhu cầu của bạn..."
              aria-label="Tin nhắn"
              className="min-h-11 max-h-28 min-w-0 flex-1 resize-none bg-transparent px-3 py-3 text-[15px] leading-5 text-slate-900 outline-none placeholder:text-slate-500"
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || isSending}
              aria-label="Gửi tin nhắn"
              className="flex size-11 shrink-0 items-center justify-center rounded-full text-white transition enabled:bg-[#176fc9] enabled:hover:bg-[#0754ad] disabled:text-slate-400 sm:size-9"
            >
              <Send className="size-[22px]" />
            </button>
          </form>
        </footer>
      </section>
    </>
  );
}
