import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { CategoryGrid } from "@/components/CategoryGrid";
import { homePageData } from "@/lib/home-data";

export const metadata: Metadata = {
  title: "Danh mục sản phẩm | Điện máy XANH",
  description: "Tất cả ngành hàng điện máy và gia dụng tại Điện máy XANH.",
};

export default function CategoriesPage() {
  return (
    <AppShell>
      <main className="mx-auto w-full max-w-[1200px] px-3 py-5 md:px-4">
        <Breadcrumbs items={[{ label: "Trang chủ", href: "/" }, { label: "Danh mục" }]} />
        <div className="mt-4 rounded-xl bg-[linear-gradient(115deg,#0875ce,#50b9f4)] px-5 py-7 text-white md:px-8">
          <p className="text-sm font-semibold text-brand-yellow">MUA SẮM DỄ DÀNG</p>
          <h1 className="mt-1 text-2xl font-bold md:text-3xl">Tất cả danh mục sản phẩm</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/85">
            Chọn ngành hàng để xem sản phẩm, mức giá và khuyến mãi tương ứng.
          </p>
        </div>
        <div className="-mx-3 md:-mx-4">
          <CategoryGrid categories={homePageData.categories} />
        </div>
      </main>
    </AppShell>
  );
}
