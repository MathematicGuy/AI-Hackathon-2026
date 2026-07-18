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
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";

interface ChatMessage {
  id: number;
  role: "assistant" | "user";
  text: string;
  time: string;
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
  const normalized = query
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .toLocaleLowerCase("vi-VN");

  if (/gia|khuyen mai|giam|flash|sale/.test(normalized)) {
    return "Anh/chị có thể xem giá Flash Sale đang áp dụng theo từng nhóm sản phẩm. Giá cuối cùng và số suất còn lại được hiển thị ngay trên thẻ sản phẩm ạ.";
  }
  if (/bao hanh|sua chua|ve sinh/.test(normalized)) {
    return "Em có thể hỗ trợ tra cứu bảo hành, vệ sinh máy lạnh hoặc máy giặt. Anh/chị mở mục Thông tin - Dịch vụ tiện ích trong Danh mục để chọn đúng dịch vụ nhé.";
  }
  if (/giao hang|van chuyen|bao lau|nhan hang/.test(normalized)) {
    return "Thời gian giao hàng phụ thuộc khu vực và tình trạng tồn kho. Với TP. Hồ Chí Minh, sản phẩm có sẵn thường được xác nhận lịch giao trong ngày ạ.";
  }
  if (/cua hang|dia chi|sieu thi/.test(normalized)) {
    return "Anh/chị có thể dùng mục Tìm địa chỉ cửa hàng trong Danh mục. Bản demo sẽ hiển thị cửa hàng gần khu vực TP. Hồ Chí Minh và thông tin liên hệ local.";
  }
  if (/tu lanh/.test(normalized)) {
    return "Nếu gia đình 3-4 người, anh/chị có thể ưu tiên tủ lạnh 250-350 lít có Inverter. Em đề xuất xem nhóm Tủ lạnh để so sánh giá và dung tích ạ.";
  }
  if (/may lanh|dieu hoa/.test(normalized)) {
    return "Phòng dưới 15m² thường phù hợp máy lạnh 1 HP; từ 15-20m² nên cân nhắc 1.5 HP. Anh/chị cho em biết diện tích phòng để tư vấn sát hơn nhé.";
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

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    conversationEnd.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
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
        },
      ]);
      setIsSending(false);
    }, 760);
  };

  const submitMessage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = input.trim();
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
          className="max-w-[250px] rounded-[20px] bg-white px-3 py-2 text-left text-xs text-[#374151] shadow-[0_4px_12px_rgba(0,0,0,0.12)] transition hover:text-[#2a83e9] active:translate-y-px"
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
      className="fixed inset-x-3 bottom-3 z-[80] flex h-[min(620px,calc(100dvh-90px))] flex-col overflow-hidden rounded-lg bg-white shadow-[0_4px_18px_rgba(0,0,0,0.2)] sm:inset-x-auto sm:bottom-6 sm:right-4 sm:h-[min(520px,calc(100vh-150px))] sm:w-[360px]"
    >
      <header className="flex h-[49px] shrink-0 items-center justify-between border-b border-[#dde5ee] bg-[#2a83e9] px-3 py-2 text-white sm:px-4">
        <div className="flex items-center gap-2">
          <SafeImage src="/images/chatbot/mascot.png" alt="Điện máy XANH" className="size-7 rounded-full object-cover" fallbackLabel="AI" />
          <div className="leading-tight">
            <p className="text-sm font-semibold">Điện máy XANH</p>
            <p className="mt-0.5 flex items-center gap-1 text-[11px] text-white/80"><span className="size-1.5 rounded-full bg-green-400" /> Trực tuyến</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={resetChat} className="flex size-8 items-center justify-center rounded-lg bg-white/10 transition hover:bg-white/20 active:scale-95" aria-label="Làm mới hội thoại" title="Làm mới">
            <RefreshCw className="size-4" />
          </button>
          <button type="button" onClick={() => setIsOpen(false)} className="flex size-8 items-center justify-center rounded-lg bg-white/10 transition hover:bg-white/20 active:scale-95" aria-label="Đóng chatbot" title="Đóng">
            <X className="size-5" />
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        <div className="flex flex-col items-center gap-3 py-6 text-center">
          <SafeImage src="/images/chatbot/chat-bot.png" alt="Trợ lý AI ĐMX" className="size-20 rounded-full border border-[#f5f8fd]" fallbackLabel="AI" />
          <p className="text-sm font-medium leading-[21px] text-[#333]">
            Chào anh/chị, em là <strong className="font-semibold text-[#2a83e9]">Trợ lý AI ĐMX</strong><br />
            Em trả lời thắc mắc và giúp anh/chị lựa chọn sản phẩm phù hợp
          </p>
        </div>

        <p className="text-center text-xs text-[#515764]">Hôm nay, {openedAt}</p>
        <div className="mt-3 flex items-end gap-1.5">
          <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
          <div className="max-w-[88%] rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4 py-3 text-sm leading-[1.4] text-[#333]">
            Dạ em có thể giúp gì ạ.
          </div>
        </div>

        <div className="mt-2 space-y-2" aria-live="polite">
          {messages.map((message) => (
            <div key={message.id} className={`flex items-end gap-1.5 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              {message.role === "assistant" ? <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" /> : null}
              <div className={`max-w-[84%] ${message.role === "user" ? "text-right" : "text-left"}`}>
                <div className={`rounded-[20px] px-4 py-3 text-sm leading-[1.45] ${message.role === "user" ? "rounded-ee-none bg-[#2a83e9] text-white" : "rounded-ss-none bg-[#f2f5f9] text-[#333]"}`}>
                  {message.text}
                </div>
                <p className="mt-1 px-1 text-[10px] text-slate-400">{message.time}</p>
                {message.role === "assistant" ? (
                  <div className="mt-1 flex justify-end gap-1 text-slate-400">
                    <button type="button" onClick={() => showToast({ variant: "success", title: "Cảm ơn phản hồi", description: "Phản hồi này giúp cải thiện trợ lý." })} className="rounded p-1 hover:bg-slate-100 hover:text-[#2a83e9]" aria-label="Phản hồi hữu ích"><ThumbsUp className="size-4" /></button>
                    <button type="button" onClick={() => showToast({ variant: "info", title: "Đã ghi nhận", description: "Trợ lý sẽ điều chỉnh câu trả lời phù hợp hơn." })} className="rounded p-1 hover:bg-slate-100 hover:text-rose-500" aria-label="Phản hồi chưa hữu ích"><ThumbsDown className="size-4" /></button>
                  </div>
                ) : null}
              </div>
            </div>
          ))}

          {isSending ? (
            <div className="flex items-end gap-1.5">
              <SafeImage src="/images/chatbot/mascot.png" alt="" className="size-9 shrink-0 rounded-full" fallbackLabel="AI" />
              <div className="flex h-10 items-center gap-1 rounded-[20px] rounded-ss-none bg-[#f2f5f9] px-4" aria-label="Trợ lý đang trả lời">
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

      <footer className="shrink-0 bg-white px-2 pb-1 pt-2">
        <form onSubmit={submitMessage} className="flex min-h-[51px] items-center rounded-[20px] border border-transparent bg-[#f2f5f9] px-1 focus-within:border-[#2a83e9]" noValidate>
          <button type="button" onClick={() => showToast({ variant: "info", title: "Nhập bằng giọng nói", description: "Trình duyệt demo chưa cấp quyền microphone. Bạn hãy nhập nội dung bằng bàn phím." })} className="flex size-8 shrink-0 items-center justify-center rounded-full text-[#9da7bc] hover:bg-white hover:text-[#2a83e9]" aria-label="Nhập bằng giọng nói">
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
            className="h-9 min-w-0 flex-1 resize-none bg-transparent px-3 py-[9px] text-[15px] leading-[18px] outline-none placeholder:text-[#9da7bc]"
            aria-label="Tin nhắn"
          />
          <button type="submit" disabled={!input.trim() || isSending} className="flex size-8 shrink-0 items-center justify-center rounded-full text-white transition enabled:bg-[#2a83e9] enabled:hover:bg-[#176fc9] disabled:text-[#9da7bc]" aria-label="Gửi tin nhắn">
            <Send className="size-[22px]" />
          </button>
        </form>
        <p className="mt-1 text-center text-[8.5px] leading-[13px] text-[#9ca3af]">Giá, tồn kho và khuyến mãi có thể thay đổi, cần xác nhận lại trước khi mua</p>
        <p className="text-center text-[8.5px] leading-[13px] text-[#9ca3af]">Thông tin chỉ mang tính tham khảo, được tư vấn bởi Trí Tuệ Nhân Tạo</p>
        <div className="scrollbar-none mt-1 flex gap-2 overflow-x-auto pb-1 sm:hidden">
          <Link href="/flashsale" onClick={() => setIsOpen(false)} className="shrink-0 rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-semibold text-[#0754ad]">Flash Sale</Link>
          <Link href="/tien-ich/tra-cuu-bao-hanh" onClick={() => setIsOpen(false)} className="shrink-0 rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-semibold text-[#0754ad]">Tra bảo hành</Link>
          <Link href="/tien-ich/tim-cua-hang" onClick={() => setIsOpen(false)} className="shrink-0 rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-semibold text-[#0754ad]">Tìm cửa hàng</Link>
        </div>
      </footer>
    </section>
  );
}
