"use client";

import { SlidersHorizontal } from "lucide-react";
import { startTransition, useDeferredValue, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { StateCard } from "@/components/StateCard";
import { useToast } from "@/components/ToastProvider";
import type { ProductItem } from "@/types/home";

type PriceFilter = "all" | "under-7" | "from-7";
type SortMode = "featured" | "price-asc" | "price-desc";

interface CategoryProductBrowserProps {
  products: ProductItem[];
}

const priceOptions: Array<{ id: PriceFilter; label: string }> = [
  { id: "all", label: "Tất cả mức giá" },
  { id: "under-7", label: "Dưới 7 triệu" },
  { id: "from-7", label: "Từ 7 triệu" },
];

export function CategoryProductBrowser({ products }: CategoryProductBrowserProps) {
  const { showToast } = useToast();
  const [priceFilter, setPriceFilter] = useState<PriceFilter>("all");
  const [sortMode, setSortMode] = useState<SortMode>("featured");
  const deferredPriceFilter = useDeferredValue(priceFilter);

  const filteredProducts = products.filter((product) => {
    if (deferredPriceFilter === "under-7") {
      return product.price < 7_000_000;
    }
    if (deferredPriceFilter === "from-7") {
      return product.price >= 7_000_000;
    }
    return true;
  });

  const sortedProducts = [...filteredProducts].sort((first, second) => {
    if (sortMode === "price-asc") {
      return first.price - second.price;
    }
    if (sortMode === "price-desc") {
      return second.price - first.price;
    }
    return 0;
  });

  const resetFilters = () => {
    startTransition(() => {
      setPriceFilter("all");
      setSortMode("featured");
    });
    showToast({
      variant: "info",
      title: "Đã đặt lại bộ lọc",
      description: "Toàn bộ sản phẩm trong ngành hàng đang được hiển thị.",
    });
  };

  return (
    <section className="mt-4 rounded-xl bg-white p-3 shadow-sm md:p-4">
      <div className="flex flex-col gap-3 border-b border-slate-100 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="size-5 text-brand-blue" />
            <h2 className="text-lg font-bold text-slate-900">
              {sortedProducts.length} sản phẩm
            </h2>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span>Sắp xếp</span>
            <select
              value={sortMode}
              onChange={(event) => setSortMode(event.target.value as SortMode)}
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium outline-none transition hover:border-sky-300 focus:border-brand-blue disabled:cursor-not-allowed disabled:bg-slate-100"
            >
              <option value="featured">Nổi bật</option>
              <option value="price-asc">Giá thấp đến cao</option>
              <option value="price-desc">Giá cao đến thấp</option>
            </select>
          </label>
        </div>

        <div className="scrollbar-none flex gap-2 overflow-x-auto pb-1">
          {priceOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => startTransition(() => setPriceFilter(option.id))}
              className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition active:translate-y-px ${
                priceFilter === option.id
                  ? "border-brand-blue bg-brand-blue text-white"
                  : "border-slate-200 bg-white text-slate-700 hover:border-sky-300 hover:bg-sky-50"
              }`}
              aria-pressed={priceFilter === option.id}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {sortedProducts.length ? (
        <div className="grid grid-cols-2 gap-2.5 pt-4 sm:grid-cols-3 lg:grid-cols-5">
          {sortedProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className="pt-4">
          <StateCard
            title="Không có sản phẩm phù hợp"
            description="Mức giá đang chọn chưa có sản phẩm phù hợp. Hãy đặt lại bộ lọc để xem toàn bộ danh sách."
            actionLabel="Đặt lại bộ lọc"
            onAction={resetFilters}
          />
        </div>
      )}
    </section>
  );
}
