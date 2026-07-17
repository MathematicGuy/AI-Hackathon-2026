"use client";

import {
  ChevronRight,
  MapPin,
  Menu,
  Search,
  ShoppingCart,
  User,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useSyncExternalStore } from "react";
import { useCart } from "@/components/CartProvider";
import { MegaMenu } from "@/components/MegaMenu";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import { getCategorySlug } from "@/lib/catalog";
import type { CategoryItem } from "@/types/home";
import { DienMayXanhLogo } from "./icons";

interface HeaderProps {
  categories: CategoryItem[];
  showTopBanner?: boolean;
}

const locations = ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Cần Thơ"];

function subscribeToAccount(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener("dmx-account-change", callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener("dmx-account-change", callback);
  };
}

function getAccountPhone() {
  return window.localStorage.getItem("dmx-account-phone") || "";
}

export function Header({ categories, showTopBanner = true }: HeaderProps) {
  const router = useRouter();
  const { itemCount } = useCart();
  const { showToast } = useToast();
  const accountPhone = useSyncExternalStore(subscribeToAccount, getAccountPhone, () => "");
  const [location, setLocation] = useState("Hồ Chí Minh");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchError, setSearchError] = useState("");
  const [isLocationOpen, setIsLocationOpen] = useState(false);
  const [isCategoryOpen, setIsCategoryOpen] = useState(false);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = searchQuery.trim();

    if (normalized.length < 2) {
      const message = normalized
        ? "Từ khóa cần có ít nhất 2 ký tự."
        : "Vui lòng nhập từ khóa cần tìm.";
      setSearchError(message);
      showToast({
        variant: "error",
        title: "Chưa thể tìm kiếm",
        description: message,
      });
      return;
    }

    setSearchError("");
    router.push(`/tim-kiem?q=${encodeURIComponent(normalized)}`);
  };

  const handleLocationChange = (nextLocation: string) => {
    setLocation(nextLocation);
    setIsLocationOpen(false);
    showToast({
      variant: "info",
      title: "Đã cập nhật khu vực",
      description: `Giá và khuyến mãi đang hiển thị theo ${nextLocation}.`,
    });
  };

  return (
    <>
      {showTopBanner ? (
        <Link
          href="/flashsale"
          className="block bg-[#2370fc]"
          aria-label="Xem chương trình cuối tuần"
        >
          <SafeImage
            src="https://cdnv2.tgdd.vn/mwg-static/dmx/Banner/a3/fd/a3fdcb27a6ace833bd969e9eba394ccd.png"
            alt="Chỉ 3 ngày, lễ hội Worldcup online giảm to"
            className="mx-auto h-[44px] w-full max-w-[1920px] object-cover object-center md:h-[55px]"
            loading="eager"
            fallbackLabel="Lễ hội Worldcup - Online giảm to"
          />
        </Link>
      ) : null}

      <header className="sticky top-0 z-40 border-b border-[#2278bd] bg-brand-blue text-white shadow-sm">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-2 px-3 py-2.5 md:flex-nowrap md:px-4">
          <Link href="/" className="shrink-0" aria-label="Về trang chủ">
            <DienMayXanhLogo className="h-9 w-[142px] md:h-11 md:w-[190px]" />
          </Link>

          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => setIsCategoryOpen((current) => !current)}
              className={`relative z-[71] flex h-10 shrink-0 items-center gap-2 rounded-md px-2 text-sm font-semibold transition active:translate-y-px md:px-3 ${
                isCategoryOpen
                  ? "bg-white text-slate-900 shadow-sm"
                  : "hover:bg-white/10"
              }`}
              aria-expanded={isCategoryOpen}
              aria-label={isCategoryOpen ? "Đóng danh mục" : "Mở danh mục sản phẩm"}
            >
              <Menu size={21} />
              <span className="hidden sm:inline">Danh mục</span>
            </button>
            <MegaMenu
              categories={categories}
              isOpen={isCategoryOpen}
              onClose={() => setIsCategoryOpen(false)}
            />
          </div>

          <form
            onSubmit={handleSubmit}
            className="order-2 w-full md:order-none md:min-w-0 md:flex-1"
            noValidate
          >
            <div className="flex h-10 items-center overflow-hidden rounded-full bg-white shadow-inner focus-within:ring-2 focus-within:ring-brand-yellow">
              <button
                type="submit"
                className="flex h-full w-11 shrink-0 items-center justify-center text-slate-400 transition hover:bg-slate-50 active:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Tìm kiếm"
              >
                <Search size={18} />
              </button>
              <input
                id="site-search"
                name="q"
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  if (searchError) {
                    setSearchError("");
                  }
                }}
                placeholder="Bạn tìm gì..."
                className="h-full min-w-0 flex-1 border-0 bg-transparent pr-4 text-sm text-slate-700 outline-none placeholder:text-slate-400"
                aria-invalid={Boolean(searchError)}
                aria-describedby={searchError ? "site-search-error" : undefined}
              />
            </div>
            {searchError ? (
              <p id="site-search-error" className="mt-1 px-3 text-xs text-rose-100">
                {searchError}
              </p>
            ) : null}
          </form>

          <Link
            href="/lich-su-mua-hang"
            className="flex h-10 shrink-0 items-center gap-2 rounded-md px-2 text-sm font-medium transition hover:bg-white/10 active:translate-y-px md:px-3"
            aria-label={accountPhone ? "Mở đơn hàng đã mua" : "Đăng nhập"}
          >
            <User size={22} />
            <span className="hidden lg:inline">{accountPhone ? "B." : "Đăng nhập"}</span>
          </Link>

          <Link
            href="/gio-hang"
            className="relative flex h-10 shrink-0 items-center gap-2 rounded-md px-2 text-sm font-semibold transition hover:bg-white/10 active:translate-y-px md:px-3"
            aria-label={itemCount ? `Giỏ hàng, ${itemCount} sản phẩm` : "Giỏ hàng"}
          >
            <ShoppingCart size={22} />
            <span className="hidden lg:inline">Giỏ hàng</span>
            {itemCount > 0 ? (
              <span className="absolute -right-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-brand-yellow px-1 text-[10px] font-bold text-slate-900">
                {itemCount > 99 ? "99+" : itemCount}
              </span>
            ) : null}
          </Link>

          <button
            type="button"
            onClick={() => setIsLocationOpen(true)}
            className="hidden h-10 min-w-[190px] shrink-0 items-center gap-2 rounded-full bg-white/15 px-4 text-left text-sm transition hover:bg-white/20 active:translate-y-px xl:flex"
          >
            <MapPin size={20} />
            <span className="truncate">{location}</span>
            <ChevronRight className="ml-auto size-4" />
          </button>
        </div>

        <nav className="border-t border-white/10 bg-[#f1f3f6] text-[#0068d7]">
          <div className="scrollbar-none mx-auto flex max-w-[1200px] gap-6 overflow-x-auto px-3 py-2 text-sm md:px-4 xl:justify-center">
            {categories.slice(0, 10).map((category) => (
              <Link
                key={category.id}
                href={`/danh-muc/${getCategorySlug(category)}`}
                className="shrink-0 whitespace-nowrap transition hover:text-[#004a9b] hover:underline active:opacity-70"
              >
                {category.name.toLocaleLowerCase("vi-VN")}
              </Link>
            ))}
          </div>
        </nav>
      </header>

      {isLocationOpen ? (
        <div className="fixed inset-0 z-[75] bg-black/45 px-4 py-10 backdrop-blur-[2px]">
          <div className="mx-auto max-w-md rounded-2xl bg-white p-5 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">Chọn khu vực xem giá</h2>
              <button
                type="button"
                onClick={() => setIsLocationOpen(false)}
                className="flex size-9 items-center justify-center rounded-full bg-slate-100 text-slate-600 transition hover:bg-slate-200 active:scale-95"
                aria-label="Đóng"
              >
                <X size={18} />
              </button>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Khu vực ảnh hưởng tới giá bán, khuyến mãi và thời gian giao hàng.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {locations.map((item) => {
                const isActive = item === location;
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => handleLocationChange(item)}
                    className={`rounded-xl border px-3 py-3 text-sm font-semibold transition active:translate-y-px ${
                      isActive
                        ? "border-brand-blue bg-sky-50 text-brand-blue"
                        : "border-slate-200 bg-white text-slate-700 hover:border-sky-300 hover:bg-sky-50"
                    }`}
                  >
                    {item}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
