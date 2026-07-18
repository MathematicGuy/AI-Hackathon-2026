import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { CategoryProductBrowser } from "@/components/CategoryProductBrowser";
import { SafeImage } from "@/components/SafeImage";
import {
  getCategoryBySlug,
  getCategorySlug,
  getProductsForCategory,
} from "@/lib/catalog";
import { homePageData } from "@/lib/home-data";

interface CategoryPageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return homePageData.categories.map((category) => ({
    slug: getCategorySlug(category),
  }));
}

export async function generateMetadata({ params }: CategoryPageProps): Promise<Metadata> {
  const { slug } = await params;
  const category = getCategoryBySlug(slug);

  return {
    title: category
      ? `${category.name} giá tốt | Điện máy XANH`
      : "Không tìm thấy danh mục | Điện máy XANH",
    description: category?.description,
  };
}

export default async function CategoryPage({ params }: CategoryPageProps) {
  const { slug } = await params;
  const category = getCategoryBySlug(slug);

  if (!category) {
    notFound();
  }

  const products = getProductsForCategory(slug);

  return (
    <AppShell>
      <main className="mx-auto w-full max-w-[1200px] px-3 py-5 md:px-4">
        <Breadcrumbs
          items={[
            { label: "Trang chủ", href: "/" },
            { label: "Danh mục", href: "/danh-muc" },
            { label: category.name },
          ]}
        />

        <section className="mt-4 grid overflow-hidden rounded-xl bg-[linear-gradient(115deg,#0c8bd9,#81d9ff)] text-white shadow-sm md:grid-cols-[1fr_260px]">
          <div className="p-5 md:p-8">
            <p className="text-sm font-bold uppercase tracking-wide text-brand-yellow">
              Giá tốt - chính hãng - giao nhanh
            </p>
            <h1 className="mt-2 text-2xl font-bold md:text-3xl">{category.name}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/90">
              {category.description || `Khám phá các sản phẩm ${category.name.toLocaleLowerCase("vi-VN")} nổi bật.`}
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold">
              <span className="rounded-full bg-white/15 px-3 py-1.5">Trả chậm 0%</span>
              <span className="rounded-full bg-white/15 px-3 py-1.5">Bảo hành chính hãng</span>
              <span className="rounded-full bg-white/15 px-3 py-1.5">Lắp đặt tận nơi</span>
            </div>
          </div>
          <div className="hidden items-center justify-center bg-white/10 p-5 md:flex">
            <SafeImage
              src={category.src}
              alt={category.name}
              className="size-44 object-contain drop-shadow-xl"
              fallbackLabel={category.name}
            />
          </div>
        </section>

        <CategoryProductBrowser products={products} />
      </main>
    </AppShell>
  );
}
