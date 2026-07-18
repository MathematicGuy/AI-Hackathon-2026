"use client";

import { ArrowUpRight, MoveHorizontal, Sparkles } from "lucide-react";
import Link from "next/link";
import { SafeImage } from "@/components/SafeImage";
import { formatMoney } from "@/lib/format";

type ComparisonBadge =
  | "lowest_price"
  | "most_popular"
  | "highest_capacity"
  | "new_model";

interface ComparisonProduct {
  id: string;
  name: string;
  image: string;
  price: number;
  href: string;
  badges: ComparisonBadge[];
  power: string;
  technology: string;
  noteworthy: string;
  rating: number;
  soldLabel: string;
}

const comparisonProducts: ComparisonProduct[] = [
  {
    id: "featured-1",
    name: "Casper Inverter 1 HP JC-09IU36X",
    image: "https://cdn.tgdd.vn/2026/05/timerseo/363971.jpg",
    price: 5990000,
    href: "/san-pham/casper-inverter-1-hp-jc-09iu36x",
    badges: ["new_model"],
    power: "1 HP",
    technology: "Inverter",
    noteworthy: "Mẫu 2026",
    rating: 4.9,
    soldLabel: "Đã bán 18,7k",
  },
  {
    id: "featured-2",
    name: "Midea Inverter 1 HP MAFA-09CDN8",
    image: "https://cdn.tgdd.vn/2026/07/timerseo/320893.png",
    price: 5190000,
    href: "/san-pham/midea-inverter-1-hp-mafa-09cdn8",
    badges: ["lowest_price", "most_popular"],
    power: "1 HP",
    technology: "Inverter",
    noteworthy: "Điều khiển dễ dùng",
    rating: 4.9,
    soldLabel: "Đã bán 64,1k",
  },
  {
    id: "featured-5",
    name: "Nagakawa Inverter 1.5 HP NIS-C12R2T62",
    image: "https://cdn.tgdd.vn/2026/07/timerseo/361677.png",
    price: 6190000,
    href: "/san-pham/nagakawa-inverter-15-hp-nis-c12r2t62",
    badges: ["highest_capacity"],
    power: "1.5 HP",
    technology: "Inverter",
    noteworthy: "Mẫu 2026",
    rating: 4.9,
    soldLabel: "Đã bán 5,7k",
  },
];

const badgeContent: Record<
  ComparisonBadge,
  { label: string; className: string }
