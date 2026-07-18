"use client";

import {
  Mic,
  RefreshCw,
  RotateCcw,
  Send,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
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

function getAssistantReply(query: string) {
  const normalized = normalizeChatQuery(query);

  if (/bao hanh|sua chua|ve sinh/.test(normalized)) {
    return "Em có thể hỗ trợ tra cứu bảo hành, vệ sinh máy lạnh hoặc máy giặt. Anh/chị mở mục Thông tin - Dịch vụ tiện ích trong Danh mục để chọn đúng dịch vụ nhé.";
  }
  if (/giao hang|van chuyen|bao lau|nhan hang/.test(normalized)) {
    return "Thời gian giao hàng phụ thuộc khu vực và tình trạng tồn kho. Với TP. Hồ Chí Minh, sản phẩm có sẵn thường được xác nhận lịch giao trong ngày ạ.";
  }
  if (/cua hang|dia chi|sieu thi/.test(normalized)) {
    return "Anh/chị có thể dùng mục Tìm địa chỉ cửa hàng trong Danh mục. Bản demo sẽ hiển thị cửa hàng gần khu vực TP. Hồ Chí Minh và thông tin liên hệ local.";
  }
  if (isComparisonQuery(query)) {
    return "Em đã rút gọn thành 3 lựa chọn để anh/chị dễ so sánh. Các nhãn chỉ mô tả điểm nổi bật trong nhóm sản phẩm đang hiển thị.";
  }
  if (/gia|khuyen mai|giam|flash|sale/.test(normalized)) {
    return "Anh/chị có thể xem giá Flash Sale đang áp dụng theo từng nhóm sản phẩm. Giá cuối cùng và số suất còn lại được hiển thị ngay trên thẻ sản phẩm ạ.";
  }
  if (/may lanh|dieu hoa/.test(normalized)) {
    return "Phòng dưới 15m² thường phù hợp máy lạnh 1 HP; từ 15-20m² nên cân nhắc 1.5 HP. Anh/chị cho em biết diện tích phòng để tư vấn sát hơn nhé.";
  }
  if (/tu lanh/.test(normalized)) {
    return "Nếu gia đình 3-4 người, anh/chị có thể ưu tiên tủ lạnh 250-350 lít có Inverter. Em đề xuất xem nhóm Tủ lạnh để so sánh giá và dung tích ạ.";
  }
  if (/tivi|tv/.test(normalized)) {
    return "Khoảng cách xem 2-3 mét phù hợp tivi 50-55 inch. Các mẫu 4K QLED đang có ưu đãi tốt trong Flash Sale ạ.";
  }
  if (/may giat/.test(normalized)) {
    return "Gia đình 3-5 người thường phù hợp máy giặt 9-10 kg. Nếu cần tiết kiệm điện nước và bảo vệ quần áo, anh/chị nên chọn máy Inverter cửa trước.";
  }

  return "Dạ em có thể hỗ trợ anh/chị tư vấn sản phẩm, kiểm tra thông tin hàng hóa, khuyến mãi, bảo hành và hướng dẫn mua hàng. Anh/chị đang quan tâm sản phẩm nào ạ?";
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
  return "Tivi được đánh giá tốt nhất";
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
  const failedOnce = useRef(new Set<string>());
  const conversationEnd = useRef<HTMLDivElement>(null);
  const latestComparison = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const latestMessage = messages[messages.length - 1];
    if (latestMessage?.kind === "comparison") {
      latestComparison.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
      return;
    }
    conversationEnd.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [isOpen, messages, isSending]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isOpen]);

  const openChat = () => {
    if (!openedAt) {
      setOpenedAt(formatChatTime(new Date()));
    }
    setIsOpen(true);
  };

  const requestReply = (query: string) => {
    setIsSending(true);
    setFailedQuery("");

    window.setTimeout(() => {
      const normalized = query.trim().toLocaleLowerCase("vi-VN");
      const shouldFail = normalized.includes("lỗi") && !failedOnce.current.has(normalized);

      if (shouldFail) {
        failedOnce.current.add(normalized);
        setIsSending(false);
        setFailedQuery(query);
        showToast({
          variant: "error",
          title: "Chưa nhận được phản hồi",
          description: "Kết nối mô phỏng bị gián đoạn. Bạn có thể thử lại ngay.",
        });
        return;
      }

      setMessages((current) => [
        ...current,
        {
          id: sequence.current++,
          role: "assistant",
          text: getAssistantReply(query),
          time: formatChatTime(new Date()),
          kind: isComparisonQuery(query) ? "comparison" : undefined,
        },
      ]);
      setIsSending(false);
    }, 760);
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
    setMessages([]);
    setInput("");
    setFailedQuery("");
    setIsSending(false);
    setOpenedAt(formatChatTime(new Date()));
    showToast({ variant: "info", title: "Đã làm mới hội thoại", description: "Bạn có thể bắt đầu câu hỏi mới." });
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-5 right-4 z-[80] flex flex-col-reverse items-end gap-2 sm:bottom-20 sm:right-14">
        <button
          type="button"
          onClick={openChat}
          className="group relative flex size-[55px] items-center justify-center rounded-full transition hover:scale-105 active:scale-95"
          aria-label="Mở Trợ lý AI Điện máy XANH"
        >
          <SafeImage src="/images/chatbot/chat-bot.png" alt="Trợ lý AI Điện máy XANH" className="size-[55px] rounded-full object-cover shadow-lg" fallbackLabel="AI" />
          <span className="absolute -right-3 -top-1 rounded-full bg-[linear-gradient(#fff,#ddd)] px-1.5 py-px text-[9px] font-bold leading-[14px] text-[#526478] shadow-sm">BETA</span>
        </button>
        <button
          type="button"
          onClick={openChat}
          className="min-h-11 max-w-[250px] rounded-[20px] bg-white px-3 py-2 text-left text-xs text-[#374151] shadow-[0_4px_12px_rgba(0,0,0,0.12)] transition hover:text-[#2a83e9] active:translate-y-px"
        >
          {suggestionForPath(pathname)}
        </button>
      </div>
    );
  }

  return (
    <section
      role="dialog"
      aria-modal="false"
      aria-label="Trợ lý AI Điện máy XANH"
      className="fixed inset-x-2 bottom-2 z-[80] flex h-[calc(100dvh-16px)] flex-col overflow-hidden rounded-2xl bg-white shadow-[0_4px_24px_rgba(0,0,0,0.22)] sm:inset-auto sm:bottom-4 sm:right-4 sm:h-[min(720px,calc(100dvh-32px))] sm:w-[min(720px,calc(100vw-32px))]"
    >
      <header className="flex min-h-14 shrink-0 items-center justify-between border-b border-[#dde5ee] bg-[#2a83e9] px-3 py-2 text-white sm:px-4">
        <div className="flex items-center gap-2">
          <SafeImage src="/images/chatbot/mascot.png" alt="Điện máy XANH" className="size-7 rounded-full object-cover" fallbackLabel="AI" />
          <div className="leading-tight">
            <p className="text-sm font-semibold">Điện máy XANH</p>
            <p className="mt-0.5 flex items-center gap-1 text-[11px] text-white/80"><span className="size-1.5 rounded-full bg-green-400" /> Trực tuyến</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={resetChat} className="flex size-11 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 active:scale-95 sm:size-9" aria-label="Làm mới hội thoại" title="Làm mới">
            <RefreshCw className="size-4" />
          </button>
          <button type="button" onClick={() => setIsOpen(false)} className="flex size-11 items-center justify-center rounded-xl bg-white/10 transition hover:bg-white/20 active:scale-95 sm:size-9" aria-label="Đóng chatbot" title="Đóng">
            <X className="size-5" />
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-5 sm:px-4">
        <div className="flex flex-col items-center gap-3 py-5 text-center sm:py-6">
          <SafeImage src="/images/chatbot/chat-bot.png" alt="Trợ lý AI ĐMX" className="size-16 rounded-full border border-[#f5f8fd] sm:size-20" fallbackLabel="AI" />
          <p className="text-sm font-medium leading-[21px] text-[#333]">
            Chào anh/chị, em là <strong className="font-semibold text-[#2a83e9]">Trợ lý AI ĐMX</strong><br />
            Em trả lời thắc mắc và giúp anh/chị lựa chọn sản phẩm phù hợp
          </p>
          <div className="w-full max-w-xl">
            <p className="mb-2 text-xs font-semibold text-slate-500">
              Câu hỏi gợi ý
            </p>
            <div className="scrollbar-none flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:justify-center">
              {QUICK_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  disabled={isSending}
                  onClick={() => sendQuery(question)}
                  className="min-h-11 shrink-0 rounded-full border border-blue-100 bg-blue-50 px-3.5 py-2 text-xs font-semibold text-[#0754ad] transition hover:border-blue-300 hover:bg-blue-100 active:scale-[0.98]"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-[#515764]">Hôm nay, {openedAt}</p>
        <div className="mt-3 flex items-end gap-1.5">
          <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
          <div className="max-w-[88%] rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4 py-3 text-sm leading-[1.4] text-[#333]">
            Dạ em có thể giúp gì ạ.
          </div>
        </div>

        <div className="mt-2 space-y-2">
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
                    aria-live={
                      message.role === "assistant" ? "polite" : undefined
                    }
                    className={`rounded-[20px] px-4 py-3 text-sm leading-[1.5] ${message.role === "user" ? "rounded-ee-none bg-[#2a83e9] text-white" : "rounded-ss-none bg-[#f2f5f9] text-[#333]"}`}
                  >
                    {message.text}
                  </div>
                  {isComparison ? (
                    <div className="-ml-[42px] w-[calc(100%+42px)]">
                      <ChatComparisonResult
                        disabled={isSending}
                        onNavigate={() => setIsOpen(false)}
                        onSuggestion={sendQuery}
                      />
                    </div>
                  ) : null}
                  <p className="mt-1 px-1 text-[11px] text-slate-400">
                    {message.time}
                  </p>
                  {message.role === "assistant" ? (
                    <div className="mt-1 flex justify-end gap-0.5 text-slate-400">
                      <button
                        type="button"
                        onClick={() =>
                          showToast({
                            variant: "success",
                            title: "Cảm ơn phản hồi",
                            description:
                              "Phản hồi này giúp cải thiện trợ lý.",
                          })
                        }
                        className="flex size-11 items-center justify-center rounded-full hover:bg-slate-100 hover:text-[#2a83e9] sm:size-9"
                        aria-label="Phản hồi hữu ích"
                      >
                        <ThumbsUp className="size-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          showToast({
                            variant: "info",
                            title: "Đã ghi nhận",
                            description:
                              "Trợ lý sẽ điều chỉnh câu trả lời phù hợp hơn.",
                          })
                        }
                        className="flex size-11 items-center justify-center rounded-full hover:bg-slate-100 hover:text-rose-500 sm:size-9"
                        aria-label="Phản hồi chưa hữu ích"
                      >
                        <ThumbsDown className="size-4" />
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            );
          })}

          {isSending ? (
            <div className="flex items-end gap-1.5">
              <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
              <div className="flex h-10 items-center gap-1 rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4" role="status" aria-label="Trợ lý đang trả lời">
                <span className="size-1.5 animate-bounce rounded-full bg-slate-400" />
                <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />
                <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />
              </div>
            </div>
          ) : null}

          {failedQuery ? (
            <div className="ml-10 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <p>Không thể nhận phản hồi cho tin nhắn này.</p>
              <button type="button" onClick={() => requestReply(failedQuery)} className="mt-2 inline-flex items-center gap-1 font-semibold text-rose-700 hover:underline">
                <RotateCcw className="size-4" /> Thử lại
              </button>
            </div>
          ) : null}
          <div ref={conversationEnd} />
        </div>
      </div>

      <footer className="shrink-0 border-t border-slate-100 bg-white px-3 pb-2 pt-2 sm:px-4">
        <form onSubmit={submitMessage} className="flex min-h-14 items-center rounded-[22px] border border-transparent bg-[#f2f5f9] px-1 focus-within:border-[#2a83e9]" noValidate>
          <button type="button" onClick={() => showToast({ variant: "info", title: "Nhập bằng giọng nói", description: "Trình duyệt demo chưa cấp quyền microphone. Bạn hãy nhập nội dung bằng bàn phím." })} className="flex size-11 shrink-0 items-center justify-center rounded-full text-[#9da7bc] hover:bg-white hover:text-[#2a83e9] sm:size-9" aria-label="Nhập bằng giọng nói">
            <Mic className="size-5" />
          </button>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value.slice(0, 1000))}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Nhập tin nhắn..."
            rows={1}
            className="h-11 min-w-0 flex-1 resize-none bg-transparent px-3 py-3 text-[15px] leading-5 outline-none placeholder:text-[#9da7bc]"
            aria-label="Tin nhắn"
          />
          <button type="submit" disabled={!input.trim() || isSending} className="flex size-11 shrink-0 items-center justify-center rounded-full text-white transition enabled:bg-[#2a83e9] enabled:hover:bg-[#176fc9] disabled:text-[#9da7bc] sm:size-9" aria-label="Gửi tin nhắn">
            <Send className="size-[22px]" />
          </button>
        </form>
        <p className="mt-1.5 text-center text-[10px] leading-4 text-[#7b8495] sm:text-[11px]">
          AI có thể sai. Vui lòng xác nhận giá và tồn kho trước khi mua.
        </p>
      </footer>
    </section>
  );
}
