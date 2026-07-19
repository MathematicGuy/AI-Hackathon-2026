"use client";

import {
  Copy,
  Pencil,
  RefreshCw,
  RotateCcw,
  Send,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { SafeImage } from "@/components/SafeImage";
import {
  ChatComparisonResult,
  type AgentComparison,
} from "@/components/chat/ChatComparisonResult";
import { useToast } from "@/components/ToastProvider";

// A stalled backend must not leave the composer spinning forever.
const REQUEST_TIMEOUT_MS = 60_000;

interface ChatMessage {
  id: number;
  role: "assistant" | "user";
  text: string;
  time: string;
  // Set from the agent's own `comparison` block, never inferred from the
  // query text: the table and the answer come from one source.
  comparison?: AgentComparison;
  imageUrl?: string;
  imageType?: "representative";
  mappingVersion?: number;
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

// Live E02 sales agent (backend/app/agent). Falls back to the retry UI when
// the API is unreachable. The path is same-origin on purpose: nginx routes
// /api/ to the backend in production, next.config.ts rewrites it in dev.

// Natural progress line while waiting, picked from the query (replaces "...").
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
  if (/khuyen mai|uu dai|giam gia/.test(normalized)) {
    return "Em đang tổng hợp ưu đãi đang chạy ạ…";
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
  return "Anh/chị cần em tư vấn chọn sản phẩm?";
}

export function ChatbotAssistant() {
  const pathname = usePathname();
  const { showToast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [openedAt, setOpenedAt] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [pendingStatus, setPendingStatus] = useState("");
  const [failedQuery, setFailedQuery] = useState("");
  const [feedback, setFeedback] = useState<Record<number, "like" | "dislike">>({});
  const sequence = useRef(1);
  const sessionId = useRef<string | null>(null);
  // User messages to silently re-send after an edit rebuilt the session.
  const replayQueue = useRef<string[]>([]);
  const launcher = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const replyTimer = useRef<number | null>(null);
  const conversationScroller = useRef<HTMLDivElement>(null);
  const latestComparison = useRef<HTMLDivElement>(null);

  const closeChat = useCallback(() => {
    setIsOpen(false);
    window.requestAnimationFrame(() => launcher.current?.focus());
  }, []);

  useEffect(() => {
    const desktopQuery = window.matchMedia("(min-width: 768px)");
    const updateViewportMode = () => setIsDesktop(desktopQuery.matches);
    updateViewportMode();
    desktopQuery.addEventListener("change", updateViewportMode);
    return () => desktopQuery.removeEventListener("change", updateViewportMode);
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
    const scroller = conversationScroller.current;
    if (!scroller) {
      return;
    }
    if (messages.length === 0 && !isSending) {
      scroller.scrollTo({ top: 0, behavior: "auto" });
      return;
    }
    if (latestMessage?.comparison && latestComparison.current) {
      const comparisonTop =
        latestComparison.current.getBoundingClientRect().top -
        scroller.getBoundingClientRect().top +
        scroller.scrollTop;
      scroller.scrollTo({ top: Math.max(0, comparisonTop - 12), behavior });
      return;
    }
    scroller.scrollTo({ top: scroller.scrollHeight, behavior });
  }, [isOpen, messages, isSending]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    if (!isDesktop) {
      document.body.style.overflow = "hidden";
    }
    window.requestAnimationFrame(() => {
      if (isDesktop) {
        composer.current?.focus();
      } else {
        closeButton.current?.focus();
      }
    });

    const handleDialogKeyboard = (event: KeyboardEvent) => {
      if (
        event.key === "Escape" &&
        (!isDesktop || dialog.current?.contains(document.activeElement))
      ) {
        closeChat();
        return;
      }
      if (isDesktop || event.key !== "Tab") {
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
      if (!isDesktop) {
        document.body.style.overflow = previousOverflow;
      }
      window.removeEventListener("keydown", handleDialogKeyboard);
    };
  }, [closeChat, isDesktop, isOpen]);

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
    setPendingStatus(statusForQuery(query));
    const assistantId = sequence.current++;
    let started = false;
    // Bounds the whole turn, including the streaming read loop: without it a
    // stalled backend leaves the UI in "đang trả lời" with no way out.
    const abort = new AbortController();
    const timeout = window.setTimeout(() => abort.abort(), REQUEST_TIMEOUT_MS);

    try {
      // After an edit, rebuild the server-side session by replaying the
      // earlier user messages (the deterministic pipeline makes this cheap).
      if (replayQueue.current.length > 0) {
        const queue = [...replayQueue.current];
        replayQueue.current = [];
        setPendingStatus("Em đang cập nhật lại ngữ cảnh ạ…");
        for (const past of queue) {
          const replayResponse = await fetch("/api/v1/agent/respond", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sessionId.current,
              message: past,
            }),
            signal: abort.signal,
          });
          // A failed replay silently desyncs the server-side context, so it
          // must not pass unnoticed.
          if (!replayResponse.ok) {
            throw new Error(`replay HTTP ${replayResponse.status}`);
          }
          const data = (await replayResponse.json()) as { session_id?: string };
          if (data.session_id) {
            sessionId.current = data.session_id;
          }
        }
        setPendingStatus(statusForQuery(query));
      }
      const response = await fetch("/api/v1/agent/respond/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId.current, message: query }),
        signal: abort.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }
          const event = JSON.parse(line) as {
            type: string;
            text?: string;
            session_id?: string;
            comparison?: AgentComparison | null;
            image_url?: string | null;
            image_type?: "representative" | null;
            mapping_version?: number | null;
          };
          if (event.type === "chunk" && event.text !== undefined) {
            if (!started) {
              started = true;
              setPendingStatus("");
              setMessages((current) => [
                ...current,
                {
                  id: assistantId,
                  role: "assistant",
                  text: event.text ?? "",
                  time: formatChatTime(new Date()),
                },
              ]);
            } else {
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantId
                    ? { ...message, text: message.text + (event.text ?? "") }
                    : message,
                ),
              );
            }
          } else if (event.type === "done") {
            if (event.session_id) {
              sessionId.current = event.session_id;
            }
            // The table arrives with the final event, built by the agent from
            // the same records the reply text quotes.
            if (event.comparison) {
              const table = event.comparison;
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantId
                    ? { ...message, comparison: table }
                    : message,
                ),
              );
            }
            if (event.image_url && event.image_type === "representative") {
              const imageUrl = event.image_url;
              const mappingVersion = event.mapping_version ?? undefined;
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantId
                    ? {
                        ...message,
                        imageUrl,
                        imageType: "representative",
                        mappingVersion,
                      }
                    : message,
                ),
              );
            }
          }
        }
      }
      if (!started) {
        throw new Error("empty stream");
      }
    } catch (error) {
      const timedOut =
        error instanceof DOMException && error.name === "AbortError";
      if (!started) {
        setFailedQuery(query);
        showToast({
          variant: "error",
          title: timedOut ? "Phản hồi quá lâu" : "Chưa nhận được phản hồi",
          description: timedOut
            ? "Trợ lý chưa trả lời kịp. Anh/chị thử lại giúp em ạ."
            : "Không kết nối được trợ lý AI. Anh/chị có thể thử lại ngay.",
        });
      } else if (timedOut) {
        // Partial answer already on screen: say so instead of leaving a
        // truncated reply looking complete.
        showToast({
          variant: "error",
          title: "Phản hồi bị gián đoạn",
          description: "Câu trả lời chưa hoàn tất. Anh/chị hỏi lại giúp em ạ.",
        });
      }
    } finally {
      window.clearTimeout(timeout);
      setIsSending(false);
      setPendingStatus("");
    }
  };

  const copyMessage = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      showToast({ variant: "success", title: "Đã sao chép", description: "Nội dung đã vào bộ nhớ tạm." });
    } catch {
      showToast({ variant: "error", title: "Không sao chép được", description: "Trình duyệt chặn quyền clipboard." });
    }
  };

  const editMessage = (id: number, text: string) => {
    // Real edit semantics: cut the conversation back to before this message,
    // queue the earlier user turns for a silent replay on a fresh session,
    // and load the text into the composer for editing.
    const index = messages.findIndex((message) => message.id === id);
    if (index === -1) {
      return;
    }
    const prefix = messages.slice(0, index);
    setMessages(prefix);
    replayQueue.current = prefix
      .filter((message) => message.role === "user")
      .map((message) => message.text);
    sessionId.current = null;
    setInput(text);
    window.requestAnimationFrame(() => composer.current?.focus());
  };

  const rateMessage = (id: number, rating: "like" | "dislike") => {
    setFeedback((current) => {
      const next = { ...current };
      if (next[id] === rating) {
        delete next[id];
      } else {
        next[id] = rating;
      }
      return next;
    });
    void fetch("/api/v1/agent/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId.current ?? "no-session",
        message_index: id,
        rating,
      }),
    }).catch(() => {
      // Roll the optimistic rating back so the UI does not claim a vote that
      // never reached the server.
      setFeedback((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      showToast({
        variant: "error",
        title: "Chưa gửi được đánh giá",
        description: "Anh/chị thử lại giúp em ạ.",
      });
    });
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
    setFeedback({});
    setIsSending(false);
    sessionId.current = null;
    replayQueue.current = [];
    setOpenedAt(formatChatTime(new Date()));
    showToast({ variant: "info", title: "Đã làm mới hội thoại", description: "Anh/chị có thể bắt đầu câu hỏi mới." });
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
      {!isDesktop ? (
        <div
          className="fixed inset-0 z-[79] bg-slate-950/25 backdrop-blur-[1px]"
          aria-hidden="true"
          onMouseDown={closeChat}
        />
      ) : null}
    <section
      ref={dialog}
      role="dialog"
      aria-modal={!isDesktop}
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
          <button ref={closeButton} type="button" onClick={closeChat} className="flex size-11 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 focus-visible:outline-white active:scale-95 sm:size-9" aria-label="Đóng chatbot" title="Đóng">
            <X className="size-5" />
          </button>
        </div>
      </header>

      <div ref={conversationScroller} className="min-h-0 flex-1 overscroll-y-contain overflow-y-auto px-3 pb-5 sm:px-4">
        {messages.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-5 text-center sm:py-6">
          <SafeImage src="/images/chatbot/chat-bot.png" alt="" className="size-16 rounded-full border border-blue-50 sm:size-20" fallbackLabel="AI" />
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Em có thể giúp anh/chị chọn sản phẩm
            </h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Hỏi về nhu cầu, so sánh, khuyến mãi hoặc bảo hành.
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
            Dạ anh/chị đang quan tâm sản phẩm nào ạ? Em có thể giúp lọc lựa chọn hoặc so sánh nhanh ạ.
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
              message.role === "assistant" && message.comparison !== undefined;

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
                  {message.imageUrl && message.imageType === "representative" ? (
                    <figure
                      data-testid="chat-representative-image"
                      data-mapping-version={message.mappingVersion}
                      className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white p-2 shadow-sm"
                    >
                      <SafeImage
                        src={message.imageUrl}
                        alt="Hình ảnh minh họa cho sản phẩm được tư vấn"
                        className="mx-auto aspect-square max-h-52 w-full rounded-xl object-contain"
                        fallbackLabel="Hình ảnh minh họa"
                      />
                      <figcaption className="mt-1.5 text-center text-xs font-medium text-slate-500">
                        Hình ảnh minh họa
                      </figcaption>
                    </figure>
                  ) : null}
                  {message.comparison ? (
                    <div className="-ml-[42px] w-[calc(100%+42px)]">
                      <ChatComparisonResult
                        comparison={message.comparison}
                        disabled={isSending}
                        onSuggestion={sendQuery}
                      />
                    </div>
                  ) : null}
                  <div
                    className={`mt-1 flex items-center gap-1 px-1 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <p className="text-xs font-medium text-slate-500">
                      {message.time}
                    </p>
                    {message.role === "assistant" ? (
                      <>
                        <button
                          type="button"
                          onClick={() => copyMessage(message.text)}
                          className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-[#176fc9]"
                          aria-label="Sao chép nội dung"
                          title="Sao chép"
                        >
                          <Copy className="size-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => rateMessage(message.id, "like")}
                          className={`rounded p-1 transition hover:bg-slate-100 ${feedback[message.id] === "like" ? "text-[#176fc9]" : "text-slate-400 hover:text-[#176fc9]"}`}
                          aria-label="Hài lòng với câu trả lời"
                          aria-pressed={feedback[message.id] === "like"}
                          title="Hài lòng"
                        >
                          <ThumbsUp className="size-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => rateMessage(message.id, "dislike")}
                          className={`rounded p-1 transition hover:bg-slate-100 ${feedback[message.id] === "dislike" ? "text-red-500" : "text-slate-400 hover:text-red-500"}`}
                          aria-label="Chưa hài lòng với câu trả lời"
                          aria-pressed={feedback[message.id] === "dislike"}
                          title="Chưa hài lòng"
                        >
                          <ThumbsDown className="size-3.5" />
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => editMessage(message.id, message.text)}
                        className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-[#176fc9]"
                        aria-label="Chỉnh sửa và gửi lại từ đây"
                        title="Chỉnh sửa và gửi lại"
                      >
                        <Pencil className="size-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {isSending && pendingStatus ? (
            <div className="flex items-end gap-1.5">
              <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
              <div className="flex min-h-10 items-center gap-2 rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4 py-2 text-sm text-slate-600" role="status" aria-label="Trợ lý đang trả lời">
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
              <button type="button" onClick={() => requestReply(failedQuery)} className="mt-2 inline-flex items-center gap-1 font-semibold text-rose-700 hover:underline">
                <RotateCcw className="size-4" /> Thử lại
              </button>
            </div>
          ) : null}
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
            placeholder="Mô tả nhu cầu của anh/chị..."
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
