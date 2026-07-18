"use client";

import {
  RefreshCw,
  RotateCcw,
  Send,
  X,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { SafeImage } from "@/components/SafeImage";
import { ChatComparisonResult } from "@/components/chat/ChatComparisonResult";
import { useToast } from "@/components/ToastProvider";

interface ChatMessage {
  id: number;
  role: "assistant" | "user";
  text: string;
  time: string;
  kind?: "comparison";
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

function isComparisonQuery(query: string) {
  const normalized = normalizeChatQuery(query);
  return (
    /so sanh/.test(normalized) && /may lanh|dieu hoa/.test(normalized)
  );
}

function formatChatTime(date: Date) {
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
}

// Live E02 sales agent (backend/app/agent). Falls back to the retry UI when
// the API is unreachable.
const AGENT_API_BASE =
  process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8000";

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
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [failedQuery, setFailedQuery] = useState("");
  const sequence = useRef(1);
  const sessionId = useRef<string | null>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const replyTimer = useRef<number | null>(null);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const latestComparison = useRef<HTMLDivElement>(null);

  const closeChat = useCallback(() => {
    setIsOpen(false);
    window.requestAnimationFrame(() => launcher.current?.focus());
  }, []);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const latestMessage = messages[messages.length - 1];
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)")
      .matches
      ? "auto"
      : "smooth";
    if (latestMessage?.kind === "comparison") {
      latestComparison.current?.scrollIntoView({
        behavior,
        block: "start",
      });
      return;
    }
    conversationEnd.current?.scrollIntoView({
      behavior,
      block: "nearest",
    });
  }, [isOpen, messages, isSending]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.requestAnimationFrame(() => composer.current?.focus());

    const handleDialogKeyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeChat();
        return;
      }
      if (event.key !== "Tab") {
        return;
      }

      const focusable = dialog.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), a[href], textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", handleDialogKeyboard);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleDialogKeyboard);
    };
  }, [closeChat, isOpen]);

  useEffect(
    () => () => {
      if (replyTimer.current !== null) {
        window.clearTimeout(replyTimer.current);
      }
    },
    [],
  );

  const openChat = () => {
    if (!openedAt) {
      setOpenedAt(formatChatTime(new Date()));
    }
    setIsOpen(true);
  };

  const requestReply = async (query: string) => {
    setIsSending(true);
    setFailedQuery("");

    try {
      const response = await fetch(`${AGENT_API_BASE}/api/v1/agent/respond`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId.current, message: query }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: { session_id: string; text: string } = await response.json();
      sessionId.current = data.session_id;
      setMessages((current) => [
        ...current,
        {
          id: sequence.current++,
          role: "assistant",
          text: data.text,
          time: formatChatTime(new Date()),
          kind: isComparisonQuery(query) ? "comparison" : undefined,
        },
      ]);
    } catch {
      setFailedQuery(query);
      showToast({
        variant: "error",
        title: "Chưa nhận được phản hồi",
        description: "Không kết nối được trợ lý AI. Bạn có thể thử lại ngay.",
      });
    } finally {
      setIsSending(false);
    }
  };

  const sendQuery = (rawQuery: string) => {
    const query = rawQuery.trim();
    if (!query || isSending) {
      return;
    }
    if (query.length < 2) {
      showToast({
        variant: "error",
        title: "Tin nhắn quá ngắn",
        description: "Vui lòng nhập ít nhất 2 ký tự.",
      });
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: sequence.current++,
        role: "user",
        text: query,
        time: formatChatTime(new Date()),
      },
    ]);
    setInput("");
    requestReply(query);
  };

  const submitMessage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    sendQuery(input);
  };

  const resetChat = () => {
    if (replyTimer.current !== null) {
      window.clearTimeout(replyTimer.current);
      replyTimer.current = null;
    }
    setMessages([]);
    setInput("");
    setFailedQuery("");
    setIsSending(false);
    sessionId.current = null;
    setOpenedAt(formatChatTime(new Date()));
    showToast({ variant: "info", title: "Đã làm mới hội thoại", description: "Bạn có thể bắt đầu câu hỏi mới." });
    window.requestAnimationFrame(() => composer.current?.focus());
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
            <SafeImage src="/images/chatbot/chat-bot.png" alt="" className="size-[56px] rounded-full object-cover" fallbackLabel="AI" />
            <span className="absolute -right-2 -top-1 rounded-full bg-white px-1.5 py-px text-[9px] font-bold leading-[14px] text-slate-600 shadow-sm">BETA</span>
          </span>
        </button>
      </div>
    );
  }

  return (
    <>
      <div
        className="fixed inset-0 z-[79] bg-slate-950/25 backdrop-blur-[1px]"
        aria-hidden="true"
        onMouseDown={closeChat}
      />
    <section
      ref={dialog}
      role="dialog"
      aria-modal="true"
      aria-labelledby="chatbot-title"
      className="chatbot-panel fixed z-[80] flex flex-col overflow-hidden rounded-2xl bg-white shadow-[0_16px_48px_rgba(15,23,42,0.28)]"
    >
      <header className="flex min-h-16 shrink-0 items-center justify-between border-b border-blue-800/20 bg-[#176fc9] px-3 py-2 text-white sm:px-4">
        <div className="flex items-center gap-2">
          <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 rounded-full border border-white/30 object-cover" fallbackLabel="AI" />
          <div className="leading-tight">
            <p id="chatbot-title" className="text-sm font-bold">Trợ lý AI Điện máy XANH</p>
            <p className="mt-1 text-xs font-medium text-white">Phản hồi tự động</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={resetChat} disabled={isSending || messages.length === 0} className="flex size-11 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 focus-visible:outline-white active:scale-95 sm:size-9" aria-label="Làm mới hội thoại" title="Làm mới">
            <RefreshCw className="size-4" />
          </button>
          <button type="button" onClick={closeChat} className="flex size-11 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 focus-visible:outline-white active:scale-95 sm:size-9" aria-label="Đóng chatbot" title="Đóng">
            <X className="size-5" />
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overscroll-y-contain overflow-y-auto px-3 pb-5 sm:px-4">
        {messages.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-5 text-center sm:py-6">
          <SafeImage src="/images/chatbot/chat-bot.png" alt="" className="size-16 rounded-full border border-blue-50 sm:size-20" fallbackLabel="AI" />
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Chọn máy lạnh dễ hơn cùng AI
            </h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Cho mình biết diện tích phòng, ngân sách và điều bạn ưu tiên.
            </p>
          </div>
          <div className="w-full max-w-xl">
            <p className="mb-2 text-xs font-semibold text-slate-500">
              Bắt đầu nhanh
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

        <p className="text-center text-xs font-medium text-slate-500">Bắt đầu lúc {openedAt}</p>
        <div className="mt-3 flex items-end gap-1.5">
          <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
          <div className="max-w-[88%] rounded-[20px] rounded-ss-none bg-slate-100 px-4 py-3 text-sm leading-6 text-slate-800">
            Bạn đang cần chọn máy lạnh cho phòng bao nhiêu m² và ngân sách khoảng bao nhiêu?
          </div>
        </div>

        <div
          className="mt-3 space-y-3"
          role="log"
          aria-live="polite"
          aria-relevant="additions text"
          aria-busy={isSending}
        >
          {messages.map((message) => {
            const isComparison =
              message.role === "assistant" && message.kind === "comparison";

            return (
              <div
                key={message.id}
                ref={
                  isComparison &&
                  message.id === messages[messages.length - 1]?.id
                    ? latestComparison
                    : undefined
                }
                className={`scroll-mt-3 flex gap-1.5 ${isComparison ? "items-start" : "items-end"} ${message.role === "user" ? "justify-end" : "justify-start"}`}
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
                    isComparison
                      ? "min-w-0 flex-1 text-left"
                      : `max-w-[84%] ${message.role === "user" ? "text-right" : "text-left"}`
                  }
                >
                  <div
                    className={`whitespace-pre-line rounded-[20px] px-4 py-3 text-sm leading-6 ${message.role === "user" ? "rounded-ee-none bg-[#176fc9] text-white" : "rounded-ss-none bg-slate-100 text-slate-800"}`}
                  >
                    {message.text}
                  </div>
                  {isComparison ? (
                    <div className="-ml-[42px] w-[calc(100%+42px)]">
                      <ChatComparisonResult
                        disabled={isSending}
                        onNavigate={closeChat}
                        onSuggestion={sendQuery}
                      />
                    </div>
                  ) : null}
                  <p className="mt-1 px-1 text-xs font-medium text-slate-500">
                    {message.time}
                  </p>
                </div>
              </div>
            );
          })}

          {isSending ? (
            <div className="flex items-end gap-1.5">
              <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
              <div className="flex h-10 items-center gap-1 rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4" role="status" aria-label="Trợ lý đang trả lời">
                <span className="sr-only">Trợ lý đang trả lời</span>
                <span className="size-1.5 animate-bounce rounded-full bg-slate-400" />
                <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />
                <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />
              </div>
            </div>
          ) : null}

          {failedQuery ? (
            <div role="alert" className="ml-10 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <p>Không thể nhận phản hồi cho tin nhắn này.</p>
              <button type="button" onClick={() => requestReply(failedQuery)} className="mt-2 inline-flex items-center gap-1 font-semibold text-rose-700 hover:underline">
                <RotateCcw className="size-4" /> Thử lại
              </button>
            </div>
          ) : null}
          <div ref={conversationEnd} />
        </div>
      </div>

      <footer className="shrink-0 border-t border-slate-200 bg-white px-3 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 sm:px-4">
        <form onSubmit={submitMessage} className="flex min-h-14 items-end rounded-[22px] border border-slate-200 bg-slate-100 px-1.5 py-1 focus-within:border-[#176fc9] focus-within:ring-2 focus-within:ring-blue-100" noValidate>
          <textarea
            ref={composer}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Mô tả nhu cầu của bạn..."
            rows={1}
            maxLength={1000}
            className="min-h-11 max-h-28 min-w-0 flex-1 resize-none bg-transparent px-3 py-3 text-[15px] leading-5 text-slate-900 outline-none [field-sizing:content] placeholder:text-slate-500"
            aria-label="Tin nhắn"
            aria-describedby="chatbot-disclaimer"
          />
          <button type="submit" disabled={!input.trim() || isSending} className="flex size-11 shrink-0 items-center justify-center rounded-full text-white transition enabled:bg-[#176fc9] enabled:hover:bg-[#0754ad] disabled:text-slate-400 sm:size-9" aria-label="Gửi tin nhắn">
            <Send className="size-[22px]" />
          </button>
        </form>
        <p id="chatbot-disclaimer" className="mt-1.5 text-center text-xs leading-4 text-slate-600">
          AI có thể sai. Vui lòng xác nhận giá và tồn kho trước khi mua.
        </p>
      </footer>
    </section>
    </>
  );
}
