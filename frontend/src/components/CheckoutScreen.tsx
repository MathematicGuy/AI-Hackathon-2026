"use client";

import { CheckCircle2, MapPin, PackageCheck, Truck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useCart } from "@/components/CartProvider";
import { DemoNotice } from "@/components/DemoNotice";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import { getProductBySlug } from "@/lib/catalog";
import { formatMoney } from "@/lib/format";

interface CheckoutFields {
  name: string;
  phone: string;
  city: string;
  district: string;
  address: string;
  note: string;
}

type CheckoutErrors = Partial<Record<keyof CheckoutFields, string>>;

const initialFields: CheckoutFields = {
  name: "",
  phone: "",
  city: "",
  district: "",
  address: "",
  note: "",
};

export function CheckoutScreen() {
  const { items, isHydrated, clearCart } = useCart();
  const { showToast } = useToast();
  const [fields, setFields] = useState(initialFields);
  const [errors, setErrors] = useState<CheckoutErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderCode, setOrderCode] = useState("");

  const detailedItems = items.flatMap((line) => {
    const product = getProductBySlug(line.productId);
    return product ? [{ line, product }] : [];
  });
  const total = detailedItems.reduce(
    (sum, item) => sum + item.product.price * item.line.quantity,
    0,
  );

  const updateField = (name: keyof CheckoutFields, value: string) => {
    setFields((current) => ({ ...current, [name]: value }));
    if (errors[name]) {
      setErrors((current) => ({ ...current, [name]: undefined }));
    }
  };

  const validate = () => {
    const nextErrors: CheckoutErrors = {};
    if (fields.name.trim().length < 2) nextErrors.name = "Vui lòng nhập họ tên đầy đủ.";
    if (!/^0[35789]\d{8}$/.test(fields.phone)) nextErrors.phone = "Số điện thoại chưa đúng định dạng.";
    if (!fields.city) nextErrors.city = "Vui lòng chọn tỉnh/thành phố.";
    if (!fields.district) nextErrors.district = "Vui lòng chọn quận/huyện.";
    if (fields.address.trim().length < 5) nextErrors.address = "Vui lòng nhập địa chỉ nhận hàng rõ ràng.";
    return nextErrors;
  };

  const submitOrder = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validate();

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      showToast({
        variant: "error",
        title: "Thông tin giao hàng chưa đầy đủ",
        description: "Kiểm tra các trường được đánh dấu và thử lại.",
      });
      return;
    }

    setIsSubmitting(true);
    window.setTimeout(() => {
      setOrderCode(`DMX${fields.phone.slice(-4)}2026`);
      setIsSubmitting(false);
      clearCart();
      showToast({
        variant: "success",
        title: "Đặt hàng thành công",
        description: "Đơn hàng đã được tạo trong phiên hiện tại.",
      });
    }, 800);
  };

  if (!isHydrated) {
    return <div className="mx-auto h-[520px] max-w-[1000px] animate-pulse rounded-xl bg-white shadow-sm" />;
  }

  if (orderCode) {
    return (
      <section className="mx-auto max-w-[720px] rounded-xl bg-white p-6 text-center shadow-sm md:p-10">
        <CheckCircle2 className="mx-auto size-20 text-emerald-500" />
        <h1 className="mt-4 text-2xl font-bold text-slate-900">Đặt hàng thành công</h1>
        <p className="mt-2 text-sm text-slate-500">Mã đơn hàng của bạn</p>
        <p className="mt-2 text-xl font-bold text-brand-blue">{orderCode}</p>
        <div className="mt-6 grid gap-3 text-left sm:grid-cols-2">
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-xs uppercase text-slate-400">Người nhận</p>
            <p className="mt-1 font-semibold text-slate-800">{fields.name} - {fields.phone}</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-xs uppercase text-slate-400">Giao hàng</p>
            <p className="mt-1 font-semibold text-slate-800">Dự kiến trong 2-4 ngày</p>
          </div>
        </div>
        <Link
          href="/"
          className="mt-7 inline-flex h-11 items-center justify-center rounded-lg bg-brand-blue px-6 text-sm font-bold text-white transition hover:bg-[#1978c4] active:translate-y-px"
        >
          Tiếp tục mua sắm
        </Link>
      </section>
    );
  }

  if (!detailedItems.length) {
    return (
      <section className="mx-auto max-w-[720px] rounded-xl bg-white p-8 text-center shadow-sm">
        <PackageCheck className="mx-auto size-16 text-slate-300" />
        <h1 className="mt-4 text-2xl font-bold text-slate-900">Chưa có sản phẩm để thanh toán</h1>
        <p className="mt-2 text-sm text-slate-500">Hãy thêm ít nhất một sản phẩm vào giỏ hàng trước khi tiếp tục.</p>
        <Link href="/" className="mt-6 inline-flex h-11 items-center justify-center rounded-lg bg-brand-blue px-6 text-sm font-bold text-white hover:bg-[#1978c4]">
          Chọn sản phẩm
        </Link>
      </section>
    );
  }

  const fieldClass = (name: keyof CheckoutFields) =>
    `mt-1 h-11 w-full rounded-lg border bg-white px-3 text-sm outline-none transition focus:border-brand-blue disabled:cursor-not-allowed disabled:bg-slate-100 ${
      errors[name] ? "border-rose-500" : "border-slate-200 hover:border-sky-300"
    }`;

  return (
    <form onSubmit={submitOrder} className="mx-auto grid max-w-[1000px] gap-4 lg:grid-cols-[1fr_380px]" noValidate>
      <section className="rounded-xl bg-white p-4 shadow-sm md:p-6">
        <DemoNotice>
          đơn hàng chỉ được tạo trên trình duyệt để minh hoạ luồng đặt hàng,
          không có đơn nào được gửi tới hệ thống bán hàng.
        </DemoNotice>
        <div className="flex items-center gap-2 border-b border-slate-200 pb-4">
          <MapPin className="size-6 text-brand-blue" />
          <h1 className="text-xl font-bold text-slate-900">Thông tin nhận hàng</h1>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Họ và tên <span className="text-rose-600">*</span>
            <input
              name="name"
              autoComplete="name"
              value={fields.name}
              onChange={(event) => updateField("name", event.target.value)}
              className={fieldClass("name")}
              placeholder="Nguyễn Văn An"
              aria-invalid={Boolean(errors.name)}
            />
            {errors.name ? <span className="mt-1 block text-xs text-rose-600">{errors.name}</span> : null}
          </label>
          <label className="text-sm font-medium text-slate-700">
            Số điện thoại <span className="text-rose-600">*</span>
            <input
              name="phone"
              type="tel"
              inputMode="numeric"
              autoComplete="tel"
              value={fields.phone}
              onChange={(event) => updateField("phone", event.target.value.replace(/[^0-9]/g, "").slice(0, 10))}
              className={fieldClass("phone")}
              placeholder="0901234567"
              aria-invalid={Boolean(errors.phone)}
            />
            {errors.phone ? <span className="mt-1 block text-xs text-rose-600">{errors.phone}</span> : null}
          </label>
          <label className="text-sm font-medium text-slate-700">
            Tỉnh/Thành phố <span className="text-rose-600">*</span>
            <select
              name="city"
              value={fields.city}
              onChange={(event) => updateField("city", event.target.value)}
              className={fieldClass("city")}
              aria-invalid={Boolean(errors.city)}
            >
              <option value="">Chọn tỉnh/thành phố</option>
              <option>Hồ Chí Minh</option>
              <option>Hà Nội</option>
              <option>Đà Nẵng</option>
              <option>Cần Thơ</option>
            </select>
            {errors.city ? <span className="mt-1 block text-xs text-rose-600">{errors.city}</span> : null}
          </label>
          <label className="text-sm font-medium text-slate-700">
            Quận/Huyện <span className="text-rose-600">*</span>
            <select
              name="district"
              value={fields.district}
              onChange={(event) => updateField("district", event.target.value)}
              className={fieldClass("district")}
              aria-invalid={Boolean(errors.district)}
            >
              <option value="">Chọn quận/huyện</option>
              <option>Quận 1</option>
              <option>Quận 3</option>
              <option>Thành phố Thủ Đức</option>
              <option>Quận/Huyện khác</option>
            </select>
            {errors.district ? <span className="mt-1 block text-xs text-rose-600">{errors.district}</span> : null}
          </label>
        </div>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Địa chỉ nhận hàng <span className="text-rose-600">*</span>
          <input
            name="address"
            autoComplete="street-address"
            value={fields.address}
            onChange={(event) => updateField("address", event.target.value)}
            className={fieldClass("address")}
            placeholder="Số nhà, tên đường, phường/xã"
            aria-invalid={Boolean(errors.address)}
          />
          {errors.address ? <span className="mt-1 block text-xs text-rose-600">{errors.address}</span> : null}
        </label>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Ghi chú giao hàng
          <textarea
            name="note"
            value={fields.note}
            onChange={(event) => updateField("note", event.target.value)}
            className="mt-1 min-h-24 w-full resize-y rounded-lg border border-slate-200 bg-white p-3 text-sm outline-none transition hover:border-sky-300 focus:border-brand-blue"
            placeholder="Ví dụ: gọi trước khi giao"
          />
        </label>

        <div className="mt-5 flex items-center gap-3 rounded-lg bg-sky-50 p-4 text-sm text-slate-700">
          <Truck className="size-6 shrink-0 text-brand-blue" />
          <span>Miễn phí giao hàng và hỗ trợ lắp đặt theo chính sách từng sản phẩm.</span>
        </div>
      </section>

      <aside className="h-fit rounded-xl bg-white p-4 shadow-sm md:p-5">
        <h2 className="text-lg font-bold text-slate-900">Đơn hàng ({detailedItems.length} sản phẩm)</h2>
        <div className="mt-4 max-h-[300px] space-y-3 overflow-y-auto">
          {detailedItems.map(({ line, product }) => (
            <div key={product.id} className="grid grid-cols-[64px_1fr] gap-3 border-b border-slate-100 pb-3">
              <SafeImage
                src={product.src}
                alt={product.name}
                className="aspect-square w-full rounded-md border border-slate-100 object-contain p-1"
                fallbackLabel={product.name}
              />
              <div className="min-w-0">
                <p className="line-clamp-2 text-xs font-semibold leading-5 text-slate-800">{product.name}</p>
                <div className="mt-1 flex items-center justify-between gap-2 text-xs">
                  <span className="text-slate-500">Số lượng: {line.quantity}</span>
                  <strong className="text-[#d70018]">{formatMoney(product.price * line.quantity)}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 space-y-2 border-t border-slate-200 pt-4 text-sm">
          <div className="flex justify-between"><span className="text-slate-500">Tạm tính</span><span>{formatMoney(total)}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">Phí giao hàng</span><span className="font-semibold text-emerald-600">Miễn phí</span></div>
          <div className="flex justify-between border-t border-slate-100 pt-3 text-base font-bold"><span>Tổng cộng</span><strong className="text-xl text-[#d70018]">{formatMoney(total)}</strong></div>
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-5 h-12 w-full rounded-lg bg-[#f57c00] text-base font-bold text-white transition hover:bg-[#df6f00] active:translate-y-px disabled:cursor-wait disabled:bg-slate-300"
        >
          {isSubmitting ? "ĐANG XỬ LÝ..." : "ĐẶT HÀNG"}
        </button>
        <p className="mt-3 text-center text-[11px] leading-4 text-slate-400">Đây là luồng thanh toán demo, không phát sinh giao dịch thật.</p>
      </aside>
    </form>
  );
}
