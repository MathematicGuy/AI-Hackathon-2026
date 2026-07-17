"use client";

import { Minus, Plus, ShoppingBasket, Trash2 } from "lucide-react";
import Link from "next/link";
import { useCart } from "@/components/CartProvider";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import { getProductBySlug, getProductSlug } from "@/lib/catalog";
import { formatMoney } from "@/lib/format";

export function CartScreen() {
  const {
    items,
    isHydrated,
    updateQuantity,
    removeItem,
    clearCart,
  } = useCart();
  const { showToast } = useToast();

  if (!isHydrated) {
    return (
      <div className="mx-auto max-w-[760px] animate-pulse rounded-xl bg-white p-5 shadow-sm">
        <div className="h-7 w-40 rounded bg-slate-200" />
        <div className="mt-5 h-36 rounded-xl bg-slate-100" />
        <div className="mt-3 h-36 rounded-xl bg-slate-100" />
        <div className="mt-5 h-12 rounded-lg bg-slate-200" />
      </div>
    );
  }

  const detailedItems = items.flatMap((line) => {
    const product = getProductBySlug(line.productId);
    return product ? [{ line, product }] : [];
  });

  if (!detailedItems.length) {
    return (
      <section className="mx-auto flex min-h-[560px] max-w-[760px] flex-col items-center justify-center px-4 py-12 text-center">
        <div className="relative flex h-52 w-72 items-center justify-center rounded-[48%_52%_42%_58%/50%_45%_55%_50%] bg-[#eaf2ff]">
          <ShoppingBasket className="size-28 text-[#4285e9]" strokeWidth={1.5} />
          <span className="absolute right-12 top-9 size-9 rounded-full bg-white/70" />
          <span className="absolute bottom-10 left-10 size-5 rounded-full bg-brand-yellow" />
        </div>
        <h1 className="mt-5 text-2xl font-bold text-slate-800">Giỏ hàng trống</h1>
        <p className="mt-2 text-base text-slate-400">Không có sản phẩm nào trong giỏ hàng</p>
        <Link
          href="/"
          className="mt-8 flex h-12 w-full max-w-[580px] items-center justify-center rounded-lg bg-brand-blue text-base font-bold text-white transition hover:bg-[#1978c4] active:translate-y-px"
        >
          Về trang chủ
        </Link>
        <p className="mt-3 text-xs text-slate-400">
          Khi cần trợ giúp vui lòng gọi {" "}
          <a href="tel:1900232461" className="text-brand-blue hover:underline">1900 232 461</a>
          {" "}(8:00 - 21:30)
        </p>
      </section>
    );
  }

  const total = detailedItems.reduce(
    (sum, item) => sum + item.product.price * item.line.quantity,
    0,
  );

  return (
    <section className="mx-auto max-w-[760px] overflow-hidden rounded-xl bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-4 md:px-5">
        <h1 className="text-xl font-bold text-slate-900">Giỏ hàng của bạn</h1>
        <button
          type="button"
          onClick={() => {
            clearCart();
            showToast({
              variant: "info",
              title: "Đã xóa giỏ hàng",
              description: "Tất cả sản phẩm đã được gỡ khỏi giỏ hàng.",
            });
          }}
          className="text-sm font-medium text-slate-500 transition hover:text-rose-600 hover:underline active:opacity-70"
        >
          Xóa tất cả
        </button>
      </div>

      <div className="divide-y divide-slate-100">
        {detailedItems.map(({ line, product }) => (
          <div key={product.id} className="grid grid-cols-[90px_1fr] gap-3 p-4 md:grid-cols-[120px_1fr_auto] md:p-5">
            <Link href={`/san-pham/${getProductSlug(product)}`}>
              <SafeImage
                src={product.src}
                alt={product.name}
                className="aspect-square w-full rounded-lg border border-slate-100 object-contain p-1"
                fallbackLabel={product.name}
              />
            </Link>

            <div className="min-w-0">
              <Link
                href={`/san-pham/${getProductSlug(product)}`}
                className="line-clamp-2 text-sm font-semibold leading-5 text-slate-800 hover:text-brand-blue"
              >
                {product.name}
              </Link>
              <p className="mt-1 text-xs text-slate-500">{product.sub}</p>
              <strong className="mt-2 block text-base text-[#d70018]">{formatMoney(product.price)}</strong>
              <button
                type="button"
                onClick={() => {
                  removeItem(product.id);
                  showToast({
                    variant: "info",
                    title: "Đã xóa sản phẩm",
                    description: `${product.name} đã được gỡ khỏi giỏ.`,
                  });
                }}
                className="mt-3 inline-flex items-center gap-1 text-xs text-slate-500 transition hover:text-rose-600 active:opacity-70 md:hidden"
              >
                <Trash2 className="size-4" /> Xóa
              </button>
            </div>

            <div className="col-span-2 flex items-center justify-between md:col-span-1 md:flex-col md:items-end">
              <div className="flex items-center overflow-hidden rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => updateQuantity(product.id, line.quantity - 1)}
                  disabled={line.quantity <= 1}
                  className="flex size-9 items-center justify-center text-slate-600 transition hover:bg-slate-100 active:bg-slate-200 disabled:cursor-not-allowed disabled:text-slate-300"
                  aria-label={`Giảm số lượng ${product.name}`}
                >
                  <Minus className="size-4" />
                </button>
                <span className="flex h-9 min-w-10 items-center justify-center border-x border-slate-200 text-sm font-bold">
                  {line.quantity}
                </span>
                <button
                  type="button"
                  onClick={() => updateQuantity(product.id, line.quantity + 1)}
                  className="flex size-9 items-center justify-center text-slate-600 transition hover:bg-slate-100 active:bg-slate-200 disabled:cursor-not-allowed disabled:text-slate-300"
                  aria-label={`Tăng số lượng ${product.name}`}
                >
                  <Plus className="size-4" />
                </button>
              </div>
              <button
                type="button"
                onClick={() => {
                  removeItem(product.id);
                  showToast({
                    variant: "info",
                    title: "Đã xóa sản phẩm",
                    description: `${product.name} đã được gỡ khỏi giỏ.`,
                  });
                }}
                className="hidden items-center gap-1 text-xs text-slate-500 transition hover:text-rose-600 active:opacity-70 md:inline-flex"
              >
                <Trash2 className="size-4" /> Xóa
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-slate-200 bg-slate-50 p-4 md:p-5">
        <div className="flex items-center justify-between gap-4">
          <span className="font-semibold text-slate-700">Tạm tính</span>
          <strong className="text-xl text-[#d70018]">{formatMoney(total)}</strong>
        </div>
        <p className="mt-2 text-xs leading-5 text-slate-500">
          Phí giao hàng và ưu đãi cuối cùng sẽ được xác nhận tại bước thanh toán.
        </p>
        <Link
          href="/thanh-toan"
          className="mt-4 flex h-12 w-full items-center justify-center rounded-lg bg-[#f57c00] text-base font-bold text-white transition hover:bg-[#df6f00] active:translate-y-px"
        >
          Tiến hành thanh toán
        </Link>
        <Link href="/" className="mt-3 block text-center text-sm font-medium text-brand-blue hover:underline">
          Chọn thêm sản phẩm khác
        </Link>
      </div>
    </section>
  );
}
