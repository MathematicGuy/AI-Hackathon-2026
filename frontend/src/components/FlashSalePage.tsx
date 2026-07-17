"use client";

import { ChevronDown, Gift, Phone, Trophy, X } from "lucide-react";
import { startTransition, useDeferredValue, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { SafeImage } from "@/components/SafeImage";
import { StateCard } from "@/components/StateCard";
import { useToast } from "@/components/ToastProvider";
import { getProductCategorySlug } from "@/lib/catalog";
import type { ProductItem } from "@/types/home";

interface FlashSalePageProps {
  products: ProductItem[];
}

type SaleTab = "all" | "cooling" | "electronics" | "home" | "water" | "kitchen" | "beauty" | "utility";
type SortMode = "featured" | "discount" | "price";

const saleTabs: Array<{ id: SaleTab; label: string }> = [
  { id: "all", label: "Flashsale" },
  { id: "cooling", label: "Điện lạnh" },
  { id: "electronics", label: "Điện tử" },
  { id: "home", label: "Gia dụng" },
  { id: "water", label: "Máy lọc nước" },
  { id: "kitchen", label: "Việc Bếp Dễ Dàng" },
  { id: "beauty", label: "Sức khoẻ - Làm đẹp" },
  { id: "utility", label: "Hàng tiện ích - Giá thật thích" },
];

const sortModes: Array<{ id: SortMode; label: string }> = [
  { id: "featured", label: "Nổi bật" },
  { id: "discount", label: "% giảm nhiều" },
  { id: "price", label: "Giá thấp đến cao" },
];

const tabCategories: Record<Exclude<SaleTab, "all">, string[]> = {
  cooling: ["may-lanh", "tu-lanh", "quat-dieu-hoa", "may-giat", "may-say-quan-ao", "tu-dong"],
  electronics: ["tivi"],
  home: ["gia-dung", "noi-com-dien", "quat", "robot-hut-bui"],
  water: ["may-loc-nuoc"],
  kitchen: ["gia-dung", "noi-com-dien"],
  beauty: ["cham-soc-ca-nhan"],
  utility: ["robot-hut-bui", "quat", "may-say-quan-ao", "tu-dong"],
};

function discountValue(product: ProductItem) {
  if (!product.originalPrice || product.originalPrice <= product.price) {
    return 0;
  }
  return (product.originalPrice - product.price) / product.originalPrice;
}

export function FlashSalePage({ products }: FlashSalePageProps) {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<SaleTab>("all");
  const deferredTab = useDeferredValue(activeTab);
  const [sortMode, setSortMode] = useState<SortMode>("featured");
  const [visibleCount, setVisibleCount] = useState(10);
  const [isRulesOpen, setIsRulesOpen] = useState(false);
  const [isGameOpen, setIsGameOpen] = useState(false);
  const [gameState, setGameState] = useState<"ready" | "spinning" | "result">("ready");

  const tabProducts = deferredTab === "all"
    ? products
    : products.filter((product) => {
        const routeCategory = getProductCategorySlug(product);
        return tabCategories[deferredTab].includes(product.category) || tabCategories[deferredTab].includes(routeCategory);
      });

  const sortedProducts = [...tabProducts].sort((first, second) => {
    if (sortMode === "price") {
      return first.price - second.price;
    }
    if (sortMode === "discount") {
      return discountValue(second) - discountValue(first);
    }
    return products.indexOf(first) - products.indexOf(second);
  });

  const visibleProducts = sortedProducts.slice(0, visibleCount);
  const isFiltering = activeTab !== deferredTab;

  const selectTab = (tab: SaleTab) => {
    setVisibleCount(10);
    startTransition(() => setActiveTab(tab));
  };

  const spinWheel = () => {
    setGameState("spinning");
    window.setTimeout(() => {
      setGameState("result");
      showToast({
        variant: "success",
        title: "Bạn nhận được voucher 100.000đ",
        description: "Mã WORLDCUP100 đã được lưu cho phiên mua sắm này.",
      });
    }, 900);
  };

  return (
    <main className="min-h-screen bg-[#0754ad]">
      <section className="flashsale-campaign-hero relative">
        <div className="absolute inset-x-0 bottom-0 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 bg-black/10 px-3 py-2 text-sm text-white md:text-base">
          <span>Từ 15/07 - 20/07</span>
          <span aria-hidden>|</span>
          <button type="button" onClick={() => setIsRulesOpen(true)} className="font-medium hover:underline">Xem thể lệ</button>
          <span aria-hidden>|</span>
          <a href="tel:1900232461" className="flex items-center gap-1 font-medium hover:underline">
            <Phone className="size-4" /> Tổng đài: 1900 232 461
          </a>
        </div>
      </section>

      <section className="bg-white px-3 py-4 md:px-4">
        <div className="mx-auto max-w-[1200px]">
          <button
            type="button"
            onClick={() => {
              setGameState("ready");
              setIsGameOpen(true);
            }}
            className="block w-full overflow-hidden rounded-[24px] transition hover:brightness-105 active:scale-[0.998]"
            aria-label="Chơi sút vòng quay"
          >
            <SafeImage
              src="/images/flashsale/game-banner.png"
              alt="Sút vòng quay - Rinh ngay quà đỉnh"
              className="w-full object-contain"
              fallbackLabel="Sút vòng quay"
            />
          </button>
          <SafeImage
            src="/images/flashsale/wheel-banner.gif"
            alt="Quà tặng lễ hội World Cup"
            className="mt-4 h-auto w-full rounded-xl object-cover"
            fallbackLabel="Quà tặng lễ hội World Cup"
          />
        </div>
      </section>

      <section className="sticky top-[97px] z-30 border-y border-white/15 bg-[#064795]/95 shadow-md backdrop-blur md:top-[101px]">
        <div className="scrollbar-none mx-auto flex max-w-[1200px] gap-2 overflow-x-auto px-3 py-3 md:px-4">
          {saleTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => selectTab(tab.id)}
              className={`shrink-0 rounded-full border px-4 py-2 text-sm font-bold transition active:translate-y-px ${
                activeTab === tab.id
                  ? "border-[#ffe500] bg-[#ffe500] text-[#073c80] shadow"
                  : "border-white/30 bg-white/10 text-white hover:bg-white/20"
              }`}
              aria-pressed={activeTab === tab.id}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </section>

      <section className="px-3 pb-12 pt-5 md:px-4 md:pt-8">
        <div className="mx-auto max-w-[1200px] overflow-hidden rounded-[26px] bg-[#279bea] pb-5 shadow-2xl">
          <SafeImage
            src="/images/flashsale/deal-title.png"
            alt="Flash Sale"
            className="h-auto w-full object-contain"
            fallbackLabel="Flash Sale"
          />

          <div className="px-3 md:px-5">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[#126ec1] p-3 text-white">
              <div className="scrollbar-none flex gap-2 overflow-x-auto">
                {sortModes.map((mode) => (
                  <button
                    key={mode.id}
                    type="button"
                    onClick={() => startTransition(() => setSortMode(mode.id))}
                    className={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition ${
                      sortMode === mode.id
                        ? "bg-white text-[#0754ad] shadow"
                        : "bg-white/10 text-white hover:bg-white/20"
                    }`}
                    aria-pressed={sortMode === mode.id}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>
              <span className="text-sm font-medium">{sortedProducts.length} sản phẩm</span>
            </div>

            {isFiltering ? (
              <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5" aria-label="Đang lọc sản phẩm">
                {[0, 1, 2, 3, 4].map((item) => (
                  <div key={item} className="h-[390px] animate-pulse rounded-xl bg-white/80" />
                ))}
              </div>
            ) : visibleProducts.length ? (
              <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
                {visibleProducts.map((product) => (
                  <ProductCard key={product.id} product={product} showRemaining />
                ))}
              </div>
            ) : (
              <div className="mt-4 rounded-xl bg-white p-4">
                <StateCard
                  title="Chưa có sản phẩm trong nhóm này"
                  description="Ưu đãi Sức khoẻ - Làm đẹp đang được cập nhật. Hãy chọn nhóm khác để tiếp tục."
                  actionLabel="Xem toàn bộ Flash Sale"
                  onAction={() => selectTab("all")}
                />
              </div>
            )}

            {visibleProducts.length < sortedProducts.length ? (
              <button
                type="button"
                onClick={() => {
                  setVisibleCount((count) => count + 10);
                  showToast({ variant: "success", title: "Đã tải thêm sản phẩm", description: "Các ưu đãi mới đã được hiển thị." });
                }}
                className="mx-auto mt-5 flex h-11 items-center gap-2 rounded-full bg-white px-6 text-sm font-bold text-[#0754ad] shadow transition hover:bg-[#fff7c7] active:translate-y-px"
              >
                Xem thêm sản phẩm <ChevronDown className="size-4" />
              </button>
            ) : null}
          </div>
        </div>
      </section>

      {isRulesOpen ? (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 px-4 py-8">
          <section role="dialog" aria-modal="true" aria-labelledby="flashsale-rules-title" className="max-h-full w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-5 shadow-2xl md:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-bold text-[#d70018]">LỄ HỘI WORLDCUP</p>
                <h2 id="flashsale-rules-title" className="mt-1 text-2xl font-bold text-slate-900">Thể lệ chương trình Flash Sale</h2>
              </div>
              <button type="button" onClick={() => setIsRulesOpen(false)} className="flex size-10 shrink-0 items-center justify-center rounded-full bg-slate-100 hover:bg-slate-200" aria-label="Đóng thể lệ">
                <X className="size-5" />
              </button>
            </div>
            <div className="mt-5 space-y-4 text-sm leading-6 text-slate-700 md:text-base">
              <p><strong>Thời gian:</strong> Từ ngày 15/07 đến hết ngày 20/07/2026.</p>
              <p><strong>Phạm vi:</strong> Áp dụng khi đặt hàng online tại Điện máy XANH trên các sản phẩm có nhãn Flash Sale.</p>
              <p><strong>Số lượng:</strong> Mỗi khách hàng được mua tối đa 2 sản phẩm cùng loại trong chương trình. Ưu đãi có thể kết thúc sớm khi hết suất.</p>
              <p><strong>Lưu ý:</strong> Giá và quà tặng được xác nhận tại bước thanh toán; dữ liệu trên bản clone chỉ phục vụ trình diễn.</p>
            </div>
            <button type="button" onClick={() => setIsRulesOpen(false)} className="mt-6 h-11 w-full rounded-md bg-[#2a83e9] font-bold text-white hover:bg-[#176fc9]">Tôi đã hiểu</button>
          </section>
        </div>
      ) : null}

      {isGameOpen ? (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/65 px-4 py-8">
          <section role="dialog" aria-modal="true" aria-labelledby="flashsale-game-title" className="w-full max-w-md overflow-hidden rounded-2xl bg-white text-center shadow-2xl">
            <div className="bg-[linear-gradient(135deg,#0649a7,#1689ed)] p-6 text-white">
              <button type="button" onClick={() => setIsGameOpen(false)} className="ml-auto flex size-9 items-center justify-center rounded-full bg-white/15 hover:bg-white/25" aria-label="Đóng trò chơi"><X className="size-5" /></button>
              {gameState === "result" ? <Trophy className="mx-auto mt-1 size-20 text-[#ffe500]" /> : <Gift className={`mx-auto mt-1 size-20 text-[#ffe500] ${gameState === "spinning" ? "animate-bounce" : ""}`} />}
              <h2 id="flashsale-game-title" className="mt-4 text-2xl font-black">{gameState === "result" ? "SÚT THÀNH CÔNG!" : "SÚT VÒNG QUAY"}</h2>
              <p className="mt-2 text-sm text-white/80">Cơ hội nhận voucher mua hàng đến 1.000.000đ</p>
            </div>
            <div className="p-6">
              {gameState === "result" ? (
                <>
                  <p className="text-sm text-slate-500">Phần quà của bạn</p>
                  <p className="mt-2 text-2xl font-black text-[#d70018]">VOUCHER 100.000đ</p>
                  <p className="mt-2 rounded-lg bg-slate-100 px-3 py-2 font-mono font-bold text-[#0754ad]">WORLDCUP100</p>
                  <button type="button" onClick={() => setIsGameOpen(false)} className="mt-5 h-11 w-full rounded-full bg-[#2a83e9] font-bold text-white hover:bg-[#176fc9]">Tiếp tục mua sắm</button>
                </>
              ) : (
                <button type="button" disabled={gameState === "spinning"} onClick={spinWheel} className="h-12 w-full rounded-full bg-[#d70018] font-black text-white shadow-lg transition hover:bg-[#b80014] active:translate-y-px disabled:cursor-wait">
                  {gameState === "spinning" ? "ĐANG SÚT..." : "CHƠI NGAY"}
                </button>
              )}
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
