"use client";

import {
  Check,
  ChevronRight,
  CreditCard,
  MapPin,
  ShieldCheck,
  ShoppingCart,
  Truck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useCart } from "@/components/CartProvider";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import { formatMoney } from "@/lib/format";
import type { ProductItem } from "@/types/home";

interface ProductDetailClientProps {
  product: ProductItem;
}

type PackageId = "standard" | "protected" | "delivery";

export function ProductDetailClient({ product }: ProductDetailClientProps) {
  const router = useRouter();
  const { addItem } = useCart();
  const { showToast } = useToast();
  const [selectedView, setSelectedView] = useState(0);
  const [selectedPackage, setSelectedPackage] = useState<PackageId>("delivery");

  const packages = [
    {
      id: "standard" as const,
      label: "Gói tiêu chuẩn",
      price: product.price + 1_000_000,
      features: ["Miễn phí công lắp đặt", "Vật tư cơ bản", "Hút chân không"],
    },
    {
      id: "protected" as const,
      label: "Gói an tâm sử dụng",
      price: product.price + 1_225_000,
      features: ["Bảo hành 1 đổi 1", "Miễn phí lắp đặt", "Hỗ trợ tận nhà"],
    },
    {
      id: "delivery" as const,
      label: "Gói chỉ giao hàng",
      price: product.price,
      features: ["Giao hàng tận nơi", "Kiểm tra sản phẩm", "Giữ nguyên giá online"],
    },
  ];
  const activePackage = packages.find((item) => item.id === selectedPackage) || packages[2];

  const addToCart = (goToCart: boolean) => {
    addItem(product.id);
    showToast({
      variant: "success",
      title: "Đã thêm vào giỏ hàng",
      description: `${product.name} đã được thêm với ${activePackage.label.toLocaleLowerCase("vi-VN")}.`,
    });

    if (goToCart) {
      router.push("/gio-hang");
    }
  };

  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(370px,.8fr)]">
      <section className="rounded-xl bg-white p-3 shadow-sm md:p-5">
        <div className="relative flex aspect-[4/3] items-center justify-center overflow-hidden rounded-lg bg-[linear-gradient(145deg,#e7f2ff,#f8fbff)]">
          <span className="absolute left-3 top-3 z-10 rounded-full bg-white px-3 py-1.5 text-xs font-bold text-brand-blue shadow-sm">
            {selectedView === 0 ? "Nổi bật" : selectedView === 1 ? "Thiết kế" : "Lắp đặt"}
          </span>
          <SafeImage
            src={product.src}
            alt={product.name}
            className={`h-full w-full object-contain transition duration-300 ${
              selectedView === 0 ? "p-5" : selectedView === 1 ? "p-10 scale-95" : "p-7 scale-90"
            }`}
            fallbackLabel={product.name}
          />
        </div>

        <div className="scrollbar-none mt-3 flex gap-2 overflow-x-auto">
          {["Nổi bật", "Cận cảnh", "Lắp đặt"].map((label, index) => (
            <button
              key={label}
              type="button"
              onClick={() => setSelectedView(index)}
              className={`shrink-0 rounded-lg border p-2 text-center transition active:translate-y-px ${
                selectedView === index
                  ? "border-brand-blue bg-sky-50 text-brand-blue"
                  : "border-slate-200 text-slate-600 hover:border-sky-300"
              }`}
              aria-pressed={selectedView === index}
            >
              <SafeImage
                src={product.src}
                alt=""
                className="mx-auto size-12 object-contain"
                fallbackLabel={label}
              />
              <span className="mt-1 block text-[11px] font-medium">{label}</span>
            </button>
          ))}
        </div>

        <div className="mt-5 border-t border-slate-100 pt-5">
          <h2 className="text-lg font-bold text-slate-900">Đặc điểm nổi bật</h2>
          <ul className="mt-3 space-y-2.5 text-sm leading-6 text-slate-700">
            {(product.highlights || [product.sub]).map((highlight) => (
              <li key={highlight} className="flex gap-2">
                <Check className="mt-1 size-4 shrink-0 text-emerald-600" />
                <span>{highlight}</span>
              </li>
            ))}
            <li className="flex gap-2">
              <Check className="mt-1 size-4 shrink-0 text-emerald-600" />
              <span>{product.description}</span>
            </li>
          </ul>
        </div>
      </section>

      <aside className="h-fit overflow-hidden rounded-xl bg-white shadow-sm">
        <div className="bg-[linear-gradient(135deg,#ff6a00,#ff3d00)] p-4 text-white">
          <div className="flex items-center justify-between gap-3">
            <p className="font-bold">🔥 Online Giá Rẻ Quá</p>
            <span className="rounded bg-white/20 px-2 py-1 text-xs font-semibold">Còn số lượng giới hạn</span>
          </div>
          <p className="mt-2 text-sm text-white/85">Giá và khuyến mãi tại Hồ Chí Minh</p>
        </div>

        <div className="p-4">
          <h2 className="font-bold text-slate-900">Gói dịch vụ</h2>
          <div className="mt-3 space-y-2">
            {packages.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedPackage(item.id)}
                className={`w-full rounded-lg border p-3 text-left transition active:translate-y-px ${
                  selectedPackage === item.id
                    ? "border-brand-blue bg-sky-50 ring-1 ring-brand-blue/20"
                    : "border-slate-200 hover:border-sky-300"
                }`}
                aria-pressed={selectedPackage === item.id}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-bold text-slate-800">{item.label}</span>
                  <strong className="text-[#d70018]">{formatMoney(item.price)}</strong>
                </div>
                <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-600">
                  {item.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-1.5">
                      <Check className="size-3.5 text-emerald-600" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </button>
            ))}
          </div>

          <div className="mt-4 rounded-lg border border-orange-200 bg-orange-50 p-3">
            <p className="text-sm font-bold text-slate-900">Khuyến mãi</p>
            <ol className="mt-2 space-y-2 text-xs leading-5 text-slate-700">
              <li>1. Đổi mới trong 12 tháng nếu có lỗi kỹ thuật.</li>
              <li>2. Tặng phiếu mua hàng phụ kiện trị giá đến 300.000đ.</li>
              <li>3. Tích điểm Quà Tặng VIP cho đơn hàng hoàn tất.</li>
            </ol>
          </div>

          <button
            type="button"
            className="mt-4 flex w-full items-center gap-2 rounded-lg border border-slate-200 p-3 text-left text-sm transition hover:border-sky-300 hover:bg-sky-50 active:translate-y-px"
            onClick={() =>
              showToast({
                variant: "info",
                title: "Địa chỉ nhận hàng",
                description: "Thời gian giao dự kiến từ 2 đến 4 ngày tùy khu vực.",
              })
            }
          >
            <MapPin className="size-5 text-brand-blue" />
            <span>Chọn địa chỉ nhận hàng để biết thời gian giao</span>
            <ChevronRight className="ml-auto size-4 text-slate-400" />
          </button>

          <div className="mt-4 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => addToCart(false)}
              className="flex min-h-12 items-center justify-center gap-2 rounded-lg border-2 border-brand-blue bg-white px-3 text-sm font-bold text-brand-blue transition hover:bg-sky-50 active:translate-y-px disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
            >
              <ShoppingCart className="size-5" />
              Thêm vào giỏ
            </button>
            <button
              type="button"
              onClick={() => addToCart(true)}
              className="min-h-12 rounded-lg bg-[#f57c00] px-3 text-sm font-bold text-white transition hover:bg-[#df6f00] active:translate-y-px disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              Mua ngay
            </button>
          </div>
          <button
            type="button"
            onClick={() =>
              showToast({
                variant: "success",
                title: "Đã ghi nhận lựa chọn trả chậm",
                description: "Chuyên viên sẽ tư vấn phương án trả chậm 0% phù hợp.",
              })
            }
            className="mt-2 flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-brand-blue px-4 text-sm font-bold text-white transition hover:bg-[#1478c5] active:translate-y-px"
          >
            <CreditCard className="size-5" />
            Mua trả chậm 0%
          </button>

          <div className="mt-4 grid gap-2 text-xs text-slate-600 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            <span className="flex items-center gap-1.5"><Truck className="size-4 text-brand-blue" /> Giao nhanh</span>
            <span className="flex items-center gap-1.5"><ShieldCheck className="size-4 text-emerald-600" /> Chính hãng</span>
            <span className="flex items-center gap-1.5"><Check className="size-4 text-emerald-600" /> Đổi lỗi</span>
          </div>
        </div>
      </aside>
    </div>
  );
}
