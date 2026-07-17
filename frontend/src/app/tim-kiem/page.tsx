import type { Metadata } from "next";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ProductCard } from "@/components/ProductCard";
import { StateCard } from "@/components/StateCard";
import { searchProducts } from "@/lib/catalog";
import { homePageData } from "@/lib/home-data";

export const metadata: Metadata = {
  title: "Tìm kiếm sản phẩm | Điện máy XANH",
};

interface SearchPageProps {
  searchParams: Promise<{ q?: string | string[] }>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const rawQuery = (await searchParams).q;
  const query = (Array.isArray(rawQuery) ? rawQuery[0] : rawQuery || "").trim();
  const products = query.length >= 2 ? searchProducts(query) : [];

  return (
    <AppShell>
      <main className="mx-auto w-full max-w-[1200px] px-3 py-5 md:px-4">
        <Breadcrumbs items={[{ label: "Trang chủ", href: "/" }, { label: "Tìm kiếm" }]} />
        <section className="mt-4 rounded-xl bg-white p-4 shadow-sm md:p-6">
          <h1 className="text-xl font-bold text-slate-900 md:text-2xl">
            {query ? `Kết quả tìm kiếm cho “${query}”` : "Tìm kiếm sản phẩm"}
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            {query.length >= 2
              ? `Tìm thấy ${products.length} sản phẩm phù hợp.`
              : "Nhập ít nhất 2 ký tự trong ô tìm kiếm phía trên để bắt đầu."}
          </p>

          {products.length ? (
            <div className="mt-5 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : query.length >= 2 ? (
            <div className="mt-5">
              <StateCard
                title="Không tìm thấy sản phẩm"
                description={`Chưa có sản phẩm phù hợp với “${query}”. Hãy thử tên ngành hàng hoặc từ khóa ngắn hơn.`}
              />
            </div>
          ) : null}
        </section>

        <section className="mt-4 rounded-xl bg-white p-4 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">Từ khóa được quan tâm</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {homePageData.searchTags.map((tag) => (
              <Link
                key={tag.id}
                href={`/tim-kiem?q=${encodeURIComponent(tag.label)}`}
                className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-700 transition hover:bg-sky-50 hover:text-brand-blue active:translate-y-px"
              >
                {tag.label}
              </Link>
            ))}
          </div>
        </section>
      </main>
    </AppShell>
  );
}
