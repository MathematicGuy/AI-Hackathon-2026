import Link from "next/link";
import { SafeImage } from "@/components/SafeImage";
import { StateCard } from "@/components/StateCard";
import { getCategorySlug } from "@/lib/catalog";
import type { CategoryItem } from "@/types/home";

interface CategoryGridProps {
  categories: CategoryItem[];
}

export function CategoryGrid({ categories }: CategoryGridProps) {
  if (!categories.length) {
    return (
      <section className="mx-auto max-w-[1200px] px-3 pt-4 md:px-4">
        <StateCard
          title="Danh mục đang trống"
          description="Hiện chưa có nhóm ngành hàng nào để hiển thị. Vui lòng thử lại sau."
        />
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-[1200px] px-3 pt-4 md:px-4">
      <div className="grid grid-cols-3 gap-x-2 gap-y-3 rounded-xl bg-white p-3 shadow-sm sm:grid-cols-4 md:grid-cols-6 md:p-4 lg:grid-cols-8">
        {categories.map((item) => (
          <Link
            key={item.id}
            href={`/danh-muc/${getCategorySlug(item)}`}
            className="group relative flex min-h-[105px] flex-col items-center justify-center rounded-xl border border-transparent px-2 py-3 text-center transition hover:border-sky-100 hover:bg-sky-50 active:translate-y-px active:bg-sky-100"
          >
            {item.badge ? (
              <span className="absolute left-1.5 top-1.5 rounded-full bg-[#ffebe9] px-1.5 py-0.5 text-[9px] font-bold text-[#d92d20]">
                {item.badge}
              </span>
            ) : null}
            <SafeImage
              src={item.src}
              alt={item.name}
              className="mb-2 size-14 object-contain transition group-hover:scale-105"
              fallbackLabel={item.name}
              loading="lazy"
            />
            <span className="text-[11px] font-medium leading-4 text-slate-700 md:text-xs">
              {item.name}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
