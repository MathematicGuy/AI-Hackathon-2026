import Link from "next/link";
import { SafeImage } from "@/components/SafeImage";
import { formatMoney } from "@/lib/format";
import { getProductSlug } from "@/lib/catalog";
import { cn } from "@/lib/utils";
import type { ProductItem } from "@/types/home";

interface ProductCardProps {
  product: ProductItem;
  showRemaining?: boolean;
  className?: string;
}

export function ProductCard({
  product,
  showRemaining = false,
  className,
}: ProductCardProps) {
  return (
    <Link
      href={`/san-pham/${getProductSlug(product)}`}
      className={cn(
        "group flex h-full min-w-0 flex-col rounded-xl border border-slate-100 bg-white p-2.5 text-left shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-sky-100 hover:shadow-md active:translate-y-0 active:bg-slate-50 sm:p-3",
        className,
      )}
    >
      {product.extra ? (
        <span className="mb-2 w-fit max-w-full truncate rounded bg-[#fef3e7] px-2 py-1 text-[10px] font-semibold text-[#e05c00]">
          {product.extra}
        </span>
      ) : null}

      <div className="relative mb-3 aspect-square overflow-hidden rounded-lg bg-white">
        <SafeImage
          src={product.src}
          alt={product.name}
          className="h-full w-full object-contain p-1 transition duration-300 group-hover:scale-[1.03]"
          fallbackLabel={product.name}
          loading="lazy"
        />
        {product.discount ? (
          <span className="absolute bottom-1 left-1 rounded bg-[#d70018] px-1.5 py-0.5 text-[10px] font-bold text-white">
            {product.discount}
          </span>
        ) : null}
      </div>

      <h3 className="line-clamp-2 min-h-10 text-[13px] font-medium leading-5 text-slate-800 transition group-hover:text-brand-blue sm:text-sm">
        {product.name}
      </h3>
      <p className="mt-1 line-clamp-1 text-[11px] text-slate-500 sm:text-xs">
        {product.sub}
      </p>

      <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
        <strong className="text-[16px] text-[#d70018] sm:text-lg">
          {formatMoney(product.price)}
        </strong>
        {product.originalPrice ? (
          <span className="text-[11px] text-slate-400 line-through sm:text-xs">
            {formatMoney(product.originalPrice)}
          </span>
        ) : null}
      </div>

      {showRemaining && product.remain ? (
        <div className="mt-3 overflow-hidden rounded-full bg-[#ffd6d2]">
          <div className="bg-[linear-gradient(90deg,#ff8a3d,#ef3f2f)] px-2 py-1 text-center text-[10px] font-bold text-white sm:text-[11px]">
            {product.remain}
          </div>
        </div>
      ) : null}

      {product.rating || product.soldLabel ? (
        <p className="mt-auto pt-3 text-[11px] text-slate-500 sm:text-xs">
          {product.rating ? <span className="text-amber-500">★ {product.rating.toFixed(1)}</span> : null}
          {product.rating && product.soldLabel ? " • " : null}
          {product.soldLabel || ""}
        </p>
      ) : null}

      {showRemaining ? (
        <span className="mt-3 inline-flex w-full items-center justify-center rounded-md bg-[#fff1e8] px-3 py-2 text-xs font-bold text-[#d94b00] transition group-hover:bg-[#ffe2d0]">
          {product.ctaLabel || "Mua ngay"}
        </span>
      ) : null}
    </Link>
  );
}
