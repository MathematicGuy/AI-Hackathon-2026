"use client";

import { ArrowUpRight, MoveHorizontal, Sparkles } from "lucide-react";
import Link from "next/link";
import { SafeImage } from "@/components/SafeImage";
import { formatMoney } from "@/lib/format";
import type {
  AgentPresentation,
  AgentPresentedProduct,
} from "@/types/agent";

<<<<<<< HEAD
const numberFormatter = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 1,
});

function MissingValue({ children = "Chưa có dữ liệu" }: { children?: string }) {
  return <span className="text-slate-400">{children}</span>;
}

function ProductBadges({ product }: { product: AgentPresentedProduct }) {
  if (product.badges.length === 0) {
    return null;
  }
  return (
    <div className="flex flex-wrap gap-1">
      {product.badges.map((badge, index) => (
        <span
          key={`${badge.code}-${index}`}
          className="inline-flex rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] font-bold leading-4 text-blue-700"
        >
          {badge.label}
        </span>
      ))}
    </div>
  );
}

function ProductPrice({ product }: { product: AgentPresentedProduct }) {
  return (
    <div className="mt-2">
      {product.effective_price_vnd === null ? (
        <MissingValue>Chưa có giá</MissingValue>
      ) : (
        <strong className="text-base text-[#d70018]">
          {formatMoney(product.effective_price_vnd)}
        </strong>
      )}
      <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs">
        {product.list_price_vnd === null ||
          product.discount_percent === null ||
          product.discount_percent <= 0 ? null : (
          <span className="text-slate-500 line-through">
            {formatMoney(product.list_price_vnd)}
          </span>
        )}
        {product.discount_percent === null ||
          product.discount_percent <= 0 ? null : (
          <span className="font-semibold text-rose-600">
            -{numberFormatter.format(product.discount_percent)}%
          </span>
        )}
      </div>
      {product.promotion_text === null ? null : (
        <p className="mt-1 text-xs font-medium leading-5 text-emerald-700">
          {product.promotion_text}
        </p>
      )}
    </div>
  );
}

function ProductFacts({ product }: { product: AgentPresentedProduct }) {
  return (
    <dl className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-xs">
      {product.highlights.map((highlight, index) => (
        <div key={`${highlight.label}-${index}`} className="flex gap-2">
          <dt className="min-w-24 font-semibold text-slate-600">
            {highlight.label}
          </dt>
          <dd className="text-slate-800">
            {highlight.value ?? <MissingValue />}
          </dd>
        </div>
      ))}
      <div className="flex gap-2">
        <dt className="min-w-24 font-semibold text-slate-600">Đánh giá</dt>
        <dd className="text-slate-800">
          {product.rating === null ? (
            <MissingValue />
          ) : (
            `${numberFormatter.format(product.rating)}/5`
          )}
        </dd>
      </div>
      <div className="flex gap-2">
        <dt className="min-w-24 font-semibold text-slate-600">Đã bán</dt>
        <dd className="text-slate-800">
          {product.sold_count === null ? (
            <MissingValue />
          ) : (
            numberFormatter.format(product.sold_count)
          )}
        </dd>
      </div>
    </dl>
  );
}

function ProductAction({
  product,
  onNavigate,
}: {
  product: AgentPresentedProduct;
  onNavigate: () => void;
}) {
  if (product.product_url === null) {
    return <MissingValue>Chưa có liên kết sản phẩm</MissingValue>;
  }
  return (
    <Link
      href={product.product_url}
      onClick={onNavigate}
      aria-label={`Xem sản phẩm ${product.name}`}
      className="inline-flex min-h-11 w-full items-center justify-center gap-1 rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-bold text-[#0754ad] transition hover:border-blue-300 hover:bg-blue-100"
    >
      Xem sản phẩm
      <ArrowUpRight className="size-3.5" aria-hidden="true" />
    </Link>
  );
}

