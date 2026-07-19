"use client";

import { Check, MoveHorizontal, Sparkles } from "lucide-react";
import { formatMoney } from "@/lib/format";

// Shape of the `comparison` block on the agent response. The agent builds it
// from the same dimension registry its reply text is built from, so the table
// can never contradict the answer above it. It is absent on every turn that is
// not a comparison.
export interface AgentComparisonProduct {
  id: string;
  name: string;
  brand: string | null;
  effective_price: number | null;
  list_price: number | null;
  discount_percent: number | null;
  gift: string | null;
}

export interface AgentComparisonRow {
  label: string;
  unit: string;
  explain: string;
  values: Record<string, string>;
  winner_id: string | null;
}

export interface AgentComparison {
  products: AgentComparisonProduct[];
  rows: AgentComparisonRow[];
  price_delta: number | null;
}

const followUpQuestions = [
  "Mẫu nào tiết kiệm điện hơn?",
  "Có khuyến mãi gì không?",
  "Phòng 18m² nên chọn mẫu nào?",
];

export function ChatComparisonResult({
  comparison,
  disabled,
  onSuggestion,
}: {
  comparison: AgentComparison;
  disabled: boolean;
  onSuggestion: (question: string) => void;
}) {
  const { products, rows } = comparison;
  if (products.length < 2) {
    return null;
  }

  return (
    <section
      data-testid="chat-comparison-result"
      className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_32px_rgba(15,23,42,0.08)]"
      aria-label="Bảng so sánh sản phẩm"
    >
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-[linear-gradient(135deg,#eff6ff,#ffffff)] px-3 py-3 sm:px-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[#0754ad]">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-blue-100">
              <Sparkles className="size-4" aria-hidden="true" />
            </span>
            <h3 className="text-sm font-bold sm:text-base">
              So sánh {products.length} mẫu
            </h3>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-600 sm:text-sm">
            {comparison.price_delta
              ? `Chênh lệch giá ${formatMoney(comparison.price_delta)}.`
              : "So sánh theo các thông số của ngành hàng này."}
          </p>
        </div>
        <span className="hidden shrink-0 items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 shadow-sm md:flex">
          <MoveHorizontal className="size-3.5" aria-hidden="true" />
          Cuộn bảng
        </span>
      </div>

      <div className="flex items-center gap-1.5 border-b border-slate-100 bg-slate-50 px-3 py-2 text-[11px] font-medium text-slate-600 md:hidden">
        <MoveHorizontal className="size-4" aria-hidden="true" />
        Vuốt ngang để xem đủ bảng
      </div>

      <div
        data-testid="chat-comparison-table-scroll"
        className="chat-scrollbar overflow-x-auto overscroll-x-contain focus-visible:outline-2 focus-visible:outline-offset-[-3px] focus-visible:outline-[#176fc9]"
        role="region"
        tabIndex={0}
        aria-label="Bảng có thể cuộn ngang"
      >
        <table className="min-w-[560px] table-fixed border-separate border-spacing-0 text-left">
          <caption className="sr-only">
            So sánh giá và thông số của {products.length} sản phẩm
          </caption>
          <colgroup>
            <col className="w-[128px]" />
            {products.map((product) => (
              <col key={product.id} className="w-[200px]" />
            ))}
          </colgroup>
          <thead>
            <tr>
              <th
                scope="col"
                className="sticky left-0 z-20 border-b border-r border-slate-200 bg-slate-50 px-3 py-3 align-top text-xs font-bold text-slate-600"
              >
                Sản phẩm
              </th>
              {products.map((product) => (
                <th
                  key={product.id}
                  data-testid={`chat-comparison-product-${product.id}`}
                  scope="col"
                  className="border-b border-r border-slate-200 bg-white px-3 py-3 align-top last:border-r-0"
                >
                  <div className="flex h-full flex-col">
                    <div className="mb-2 flex flex-wrap gap-1">
                      {product.discount_percent ? (
                        <span className="inline-flex h-fit rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-bold leading-4 text-emerald-700">
                          Giảm {Math.round(product.discount_percent)}%
                        </span>
                      ) : null}
                      {product.gift ? (
                        <span className="inline-flex h-fit rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[11px] font-bold leading-4 text-amber-800">
                          Có quà tặng
                        </span>
                      ) : null}
                    </div>
                    <p className="line-clamp-3 min-h-10 text-[13px] font-semibold leading-5 text-slate-800">
                      {product.name}
                    </p>
                    {product.effective_price ? (
                      <strong className="mt-1 text-base text-[#d70018]">
                        {formatMoney(product.effective_price)}
                      </strong>
                    ) : (
                      <span className="mt-1 text-[13px] text-slate-500">
                        Giá đang cập nhật
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th
                  scope="row"
                  className="sticky left-0 z-10 border-b border-r border-slate-200 bg-slate-50 px-3 py-3 text-[13px] font-bold text-slate-600"
                >
                  <span title={row.explain || undefined}>{row.label}</span>
                </th>
                {products.map((product) => {
                  const isWinner = row.winner_id === product.id;
                  return (
                    <td
                      key={product.id}
                      className={`border-b border-r border-slate-200 px-3 py-3 text-[13px] leading-5 last:border-r-0 ${
                        isWinner
                          ? "bg-emerald-50 font-semibold text-emerald-800"
                          : "bg-white text-slate-700"
                      }`}
                    >
                      <span className="inline-flex items-center gap-1">
                        {row.values[product.id] ?? "—"}
                        {isWinner ? (
                          <Check
                            className="size-3.5 shrink-0"
                            aria-label="Nhỉnh hơn ở tiêu chí này"
                          />
                        ) : null}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-100 px-3 py-3 sm:px-4">
        <p className="mb-2 text-xs font-bold text-slate-700">
          Anh/chị muốn hỏi tiếp điều gì ạ?
        </p>
        <div className="grid gap-2 sm:flex sm:flex-wrap">
          {followUpQuestions.map((question) => (
            <button
              key={question}
              type="button"
              disabled={disabled}
              onClick={() => onSuggestion(question)}
              className="min-h-11 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 hover:text-[#0754ad] active:scale-[0.98] sm:rounded-full sm:text-xs"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
