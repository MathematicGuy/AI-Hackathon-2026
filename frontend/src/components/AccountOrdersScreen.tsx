"use client";

import {
  Apple,
  BookUser,
  CalendarDays,
  ChevronLeft,
  ClipboardList,
  MapPin,
  PackageCheck,
  Play,
  QrCode,
  ShoppingBag,
  TicketPercent,
  Truck,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { startTransition, useState, useSyncExternalStore } from "react";
import { SafeImage } from "@/components/SafeImage";
import { useToast } from "@/components/ToastProvider";
import { getProductSlug } from "@/lib/catalog";
import { formatDate, formatMoney } from "@/lib/format";
import type { ProductItem } from "@/types/home";

interface AccountOrdersScreenProps {
  products: ProductItem[];
}

type AccountPanel = "orders" | "addresses" | "coupons";
type OrderStatus = "all" | "pending" | "confirmed" | "shipping" | "delivered" | "cancelled" | "successful";

interface MockOrder {
  id: string;
  createdAt: string;
  status: Exclude<OrderStatus, "all">;
  product: ProductItem;
  quantity: number;
}

const orderStatuses: Array<{ id: OrderStatus; label: string }> = [
  { id: "all", label: "Tất cả" },
  { id: "pending", label: "Chờ xử lý" },
  { id: "confirmed", label: "Đã xác nhận" },
  { id: "shipping", label: "Đang chuyển hàng" },
  { id: "delivered", label: "Đang giao hàng" },
  { id: "cancelled", label: "Đã hủy" },
  { id: "successful", label: "Thành công" },
];

const statusLabels: Record<Exclude<OrderStatus, "all">, string> = {
  pending: "Chờ xử lý",
  confirmed: "Đã xác nhận",
  shipping: "Đang chuyển hàng",
  delivered: "Đang giao hàng",
  cancelled: "Đã hủy",
  successful: "Giao hàng thành công",
};

function toDisplayDate(value: string) {
  return formatDate(`${value}T00:00:00+07:00`);
}

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

export function AccountOrdersScreen({ products }: AccountOrdersScreenProps) {
  const router = useRouter();
  const { showToast } = useToast();
  const [activePanel, setActivePanel] = useState<AccountPanel>("orders");
  const [activeStatus, setActiveStatus] = useState<OrderStatus>("all");
  const phone = useSyncExternalStore(subscribeToAccount, getAccountPhone, () => "");
  const [isDateModalOpen, setIsDateModalOpen] = useState(false);
  const [startDate, setStartDate] = useState("2025-07-17");
  const [endDate, setEndDate] = useState("2026-07-17");
  const [draftStartDate, setDraftStartDate] = useState(startDate);
  const [draftEndDate, setDraftEndDate] = useState(endDate);
  const [dateError, setDateError] = useState("");
  const [showSampleOrders, setShowSampleOrders] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isAddressFormOpen, setIsAddressFormOpen] = useState(false);
  const [addressName, setAddressName] = useState("");
  const [addressDetail, setAddressDetail] = useState("");
  const [addressError, setAddressError] = useState("");

  const mockOrders: MockOrder[] = products.slice(0, 4).map((product, index) => ({
    id: `DMX2607${String(index + 1).padStart(3, "0")}`,
    createdAt: ["2026-07-16", "2026-07-14", "2026-07-10", "2026-07-05"][index] || "2026-07-01",
    status: (["confirmed", "shipping", "delivered", "successful"] as const)[index] || "pending",
    product,
    quantity: index === 2 ? 2 : 1,
  }));

  const visibleOrders = showSampleOrders
    ? mockOrders.filter((order) => activeStatus === "all" || order.status === activeStatus)
    : [];

  const changeStatus = (status: OrderStatus) => {
    setIsLoading(true);
    startTransition(() => setActiveStatus(status));
    window.setTimeout(() => setIsLoading(false), 320);
  };

  const applyDateRange = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draftStartDate || !draftEndDate) {
      setDateError("Vui lòng chọn đủ ngày bắt đầu và ngày kết thúc.");
      return;
    }
    if (draftStartDate > draftEndDate) {
      setDateError("Ngày bắt đầu không được sau ngày kết thúc.");
      return;
    }
    setStartDate(draftStartDate);
    setEndDate(draftEndDate);
    setDateError("");
    setIsDateModalOpen(false);
    showToast({
      variant: "success",
      title: "Đã cập nhật thời gian",
      description: `${toDisplayDate(draftStartDate)} - ${toDisplayDate(draftEndDate)}`,
    });
  };

  const saveAddress = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (addressName.trim().length < 2 || addressDetail.trim().length < 10) {
      setAddressError("Nhập họ tên và địa chỉ chi tiết ít nhất 10 ký tự.");
      return;
    }
    setAddressError("");
    setIsAddressFormOpen(false);
    showToast({
      variant: "success",
      title: "Đã thêm địa chỉ",
      description: addressDetail.trim(),
    });
  };

  const logout = () => {
    window.localStorage.removeItem("dmx-account-phone");
    window.dispatchEvent(new Event("dmx-account-change"));
    showToast({
      variant: "success",
      title: "Đã đăng xuất",
      description: "Thông tin tài khoản đã được xóa khỏi phiên này.",
    });
    router.push("/dang-nhap");
  };

  return (
    <main className="min-h-[650px] bg-[#f1f3f6] px-3 py-7 md:px-4 md:py-9">
      <div className="mx-auto grid max-w-[1500px] grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:gap-9 2xl:grid-cols-[400px_minmax(0,1fr)]">
        <aside>
          <div className="flex items-end justify-between lg:block">
            <div>
              <p className="text-xl text-slate-800">Bạn</p>
              {phone ? <p className="mt-1 text-sm text-slate-500">{phone}</p> : null}
            </div>
            {!phone ? (
              <Link href="/dang-nhap" className="text-sm font-semibold text-[#0068d7] hover:underline">
                Đăng nhập
              </Link>
            ) : null}
          </div>

          <nav className="scrollbar-none mt-6 flex gap-2 overflow-x-auto lg:block lg:space-y-1">
            <button
              type="button"
              onClick={() => setActivePanel("orders")}
              className={`flex h-[54px] min-w-[210px] items-center gap-3 rounded-md px-4 text-left text-base transition lg:w-full ${
                activePanel === "orders" ? "bg-[#e4e7ed] font-medium" : "hover:bg-white/70"
              }`}
            >
              <ClipboardList className={`size-6 ${activePanel === "orders" ? "text-emerald-400" : "text-slate-400"}`} />
              Đơn hàng đã mua
            </button>
            <button
              type="button"
              onClick={() => setActivePanel("addresses")}
              className={`flex h-[54px] min-w-[180px] items-center gap-3 rounded-md px-4 text-left text-base transition lg:w-full ${
                activePanel === "addresses" ? "bg-[#e4e7ed] font-medium" : "hover:bg-white/70"
              }`}
            >
              <BookUser className={`size-6 ${activePanel === "addresses" ? "text-emerald-400" : "text-slate-400"}`} />
              Sổ địa chỉ
            </button>
            <button
              type="button"
              onClick={() => setActivePanel("coupons")}
              className={`flex h-[54px] min-w-[190px] items-center gap-3 rounded-md px-4 text-left text-base transition lg:w-full ${
                activePanel === "coupons" ? "bg-[#e4e7ed] font-medium" : "hover:bg-white/70"
              }`}
            >
              <TicketPercent className={`size-6 ${activePanel === "coupons" ? "text-emerald-400" : "text-slate-400"}`} />
              Mã giảm của bạn
            </button>
          </nav>

          <button
            type="button"
            onClick={logout}
            className="mt-7 hidden h-[58px] w-full items-center justify-center rounded-md border border-[#438fe7] font-bold text-[#438fe7] transition hover:bg-blue-50 active:translate-y-px lg:flex"
          >
            Đăng Xuất
          </button>

          <section className="mt-6 hidden rounded-xl bg-[#fff7c9] p-4 lg:block">
            <h2 className="border-b border-amber-100 pb-3 text-base font-bold">Tổng điểm tích lũy: 0 điểm</h2>
            <div className="mt-3 grid grid-cols-[1fr_82px] gap-2">
              <div>
                <p className="text-sm font-bold">Tải app Quà Tặng VIP</p>
                <p className="mt-2 text-xs leading-4 text-slate-600">
                  Tích và sử dụng điểm cho khách hàng thân thiết.
                </p>
              </div>
              <QrCode className="size-[82px] bg-white p-1 text-black" />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <span className="flex h-10 items-center justify-center gap-1 rounded bg-black px-2 text-[10px] text-white">
                <Apple className="size-5" /> App Store
              </span>
              <span className="flex h-10 items-center justify-center gap-1 rounded bg-black px-2 text-[10px] text-white">
                <Play className="size-4 fill-white" /> Google Play
              </span>
            </div>
          </section>
        </aside>

        <section className="min-w-0">
          {activePanel === "orders" ? (
            <>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <h1 className="text-[22px] font-medium text-slate-800 md:text-2xl">Đơn hàng đã mua</h1>
                <span className="text-sm font-medium text-slate-800 md:text-base">
                  Từ {toDisplayDate(startDate)} - {toDisplayDate(endDate)}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setDraftStartDate(startDate);
                    setDraftEndDate(endDate);
                    setDateError("");
                    setIsDateModalOpen(true);
                  }}
                  className="flex items-center gap-1.5 text-sm font-medium text-[#004f9f] transition hover:text-[#006fe6] hover:underline"
                >
                  <CalendarDays className="size-4" /> Thay đổi
                </button>
              </div>

              <div className="scrollbar-none mt-5 flex gap-2 overflow-x-auto pb-1 2xl:gap-4">
                {orderStatuses.map((status) => (
                  <button
                    key={status.id}
                    type="button"
                    onClick={() => changeStatus(status.id)}
                    className={`h-12 shrink-0 rounded-md border bg-white px-4 text-sm transition hover:border-[#0068d7] hover:text-[#0068d7] active:bg-blue-50 2xl:px-6 ${
                      activeStatus === status.id
                        ? "border-[#0068d7] text-[#0068d7]"
                        : "border-[#c7c7c7] text-slate-700"
                    }`}
                    aria-pressed={activeStatus === status.id}
                  >
                    {status.label}
                  </button>
                ))}
              </div>

              <div className="mt-4 min-h-[465px] bg-white p-4 md:p-8">
                {isLoading ? (
                  <div className="space-y-4" aria-label="Đang tải đơn hàng">
                    {[0, 1, 2].map((item) => (
                      <div key={item} className="h-28 animate-pulse rounded-lg bg-slate-100" />
                    ))}
                  </div>
                ) : visibleOrders.length ? (
                  <div className="space-y-4">
                    {visibleOrders.map((order) => (
                      <article key={order.id} className="rounded-lg border border-slate-200 p-4 transition hover:border-sky-200 hover:shadow-sm">
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3 text-sm">
                          <span className="font-semibold text-slate-700">Mã đơn: {order.id}</span>
                          <span className={`font-semibold ${order.status === "cancelled" ? "text-rose-600" : "text-emerald-600"}`}>
                            {statusLabels[order.status]}
                          </span>
                        </div>
                        <div className="mt-3 flex gap-4">
                          <SafeImage src={order.product.src} alt={order.product.name} className="size-20 shrink-0 object-contain" fallbackLabel={order.product.name} />
                          <div className="min-w-0 flex-1">
                            <Link href={`/san-pham/${getProductSlug(order.product)}`} className="line-clamp-2 font-medium text-slate-800 hover:text-[#0068d7]">
                              {order.product.name}
                            </Link>
                            <p className="mt-1 text-sm text-slate-500">Số lượng: {order.quantity} · Đặt ngày {toDisplayDate(order.createdAt)}</p>
                            <p className="mt-2 font-bold text-[#d70018]">{formatMoney(order.product.price * order.quantity)}</p>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="flex min-h-[395px] flex-col items-center justify-center text-center">
                    <ShoppingBag className="size-24 text-[#21499a]" strokeWidth={1.8} />
                    <h2 className="mt-4 text-xl font-bold text-slate-900 md:text-2xl">Rất tiếc, không tìm thấy đơn hàng nào phù hợp</h2>
                    <p className="mt-2 text-sm text-slate-400 md:text-base">Vẫn còn rất nhiều sản phẩm đang chờ bạn</p>
                    <div className="mt-6 flex max-w-md flex-wrap justify-center gap-3">
                      {[
                        ["Tivi", "/danh-muc/tivi"],
                        ["Tủ lạnh", "/danh-muc/tu-lanh"],
                        ["Máy lạnh", "/danh-muc/may-lanh"],
                        ["Máy giặt", "/danh-muc/may-giat"],
                        ["Gia dụng", "/danh-muc/gia-dung"],
                      ].map(([label, href]) => (
                        <Link key={label} href={href} className="rounded-md border border-[#1685ef] px-3 py-3 text-sm text-[#005cb8] transition hover:bg-blue-50 active:translate-y-px">
                          {label}
                        </Link>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setShowSampleOrders(true);
                        showToast({ variant: "success", title: "Đã tải đơn hàng mẫu", description: "Bạn có thể thử các bộ lọc trạng thái." });
                      }}
                      className="mt-6 rounded-md bg-[#2a83e9] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#176fc9] active:translate-y-px"
                    >
                      Xem đơn hàng mẫu
                    </button>
                    <Link href="/" className="mt-5 flex items-center gap-2 text-[#005cb8] hover:underline">
                      <ChevronLeft className="size-5" /> Về trang chủ
                    </Link>
                  </div>
                )}
              </div>
            </>
          ) : null}

          {activePanel === "addresses" ? (
            <section className="rounded-lg bg-white p-5 shadow-sm md:p-8">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h1 className="text-2xl font-bold text-slate-900">Sổ địa chỉ</h1>
                  <p className="mt-1 text-sm text-slate-500">Quản lý địa chỉ nhận hàng của bạn.</p>
                </div>
                <button type="button" onClick={() => setIsAddressFormOpen((value) => !value)} className="rounded-md bg-[#2a83e9] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#176fc9] active:translate-y-px">
                  Thêm địa chỉ
                </button>
              </div>
              {isAddressFormOpen ? (
                <form onSubmit={saveAddress} className="mt-5 rounded-lg border border-sky-100 bg-sky-50 p-4" noValidate>
                  <div className="grid gap-3 md:grid-cols-2">
                    <label className="text-sm font-medium text-slate-700">Họ và tên
                      <input value={addressName} onChange={(event) => { setAddressName(event.target.value); setAddressError(""); }} className="mt-1 h-11 w-full rounded-md border border-slate-300 bg-white px-3 outline-none focus:border-[#2a83e9]" />
                    </label>
                    <label className="text-sm font-medium text-slate-700">Địa chỉ chi tiết
                      <input value={addressDetail} onChange={(event) => { setAddressDetail(event.target.value); setAddressError(""); }} className="mt-1 h-11 w-full rounded-md border border-slate-300 bg-white px-3 outline-none focus:border-[#2a83e9]" />
                    </label>
                  </div>
                  {addressError ? <p className="mt-2 text-sm text-rose-600">{addressError}</p> : null}
                  <button type="submit" className="mt-3 rounded-md bg-[#2a83e9] px-5 py-2 text-sm font-semibold text-white hover:bg-[#176fc9]">Lưu địa chỉ</button>
                </form>
              ) : null}
              <article className="mt-6 rounded-lg border border-slate-200 p-5">
                <div className="flex items-start gap-3">
                  <MapPin className="mt-0.5 size-6 shrink-0 text-[#2a83e9]" />
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-bold text-slate-900">Bạn</h2>
                      <span className="rounded bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-600">Mặc định</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">128 Trần Quang Khải, Phường Tân Định, TP. Hồ Chí Minh</p>
                    <p className="text-sm text-slate-500">{phone || "090 123 4567"}</p>
                  </div>
                </div>
              </article>
            </section>
          ) : null}

          {activePanel === "coupons" ? (
            <section className="rounded-lg bg-white p-5 shadow-sm md:p-8">
              <h1 className="text-2xl font-bold text-slate-900">Mã giảm của bạn</h1>
              <p className="mt-1 text-sm text-slate-500">Chọn mã khi thanh toán để áp dụng ưu đãi.</p>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                {[
                  { code: "DMX200K", value: "Giảm 200.000đ", note: "Đơn điện lạnh từ 8 triệu", icon: PackageCheck },
                  { code: "FREESHIP", value: "Miễn phí giao hàng", note: "Áp dụng tại TP. Hồ Chí Minh", icon: Truck },
                ].map((coupon) => (
                  <article key={coupon.code} className="relative overflow-hidden rounded-lg border border-dashed border-[#2a83e9] bg-blue-50 p-5">
                    <coupon.icon className="size-9 text-[#2a83e9]" />
                    <h2 className="mt-3 text-lg font-bold text-[#005cb8]">{coupon.value}</h2>
                    <p className="mt-1 text-sm text-slate-600">{coupon.note}</p>
                    <button type="button" onClick={() => showToast({ variant: "success", title: `Đã lưu mã ${coupon.code}`, description: "Mã sẽ xuất hiện ở bước thanh toán." })} className="mt-4 rounded-md border border-[#2a83e9] bg-white px-3 py-2 text-sm font-semibold text-[#005cb8] hover:bg-blue-100">
                      Lưu mã {coupon.code}
                    </button>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </section>
      </div>

      {isDateModalOpen ? (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 px-4">
          <form onSubmit={applyDateRange} className="w-full max-w-md rounded-xl bg-white p-5 shadow-2xl" noValidate>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">Thay đổi khoảng thời gian</h2>
              <button type="button" onClick={() => setIsDateModalOpen(false)} className="flex size-9 items-center justify-center rounded-full bg-slate-100 hover:bg-slate-200" aria-label="Đóng">
                <X className="size-5" />
              </button>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">Từ ngày
                <input type="date" value={draftStartDate} onChange={(event) => { setDraftStartDate(event.target.value); setDateError(""); }} className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-[#2a83e9]" />
              </label>
              <label className="text-sm font-medium text-slate-700">Đến ngày
                <input type="date" value={draftEndDate} onChange={(event) => { setDraftEndDate(event.target.value); setDateError(""); }} className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-[#2a83e9]" />
              </label>
            </div>
            {dateError ? <p className="mt-3 text-sm text-rose-600">{dateError}</p> : null}
            <button type="submit" className="mt-5 h-11 w-full rounded-md bg-[#2a83e9] font-semibold text-white transition hover:bg-[#176fc9] active:translate-y-px">
              Áp dụng
            </button>
          </form>
        </div>
      ) : null}
    </main>
  );
}