function PresentationNotices({
  presentation,
  disabled,
  onSuggestion,
}: {
  presentation: AgentPresentation;
  disabled: boolean;
  onSuggestion: (question: string) => void;
}) {
  if (
    presentation.warnings.length === 0 &&
    presentation.follow_up_questions.length === 0
  ) {
    return null;
  }
  return (
    <div className="border-t border-slate-100 px-3 py-3 sm:px-4">
      {presentation.warnings.length > 0 ? (
        <div className="mb-3 space-y-1" role="note" aria-label="Lưu ý">
          {presentation.warnings.map((warning, index) => (
            <p
              key={`${warning}-${index}`}
              className="rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800"
            >
              {warning}
            </p>
          ))}
        </div>
      ) : null}
      {presentation.follow_up_questions.length > 0 ? (
        <div>
          <p className="mb-2 text-xs font-bold text-slate-700">
            Bạn muốn hỏi tiếp điều gì?
          </p>
          <div className="grid gap-2 sm:flex sm:flex-wrap">
            {presentation.follow_up_questions.map((question, index) => (
              <button
                key={`${question}-${index}`}
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
      ) : null}
    </div>
  );
}

function RecommendationResult({
  presentation,
=======
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
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
  disabled,
  onSuggestion,
<<<<<<< HEAD
}: ChatComparisonResultProps) {
  return (
    <section
      data-testid="chat-recommendation-result"
      className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_32px_rgba(15,23,42,0.08)]"
      aria-label="Sản phẩm được trợ lý đề xuất"
    >
      <div className="border-b border-slate-100 bg-[linear-gradient(135deg,#eff6ff,#ffffff)] px-3 py-3 sm:px-4">
        <div className="flex items-center gap-2 text-[#0754ad]">
          <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-blue-100">
            <Sparkles className="size-4" aria-hidden="true" />
          </span>
          <h3 className="text-sm font-bold sm:text-base">
            {presentation.products.length} lựa chọn phù hợp
          </h3>
        </div>
      </div>
      <div className="grid gap-3 p-3 sm:grid-cols-2 sm:p-4">
        {presentation.products.map((product) => (
          <article
            key={product.sku}
            data-testid={`chat-presentation-product-${product.sku}`}
            className="flex min-w-0 flex-col rounded-xl border border-slate-200 p-3"
          >
            <ProductBadges product={product} />
            <SafeImage
              src={product.image_url ?? undefined}
              alt=""
              className="mt-2 h-28 w-full rounded-xl object-contain p-1"
              fallbackLabel="Chưa có hình ảnh"
              loading="lazy"
            />
            {product.brand === null ? null : (
              <p className="mt-2 text-xs font-semibold uppercase text-slate-500">
                {product.brand}
              </p>
            )}
            <h4 className="mt-1 text-sm font-semibold leading-5 text-slate-800">
              {product.name}
            </h4>
            <ProductPrice product={product} />
            <ProductFacts product={product} />
            <div className="mt-auto pt-3">
              <ProductAction product={product} onNavigate={onNavigate} />
            </div>
          </article>
        ))}
      </div>
      <PresentationNotices
        presentation={presentation}
        disabled={disabled}
        onSuggestion={onSuggestion}
      />
    </section>
  );
}

interface ChatComparisonResultProps {
  presentation: AgentPresentation;
=======
}: {
  comparison: AgentComparison;
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
  disabled: boolean;
  onSuggestion: (question: string) => void;
<<<<<<< HEAD
}

export function ChatComparisonResult(props: ChatComparisonResultProps) {
  const { presentation, disabled, onNavigate, onSuggestion } = props;

  if (presentation.type === "text") {
    if (
      presentation.warnings.length === 0 &&
      presentation.follow_up_questions.length === 0
    ) {
      return null;
    }
    return (
      <section
        data-testid="chat-text-presentation"
        className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white"
      >
        <PresentationNotices
          presentation={presentation}
          disabled={disabled}
          onSuggestion={onSuggestion}
        />
      </section>
    );
  }

  if (presentation.type === "recommendation") {
    return <RecommendationResult {...props} />;
=======
}) {
  const { products, rows } = comparison;
  if (products.length < 2) {
    return null;
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
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
<<<<<<< HEAD
              So sánh { presentation.products.length } sản phẩm
            </h3 >
          </div >
=======
              So sánh {products.length} mẫu
            </h3>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-600 sm:text-sm">
            {comparison.price_delta
              ? `Chênh lệch giá ${formatMoney(comparison.price_delta)}.`
              : "So sánh theo các thông số của ngành hàng này."}
          </p>
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
        </div >
    <span className="hidden shrink-0 items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 shadow-sm md:flex">
      <MoveHorizontal className="size-3.5" aria-hidden="true" />
      Cuộn bảng
    </span>
      </div >

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
<<<<<<< HEAD
  <table
    className="table-fixed border-separate border-spacing-0 text-left"
    style={{ minWidth: 112 + presentation.products.length * 184 }}
  >
    <caption className="sr-only">
      So sánh các thông tin do trợ lý cung cấp cho sản phẩm
    </caption>
    <colgroup>
      <col className="w-[112px]" />
      {presentation.products.map((product) => (
        <col key={product.sku} className="w-[184px]" />
=======
        <table className="min-w-[560px] table-fixed border-separate border-spacing-0 text-left">
          <caption className="sr-only">
            So sánh giá và thông số của {products.length} sản phẩm
          </caption>
          <colgroup>
            <col className="w-[128px]" />
            {products.map((product) => (
              <col key={product.id} className="w-[200px]" />
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
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
<<<<<<< HEAD
  {
    presentation.products.map((product) => (
=======
              {products.map((product) => (
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
      <th
        key={product.sku}
        data-testid={`chat-presentation-product-${product.sku}`}
        scope="col"
        className="border-b border-r border-slate-200 bg-white px-3 py-3 align-top last:border-r-0"
      >
        <div className="flex h-full flex-col">
<<<<<<< HEAD
                    <ProductBadges product={product} />
                    <SafeImage
                      src={product.image_url ?? undefined}
                      alt=""
                      className="my-2 h-24 w-full rounded-xl object-contain p-1"
                      fallbackLabel="Chưa có hình ảnh"
                      loading="lazy"
                    />
                    {
        product.brand === null ? null : (
          <p className="text-[11px] font-semibold uppercase text-slate-500">
            {product.brand}
          </p>
        )
      }
      < p className = "mt-1 text-[13px] font-semibold leading-5 text-slate-800" >
      { product.name }
                    </p >
                    <ProductPrice product={product} />
                    <div className="mt-2 text-xs leading-5 text-slate-600">
                      <p>
                        Đánh giá: {product.rating === null ? <MissingValue /> : `${numberFormatter.format(product.rating)}/5`}
                      </p>
                      <p>
                        Đã bán: {product.sold_count === null ? <MissingValue /> : numberFormatter.format(product.sold_count)}
                      </p>
                    </div>
=======
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
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
                  </div >
                </th >
              ))
  }
            </tr >
          </thead >
    <tbody>
<<<<<<< HEAD
  {
    presentation.comparison_rows.map((row, rowIndex) => {
      const valuesBySku = new Map(
        row.values.map((cell) => [cell.sku, cell.value]),
      );
      return (
        <tr key={`${row.label}-${rowIndex}`}>
          <th
            scope="row"
            className="sticky left-0 z-10 border-b border-r border-slate-200 bg-slate-50 px-3 py-3 text-[13px] font-bold text-slate-600"
          >
            {row.label}
          </th>
          {presentation.products.map((product) => (
            <td
              key={product.sku}
              className="border-b border-r border-slate-200 bg-white px-3 py-3 text-[13px] leading-5 text-slate-700 last:border-r-0"
            >
              {valuesBySku.get(product.sku) ?? <MissingValue />}
            </td>
          ))}
        </tr>
      );
    })
  }
  <tr>
    <th
      scope="row"
      className="sticky left-0 z-10 border-r border-slate-200 bg-slate-50 px-3 py-3 text-[13px] font-bold text-slate-600"
    >
      Xem chi tiết
    </th>
    {presentation.products.map((product) => (
      <td
        key={product.sku}
        className="border-r border-slate-200 bg-white px-3 py-3 last:border-r-0"
      >
        <ProductAction product={product} onNavigate={onNavigate} />
      </td>
    ))}
  </tr>
=======
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
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
          </tbody >
        </table >
      </div >

<<<<<<< HEAD
    <PresentationNotices
      presentation={presentation}
      disabled={disabled}
      onSuggestion={onSuggestion}
    />
=======
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
>>>>>>> 209597c5b41b7b35759f7c730a06397399c9665b
    </section >
  );
}