> = {
  lowest_price: {
    label: "Giá thấp nhất",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  most_popular: {
    label: "Bán nhiều nhất",
    className: "border-violet-200 bg-violet-50 text-violet-700",
  },
  highest_capacity: {
    label: "Công suất cao nhất",
    className: "border-amber-200 bg-amber-50 text-amber-800",
  },
  new_model: {
    label: "Mẫu 2026",
    className: "border-blue-200 bg-blue-50 text-blue-700",
  },
};

const comparisonRows = [
  {
    label: "Công suất",
    value: (product: ComparisonProduct) => product.power,
  },
  {
    label: "Công nghệ",
    value: (product: ComparisonProduct) => product.technology,
  },
  {
    label: "Điểm đáng chú ý",
    value: (product: ComparisonProduct) => product.noteworthy,
  },
  {
    label: "Đánh giá",
    value: (product: ComparisonProduct) =>
      `★ ${product.rating.toFixed(1)} · ${product.soldLabel}`,
  },
];

const followUpQuestions = [
  "Máy lạnh có khuyến mãi gì?",
  "Phòng 18m² chọn máy lạnh nào?",
  "Tra cứu bảo hành máy lạnh",
];

export function ChatComparisonResult({
  disabled,
  onNavigate,
  onSuggestion,
}: {
  disabled: boolean;
  onNavigate: () => void;
  onSuggestion: (question: string) => void;
}) {
  return (
    <section
      data-testid="chat-comparison-result"
      className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_32px_rgba(15,23,42,0.08)]"
      aria-label="Bảng so sánh máy lạnh"
    >
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-[linear-gradient(135deg,#eff6ff,#ffffff)] px-3 py-3 sm:px-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[#0754ad]">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-blue-100">
              <Sparkles className="size-4" aria-hidden="true" />
            </span>
            <h3 className="text-sm font-bold sm:text-base">
              {comparisonProducts.length} lựa chọn dễ cân nhắc
            </h3>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-600 sm:text-sm">
            So sánh nhanh theo giá và điểm mạnh nổi bật.
          </p>
        </div>
        <span className="hidden shrink-0 items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500 shadow-sm sm:flex">
          <MoveHorizontal className="size-3.5" aria-hidden="true" />
          Kéo ngang
        </span>
      </div>

      <div className="flex items-center gap-1.5 border-b border-slate-100 bg-slate-50 px-3 py-2 text-[11px] font-medium text-slate-500 sm:hidden">
        <MoveHorizontal className="size-4" aria-hidden="true" />
        Vuốt ngang để xem đủ bảng
      </div>

      <div
        data-testid="chat-comparison-table-scroll"
        className="overflow-x-auto overscroll-x-contain"
        role="region"
        tabIndex={0}
        aria-label="Bảng có thể cuộn ngang"
      >
        <table className="min-w-[656px] table-fixed border-separate border-spacing-0 text-left sm:min-w-[720px]">
          <caption className="sr-only">
            So sánh giá, công suất, công nghệ và đánh giá của ba máy lạnh
          </caption>
          <colgroup>
            <col className="w-[104px] sm:w-[132px]" />
            {comparisonProducts.map((product) => (
              <col key={product.id} className="w-[184px] sm:w-[196px]" />
            ))}
          </colgroup>
          <thead>
            <tr>
              <th className="sticky left-0 z-20 border-b border-r border-slate-200 bg-slate-50 px-3 py-3 align-top text-xs font-bold text-slate-600">
                Sản phẩm
              </th>
              {comparisonProducts.map((product) => (
                <th
                  key={product.id}
                  data-testid={`chat-comparison-product-${product.id}`}
                  scope="col"
                  className="border-b border-r border-slate-200 bg-white px-3 py-3 align-top last:border-r-0"
                >
                  <div className="flex h-full flex-col">
                    <div className="mb-2 flex min-h-12 flex-wrap content-start gap-1">
                      {product.badges.map((badge) => (
                        <span
                          key={badge}
                          className={`inline-flex h-fit rounded-full border px-2 py-1 text-[11px] font-bold leading-4 ${badgeContent[badge].className}`}
                        >
                          {badgeContent[badge].label}
                        </span>
                      ))}
                    </div>
                    <div className="mb-2 flex h-24 items-center justify-center rounded-xl bg-white">
                      <SafeImage
                        src={product.image}
                        alt={product.name}
                        className="h-full w-full object-contain p-1"
                        fallbackLabel={product.name}
                        loading="lazy"
                      />
                    </div>
                    <p className="line-clamp-2 min-h-10 text-[13px] font-semibold leading-5 text-slate-800">
                      {product.name}
                    </p>
                    <strong className="mt-1 text-base text-[#d70018]">
                      {formatMoney(product.price)}
                    </strong>
                    <Link
                      href={product.href}
                      onClick={onNavigate}
                      aria-label={`Xem sản phẩm ${product.name}`}
                      className="mt-3 inline-flex min-h-11 items-center justify-center gap-1 rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-bold text-[#0754ad] transition hover:border-blue-300 hover:bg-blue-100"
                    >
                      Xem sản phẩm
                      <ArrowUpRight className="size-3.5" aria-hidden="true" />
                    </Link>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row, rowIndex) => (
              <tr key={row.label}>
                <th
                  scope="row"
                  className={`sticky left-0 z-10 border-r border-slate-200 bg-slate-50 px-3 py-3 text-xs font-bold text-slate-600 ${rowIndex < comparisonRows.length - 1 ? "border-b" : ""}`}
                >
                  {row.label}
                </th>
                {comparisonProducts.map((product) => (
                  <td
                    key={product.id}
                    className={`border-r border-slate-200 bg-white px-3 py-3 text-xs leading-5 text-slate-700 last:border-r-0 ${rowIndex < comparisonRows.length - 1 ? "border-b" : ""}`}
                  >
                    {row.value(product)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-100 px-3 py-3 sm:px-4">
        <p className="mb-2 text-xs font-bold text-slate-700">
          Bạn muốn hỏi tiếp điều gì?
        </p>
        <div className="scrollbar-none flex gap-2 overflow-x-auto pb-1">
          {followUpQuestions.map((question) => (
            <button
              key={question}
              type="button"
              disabled={disabled}
              onClick={() => onSuggestion(question)}
              className="min-h-11 shrink-0 rounded-full border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 hover:text-[#0754ad] active:scale-[0.98]"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
