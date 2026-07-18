"use client";

import { CheckCircle2, LoaderCircle, RotateCcw, Search } from "lucide-react";
import Link from "next/link";
import { useRef, useState } from "react";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import type { MegaMenuItem } from "@/lib/mega-menu-data";

interface UtilityServiceScreenProps {
  item: MegaMenuItem;
}

const descriptions: Record<string, string> = {
  "buying-advice": "Chọn ngành hàng và nhu cầu sử dụng để nhận gợi ý sản phẩm phù hợp.",
  stores: "Tìm siêu thị Điện máy XANH gần khu vực của bạn.",
  installments: "Ước tính khoản trả hàng tháng và điều kiện mua trả chậm.",
  warranty: "Tra cứu thời hạn bảo hành theo số điện thoại hoặc mã sản phẩm.",
  "clean-ac": "Đăng ký vệ sinh máy lạnh tại nhà với khung giờ phù hợp.",
  "replace-filter": "Đặt lịch kiểm tra và thay lõi máy lọc nước chính hãng.",
  "clean-washer": "Đặt lịch vệ sinh máy giặt cửa trên hoặc cửa trước.",
};

function inputCopy(item: MegaMenuItem) {
  if (item.id === "stores") {
    return { label: "Khu vực cần tìm", placeholder: "Ví dụ: Quận 1, TP. Hồ Chí Minh" };
  }
  if (item.id === "warranty") {
    return { label: "Số điện thoại hoặc mã sản phẩm", placeholder: "Nhập thông tin cần tra cứu" };
  }
  if (["clean-ac", "replace-filter", "clean-washer", "installments", "pay-installment"].includes(item.id)) {
    return { label: "Số điện thoại liên hệ", placeholder: "Ví dụ: 0901234567" };
  }
  return { label: "Nội dung cần hỗ trợ", placeholder: "Mô tả nhu cầu của bạn" };
}

function successMessage(item: MegaMenuItem, value: string) {
  if (item.id === "stores") {
    return `Đã tìm thấy 3 cửa hàng gần “${value}”. Cửa hàng gần nhất mở cửa từ 8:00 đến 21:30.`;
  }
  if (item.id === "warranty") {
    return "Thông tin đã được ghi nhận. Sản phẩm mẫu còn bảo hành đến 17/07/2027.";
  }
  if (["clean-ac", "replace-filter", "clean-washer"].includes(item.id)) {
    return "Yêu cầu đặt lịch đã được tiếp nhận. Nhân viên sẽ gọi xác nhận khung giờ trong vòng 30 phút.";
  }
  return "Thông tin phù hợp đã được tổng hợp. Bạn có thể tiếp tục xem sản phẩm hoặc gửi yêu cầu tư vấn.";
}

export function UtilityServiceScreen({ item }: UtilityServiceScreenProps) {
  const { showToast } = useToast();
  const copy = inputCopy(item);
  const [value, setValue] = useState("");
  const [lastValue, setLastValue] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const failedOnce = useRef(false);

  const requestResult = (query: string) => {
    setIsLoading(true);
    setError("");
    setResult("");
    setLastValue(query);

    window.setTimeout(() => {
      if (query.toLocaleLowerCase("vi-VN").includes("lỗi") && !failedOnce.current) {
        failedOnce.current = true;
        setIsLoading(false);
        setError("Không thể tải thông tin lúc này. Vui lòng thử lại.");
        showToast({ variant: "error", title: "Tra cứu chưa thành công", description: "Kết nối mô phỏng vừa bị gián đoạn." });
        return;
      }
      const message = successMessage(item, query);
      setResult(message);
      setIsLoading(false);
      showToast({ variant: "success", title: "Tra cứu thành công", description: message });
    }, 650);
  };

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = value.trim();
    if (normalized.length < 3) {
      setError("Vui lòng nhập ít nhất 3 ký tự để tiếp tục.");
      return;
    }
    requestResult(normalized);
  };

  return (
    <main className="mx-auto w-full max-w-[1200px] px-3 py-6 md:px-4 md:py-10">
      <div className="grid overflow-hidden rounded-2xl bg-white shadow-sm lg:grid-cols-[360px_1fr]">
        <section className="flex min-h-[360px] flex-col items-center justify-center bg-[linear-gradient(145deg,#eaf4ff,#f8fbff)] p-8 text-center">
          <SafeImage src={item.image} alt={item.label} className="size-28 object-contain" fallbackLabel={item.label} />
          <h1 className="mt-5 text-2xl font-bold text-slate-900">{item.label}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">{descriptions[item.id] || "Dịch vụ tiện ích dành cho khách hàng Điện máy XANH."}</p>
        </section>

        <section className="p-5 md:p-9">
          <p className="text-sm font-bold uppercase tracking-wide text-[#2a83e9]">Thông tin - Dịch vụ tiện ích</p>
          <h2 className="mt-2 text-2xl font-bold text-slate-900">Nhập thông tin để tiếp tục</h2>
          <form onSubmit={submit} className="mt-6" noValidate>
            <label htmlFor="utility-query" className="text-sm font-semibold text-slate-700">{copy.label}</label>
            <div className={`mt-2 flex h-12 items-center rounded-lg border bg-white px-3 transition focus-within:border-[#2a83e9] ${error ? "border-rose-500" : "border-slate-300"}`}>
              <Search className="size-5 shrink-0 text-slate-400" />
              <input id="utility-query" value={value} onChange={(event) => { setValue(event.target.value.slice(0, 120)); setError(""); }} placeholder={copy.placeholder} className="h-full min-w-0 flex-1 border-0 bg-transparent px-3 outline-none" aria-invalid={Boolean(error)} />
            </div>
            {error ? (
              <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-rose-600">
                <span>{error}</span>
                {lastValue ? <button type="button" onClick={() => requestResult(lastValue)} className="inline-flex items-center gap-1 font-semibold hover:underline"><RotateCcw className="size-4" /> Thử lại</button> : null}
              </div>
            ) : null}
            <button type="submit" disabled={isLoading} className="mt-4 flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-[#2a83e9] font-bold text-white transition hover:bg-[#176fc9] active:translate-y-px disabled:cursor-wait">
              {isLoading ? <><LoaderCircle className="size-5 animate-spin" /> Đang xử lý...</> : "Tra cứu ngay"}
            </button>
          </form>

          {result ? (
            <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-800">
              <div className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 size-5 shrink-0" /><p>{result}</p></div>
            </div>
          ) : null}

          <div className="mt-7 flex flex-wrap gap-3 border-t border-slate-100 pt-5">
            <Link href="/flashsale" className="rounded-lg border border-[#2a83e9] px-4 py-2.5 text-sm font-semibold text-[#0754ad] transition hover:bg-blue-50">Xem Flash Sale</Link>
            <Link href="/" className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">Về trang chủ</Link>
          </div>
        </section>
      </div>
    </main>
  );
}
