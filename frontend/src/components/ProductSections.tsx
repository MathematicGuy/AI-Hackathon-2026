"use client";

import Link from "next/link";
import { startTransition, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { SafeImage } from "@/components/SafeImage";
import { StateCard } from "@/components/StateCard";
import { getCampaignSlug } from "@/lib/catalog";
import type { FlashTab, ProductItem, PromoBanner } from "@/types/home";

interface ProductSectionsProps {
  tabs: FlashTab[];
  products: ProductItem[];
  banners: PromoBanner[];
}

const onlineShockBanner =
  "https://cdnv2.tgdd.vn/mwg-static/common/Campaign/41/f0/41f0a67c2fb9240ca353cbb087a59ff7.png";

export function ProductSections({
  tabs,
  products,
  banners,
}: ProductSectionsProps) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.id ?? "all");
  const visibleProducts =
    activeTab === "all"
      ? products
      : products.filter((product) => product.category === activeTab);

  return (
    <section className="mx-auto max-w-[1200px] px-3 pt-4 md:px-4">
      <Link
        href="/khuyen-mai/online-only"
        className="mb-4 block w-full overflow-hidden rounded-xl bg-white shadow-sm transition hover:shadow-md active:translate-y-px"
      >
        <SafeImage
          src={onlineShockBanner}
          alt="Online siêu sốc"
          className="min-h-20 w-full object-cover"
          fallbackLabel="Online siêu sốc"
        />
      </Link>

      <div className="overflow-hidden rounded-xl bg-white shadow-sm">
        <div className="scrollbar-none flex gap-2 overflow-x-auto border-b border-slate-100 px-3 py-3 md:px-4">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => startTransition(() => setActiveTab(item.id))}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition active:translate-y-px ${
                activeTab === item.id
                  ? "bg-brand-blue text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
              aria-pressed={activeTab === item.id}
            >
              {item.label}
            </button>
          ))}
        </div>

        {visibleProducts.length ? (
          <div className="grid grid-cols-2 gap-2.5 p-3 sm:grid-cols-3 md:p-4 lg:grid-cols-5">
            {visibleProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="p-4">
            <StateCard
              title="Chưa có sản phẩm phù hợp"
              description="Bộ lọc hiện tại chưa có dữ liệu. Hãy chọn tab khác để tiếp tục."
            />
          </div>
        )}
      </div>

      <div className="grid gap-3 pt-4 md:grid-cols-3">
        {banners.map((item) => (
          <Link
            key={item.id}
            href={`/khuyen-mai/${getCampaignSlug(item)}`}
            className="overflow-hidden rounded-xl bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
          >
            <SafeImage
              src={item.src}
              alt={item.title}
              className="aspect-[16/7] w-full object-cover"
              fallbackLabel={item.title}
              loading="lazy"
            />
          </Link>
        ))}
      </div>
    </section>
  );
}
