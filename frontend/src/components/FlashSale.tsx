"use client";

import { startTransition, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { SafeImage } from "@/components/SafeImage";
import { StateCard } from "@/components/StateCard";
import type { FlashTab, ProductItem } from "@/types/home";

interface FlashSaleProps {
  tabs: FlashTab[];
  products: ProductItem[];
}

export function FlashSale({ tabs, products }: FlashSaleProps) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.id ?? "flashsale");
  const visibleProducts =
    activeTab === "flashsale"
      ? products
      : products.filter((product) => product.category === activeTab);

  if (!tabs.length) {
    return null;
  }

  return (
    <section className="mx-auto max-w-[1200px] px-3 pt-4 md:px-4">
      <div className="overflow-hidden rounded-xl bg-[linear-gradient(135deg,#ff6a00,#ef2f20)] p-3 shadow-sm md:p-5">
        <h2 className="mb-3 text-xl font-bold text-white">Khuyến mãi online</h2>

        <div className="scrollbar-none mb-4 flex gap-2 overflow-x-auto">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => startTransition(() => setActiveTab(item.id))}
              className={`shrink-0 overflow-hidden rounded-xl border transition active:translate-y-px ${
                activeTab === item.id
                  ? "border-white bg-white/20"
                  : "border-transparent bg-white/5 hover:bg-white/10"
              }`}
              aria-pressed={activeTab === item.id}
            >
              {item.src ? (
                <SafeImage
                  src={item.src}
                  alt={item.label}
                  className="h-14 w-auto object-contain md:h-16"
                  fallbackLabel={item.label}
                />
              ) : (
                <span className="flex h-14 items-center px-4 text-sm font-semibold text-white md:h-16">
                  {item.label}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="mb-4 flex items-center gap-2 overflow-x-auto pb-1">
          {tabs.map((item) => (
            <button
              key={`${item.id}-pill`}
              type="button"
              onClick={() => startTransition(() => setActiveTab(item.id))}
              className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold transition active:scale-95 ${
                activeTab === item.id
                  ? "bg-white text-[#d92d20]"
                  : "bg-white/15 text-white hover:bg-white/25"
              }`}
              aria-pressed={activeTab === item.id}
            >
              {item.label}
            </button>
          ))}
          <span className="ml-auto hidden shrink-0 rounded-full bg-white px-3 py-1.5 text-sm font-bold text-[#d92d20] sm:inline-flex">
            Ưu đãi hôm nay
          </span>
        </div>

        {visibleProducts.length ? (
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
            {visibleProducts.map((product) => (
              <ProductCard key={product.id} product={product} showRemaining />
            ))}
          </div>
        ) : (
          <StateCard
            title="Chưa có sản phẩm cho bộ lọc này"
            description="Dữ liệu ưu đãi cho nhóm đang chọn chưa sẵn sàng. Hãy đổi sang tab khác."
          />
        )}
      </div>
    </section>
  );
}
